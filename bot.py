#!/usr/bin/env python3
"""Telegram-бот для парсинга анкет персонажей с форума Cyberpunk: Rewired.

Код разбит на логические модули в пакете bot/:
  bot/config.py         — настройки и логирование
  bot/forum_session.py  — HTTP-сессия с авторизацией на форуме
  bot/parser.py         — парсинг тем/анкет/аватаров
  bot/cache.py          — кэш персонажей и активных тем, поиск
  bot/utils.py          — экранирование Markdown, нарезка сообщений
  bot/formatters.py     — карточка персонажа
  bot/handlers/         — команды /start /help /char /list /atem
  bot/main.py           — точка входа

Запуск:  export BOT_TOKEN="..." && python bot.py
"""
from bot.main import main

if __name__ == "__main__":
    main()
