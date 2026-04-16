from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from bot.ai.gemini import process_message
from bot.config import ADMIN_USERNAME
from bot.database.models import (
    get_or_create_user, save_wish, update_wish, delete_wish, save_date, update_date, delete_date, 
    save_note, update_note, delete_note, save_gift, complete_wish,
    get_user_context, get_wishes_raw, get_notes_raw, get_dates_raw, get_gift_stats
)
from bot.keyboards.inline import get_items_keyboard

router = Router()

def is_admin(user: types.User):
    return user.username and user.username.lower() == ADMIN_USERNAME.lower()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user):
        return await message.answer("Извините, этот бот только для личного пользования администратора.")
    
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой помощник по подаркам для Марии.\n\n"
                         "Ты можешь управлять желаниями, датами и заметками через команды, меню или просто общаясь со мной.\n"
                         "Используй /help чтобы увидеть все возможности.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    if not is_admin(message.from_user): return
    help_text = (
        "<b>Интерактивное управление:</b>\n"
        "/wishes — Список желаний\n"
        "/dates — Важные даты\n"
        "/notes — Заметки\n"
        "<i>В списках можно нажать на элемент, чтобы изменить или удалить его.</i>\n\n"
        "<b>Быстрое добавление (команды):</b>\n"
        "/wishes_add Название | Описание | Цена\n"
        "/dates_add Название | ГГГГ-ММ-ДД\n"
        "/notes_add Текст\n\n"
        "<b>Другое:</b>\n"
        "/stats — Статистика подарков\n\n"
        "<i>Ты также можешь просто писать мне сообщения, и я сам пойму, что нужно сделать!</i>"
    )
    await message.answer(help_text)

# --- COMMANDS FOR LISTS (Inline) ---
@router.message(Command("wishes"))
async def cmd_wishes(message: types.Message):
    if not is_admin(message.from_user): return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    items = await get_wishes_raw(user['id'])
    await message.answer("<b>Список желаний Марии:</b>", reply_markup=get_items_keyboard(items, "wish"))

@router.message(Command("dates"))
async def cmd_dates(message: types.Message):
    if not is_admin(message.from_user): return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    items = await get_dates_raw(user['id'])
    await message.answer("<b>Важные даты:</b>", reply_markup=get_items_keyboard(items, "date"))

@router.message(Command("notes"))
async def cmd_notes(message: types.Message):
    if not is_admin(message.from_user): return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    items = await get_notes_raw(user['id'])
    await message.answer("<b>Заметки:</b>", reply_markup=get_items_keyboard(items, "note"))

# --- QUICK ADD COMMANDS ---
@router.message(Command("wishes_add"))
async def cmd_wishes_add(message: types.Message, command: CommandObject):
    if not is_admin(message.from_user): return
    if not command.args: return await message.answer("Использование: /wishes_add Название | Описание | Цена")
    parts = [p.strip() for p in command.args.split("|")]
    wish_data = {"title": parts[0], "description": parts[1] if len(parts) > 1 else None, "price_range": parts[2] if len(parts) > 2 else None}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_wish(user['id'], wish_data)
    await message.answer(f"✅ Добавлено: {wish_data['title']}")

@router.message(Command("dates_add"))
async def cmd_dates_add(message: types.Message, command: CommandObject):
    if not is_admin(message.from_user): return
    if not command.args: return await message.answer("Использование: /dates_add Название | ГГГГ-ММ-ДД")
    parts = [p.strip() for p in command.args.split("|")]
    if len(parts) < 2: return await message.answer("Нужно название и дата.")
    date_data = {"title": parts[0], "event_date": parts[1]}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_date(user['id'], date_data)
    await message.answer(f"✅ Добавлена дата: {date_data['title']}")

@router.message(Command("notes_add"))
async def cmd_notes_add(message: types.Message, command: CommandObject):
    if not is_admin(message.from_user): return
    if not command.args: return await message.answer("Использование: /notes_add Текст")
    note_data = {"content": command.args.strip()}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_note(user['id'], note_data)
    await message.answer("✅ Заметка сохранена")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user): return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_gift_stats(user['id'])
    await message.answer(text)

@router.message()
async def handle_text(message: types.Message):
    if not is_admin(message.from_user):
        return await message.answer("Извините, у вас нет доступа к этому боту.")
    
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    context = await get_user_context(user['id'])
    ai_response = await process_message(user['id'], message.text, context)
    actions = ai_response.get("actions", [])
    reply_text = ai_response.get("reply", "")
    for action in actions:
        at = action.get("type")
        if at == "save_wish": await save_wish(user['id'], action.get('wish', {}))
        elif at == "update_wish":
            w_id = action.get('wish_id')
            if w_id: await update_wish(user['id'], w_id, action.get('wish', {}))
        elif at == "delete_wish":
            w_id = action.get('wish_id')
            if w_id: await delete_wish(user['id'], w_id)
        elif at == "save_date": await save_date(user['id'], action.get('date', {}))
        elif at == "save_note": await save_note(user['id'], action.get('note', {}))
        elif at == "save_gift": await save_gift(user['id'], action.get('gift', {}))
        elif at == "complete_wish":
            cw_id = action.get('complete_wish_id')
            if cw_id: await complete_wish(user['id'], cw_id)
        elif at == "show_stats":
            stats = await get_gift_stats(user['id'])
            reply_text += f"\n\n{stats}"
        elif at == "list_wishes":
            wishes = await get_wishes_raw(user['id'])
            await message.answer("<b>Список желаний Марии:</b>", reply_markup=get_items_keyboard(wishes, "wish"))
            return
        elif at == "list_notes":
            notes = await get_notes_raw(user['id'])
            await message.answer("<b>Заметки:</b>", reply_markup=get_items_keyboard(notes, "note"))
            return
        elif at == "list_dates":
            dates = await get_dates_raw(user['id'])
            await message.answer("<b>Важные даты:</b>", reply_markup=get_items_keyboard(dates, "date"))
            return
    await message.answer(reply_text or "Я всё запомнил!")
