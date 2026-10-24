"""Утилиты: экранирование MarkdownV2, нарезка длинных сообщений."""

# Полный набор спецсимволов MarkdownV2 (по docs.telegram.org):
#   _ * [ ] ( ) ~ ` > # + - = | { } . !
_MD_V2_SPECIALS = "\\_*[]()~`>#+-=|{}.!"


def esc_md(text):
    """Экранирует спецсимволы MarkdownV2, чтобы пользовательский текст не ломал разметку."""
    if not text:
        return ""
    out = []
    for ch in text:
        if ch in _MD_V2_SPECIALS:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def md_link(title, url):
    """Ссылка MarkdownV2: URL экранируется по правилам «внутри ссылки»
    (спецсимволы \\ ( ) экранируются, остальные — в том числе '.', '=' — нет)."""
    safe_url = url.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return f"[{esc_md(title)}]({safe_url})"


def split_message(text, max_len=4000):
    """Режет текст на части не длиннее max_len (учитывая переносы строк)."""
    if len(text) <= max_len:
        return [text]
    parts, cur = [], ""
    for line in text.split('\n'):
        # если одна строка длиннее лимита — режем её по символьным блокам
        while len(line) > max_len:
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:max_len])
            line = line[max_len:]
        if len(cur) + len(line) + 1 > max_len:
            if cur:
                parts.append(cur)
            cur = line + '\n'
        else:
            cur += line + '\n'
    if cur:
        parts.append(cur)
    return parts
