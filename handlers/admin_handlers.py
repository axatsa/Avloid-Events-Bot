from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (add_category, get_categories, add_event, get_all_events, 
                    get_all_users, get_user)
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
    
    text = f"{STRINGS[lang]['active_events']}:\n\n"
    for ev_id, cat, desc in events:
        text += f"ID: {ev_id} | {cat} | {desc[:30]}...\n"
    await message.answer(text)

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
