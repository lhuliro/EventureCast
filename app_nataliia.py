from flask import Flask, render_template
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
 
load_dotenv()
 
app = Flask(__name__)
 
# بيانات الاعتماد
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
    'locations': '7',  # معرف هامبورغ
    'datum_start': today.strftime('%Y-%m-%d'),
    'datum_ende': next_week.strftime('%Y-%m-%d'),
    'columns': 'bild_s,titel,datum,zeit,location,start_date'
}
 
 
    try:
        response = requests.post(api_url, data=payload)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            print("حدث خطأ:", data['error'])
            return []
        return data.get('data', [])
    except Exception as e:
        print("Error fetching event data", e)
        return []
 
def get_weather_forecast():
    lat = 53.5511  # خط العرض لهامبورغ
    lon = 9.9937   # خط الطول لهامبورغ
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
 
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        daily_forecasts = data.get('daily', [])[:7]
        for day in daily_forecasts:
            day['readable_date'] = datetime.utcfromtimestamp(day['dt']).strftime('%A, %B %d, %Y')
        return daily_forecasts
    except Exception as e:
        print("Error fetching weather data", e)
        return []
 
@app.route('/')
def index():
    start_date = datetime.today().date()
    end_date = start_date + timedelta(days=7)
 
    events = get_events()
    filtered_events = [
        event for event in events
        if event.get('location', '').lower() == 'hamburg'
        and start_date <= datetime.strptime(event.get('start_date', '1900-01-01'), "%Y-%m-%d").date() <= end_date
    ]
 
    weather = get_weather_forecast()
    print(json.dumps(weather,indent=1))
    return render_template('index.html', events=filtered_events, weather=weather)
 
if __name__ == '__main__':
    app.run(debug=True)