from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Credentials
WASGEHTAPP_USER = os.getenv('WASGEHTAPP_USER')
WASGEHTAPP_PASS = os.getenv('WASGEHTAPP_PASS')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def get_events():
    api_url = 'https://www.wasgehtapp.de/export.php'
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    payload = {
        'mail': WASGEHTAPP_USER,
        'passwort': WASGEHTAPP_PASS,
        'locations': '7',  # Hamburg ID
        'datum_start': today.strftime('%Y-%m-%d'),
        'datum_ende': next_week.strftime('%Y-%m-%d'),
        'columns': 'bild_s,titel,datum_iso,zeit,location,id,kategorie'
    }

    try:
        response = requests.post(api_url, data=payload)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            print("API Error:", data['error'])
            return []

        formatted_events = []
        for event in data.get("data", []):
            formatted_events.append({
                "title": event.get("titel", ""),
                "start_date": event.get("datum_iso", ""),
                "end_date": event.get("datum_iso", ""),
                "location": "Hamburg",
                "venue": event.get("location", ""),
                "time": event.get("zeit", ""),
                "category": event.get("kategorie", ""),
                "id": event.get("id", ""),
                "image": event.get("bild_s") or "https://example.com/default.jpg"
            })

        return formatted_events

    except Exception as e:
        print("Error fetching event data:", e)
        return []

def get_weather_forecast():
    lat = 53.5511
    lon = 9.9937
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        daily_forecasts = data.get('daily', [])[:7]

        for day in daily_forecasts:
            day['readable_date'] = datetime.utcfromtimestamp(day['dt']).strftime('%A, %B %d, %Y')
            day['icon_url'] = f"http://openweathermap.org/img/wn/{day['weather'][0]['icon']}@2x.png"
            day['description'] = day['weather'][0]['description'].capitalize()
            day['wind'] = f"{day['wind_speed']} m/s"
        return daily_forecasts

    except Exception as e:
        print("Error fetching weather data:", e)
        return []

@app.route('/')
def index():
    events = get_events()
    weather = get_weather_forecast()
    return render_template('index.html', events=events, weather=weather)

if __name__ == '__main__':
    app.run(debug=True)
