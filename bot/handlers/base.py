from aiogram import Router, types
from aiogram.filters import Command
from bot.ai.gemini import process_message
from bot.database.models import (
    get_or_create_user, save_wish, save_date, save_note, 
    get_user_context, get_wishes_formatted, get_notes_formatted
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой помощник по подаркам для Марии. "
                         "Можешь отправлять желания списком, спрашивать что она хочет, или просто делиться заметками. "
                         "Я всё запомню!\n\nИспользуй /help чтобы узнать подробнее.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>Как я могу помочь:</b>\n\n"
        "🎁 <b>Желания:</b> Просто напиши что Мария хочет (можно списком). Я всё запишу.\n"
        "<i>Пример: 'Она хочет новые кроссовки и фен'</i>\n\n"
        "📅 <b>Даты:</b> Напиши важную дату.\n"
        "<i>Пример: 'День рождения Марии 5 мая'</i>\n\n"
        "📝 <b>Заметки:</b> Любые факты или предпочтения.\n"
        "<i>Пример: 'Ей очень понравились цветы в том магазине' или 'Она не любит горький шоколад'</i>\n\n"
        "💡 <b>Советы:</b> Спроси меня что подарить.\n"
        "<i>Пример: 'Что подарить на др при бюджете 10к?'</i>\n\n"
        "📋 <b>Просмотр:</b> Попроси показать списки.\n"
        "<i>Пример: 'Покажи все желания' или 'Какие есть заметки?'</i>"
    )
    await message.answer(help_text)

@router.message()
async def handle_text(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    context = await get_user_context(user['id'])
    
    ai_response = await process_message(user['id'], message.text, context)
    
    actions = ai_response.get("actions", [])
    reply_text = ai_response.get("reply", "")

    # Execute actions
    for action in actions:
        action_type = action.get("type")
        if action_type == "save_wish":
            await save_wish(user['id'], action.get('wish', {}))
        elif action_type == "save_date":
            await save_date(user['id'], action.get('date', {}))
        elif action_type == "save_note":
            await save_note(user['id'], action.get('note', {}))
        elif action_type == "list_wishes":
            wishes_list = await get_wishes_formatted(user['id'])
            reply_text += f"\n\n<b>Список желаний:</b>\n{wishes_list}"
        elif action_type == "list_notes":
            notes_list = await get_notes_formatted(user['id'])
            reply_text += f"\n\n<b>Заметки:</b>\n{notes_list}"
        elif action_type == "list_all":
            wishes_list = await get_wishes_formatted(user['id'])
            notes_list = await get_notes_formatted(user['id'])
            reply_text += f"\n\n<b>Список желаний:</b>\n{wishes_list}\n\n<b>Заметки:</b>\n{notes_list}"

    await message.answer(reply_text or "Я всё запомнил!")
