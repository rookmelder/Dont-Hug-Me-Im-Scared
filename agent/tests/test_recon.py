"""Tests for agent/recon.py and agent/yamlio.py, on fixture nmap XML with a fake nmap (no real scans).
Run: python -m unittest discover -s agent/tests"""
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recon  # noqa: E402
import yamlio  # noqa: E402

SCOPE = ("# SCOPE\n**Status:** authorised\n- I confirm I own these targets: **(yes / no)** — " + chr(96) + "yes" + chr(96)
         + "\n- **Level:** 2\n## In scope (ONLY these)\n- " + chr(96) + "10.10.10.0/24" + chr(96) + " — lab\n## Out of scope\n- everything else\n")

DISCOVERY = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sn">
<host><status state="up"/><address addr="10.10.10.5" addrtype="ipv4"/><address addr="AA:BB:CC:00:11:22" addrtype="mac" vendor="VMware"/>
<hostnames><hostname name="web.lab" type="PTR"/></hostnames></host>
<host><status state="up"/><address addr="10.10.10.9" addrtype="ipv4"/></host>
<host><status state="down"/><address addr="10.10.10.200" addrtype="ipv4"/></host>
<host><status state="up"/><address addr="192.168.1.1" addrtype="ipv4"/></host>
</nmaprun>"""

def ports_xml(ip):
    if ip == '10.10.10.5':
        return f"""<?xml version="1.0"?>
<nmaprun scanner="nmap"><scaninfo type="syn" protocol="tcp"/>
<host><status state="up"/><address addr="{ip}" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22"><state state="open"/><service name="ssh" product="OpenSSH" version="7.2p2 Ubuntu 4ubuntu2.8" extrainfo="Ubuntu Linux; protocol 2.0"><cpe>cpe:/a:openbsd:openssh:7.2p2</cpe></service>
<script id="vulners" output="cpe:/a:openbsd:openssh:7.2p2 ...">
<table key="cpe:/a:openbsd:openssh:7.2p2">
<table><elem key="is_exploit">false</elem><elem key="cvss">7.8</elem><elem key="id">CVE-2016-6515</elem><elem key="type">cve</elem></table>
<table><elem key="is_exploit">true</elem><elem key="cvss">5.0</elem><elem key="id">EDB-ID:40136</elem><elem key="type">exploitdb</elem></table>
<table><elem key="is_exploit">false</elem><elem key="cvss">5.3</elem><elem key="id">CVE-2016-6210</elem><elem key="type">cve</elem></table>
</table></script></port>
<port protocol="tcp" portid="80"><state state="open"/><service name="http" product="Apache httpd" version="2.4.18"/>
<script id="http-title" output="Site at 10.10.10.5 &#xa; Welcome"/></port>
<port protocol="tcp" portid="81"><state state="closed"/><service name="hosts2-ns"/></port>
</ports><os><osmatch name="Linux 4.15" accuracy="95"/><osmatch name="Linux 3.2" accuracy="90"/></os></host></nmaprun>"""
    return f"""<?xml version="1.0"?>
<nmaprun scanner="nmap"><scaninfo type="syn" protocol="tcp"/>
<host><status state="up"/><address addr="{ip}" addrtype="ipv4"/><ports>
<port protocol="tcp" portid="88"><state state="open"/><service name="kerberos-sec" product="Microsoft Windows Kerberos"/></port>
<port protocol="tcp" portid="445"><state state="open"/><service name="microsoft-ds"/>
<script id="smb-vuln-ms17-010" output="VULNERABLE: Remote Code Execution (ms17-010) IDs: CVE:CVE-2017-0143"/></port>
</ports></host></nmaprun>"""

FAKE_NMAP = r'''#!/usr/bin/env python3
import sys, os, json
args = sys.argv[1:]
out = args[args.index('-oX') + 1]
fx = os.environ['FAKE_NMAP_DIR']
name = 'discovery.xml' if '-sn' in args else 'ports-' + [a for a in args if a.count('.') == 3][-1] + '.xml'
open(out, 'w').write(open(os.path.join(fx, name)).read())
with open(os.path.join(fx, 'calls.jsonl'), 'a') as f:
    f.write(json.dumps(args) + '\n')
print('fake nmap done')
'''


class Yaml(unittest.TestCase):
    def test_roundtrip_tricky_values(self):
        d = {'version': '8.0', 'word': 'yes', 'null_word': 'null', 'colon': 'a: b', 'hash': 'x #y', 'n': 3, 'f': 9.8,
             'b': False, 'none': None, 'e': [], 'm': {}, 'text': 'one\ntwo: x # y\n', 'quote': 'say "hi"',
             'ports': [{'port': 22, 'cves': [{'id': 'CVE-1', 'cvss': None}], 'tags': ['a']}, {'port': 80, 'cves': []}],
             'deep': {'a': {'b': [1, [2, 3]]}}, 'cpe:/a:x': 1}
        self.assertEqual(yamlio.load(yamlio.dump(d, 'head\nline')), d)

    def test_hand_edited(self):
        t = '# c\nparallel: 4  # four\nname: my lab\nl: [a, "b, c", 3]\nurl: http://x/y#z\nt:\n  big: 60\nitems:\n- a\n- k: v\n  k2: [1]\n'
        self.assertEqual(yamlio.load(t), {'parallel': 4, 'name': 'my lab', 'l': ['a', 'b, c', 3], 'url': 'http://x/y#z',
                                          't': {'big': 60}, 'items': ['a', {'k': 'v', 'k2': [1]}]})

    def test_errors_name_the_line(self):
        with self.assertRaises(yamlio.YamlError) as e:
            yamlio.load('a: 1\n    b: 2\n')
        self.assertIn('line 2', str(e.exception))

    def test_recon_config_parses(self):
        cfg = recon.config()
        self.assertIn('{targets}', cfg['discover'])
        self.assertIn('{host}', cfg['ports'])
        self.assertTrue(cfg['score']['roles'])


class Parse(unittest.TestCase):
    def test_discovery(self):
        hosts, port_scan = recon.parse_nmap(DISCOVERY)
        self.assertFalse(port_scan)
        self.assertEqual([(h['ip'], h['up']) for h in hosts], [('10.10.10.5', True), ('10.10.10.9', True),
                                                               ('10.10.10.200', False), ('192.168.1.1', True)])
        self.assertEqual((hosts[0]['hostnames'], hosts[0]['vendor']), (['web.lab'], 'VMware'))

    def test_ports_vulners_and_scripts(self):
        (h,), port_scan = recon.parse_nmap(ports_xml('10.10.10.5'))
        self.assertTrue(port_scan)
        self.assertEqual([p['port'] for p in h['ports']], [22, 80])            # closed port dropped
        ssh = h['ports'][0]
        self.assertEqual([c['id'] for c in ssh['cves']], ['CVE-2016-6515', 'CVE-2016-6210'])   # worst first
        self.assertEqual(ssh['exploits'][0]['title'], 'EDB-ID:40136')
        self.assertEqual(h['os'], {'name': 'Linux 4.15', 'accuracy': 95})
        (dc,), _ = recon.parse_nmap(ports_xml('10.10.10.9'))
        self.assertEqual(dc['ports'][1]['cves'][0]['id'], 'CVE-2017-0143')     # from smb-vuln script text
        self.assertEqual(dc['ports'][1]['cves'][0]['source'], 'tool: nmap smb-vuln-ms17-010')

    def test_bad_xml(self):
        with self.assertRaises(recon.Fail) as e:
            recon.parse_nmap('<nmaprun><host>')
        self.assertEqual(e.exception.code, 6)

    def test_stealth_levels(self):
        normal, sneaky = recon.config(), recon.config('sneaky')
        self.assertEqual((normal['stealth'], normal['parallel']), ('normal', 4))
        self.assertEqual((sneaky['parallel'], sneaky['profile']['ports']), (1, '--top-ports 1000'))
        p = sneaky['profile']
        argv = recon.fill(sneaky['ports'], raw={'timing': p['timing'], 'ports': p['ports'], 'scripts': p['scripts']},
                          host='10.0.0.5', out='o.xml')
        self.assertEqual(argv, ['nmap', '-Pn', '-n', '-sV', '-T2', '--max-rate', '10', '--version-light', '--top-ports', '1000',
                                '--script=vulners', '10.0.0.5', '-oX', 'o.xml'])
        d = recon.fill(recon.config('paranoid')['discover'], raw={'timing': recon.config('paranoid')['profile']['discover_timing']},
                       targets=['10.0.0.0/24'], out='d.xml')
        self.assertIn('--randomize-hosts', d)
        self.assertEqual(d[d.index('--max-rate') + 1], '1')
        with self.assertRaises(recon.Fail) as e:
            recon.config('invisible')
        self.assertEqual(e.exception.code, 2)

    def test_fill_quotes_values(self):
        self.assertEqual(recon.fill('nmap {targets} -oX {out}', targets=['10.0.0.0/24', 'a;b'], out='x y.xml'),
                         ['nmap', '10.0.0.0/24', 'a;b', '-oX', 'x y.xml'])


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__('shutil').rmtree(self.t, True))
        (self.t / 'engagements' / 'lab').mkdir(parents=True)
        (self.t / 'engagements' / 'lab' / 'SCOPE.md').write_text(SCOPE, encoding='utf-8')
        fx = self.t / 'fx'
        fx.mkdir()
        (fx / 'discovery.xml').write_text(DISCOVERY)
        for ip in ('10.10.10.5', '10.10.10.9'):
            (fx / f'ports-{ip}.xml').write_text(ports_xml(ip))
        bin_ = self.t / 'bin'
        bin_.mkdir()
        (bin_ / 'nmap').write_text(FAKE_NMAP)
        (bin_ / 'nmap').chmod(0o755)
        env = {'PATH': f"{bin_}{os.pathsep}{os.environ['PATH']}", 'FAKE_NMAP_DIR': str(fx)}
        p = mock.patch.dict(os.environ, env)
        p.start()
        self.addCleanup(p.stop)
        r = mock.patch.object(recon, 'ROOT', self.t)
        r.start()
        self.addCleanup(r.stop)
        self.fx = fx
        self.eng = recon.Engagement('lab', root=self.t)
        self.cfg = recon.config('quiet')
        self.cfg['searchsploit'] = False

    def calls(self):
        return [json.loads(l) for l in (self.fx / 'calls.jsonl').read_text().splitlines()]

    def test_discover_scan_rank(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ins = recon.cmd_discover(self.eng, self.cfg)
        self.assertEqual(sorted(ins), ['10.10.10.5', '10.10.10.9'])
        self.assertIn('OUT OF SCOPE (not scanned): 192.168.1.1', out.getvalue())
        self.assertEqual(self.calls()[0][-3:-2], ['10.10.10.0/24'])            # only SCOPE targets go to nmap
        self.assertIn('--max-rate', self.calls()[0])                           # the stealth level reached nmap
        with contextlib.redirect_stdout(io.StringIO()):
            recon.cmd_scan(self.eng, self.cfg, [])
        scanned = sorted(c[c.index('-oX') - 1] for c in self.calls()[1:])
        self.assertEqual(scanned, ['10.10.10.5', '10.10.10.9'])                 # never the out-of-scope host
        web = self.eng.load_host('10.10.10.5')
        self.assertEqual((web['label'], web['status'], web['hostnames']), ('host-01', 'scanned', ['web.lab']))
        self.assertTrue(web['scans'][-1].startswith('hosts/10.10.10.5/scans/ports-'))
        idx = yamlio.read(self.eng.hosts_dir / 'index.yaml')
        self.assertEqual(idx['out_of_scope'], ['192.168.1.1'])
        dc = next(h for h in idx['hosts'] if h['ip'] == '10.10.10.9')
        self.assertEqual(dc['role'], 'domain controller')
        self.assertEqual([h['ip'] for h in idx['hosts']][0], '10.10.10.5')    # 7.8*4 + 15 + 4 + 5 = 55.2 vs DC 0+0+4+25 = 29
        self.assertEqual((web['score']['total'], web['tier'], idx['hosts'][0]['score']), (55.2, 'medium', 55.2))
        self.assertTrue((self.eng.hosts_dir / '10.10.10.5' / 'host.yaml').read_text().startswith('# Made by agent/recon.py'))

    def test_scan_refuses_out_of_scope(self):
        with self.assertRaises(recon.Fail) as e:
            recon.cmd_scan(self.eng, self.cfg, ['192.168.1.1'])
        self.assertEqual(e.exception.code, 4)
        self.assertFalse((self.fx / 'calls.jsonl').exists())                  # nothing ran

    def test_unauthorised_and_missing_tool(self):
        (self.t / 'engagements' / 'lab' / 'SCOPE.md').write_text(SCOPE.replace('yes' + chr(96), 'no' + chr(96)))
        with self.assertRaises(recon.Fail) as e:
            recon.Engagement('lab', root=self.t)
        self.assertEqual(e.exception.code, 4)
        with self.assertRaises(recon.Fail) as e:
            recon.run_logged(['no-such-scanner-xyz'], self.t / 'x.log', 5)
        self.assertIn('not installed', str(e.exception))

    def run_quiet(self, fn, *a):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as out:
            fn(*a)
        return out.getvalue()

    def test_research_task_has_no_addresses_and_merge(self):
        self.run_quiet(recon.cmd_discover, self.eng, self.cfg)
        self.run_quiet(recon.cmd_scan, self.eng, self.cfg, [])
        out = self.run_quiet(recon.cmd_research, self.eng, [])
        self.assertIn('--role host-researcher --task-file .worker/research-host-01.md --schema agent/schemas/host-research.json', out)
        task = (self.t / '.worker' / 'research-host-01.md').read_text()
        self.assertNotIn('10.10.10', task)
        self.assertNotIn('web.lab', task)
        self.assertIn('OpenSSH 7.2p2', task)
        self.assertIn('CVE-2016-6515', task)
        result = {'what': 'Ubuntu web server', 'used_for': 'intranet site', 'value': 4, 'value_reason': 'old ssh + apache',
                  'cves': [{'id': 'cve-2016-6515', 'service': '22/ssh', 'cvss': 7.8, 'in_kev': True, 'exploit_public': True,
                            'applies': 'yes', 'why': 'version in range', 'source': 'https://nvd.nist.gov/vuln/detail/CVE-2016-6515'},
                           {'id': 'CVE-2099-0001', 'service': '80/http', 'cvss': 9.9, 'in_kev': False, 'exploit_public': False,
                            'applies': 'yes', 'why': 'remembered', 'source': ''},
                           {'id': 'not-a-cve', 'source': 'x'}],
                  'exploits': [], 'attack_paths': ['ssh user enum'], 'sources': ['https://nvd.nist.gov/'], 'unsure': 'nothing'}
        (self.t / '.worker' / 'run-0123abcd.json').write_text(json.dumps(
            {'code': 0, 'worker': 'codex gpt-6-astra (high)', 'web_uses': ['{"query": "OpenSSH 7.2p2 CVE"}'], 'response': 'Here it is:\n' + chr(96) * 3 + 'json\n' + json.dumps(result) + '\n' + chr(96) * 3}))
        out = self.run_quiet(recon.cmd_merge, self.eng, self.cfg, 'host-01', '0123abcd')
        self.assertIn('1 CVE(s) kept, 2 dropped (no source)', out)
        h = self.eng.by_label('host-01')
        self.assertEqual((h['status'], h['research']['value'], h['research']['cves'][0]['id']), ('researched', 4, 'CVE-2016-6515'))
        self.assertEqual(h['tier'], 'big')                                     # 55.2 + kev 20 + value 4*5 = 95.2
        self.assertEqual(h['score']['total'], 95.2)
        self.assertEqual(self.eng.by_label('host-01')['score']['parts']['kev'], 20)
        # the same answer from a run that searched nothing: URL-sourced CVEs are unverified and do not count
        run = json.loads((self.t / '.worker' / 'run-0123abcd.json').read_text())
        run['web_uses'] = []
        (self.t / '.worker' / 'run-0123abce.json').write_text(json.dumps(run))
        out = self.run_quiet(recon.cmd_merge, self.eng, self.cfg, 'host-01', '0123abce')
        self.assertIn('1 UNVERIFIED', out)
        h = self.eng.by_label('host-01')
        self.assertIn('unverified', h['research']['cves'][0])
        self.assertEqual((h['score']['parts']['kev'], h['score']['total']), (0, 75.2))



class Leaks(unittest.TestCase):
    """Nothing that names the target goes into a research task; version numbers stay."""

    def test_task_scrubs_names_keeps_versions(self):
        import ipaddress
        h = {'ip': '10.10.10.5', 'label': 'host-07', 'hostnames': ['dc01.acme.local'], 'target_names': [], 'os': {'name': 'Windows'},
             'score': {'role': 'database'},
             'ports': [{'port': 1521, 'proto': 'tcp', 'service': 'oracle-tns', 'product': 'Oracle TNS listener', 'version': '10.2.0.4',
                        'extra': 'Domain: ACME, Site: Brussels-HQ', 'cpe': [],
                        'scripts': {'smb-os-discovery': 'Computer name: DC01 Domain name: acme.local FQDN: dc01.acme.local',
                                    'ssl-cert': 'Subject: commonName=portal.acme.com'}, 'cves': [], 'exploits': []},
                       {'port': 3000, 'proto': 'tcp', 'service': 'http', 'product': 'Node.js Express framework', 'version': '',
                        'extra': 'served by mail.acme.com for 10.10.10.77', 'cpe': [], 'scripts': {}, 'cves': [], 'exploits': []}]}
        t = recon.research_task(h, [ipaddress.ip_network('10.10.10.0/24')])
        for leak in ('acme', 'ACME', 'DC01', 'Brussels', 'portal', '10.10.10.5', '10.10.10.77'):
            self.assertNotIn(leak, t, leak)
        for keep in ('Oracle TNS listener 10.2.0.4', 'Node.js Express', 'host-07'):
            self.assertIn(keep, t, keep)


class HostnameScope(unittest.TestCase):
    def test_hostname_only_scope_scans_and_ptr_names_do_not_count(self):
        t = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__('shutil').rmtree(t, True))
        (t / 'engagements' / 'lab').mkdir(parents=True)
        (t / 'engagements' / 'lab' / 'SCOPE.md').write_text(SCOPE.replace(chr(96) + '10.10.10.0/24' + chr(96), chr(96) + 'box.lan' + chr(96)))
        eng = recon.Engagement('lab', root=t)
        xml = ('<nmaprun><host><status state="up"/><address addr="172.16.0.9" addrtype="ipv4"/>'
               '<hostnames><hostname name="box.lan" type="user"/></hostnames></host>'
               '<host><status state="up"/><address addr="172.16.0.10" addrtype="ipv4"/>'
               '<hostnames><hostname name="www.box.lan" type="PTR"/></hostnames></host></nmaprun>')
        found, _ = recon.parse_nmap(xml)
        ins, outs = recon.upsert(eng, found)
        self.assertEqual((ins, outs), (['172.16.0.9'], ['172.16.0.10']))     # a PTR name never puts a host in scope
        calls = []
        with mock.patch.object(recon, 'scan_one', lambda e, c, ip: (calls.append(ip), (ip, 'ok'))[1]), \
                mock.patch.object(recon, 'ROOT', t):
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                recon.cmd_scan(eng, {'parallel': 1, 'searchsploit': False}, [])
        self.assertEqual(calls, ['172.16.0.9'])


if __name__ == '__main__':
    unittest.main()
