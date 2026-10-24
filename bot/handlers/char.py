"""Хендлер команды /char — поиск и вывод карточки персонажа."""

import io

from bot.config import logger
from bot.cache import search_character, characters_cache
from bot.parser import download_avatar
from bot.formatters import fmt
from bot.utils import split_message


async def char_cmd(update, ctx):
    if not ctx.args:
        await update.message.reply_text("⚠️ Укажите имя, позывной или номер из /list.\nПримеры: /char Leon Cross • /char Ghost • /char 7")
        return
    q = " ".join(ctx.args).strip('"').strip("'").strip()
    if not q:
        await update.message.reply_text("⚠️ Имя не может быть пустым.")
        return
    sm = await update.message.reply_text(f"🔍 Ищу: {q}...", parse_mode="Markdown")
    try:
        ch = await search_character(q)
        if ch:
            msg = fmt(ch)
            avatar = await download_avatar(ch.get("avatar_url"))
            if avatar:
                # подпись фото в Telegram не длиннее 1024 символов —
                # режем карточку по этому лимиту для первой части
                parts = split_message(msg, max_len=1024)
            else:
                parts = split_message(msg)
            try:
                if avatar:
                    await sm.delete()
                    await update.message.reply_photo(
                        photo=io.BytesIO(avatar), caption=parts[0],
                        parse_mode="Markdown", disable_web_page_preview=True,
                    )
                else:
                    await sm.edit_text(parts[0], parse_mode="Markdown", disable_web_page_preview=True)
            except Exception as me:
                # если Telegram не принял фото (битый файл и т.п.) — падаем на текстовый вариант
                logger.warning(f"Не удалось отправить аватар как фото: {me}")
                await update.message.reply_text(parts[0], parse_mode="Markdown", disable_web_page_preview=True)
            for p in parts[1:]:
                await update.message.reply_text(p, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await sm.edit_text(f'❌ Не найден: "{q}"\n\nЗагружено: {len(characters_cache)}\nИспользуйте /list — там есть номера персонажей, можно искать по номеру: /char 7')
    except Exception as e:
        logger.error(f"Search error: {e}")
        await sm.edit_text(f"⚠️ Ошибка. Загружено: {len(characters_cache)}")
