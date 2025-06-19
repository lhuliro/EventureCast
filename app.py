from flask import Flask, render_template, request
import requests
import http.client
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def get_weather_forecast():
    lat = 53.5511   # Hamburg latitude
    lon = 9.9937    # Hamburg longitude
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts"
        f"&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
    )
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        forecasts = data.get('daily', [])[:7]  # فقط 7 أيام قادمة
        for day in forecasts:
            day['readable_date'] = datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d')
        return forecasts
    except Exception as e:
        print("❌ Error fetching weather:", e)
        return []

def fetch_hamburg_events():
    try:
        conn = http.client.HTTPSConnection("www.wasgehtapp.de")
        boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

        dataList = []
        def encode(text):
            return text.encode('utf-8')

        dataList.append(encode('--' + boundary))
        dataList.append(encode('Content-Disposition: form-data; name=mail;'))
        dataList.append(encode('Content-Type: text/plain'))
        dataList.append(encode(''))
        dataList.append(encode("ghaith.alshathi.24@nithh.onmicrosoft.com"))

        dataList.append(encode('--' + boundary))
        dataList.append(encode('Content-Disposition: form-data; name=passwort;'))
        dataList.append(encode('Content-Type: text/plain'))
        dataList.append(encode(''))
        dataList.append(encode("Gatetomba90"))

        dataList.append(encode('--' + boundary + '--'))
        dataList.append(encode(''))

        body = b'\r\n'.join(dataList)
        headers = {'Content-type': f'multipart/form-data; boundary={boundary}'}

        conn.request("POST", "/export.php", body, headers)
        res = conn.getresponse()
        data = res.read()
        response_text = data.decode("utf-8")
        events_data = json.loads(response_text)

        formatted_events = []
        if 'data' in events_data and isinstance(events_data['data'], list):
            for event in events_data['data']:
                bild_url = event.get("bild")
                if not bild_url or bild_url.strip() == "":
                    bild_url = "/static/placeholder.png"
                formatted_events.append({
                    "titel": event.get("titel", ""),
                    "start_date": event.get("datum_iso", ""),
                    "end_date": event.get("datum_iso", ""),
                    "location": "Hamburg",
                    "venue": event.get("location", ""),
                    "zeit": event.get("zeit", ""),
                    "kategorie": event.get("kategorie", ""),
                    "id": event.get("id", ""),
                    "bild": bild_url
                })
        return formatted_events
    except Exception as e:
        print("❌ Error fetching events:", e)
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = get_weather_forecast()
    events = fetch_hamburg_events()

    # قراءة مدخلات الفلترة من المستخدم
    query = request.args.get('query', '').lower()
    selected_category = request.args.get('category', '').lower()
    selected_date = request.args.get('date', '')
    selected_time = request.args.get('time', '').lower()
    selected_location = request.args.get('location', '').lower()

    # خريطة ربط الطقس حسب التاريخ
    weather_map = {w['readable_date']: w for w in weather}

    # ربط الطقس بكل حدث حسب التاريخ
    for event in events:
        date_str = event['start_date'][:10] if event['start_date'] else None
        event['weather'] = weather_map.get(date_str)

    # تطبيق الفلاتر
    filtered_events = []
    for event in events:
        if query and query not in event['titel'].lower():
            continue
        if selected_category and selected_category not in event['kategorie'].lower():
            continue
        if selected_date and selected_date not in event['start_date']:
            continue
        if selected_time and selected_time not in event['zeit'].lower():
            continue
        if selected_location and selected_location not in event['venue'].lower():
            continue
        filtered_events.append(event)

    return render_template(
        'index.html',
        weather=weather,
        events=filtered_events,
        query=query,
        category=selected_category,
        date=selected_date,
        time=selected_time,
        location=selected_location
    )

if __name__ == '__main__':
    app.run(debug=True)