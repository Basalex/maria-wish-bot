from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from bot.ai.gemini import process_message
from bot.database.models import (
    get_or_create_user, save_wish, update_wish, delete_wish, save_date, update_date, delete_date, 
    save_note, update_note, delete_note, save_gift, complete_wish,
    get_user_context, get_wishes_formatted, get_notes_formatted, get_dates_formatted, get_gift_stats
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой помощник по подаркам для Марии.\n\n"
                         "Ты можешь управлять желаниями, датами и заметками через команды или просто общаясь со мной.\n"
                         "Используй /help чтобы увидеть все возможности.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>🎁 Желания:</b>\n"
        "/wishes — Список\n"
        "/wishes_add Название | Описание | Цена\n"
        "/wishes_edit ID Поле Значение (поле: title, desc, price, link)\n"
        "/wishes_delete ID\n"
        "/wishes_done ID\n\n"
        "<b>📅 Даты:</b>\n"
        "/dates — Список\n"
        "/dates_add Название | ГГГГ-ММ-ДД | [дни_напоминания]\n"
        "/dates_edit ID Поle Значение (поле: title, date, rem)\n"
        "/dates_delete ID\n\n"
        "<b>📝 Заметки:</b>\n"
        "/notes — Список\n"
        "/notes_add Содержание | [категория]\n"
        "/notes_edit ID Поле Значение (поле: text, cat)\n"
        "/notes_delete ID\n\n"
        "<b>📊 Прочее:</b>\n"
        "/stats — Статистика подарков"
    )
    await message.answer(help_text)

# --- WISHES ---
@router.message(Command("wishes"))
async def cmd_wishes(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_wishes_formatted(user['id'])
    await message.answer(f"<b>Желания Марии:</b>\n\n{text}")

@router.message(Command("wishes_add"))
async def cmd_wishes_add(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /wishes_add Название | Описание | Цена")
    parts = [p.strip() for p in command.args.split("|")]
    wish_data = {"title": parts[0], "description": parts[1] if len(parts) > 1 else None, "price_range": parts[2] if len(parts) > 2 else None}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_wish(user['id'], wish_data)
    await message.answer(f"✅ Добавлено желание: {wish_data['title']}")

@router.message(Command("wishes_edit"))
async def cmd_wishes_edit(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /wishes_edit ID Поле Значение")
    parts = command.args.split(maxsplit=2)
    if len(parts) < 3: return await message.answer("Недостаточно аргументов.")
    wish_id, field, value = int(parts[0]), parts[1], parts[2]
    field_map = {"title": "title", "desc": "description", "price": "price_range", "link": "link"}
    if field not in field_map: return await message.answer(f"Доступны поля: {', '.join(field_map.keys())}")
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await update_wish(user['id'], wish_id, {field_map[field]: value})
    await message.answer(f"✅ Обновлено #{wish_id}")

@router.message(Command("wishes_delete"))
async def cmd_wishes_delete(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /wishes_delete ID")
    wish_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await delete_wish(user['id'], wish_id)
    await message.answer(f"🗑 Удалено #{wish_id}")

@router.message(Command("wishes_done"))
async def cmd_wishes_done(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /wishes_done ID")
    wish_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await complete_wish(user['id'], wish_id)
    await message.answer(f"🎉 Выполнено #{wish_id}!")

# --- DATES ---
@router.message(Command("dates"))
async def cmd_dates(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_dates_formatted(user['id'])
    await message.answer(f"<b>Важные даты:</b>\n\n{text}")

@router.message(Command("dates_add"))
async def cmd_dates_add(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /dates_add Название | ГГГГ-ММ-ДД | [дни]")
    parts = [p.strip() for p in command.args.split("|")]
    if len(parts) < 2: return await message.answer("Нужно название и дата.")
    date_data = {"title": parts[0], "event_date": parts[1], "reminder_days": int(parts[2]) if len(parts) > 2 else 7}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_date(user['id'], date_data)
    await message.answer(f"✅ Добавлена дата: {date_data['title']}")

@router.message(Command("dates_edit"))
async def cmd_dates_edit(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /dates_edit ID Поле Значение")
    parts = command.args.split(maxsplit=2)
    if len(parts) < 3: return await message.answer("Недостаточно аргументов.")
    date_id, field, value = int(parts[0]), parts[1], parts[2]
    field_map = {"title": "title", "date": "event_date", "rem": "reminder_days"}
    if field not in field_map: return await message.answer(f"Доступны поля: {', '.join(field_map.keys())}")
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await update_date(user['id'], date_id, {field_map[field]: value})
    await message.answer(f"✅ Дата #{date_id} обновлена")

@router.message(Command("dates_delete"))
async def cmd_dates_delete(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /dates_delete ID")
    date_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await delete_date(user['id'], date_id)
    await message.answer(f"🗑 Удалена дата #{date_id}")

# --- NOTES ---
@router.message(Command("notes"))
async def cmd_notes(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_notes_formatted(user['id'])
    await message.answer(f"<b>Заметки:</b>\n\n{text}")

@router.message(Command("notes_add"))
async def cmd_notes_add(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /notes_add Текст | [категория]")
    parts = [p.strip() for p in command.args.split("|")]
    note_data = {"content": parts[0], "category": parts[1] if len(parts) > 1 else "other"}
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_note(user['id'], note_data)
    await message.answer("✅ Заметка сохранена")

@router.message(Command("notes_edit"))
async def cmd_notes_edit(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /notes_edit ID Поле Значение")
    parts = command.args.split(maxsplit=2)
    if len(parts) < 3: return await message.answer("Недостаточно аргументов.")
    note_id, field, value = int(parts[0]), parts[1], parts[2]
    field_map = {"text": "content", "cat": "category"}
    if field not in field_map: return await message.answer(f"Доступны поля: {', '.join(field_map.keys())}")
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await update_note(user['id'], note_id, {field_map[field]: value})
    await message.answer(f"✅ Заметка #{note_id} обновлена")

@router.message(Command("notes_delete"))
async def cmd_notes_delete(message: types.Message, command: CommandObject):
    if not command.args: return await message.answer("Использование: /notes_delete ID")
    note_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await delete_note(user['id'], note_id)
    await message.answer(f"🗑 Удалена заметка #{note_id}")

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
            w = await get_wishes_formatted(user['id'])
            reply_text += f"\n\n<b>Список желаний:</b>\n{w}"
        elif at == "list_notes":
            n = await get_notes_formatted(user['id'])
            reply_text += f"\n\n<b>Заметки:</b>\n{n}"
        elif at == "list_dates":
            d = await get_dates_formatted(user['id'])
            reply_text += f"\n\n<b>Важные даты:</b>\n{d}"
    await message.answer(reply_text or "Я всё запомнил!")
