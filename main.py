import telebot
from telebot import types
import requests
import json
import time
from tinydb import TinyDB, Query
from datetime import datetime
from typing import Optional, Dict, List
import re

# Database initialization
db = TinyDB('users.json')

# Load settings
try:
    with open('settings.json', 'r', encoding='utf-8') as f:
        SETTINGS = json.load(f)
except FileNotFoundError:
    SETTINGS = {
        'api_url': 'https://smmupper.com/api/v2',
        'api_key': 'YOUR_API_KEY',
        'admin_id': 0,
        'sponsors': [],
        'currency': '$'
    }
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)

# Ensure currency exists
if 'currency' not in SETTINGS:
    SETTINGS['currency'] = '$'
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)

# Bot initialization
BOT_TOKEN = '8400775067:AAHq1cek_BWwmE59__P_q-wh2_1UBPkuADA'
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = SETTINGS['admin_id']
API_KEY = SETTINGS['api_key']
API_URL = SETTINGS['api_url']
SPONSOR_CHANNELS = SETTINGS['sponsors']
CURRENCY = SETTINGS.get('currency', '$')

# Normalize sponsors storage: ensure each sponsor is a dict with keys: id, username, invite_link
def _normalize_sponsors(raw_list):
    normalized = []
    for item in raw_list:
        if isinstance(item, dict):
            # already a dict, ensure keys
            sponsor = {
                'id': item.get('id') if item.get('id') is not None else item.get('channel_id'),
                'username': item.get('username'),
                'invite_link': item.get('invite_link')
            }
            normalized.append(sponsor)
        else:
            # assume it's an id string or int
            try:
                sponsor_id = int(item)
            except:
                sponsor_id = item
            normalized.append({'id': sponsor_id, 'username': None, 'invite_link': None})
    return normalized

# ensure SPONSOR_CHANNELS is normalized list of dicts
SPONSOR_CHANNELS = _normalize_sponsors(SPONSOR_CHANNELS)

# ============= MARKUPS =============

def main_menu():
    """Asosiy menu tugmalari"""
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("💰 Balans"),
        telebot.types.KeyboardButton("📊 Xizmatlar"),
        telebot.types.KeyboardButton("➕ Order qo'shish"),
        telebot.types.KeyboardButton("📦 Mening order'larim"),
        telebot.types.KeyboardButton("❓ Yordam"),
        telebot.types.KeyboardButton("⚙️ Admin")
    )
    return markup

def admin_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        telebot.types.KeyboardButton("💱 Valyuta o'zgartirish")
    )
    markup.add(
        telebot.types.KeyboardButton("📊 Statistika"),
        telebot.types.KeyboardButton("🛍️ Xizmatlar")
    )
    markup.add(
        telebot.types.KeyboardButton("💬 Xabar yuborish")
    )
    markup.add(
        telebot.types.KeyboardButton("🔒 Majburiy obuna"),
        telebot.types.KeyboardButton("💳 To'lov tizimlari")
    )
    markup.add(
        telebot.types.KeyboardButton("🔍 Foydalanuvchi boshqarish"),
    )
    markup.add(
        telebot.types.KeyboardButton("🔑 API kalit"),
        telebot.types.KeyboardButton("🛍️ Buyurtmalar")
    )
    markup.add(
        telebot.types.KeyboardButton("⬅️ Orqaga")
    )
    return markup


def back_menu():
    """Orqaga qaytish tugmasi"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
    return markup

# ============= API FUNCTIONS =============

def get_categories():
    """Barcha kategoriyalarni olish"""
    return SETTINGS.get('categories', [])

def add_category(name: str) -> bool:
    """Yangi kategoriya qo'shish"""
    global SETTINGS
    categories = SETTINGS.get('categories', [])
    
    # Duplicate check
    if any(c['name'].lower() == name.lower() for c in categories):
        return False
    
    categories.append({
        'id': len(categories) + 1,
        'name': name,
        'created_at': datetime.now().isoformat()
    })
    
    SETTINGS['categories'] = categories
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
    return True

def get_types(category_id: int) -> list:
    """Kategoriyaning turlarini olish"""
    types_data = SETTINGS.get('types', [])
    return [t for t in types_data if t['category_id'] == category_id]

def add_type(category_id: int, name: str) -> bool:
    """Kategoriyaga tur qo'shish"""
    global SETTINGS
    categories = SETTINGS.get('categories', [])
    
    # Category exists check
    if not any(c['id'] == category_id for c in categories):
        return False
    
    types_data = SETTINGS.get('types', [])
    
    # Duplicate check
    if any(t['category_id'] == category_id and t['name'].lower() == name.lower() for t in types_data):
        return False
    
    types_data.append({
        'id': len(types_data) + 1,
        'category_id': category_id,
        'name': name,
        'created_at': datetime.now().isoformat()
    })
    
    SETTINGS['types'] = types_data
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
    return True

def get_custom_services():
    """Custom xizmatlarni olish"""
    return SETTINGS.get('custom_services', [])

def add_custom_service(service_id: int, name: str, price: float, category_id: int, type_id: int):
    """Custom xizmat qo'shish"""
    global SETTINGS
    custom_services = SETTINGS.get('custom_services', [])
    
    # Duplicate check
    if any(s['service_id'] == service_id for s in custom_services):
        return False
    
    # Category va type check
    categories = SETTINGS.get('categories', [])
    types_data = SETTINGS.get('types', [])
    
    if not any(c['id'] == category_id for c in categories):
        return False
    
    if not any(t['id'] == type_id and t['category_id'] == category_id for t in types_data):
        return False
    
    custom_services.append({
        'service_id': service_id,
        'name': name,
        'price': price,
        'category_id': category_id,
        'type_id': type_id,
        'created_at': datetime.now().isoformat()
    })
    
    SETTINGS['custom_services'] = custom_services
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
    return True

def remove_custom_service(service_id: int) -> bool:
    """Custom xizmatni o'chirish"""
    global SETTINGS
    custom_services = SETTINGS.get('custom_services', [])
    
    for i, service in enumerate(custom_services):
        if service['service_id'] == service_id:
            custom_services.pop(i)
            SETTINGS['custom_services'] = custom_services
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
            return True
    return False

def remove_category(category_id: int) -> bool:
    """Kategoriya va unga tegishli turlar hamda xizmatlarni o'chirish"""
    global SETTINGS
    categories = SETTINGS.get('categories', [])
    types_data = SETTINGS.get('types', [])
    custom_services = SETTINGS.get('custom_services', [])

    # find category
    cat_index = next((i for i, c in enumerate(categories) if c['id'] == category_id), None)
    if cat_index is None:
        return False

    # remove category
    categories.pop(cat_index)

    # remove types for this category
    types_data = [t for t in types_data if t['category_id'] != category_id]

    # remove custom services for this category
    custom_services = [s for s in custom_services if s.get('category_id') != category_id]

    SETTINGS['categories'] = categories
    SETTINGS['types'] = types_data
    SETTINGS['custom_services'] = custom_services

    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)

    return True

def remove_type(type_id: int) -> bool:
    """Turni o'chirish va unga tegishli xizmatlarni olib tashlash"""
    global SETTINGS
    types_data = SETTINGS.get('types', [])
    custom_services = SETTINGS.get('custom_services', [])

    type_index = next((i for i, t in enumerate(types_data) if t['id'] == type_id), None)
    if type_index is None:
        return False

    types_data.pop(type_index)

    # remove custom services for this type
    custom_services = [s for s in custom_services if s.get('type_id') != type_id]

    SETTINGS['types'] = types_data
    SETTINGS['custom_services'] = custom_services

    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)

    return True

def get_all_services():
    """Faqatgina custom xizmatlarni olish (admin tomonidan qo'shilganlar)"""
    custom_services = get_custom_services()
    categories = SETTINGS.get('categories', [])
    types_data = SETTINGS.get('types', [])
    
    # Custom services'ni kategoriya va tur ma'lumotlari bilan format qilish
    formatted_services = []
    for service in custom_services:
        category = next((c for c in categories if c['id'] == service.get('category_id')), None)
        service_type = next((t for t in types_data if t['id'] == service.get('type_id')), None)
        
        formatted_services.append({
            'service': service['service_id'],
            'name': service['name'],
            'rate': str(service['price']),
            'category': category['name'] if category else 'Noma\'lum',
            'type': service_type['name'] if service_type else 'Noma\'lum',
            'category_id': service.get('category_id'),
            'type_id': service.get('type_id'),
            'min': '1',
            'max': '999999',
            'refill': False,
            'cancel': False
        })
    
    return formatted_services

def get_services():
    """Barcha xizmatlarni olish"""
    params = {
        'key': API_KEY,
        'action': 'services'
    }
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def add_order(service_id: int, link: str, quantity: int, runs: int = None, interval: int = None) -> Dict:
    """Yangi order qo'shish"""
    params = {
        'key': API_KEY,
        'action': 'add',
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    if runs:
        params['runs'] = runs
    if interval:
        params['interval'] = interval
    
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def get_order_status(order_id: int) -> Dict:
    """Bitta order statusini olish API dan"""
    params = {
        'key': API_KEY,
        'action': 'status',
        'order': order_id
    }
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def get_multiple_orders_status(order_ids: list) -> Dict:
    """Bir nechta order statuslarini olish API dan"""
    if not order_ids:
        return {}
    
    params = {
        'key': API_KEY,
        'action': 'status',
        'orders': ','.join(map(str, order_ids))
    }
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {}

def get_balance() -> Dict:
    """Balansni olish"""
    params = {
        'key': API_KEY,
        'action': 'balance'
    }
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def cancel_order(order_ids: str) -> Dict:
    """Order bekor qilish"""
    params = {
        'key': API_KEY,
        'action': 'cancel',
        'orders': order_ids
    }
    try:
        response = requests.post(API_URL, data=params)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

# ============= SPONSOR CHECK =============

def check_sponsors(user_id: int) -> bool:
    """Foydalanuvchi sponsor kanallarga obuna bo'lganini tekshirish"""
    if not SPONSOR_CHANNELS:
        return True
    
    for sponsor in SPONSOR_CHANNELS:
        # sponsor can be a dict with id/username/invite_link or a plain id
        chat_id = None
        if isinstance(sponsor, dict):
            chat_id = sponsor.get('id')
        else:
            try:
                chat_id = int(sponsor)
            except:
                chat_id = sponsor
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

def get_channel_username(channel_id: int) -> str:
    """Kanal ID orqali kanal username olish"""
    try:
        chat = bot.get_chat(channel_id)
        if getattr(chat, 'username', None):
            return f"@{chat.username}"
        else:
            # return title if available
            return chat.title or str(channel_id)
    except:
        return f"Canal ({channel_id})"

def get_channel_status(user_id: int, channel_id: int) -> bool:
    """Foydalanuvchining kanal uchun obuna statusini tekshirish"""
    try:
        member = bot.get_chat_member(channel_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False



def check_invite_link(text: str) -> bool:
    INVITE_REGEX = re.compile(
        r"^https://t\.me/(?:\+|joinchat/)[A-Za-z0-9_-]{10,}$"
    )
    if not text:
        return False
    return bool(INVITE_REGEX.match(text.strip()))

def show_sponsor_message(user_id: int, message_id: int = None):
    """Modernroq sponsor message ko'rsatish inline keyboard bilan"""
    if not SPONSOR_CHANNELS:
        return
    
    sponsor_text = "⚠️ Botdan to'liq foydalanish uchun homiy kanallarga obuna bo'ling!"
    
    # Inline keyboard yaratish
    markup = types.InlineKeyboardMarkup()
    
    # Har bir kanal uchun tugma
    for sponsor in SPONSOR_CHANNELS:
        # sponsor may be dict or plain id
        if isinstance(sponsor, dict):
            chat_id = sponsor.get('id')
            uname = sponsor.get('username')
            invite = sponsor.get('invite_link')
        else:
            try:
                chat_id = int(sponsor)
            except:
                chat_id = sponsor
            uname = None
            invite = None

        is_subscribed = get_channel_status(user_id, chat_id)
        status_icon = "✅" if is_subscribed else "❌"

        if invite:
            channel_label = invite
            channel_url = invite
        else:
            # Kanal nomini (title) olish
            try:
                chat = bot.get_chat(chat_id)
                channel_label = chat.title or get_channel_username(chat_id)
                
                # URL uchun username bo'lsa @username, aks holda kanal ID
                if getattr(chat, 'username', None):
                    channel_url = f"https://t.me/{chat.username}"
                else:
                    channel_url = f"https://t.me/{str(chat_id).lstrip('-')}"
            except:
                channel_label = get_channel_username(chat_id)
                channel_url = f"https://t.me/{str(channel_label).lstrip('@')}"

        button_text = f"{status_icon} {channel_label}"
        markup.add(types.InlineKeyboardButton(text=button_text, url=channel_url))
    
    # Tekshirish tugmasi
    markup.add(types.InlineKeyboardButton(
        text="🔄️ Tekshirish",
        callback_data="check_sponsor_status"
    ))
    
    if message_id:
        # Mavjud message'ni o'zgartirish
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=sponsor_text,
                reply_markup=markup
            )
        except:
            bot.send_message(user_id, sponsor_text, reply_markup=markup)
    else:
        # Yangi message yuborish
        bot.send_message(user_id, sponsor_text, reply_markup=markup)

# ============= DATABASE FUNCTIONS =============

def migrate_users():
    """Eski users'larni migrate qilish - balance qo'shish"""
    all_users = db.all()
    for user in all_users:
        if 'balance' not in user:
            User = Query()
            db.update({'balance': 0.0}, User.user_id == user['user_id'])

def add_user(user_id: int, username: str):
    """Yangi foydalanuvchi qo'shish"""
    User = Query()
    if not db.search(User.user_id == user_id):
        db.insert({
            'user_id': user_id,
            'username': username,
            'balance': 0.0,
            'created_at': datetime.now().isoformat(),
            'orders': [],
            'is_banned': False
        })
    else:
        user = db.get(User.user_id == user_id)
        if 'balance' not in user:
            db.update({'balance': 0.0}, User.user_id == user_id)
        if 'is_banned' not in user:
            db.update({'is_banned': False}, User.user_id == user_id)

def get_user(user_id: int):
    """Foydalanuvchini olish"""
    User = Query()
    return db.get(User.user_id == user_id)

def get_user_balance(user_id: int) -> float:
    """Foydalanuvchining balansini olish"""
    user = get_user(user_id)
    if not user:
        return 0.0
    if 'balance' not in user:
        set_user_balance(user_id, 0.0)
        return 0.0
    return user.get('balance', 0.0)

def set_user_balance(user_id: int, balance: float):
    """Foydalanuvchining balansini o'rnatish"""
    User = Query()
    db.update({'balance': balance}, User.user_id == user_id)

def add_balance(user_id: int, amount: float):
    """Balans qo'shish"""
    current = get_user_balance(user_id)
    set_user_balance(user_id, current + amount)

def subtract_balance(user_id: int, amount: float) -> bool:
    """Balans kamaytirishni (agar yetarli bo'lsa)"""
    current = get_user_balance(user_id)
    if current >= amount:
        set_user_balance(user_id, current - amount)
        return True
    return False

def save_order(user_id: int, order_id: int, service_id: int, link: str, quantity: int, cost: float):
    """Order ma'lumotlarini saqlash"""
    User = Query()
    user = db.get(User.user_id == user_id)
    if user:
        orders = user['orders']
        orders.append({
            'order_id': order_id,
            'service_id': service_id,
            'link': link,
            'quantity': quantity,
            'cost': cost,
            'status': 'Bajarilayotgan',
            'created_at': datetime.now().isoformat()
        })
        db.update({'orders': orders}, User.user_id == user_id)

def get_user_orders(user_id: int) -> List:
    """Foydalanuvchining barcha order larini olish"""
    user = get_user(user_id)
    return user['orders'] if user else []

def ban_user(user_id: int) -> bool:
    """Foydalanuvchini banlash"""
    User = Query()
    user = db.get(User.user_id == user_id)
    if user:
        db.update({'is_banned': True}, User.user_id == user_id)
        return True
    return False

def unban_user(user_id: int) -> bool:
    """Foydalanuvchini bandan chiqarish"""
    User = Query()
    user = db.get(User.user_id == user_id)
    if user:
        db.update({'is_banned': False}, User.user_id == user_id)
        return True
    return False

def is_user_banned(user_id: int) -> bool:
    """Foydalanuvchi banlangan bo'lsa true qaytaradi"""
    user = get_user(user_id)
    return user.get('is_banned', False) if user else False

# ============= BOT HANDLERS =============

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Start command"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Migrate old users
    migrate_users()
    
    add_user(user_id, username)
    
    # Sponsor check
    if not check_sponsors(user_id):
        show_sponsor_message(user_id)
        return
    
    welcome_text = """
🎉 Xush kelibsiz! Telegram nakrutka bot-iga 🎉

Bu bot yordamida siz quyidagilarni qila olasiz:

📊 Followers, Comments, Views va boshqa xizmatlarni sifarish qilish
💰 Alohida balans bilan ishlash
📦 Sizning order'laringizni boshqarish

Tugmalarni bosing va boshlang! 👇
    """
    bot.send_message(user_id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "💰 Balans")
def balance_handler(message):
    """Balans ko'rish"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        show_sponsor_message(user_id)
        return
    
    user_balance = get_user_balance(user_id)
    
    balance_msg = f"""
💰 SIZNING BALANSINGIZ

Balans: {user_balance:.2f}{CURRENCY}
    """
    bot.send_message(user_id, balance_msg, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📊 Xizmatlar")
def services_handler(message):
    """Services list - kategoriyalarni ko'rsatish"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        show_sponsor_message(user_id)
        return
    
    services = get_all_services()
    categories = SETTINGS.get('categories', [])
    
    if isinstance(services, list) and len(services) > 0 and len(categories) > 0:
        # Kategoriya tugmalari
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        for category in sorted(categories, key=lambda x: x['name']):
            markup.add(telebot.types.KeyboardButton(f"📁 {category['name']}"))
        markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
        
        bot.send_message(user_id, "📋 XIZMATLAR KATEGORIYALARI\n\nKategoriyani tanlang:", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ Hech qanday xizmatlar mavjud emas!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text.startswith("📁 "))
def category_types_handler(message):
    """Tanlangan kategoriyaning turlarini ko'rsatish"""
    user_id = message.from_user.id
    category_name = message.text.replace("📁 ", "", 1)
    
    categories = SETTINGS.get('categories', [])
    category = next((c for c in categories if c['name'] == category_name), None)
    
    if not category:
        # Agar admin bo'lsa: topilmagan kategoriya uchun yangi kategoriya qo'shishni taklif qilamiz
        if message.from_user.id == ADMIN_ID:
            msg = bot.send_message(user_id, f"📁 '{category_name}' kategoriyasi topilmadi. Yangi kategoriya qo'shaymi? (Ha/Yo'q)", reply_markup=back_menu())
            bot.register_next_step_handler(msg, process_create_category_confirmation, category_name)
            return
        # Oddiy foydalanuvchi uchun xabar
        bot.send_message(user_id, "❌ Kategoriya topilmadi!", reply_markup=main_menu())
        return
    
    types_list = get_types(category['id'])
    
    if not types_list:
        bot.send_message(user_id, f"❌ {category_name} kategoriyasida turlar topilmadi!", reply_markup=main_menu())
        return
    
    # Tur tugmalari
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for service_type in sorted(types_list, key=lambda x: x['name']):
        markup.add(telebot.types.KeyboardButton(f"🔹 {service_type['name']}"))
    markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
    
    bot.send_message(user_id, f"📋 {category_name} - TURLAR\n\nTurni tanlang:", reply_markup=markup)


def process_create_category_confirmation(message, category_name):
    """Admindan yangi kategoriya qo'shishni tasdiqlashni qabul qiladi"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return

    answer = message.text.strip().lower()
    if answer in ['ha', 'yes', 'y']:
        if add_category(category_name):
            bot.send_message(message.from_user.id, f"✅ '{category_name}' kategoriyasi qo'shildi!", reply_markup=admin_menu())
        else:
            bot.send_message(message.from_user.id, "⚠️ Kategoriya qo'shilmadi — ehtimol allaqachon mavjud.", reply_markup=admin_menu())
    else:
        bot.send_message(message.from_user.id, "❌ Kategoriya qo'shish bekor qilindi.", reply_markup=admin_menu())

PAGE_SIZE = 10  # Har bir sahifada 10ta xizmat

@bot.message_handler(func=lambda message: message.text.startswith("🔹 "))
def type_services_handler(message):
    """Tanlangan turning xizmatlarini pagination bilan ko'rsatish"""
    user_id = message.from_user.id
    type_name = message.text.replace("🔹 ", "", 1)
    
    services = get_all_services()
    types_data = SETTINGS.get('types', [])
    
    service_type = next((t for t in types_data if t['name'] == type_name), None)
    if not service_type:
        bot.send_message(user_id, "❌ Tur topilmadi!", reply_markup=main_menu())
        return
    
    type_services = [s for s in services if s.get('type_id') == service_type['id']]
    
    if not type_services:
        bot.send_message(user_id, f"❌ {type_name} turida xizmatlar topilmadi!", reply_markup=main_menu())
        return
    
    # Pagination uchun birinchi sahifa
    send_services_page(user_id, type_services, type_name, page=1)


def send_services_page(user_id, services, type_name, page=1):
    """Xizmatlar ro'yxatini sahifa bilan yuborish"""
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_services = services[start_idx:end_idx]
    
    services_msg = f"📋 {type_name} - xizmatlar (sahifa {page})\n\n"
    for index, service in enumerate(page_services, start=start_idx + 1):
        name = service["name"]
        short_name = name[:20] + "..." if len(name) > 20 else name
        
        services_msg += f"{index}. {short_name} - {service['rate']}{CURRENCY}\n"

    
    # Inline tugmalar
    markup = types.InlineKeyboardMarkup()
    
    # Oldingi sahifa tugmasi
    if start_idx > 0:
        markup.add(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"page_{page-1}_{type_name}"))
    
    # Keyingi sahifa tugmasi
    if end_idx < len(services):
        markup.add(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"page_{page+1}_{type_name}"))
    
    bot.send_message(user_id, services_msg, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def paginate_services(call):
    """Pagination callback handler"""
    _, page, type_name = call.data.split("_", 2)
    page = int(page)
    
    services = get_all_services()
    types_data = SETTINGS.get('types', [])
    
    service_type = next((t for t in types_data if t['name'] == type_name), None)
    if not service_type:
        bot.answer_callback_query(call.id, "❌ Tur topilmadi!")
        return
    
    type_services = [s for s in services if s.get('type_id') == service_type['id']]
    
    # Sahifani yangilash
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_services_page(call.message.chat.id, type_services, type_name, page)


@bot.callback_query_handler(func=lambda call: call.data == "check_sponsor_status")
def check_sponsor_status(call):
    """Sponsor obunasi statusini tekshirish"""
    user_id = call.from_user.id
    
    # Message'ni o'chirish
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Tekshirish
    if check_sponsors(user_id):
        # Obuna bo'lganlar uchun welcome message
        welcome_text = """
🎉 Xush kelibsiz! Telegram nakrutka bot-iga 🎉

Bu bot yordamida siz quyidagilarni qila olasiz:

📊 Followers, Comments, Views va boshqa xizmatlarni sifarish qilish
💰 Alohida balans bilan ishlash
📦 Sizning order'laringizni boshqarish

Tugmalarni bosing va boshlang! 👇
        """
        bot.send_message(user_id, welcome_text, reply_markup=main_menu())
        bot.answer_callback_query(call.id, "✅ Obunangiz tasdiqlanishdi!", show_alert=True)
    else:
        # Hali obuna bo'lmagan uchun qayta sponsor message
        show_sponsor_message(user_id)
        bot.answer_callback_query(call.id, "❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=False)


@bot.message_handler(func=lambda message: message.text == "➕ Order qo'shish")
def add_order_start(message):
    """Add order - service ID so'rash"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        show_sponsor_message(user_id)
        return
    
    msg = bot.send_message(user_id, "🔢 Xizmat ID sini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_service_id, user_id)

def process_service_id(message, user_id):
    """Service ID processing"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(user_id, "Orqaga qaytdingiz", reply_markup=main_menu())
        return
    
    try:
        service_id = int(message.text)
        msg = bot.send_message(user_id, "🔗 Link'ni kiriting (Instagram, TikTok, Telegram va h.k.):", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_link, user_id, service_id)
    except ValueError:
        msg = bot.send_message(user_id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_service_id, user_id)

def process_link(message, user_id, service_id):
    """Link processing"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(user_id, "Orqaga qaytdingiz", reply_markup=main_menu())
        return
    
    link = message.text
    msg = bot.send_message(user_id, "📊 Miqdor'ni kiriting (Followers, Views, Likes):", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_quantity, user_id, service_id, link)

def process_quantity(message, user_id, service_id, link):
    """Quantity processing"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(user_id, "Orqaga qaytdingiz", reply_markup=main_menu())
        return
    
    try:
        quantity = int(message.text)
        
        # Sponsor check
        if not check_sponsors(user_id):
            show_sponsor_message(user_id)
            return
        
        # Balans tekshirish
        user_balance = get_user_balance(user_id)
        if user_balance <= 0:
            bot.send_message(user_id, "❌ Yetarli balans yo'q! Admin'dan balans ila'tisini so'rang", reply_markup=main_menu())
            return
        
        # API'ga order qo'shish
        result = add_order(service_id, link, quantity)
        
        if 'order' in result:
            order_id = result['order']
            cost = float(quantity) * 0.01  # Simple calculation
            
            # Balans kamaytirishni
            if subtract_balance(user_id, cost):
                save_order(user_id, order_id, service_id, link, quantity, cost)
                
                success_msg = f"""
✅ ORDER QABUL QILINDI

📦 Order ID: {order_id}
🔹 Xizmat ID: {service_id}
🔗 Link: {link}
📊 Miqdor: {quantity}
💵 Narxi: {cost:.2f}{CURRENCY}

Qolgan balans: {get_user_balance(user_id):.2f}{CURRENCY}
                """
                bot.send_message(user_id, success_msg, reply_markup=main_menu())
            else:
                bot.send_message(user_id, "❌ Yetarli balans yo'q!", reply_markup=main_menu())
        else:
            bot.send_message(user_id, f"❌ Xatolik: {result.get('error', 'Noma\'lum xatolik')}", reply_markup=main_menu())
    except ValueError:
        msg = bot.send_message(user_id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_quantity, user_id, service_id, link)

@bot.message_handler(func=lambda message: message.text == "📦 Mening order'larim")
def my_orders_handler(message):
    """My orders"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        show_sponsor_message(user_id)
        return
    
    orders = get_user_orders(user_id)
    
    if not orders:
        bot.send_message(user_id, "📭 Sizning order'laringiz yo'q", reply_markup=main_menu())
        return
    
    orders_msg = "📦 MENING ORDER'LARIM\n\n"
    for order in orders:
        order_text = f"""🔹 Order ID: {order['order_id']}
📝 Xizmat: {order['service_id']}
🔗 Link: {order['link']}
📊 Miqdor: {order['quantity']}
💵 Narxi: {order['cost']}{CURRENCY}
📅 Vaqti: {order['created_at'][:10]}
─────────────────────
"""
        if len(orders_msg) + len(order_text) > 3900:
            bot.send_message(user_id, orders_msg)
            orders_msg = "📦 MENING ORDER'LARIM (DAVOMI)\n\n" + order_text
        else:
            orders_msg += order_text
    
    if orders_msg.strip() != "📦 MENING ORDER'LARIM\n\n":
        bot.send_message(user_id, orders_msg, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "❓ Yordam")
def help_handler(message):
    """Help"""
    help_text = """
📖 YORDAM

💰 Balans - Sizning balansni ko'rish
📊 Xizmatlar - Barcha xizmatlar ro'yxatini ko'rish
➕ Order qo'shish - Yangi order qo'shish
📦 Mening order'larim - Sizning order'larni ko'rish
⚙️ Admin - Admin paneli (faqat admin uchun)

❓ Savol bo'lsa admin'ga murojaat qiling!
    """
    bot.send_message(message.from_user.id, help_text, reply_markup=main_menu())

# ============= ADMIN PANEL =============

@bot.message_handler(func=lambda message: message.text == "⚙️ Admin")
def admin_panel(message):
    """Admin panel"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Sizda ruxsat yo'q!")
        return
    
    admin_msg = "⚙️ ADMIN PANELI"
    bot.send_message(user_id, admin_msg, reply_markup=admin_menu())

# ============= CURRENCY FUNCTIONS =============

@bot.message_handler(func=lambda message: message.text == "💱 Valyuta o'zgartirish")
def change_currency_start(message):
    """Change currency"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    current_currency = SETTINGS.get('currency', '$')
    msg = bot.send_message(user_id, f"💱 Hozirgi valyuta: [{current_currency}]\n\nYangi valyuta nomini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_currency_change)

def process_currency_change(message):
    """Process currency change"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    global CURRENCY, SETTINGS
    new_currency = message.text.strip()
    
    if len(new_currency) > 5:
        bot.send_message(message.from_user.id, "❌ Valyuta nomi juda uzun! (5 belgi)", reply_markup=admin_menu())
        return
    
    CURRENCY = new_currency
    SETTINGS['currency'] = new_currency
    
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
    
    bot.send_message(message.from_user.id, f"✅ Valyuta o'zgartirildi: {new_currency}", reply_markup=admin_menu())

# ============= STATISTICS FUNCTIONS =============

def get_statistics():
    """Get statistics"""
    all_users = db.all()
    total_users = len(all_users)
    
    # Users by time period
    from datetime import datetime, timedelta
    now = datetime.now()
    users_24h = 0
    users_7d = 0
    users_30d = 0
    
    for user in all_users:
        created_at = datetime.fromisoformat(user.get('created_at', ''))
        diff = now - created_at
        if diff.days == 0:
            users_24h += 1
        if diff.days <= 7:
            users_7d += 1
        if diff.days <= 30:
            users_30d += 1
    
    # Users with balance
    users_with_balance = len([u for u in all_users if u.get('balance', 0) > 0])
    total_balance = sum([u.get('balance', 0) for u in all_users])
    
    return {
        'total_users': total_users,
        'users_24h': users_24h,
        'users_7d': users_7d,
        'users_30d': users_30d,
        'users_with_balance': users_with_balance,
        'total_balance': total_balance
    }

@bot.message_handler(func=lambda message: message.text == "📊 Statistika")
def statistics_handler(message):
    """Show statistics"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    stats = get_statistics()
    
    stats_msg = f"""
📊 STATISTIKA

👥 Obunachilar soni: {stats['total_users']} ta

📈 Obunachilar qo'shilishi
• Oxirgi 24 soat: +{stats['users_24h']} obunachi
• Oxirgi 7 kun: +{stats['users_7d']} obunachi
• Oxirgi 30 kun: +{stats['users_30d']} obunachi

💵 Pullar Statistikasi
• Puli borlar: {stats['users_with_balance']} ta
• Jami pullar: {stats['total_balance']:.2f}{CURRENCY}
    """
    
    # Inline keyboard
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💵 Top-50 balans", callback_data="top_50_balance"))
    
    bot.send_message(user_id, stats_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "top_50_balance")
def show_top_balance(call):
    """Show top 50 users by balance"""
    all_users = db.all()
    users_with_balance = [(u['user_id'], u.get('balance', 0)) for u in all_users if u.get('balance', 0) > 0]
    users_with_balance.sort(key=lambda x: x[1], reverse=True)
    top_50 = users_with_balance[:50]
    
    if not top_50:
        bot.answer_callback_query(call.id, "Puli borlar yo'q!")
        return
    
    top_msg = "💵 TOP-50 BALANS\n\n"
    for idx, (user_id, balance) in enumerate(top_50, 1):
        top_msg += f"{idx}. ID: {user_id} - {balance:.2f}{CURRENCY}\n"
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    # Paginate if too long
    if len(top_msg) > 3900:
        for i in range(0, len(top_50), 25):
            chunk = top_50[i:i+25]
            chunk_msg = "💵 TOP-50 BALANS\n\n"
            for idx, (user_id, balance) in enumerate(chunk, start=i+1):
                chunk_msg += f"{idx}. ID: {user_id} - {balance:.2f}{CURRENCY}\n"
            bot.send_message(call.message.chat.id, chunk_msg)
    else:
        bot.send_message(call.message.chat.id, top_msg)

@bot.message_handler(func=lambda message: message.text == "🛍️ Xizmatlar")
def services_page(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    # Admin services management menu
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("➕ Kategoriya qo'shish"),
        telebot.types.KeyboardButton("➖ Kategoriya o'chirish"),
        telebot.types.KeyboardButton("📌 Tur qo'shish"),
        telebot.types.KeyboardButton("🗑 Tur o'chirish"),
        telebot.types.KeyboardButton("🗂 Xizmat qo'shish"),
        telebot.types.KeyboardButton("📂 Xizmat o'chirish"),
        telebot.types.KeyboardButton("⬅️ Orqaga")
    )

    bot.send_message(user_id, "🛍️ Xizmatlar — Admin boshqaruvi\n\nKerakli amaliyotni tanlang:", reply_markup=markup)

# ============= MESSAGE SENDING =============

@bot.message_handler(func=lambda message: message.text == "💬 Xabar yuborish")
def send_message_start(message):
    """Send message to all users"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "💬 Foydalanuvchilarga yuborish uchun xabarni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_send_message)

def process_send_message(message):
    """Process message to send"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    text = message.text
    all_users = db.all()
    
    bot.send_message(message.from_user.id, "✅ Xabar yuborish boshlandi!")
    
    succeeded = 0
    failed = 0
    
    for idx, user in enumerate(all_users):
        try:
            bot.send_message(user['user_id'], text)
            succeeded += 1
            
            # Rate limiting - Telegram limits (30 msg/sec)
            if idx % 30 == 0:
                time.sleep(1)
        except Exception as e:
            failed += 1
    
    result_msg = f"""
✅ Xabar yuborish yakunlandi!

📨 Muvaffaqiyatli: {succeeded} ta
❌ Xatoli: {failed} ta
    """
    bot.send_message(message.from_user.id, result_msg, reply_markup=admin_menu())

# ============= MANDATORY SUBSCRIPTION =============

@bot.message_handler(func=lambda message: message.text == "🔒 Majburiy obuna")
def mandatory_subscription_menu(message):
    """Mandatory subscription menu"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("🔒 Kanallar"),
        telebot.types.KeyboardButton("➕ Kanal qo'shish"),
        telebot.types.KeyboardButton("➖ Kanal o'chirish"),
        telebot.types.KeyboardButton("⬅️ Orqaga")
    )
    
    bot.send_message(user_id, "🔐 MAJBURIY OBUNA BOSHQARISH", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔒 Kanallar")
def show_channels(message):
    """Show subscription channels"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    if not SPONSOR_CHANNELS:
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        bot.send_message(user_id, "📭 Majburiy obuna kanallar yo'q", reply_markup=markup.add(
        telebot.types.KeyboardButton("🔒 Kanallar"),
        telebot.types.KeyboardButton("➕ Kanal qo'shish"),
        telebot.types.KeyboardButton("➖ Kanal o'chirish"),
        telebot.types.KeyboardButton("⬅️ Orqaga")
    ))
        return
    
    channels_msg = "🔒 MAJBURIY OBUNA KANALLAR:\n\n"
    for idx, sponsor in enumerate(SPONSOR_CHANNELS, 1):
        if isinstance(sponsor, dict):
            if sponsor.get('username'):
                label = f"@{sponsor.get('username')}"
            elif sponsor.get('invite_link'):
                label = sponsor.get('invite_link')
            else:
                label = str(sponsor.get('id'))
        else:
            label = str(sponsor)
        channels_msg += f"{idx}. {label}\n"
    
    bot.send_message(user_id, channels_msg, reply_markup=back_menu())

@bot.message_handler(func=lambda message: message.text == "➕ Kanal qo'shish", content_types=['text', 'document'])
def add_channel_forwarded(message):
    """Add channel (forwarded post)"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "➕ Kanal postini forward qilib yuboring (Bot kanal ID'ni olib, administrator ekanini tekshiradi):", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_channel_from_forward)

@bot.message_handler(func=lambda message: message.text == "➕ Kanal qo'shish")
def add_channel_start(message):
    """Add channel start"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "➕ Kanal postini forward qilib yuboring (Bot kanal ID'ni olib, administrator ekanini tekshiradi):", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_channel_from_forward)

def process_add_channel_from_forward(message):
    """Process channel from forward"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Orqaga qaytdingiz", reply_markup=back_menu())
        return
    
    # Check if message is forwarded
    if not message.forward_from_chat:
        bot.send_message(message.from_user.id, "❌ Post forward qilishi kerak! Qayta urinib ko'ring:", reply_markup=back_menu())
        msg = bot.register_next_step_handler(message, process_add_channel_from_forward)
        return
    
    channel_id = message.forward_from_chat.id
    
    # Check if bot is admin
    try:
        bot_member = bot.get_chat_member(channel_id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.send_message(message.from_user.id, "❌ Bot bu kanalde administrator emas!", reply_markup=back_menu())
            return

        # Try to get chat info (to obtain username)
        try:
            chat = bot.get_chat(channel_id)
        except Exception:
            chat = None

        global SPONSOR_CHANNELS, SETTINGS

        # If public (has username) - save id only (no username)
        if chat and getattr(chat, 'username', None):
            sponsor = {'id': channel_id, 'username': None, 'invite_link': None}
            # avoid duplicates
            if not any(str(s.get('id')) == str(channel_id) for s in SPONSOR_CHANNELS):
                SPONSOR_CHANNELS.append(sponsor)
                SETTINGS['sponsors'] = SPONSOR_CHANNELS
                with open('settings.json', 'w', encoding='utf-8') as f:
                    json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
                bot.send_message(message.from_user.id, f"✅ Kanal qo'shildi: @{chat.username}", reply_markup=back_menu())
            else:
                bot.send_message(message.from_user.id, "⚠️ Bu kanal allaqachon majburiy obuna ekan!", reply_markup=back_menu())
            return

        # Otherwise channel may be private - ask for invite link
        msg = bot.send_message(message.from_user.id, "⚠️ Kanal yopiq ekan, kanal sozlamalaridan invite link oling va botga tashlang:\n\nIltimos invite linkni yuboring:", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_add_channel_invite_link, channel_id)
    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Xatoli: {str(e)}", reply_markup=back_menu())


def process_add_channel_invite_link(message, channel_id):
    """Process invite link sent by admin for a private channel"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Orqaga qaytdingiz", reply_markup=back_menu())
        return

    link = message.text.strip()
    ok, info = check_invite_link(link)
    if not ok:
        bot.send_message(message.from_user.id, f"❌ Invite link yaroqsiz: {info}", reply_markup=back_menu())
        return

    # try to extract chat id from info
    chat_id = None
    try:
        # info may be an object with .chat or a dict
        if hasattr(info, 'chat') and getattr(info.chat, 'id', None):
            chat_id = info.chat.id
        elif isinstance(info, dict) and info.get('chat') and info['chat'].get('id'):
            chat_id = info['chat']['id']
    except:
        chat_id = None

    # fallback to forwarded channel_id if chat_id not obtained
    if not chat_id:
        chat_id = channel_id

    sponsor = {'id': chat_id, 'username': None, 'invite_link': link}
    global SPONSOR_CHANNELS, SETTINGS
    if not any(str(s.get('id')) == str(chat_id) or s.get('invite_link') == link for s in SPONSOR_CHANNELS):
        SPONSOR_CHANNELS.append(sponsor)
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        bot.send_message(message.from_user.id, f"✅ Private kanal invite link bilan saqlandi.", reply_markup=back_menu())
    else:
        bot.send_message(message.from_user.id, "⚠️ Bu kanal allaqachon mavjud!", reply_markup=back_menu())

@bot.message_handler(func=lambda message: message.text == "➖ Kanal o'chirish")
def remove_channel_start(message):
    """Remove channel"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    if not SPONSOR_CHANNELS:
        bot.send_message(user_id, "📭 Ochirilishi kerak bo'lgan kanal yo'q", reply_markup=back_menu())
        return
    
    channels_msg = "➖ O'CHIRILISHI KERAK BO'LGAN KANALLAR:\n\n"
    for idx, sponsor in enumerate(SPONSOR_CHANNELS, 1):
        if isinstance(sponsor, dict):
            if sponsor.get('username'):
                label = f"@{sponsor.get('username')}"
            elif sponsor.get('invite_link'):
                label = sponsor.get('invite_link')
            else:
                label = str(sponsor.get('id'))
        else:
            label = str(sponsor)
        channels_msg += f"{idx}. {label}\n"
    
    msg = bot.send_message(user_id, channels_msg + "\n\nKanal ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_remove_channel)

def process_remove_channel(message):
    """Process remove channel"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Orqaga qaytdingiz", reply_markup=back_menu())
        return
    
    global SPONSOR_CHANNELS, SETTINGS
    identifier = message.text.strip()

    removed = False
    for s in list(SPONSOR_CHANNELS):
        sid = str(s.get('id')) if isinstance(s, dict) else str(s)
        sun = s.get('username') if isinstance(s, dict) else None
        sinvite = s.get('invite_link') if isinstance(s, dict) else None
        if identifier == sid or (sun and identifier.lstrip('@') == str(sun)) or (sinvite and identifier == sinvite):
            SPONSOR_CHANNELS.remove(s)
            removed = True
            break

    if removed:
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        bot.send_message(message.from_user.id, f"✅ Kanal o'chirildi: {identifier}", reply_markup=back_menu())
    else:
        bot.send_message(message.from_user.id, "❌ Bu kanal topilmadi!", reply_markup=back_menu())

def process_api_key(message):
    """Process API key"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    global API_KEY, SETTINGS
    API_KEY = message.text.strip()
    SETTINGS['api_key'] = API_KEY
    
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
    
    bot.send_message(message.from_user.id, "✅ API Kaliti o'zlashtirilib bo'ldi!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🔑 API kalit")
def set_api_key_start(message):
    """Set API key"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "🔑 Yangi API Kalitini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_api_key)

@bot.message_handler(func=lambda message: message.text == "➕ Sponsor qo'shish")
def add_sponsor_start(message):
    """Add sponsor channel"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "📢 Sponsor kanal ID'ni kiriting (masalan: -1001234567890):", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_sponsor)

def process_add_sponsor(message):
    """Process add sponsor"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    global SPONSOR_CHANNELS, SETTINGS
    raw = message.text.strip()
    # try as id or username
    try:
        # if it's an invite link
        if raw.startswith('https://t.me/') or 'joinchat' in raw or 'invite' in raw:
            ok, info = check_invite_link(raw)
            if not ok:
                bot.send_message(message.from_user.id, f"❌ Invite link yaroqsiz: {info}", reply_markup=admin_menu())
                return
            # try to get chat id from info
            chat_id = None
            try:
                if hasattr(info, 'chat') and getattr(info.chat, 'id', None):
                    chat_id = info.chat.id
                elif isinstance(info, dict) and info.get('chat') and info['chat'].get('id'):
                    chat_id = info['chat']['id']
            except:
                chat_id = None
            sponsor = {'id': chat_id or raw, 'username': None, 'invite_link': raw}
        else:
            # try to resolve chat (id or @username)
            try:
                chat = bot.get_chat(raw)
                uname = getattr(chat, 'username', None)
                sponsor = {'id': chat.id if getattr(chat, 'id', None) else raw, 'username': uname, 'invite_link': None}
            except Exception:
                # fallback: store as id-like
                try:
                    sponsor = {'id': int(raw), 'username': None, 'invite_link': None}
                except:
                    sponsor = {'id': raw, 'username': None, 'invite_link': None}

    except Exception as e:
        bot.send_message(message.from_user.id, f"❌ Xatolik: {e}", reply_markup=admin_menu())
        return

    # avoid duplicates by id or invite
    exists = any(str(s.get('id')) == str(sponsor.get('id')) or (s.get('invite_link') and sponsor.get('invite_link') and s.get('invite_link') == sponsor.get('invite_link')) for s in SPONSOR_CHANNELS)
    if not exists:
        SPONSOR_CHANNELS.append(sponsor)
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        bot.send_message(message.from_user.id, f"✅ Sponsor kanal qo'shildi.", reply_markup=admin_menu())
    else:
        bot.send_message(message.from_user.id, "⚠️ Bu kanal allaqachon mavjud!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "➖ Sponsor o'chirish")
def remove_sponsor_start(message):
    """Remove sponsor channel"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "📢 O'chirilishi kerak bo'lgan kanal ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_remove_sponsor)

def process_remove_sponsor(message):
    """Process remove sponsor"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    global SPONSOR_CHANNELS, SETTINGS
    identifier = message.text.strip()

    removed = False
    for s in list(SPONSOR_CHANNELS):
        sid = str(s.get('id')) if isinstance(s, dict) else str(s)
        sun = s.get('username') if isinstance(s, dict) else None
        sinvite = s.get('invite_link') if isinstance(s, dict) else None
        if identifier == sid or (sun and identifier.lstrip('@') == str(sun)) or (sinvite and identifier == sinvite):
            SPONSOR_CHANNELS.remove(s)
            removed = True
            break

    if removed:
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        bot.send_message(message.from_user.id, f"✅ Sponsor kanal o'chirildi: {identifier}", reply_markup=admin_menu())
    else:
        bot.send_message(message.from_user.id, "❌ Bu kanal topilmadi!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "📋 Sponsor'lar ro'yxati")
def sponsors_list(message):
    """Sponsors list"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    if not SPONSOR_CHANNELS:
        bot.send_message(user_id, "📭 Sponsor kanallar yo'q", reply_markup=admin_menu())
        return
    
    list_msg = "📢 SPONSOR KANALLAR:\n\n"
    for idx, sponsor in enumerate(SPONSOR_CHANNELS, 1):
        if isinstance(sponsor, dict):
            if sponsor.get('username'):
                label = f"@{sponsor.get('username')}"
            elif sponsor.get('invite_link'):
                label = sponsor.get('invite_link')
            else:
                label = str(sponsor.get('id'))
        else:
            label = str(sponsor)
        list_msg += f"{idx}. {label}\n"
    
    bot.send_message(user_id, list_msg, reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🔍 Foydalanuvchi boshqarish")
def user_management_start(message):
    """User management - ask for user ID"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "👤 Foydalanuvchi ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_user_id_for_management)

def process_user_id_for_management(message):
    """Process user ID for management"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        target_user_id = int(message.text)
        user = get_user(target_user_id)
        
        if not user:
            bot.send_message(message.from_user.id, "❌ Foydalanuvchi topilmadi!", reply_markup=admin_menu())
            return
        
        # Show user info with inline buttons
        is_banned = is_user_banned(target_user_id)
        user_info = f"""
✅ FOYDALANUVCHI TOPILDI!

🆔 ID raqami: {target_user_id}
👤 Username: {user.get('username', 'Noma\'lum')}
💵 Balansi: {user.get('balance', 0):.2f}{CURRENCY}  
📊 Buyurtmalari: {len(user.get('orders', []))} ta
🚫 Ban: {'Ha' if is_banned else 'Yo\'q'}
        """
        
        markup = types.InlineKeyboardMarkup()
        
        # Ban/Unban button
        if is_banned:
            markup.add(types.InlineKeyboardButton("🔓 Bandan chiqarish", callback_data=f"unban_user_{target_user_id}"))
        else:
            markup.add(types.InlineKeyboardButton("🚫 Banlash", callback_data=f"ban_user_{target_user_id}"))
        
        # Balance buttons
        markup.add(
            types.InlineKeyboardButton("➕ Pul qo'shish", callback_data=f"add_balance_{target_user_id}"),
            types.InlineKeyboardButton("➖ Pul ayirish", callback_data=f"reduce_balance_{target_user_id}")
        )
        
        bot.send_message(message.from_user.id, user_info, reply_markup=markup)
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("ban_user_"))
def user_ban_callback(call):
    """Ban user"""
    target_user_id = int(call.data.replace("ban_user_", ""))
    
    if ban_user(target_user_id):
        bot.answer_callback_query(call.id, f"✅ Foydalanuvchi {target_user_id} banlandi!", show_alert=True)
        bot.edit_message_text("🚫 Foydalanuvchi banlandi!", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Xatolik!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unban_user_"))
def user_unban_callback(call):
    """Unban user"""
    target_user_id = int(call.data.replace("unban_user_", ""))
    
    if unban_user(target_user_id):
        bot.answer_callback_query(call.id, f"✅ Foydalanuvchi {target_user_id} bandan chiqarildi!", show_alert=True)
        bot.edit_message_text("🔓 Foydalanuvchi bandan chiqarildi!", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Xatolik!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_balance_"))
def add_balance_callback(call):
    """Add balance callback"""
    target_user_id = int(call.data.replace("add_balance_", ""))
    msg = bot.send_message(call.message.chat.id, "💵 Qo'shish miqdorini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_user_balance, target_user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reduce_balance_"))
def reduce_balance_callback(call):
    """Reduce balance callback"""
    target_user_id = int(call.data.replace("reduce_balance_", ""))
    msg = bot.send_message(call.message.chat.id, "💵 Ayirish miqdorini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_reduce_user_balance, target_user_id)

def process_add_user_balance(message, target_user_id):
    """Process adding balance"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        amount = float(message.text)
        old_balance = get_user_balance(target_user_id)
        add_balance(target_user_id, amount)
        new_balance = get_user_balance(target_user_id)
        
        result_msg = f"""
✅ BALANS O'ZGARTIRILDI

Foydalanuvchi ID: {target_user_id}
➕ Qo'shildi: {amount:.2f}{CURRENCY}

Eski balans: {old_balance:.2f}{CURRENCY}
Yangi balans: {new_balance:.2f}{CURRENCY}
        """
        bot.send_message(message.from_user.id, result_msg, reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

def process_reduce_user_balance(message, target_user_id):
    """Process reducing balance"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        amount = float(message.text)
        old_balance = get_user_balance(target_user_id)
        add_balance(target_user_id, -amount)
        new_balance = get_user_balance(target_user_id)
        
        result_msg = f"""
✅ BALANS O'ZGARTIRILDI

Foydalanuvchi ID: {target_user_id}
➖ Ayirildi: {amount:.2f}{CURRENCY}

Eski balans: {old_balance:.2f}{CURRENCY}
Yangi balans: {new_balance:.2f}{CURRENCY}
        """
        bot.send_message(message.from_user.id, result_msg, reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🛍️ Buyurtmalar")
def orders_admin_handler(message):
    """Show orders statistics with real statuses from API"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    all_users = db.all()
    total_orders = 0
    status_counts = {
        'Completed': 0,
        'In progress': 0,
        'Partial': 0,
        'Cancelled': 0,
        'Unknown': 0
    }
    
    all_order_ids = []
    order_map = {}  # order_id -> user_id mapping
    
    # Collect all order IDs
    for user in all_users:
        for order in user.get('orders', []):
            order_id = order.get('order_id')
            if order_id:
                all_order_ids.append(order_id)
                order_map[str(order_id)] = (user.get('user_id'), order)
                total_orders += 1
    
    # Fetch statuses from API (batched)
    if all_order_ids:
        statuses = get_multiple_orders_status(all_order_ids)
        for order_id_str, status_data in statuses.items():
            if isinstance(status_data, dict):
                status = status_data.get('status', 'Unknown')
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['Unknown'] += 1
    
    orders_msg = f"""
📈 BUYURTMALAR STATISTIKASI

📊 Jami Buyurtmalar: {total_orders} ta

✅ Bajarilganlar: {status_counts['Completed']} ta
⛔️ Bekor qilinganlar: {status_counts['Cancelled']} ta
⏳ Bajarilayotganlar: {status_counts['In progress']} ta
🔄 Qismiy bajarilganlar: {status_counts['Partial']} ta
❓ Noma'lumi: {status_counts['Unknown']} ta
    """
    
    # Add button to see detailed orders list
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Batafsil ro'yxat", callback_data="orders_detailed_list"))
    
    bot.send_message(user_id, orders_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "orders_detailed_list")
def orders_detailed_list(call):
    """Show detailed orders list"""
    all_users = db.all()
    all_order_ids = []
    order_map = {}  # order_id -> (user_id, user_username, order_data) mapping
    
    # Collect all order IDs
    for user in all_users:
        for order in user.get('orders', []):
            order_id = order.get('order_id')
            if order_id:
                all_order_ids.append(order_id)
                order_map[str(order_id)] = (user.get('user_id'), user.get('username', 'N/A'), order)
    
    if not all_order_ids:
        bot.edit_message_text("📭 Buyurtmalar yo'q", call.message.chat.id, call.message.message_id)
        return
    
    # Fetch statuses from API
    statuses = get_multiple_orders_status(all_order_ids)
    
    # Status emojis
    status_emoji = {
        'Completed': '✅',
        'In progress': '⏳',
        'Partial': '🔄',
        'Cancelled': '⛔️'
    }
    
    orders_list = "📋 BARCHA BUYURTMALAR\n\n"
    for i, (order_id_str, status_data) in enumerate(statuses.items(), 1):
        if isinstance(status_data, dict) and 'error' not in status_data:
            user_id, username, order_data = order_map.get(order_id_str, (None, 'N/A', {}))
            status = status_data.get('status', 'Unknown')
            emoji = status_emoji.get(status, '❓')
            remains = status_data.get('remains', '0')
            
            order_text = f"{emoji} Order {order_id_str}: {username} | {status} ({remains} qolgan)\n"
            
            # Limit message length
            if len(orders_list) + len(order_text) > 3900:
                bot.send_message(call.message.chat.id, orders_list)
                orders_list = "📋 BARCHA BUYURTMALAR (DAVOMI)\n\n" + order_text
            else:
                orders_list += order_text
    
    if orders_list.strip() != "📋 BARCHA BUYURTMALAR\n\n":
        bot.edit_message_text(orders_list, call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("📭 Buyurtmalar yo'q", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "🗂 Xizmat qo'shish")
@bot.message_handler(func=lambda message: message.text == "➕ Xizmat qo'shish")
def add_service_start(message):
    """Add custom service - kategoriya tanlash"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    categories = get_categories()
    if not categories:
        bot.send_message(user_id, "❌ Birinchi kategoriya qo'shing!", reply_markup=admin_menu())
        return
    
    # Kategoriya tugmalari
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in sorted(categories, key=lambda x: x['name']):
        markup.add(telebot.types.KeyboardButton(f"📁 {category['name']}"))
    markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
    
    msg = bot.send_message(user_id, "📁 Kategoriyani tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_service_category)

def process_service_category(message):
    """Process service category selection"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    category_name = message.text.replace("📁 ", "", 1)
    categories = get_categories()
    category = next((c for c in categories if c['name'] == category_name), None)
    
    if not category:
        msg = bot.send_message(message.from_user.id, "❌ Kategoriya topilmadi! Qayta tanlang:", reply_markup=admin_menu())
        bot.register_next_step_handler(msg, process_service_category)
        return
    
    types_list = get_types(category['id'])
    if not types_list:
        bot.send_message(message.from_user.id, "❌ Bu kategoriyasida tur yo'q! Tur qo'shing va qayta urinib ko'ring.", reply_markup=admin_menu())
        return
    
    # Tur tugmalari
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for service_type in sorted(types_list, key=lambda x: x['name']):
        markup.add(telebot.types.KeyboardButton(f"🔹 {service_type['name']}"))
    markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
    
    msg = bot.send_message(message.from_user.id, f"🔹 {category_name} - Turni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_service_type, category['id'])

def process_service_type(message, category_id):
    """Process service type selection"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    type_name = type_name = message.text.replace("🔹 ", "", 1)
    types_list = get_types(category_id)
    service_type = next((t for t in types_list if t['name'] == type_name), None)
    
    if not service_type:
        msg = bot.send_message(message.from_user.id, "❌ Tur topilmadi! Qayta tanlang:", reply_markup=admin_menu())
        bot.register_next_step_handler(msg, process_service_type, category_id)
        return
    
    msg = bot.send_message(message.from_user.id, "🔢 Xizmat ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_service_id_for_add, category_id, service_type['id'])

def process_service_id_for_add(message, category_id, type_id):
    """Process service ID for adding"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        service_id = int(message.text)
        
        # Check if service exists
        custom_services = get_custom_services()
        if any(s['service_id'] == service_id for s in custom_services):
            bot.send_message(message.from_user.id, "❌ Bu xizmat ID allaqachon mavjud!", reply_markup=admin_menu())
            return
        
        # API dan xizmatni qidirish
        try:
            api_services = get_services()
            if isinstance(api_services, list):
                service_info = next((s for s in api_services if s.get('service') == service_id), None)
                if not service_info:
                    bot.send_message(message.from_user.id, f"❌ Xizmat ID {service_id} API'da topilmadi!", reply_markup=admin_menu())
                    return
                
                msg = bot.send_message(message.from_user.id, f"💵 Xizmat narxini kiriting (USD) [API narxi: ${service_info.get('rate', 'N/A')}]:", reply_markup=back_menu())
                bot.register_next_step_handler(msg, process_service_price_add, service_id, service_info.get('name', 'Noma\'lum'), category_id, type_id)
            else:
                msg = bot.send_message(message.from_user.id, "💵 Xizmat narxini kiriting (USD):", reply_markup=back_menu())
                bot.register_next_step_handler(msg, process_service_price_add, service_id, f"Service {service_id}", category_id, type_id)
        except:
            msg = bot.send_message(message.from_user.id, "💵 Xizmat narxini kiriting (USD):", reply_markup=back_menu())
            bot.register_next_step_handler(msg, process_service_price_add, service_id, f"Service {service_id}", category_id, type_id)
    except ValueError:
        msg = bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_service_id_for_add, category_id, type_id)

def process_service_price_add(message, service_id, service_name, category_id, type_id):
    """Process service price"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        price = float(message.text)
        
        # Add service
        if add_custom_service(service_id, service_name, price, category_id, type_id):
            success_msg = f"""
✅ XIZMAT QO'SHILDI

🔢 ID: {service_id}
📝 Nomi: {service_name}
💵 Narxi: ${price:.2f}
            """
            bot.send_message(message.from_user.id, success_msg, reply_markup=admin_menu())
        else:
            bot.send_message(message.from_user.id, "❌ Xizmat qo'shishda xatolik! (Kategoriya yoki tur mavjud emas)", reply_markup=admin_menu())
    except ValueError:
        msg = bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_service_price_add, service_id, service_name, category_id, type_id)

@bot.message_handler(func=lambda message: message.text == "➕ Kategoriya qo'shish")
def add_category_start(message):
    """Add new category"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "📝 Kategoriya nomini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_category)

def process_add_category(message):
    """Process add category"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    category_name = message.text.strip()
    
    if add_category(category_name):
        bot.send_message(message.from_user.id, f"✅ '{category_name}' kategoriyasi qo'shildi!", reply_markup=admin_menu())
    else:
        bot.send_message(message.from_user.id, "❌ Bu kategoriya allaqachon mavjud!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "📌 Tur qo'shish")
def add_type_start(message):
    """Add new type to category"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    categories = get_categories()
    if not categories:
        bot.send_message(user_id, "❌ Birinchi kategoriya qo'shing!", reply_markup=admin_menu())
        return
    
    # Kategoriya tugmalari
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in sorted(categories, key=lambda x: x['name']):
        markup.add(telebot.types.KeyboardButton(f"📁 {category['name']}"))
    markup.add(telebot.types.KeyboardButton("⬅️ Orqaga"))
    
    msg = bot.send_message(user_id, "📁 Kategoriyani tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_type_category)

def process_type_category(message):
    """Process category selection for type"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    category_name = message.text.replace("📁 ", "", 1)
    categories = get_categories()
    category = next((c for c in categories if c['name'] == category_name), None)
    
    if not category:
        msg = bot.send_message(message.from_user.id, "❌ Kategoriya topilmadi! Qayta tanlang:", reply_markup=admin_menu())
        bot.register_next_step_handler(msg, process_type_category)
        return
    
    msg = bot.send_message(message.from_user.id, f"📝 {category_name} - Tur nomini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_add_type_name, category['id'])

def process_add_type_name(message, category_id):
    """Process add type name"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    type_name = message.text.strip()
    
    if add_type(category_id, type_name):
        bot.send_message(message.from_user.id, f"✅ '{type_name}' turi qo'shildi!", reply_markup=admin_menu())
    else:
        bot.send_message(message.from_user.id, "❌ Bu tur allaqachon mavjud!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "➖ Kategoriya o'chirish")
def remove_category_start(message):
    """Remove category (and dependent types/services)"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return

    categories = get_categories()
    if not categories:
        bot.send_message(user_id, "❌ O'chirilishi kerak bo'lgan kategoriya yo'q", reply_markup=admin_menu())
        return

    categories_list = "🗑️ O'CHIRILISHI MUMKIN BO'LGAN KATEGORIYALAR\n\n"
    for c in categories:
        categories_list += f"🔹 ID: {c['id']} - {c['name']}\n"

    msg = bot.send_message(user_id, categories_list + "\n\nKategoriya ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_remove_category)

def process_remove_category(message):
    """Process remove category"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return

    try:
        category_id = int(message.text)
        if remove_category(category_id):
            bot.send_message(message.from_user.id, f"✅ Kategoriya {category_id} o'chirildi! (Turlar va xizmatlar ham o'chirildi)", reply_markup=admin_menu())
        else:
            bot.send_message(message.from_user.id, "❌ Bu kategoriya topilmadi!", reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🗑 Tur o'chirish")
@bot.message_handler(func=lambda message: message.text == "➖ Tur o'chirish")
def remove_type_start(message):
    """Remove type (and dependent services)"""
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return

    types_data = SETTINGS.get('types', [])
    if not types_data:
        bot.send_message(user_id, "❌ O'chirilishi kerak bo'lgan tur yo'q", reply_markup=admin_menu())
        return

    # build types list with category names
    categories = get_categories()
    cat_map = {c['id']: c['name'] for c in categories}

    types_list = "🗑️ O'CHIRILISHI MUMKIN BO'LGAN TURLAR\n\n"
    for t in types_data:
        types_list += f"🔹 ID: {t['id']} - {t['name']} (Kategoriya: {cat_map.get(t['category_id'], 'Noma\'lum')})\n"

    msg = bot.send_message(user_id, types_list + "\n\nTur ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_remove_type)

def process_remove_type(message):
    """Process remove type"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return

    try:
        type_id = int(message.text)
        if remove_type(type_id):
            bot.send_message(message.from_user.id, f"✅ Tur {type_id} o'chirildi! (Unga tegishli xizmatlar ham o'chirildi)", reply_markup=admin_menu())
        else:
            bot.send_message(message.from_user.id, "❌ Bu tur topilmadi!", reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "📂 Xizmat o'chirish")
@bot.message_handler(func=lambda message: message.text == "➖ Xizmat o'chirish")
def remove_service_start(message):
    """Remove custom service"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    custom_services = get_custom_services()
    if not custom_services:
        bot.send_message(user_id, "❌ O'chirilishi kerak bo'lgan xizmatlar yo'q", reply_markup=admin_menu())
        return
    
    services_list = "🗑️ O'CHIRILISHI MUMKIN BO'LGAN XIZMATLAR\n\n"
    for service in custom_services:
        services_list += f"🔹 ID: {service['service_id']} - {service['name']} (${service['price']})\n"
    
    msg = bot.send_message(user_id, services_list + "\n\nXizmat ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_remove_service)

def process_remove_service(message):
    """Process remove service"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        service_id = int(message.text)
        
        if remove_custom_service(service_id):
            bot.send_message(message.from_user.id, f"✅ Xizmat {service_id} o'chirildi!", reply_markup=admin_menu())
        else:
            bot.send_message(message.from_user.id, "❌ Bu xizmat topilmadi!", reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "💵 Foydalanuvchi balansini o'zgartirish")
def change_user_balance_start(message):
    """Change user balance"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "👤 Foydalanuvchi ID'ni kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_user_id_for_balance)

def process_user_id_for_balance(message):
    """Process user ID for balance change"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        target_user_id = int(message.text)
        user = get_user(target_user_id)
        
        if not user:
            bot.send_message(message.from_user.id, "❌ Foydalanuvchi topilmadi!", reply_markup=admin_menu())
            return
        
        msg = bot.send_message(message.from_user.id, f"💵 {user['username']} uchun miqdor kiriting (musbat raqam qo'shishi, manfiy raqam kamaytirishini ko'rsatadi):", reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_balance_amount, target_user_id)
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format!", reply_markup=admin_menu())

def process_balance_amount(message, target_user_id):
    """Process balance amount"""
    if message.text == "⬅️ Orqaga":
        bot.send_message(message.from_user.id, "Admin paneliga qaytdingiz", reply_markup=admin_menu())
        return
    
    try:
        amount = float(message.text)
        current_balance = get_user_balance(target_user_id)
        
        if amount > 0:
            add_balance(target_user_id, amount)
            action = f"➕ Qo'shildi"
        else:
            add_balance(target_user_id, amount)
            action = f"➖ Kamaytirildi"
        
        new_balance = get_user_balance(target_user_id)
        result_msg = f"""
✅ BALANS O'ZGARTIRILDI

Foydalanuvchi ID: {target_user_id}
{action}: {abs(amount):.2f}{CURRENCY}

Eski balans: {current_balance:.2f}{CURRENCY}
Yangi balans: {new_balance:.2f}{CURRENCY}
        """
        bot.send_message(message.from_user.id, result_msg, reply_markup=admin_menu())
    except ValueError:
        bot.send_message(message.from_user.id, "❌ Noto'g'ri format! Raqam kiriting:", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "👥 Foydalanuvchilar soni")
def users_count(message):
    """Users count"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    count = len(db.all())
    bot.send_message(user_id, f"👥 Jami foydalanuvchilari: {count}", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "⬅️ Orqaga")
def back_to_menu(message):
    """Back to main menu"""
    user_id = message.from_user.id
    bot.send_message(user_id, "Bosh menu", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Default message handler"""
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        bot.send_message(user_id, "❓ Noto'g'ri buyruq!", reply_markup=admin_menu())
    else:
        bot.send_message(user_id, "❓ Noto'g'ri buyruq! Tugmalarni bosing.", reply_markup=main_menu())

# ============= BOT START =============

if __name__ == '__main__':
    print("🤖 Bot ishga tushdi...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
