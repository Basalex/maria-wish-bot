from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.models import (
    get_or_create_user, get_wish, get_date, get_note,
    delete_wish, delete_date, delete_note,
    complete_wish, update_wish, update_date, update_note,
    get_wishes_raw, get_dates_raw, get_notes_raw
)
from bot.keyboards.inline import get_items_keyboard, get_item_actions_keyboard, get_edit_fields_keyboard

router = Router()

class EditState(StatesGroup):
    waiting_for_value = State()

# --- LISTS ---
@router.callback_query(F.data == "wish_list")
async def wish_list_cb(callback: types.CallbackQuery):
    user = await get_or_create_user(callback.from_user.id)
    items = await get_wishes_raw(user['id'])
    await callback.message.edit_text("<b>Список желаний Марии:</b>", reply_markup=get_items_keyboard(items, "wish"))

@router.callback_query(F.data == "date_list")
async def date_list_cb(callback: types.CallbackQuery):
    user = await get_or_create_user(callback.from_user.id)
    items = await get_dates_raw(user['id'])
    await callback.message.edit_text("<b>Важные даты:</b>", reply_markup=get_items_keyboard(items, "date"))

@router.callback_query(F.data == "note_list")
async def note_list_cb(callback: types.CallbackQuery):
    user = await get_or_create_user(callback.from_user.id)
    items = await get_notes_raw(user['id'])
    await callback.message.edit_text("<b>Заметки:</b>", reply_markup=get_items_keyboard(items, "note"))

# --- VIEW ITEM ---
@router.callback_query(F.data.startswith("wish_view:"))
async def wish_view_cb(callback: types.CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(callback.from_user.id)
    w = await get_wish(user['id'], wish_id)
    if not w: return await callback.answer("Не найдено")
    
    text = f"🎁 <b>{w['title']}</b>\n\n"
    if w['description']: text += f"Описание: {w['description']}\n"
    if w['price_range']: text += f"Цена: {w['price_range']}\n"
    if w['link']: text += f"Ссылка: {w['link']}\n"
    
    await callback.message.edit_text(text, reply_markup=get_item_actions_keyboard(wish_id, "wish", is_wish=True))

@router.callback_query(F.data.startswith("date_view:"))
async def date_view_cb(callback: types.CallbackQuery):
    date_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(callback.from_user.id)
    d = await get_date(user['id'], date_id)
    if not d: return await callback.answer("Не найдено")
    
    text = f"📅 <b>{d['title']}</b>\n\nДата: {d['event_date'].strftime('%d.%m.%Y')}\nНапоминание за: {d['reminder_days']} дн."
    await callback.message.edit_text(text, reply_markup=get_item_actions_keyboard(date_id, "date"))

@router.callback_query(F.data.startswith("note_view:"))
async def note_view_cb(callback: types.CallbackQuery):
    note_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(callback.from_user.id)
    n = await get_note(user['id'], note_id)
    if not n: return await callback.answer("Не найдено")
    
    text = f"📝 <b>Заметка</b>\n\n{n['content']}\n\nКатегория: {n['category']}"
    await callback.message.edit_text(text, reply_markup=get_item_actions_keyboard(note_id, "note"))

# --- ACTIONS ---
@router.callback_query(F.data.startswith("wish_done:"))
async def wish_done_cb(callback: types.CallbackQuery):
    wish_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(callback.from_user.id)
    await complete_wish(user['id'], wish_id)
    await callback.answer("Поздравляю! Желание исполнено.")
    await wish_list_cb(callback)

@router.callback_query(F.data.contains("_delete:"))
async def item_delete_cb(callback: types.CallbackQuery):
    prefix, item_id = callback.data.split("_delete:")
    item_id = int(item_id)
    user = await get_or_create_user(callback.from_user.id)
    
    if prefix == "wish": await delete_wish(user['id'], item_id)
    elif prefix == "date": await delete_date(user['id'], item_id)
    elif prefix == "note": await delete_note(user['id'], item_id)
    
    await callback.answer("Удалено")
    # Redirect back to list
    if prefix == "wish": await wish_list_cb(callback)
    elif prefix == "date": await date_list_cb(callback)
    elif prefix == "note": await note_list_cb(callback)

# --- EDITING ---
@router.callback_query(F.data.contains("_edit:"))
async def item_edit_cb(callback: types.CallbackQuery):
    prefix, item_id = callback.data.split("_edit:")
    item_id = int(item_id)
    
    fields = {}
    if prefix == "wish": fields = {"Название": "title", "Описание": "description", "Цена": "price_range", "Ссылка": "link"}
    elif prefix == "date": fields = {"Название": "title", "Дата (ГГГГ-ММ-ДД)": "event_date", "Дни напоминания": "reminder_days"}
    elif prefix == "note": fields = {"Текст": "content", "Категория": "category"}
    
    await callback.message.edit_text("Что именно хочешь изменить?", reply_markup=get_edit_fields_keyboard(item_id, prefix, fields))

@router.callback_query(F.data.contains("_editf:"))
async def item_edit_field_cb(callback: types.CallbackQuery, state: FSMContext):
    # data: wish_editf:ID:field
    parts = callback.data.split(":")
    prefix = parts[0].split("_")[0]
    item_id, field = int(parts[1]), parts[2]
    
    await state.set_state(EditState.waiting_for_value)
    await state.update_data(prefix=prefix, item_id=item_id, field=field)
    
    await callback.message.edit_text(f"Введи новое значение для поля <b>{field}</b>:")
    await callback.answer()

@router.message(EditState.waiting_for_value)
async def process_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    prefix, item_id, field = data['prefix'], data['item_id'], data['field']
    user = await get_or_create_user(message.from_user.id)
    
    val = message.text
    if prefix == "wish": await update_wish(user['id'], item_id, {field: val})
    elif prefix == "date": await update_date(user['id'], item_id, {field: val})
    elif prefix == "note": await update_note(user['id'], item_id, {field: val})
    
    await state.clear()
    await message.answer(f"✅ Обновлено!")
    
    # Show item again
    # We simulate callback to show item view
    if prefix == "wish":
        w = await get_wish(user['id'], item_id)
        await message.answer(f"🎁 <b>{w['title']}</b>\n\nОбновлено.", reply_markup=get_item_actions_keyboard(item_id, "wish", is_wish=True))
    elif prefix == "date":
        d = await get_date(user['id'], item_id)
        await message.answer(f"📅 <b>{d['title']}</b>\n\nОбновлено.", reply_markup=get_item_actions_keyboard(item_id, "date"))
    elif prefix == "note":
        n = await get_note(user['id'], item_id)
        await message.answer(f"📝 <b>Заметка</b>\n\nОбновлено.", reply_markup=get_item_actions_keyboard(item_id, "note"))
