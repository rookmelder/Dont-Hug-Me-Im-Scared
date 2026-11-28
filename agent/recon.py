#!/usr/bin/env python3
"""Recon pipeline for the Lead: scan, parse, one scan per host, CVEs, score, rank. Raw output goes to files; the
Lead reads only the short summaries this script prints and the YAML host files. Standard library only.

  python agent/recon.py discover              # which in-scope hosts are up -> hosts/<ip>/host.yaml (status: discovered)
  python agent/recon.py scan [IP ...]         # one full port scan per host, in parallel -> services, CVEs, score
  python agent/recon.py all                   # discover + scan
  python agent/recon.py import FILE.xml       # read an nmap XML you ran yourself (discovery or port scan)
  python agent/recon.py status                # the ranked host list (big / medium / small fish)
  python agent/recon.py research [LABEL ...]  # write researcher tasks (labels, never IPs) + print the delegate commands
  python agent/recon.py merge LABEL RUN_ID    # put a researcher's result (its run id) into the host file, re-rank
  python agent/recon.py score                 # re-rank after editing agent/recon.yaml
  --stealth normal|quiet|sneaky|paranoid      # how loud discover/scan are (rate, parallel, ports, probes)

Where things go (engagements/<name>/, git-ignored):
  scans/discover-<time>.xml|.log      raw discovery output
  hosts/<ip>/host.yaml                everything known about one host (made by this script; easy to read)
  hosts/<ip>/scans/ports-<time>.xml   raw per-host scan output
  hosts/index.yaml                    every host with its score and tier, best first
Safety: runs only when the engagement's SCOPE.md is authorised, and only ever scans in-scope targets. A live host
that SCOPE.md does not list is recorded under out_of_scope in index.yaml and never scanned.
Settings (commands, parallel scans, scoring, tiers): agent/recon.yaml.
Exit: 0 ok, 2 bad input, 4 not authorised / out of scope, 6 a tool failed.
"""
import argparse
import concurrent.futures
import ipaddress
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
ROOT = AGENT_DIR.parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(ROOT / '.claude' / 'hooks'))
import yamlio   # noqa: E402
import _scope   # noqa: E402   SCOPE.md reading, shared with the hooks

CVE = re.compile(r'\bCVE-\d{4}-\d{4,}\b', re.I)
FENCE = chr(96) * 3
HEADER = 'Made by agent/recon.py: edit research notes by hand if you like; scans and scores are rewritten.'


class Fail(Exception):
    def __init__(self, msg, code):
        super().__init__(msg)
        self.code = code


def now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def stamp():
    return time.strftime('%Y%m%d-%H%M%S')


def config(stealth=None):
    """recon.yaml with the stealth level applied: its parallel / timeout_min win, its timing/ports/scripts fill the
    commands. stealth (from --stealth) overrides the file's stealth: line."""
    cfg = yamlio.read(AGENT_DIR / 'recon.yaml')
    levels = cfg.get('stealth_levels') or {}
    name = str(stealth or cfg.get('stealth') or 'normal').strip().lower()
    if levels and name not in levels:
        raise Fail(f"stealth '{name}': pick one of {', '.join(levels)} (agent/recon.yaml stealth_levels).", 2)
    prof = levels.get(name) or {}
    cfg['stealth'] = name
    cfg['profile'] = {'discover_timing': str(prof.get('discover_timing') or ''), 'timing': str(prof.get('timing') or ''),
                      'ports': str(prof.get('ports') or '-p-'), 'scripts': str(prof.get('scripts') or 'default,vulners')}
    for k in ('parallel', 'timeout_min'):
        if prof.get(k) is not None:
            cfg[k] = prof[k]
    return cfg


# --- Engagement and scope ----------------------------------------------------------------------
class Engagement:
    """The active engagement: its folder, and the in-scope networks and hostnames from its SCOPE.md."""

    def __init__(self, name=None, root=None):
        root = Path(root or ROOT)
        self.root = root
        engs = {e.name: e for e in _scope.engagements(root)}
        if name:
            if name not in engs:
                raise Fail(f"no engagement '{name}' under engagements/ (have: {', '.join(engs) or 'none'}).", 2)
            folder = engs[name]
        else:
            state, names = _scope.status(root)
            if state != 'ok':
                raise Fail({'none': 'no engagement yet: start one (new-engagement skill).',
                            'unauthorised': 'SCOPE.md is NOT AUTHORISED YET: the user fills it in first. Nothing was scanned.',
                            'ambiguous': f"several engagements ({', '.join(names)}): give --engagement NAME."}[state], 4)
            folder = engs[names[0]]
        scope = _scope.read(folder / 'SCOPE.md')
        if not _scope.authorised(scope):
            raise Fail(f'{folder.name}: SCOPE.md is NOT AUTHORISED YET. Nothing was scanned.', 4)
        self.name, self.dir = folder.name, folder
        self.nets, self.names = _scope.parse_targets(scope)
        if not self.nets and not self.names:
            raise Fail(f'{folder.name}: SCOPE.md lists no in-scope targets.', 4)
        self.hosts_dir = folder / 'hosts'

    def in_scope(self, ip, hostnames=()):
        try:
            addr = ipaddress.ip_address(ip)
            if any(addr.version == n.version and addr in n for n in self.nets):
                return True
        except ValueError:
            pass
        return any(h.lower() == s or h.lower().endswith('.' + s) for h in hostnames for s in self.names)

    def targets(self):
        return [str(n) for n in self.nets] + sorted(self.names)

    def host_file(self, ip):
        return self.hosts_dir / ip / 'host.yaml'

    def load_host(self, ip):
        f = self.host_file(ip)
        return yamlio.read(f) if f.exists() else None

    def save_host(self, h):
        yamlio.write(self.host_file(h['ip']), h, HEADER)

    def all_hosts(self):
        out = []
        for f in sorted(self.hosts_dir.glob('*/host.yaml')):
            try:
                out.append(yamlio.read(f))
            except ValueError as e:
                print(f'warning: {f} unreadable ({e}); skipped', file=sys.stderr)
        return out

    def by_label(self, label):
        for h in self.all_hosts():
            if label in (h.get('label'), h.get('ip')):
                return h
        raise Fail(f"no host '{label}' (labels: python agent/recon.py status).", 2)


# --- nmap XML -> host data --------------------------------------------------------------------
def _vulners(script):
    """<script id="vulners"> -> (cves, exploits). Tables per CPE, each entry: id, cvss, type, is_exploit."""
    cves, exploits = [], []
    for t in script.iter('table'):
        e = {x.get('key'): (x.text or '') for x in t.findall('elem')}
        if not e.get('id'):
            continue
        try:
            cvss = float(e.get('cvss') or 0) or None
        except ValueError:
            cvss = None
        is_exp = (e.get('is_exploit') or '').lower() == 'true'
        if (e.get('type') or '').lower() == 'cve' or CVE.fullmatch(e['id']):
            cves.append({'id': e['id'].upper(), 'cvss': cvss, 'exploit': is_exp, 'source': 'tool: nmap vulners'})
        elif is_exp:
            exploits.append({'title': e['id'], 'cve': '', 'source': 'tool: nmap vulners'})
    if not cves:   # older vulners output: text lines "CVE-2016-6515  7.8  https://..."
        for m in re.finditer(r'(CVE-\d{4}-\d{4,})\s+(\d+(?:\.\d)?)([^\n]*)', script.get('output') or '', re.I):
            cves.append({'id': m.group(1).upper(), 'cvss': float(m.group(2)), 'exploit': '*EXPLOIT*' in m.group(3),
                         'source': 'tool: nmap vulners'})
    seen, uniq = set(), []
    for c in cves:
        if c['id'] not in seen:
            seen.add(c['id'])
            uniq.append(c)
    return sorted(uniq, key=lambda c: -(c['cvss'] or 0)), exploits


def parse_nmap(xml_text):
    """nmap -oX output -> ([{ip, up, hostnames, mac, vendor, os, ports: [...]}, ...], was it a port scan)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise Fail(f'not valid nmap XML ({e}): was the scan stopped early?', 6)
    port_scan = root.find('scaninfo') is not None
    hosts = []
    for h in root.findall('host'):
        st = h.find('status')
        up = st is None or st.get('state') == 'up'
        ip = mac = vendor = ''
        for a in h.findall('address'):
            if a.get('addrtype') in ('ipv4', 'ipv6'):
                ip = a.get('addr', '')
            elif a.get('addrtype') == 'mac':
                mac, vendor = a.get('addr', ''), a.get('vendor', '')
        if not ip:
            continue
        names = sorted({n.get('name', '') for n in h.iter('hostname') if n.get('name')})
        # Only a name we gave nmap (type="user") can put a host in scope; PTR names come from the target's own DNS.
        asked = sorted({n.get('name', '') for n in h.iter('hostname') if n.get('name') and n.get('type') == 'user'})
        os_ = {}
        best = max(h.iter('osmatch'), key=lambda o: int(o.get('accuracy') or 0), default=None)
        if best is not None:
            os_ = {'name': best.get('name', ''), 'accuracy': int(best.get('accuracy') or 0)}
        ports = []
        for p in h.iter('port'):
            state = (p.find('state').get('state') if p.find('state') is not None else '')
            if state not in ('open', 'open|filtered'):
                continue
            s = p.find('service')
            s = s.attrib if s is not None else {}
            cpes = [c.text for c in p.iter('cpe') if c.text]
            scripts, cves, exploits = {}, [], []
            for sc in p.findall('script'):
                if sc.get('id') == 'vulners':
                    cves, exploits = _vulners(sc)
                else:
                    scripts[sc.get('id', '?')] = ' '.join((sc.get('output') or '').split())[:300]
            for sid, out in scripts.items():   # CVE ids other scripts name (e.g. smb-vuln-*)
                for cid in sorted({m.upper() for m in CVE.findall(out)}):
                    if cid not in {c['id'] for c in cves}:
                        cves.append({'id': cid, 'cvss': None, 'exploit': False, 'source': f'tool: nmap {sid}'})
            name = s.get('name', '')
            if s.get('tunnel') == 'ssl' and name and not name.startswith('ssl'):
                name = 'ssl/' + name
            ports.append({'port': int(p.get('portid')), 'proto': p.get('protocol', 'tcp'), 'state': state, 'service': name,
                          'product': s.get('product', ''), 'version': s.get('version', ''), 'extra': s.get('extrainfo', ''),
                          'cpe': cpes, 'scripts': scripts, 'cves': cves, 'exploits': exploits})
        hosts.append({'ip': ip, 'up': up, 'hostnames': names, 'target_names': asked, 'mac': mac, 'vendor': vendor, 'os': os_,
                      'ports': sorted(ports, key=lambda x: (x['proto'], x['port']))})
    return hosts, port_scan


# --- Running tools ------------------------------------------------------------------------------
def fill(template, raw=None, **values):
    """A command from recon.yaml -> argv. {targets}/{host}/{out} are filled shell-quoted (one argument each); raw
    values (the stealth options from recon.yaml itself) are split into their options. No shell runs it."""
    def q(v):
        return ' '.join(shlex.quote(x) for x in v) if isinstance(v, (list, tuple)) else shlex.quote(str(v))
    cmd = template
    for k, v in (raw or {}).items():
        cmd = cmd.replace('{' + k + '}', str(v))
    for k, v in values.items():
        cmd = cmd.replace('{' + k + '}', q(v))
    return shlex.split(cmd)


def run_logged(argv, log_path, timeout):
    """Run a tool with all its output in log_path (never printed). Returns its exit code, None on timeout."""
    if not shutil.which(argv[0]):
        raise Fail(f'{argv[0]} is not installed on this machine (install it, e.g. apt install {argv[0]}).', 6)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'wb') as log:
        log.write(('$ ' + shlex.join(argv) + '\n').encode())
        log.flush()
        try:
            return subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                  timeout=timeout, cwd=str(ROOT)).returncode
        except subprocess.TimeoutExpired:
            return None


def searchsploit(port):
    """Exploit-DB hits for one service (product + version), [] when nothing or not installed."""
    q = ' '.join(x for x in (port.get('product'), port.get('version')) if x).strip()
    if not q or not shutil.which('searchsploit'):
        return []
    try:
        r = subprocess.run(['searchsploit', '--json', '--disable-colour', q], capture_output=True, text=True, timeout=60)
        data = json.loads(r.stdout or '{}')
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return []
    out = []
    for e in (data.get('RESULTS_EXPLOIT') or [])[:10]:
        title = e.get('Title', '')
        out.append({'title': f"EDB-{e.get('EDB-ID', '?')}: {title}", 'cve': ', '.join(sorted(set(CVE.findall(title)))),
                    'source': 'tool: searchsploit'})
    return out


# --- Host files, scoring, index ------------------------------------------------------------------
def next_label(eng):
    used = [int(m.group(1)) for h in eng.all_hosts() for m in [re.match(r'host-(\d+)$', str(h.get('label') or ''))] if m]
    return f'host-{(max(used) + 1 if used else 1):02d}'


def upsert(eng, found, scan_file=None, ports_scanned=False):
    """Merge parsed nmap hosts into host.yaml files. Returns (in-scope ips, out-of-scope ips)."""
    ins, outs = [], []
    for f in found:
        if not f['up']:
            continue
        if not eng.in_scope(f['ip'], f.get('target_names') or []):
            outs.append(f['ip'])
            continue
        h = eng.load_host(f['ip']) or {'ip': f['ip'], 'label': next_label(eng), 'status': 'discovered', 'first_seen': now(),
                                       'hostnames': [], 'mac': '', 'vendor': '', 'os': {}, 'ports': [], 'scans': [],
                                       'research': {}, 'score': {}, 'tier': ''}
        h['hostnames'] = sorted(set(h.get('hostnames') or []) | set(f['hostnames']))
        h['target_names'] = sorted(set(h.get('target_names') or []) | set(f.get('target_names') or []))
        for k in ('mac', 'vendor'):
            h[k] = f[k] or h.get(k, '')
        if f['os']:
            h['os'] = f['os']
        if ports_scanned:
            h['ports'] = f['ports']
            h['status'] = 'researched' if h.get('research') else 'scanned'
            h['last_scan'] = now()
        if scan_file:
            h['scans'] = (h.get('scans') or []) + [str(scan_file.relative_to(eng.dir))]
        eng.save_host(h)
        ins.append(f['ip'])
    return ins, outs


def score_host(h, cfg):
    """-> {total, parts, role, worst_cvss}: the formula from recon.yaml, so the ranking is the same every time."""
    s, ports, research = cfg.get('score') or {}, h.get('ports') or [], h.get('research') or {}
    rcves = [c for c in (research.get('cves') or []) if c.get('applies') in ('yes', 'likely') and not c.get('unverified')]
    cvss = [c.get('cvss') or 0 for p in ports for c in p.get('cves') or []] + [c.get('cvss') or 0 for c in rcves]
    exploit = (any(c.get('exploit') for p in ports for c in p.get('cves') or []) or any(p.get('exploits') for p in ports)
               or any(c.get('exploit_public') for c in rcves) or bool(research.get('exploits')))
    kev = any(c.get('in_kev') for c in rcves)
    names = {str(p.get('service') or '').lower() for p in ports}
    nums = {int(p.get('port') or 0) for p in ports}
    role, role_pts = '', 0
    for r in s.get('roles') or []:
        if ({str(x).lower() for x in r.get('services') or []} & names or set(r.get('ports') or []) & nums) and r.get('points', 0) > role_pts:
            role, role_pts = r.get('name', ''), r.get('points', 0)
    parts = {
        'worst_cvss': round((max(cvss) if cvss else 0) * s.get('cvss', 0), 1),
        'exploit': s.get('exploit', 0) if exploit else 0,
        'kev': s.get('kev', 0) if kev else 0,
        'services': min(len(ports) * s.get('per_service', 0), s.get('services_cap', 0)),
        'role': role_pts,
        'research': (research.get('value') or 0) * s.get('research_value', 0),
    }
    return {'total': round(sum(parts.values()), 1), 'parts': parts, 'role': role, 'worst_cvss': max(cvss) if cvss else None}


def tier(total, cfg):
    t = cfg.get('tiers') or {}
    return 'big' if total >= t.get('big', 60) else 'medium' if total >= t.get('medium', 30) else 'small'


def short_services(h, n=99):
    out = []
    for p in (h.get('ports') or [])[:n]:
        what = ' '.join(x for x in (p.get('product'), p.get('version')) if x)
        out.append(f"{p['port']}/{p.get('service') or '?'}" + (f' {what}' if what else ''))
    more = len(h.get('ports') or []) - n
    return out + ([f'+{more} more'] if more > 0 else [])


def rescore(eng, cfg=None, out_of_scope=()):
    cfg = cfg or config()
    hosts = eng.all_hosts()
    for h in hosts:
        h['score'] = score_host(h, cfg)
        h['tier'] = tier(h['score']['total'], cfg)
        eng.save_host(h)
    hosts.sort(key=lambda h: -h['score']['total'])
    old = yamlio.read(eng.hosts_dir / 'index.yaml') if (eng.hosts_dir / 'index.yaml').exists() else {}
    oos = sorted(set(old.get('out_of_scope') or []) | set(out_of_scope))
    index = {'engagement': eng.name, 'updated': now(),
             'counts': {t: sum(1 for h in hosts if h['tier'] == t) for t in ('big', 'medium', 'small')},
             'hosts': [{'label': h['label'], 'ip': h['ip'], 'tier': h['tier'], 'score': h['score']['total'],
                        'status': h.get('status', ''), 'role': h['score']['role'], 'worst_cvss': h['score']['worst_cvss'],
                        'services': short_services(h, 6)} for h in hosts],
             'out_of_scope': oos}
    yamlio.write(eng.hosts_dir / 'index.yaml', index, 'Every host, best target first. Made by agent/recon.py (score / status).')
    return hosts


# --- Commands -------------------------------------------------------------------------------------
def warn_level(eng):
    lvl = _scope.level(eng.root)
    if lvl < 2:
        print(f'warning: SCOPE.md level is {lvl} (recon = passive only); these scans are active (level 2). '
              'Ask the user to raise the level first.', file=sys.stderr)


def cmd_discover(eng, cfg):
    warn_level(eng)
    out = eng.dir / 'scans' / f'discover-{stamp()}.xml'
    p = cfg.get('profile') or {}
    argv = fill(cfg['discover'], raw={'timing': p.get('discover_timing', '')}, targets=eng.targets(), out=str(out))
    print(f"discover: {len(eng.targets())} in-scope target(s), stealth {cfg.get('stealth', 'normal')}, "
          f"output in {out.relative_to(eng.root)}")
    rc = run_logged(argv, out.with_suffix('.log'), (cfg.get('timeout_min') or 90) * 60)
    if rc is None or not out.exists():
        raise Fail(f'discovery {"timed out" if rc is None else f"failed (exit {rc})"}: see {out.with_suffix(".log")}', 6)
    found, ports = parse_nmap(out.read_text(encoding='utf-8', errors='replace'))
    ins, outs = upsert(eng, found, out, ports)
    rescore(eng, cfg, outs)
    print(f'discover: {len(ins)} live in-scope host(s)' + (f', {len(outs)} OUT OF SCOPE (not scanned): {", ".join(outs[:10])}' if outs else ''))
    return ins


def scan_one(eng, cfg, ip):
    out = eng.hosts_dir / ip / 'scans' / f'ports-{stamp()}.xml'
    p = cfg.get('profile') or {}
    argv = fill(cfg['ports'], raw={'timing': p.get('timing', ''), 'ports': p.get('ports', '-p-'), 'scripts': p.get('scripts', 'default,vulners')},
                host=ip, out=str(out))
    rc = run_logged(argv, out.with_suffix('.log'), (cfg.get('timeout_min') or 90) * 60)
    if rc is None:
        return ip, 'timed out'
    if not out.exists():
        return ip, f'failed (exit {rc})'
    found, _ = parse_nmap(out.read_text(encoding='utf-8', errors='replace'))
    found = [f for f in found if f['ip'] == ip] or [{'ip': ip, 'up': True, 'hostnames': [], 'mac': '', 'vendor': '', 'os': {}, 'ports': []}]
    found[0]['target_names'] = (eng.load_host(ip) or {}).get('target_names') or found[0].get('target_names') or []
    if cfg.get('searchsploit', True):
        for p in found[0]['ports']:
            p['exploits'] = (p.get('exploits') or []) + searchsploit(p)
    upsert(eng, found, out, ports_scanned=True)
    return ip, 'ok'


def cmd_scan(eng, cfg, ips):
    known = {h['ip']: h for h in eng.all_hosts()}
    if not ips:
        ips = [ip for ip, h in known.items() if h.get('status') == 'discovered']
    for ip in ips:   # every host checked against SCOPE.md before anything runs
        if not eng.in_scope(ip, (known.get(ip) or {}).get('target_names') or []):
            raise Fail(f'{ip} is not in SCOPE.md: not scanned. The user adds it to SCOPE.md first.', 4)
    if not ips:
        print('scan: nothing to scan (no hosts with status discovered; give IPs to rescan).')
        return
    warn_level(eng)
    if cfg.get('searchsploit', True) and not shutil.which('searchsploit'):
        print('scan: searchsploit not installed: Exploit-DB lookups skipped (apt install exploitdb).')
    par = max(1, int(cfg.get('parallel') or 4))
    print(f"scan: {len(ips)} host(s), {par} at a time, stealth {cfg.get('stealth', 'normal')} "
          f"({(cfg.get('profile') or {}).get('timing', '')} {(cfg.get('profile') or {}).get('ports', '')}); raw output in hosts/<ip>/scans/")
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=par) as pool:
        for ip, result in pool.map(lambda ip: scan_one(eng, cfg, ip), ips):
            print(f'  {ip}: {result}', flush=True)
            if result != 'ok':
                failed.append(ip)
    rescore(eng, cfg)
    if failed:
        raise Fail(f'{len(failed)} scan(s) failed: {", ".join(failed)} (see hosts/<ip>/scans/*.log)', 6)


def cmd_import(eng, cfg, path):
    p = Path(path)
    if not p.exists():
        raise Fail(f'{path}: no such file.', 2)
    found, ports = parse_nmap(p.read_text(encoding='utf-8', errors='replace'))
    ins, outs = upsert(eng, found, p.resolve() if p.resolve().is_relative_to(eng.dir.resolve()) else None, ports)
    rescore(eng, cfg, outs)
    print(f"import: {len(ins)} in-scope host(s) ({'with ports' if ports else 'discovery only'})"
          + (f', {len(outs)} OUT OF SCOPE (ignored): {", ".join(outs[:10])}' if outs else ''))


def cmd_status(eng):
    hosts = rescore(eng)
    if not hosts:
        print('no hosts yet: python agent/recon.py discover')
        return
    print(f'{eng.name}: {len(hosts)} host(s)')
    print(f"{'label':8} {'tier':6} {'score':>5}  {'status':10} {'role':18} {'cvss':>4}  services")
    for h in hosts:
        sc = h['score']
        cv = '' if sc['worst_cvss'] is None else f"{sc['worst_cvss']:.1f}"
        print(f"{h['label']:8} {h['tier']:6} {sc['total']:>5}  {h.get('status', ''):10} {(sc['role'] or '-')[:18]:18} {cv:>4}  "
              + '; '.join(short_services(h, 4)))
    idx = yamlio.read(eng.hosts_dir / 'index.yaml')
    if idx.get('out_of_scope'):
        print(f"out of scope (seen, never scanned): {len(idx['out_of_scope'])}, listed in hosts/index.yaml")


RESEARCH_TASK = """# Research one host ({label})

Goal: find out what this host is, what it is used for, how valuable a target it is, and which known
vulnerabilities apply to its exact versions. Return the JSON the schema asks for; nothing else.

The host is called {label}. Never put an IP address, hostname or engagement name in a web search or a URL:
search for the products and versions only.

## What the scans found
OS guess: {os}
Role guess from its services: {role}

{services}

## Known vulnerabilities from the tools (start here)
{cves}

## Public exploits the tools found
{exploits}

## Do
1. Say what the host is and what it is probably used for (from the services, versions and banners above).
2. For every CVE above: check on the web (NVD, the vendor advisory, CISA KEV) whether the affected version range
   really covers THIS version; set applies, cvss, in_kev, exploit_public; source = the URL you read, or
   "tool: nmap vulners" / "tool: searchsploit" when you only had the tool output.
3. Search the web for important CVEs the tools missed for these exact versions. Add only ones you read on a page,
   with that page's URL as source. Never a CVE from memory.
4. Rate value 1-5 (5 = domain controller, database with real data, or a host that opens the rest of the network)
   and give the 0-4 most promising attack paths, best first.
5. List every URL you read under sources. Anything you could not confirm goes under unsure.
"""

IP_LIKE = re.compile(r'(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])')
# Domain-like words a banner may carry (acme.com, dc01.corp.local). Product names (Node.js, ASP.NET) stay.
DOMAIN_LIKE = re.compile(r'\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|co|uk|de|nl|be|fr|eu|us|gov|edu|info|biz)\b'
                         r'|(?i:\b(?:[a-z0-9-]+\.)+(?:local|lan|corp|internal|intranet|home|htb|thm|localdomain)\b)'
                         r'|\b[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*\b')
NAME_FIELDS = re.compile(r'\b(domain|workgroup|site|host|hostname|computer|fqdn|dns|realm|forest|cn|commonname)\s*[:=]\s*[^,;)]+', re.I)


def research_task(h, nets=()):
    """The researcher's task: label, services, versions, tool CVEs. Nothing that names the target reaches the web: no
    script output (smb-os-discovery, ssl-cert, http-title... carry computer, domain and site names), no hostnames or
    domain-like words, no address of this host or its networks. Version numbers like 10.2.0.4 stay."""
    names = [n for n in (h.get('hostnames') or []) + (h.get('target_names') or []) if n]

    def own_ip(m):
        try:
            ip = ipaddress.ip_address(m.group(1))
        except ValueError:
            return m.group(0)
        return '<ip>' if m.group(1) == h.get('ip') or any(ip.version == n.version and ip in n for n in nets) else m.group(0)

    def clean(text):
        text = IP_LIKE.sub(own_ip, str(text))
        for n in names:
            text = re.sub(re.escape(n), '<hostname>', text, flags=re.I)
        text = NAME_FIELDS.sub(lambda m: m.group(1) + ': <name>', text)
        return DOMAIN_LIKE.sub('<name>', text)
    lines = []
    for p in h.get('ports') or []:
        what = ' '.join(x for x in (p.get('product'), p.get('version'), p.get('extra')) if x)
        lines.append(clean(f"- {p['port']}/{p.get('proto', 'tcp')} {p.get('service') or '?'}: {what or 'unknown version'}")
                     + (f" (cpe: {', '.join(p['cpe'])})" if p.get('cpe') else ''))
    cves = [f"- {c['id']} (cvss {c.get('cvss') or '?'}{', exploit' if c.get('exploit') else ''}) on {p['port']}/{p.get('service')}"
            f" ({c.get('source')})" for p in h.get('ports') or [] for c in p.get('cves') or []]
    exps = [clean(f"- {e['title']} on {p['port']}/{p.get('service')} ({e.get('source')})")
            for p in h.get('ports') or [] for e in p.get('exploits') or []]
    os_ = clean((h.get('os') or {}).get('name') or 'unknown')
    return RESEARCH_TASK.format(label=h['label'], os=os_, role=(h.get('score') or {}).get('role') or 'none matched',
                                services='\n'.join(lines) or '- no open services found',
                                cves='\n'.join(cves[:60]) or '- none', exploits='\n'.join(exps[:40]) or '- none')


def cmd_research(eng, labels):
    hosts = rescore(eng)
    todo = [h for h in hosts if (h['label'] in labels or h['ip'] in labels)] if labels else \
        [h for h in hosts if h.get('status') == 'scanned']
    if not todo:
        print('research: nothing to do (no scanned hosts without research; give labels to redo one).')
        return
    print(f'research: {len(todo)} task(s), best target first. Run each in the background (the worker cap queues them):')
    for h in todo:
        task = ROOT / '.worker' / f"research-{h['label']}.md"
        task.parent.mkdir(exist_ok=True)
        task.write_text(research_task(h, eng.nets), encoding='utf-8')
        print(f"  [{h['tier']:6} {h['score']['total']:>5}] python agent/delegate.py --role host-researcher "
              f"--task-file .worker/{task.name} --schema agent/schemas/host-research.json")
    print('then, per finished run: python agent/recon.py merge <label> <run id>')


def extract_json(text):
    text = str(text or '').strip()
    m = re.search(FENCE + r'(?:json)?\s*(\{.*\})\s*' + FENCE, text, re.S)
    for cand in ([m.group(1)] if m else []) + [text, text[text.find('{'):text.rfind('}') + 1]]:
        try:
            v = json.loads(cand)
            if isinstance(v, dict):
                return v
        except ValueError:
            continue
    raise Fail('the worker result is not the research JSON (see its run file).', 6)


def cmd_merge(eng, cfg, label, run):
    h = eng.by_label(label)
    m = re.fullmatch(r'(?:.*[\\/])?(?:run-)?([0-9a-f]{8})(?:\.json)?', run.strip())
    f = ROOT / '.worker' / f'run-{m.group(1)}.json' if m else Path(run)
    if not f.exists():
        raise Fail(f"{run}: no such run in .worker/ (give the id from the 'saved:' line).", 2)
    res = json.loads(f.read_text(encoding='utf-8'))
    if res.get('code') not in (0, None):
        print(f"merge: warning: that run ended with exit {res.get('code')}", file=sys.stderr)
    data = extract_json(res.get('response'))
    cves, dropped = [], []
    for c in data.get('cves') or []:
        if not isinstance(c, dict) or not CVE.fullmatch(str(c.get('id') or '')):
            dropped.append(str(c)[:60])
        elif str(c.get('source') or '').strip().lower() in ('', 'memory', 'none', 'n/a', 'unknown'):
            dropped.append(c['id'])
        else:
            c['id'] = c['id'].upper()
            cves.append(c)
    unverified = 0
    if not res.get('web_uses'):   # nothing was searched in that run: a URL source was not read there
        for c in cves:
            if 'tool:' not in str(c.get('source') or ''):
                c['unverified'] = 'no web lookup in that run: the source URL was not read'
                unverified += 1
    try:
        value = max(1, min(5, int(data.get('value') or 1)))
    except (TypeError, ValueError):
        value = 1
    h['research'] = {'what': str(data.get('what') or ''), 'used_for': str(data.get('used_for') or ''), 'value': value,
                     'value_reason': str(data.get('value_reason') or ''), 'cves': cves,
                     'exploits': [e for e in data.get('exploits') or [] if isinstance(e, dict) and str(e.get('source') or '').strip()],
                     'attack_paths': [str(x) for x in data.get('attack_paths') or []][:4],
                     'sources': [str(x) for x in data.get('sources') or []], 'unsure': str(data.get('unsure') or ''),
                     'by': f"{res.get('worker')} (run {f.stem[4:]})", 'at': now(), 'dropped_no_source': dropped}
    h['status'] = 'researched'
    eng.save_host(h)
    hosts = rescore(eng, cfg)
    h = next(x for x in hosts if x['ip'] == h['ip'])
    print(f"merge: {h['label']} researched: {len(cves)} CVE(s) kept" + (f', {len(dropped)} dropped (no source)' if dropped else '')
          + (f', {unverified} UNVERIFIED (the worker searched nothing; not counted in the score)' if unverified else '')
          + f"; score {h['score']['total']}, {h['tier']} fish")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=('discover', 'scan', 'all', 'import', 'status', 'research', 'merge', 'score'))
    ap.add_argument('args', nargs='*')
    ap.add_argument('--engagement', help='engagement folder name (default: the one authorised engagement)')
    ap.add_argument('--stealth', help='normal | quiet | sneaky | paranoid: how loud the scans are (default: recon.yaml stealth)')
    a = ap.parse_args(argv)
    eng = Engagement(a.engagement)
    cfg = config(a.stealth)
    if a.command == 'discover':
        cmd_discover(eng, cfg)
    elif a.command == 'scan':
        cmd_scan(eng, cfg, a.args)
    elif a.command == 'all':
        cmd_discover(eng, cfg)
        cmd_scan(eng, cfg, [])
        cmd_status(eng)
    elif a.command == 'import':
        if len(a.args) != 1:
            raise Fail('import FILE.xml', 2)
        cmd_import(eng, cfg, a.args[0])
    elif a.command in ('status', 'score'):
        cmd_status(eng)
    elif a.command == 'research':
        cmd_research(eng, a.args)
    elif a.command == 'merge':
        if len(a.args) != 2:
            raise Fail('merge LABEL RUN_ID', 2)
        cmd_merge(eng, cfg, *a.args)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Fail as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(e.code)
