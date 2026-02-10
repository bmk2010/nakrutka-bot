# Xizmatlar Buyurtmash Tizimi - Dokumentatsiya

## Qo'shilgan Xususiyatlar

Yangi buyurtma sistema ko'vetiga o'tkazildi. Foydalanuvchilar endi quyidagi yo'lda buyurtma berishlari mumkin:

### 1. Xizmatlar Ko'rishatishs
- **Yo'l:** `💰 Balans` → `📊 Xizmatlar` → `📁 Kategoriya` → `🔹 Tur`
- Tanlangan turning barcha xizmatlar inline tugmalar bilan ko'rsatiladi
- Har bir xizmat uchun emoji raqamli tugma (1️⃣2️⃣3️⃣ va h.k.)
- Pagination: Ortiqcha xizmatlar uchun "Oldingi/Keyingi" tugmalari

### 2. Xizmat Haqida To'liq Ma'lumot
Xizmatni bosish orqali quyidagi ma'lumotlar ko'rsatiladi:

```
🛍 {Xizmat to'liq nomi}

💰 Narxi (1000x): {Narxi}{CURRENCY}

⏬ Minimal: {APIdan olingan minimal miqdor} ta
⏫ Maksimal: {APIdan olingan maksimal miqdor} ta
```

- ✅ Buyurtma berish - buyurtmani boshlash
- ❌ Bekor qilish - xizmatlar ro'yxatiga qaytish (message o'chiriladi)

### 3. Buyurtma Qilish Jarayoni

#### 3.1 Balans Tekshirish
- Agar foydalanuvchi balans 0 yoki manfi bo'lsa:
  ```
  ❌ Yetarli balans yo'q!
  💰 Kerakli: {narx}
  💰 Sizning balans: {balans}
  ```

#### 3.2 Miqdor So'rash
```
🔢 Buyurtma miqdorini kiriting...

⏬ Minimal: {min} ta
⏫ Maksimal: {max} ta
💰 Narxi (1000x): {price}
```

- Foydalanuvchi raqam kiritadi
- Raqam min va max orasida tekshiriladi
- Agar noto'g'ri bo'lsa, qayta kiritishni so'rash

#### 3.3 Havola So'rash
```
🔗 Buyurtma uchun havolani yuboring...

(Instagram, TikTok, Telegram, YouTube va h.k.)
```

- Foydalanuvchi havola kiritadi
- Havola uzunligi tekshiriladi (minimal 5 ta belgi)

#### 3.4 Buyurtma Yaratish va Balans Kamaytirishni
- API'ga order qilish: `add_order(service_id, link, quantity)`
- Balans kamaytirishni: `subtract_balance(user_id, total_cost)`
- Ma'lumotlarni saqlash: `save_order(...)`

#### 3.5 Muvaffaqiyat Xabari
```
✅ Buyurtma qabul qilindi!

🆔 Buyurtma ID si: {order_id}
🛍 Xizmat: {service_name}
🔗 Havola: {link}
📊 Miqdor: {quantity}
💵 To'lov: {total_cost:2f}

💰 Qolgan balans: {new_balance:2f}
```

### 4. Narxlash
- **Narx Hisoblash:** `(quantity / 1000.0) * service_price`
  - M: 500 miqdor, 2$ narxi = (500 / 1000) * 2 = 1$

- **Narx Manbai:** `custom_services`dagi narx (APIdan emas)

### 5. Xodisa Kodlari (Callback Data)

| Kodlash | Tavsif |
|---------|---------|
| `service_<service_id>_<type_name>` | Xizmat tanlandi |
| `order_confirm_<service_id>_<type_name>` | Buyurtma tasdiqlandi |
| `order_cancel_<service_id>` | Buyurtma bekor qilindi |
| `page_<page>_<type_name>` | Sahifa o'zgartirildi |

### 6. Qo'shilgan Funktsiyalar

#### `get_service_details(service_id: int) -> Dict`
- API'dan xizmatning min/max ma'lumotlarini olish
- Agar API javabot bersa, fallback qiymatlar qo'llaniladi

#### `show_service_details(call)`
- Xizmat haqida to'liq ma'lumot ko'rsatish
- API'dan min/max olish

#### `cancel_service_view(call)`
- Xizmat ko'rinishini bekor qilish

#### `start_ordering(call)`
- Buyurtma jarayonini boshlash
- Balans tekshirish

#### `process_order_quantity(message, service_id, type_name, min_qty, max_qty)`
- Miqdor qabul qilish va tekshirish

#### `process_order_link(message, service_id, type_name, quantity)`
- Havola qabul qilish
- Balans tekshirish va order yaratish
- Balans kamaytirishni

### 7. Xato Xondlash

- ❌ Xizmat topilmadi - buyurtma bekor qilindi
- ❌ Yetarli balans yo'q - buyurtmadan bosh tortildi
- ❌ Noto'g'ri miqdor - qayta kiritish so'raldi
- ❌ Noto'g'ri havola - qayta kiritish so'raldi
- ❌ API xatolig'i - xato xabari ko'rsatildi

## Ishlash Rasm

```
Xizmatlar → Kategoriya → Tur → Xizmatlar Ro'yxati
                                      ↓
                              Inline Tugmalar (1️⃣ 2️⃣ 3️⃣...)
                                      ↓
                              Xizmat Tafsiloti
                                      ↓
                         ✅ Buyurtma / ❌ Bekor
                                      ↓ (✅ Bosish)
                              Balans Tekshirish
                                      ↓
                         Miqdor So'rash (Min-Max)
                                      ↓
                          Havola So'rash & Tekshirish
                                      ↓
                         API'ga Order Qo'shish
                                      ↓
                         Balans Kamaytirishni
                                      ↓
                     ✅ Buyurtma Qabul Qilindi
```

## Adabiyotlar

- Eski "➕ Order qo'shish" handler hali ham mavjud va ishlaydi
- Yangi system xizmatlar katalogidan bevosita buyurtma qilish imkoniyatini beradi
- Barcha ma'lumotlar TinyDB da saqlanadi
- API bilan integratsiya: `smmupper.com/api/v2`
