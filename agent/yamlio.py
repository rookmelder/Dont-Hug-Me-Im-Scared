"""Tiny YAML for the files people read here (host.yaml, index.yaml, recon.yaml, findings). Standard library only.

dump() writes a plain subset: nested mappings, lists, strings (always "quoted", or a | block when they have line
breaks), numbers, true/false, null. load() reads that subset back, and is forgiving with hand edits: unquoted words,
# comments, [a, b] lists. Not a full YAML parser: anchors, tags, flow mappings and multi-document files are not read.
Workers never write these files; they return JSON and a script writes the YAML.
"""
import json
import re

_PLAIN_KEY = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.\-/]*$')


def _key(k):
    k = str(k)
    return k if _PLAIN_KEY.match(k) and k.lower() not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off', '~') else json.dumps(k)


def _scalar(v):
    if v is None:
        return 'null'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, (int, float)):
        return json.dumps(v)
    return json.dumps(str(v), ensure_ascii=False)   # a JSON string is a valid YAML double-quoted string


def _emit(v, indent, out):
    pad = ' ' * indent
    if isinstance(v, dict):
        if not v:
            out[-1] += ' {}'
            return
        for k, x in v.items():
            out.append(f'{pad}{_key(k)}:')
            _value(x, indent, out)
    elif isinstance(v, (list, tuple)):
        if not v:
            out[-1] += ' []'
            return
        for x in v:
            if isinstance(x, dict) and x:
                first = True
                for k, y in x.items():
                    out.append(f"{pad}{'- ' if first else '  '}{_key(k)}:")
                    _value(y, indent + 2, out)
                    first = False
            elif isinstance(x, (list, tuple)) and x:
                out.append(f'{pad}-')
                _emit(x, indent + 2, out)
            else:
                out.append(f'{pad}-')
                _value(x, indent, out)
    else:
        out[-1] += ' ' + _scalar(v)


def _value(x, indent, out):
    """The value after 'key:' (or '-'): inline for scalars/empty, on the next lines for the rest."""
    if isinstance(x, str) and '\n' in x.strip('\n'):
        out[-1] += ' |' + ('-' if not x.endswith('\n') else '')
        out.extend(' ' * (indent + 2) + line if line else '' for line in x.rstrip('\n').split('\n'))
    elif isinstance(x, dict) and x:
        _emit(x, indent + 2, out)
    elif isinstance(x, (list, tuple)) and x:
        _emit(x, indent + 2, out)
    else:
        _emit(x, indent, out)


def dump(data, header=''):
    """data (dict or list) -> YAML text. header: comment lines put on top (without the # )."""
    out = ['']   # a placeholder line the first value can attach to
    _emit(data, 0, out)
    body = out[1:] if out[0] == '' else [out[0].strip()]   # a bare scalar or empty root attaches to the placeholder
    top = [f'# {h}' if h else '#' for h in header.splitlines()]
    return '\n'.join(top + body) + '\n'


# --- load ---------------------------------------------------------------------------------------
class YamlError(ValueError):
    pass


def _strip_comment(line):
    """Drop a # comment that is not inside quotes."""
    q = None
    for i, ch in enumerate(line):
        if q:
            if ch == '\\' and q == '"':
                continue
            if ch == q:
                q = None
        elif ch in '"\'':
            q = ch
        elif ch == '#' and (i == 0 or line[i - 1] in ' \t'):
            return line[:i].rstrip()
    return line.rstrip()


def _parse_scalar(s):
    s = s.strip()
    if s == '' or s in ('~', 'null', 'Null', 'NULL'):
        return None
    if s.startswith('"'):
        try:
            return json.loads(s)
        except ValueError:
            raise YamlError(f'bad "quoted" string: {s}')
    if s.startswith("'") and s.endswith("'") and len(s) >= 2:
        return s[1:-1].replace("''", "'")
    if s in ('true', 'True', 'TRUE', 'yes', 'Yes', 'on'):
        return True
    if s in ('false', 'False', 'FALSE', 'no', 'No', 'off'):
        return False
    if s == '[]':
        return []
    if s == '{}':
        return {}
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1].strip()
        return [_parse_scalar(x) for x in _split_flow(inner)] if inner else []
    if re.fullmatch(r'[-+]?\d+', s):
        return int(s)
    if re.fullmatch(r'[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?', s):
        return float(s)
    return s


def _split_flow(s):
    parts, buf, q = [], '', None
    for ch in s:
        if q:
            buf += ch
            if ch == q:
                q = None
        elif ch in '"\'':
            q = ch
            buf += ch
        elif ch == ',':
            parts.append(buf)
            buf = ''
        else:
            buf += ch
    parts.append(buf)
    return [p.strip() for p in parts]


_QKEY = re.compile(r'^("(?:[^"\\]|\\.)*"|\'[^\']*\')\s*:(?:\s+(.*)|$)')
_PKEY = re.compile(r'^([^:#\s"\'][^:#]*?)\s*:(?:\s+(.*)|$)')


def _key_match(c):
    """'key: value' -> match (group 1 key, group 2 rest), else None. A "quoted: text" scalar is not a key line."""
    return (_QKEY if c[:1] in '"\'' else _PKEY).match(c)


def load(text):
    """YAML text (the subset above) -> dict / list / scalar. Raises YamlError with the line number."""
    raw = [l.replace('\t', '  ') for l in text.replace('\r\n', '\n').split('\n')]
    lines = []   # (indent, content, line number); block scalars are kept raw
    for n, l in enumerate(raw, 1):
        c = _strip_comment(l) if not l.lstrip().startswith('#') else ''
        lines.append((len(l) - len(l.lstrip(' ')), c.strip(), n, l))
    pos = [0]

    def skip():
        while pos[0] < len(lines) and not lines[pos[0]][1]:
            pos[0] += 1

    def block_scalar(indent, style):
        out, block_ind = [], None
        while pos[0] < len(lines):
            ind, c, n, l = lines[pos[0]]
            if l.strip() == '':
                out.append('')
                pos[0] += 1
                continue
            if ind <= indent:
                break
            block_ind = ind if block_ind is None else block_ind
            out.append(l[block_ind:])
            pos[0] += 1
        while out and out[-1] == '':
            out.pop()
        s = '\n'.join(out)
        return s if style.endswith('-') else s + '\n'

    def value_after(rest, indent, n):
        """What follows 'key:' or '- ': inline scalar, a block scalar, or a nested node on the next lines."""
        if rest and rest[0] in '|>':
            return block_scalar(indent, rest)
        if rest:
            return _parse_scalar(rest)
        skip()
        if pos[0] < len(lines) and (lines[pos[0]][0] > indent or (lines[pos[0]][0] == indent and lines[pos[0]][1].startswith('- '))):
            return node(lines[pos[0]][0])
        return None

    def node(indent):
        skip()
        if pos[0] >= len(lines):
            return None
        ind, c, n, _ = lines[pos[0]]
        if c.startswith('- ') or c == '-':
            out = []
            while pos[0] < len(lines):
                skip()
                if pos[0] >= len(lines):
                    break
                ind, c, n, _ = lines[pos[0]]
                if ind != indent or not (c.startswith('- ') or c == '-'):
                    if ind > indent:
                        raise YamlError(f'line {n}: unexpected indent')
                    break
                rest = c[1:].strip()
                pos[0] += 1
                if rest and _key_match(rest):
                    # "- key: value" starts a mapping inside the list; its other keys sit at indent + 2
                    lines.insert(pos[0], (indent + 2, rest, n, ' ' * (indent + 2) + rest))
                    out.append(node(indent + 2))
                else:
                    out.append(value_after(rest, indent, n))
            return out
        out = {}
        while pos[0] < len(lines):
            skip()
            if pos[0] >= len(lines):
                break
            ind, c, n, _ = lines[pos[0]]
            if ind < indent:
                break
            if ind > indent:
                raise YamlError(f'line {n}: unexpected indent')
            if c.startswith('- '):
                break
            m = _key_match(c)
            if not m:
                raise YamlError(f'line {n}: expected "key: value", got: {c}')
            k = m.group(1)
            k = _parse_scalar(k) if k[0] in '"\'' else k.strip()
            pos[0] += 1
            out[str(k)] = value_after((m.group(2) or '').strip(), indent, n)
        return out

    skip()
    if pos[0] >= len(lines):
        return {}
    first = lines[pos[0]]
    if not first[1].startswith('-') and not _key_match(first[1]):
        return _parse_scalar(first[1])
    result = node(first[0])
    skip()
    if pos[0] < len(lines):
        raise YamlError(f'line {lines[pos[0]][2]}: unexpected text: {lines[pos[0]][1]}')
    return result


def read(path):
    from pathlib import Path
    return load(Path(path).read_text(encoding='utf-8-sig'))


def write(path, data, header=''):
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(dump(data, header), encoding='utf-8')
    tmp.replace(p)   # never a half-written file
