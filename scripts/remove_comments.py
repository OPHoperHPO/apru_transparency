import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
HASH_EXTS = {'.py', '.pyw', '.pyi', '.pyx', '.pxd', '.pxi', '.rpy', '.cfg', '.ini', '.conf', '.txt', '.rst', '.yml', '.yaml', '.env', '.sh'}
JS_EXTS = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}
CSS_EXTS = {'.css', '.scss', '.sass', '.less'}
HTML_EXTS = {'.html', '.htm'}
VUE_EXTS = {'.vue'}
HASH_COMMENT_PATTERN = re.compile(
    r"(?:(?<!\w)(?:[rRbBuUfF]{1,3})?'''[\s\S]*?'''|(?<!\w)(?:[rRbBuUfF]{1,3})?\"\"\"[\s\S]*?\"\"\"|(?<!\w)(?:[rRbBuUfF]{1,3})?'(?:\\.|[^\\'])*'|(?<!\w)(?:[rRbBuUfF]{1,3})?\"(?:\\.|[^\\\"])*\")"
    r"|(?P<comment>\#[^\n]*)"
)
HTML_COMMENT_PATTERN = re.compile(r'<!--[\s\S]*?-->', re.MULTILINE)
CSS_COMMENT_PATTERN = re.compile(r'/\*[\s\S]*?\*/')
def remove_hash_comments(text: str) -> str:
    shebang = ''
    rest = text
    if text.startswith('#!'):
        newline_idx = text.find('\n')
        if newline_idx == -1:
            return text
        shebang = text[:newline_idx + 1]
        rest = text[newline_idx + 1:]
    def _replacer(match: re.Match) -> str:
        if match.group('comment') is not None:
            return ''
        return match.group(0)
    cleaned = HASH_COMMENT_PATTERN.sub(_replacer, rest)
    cleaned_lines = [line.rstrip() for line in cleaned.splitlines()]
    while cleaned_lines and cleaned_lines[0] == '':
        cleaned_lines.pop(0)
    cleaned_text = '\n'.join(cleaned_lines)
    if cleaned_lines:
        cleaned_text += '\n'
    elif rest.endswith('\n'):
        cleaned_text = ''
    if shebang:
        cleaned_text = shebang + cleaned_text
    return cleaned_text
def remove_js_comments(text: str) -> str:
    result_chars = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == '"' or ch == "'":
            quote = ch
            result_chars.append(ch)
            i += 1
            while i < length:
                curr = text[i]
                result_chars.append(curr)
                if curr == '\\':
                    i += 2
                    if i <= length:
                        continue
                    break
                if curr == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == '`':
            result_chars.append(ch)
            i += 1
            while i < length:
                curr = text[i]
                result_chars.append(curr)
                if curr == '\\':
                    i += 2
                    if i <= length:
                        continue
                    break
                if curr == '`':
                    i += 1
                    break
                if curr == '$' and i + 1 < length and text[i + 1] == '{':
                    i += 2
                    result_chars.append('{')
                    brace_depth = 1
                    while i < length and brace_depth:
                        curr = text[i]
                        if curr == '\\':
                            result_chars.append(curr)
                            if i + 1 < length:
                                result_chars.append(text[i + 1])
                                i += 2
                                continue
                            else:
                                i += 1
                                break
                        if curr == '{':
                            brace_depth += 1
                        elif curr == '}':
                            brace_depth -= 1
                            if brace_depth == 0:
                                result_chars.append(curr)
                                i += 1
                                break
                        result_chars.append(curr)
                        i += 1
                    continue
                i += 1
            continue
        if ch == '/':
            if i + 1 < length:
                nxt = text[i + 1]
                if nxt == '/':
                    i += 2
                    while i < length and text[i] not in '\r\n':
                        i += 1
                    continue
                if nxt == '*':
                    i += 2
                    while i + 1 < length and not (text[i] == '*' and text[i + 1] == '/'):
                        i += 1
                    i += 2
                    continue
        result_chars.append(ch)
        i += 1
    return ''.join(result_chars)
def remove_css_comments(text: str) -> str:
    return CSS_COMMENT_PATTERN.sub('', text)
def remove_html_comments(text: str) -> str:
    return HTML_COMMENT_PATTERN.sub('', text)
def process_vue(text: str) -> str:
    def replace_script(match: re.Match) -> str:
        open_tag, content, close_tag = match.groups()
        return f"{open_tag}{remove_js_comments(content)}{close_tag}"
    def replace_style(match: re.Match) -> str:
        open_tag, content, close_tag = match.groups()
        return f"{open_tag}{remove_css_comments(content)}{close_tag}"
    script_pattern = re.compile(r'(<script\b[^>]*>)([\s\S]*?)(</script>)', re.IGNORECASE)
    style_pattern = re.compile(r'(<style\b[^>]*>)([\s\S]*?)(</style>)', re.IGNORECASE)
    text = script_pattern.sub(replace_script, text)
    text = style_pattern.sub(replace_style, text)
    text = remove_html_comments(text)
    return text
def is_hash_style_file(path: Path, suffix: str) -> bool:
    name = path.name.lower()
    if suffix in HASH_EXTS:
        return True
    if name.startswith('.env'):
        return True
    if name == 'dockerfile' or name.endswith('.dockerfile'):
        return True
    return False
def should_process(path: Path) -> bool:
    suffix = path.suffix.lower()
    return (
        is_hash_style_file(path, suffix)
        or suffix in JS_EXTS
        or suffix in CSS_EXTS
        or suffix in HTML_EXTS
        or suffix in VUE_EXTS
    )
def remove_comments_in_file(path: Path) -> None:
    suffix = path.suffix.lower()
    try:
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return
    original = content
    if is_hash_style_file(path, suffix):
        content = remove_hash_comments(content)
    if suffix in JS_EXTS:
        content = remove_js_comments(content)
    if suffix in CSS_EXTS:
        content = remove_css_comments(content)
    if suffix in HTML_EXTS:
        content = remove_html_comments(content)
    if suffix in VUE_EXTS:
        content = process_vue(content)
    if content != original:
        path.write_text(content, encoding='utf-8')
def main() -> None:
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        if path.name.startswith('.git'):
            continue
        if 'node_modules' in path.parts or '.venv' in path.parts or '__pycache__' in path.parts:
            continue
        if should_process(path):
            remove_comments_in_file(path)
if __name__ == '__main__':
    main()
