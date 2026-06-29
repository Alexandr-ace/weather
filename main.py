import requests
import telebot
import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Переменная BOT_TOKEN не найдена в окружении!")

weather_api_url = os.environ.get("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения выбранных городов пользователей
user_keywords_cities = {}
router = Router()

# Ключи в нижнем регистре!
CITIES = {
    "москва": (55.75, 37.62),
    "санкт-петербург": (59.93, 30.32),
    "новосибирск": (55.03, 82.92),
    "екатеринбург": (56.84, 60.60),
    "казань": (55.79, 49.12),
    "сочи": (43.60, 39.73),
    "владивосток": (43.12, 131.87),
}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для мониторинга погоды.\n\n"
        "Доступные команды:\n"
        "/weather — показать погоду по выбранным городам\n"
        "/cities Москва Сочи — выбрать города\n"
        "/list — список ваших городов"
    )
    bot.send_message(message.chat.id, welcome_text)


@bot.message_handler(commands=['weather'])
def send_weather(message):
    # 1. Получаем города пользователя (с защитой от KeyError)
    user_cities = user_keywords_cities.get(message.chat.id, [])
    
    # 2. Проверяем, что есть выбранные города
    if not user_cities:
        bot.send_message(
            message.chat.id,
            "❌ Сначала выберите город через /cities Москва Сочи"
        )
        return
    
    # 3. Проходим по всем выбранным городам
    for city in user_cities:
        lat, lon = CITIES[city]
        
        # 4. Формируем URL
        full_url = f"{weather_api_url}?latitude={lat}&longitude={lon}&current_weather=true"
        
        # 5. Делаем запрос
        response = requests.get(full_url)
        
        # 6. Проверяем статус
        if response.status_code != 200:
            bot.send_message(
                message.chat.id,
                f"❌ Не удалось получить погоду для {city.title()}"
            )
            continue  # переходим к следующему городу
        
        # 7. Парсим JSON
        try:
            data = response.json()
            current_weather = data["current_weather"]
            temp = current_weather["temperature"]
            wind = current_weather["windspeed"]
            code = current_weather["weathercode"]
            
            # 8. Формируем сообщение (с правильным названием города!)
            weather_text = (
                f"🌍 Погода в {city.title()}:\n"
                f"🌡️ Температура: {temp}°C\n"
                f"💨 Ветер: {wind} м/с\n"
                f"☁️ Код погоды: {code}"
            )
            bot.send_message(message.chat.id, weather_text)
        
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка обработки данных для {city.title()}"
            )


@bot.message_handler(commands=['cities'])
def choose_weather(message):
    # 1. Получаем список доступных городов (уже в нижнем регистре)
    available_cities = list(CITIES.keys())
    
    # 2. Разбираем команду
    cities = [word.lower() for word in message.text.split()[1:]]
    
    # 3. Проверяем, что пользователь что-то ввёл
    if not cities:
        bot.send_message(
            message.chat.id,
            "❌ Укажите города. Пример: /cities Москва Сочи"
        )
        return
    
    # 4. Находим совпадения и несовпадения
    found = [c for c in cities if c in available_cities]
    not_found = [c for c in cities if c not in available_cities]
    
    # 5. Если ничего не найдено
    if not found:
        bot.send_message(
            message.chat.id,
            "❌ Ни одного указанного города нет в списке.\n"
            f"Доступные: {', '.join([c.title() for c in available_cities])}"
        )
        return
    
    # 6. Сохраняем найденные города
    user_keywords_cities[message.chat.id] = found
    
    # 7. Отправляем результат
    if not_found:
        bot.send_message(
            message.chat.id,
            f"✅ Добавлены: {', '.join([c.title() for c in found])}\n"
            f"⚠️ Не найдены: {', '.join(not_found)}"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"✅ Добавлены: {', '.join([c.title() for c in found])}"
        )


@bot.message_handler(commands=['list'])
def list_cities(message):
    user_cities = user_keywords_cities.get(message.chat.id, [])
    if not user_cities:
        bot.send_message(message.chat.id, "❌ У вас нет выбранных городов")
        return
    text = ", ".join([c.title() for c in user_cities])
    bot.send_message(message.chat.id, f"📋 Ваши города:\n{text}")


print("🤖 Бот запущен и ожидает сообщений...")
bot.polling(none_stop=True)