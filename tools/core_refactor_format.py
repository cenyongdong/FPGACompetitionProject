"""One-time source migration support; preserve C++ tokens and Python AST.

Uses only the existing Python runtime. This tool never changes frozen sources.
The token proof complements compilation and output regressions; it is not a
substitute for either. Preprocessor lines are retained verbatim.
"""
from pathlib import Path
import ast
import re

TOKEN = re.compile(
    r'(?P<directive>^[ \t]*\#[^\n]*(?:\\\n[^\n]*)*)'
    r'|(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)'
    r'|(?P<literal>(?:u8|u|U|L)?"(?:\\.|[^"\\])*"|(?:u|U|L)?\'(?:\\.|[^\'\\])*\')'
    r'|(?P<word>[A-Za-z_][A-Za-z_0-9]*|(?:\d[\w.]*(?:[eEpP][+-]?\d+)?)|\.\d[\w.]*)'
    r'|(?P<operator>::|->\*|->|\.\*|<<=|>>=|<=>|\.\.\.|==|!=|<=|>=|&&|\|\||\+\+|--|<<|>>|[+*/%&|^!-]=|.)',
    re.MULTILINE,
)


def tokens(source, comments=False):
    return [(m.lastgroup, m.group().strip()) for m in TOKEN.finditer(source)
            if not m.group().isspace() and (comments or m.lastgroup != 'comment')]


def format_cpp(source):
    """Expand statements without changing any non-comment source token."""
    stream = tokens(source, True)
    lines, current, braces = [], '', []
    indent = parens = 0
    previous = ''

    def emit():
        nonlocal current
        if current.strip():
            lines.append('    ' * indent + current.strip())
        current = ''

    def append(value):
        nonlocal current
        if not current:
            current = value
            return
        no_before = value in (')', ']', ',', ';', '.', '::', '->')
        no_after = previous in ('(', '[', '.', '::', '->', '!', '~', '++', '--')
        if value == '(' and (previous.isidentifier() or previous in ('>', '>>', ')', ']')) and previous not in ('if', 'for', 'while', 'switch', 'catch'):
            no_before = True
        if value == '[':
            no_before = True
        if previous and tokens(previous + value) != tokens(previous) + tokens(value):
            no_before = no_after = False
        current += ('' if no_before or no_after else ' ') + value

    for index, (kind, value) in enumerate(stream):
        following = stream[index + 1][1] if index + 1 < len(stream) else ''
        if kind == 'directive':
            emit()
            lines.append(value)
            previous = ''
            continue
        if kind == 'comment':
            if current:
                current += ' ' + value
                emit()
            else:
                lines.extend('    ' * indent + s.strip() for s in value.splitlines())
            previous = ''
            continue
        if value == '{':
            block = (previous in (')', ']', 'else', 'try', 'do', ';', '{', '}')
                     or re.search(r'\b(namespace|struct|class|enum)\b', current)
                     or re.search(r'\[[^\]]*\].*$', current)
                     or re.search(r'\)\s*(const|noexcept|override|final)\s*$', current))
            # Empty braces initialize data; they stay compact even in signatures.
            block = bool(block) and following != '}'
            braces.append((block, parens))
            if block:
                append(value)
                emit()
                indent += 1
            else:
                append(value)
        elif value == '}':
            block, base = braces.pop()
            if block:
                emit()
                indent -= 1
                current = '}'
                if following not in (';', ',', ')', 'else', 'catch', ']'):
                    emit()
                    if indent <= 2 and lines and lines[-1]:
                        lines.append('')
            else:
                append(value)
        elif value == ';':
            append(value)
            base = next((p for block, p in reversed(braces) if block), 0)
            if parens == base:
                emit()
        elif value == ':' and previous in ('public', 'private', 'protected'):
            current = current.rstrip() + ':'
            emit()
        else:
            append(value)
            if value == '(':
                parens += 1
            elif value == ')':
                parens -= 1
            # Wrap stream output without changing expression association.
            if value == '<<' and len(current) > 105:
                emit()
        previous = value
    emit()
    result = '\n'.join(lines).rstrip() + '\n'
    # Presentation-only polishing, applied outside literals/comments/directives.
    parts = []
    for match in TOKEN.finditer(result):
        if match.lastgroup in ('literal', 'comment', 'directive'):
            parts.append((match.start(), match.end()))
    start, polished = 0, []
    for first, last in [*parts, (len(result), len(result))]:
        code = result[start:first]
        code = re.sub(r'\b((?:std::[\w:]+|[\w:]+_cast|BackendOpRegisterHelper|Session::Create|add))\s+<\s+', r'\1<', code)
        code = re.sub(r'\s+>(\s*[(:,;])', r'>\1', code)
        code = re.sub(r'\b(char|void|float|double|int|Tensor|Pose|Config|Window|Result|std::[\w:]+)\s+([*&])\s+(?=\w)', r'\1\2 ', code)
        code = code.replace('{ }', '{}').replace('++ ', '++').replace('-- ', '--')
        polished.extend((code, result[first:last]))
        start = last
    result = ''.join(polished)
    before, after = tokens(source), tokens(result)
    if before != after:
        first = next((i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]), min(len(before), len(after)))
        raise AssertionError(f'C++ tokens changed at {first}: {before[max(0,first-3):first+4]} -> {after[max(0,first-3):first+4]}')
    return result


def format_python(source):
    tree = ast.parse(source)
    result = ast.unparse(tree) + '\n'
    assert ast.dump(tree, include_attributes=False) == ast.dump(ast.parse(result), include_attributes=False)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.files:
        source = path.read_text(encoding='utf-8')
        output = format_python(source) if path.suffix == '.py' else format_cpp(source)
        path.write_text(output, encoding='utf-8', newline='\n')
