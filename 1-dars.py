# def yosh_tekshir(yosh):
#     if yosh < 18:
#         print("voyaga yetmagan")
#     elif yosh > 150:
#         print("yo'g'eee 😂")
#     else:
#         print("voyaga yetgan")

# def eng_katta(a, b, c):
#     # buni qilishda qiynaldim
#     return

# def bahola(ball):
#     if ball >= 90:
#         return "A"
#     elif ball >= 80:
#         return "B"
#     elif ball >= 70:
#         return "C"
#     # ...

# sonlar = [1, 4, 7, 10, 13, 16]

# def find_even(numbers):
#     for number in numbers:
#         if number % 2 == 0:
#             print(number)

# ballar = [80, 90, 75, 60, 100]

# def calculate_sum(numbers):
#     result = 0
#     for ball in numbers:
#         result = result + ball
#     return result

# ismlar = ["Ali", "Vali", "Zayniddin"]

# def find_length_of_names(names):
#     for name in names:
#         lengthofname = name.length
#         print(name + " - " + lengthofname)


# Bank tizimi api simulate

import json

users_db = "users.json"

def load():
    try:
       with open(users_db, "r") as file:
         data = json.load(file)

         return data
    except FileNotFoundError:
        print(f"Error: The file '{users_db}' was not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return []
    
def write(write_data):
    try:
        with open(users_db, "w", encoding="utf-8") as file:
            json.dump(write_data, file, indent=2, ensure_ascii=False)
        return True
    except FileNotFoundError:
        print(f"Error: The file '{users_db}' was not found.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def get_users():
   users = load()
   return users

def get_user(id):
    users = load()
    for usr in users:
        if usr["id"] == id:
            return usr
    raise ValueError(f"User with id {id} not found")

def add_user(name, phone, password):
    users = load()

    if users:
        latest_user_id = users[-1]["user_id"]
    else:
        latest_user_id = 0

    new_user_data = {
        "user_id": latest_user_id + 1,
        "name": name,
        "phone": phone,
        "password": password
    }

    users.append(new_user_data)

    if write(users):
        return f"User muvaffaqiyatli qo‘shildi. id: {new_user_data['user_id']}"
    else:
        return "User qo‘shishda xatolik yuz berdi"


print(add_user("d", 11, 11))