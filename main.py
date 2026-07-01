import time
import telebot
import os
from dotenv import load_dotenv
import asyncio
import aiohttp


load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Переменная BOT_TOKEN не найдена в окружении!")

weather_api_url = os.environ.get("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения выбранных городов пользователей
user_keywords_cities = {}


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


async def fetch_weather_for_city(session, city, lat, lon):
    """Получает погоду для ОДНОГО города."""
    # 1. Формируем URL
    full_url = f"{weather_api_url}?latitude={lat}&longitude={lon}&current_weather=true"
    # 2. Делаем запрос через session.get()
    try:
        async with session.get(full_url) as response:
            # 3. Проверяем статус (в aiohttp это status, не status_code!)
            if response.status != 200:
                print(f"❌ Ошибка для {city}: статус {response.status}")
                return None
            # 4. Парсим JSON (обязательно с await!)
            data = await response.json()
            # 5. Извлекаем нужные данные
            current_weather = data["current_weather"]
            # 6. Возвращаем структурированный результат
            return {
                "city": city,
                "temp": current_weather["temperature"],
                "wind": current_weather["windspeed"],
                "code": current_weather["weathercode"]
            }
    except Exception as e:
        # 7. Если что-то пошло не так — возвращаем None (не падаем!)
        print(f"❌ Исключение для {city}: {e}")
        return None

async def fetch_all_weathers(cities_list):
    """Получает погоду для ВСЕХ городов ПАРАЛЛЕЛЬНО."""
    # 1. Создаём ОДНУ aiohttp.ClientSession()
    async with aiohttp.ClientSession() as session:
        # 2. Создаём список задач: [fetch_weather_for_city(...) для каждого города]
        tasks = []
        for city in cities_list:
            lat, lon = CITIES[city]
            task = fetch_weather_for_city(session, city, lat, lon)
            tasks.append(task)
        # 3. Запускаем все через asyncio.gather(*tasks)
        # 4. Возвращаем список результатов
        results = await asyncio.gather(*tasks)
        return results
    

@bot.message_handler(commands=['weather'])
def send_weather(message):
    start_time = time.time()  # ← замер времени
    
    user_cities = user_keywords_cities.get(message.chat.id, [])
    
    if not user_cities:
        bot.send_message(
            message.chat.id,
            "❌ Сначала выберите город через /cities Москва Сочи"
        )
        return
    
    # Запускаем асинхронную функцию
    results = asyncio.run(fetch_all_weathers(user_cities))
    
    # Обрабатываем результаты
    for i, result in enumerate(results):
        if result:
            # Успех — формируем красивое сообщение
            weather_text = (
                f"🌍 Погода в {result['city'].title()}:\n"
                f"🌡️ Температура: {result['temp']}°C\n"
                f"💨 Ветер: {result['wind']} м/с\n"
                f"☁️ Код погоды: {result['code']}"
            )
            bot.send_message(message.chat.id, weather_text)
        else:
            # Ошибка — берём город по индексу
            city_name = user_cities[i].title()
            bot.send_message(
                message.chat.id,
                f"❌ Не удалось получить погоду для {city_name}"
            )
    
    # Показываем общее время
    total_time = time.time() - start_time
    bot.send_message(
        message.chat.id,
        f"⏱️ Время выполнения: {round(total_time, 2)}с"
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