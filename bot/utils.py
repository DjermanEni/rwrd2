"""Утилиты: экранирование Markdown, нарезка длинных сообщений."""


def esc_md(text):
    """Экранирует спецсимволы Markdown, чтобы пользовательский текст не ломал разметку."""
    if not text:
        return ""
    for ch in ("\\", "*", "_", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


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
