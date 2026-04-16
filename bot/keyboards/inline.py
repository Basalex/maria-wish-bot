from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_items_keyboard(items: list, prefix: str):
    builder = InlineKeyboardBuilder()
    for item in items:
        # Для желаний используем title, для заметок content
        text = item.get('title') or item.get('content') or f"ID {item['id']}"
        # Ограничиваем длину текста на кнопке
        if len(text) > 30:
            text = text[:27] + "..."
        builder.row(InlineKeyboardButton(text=text, callback_data=f"{prefix}_view:{item['id']}"))
    
    return builder.as_markup()

def get_item_actions_keyboard(item_id: int, prefix: str, is_wish: bool = False):
    builder = InlineKeyboardBuilder()
    if is_wish:
        builder.row(InlineKeyboardButton(text="✅ Выполнено", callback_data=f"{prefix}_done:{item_id}"))
    
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"{prefix}_edit:{item_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"{prefix}_delete:{item_id}")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=f"{prefix}_list"))
    
    return builder.as_markup()

def get_edit_fields_keyboard(item_id: int, prefix: str, fields: dict):
    builder = InlineKeyboardBuilder()
    for label, field in fields.items():
        builder.row(InlineKeyboardButton(text=label, callback_data=f"{prefix}_editf:{item_id}:{field}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_view:{item_id}"))
    return builder.as_markup()
