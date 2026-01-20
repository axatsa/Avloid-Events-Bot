from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (add_category, get_categories, add_event, get_all_events, 
                    get_all_users, get_user, delete_event, get_event_by_id, update_event_field)
from aiogram.types import CallbackQuery
from strings import STRINGS
from config import ADMIN_PASSWORD
import keyboards as kb

router = Router()

class AdminState(StatesGroup):
    password = State()
    menu = State()
    create_category = State()
    add_event_cat = State()
    add_event_img = State()
    add_event_desc = State()
    add_event_time = State()
    add_event_date = State()
    add_event_capacity = State()
    add_event_location = State()
    
    # Edit states
    edit_field_value = State()

@router.message(Command("admin"))
async def admin_login(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.password)
    await message.answer(STRINGS[lang]["admin_pass"], reply_markup=ReplyKeyboardRemove())

@router.message(AdminState.password)
async def process_password(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    if message.text == ADMIN_PASSWORD:
        await state.set_state(AdminState.menu)
        await message.answer(STRINGS[lang]["admin_menu"], reply_markup=kb.get_admin_menu(lang))
    else:
        await message.answer(STRINGS[lang]["wrong_pass"])
        await state.clear()

@router.message(AdminState.menu, F.text.in_(["Активные ивенты", "Faol tadbirlar", "Active Events"]))
async def active_events(message: Message):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    events = get_all_events()
    if not events:
        await message.answer(STRINGS[lang]["no_events"])
        return
    
    await message.answer(STRINGS[lang]["active_events"], reply_markup=kb.get_admin_events_keyboard(events))

@router.callback_query(F.data == "admin_back_list")
async def back_to_list(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    events = get_all_events()
    
    # Delete the current message (could be photo or text)
    await callback.message.delete()
    
    if not events:
        await callback.message.answer(STRINGS[lang]["no_events"])
        return
    
    await callback.message.answer(STRINGS[lang]["active_events"], reply_markup=kb.get_admin_events_keyboard(events))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_event_"))
async def view_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    event = get_event_by_id(event_id)
    if not event:
        await callback.answer("Event not found", show_alert=True)
        return
        
    # event: id, cat_name, desc, image_id, time_info, date, participants, location
    # 0, 1, 2, 3, 4, 5, 6, 7
    
    caption = (f"[{event[1]}]\n\n"
               f"{event[2]}\n\n"
               f"📅 {event[5]} | ⏰ {event[4]}\n"
               f"👥 {event[6]}\n")
    if event[7]:
        caption += f"📍 {event[7]}"
        
    await callback.message.delete()
    if event[3]:
        await callback.message.answer_photo(photo=event[3], caption=caption, 
                                          reply_markup=kb.get_event_manage_keyboard(lang, event_id))
    else:
        await callback.message.answer(caption, reply_markup=kb.get_event_manage_keyboard(lang, event_id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_ask_"))
async def ask_delete_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[3])
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    await callback.message.edit_reply_markup(reply_markup=kb.get_delete_confirm_keyboard(lang, event_id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_confirm_"))
async def confirm_delete_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[3])
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    delete_event(event_id)
    await callback.answer(STRINGS[lang]["event_deleted"], show_alert=True)
    
    # Return to list
    events = get_all_events()
    if not events:
        await callback.message.delete()
        await callback.message.answer(STRINGS[lang]["no_events"])
    else:
        await callback.message.delete()
        await callback.message.answer(STRINGS[lang]["active_events"], reply_markup=kb.get_admin_events_keyboard(events))

@router.callback_query(F.data.startswith("admin_edit_"))
async def list_edit_options(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    event = get_event_by_id(event_id)
    if not event:
        await callback.answer("Event not found")
        return
        
    is_offline = "Offline" in event[1] or "Оффлайн" in event[1]
    
    await callback.message.edit_reply_markup(reply_markup=kb.get_event_edit_keyboard(lang, event_id, is_offline))
    await callback.answer()

@router.callback_query(F.data.startswith("edit_field_"))
async def edit_field_start(callback: CallbackQuery, state: FSMContext):
    # data: edit_field_{field}_{id}
    parts = callback.data.split("_")
    field = parts[2]
    event_id = int(parts[3])
    
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    await state.update_data(edit_event_id=event_id, edit_field=field)
    await state.set_state(AdminState.edit_field_value)
    
    prompt = STRINGS[lang]["enter_new_val"]
    if field == "img":
        prompt = STRINGS[lang]["send_img"]
    elif field == "loc":
        prompt = STRINGS[lang]["send_location"]
        
    await callback.message.delete()
    await callback.message.answer(prompt, reply_markup=kb.get_back_keyboard(lang, f"admin_edit_{event_id}")) # Back to edit menu
    await callback.answer()

@router.callback_query(AdminState.edit_field_value, F.data.startswith("admin_edit_"))
async def cancel_edit_field(callback: CallbackQuery, state: FSMContext):
    """Handle back button press during editing"""
    event_id = int(callback.data.split("_")[2])
    user = get_user(callback.from_user.id)
    lang = user[3] if user else "ru"
    
    # Return to event view with edit menu
    event = get_event_by_id(event_id)
    if not event:
        await callback.answer("Event not found")
        return
        
    is_offline = "Offline" in event[1] or "Оффлайн" in event[1]
    
    # Get the message that has the back button
    await callback.message.delete()
    
    # Show event details with edit menu
    caption = (f"[{event[1]}]\n\n"
               f"{event[2]}\n\n"
               f"📅 {event[5]} | ⏰ {event[4]}\n"
               f"👥 {event[6]}\n")
    if event[7]:
        caption += f"📍 {event[7]}"
        
    if event[3]:
        await callback.message.answer_photo(photo=event[3], caption=caption, 
                                          reply_markup=kb.get_event_edit_keyboard(lang, event_id, is_offline))
    else:
        await callback.message.answer(caption, reply_markup=kb.get_event_edit_keyboard(lang, event_id, is_offline))
    
    await state.set_state(AdminState.menu)
    await callback.answer()

@router.message(AdminState.edit_field_value)
async def process_edit_field(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data['edit_event_id']
    field_code = data['edit_field']
    
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    
    db_field = ""
    value = None
    
    if field_code == "img":
        if not message.photo:
            await message.answer("Please send a photo.")
            return
        db_field = "image_id"
        value = message.photo[-1].file_id
        
    elif field_code == "desc":
        db_field = "description"
        value = message.text
        
    elif field_code == "time":
        db_field = "time_info"
        value = message.text
        
    elif field_code == "date":
        db_field = "event_date"
        value = message.text
        
    elif field_code == "cap":
        db_field = "max_participants"
        try:
            value = int(message.text)
        except:
            await message.answer("Please send a number.")
            return
            
    elif field_code == "loc":
        if not message.location:
            await message.answer(STRINGS[lang]["location_invalid"])
            return
        db_field = "location"
        lat = message.location.latitude
        lon = message.location.longitude
        value = f"https://www.google.com/maps?q={lat},{lon}"
        
    if db_field:
        update_event_field(event_id, db_field, value)
        await message.answer(STRINGS[lang]["event_updated"])
    
    # Show event again
    event = get_event_by_id(event_id)
    caption = (f"[{event[1]}]\n\n"
               f"{event[2]}\n\n"
               f"📅 {event[5]} | ⏰ {event[4]}\n"
               f"👥 {event[6]}\n")
    if event[7]:
        caption += f"📍 {event[7]}"
        
    if event[3]:
        await message.answer_photo(photo=event[3], caption=caption, 
                                          reply_markup=kb.get_event_manage_keyboard(lang, event_id))
    else:
        await message.answer(caption, reply_markup=kb.get_event_manage_keyboard(lang, event_id))
        
    await state.set_state(AdminState.menu)

@router.message(AdminState.menu, F.text.in_(["Создать категорию", "Kategoriya yaratish", "Create Category"]))
async def start_create_cat(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.create_category)
    await message.answer(STRINGS[lang]["cat_name"])

@router.message(AdminState.create_category)
async def process_create_cat(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    if add_category(message.text):
        await message.answer(STRINGS[lang]["cat_saved"])
    else:
        await message.answer("Error or duplicate.")
    await state.set_state(AdminState.menu)
    await message.answer(STRINGS[lang]["admin_menu"], reply_markup=kb.get_admin_menu(lang))

@router.message(AdminState.menu, F.text.in_(["Добавить ивент", "Tadbir qo'shish", "Add Event"]))
async def start_add_event(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    cats = get_categories()
    await state.set_state(AdminState.add_event_cat)
    await message.answer(STRINGS[lang]["choose_cat"], reply_markup=kb.get_categories_keyboard(cats))

@router.message(AdminState.add_event_cat)
async def process_add_event_cat(message: Message, state: FSMContext):
    cats = get_categories()
    cat_id = next((c[0] for c in cats if c[1] == message.text), None)
    if cat_id:
        await state.update_data(cat_id=cat_id)
        user = get_user(message.from_user.id)
        lang = user[3] if user else "ru"
        await state.set_state(AdminState.add_event_img)
        await message.answer(STRINGS[lang]["send_img"], reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Please choose from buttons.")

@router.message(AdminState.add_event_img, F.photo)
async def process_add_event_img(message: Message, state: FSMContext):
    await state.update_data(img_id=message.photo[-1].file_id)
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.add_event_desc)
    await message.answer(STRINGS[lang]["send_desc"])

@router.message(AdminState.add_event_desc)
async def process_add_event_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.add_event_time)
    await message.answer(STRINGS[lang]["send_time"])

@router.message(AdminState.add_event_time)
async def process_add_event_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.add_event_date)
    await message.answer(STRINGS[lang]["send_date"])

@router.message(AdminState.add_event_date)
async def process_add_event_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(AdminState.add_event_capacity)
    await message.answer(STRINGS[lang]["send_capacity"])

@router.message(AdminState.add_event_capacity)
async def process_add_event_capacity(message: Message, state: FSMContext, bot: Bot):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"

    try:
        max_participants = int(message.text)
        if max_participants < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите число (0 или больше) / Please enter a number (0 or more)")
        return
    
    data = await state.get_data()
    # Check if category is Offline to ask for location
    from database import get_categories
    cats = get_categories()
    cat_name = next((c[1] for c in cats if c[0] == data['cat_id']), "")
    
    await state.update_data(capacity=max_participants)
    
    if "Offline" in cat_name or "Оффлайн" in cat_name or "Offlayn" in cat_name:
        await state.set_state(AdminState.add_event_location)
        await message.answer(STRINGS[lang]["send_location"])
        return
        
    add_event(data['cat_id'], data['img_id'], data['desc'], data['time'], data['date'], max_participants)
    
    await message.answer(STRINGS[lang]["event_saved"])
    
    # Notify users
    all_users = get_all_users()
    for uid in all_users:
        u_data = get_user(uid)
        u_lang = u_data[3] if u_data else "ru"
        try:
            await bot.send_message(uid, STRINGS[u_lang]["new_event_notify"])
        except:
            pass
            
    await state.set_state(AdminState.menu)
    await message.answer(STRINGS[lang]["admin_menu"], reply_markup=kb.get_admin_menu(lang))

@router.message(AdminState.add_event_location, F.location)
async def process_add_event_location(message: Message, state: FSMContext, bot: Bot):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    
    lat = message.location.latitude
    lon = message.location.longitude
    # Create Google Maps link
    location_url = f"https://www.google.com/maps?q={lat},{lon}"
    
    data = await state.get_data()
    add_event(data['cat_id'], data['img_id'], data['desc'], data['time'], data['date'], data['capacity'], location_url)
    
    await message.answer(STRINGS[lang]["event_saved"])
    
    # Notify users
    all_users = get_all_users()
    for uid in all_users:
        u_data = get_user(uid)
        u_lang = u_data[3] if u_data else "ru"
        try:
            await bot.send_message(uid, STRINGS[u_lang]["new_event_notify"])
        except:
            pass
            
    await state.set_state(AdminState.menu)
    await message.answer(STRINGS[lang]["admin_menu"], reply_markup=kb.get_admin_menu(lang))

@router.message(AdminState.add_event_location)
async def process_add_event_location_invalid(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await message.answer(STRINGS[lang]["location_invalid"])

@router.message(AdminState.menu, F.text.in_(["Выйти из админки", "Admindan chiqish", "Exit Admin"]))
async def exit_admin(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.clear()
    await message.answer(STRINGS[lang]["main_menu"], reply_markup=kb.get_main_menu(lang))
