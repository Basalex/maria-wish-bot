from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from bot.ai.gemini import process_message
from bot.database.models import (
    get_or_create_user, save_wish, update_wish, delete_wish, save_date, save_note, save_gift, complete_wish,
    get_user_context, get_wishes_formatted, get_notes_formatted, get_dates_formatted, get_gift_stats
)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой помощник по подаркам для Марии.\n\n"
                         "Ты можешь управлять желаниями как командами, так и просто общаясь со мной.\n"
                         "Используй /help чтобы узнать подробнее.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>Команды управления желаниями:</b>\n"
        "/wishes — Показать список\n"
        "/wishes_add Название | Описание | Цена — Добавить\n"
        "/wishes_edit ID Поле Значение — Изменить (поле: title, desc, price, link)\n"
        "/wishes_delete ID — Удалить\n"
        "/wishes_done ID — Отметить выполненным\n\n"
        "<b>Другие команды:</b>\n"
        "/notes — Заметки\n"
        "/dates — Даты\n"
        "/stats — Статистика подарков\n\n"
        "<i>Ты также можешь просто писать мне сообщения, и я сам пойму, что нужно сделать!</i>"
    )
    await message.answer(help_text)

@router.message(Command("wishes"))
async def cmd_wishes(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = await get_wishes_formatted(user['id'])
    await message.answer(f"<b>Желания Марии:</b>\n\n{text}")

@router.message(Command("wishes_add"))
async def cmd_wishes_add(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Использование: /wishes_add Название | Описание | Цена")
    
    parts = [p.strip() for p in command.args.split("|")]
    wish_data = {
        "title": parts[0],
        "description": parts[1] if len(parts) > 1 else None,
        "price_range": parts[2] if len(parts) > 2 else None
    }
    
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_wish(user['id'], wish_data)
    await message.answer(f"✅ Добавлено желание: {wish_data['title']}")

@router.message(Command("wishes_edit"))
async def cmd_wishes_edit(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Использование: /wishes_edit ID Поле Значение (поле: title, desc, price, link)")
    
    parts = command.args.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("Недостаточно аргументов.")
    
    wish_id, field, value = int(parts[0]), parts[1], parts[2]
    field_map = {"title": "title", "desc": "description", "price": "price_range", "link": "link"}
    
    if field not in field_map:
        return await message.answer(f"Неверное поле. Доступны: {', '.join(field_map.keys())}")
    
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await update_wish(user['id'], wish_id, {field_map[field]: value})
    await message.answer(f"✅ Обновлено поле {field} для желания #{wish_id}")

@router.message(Command("wishes_delete"))
async def cmd_wishes_delete(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Использование: /wishes_delete ID")
    
    wish_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await delete_wish(user['id'], wish_id)
    await message.answer(f"🗑 Удалено желание #{wish_id}")

@router.message(Command("wishes_done"))
async def cmd_wishes_done(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Использование: /wishes_done ID")
    
    wish_id = int(command.args.strip())
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await complete_wish(user['id'], wish_id)
    await message.answer(f"🎉 Желание #{wish_id} отмечено как выполненное!")

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
