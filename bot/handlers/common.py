"""Хендлеры /start и /help."""

HELP_TEXT = (
    "🤖 Помощь\n\n"
    "/char Имя/Позывной/Номер — найти анкету\n"
    "   примеры: /char Маттиас Райндт • /char Raven • /char 7\n"
    "/list — список персонажей: № / Имя Фамилия / Позывной / ссылка на анкету\n"
    "/atem — активные темы форума\n"
    "/help — эта справка\n\n"
    "Раздел анкет: https://rwrd.rusff.me/viewforum.php?id=25"
)


async def start_cmd(update, ctx):
    await update.message.reply_text(
        "Привет! Я бот-помощник участников CyberPunk Rewired. "
        "Если ты не ковбой, я всё тебе расскажу: "
        "Воспользуйся /help для получения списка команд"
    )


async def help_cmd(update, ctx):
    await update.message.reply_text(HELP_TEXT)
