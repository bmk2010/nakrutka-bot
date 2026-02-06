import telebot
from telebot import types
import requests
import json
from tinydb import TinyDB, Query
from datetime import datetime
from typing import Optional, Dict, List

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
        'sponsors': []
    }
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(SETTINGS, f, indent=4, ensure_ascii=False)

# Bot initialization
BOT_TOKEN = '8400775067:AAHq1cek_BWwmE59__P_q-wh2_1UBPkuADA'
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = SETTINGS['admin_id']
API_KEY = SETTINGS['api_key']
API_URL = SETTINGS['api_url']
SPONSOR_CHANNELS = SETTINGS['sponsors']

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
    """Admin menu tugmalari"""
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("🔑 API Kalitini o'zgartirish"),
        telebot.types.KeyboardButton("➕ Sponsor qo'shish"),
        telebot.types.KeyboardButton("➖ Sponsor o'chirish"),
        telebot.types.KeyboardButton("📋 Sponsor'lar ro'yxati"),
        telebot.types.KeyboardButton("💵 Foydalanuvchi balansini o'zgartirish"),
        telebot.types.KeyboardButton("➕ Kategoriya qo'shish"),
        telebot.types.KeyboardButton("📌 Tur qo'shish"),
        telebot.types.KeyboardButton("➕ Xizmat qo'shish")
    )
    
    # Agar custom xizmatlar bo'lsa o'chirish tugmasini qo'sh
    if get_custom_services():
        markup.add(telebot.types.KeyboardButton("➖ Xizmat o'chirish"))
    
    markup.add(
        telebot.types.KeyboardButton("👥 Foydalanuvchilar soni"),
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
    """Bitta order statusini olish"""
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
    
    for channel in SPONSOR_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

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
            'orders': []
        })
    else:
        user = db.get(User.user_id == user_id)
        if 'balance' not in user:
            db.update({'balance': 0.0}, User.user_id == user_id)

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
            'created_at': datetime.now().isoformat()
        })
        db.update({'orders': orders}, User.user_id == user_id)

def get_user_orders(user_id: int) -> List:
    """Foydalanuvchining barcha order larini olish"""
    user = get_user(user_id)
    return user['orders'] if user else []

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
        sponsor_msg = "❌ Avval quyidagi kanallarga obuna bo'ling:\n\n"
        for idx, channel in enumerate(SPONSOR_CHANNELS, 1):
            sponsor_msg += f"{idx}. {channel}\n"
        sponsor_msg += "\nKo'p vaqt kutmang va qayta /start ni bosing"
        bot.reply_to(message, sponsor_msg)
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
        bot.reply_to(message, "❌ Sponsor kanallarga obuna bo'ling!")
        return
    
    user_balance = get_user_balance(user_id)
    
    balance_msg = f"""
💰 SIZNING BALANSINGIZ

Balans: ${user_balance:.2f}
    """
    bot.send_message(user_id, balance_msg, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📊 Xizmatlar")
def services_handler(message):
    """Services list - kategoriyalarni ko'rsatish"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        bot.reply_to(message, "❌ Sponsor kanallarga obuna bo'ling!")
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

PAGE_SIZE = 1  # Har bir sahifada 10ta xizmat

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
        services_msg += f"{index}. {service['name']}\n"
    
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




@bot.message_handler(func=lambda message: message.text == "➕ Order qo'shish")
def add_order_start(message):
    """Add order - service ID so'rash"""
    user_id = message.from_user.id
    
    if not check_sponsors(user_id):
        bot.reply_to(message, "❌ Sponsor kanallarga obuna bo'ling!")
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
💵 Narxi: ${cost:.2f}

Qolgan balans: ${get_user_balance(user_id):.2f}
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
        bot.reply_to(message, "❌ Sponsor kanallarga obuna bo'ling!")
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
💵 Narxi: ${order['cost']}
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

@bot.message_handler(func=lambda message: message.text == "🔑 API Kalitini o'zgartirish")
def set_api_key_start(message):
    """Set API key"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin emas!")
        return
    
    msg = bot.send_message(user_id, "🔑 Yangi API Kalitini kiriting:", reply_markup=back_menu())
    bot.register_next_step_handler(msg, process_api_key)

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
    channel_id = message.text.strip()
    
    if channel_id not in SPONSOR_CHANNELS:
        SPONSOR_CHANNELS.append(channel_id)
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        
        bot.send_message(message.from_user.id, f"✅ Sponsor kanal qo'shildi: {channel_id}", reply_markup=admin_menu())
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
    channel_id = message.text.strip()
    
    if channel_id in SPONSOR_CHANNELS:
        SPONSOR_CHANNELS.remove(channel_id)
        SETTINGS['sponsors'] = SPONSOR_CHANNELS
        
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(SETTINGS, f, indent=4, ensure_ascii=False)
        
        bot.send_message(message.from_user.id, f"✅ Sponsor kanal o'chirildi: {channel_id}", reply_markup=admin_menu())
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
    for idx, channel in enumerate(SPONSOR_CHANNELS, 1):
        list_msg += f"{idx}. {channel}\n"
    
    bot.send_message(user_id, list_msg, reply_markup=admin_menu())

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
    
    services_list = "🗑️ O'CHIRILISHI KERAK BO'LGAN XIZMATLAR\n\n"
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
{action}: ${abs(amount):.2f}

Eski balans: ${current_balance:.2f}
Yangi balans: ${new_balance:.2f}
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
