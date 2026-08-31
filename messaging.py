"""
Отправка карточек с картинкой.

Telegram ограничивает подпись к фото 1024 символами, а обычное сообщение — 4096.
Если текст не влезает в подпись, отправляем фото отдельно, а текст — сообщением.
"""

CAPTION_LIMIT = 1024
MESSAGE_LIMIT = 4096


def tg_length(text: str) -> int:
    """Длина в кодовых единицах UTF-16 — именно так считает Telegram."""
    return len(text.encode("utf-16-le")) // 2


def fits_caption(text: str) -> bool:
    return tg_length(text) <= CAPTION_LIMIT


def split_text(text: str, limit: int = MESSAGE_LIMIT) -> list[str]:
    if tg_length(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if tg_length(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while tg_length(line) > limit:
            cut = limit
            while cut > 0 and tg_length(line[:cut]) > limit:
                cut -= 1
            chunks.append(line[:cut])
            line = line[cut:]
        current = line
    if current:
        chunks.append(current)
    return chunks


async def answer_card(message, text: str, reply_markup=None, photo=None):
    """Ответ пользователю карточкой: фото с подписью либо фото + текст."""
    if photo:
        if fits_caption(text):
            try:
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
                return
            except Exception:
                pass
        else:
            try:
                await message.answer_photo(photo=photo, caption=None)
            except Exception:
                pass

    chunks = split_text(text)
    for i, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=reply_markup if i == len(chunks) - 1 else None,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


async def send_card(bot, chat_id: int, text: str, reply_markup=None, photo=None):
    """То же самое для рассылок через bot.send_*."""
    if photo:
        if fits_caption(text):
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
                return
            except Exception:
                pass
        else:
            try:
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=None)
            except Exception:
                pass

    chunks = split_text(text)
    for i, chunk in enumerate(chunks):
        await bot.send_message(
            chat_id=chat_id,
            text=chunk,
            reply_markup=reply_markup if i == len(chunks) - 1 else None,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
