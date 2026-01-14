from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (add_user, get_user, update_user_lang, 
                      update_user_name, update_user_phone, 
                      get_events_by_category, get_all_events,
                      is_user_registered, register_user_local)
from strings import STRINGS
from config import SOCIAL_LINKS
import keyboards as kb

router = Router()

class Registration(StatesGroup):
    language = State()
    full_name = State()
    phone = State()

class ProfileUpdate(StatesGroup):
    new_name = State()
    new_phone = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if user:
        lang = user[3]
        await message.answer(STRINGS[lang]["main_menu"], reply_markup=kb.get_main_menu(lang))
    else:
        await state.set_state(Registration.language)
        await message.answer("Please choose a language / Пожалуйста, выберите язык / Tilni tanlang:", reply_markup=kb.get_lang_keyboard())

@router.message(Registration.language)
async def process_language(message: Message, state: FSMContext):
    lang_map = {"RU": "ru", "UZ": "uz", "EN": "en"}
    if message.text in lang_map:
        lang = lang_map[message.text]
        await state.update_data(language=lang)
        await state.set_state(Registration.full_name)
        await message.answer(STRINGS[lang]["get_name"], reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Please use the buttons.")

@router.message(Registration.full_name)
async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']
    await state.update_data(full_name=message.text)
    await state.set_state(Registration.phone)
    await message.answer(STRINGS[lang]["get_phone"], reply_markup=kb.get_phone_keyboard(lang))

@router.message(Registration.phone, F.contact)
@router.message(Registration.phone, F.text.regexp(r'^\+?[\d\s]{10,15}$'))
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['language']
    name = data['full_name']
    phone = message.contact.phone_number if message.contact else message.text
    
    add_user(message.from_user.id, name, phone, lang)
    await state.clear()
    await message.answer(STRINGS[lang]["main_menu"], reply_markup=kb.get_main_menu(lang))

@router.message(F.text.in_(["Онлайн ивенты", "Оффлайн ивенты", "Onlayn tadbirlar", "Offlayn tadbirlar", "Online Events", "Offline Events"]))
async def show_events(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    
    cat_name = "Online" if any(x in message.text for x in ["нлайн", "nlayn", "Online"]) else "Offline"
    
    # Get events with max_participants
    from database import DATABASE_NAME, get_event_participants_count
    import sqlite3
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.id, e.image_id, e.description, e.time_info, e.event_date, e.max_participants, e.location
        FROM events e
        JOIN categories c ON e.category_id = c.id
        WHERE c.name = ?
    ''', (cat_name,))
    events = cursor.fetchall()
    conn.close()

    if not events:
        await message.answer(STRINGS[lang]["no_events"])
        return
        
    for ev_id, img_id, desc, time_info, event_date, max_participants, location in events:
        date_str = f"📅 {event_date}\n" if event_date else ""
        
        # Calculate available spots
        if max_participants > 0:
            registered_count = get_event_participants_count(ev_id)
            available = max_participants - registered_count
            spots_str = f"👥 Мест: {available}/{max_participants}\n" if lang == "ru" else \
                       f"👥 O'rinlar: {available}/{max_participants}\n" if lang == "uz" else \
                       f"👥 Spots: {available}/{max_participants}\n"
        else:
            spots_str = "👥 Мест: ∞\n" if lang == "ru" else \
                       "👥 O'rinlar: ∞\n" if lang == "uz" else \
                       "👥 Spots: ∞\n"
        
        # Location string
        loc_str = ""
        if location:
            loc_label = "📍 Локация" if lang == "ru" else "📍 Joylashuv" if lang == "uz" else "📍 Location"
            loc_str = f"<a href='{location}'>{loc_label}</a>\n"

        caption = f"{desc}\n\n{date_str}{spots_str}{loc_str}🕒 {time_info}"
        reply_markup = kb.get_event_reg_keyboard(lang, ev_id)
        
        # Send with HTML parse mode for link
        from aiogram.enums import ParseMode
        if img_id:
            await message.answer_photo(photo=img_id, caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.answer(caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("reg_"))
async def register_for_event(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user: return
    
    lang = user[3]
    event_id = int(callback.data.split("_")[1])
    
    if is_user_registered(user[0], event_id):
        await callback.answer(STRINGS[lang]["already_reg"], show_alert=True)
        return

    # Check if event is full
    from database import DATABASE_NAME, get_event_participants_count
    import sqlite3
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT max_participants FROM events WHERE id = ?", (event_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        max_participants = result[0]
        if max_participants > 0:  # If there's a limit
            current_count = get_event_participants_count(event_id)
            if current_count >= max_participants:
                await callback.answer(
                    "❌ Мест нет / No spots available / O'rinlar yo'q",
                    show_alert=True
                )
                return

    # Show confirmation dialog
    text = STRINGS[lang]["confirm_reg"].format(name=user[1], phone=user[2])
    await callback.message.answer(text, reply_markup=kb.get_reg_confirm_keyboard(lang, event_id))
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_reg_"))
async def confirm_registration(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user: return
    
    lang = user[3]
    event_id = int(callback.data.split("_")[2])
    
    if is_user_registered(user[0], event_id):
        await callback.answer(STRINGS[lang]["already_reg"], show_alert=True)
        return

    # Check capacity again just in case
    from database import DATABASE_NAME, get_event_participants_count
    import sqlite3
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT max_participants FROM events WHERE id = ?", (event_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] > 0:
        if get_event_participants_count(event_id) >= result[0]:
            await callback.answer("❌ Мест нет / No spots available", show_alert=True)
            return

    # Save registration to database
    register_user_local(user[0], event_id)
    await callback.message.delete()
    await callback.message.answer(STRINGS[lang]["reg_success"])
    await callback.answer()

@router.callback_query(F.data.startswith("edit_reg_"))
async def edit_reg_data(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user: return
    lang = user[3]
    
    # data format: edit_reg_name_123 or edit_reg_phone_123
    parts = callback.data.split("_")
    edit_type = parts[2] # name or phone
    event_id = int(parts[3])
    
    await state.update_data(reg_event_id=event_id)
    
    if edit_type == "name":
        await state.set_state(ProfileUpdate.new_name)
        await callback.message.answer(STRINGS[lang]["get_name"], reply_markup=ReplyKeyboardRemove())
    elif edit_type == "phone":
        await state.set_state(ProfileUpdate.new_phone)
        await callback.message.answer(STRINGS[lang]["get_phone"], reply_markup=kb.get_phone_keyboard(lang))
    
    await callback.answer()

@router.message(F.text.in_(["О нас", "Biz haqimizda", "About Us"]))
async def about_us(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    await message.answer(STRINGS[lang]["about_text"], reply_markup=kb.get_social_keyboard(SOCIAL_LINKS))

@router.message(F.text.in_(["Настройки", "Sozlamalar", "Settings"]))
async def settings(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    # Get language name for display
    lang_names = {"ru": "Русский", "uz": "O'zbek", "en": "English"}
    lang_display = lang_names.get(lang, lang)
    text = STRINGS[lang]["curr_profile"].format(name=user[1], phone=user[2], lang=lang_display)
    await message.answer(text, reply_markup=kb.get_settings_keyboard(lang))

@router.message(F.text.in_(["Главное меню", "Asosiy menyu", "Main Menu"]))
async def back_to_main(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    await message.answer(STRINGS[lang]["main_menu"], reply_markup=kb.get_main_menu(lang))

@router.message(F.text.in_(["Выбор языка", "Tilni tanlash", "Choose language"]))
async def change_lang_menu(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    await message.answer(STRINGS[lang]["change_lang"], reply_markup=kb.get_lang_keyboard())

@router.message(F.text.in_(["RU", "UZ", "EN"]))
async def change_language(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    
    lang_map = {"RU": "ru", "UZ": "uz", "EN": "en"}
    new_lang = lang_map[message.text]
    update_user_lang(message.from_user.id, new_lang)
    await message.answer(STRINGS[new_lang]["main_menu"], reply_markup=kb.get_main_menu(new_lang))

@router.message(F.text.in_(["Изменить ФИО", "FIO o'zgartirish", "Change Name"]))
async def change_name_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    await state.set_state(ProfileUpdate.new_name)
    await message.answer(STRINGS[lang]["get_name"], reply_markup=ReplyKeyboardRemove())

@router.message(ProfileUpdate.new_name)
async def change_name_finish(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    
    # Check if we are in registration flow
    data = await state.get_data()
    reg_event_id = data.get('reg_event_id')
    
    update_user_name(message.from_user.id, message.text)
    user = get_user(message.from_user.id) # Refresh data
    
    await state.clear()
    
    if reg_event_id:
        await message.answer(STRINGS[lang]["name_changed"])
        text = STRINGS[lang]["confirm_reg"].format(name=user[1], phone=user[2])
        await message.answer(text, reply_markup=kb.get_reg_confirm_keyboard(lang, reg_event_id))
    else:
        await message.answer(STRINGS[lang]["name_changed"], reply_markup=kb.get_settings_keyboard(lang))

@router.message(F.text.in_(["Изменить номер", "Raqamni o'zgartirish", "Change Phone"]))
async def change_phone_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    await state.set_state(ProfileUpdate.new_phone)
    await message.answer(STRINGS[lang]["get_phone"], reply_markup=kb.get_phone_keyboard(lang))

@router.message(ProfileUpdate.new_phone, F.contact)
@router.message(ProfileUpdate.new_phone, F.text.regexp(r'^\+?[\d\s]{10,15}$'))
async def change_phone_finish(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user: return
    lang = user[3]
    
    # Check if we are in registration flow
    data = await state.get_data()
    reg_event_id = data.get('reg_event_id')
    
    phone = message.contact.phone_number if message.contact else message.text
    update_user_phone(message.from_user.id, phone)
    user = get_user(message.from_user.id) # Refresh data
    
    await state.clear()
    
    if reg_event_id:
        await message.answer(STRINGS[lang]["phone_changed"])
        text = STRINGS[lang]["confirm_reg"].format(name=user[1], phone=user[2])
        await message.answer(text, reply_markup=kb.get_reg_confirm_keyboard(lang, reg_event_id))
    else:
        await message.answer(STRINGS[lang]["phone_changed"], reply_markup=kb.get_settings_keyboard(lang))
