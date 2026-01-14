from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, get_all_events, get_registrations_by_event
from strings import STRINGS
from config import MODERATOR_PASSWORD
import keyboards as kb

router = Router()

class ModeratorState(StatesGroup):
    password = State()
    menu = State()
    selected_event = State()
    check_phone = State()

@router.message(Command("moder"))
async def moder_login(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    await state.set_state(ModeratorState.password)
    await message.answer("Введите пароль модератора / Enter moderator password:")

@router.message(ModeratorState.password)
async def process_moder_password(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    lang = user[3] if user else "ru"
    
    if message.text == MODERATOR_PASSWORD:
        await state.set_state(ModeratorState.menu)
        
        # Get all events grouped by category
        events = get_all_events()
        
        if not events:
            await message.answer("Нет доступных ивентов / No events available")
            await state.clear()
            return
        
        # Separate online and offline events
        online_events = [(ev_id, desc) for ev_id, cat, desc in events if cat == "Online"]
        offline_events = [(ev_id, desc) for ev_id, cat, desc in events if cat == "Offline"]
        
        # Send online events
        if online_events:
            await message.answer("📱 Онлайн ивенты / Online Events:", 
                               reply_markup=kb.get_moder_events_keyboard(online_events))
        
        # Send offline events
        if offline_events:
            await message.answer("📍 Оффлайн ивенты / Offline Events:", 
                               reply_markup=kb.get_moder_events_keyboard(offline_events))
    else:
        await message.answer("Неверный пароль / Wrong password")
        await state.clear()

@router.callback_query(ModeratorState.menu, F.data.startswith("moder_event_"))
async def select_event(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[2])
    await state.update_data(event_id=event_id)
    await state.set_state(ModeratorState.check_phone)
    
    await callback.message.answer(
        "Введите номер телефона для проверки:\n"
        "Enter phone number to check:"
    )
    await callback.answer()

@router.message(ModeratorState.check_phone)
async def check_participant(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data['event_id']
    phone = message.text.strip()
    
    # Search for participant
    registrations = get_registrations_by_event(event_id)
    
    found = None
    for user_id, full_name, user_phone in registrations:
        if phone in user_phone or user_phone in phone:
            found = (full_name, user_phone)
            break
    
    if found:
        await message.answer(
            f"✅ Участник найден / Participant found:\n\n"
            f"ФИО / Name: {found[0]}\n"
            f"Телефон / Phone: {found[1]}"
        )
    else:
        await message.answer(
            f"❌ Участник не найден / Participant not found\n\n"
            f"Номер: {phone}"
        )
    
    # Ask if want to check another
    await message.answer(
        "Введите другой номер для проверки или /moder для выхода\n"
        "Enter another number to check or /moder to exit"
    )
