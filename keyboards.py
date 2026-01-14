from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from strings import STRINGS

def get_lang_keyboard():
    buttons = [
        [KeyboardButton(text="RU"), KeyboardButton(text="UZ"), KeyboardButton(text="EN")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_phone_keyboard(lang):
    buttons = [
        [KeyboardButton(text=STRINGS[lang]["share_phone"], request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_main_menu(lang):
    buttons = [
        [KeyboardButton(text=STRINGS[lang]["online_events"]), KeyboardButton(text=STRINGS[lang]["offline_events"])],
        [KeyboardButton(text=STRINGS[lang]["about_us"]), KeyboardButton(text=STRINGS[lang]["settings"])]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_settings_keyboard(lang):
    buttons = [
        [KeyboardButton(text=STRINGS[lang]["change_name"]), KeyboardButton(text=STRINGS[lang]["change_phone"])],
        [KeyboardButton(text=STRINGS[lang]["change_lang"])],
        [KeyboardButton(text=STRINGS[lang]["main_menu"])]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_menu(lang):
    buttons = [
        [KeyboardButton(text=STRINGS[lang]["active_events"]), KeyboardButton(text=STRINGS[lang]["create_cat"])],
        [KeyboardButton(text=STRINGS[lang]["add_event"]), KeyboardButton(text=STRINGS[lang]["exit_admin"])]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_categories_keyboard(categories):
    # categories: list of (id, name)
    buttons = []
    for cat_id, name in categories:
        buttons.append([KeyboardButton(text=name)])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_social_keyboard(links):
    buttons = []
    for platform, url in links.items():
        buttons.append([InlineKeyboardButton(text=platform.capitalize(), url=url)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_event_reg_keyboard(lang, event_id):
    buttons = [
        [InlineKeyboardButton(text=STRINGS[lang]["register"], callback_data=f"reg_{event_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_moder_events_keyboard(events):
    """Create inline keyboard for moderator event selection"""
    buttons = []
    for ev_id, desc in events:
        # Truncate description to fit button
        short_desc = desc[:40] + "..." if len(desc) > 40 else desc
        buttons.append([InlineKeyboardButton(text=short_desc, callback_data=f"moder_event_{ev_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reg_confirm_keyboard(lang, event_id):
    buttons = [
        [InlineKeyboardButton(text=STRINGS[lang]["confirm_btn"], callback_data=f"confirm_reg_{event_id}")],
        [InlineKeyboardButton(text=STRINGS[lang]["edit_name_btn"], callback_data=f"edit_reg_name_{event_id}")],
        [InlineKeyboardButton(text=STRINGS[lang]["edit_phone_btn"], callback_data=f"edit_reg_phone_{event_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
