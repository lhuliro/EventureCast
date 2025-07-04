from flask import Flask, render_template, request
import requests
import http.client
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import random

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
        forecasts = data.get('daily', [])[:7]
        for day in forecasts:
            day['readable_date'] = datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d')
        return forecasts
    except Exception as e:
        print("❌ Error fetching weather:", e)
        return []

def get_hamburg_coordinates():
    """Return random coordinates within Hamburg"""
    hamburg_bounds = {
        'lat_min': 53.4,
        'lat_max': 53.7,
        'lon_min': 9.7,
        'lon_max': 10.3
    }
    
    lat = round(random.uniform(hamburg_bounds['lat_min'], hamburg_bounds['lat_max']), 6)
    lon = round(random.uniform(hamburg_bounds['lon_min'], hamburg_bounds['lon_max']), 6)
    
    return lat, lon

def fetch_hamburg_events():
    """
    Function to fetch real events from the wasgehtapp.de API
    Sends a POST request with login data to retrieve events.
    """
    try:
        conn = http.client.HTTPSConnection("www.wasgehtapp.de")
        boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

        dataList = []
        def encode(text):
            return text.encode('utf-8')

        # Login data in form data
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
                
                # Add random coordinates for each event (for map display purposes, for example)
                lat, lon = get_hamburg_coordinates()
                
                formatted_events.append({
                    "titel": event.get("titel", ""),
                    "start_date": event.get("datum_iso", ""),
                    "end_date": event.get("datum_iso", ""),
                    "location": "Hamburg",
                    "venue": event.get("location", ""),
                    "zeit": event.get("zeit", ""),
                    "kategorie": event.get("kategorie", ""),
                    "id": event.get("id", ""),
                    "bild": bild_url,
                    "lat": lat,  # Add latitude
                    "lon": lon   # Add longitude
                })
        return formatted_events
    except Exception as e:
        print("❌ Error fetching events:", e)
        return []

def filter_by_time_numeric(event_time, selected_time):
    # Same function as before, for filtering time based on numeric text
    if not selected_time:
        return True
    if not event_time:
        return False
    selected_time = selected_time.strip()
    event_time = event_time.strip()

    if selected_time in event_time:
        return True

    import re
    selected_numbers = re.findall(r'\d+', selected_time)
    event_numbers = re.findall(r'\d+', event_time)

    if selected_numbers:
        for selected_num in selected_numbers:
            if selected_num in event_numbers:
                return True
            if selected_num in event_time:
                return True

    if selected_time.isdigit():
        hour = int(selected_time)
        patterns_24h = [
            f"{hour:02d}:", f"{hour:02d}.", f"{hour:02d} ", f" {hour:02d}", f"{hour} ", f" {hour}",
        ]
        for pattern in patterns_24h:
            if pattern in event_time:
                return True

        if hour > 12:
            hour_12 = hour - 12
            patterns_12h = [
                f"{hour_12}:", f"{hour_12}.", f"{hour_12} ", f" {hour_12}",
            ]
            for pattern in patterns_12h:
                if pattern in event_time:
                    return True

    if ':' in selected_time:
        if selected_time in event_time:
            return True
        try:
            hour_part = selected_time.split(':')[0]
            if hour_part in event_time:
                return True
        except:
            pass

    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = get_weather_forecast()
    events = fetch_hamburg_events()

    query = request.args.get('query', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_date = request.args.get('date', '').strip()
    selected_time = request.args.get('time', '').strip()
    selected_location = request.args.get('location', '').strip()

    weather_map = {w['readable_date']: w for w in weather}

    for event in events:
        date_str = event['start_date'][:10] if event['start_date'] else None
        event['weather'] = weather_map.get(date_str)

    filtered_events = []
    for event in events:
        try:
            if query and query.lower() not in event.get('titel', '').lower():
                continue
            if selected_category and selected_category.lower() not in event.get('kategorie', '').lower():
                continue
            if selected_date and selected_date not in event.get('start_date', ''):
                continue
            if selected_time and not filter_by_time_numeric(event.get('zeit', ''), selected_time):
                continue
            if selected_location and selected_location.lower() not in event.get('venue', '').lower():
                continue
            filtered_events.append(event)
        except Exception as e:
            print(f"❌ Error filtering event {event.get('id', 'unknown')}: {e}")
            continue

    return render_template(
        'index.html',
        weather=weather,
        events=filtered_events,
        query=query,
        category=selected_category,
        date=selected_date,
        time=selected_time,
        location=selected_location,
        total_events=len(events),
        filtered_count=len(filtered_events)
    )

@app.route('/debug')
def debug():
    events = fetch_hamburg_events()
    unique_times = set(event.get('zeit', '') for event in events if event.get('zeit', ''))
    unique_categories = set(event.get('kategorie', '') for event in events if event.get('kategorie', ''))

    debug_info = {
        'total_events': len(events),
        'unique_times': sorted(list(unique_times)),
        'unique_categories': sorted(list(unique_categories)),
        'sample_events': events[:5]
    }

    return f"""
    <h1>Debug Information</h1>
    <h2>Total Events: {debug_info['total_events']}</h2>
    
    <h3>Unique Time Values:</h3>
    <ul>
        {''.join([f'<li><strong>{time}</strong></li>' for time in debug_info['unique_times']])}
    </ul>
    
    <h3>Unique Categories:</h3>
    <ul>
        {''.join([f'<li>{cat}</li>' for cat in debug_info['unique_categories']])}
    </ul>
    
    <h3>Sample Events with Time Info:</h3>
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <thead>
            <tr>
                <th>Title</th>
                <th>Time (zeit)</th>
                <th>Category</th>
            </tr>
        </thead>
        <tbody>
            {''.join([f'<tr><td>{event.get("titel", "N/A")}</td><td><strong>{event.get("zeit", "N/A")}</strong></td><td>{event.get("kategorie", "N/A")}</td></tr>' for event in debug_info['sample_events']])}
        </tbody>
    </table>
    """

if __name__ == '__main__':
    app.run(debug=True)
