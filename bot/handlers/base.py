from aiogram import Router, types
from aiogram.filters import Command
from bot.ai.gemini import process_message
from bot.database.models import (
    get_or_create_user, save_wish, update_wish, delete_wish, save_date, save_note, save_gift, complete_wish,
    get_user_context, get_wishes_formatted, get_notes_formatted, get_dates_formatted, get_gift_stats
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой помощник по подаркам для Марии. "
                         "Я помогу тебе помнить её желания, важные даты и планировать сюрпризы.\n\n"
                         "Используй /help чтобы узнать, что я умею.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>Как я могу помочь:</b>\n\n"
        "🎁 <b>Желания:</b> Напиши что она хочет.\n"
        "<i>'Мария хочет новые кроссовки'</i>\n\n"
        "📅 <b>Даты:</b> Напиши когда праздник.\n"
        "<i>'Наш юбилей 12 октября'</i>\n\n"
        "📝 <b>Заметки:</b> Расскажи о её вкусах.\n"
        "<i>'Она любит пионы'</i>\n\n"
        "✅ <b>Подарки:</b> Отметь когда что-то подарил.\n"
        "<i>'Подарил ей букет сегодня'</i>\n\n"
        "💡 <b>Советы:</b> Спроси меня что подарить.\n"
        "<i>'Что подарить на др?'</i>\n\n"
        "🛠 <b>CRUD:</b> Ты можешь изменять или удалять желания.\n"
        "<i>'Удали желание с ID 5' или 'Измени цену для платья на 5000'</i>\n\n"
        "<b>Меню команд:</b>\n"
        "/wishes — Список желаний\n"
        "/notes — Заметки\n"
        "/dates — Важные даты\n"
        "/stats — Статистика подарков"
    )
    await message.answer(help_text)

@router.message(Command("wishes"))
async def cmd_wishes(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_wishes_formatted(user['id'])
    await message.answer(f"<b>Желания Марии:</b>\n\n{text}")

@router.message(Command("notes"))
async def cmd_notes(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_notes_formatted(user['id'])
    await message.answer(f"<b>Заметки о предпочтениях:</b>\n\n{text}")

@router.message(Command("dates"))
async def cmd_dates(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_dates_formatted(user['id'])
    await message.answer(f"<b>Важные даты:</b>\n\n{text}")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_gift_stats(user['id'])
    await message.answer(text)

@router.message()
async def handle_text(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    context = await get_user_context(user['id'])
    
    ai_response = await process_message(user['id'], message.text, context)
    
    actions = ai_response.get("actions", [])
    reply_text = ai_response.get("reply", "")

    for action in actions:
        at = action.get("type")
        if at == "save_wish":
            await save_wish(user['id'], action.get('wish', {}))
        elif at == "update_wish":
            w_id = action.get('wish_id')
            if w_id:
                await update_wish(user['id'], w_id, action.get('wish', {}))
        elif at == "delete_wish":
            w_id = action.get('wish_id')
            if w_id:
                await delete_wish(user['id'], w_id)
        elif at == "save_date":
            await save_date(user['id'], action.get('date', {}))
        elif at == "save_note":
            await save_note(user['id'], action.get('note', {}))
        elif at == "save_gift":
            await save_gift(user['id'], action.get('gift', {}))
        elif at == "complete_wish":
            cw_id = action.get('complete_wish_id')
            if cw_id:
                await complete_wish(user['id'], cw_id)
        elif at == "show_stats":
            stats = await get_gift_stats(user['id'])
            reply_text += f"\n\n{stats}"
        elif at == "list_wishes":
            w = await get_wishes_formatted(user['id'])
            reply_text += f"\n\n<b>Список желаний:</b>\n{w}"
        elif at == "list_notes":
            n = await get_notes_formatted(user['id'])
            reply_text += f"\n\n<b>Заметки:</b>\n{n}"
        elif at == "list_dates":
            d = await get_dates_formatted(user['id'])
            reply_text += f"\n\n<b>Важные даты:</b>\n{d}"

    await message.answer(reply_text or "Я всё запомнил!")
