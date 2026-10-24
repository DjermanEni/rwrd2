"""Точка входа: RWRD Character Bot.

Запуск:
    export BOT_TOKEN="123456:ABC-DEF..."
    python -m bot.main
"""

from telegram import Update
from telegram.ext import Application, CommandHandler

from bot.config import BOT_TOKEN, FORUM_URL, FORUM_ID, logger
from bot.handlers.common import start_cmd, help_cmd
from bot.handlers.char import char_cmd
from bot.handlers.list import list_cmd
from bot.handlers.atem import atem_cmd


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "Ошибка: не задан токен бота.\n"
            "Получите токен у @BotFather и задайте его через переменную окружения:\n"
            '    export BOT_TOKEN="123456:ABC-DEF..."'
        )
    logger.info("=" * 50)
    logger.info("Запуск RWRD Character Bot...")
    logger.info(f"Форум: {FORUM_URL}/viewforum.php?id={FORUM_ID}")
    logger.info("=" * 50)
    app = Application.builder().token(BOT_TOKEN).build()
    # Регистрируем команды в разных регистрах (Telegram сохраняет регистр в webhook/polling)
    for name, handler in (("char", char_cmd), ("list", list_cmd), ("atem", atem_cmd)):
        for variant in (name, name.capitalize(), name.upper()):
            app.add_handler(CommandHandler(variant, handler))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
