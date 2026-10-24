"""Хендлеры /start и /help."""


async def start_cmd(update, ctx):
    await update.message.reply_text(
        "Привет! Я бот-помощник участников CyberPunk Rewired. "
        "Если ты не ковбой, я всё тебе расскажу: "
        "Воспользуйся /help для получения списка команд"
    )


async def help_cmd(update, ctx):
    await update.message.reply_text(
        "🤖 *Помощь*\n\n"
        "/char `Имя/Позывной/Номер` — найти анкету (примеры: `/char Маттиас Райндт`, `/char Raven`, `/char 7`)\n"
        "/list — таблица персонажей: № / Имя Фамилия / Позывной / ссылка на анкету\n"
        "/atem — активные темы\n"
        "/help — справка\n\n"
        "📌 https://rwrd.rusff.me/viewforum.php?id=25",
        parse_mode="Markdown",
    )
