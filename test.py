import os
import aiohttp

CITIES = {
    "москва": (55.75, 37.62),
    "санкт-петербург": (59.93, 30.32),
    "новосибирск": (55.03, 82.92),
    "екатеринбург": (56.84, 60.60),
    "казань": (55.79, 49.12),
    "сочи": (43.60, 39.73),
    "владивосток": (43.12, 131.87),
}



weather_api_url = os.environ.get("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")


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
        for city in user_cities:
            lat, lon = CITIES[city]
            task = fetch_weather_for_city(session, city, lat, lon)
            tasks.append(task)
        # 3. Запускаем все через asyncio.gather(*tasks)
        # 4. Возвращаем список результатов
        return results = await asyncio.gather(*tasks)
    

@bot.message_handler(commands=['weather'])
async def send_weather(message):
    # ... проверка городов ...
    
    # Запускаем асинхронную функцию
    results = await fetch_all_weathers(user_cities)
    
    # Обрабатываем результаты и отправляем сообщения
    for result in results:
        if result:
            # отправляем сообщение с погодой
        else:
            # отправляем сообщение об ошибке