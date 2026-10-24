"""Форматирование карточки персонажа для сообщения в Telegram (Markdown)."""


def fmt(ch):
    """Собирает текстовую карточку персонажа из распарсенных полей."""
    if not ch:
        return None
    L = []
    n = ch.get('name', 'Неизвестно')
    L.append(f"📋 *{n}*")
    if ch.get("moniker") and ch["moniker"] != n:
        L.append(f"🏷 Позывной: _{ch['moniker']}_")
    if ch.get("dob") and ch["dob"] != "Неизвестно":
        L.append(f"📅 Дата рождения: {ch['dob']}")
    if ch.get("occupation") and ch["occupation"] != "Неизвестно":
        L.append(f"💼 Занятие: {ch['occupation']}")
    if ch.get("loyalty") and ch["loyalty"] != "Неизвестно":
        L.append(f"🤝 Лояльность: {ch['loyalty']}")
    if ch.get("year"):
        L.append(f"🕐 Таймлайн: {ch['year']}")
    if ch.get("implants") and len(ch["implants"]) > 0:
        L.append("")
        L.append("🦾 *Импланты:*")
        L.append(", ".join(ch["implants"]))
    if ch.get("skills") and len(ch["skills"]) > 0:
        L.append("")
        L.append("⚡ *Навыки:*")
        for s in ch["skills"]:
            L.append(f"• {s}")
    if ch.get("bio"):
        L.append("")
        L.append("📖 *Биография:*")
        L.append(ch["bio"])
    if ch.get("topic_url"):
        L.append("")
        L.append(f"🔗 [Открыть на форуме]({ch['topic_url']})")
    return "\n".join(L)
