"""Presentation-only wrapping with token/AST checks; no frozen file writes."""
from pathlib import Path
import ast
import io
import re
import tokenize
from core_refactor_format import TOKEN, tokens

ROOT = Path(__file__).resolve().parents[1]


def python_wrap(source):
    output = []
    for line in source.splitlines():
        if len(line) < 115 or line.lstrip().startswith('#'):
            output.append(line)
            continue
        try:
            pieces = list(tokenize.generate_tokens(io.StringIO(line + '\n').readline))
        except tokenize.TokenError:
            output.append(line)
            continue
        depth, begin, cuts = 0, 0, []
        for item in pieces:
            if item.type != tokenize.OP:
                continue
            if item.string in '([{':
                depth += 1
            elif item.string in ')]}':
                depth -= 1
            elif item.string == ',' and depth > 0 and item.end[1] - begin > 85:
                cuts.append(item.end[1])
                begin = item.end[1]
        indentation = ' ' * (len(line) - len(line.lstrip()) + 4)
        begin = 0
        for end in cuts:
            output.append((line[begin:end] if begin == 0 else indentation + line[begin:end].lstrip()).rstrip())
            begin = end
        output.append((line[begin:] if begin == 0 else indentation + line[begin:].lstrip()).rstrip())
    result = re.sub(r'\n{4,}', '\n\n\n', '\n'.join(output) + '\n')
    assert ast.dump(ast.parse(source)) == ast.dump(ast.parse(result))
    return result


def cpp_wrap(source):
    # Token-preserving spacing outside string literals and comments.
    protected = [(m.start(), m.end()) for m in TOKEN.finditer(source)
                 if m.lastgroup in ('literal', 'comment', 'directive')]
    output, begin = [], 0
    for first, last in [*protected, (len(source), len(source))]:
        code = source[begin:first]
        code = re.sub(r'\b(bool|int|float|double|char|uint\d+_t|size_t|Pose|AccessUnit|OwnedFrame|Tensor|\d+) +(?=>)', r'\1', code)
        code = re.sub(r'\b([\w:]+) +& +(?=[a-zA-Z_]\w*\s*[,)=;])', r'\1& ', code)
        code = code.replace('=[', '= [').replace(',[', ', [')
        output.extend((code, source[first:last]))
        begin = last
    result = ''.join(output)
    # Separate include groups from the following namespace/body.
    result = re.sub(r'(?m)(^#include[^\n]+\n)(?=namespace|using|int main)', r'\1\n', result)
    assert tokens(source) == tokens(result)
    return result


def main():
    folders = [ROOT / 'software/core', ROOT / 'software/demo']
    skip = {'collect_final.py', 'finish_reboot_audit.py', 'reboot_once.py', 'review.py', 'review_video.py', 'native_render.py'}
    for folder in folders:
        for path in folder.rglob('*'):
            if not path.is_file() or path.name in skip or '__pycache__' in path.parts:
                continue
            source = path.read_text(encoding='utf-8') if path.suffix in ('.cpp', '.hpp', '.py') else None
            if source is not None:
                result = python_wrap(source) if path.suffix == '.py' else cpp_wrap(source)
                path.write_text(result, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
