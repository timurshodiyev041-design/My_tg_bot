import telebot
import requests
import time
from telebot import types

TOKEN = "8284016146:AAFSXT4zcslPpw5IKpce5Lp8b7pt4hT9CwE"
bot = telebot.TeleBot(TOKEN)

# --- Кэш ---
cache = {"timestamp": 0, "rates": {}, "ok": False}
user_state = {}

# --- Переводы ---
texts = {
    "ru": {
        "greet": "💱 Привет! Я помогу быстро конвертировать валюту.\n\nСначала выбери валюту, **из которой** хочешь перевести:",
        "choose_lang": "🌍 Выбери язык:",
        "from_currency": "✅ Из валюты: {cur}\nТеперь введи сумму:",
        "enter_amount": "Теперь выбери валюту, **в которую** перевести:",
        "invalid_number": "⚠️ Введи число, например 100 или 12.5",
        "invalid_choice": "❗ Выбери валюту из кнопок.",
        "same_currency": "⚠️ Выбери разные валюты.",
        "result": "💹 {amount} {base} = {res:,.2f} {target}\n(1 {base} = {rate:.2f} {target})",
        "again": "Хочешь ещё конвертировать? Выбери первую валюту:",
    },
    "uz": {
        "greet": "💱 Salom! Men sizga valyutani tezda konvertatsiya qilishda yordam beraman.\n\nAvval qaysi valyutadan o'tkazmoqchisiz, tanlang:",
        "choose_lang": "🌍 Tilni tanlang:",
        "from_currency": "✅ Valyutadan: {cur}\nEndi miqdorni kiriting:",
        "enter_amount": "Endi qaysi valyutaga o'tkazmoqchisiz, tanlang:",
        "invalid_number": "⚠️ Iltimos, raqam kiriting, masalan 100 yoki 12.5",
        "invalid_choice": "❗ Tugmalardan birini tanlang.",
        "same_currency": "⚠️ Ikkita bir xil valyutani tanlamang.",
        "result": "💹 {amount} {base} = {res:,.2f} {target}\n(1 {base} = {rate:.2f} {target})",
        "again": "Yana konvertatsiya qilmoqchimisiz? Dastlabki valyutani tanlang:",
    },
    "en": {
        "greet": "💱 Hi! I can help you convert currencies quickly.\n\nFirst, choose the currency **from which** you want to convert:",
        "choose_lang": "🌍 Choose your language:",
        "from_currency": "✅ From currency: {cur}\nNow enter the amount:",
        "enter_amount": "Now choose the currency **to** convert to:",
        "invalid_number": "⚠️ Please enter a number, e.g. 100 or 12.5",
        "invalid_choice": "❗ Please choose from the buttons.",
        "same_currency": "⚠️ Choose different currencies.",
        "result": "💹 {amount} {base} = {res:,.2f} {target}\n(1 {base} = {rate:.2f} {target})",
        "again": "Want to convert again? Choose the first currency:",
    },
    "ua": {
        "greet": "💱 Привіт! Я допоможу швидко конвертувати валюту.\n\nСпочатку вибери валюту, **з якої** хочеш перевести:",
        "choose_lang": "🌍 Вибери мову:",
        "from_currency": "✅ З валюти: {cur}\nТепер введи суму:",
        "enter_amount": "Тепер вибери валюту, **в яку** перевести:",
        "invalid_number": "⚠️ Введи число, наприклад 100 або 12.5",
        "invalid_choice": "❗ Вибери валюту з кнопок.",
        "same_currency": "⚠️ Вибери різні валюти.",
        "result": "💹 {amount} {base} = {res:,.2f} {target}\n(1 {base} = {rate:.2f} {target})",
        "again": "Хочеш ще конвертувати? Вибери першу валюту:",
    },
}

def preload_rates():
    try:
        r = requests.get("https://api.frankfurter.app/latest", timeout=3)
        data = r.json()
        data["rates"]["EUR"] = 1.0
        cache["rates"] = data["rates"]
        cache["timestamp"] = time.time()
        cache["ok"] = True
        print("✅ Курсы валют обновлены")
    except Exception as e:
        print("⚠️ Не удалось обновить курсы:", e)
        cache["ok"] = False

preload_rates()

def update_rates_if_needed():
    if time.time() - cache["timestamp"] > 600:
        preload_rates()

def get_rate(base, target):
    update_rates_if_needed()
    if not cache["ok"]:
        return None

    rates = cache["rates"]
    manual = {"UZS": 12800}

    def to_usd(cur):
        if cur == "USD": return 1
        if cur == "EUR": return 1 / rates["USD"]
        if cur == "RUB": return rates["USD"] / rates.get("RUB", 90)
        if cur == "UZS": return 1 / manual["UZS"]
        return None

    def from_usd(cur):
        if cur == "USD": return 1
        if cur == "EUR": return rates["USD"]
        if cur == "RUB": return rates.get("RUB", 90) / rates["USD"]
        if cur == "UZS": return manual["UZS"]
        return None

    a = to_usd(base)
    b = from_usd(target)
    if a is None or b is None:
        return None
    return a * b

def currency_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for cur in ["USD", "EUR", "RUB", "UZS"]:
        markup.add(types.KeyboardButton(cur))
    return markup

def lang_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Русский 🇷🇺"),
        types.KeyboardButton("Oʻzbek 🇺🇿"),
        types.KeyboardButton("English 🇬🇧"),
        types.KeyboardButton("Українська 🇺🇦"),
    )
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, texts["ru"]["choose_lang"], reply_markup=lang_keyboard())
    user_state[message.chat.id] = {"lang": None, "from": None, "amount": None, "to": None}

@bot.message_handler(content_types=["text"])
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_state:
        user_state[chat_id] = {"lang": None, "from": None, "amount": None, "to": None}

    state = user_state[chat_id]

    # --- Выбор языка ---
    if state["lang"] is None:
        if text.startswith("Рус"):
            state["lang"] = "ru"
        elif text.startswith("Oʻzbek") or text.startswith("Uzbek"):
            state["lang"] = "uz"
        elif text.startswith("Eng"):
            state["lang"] = "en"
        elif text.startswith("Укра"):
            state["lang"] = "ua"
        else:
            bot.send_message(chat_id, "❗ Please choose one of the languages.", reply_markup=lang_keyboard())
            return

        bot.send_message(chat_id, texts[state["lang"]]["greet"], parse_mode="Markdown", reply_markup=currency_keyboard())
        return

    lang = state["lang"]
    text = text.upper()

    if state["from"] is None:
        if text not in ["USD", "EUR", "RUB", "UZS"]:
            bot.send_message(chat_id, texts[lang]["invalid_choice"], reply_markup=currency_keyboard())
            return
        state["from"] = text
        bot.send_message(chat_id, texts[lang]["from_currency"].format(cur=text))
        return

    if state["amount"] is None:
        try:
            state["amount"] = float(text)
        except ValueError:
            bot.send_message(chat_id, texts[lang]["invalid_number"])
            return
        bot.send_message(chat_id, texts[lang]["enter_amount"], parse_mode="Markdown", reply_markup=currency_keyboard())
        return

    if state["to"] is None:
        if text not in ["USD", "EUR", "RUB", "UZS"]:
            bot.send_message(chat_id, texts[lang]["invalid_choice"], reply_markup=currency_keyboard())
            return
        state["to"] = text

        base, target, amount = state["from"], state["to"], state["amount"]
        if base == target:
            bot.send_message(chat_id, texts[lang]["same_currency"])
        else:
            rate = get_rate(base, target)
            if rate:
                result = amount * rate
                bot.send_message(chat_id, texts[lang]["result"].format(amount=amount, base=base, res=result, target=target, rate=rate))
            else:
                bot.send_message(chat_id, "⚠️ Kurslarni olishda xatolik.")

        user_state[chat_id] = {"lang": lang, "from": None, "amount": None, "to": None}
        bot.send_message(chat_id, texts[lang]["again"], reply_markup=currency_keyboard())

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
