from flask import Flask, render_template, request
import http.client
import json
import requests
import os
import random
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

@lru_cache(maxsize=1)
def get_weather_forecast():
    lat = 53.5511
    lon = 9.9937
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        daily_forecasts = data.get('daily', [])[:7]

        result = []
        for day in daily_forecasts:
            readable_date = datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d')
            result.append({
                'date': readable_date,
                'temp': round(day['temp']['day']),
                'condition': day['weather'][0]['main']
            })
        return result
    except Exception as e:
        print("Error fetching weather data:", e)
        return []

def condition_to_emoji(condition):
    emoji_map = {
        "Rain": "🌧️", "Snow": "❄️", "Clear": "☀️", "Clouds": "☁️",
        "Thunderstorm": "⛈️", "Drizzle": "🌦️", "Mist": "🌫️", "Fog": "🌁",
        "Wind": "💨"
    }
    return emoji_map.get(condition, "🌈")


# Geocode address using OpenStreetMap Nominatim
def geocode_address(address):
    """
    Geocode an address to (lat, lon) using OSM Nominatim
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "EventureCast/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.ok and resp.json():
            data = resp.json()[0]
            return float(data["lat"]), float(data["lon"])
    except Exception as e:
        print(f"Geocoding failed for '{address}':", e)
    # fallback: return None
    return None, None

def fetch_hamburg_events():
    try:
        conn = http.client.HTTPSConnection("www.wasgehtapp.de")
        conn.request("GET", "/export.php?mail=ghaith.alshathi.24@nithh.onmicrosoft.com&passwort=Gatetomba90&columns=null", "", {
            'Cookie': 'lv=1747851903; v=1; vc=2'
        })
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        events_data = json.loads(data)

        weather_list = get_weather_forecast()

        formatted_events = []

        for idx, event in enumerate(events_data.get("data", [])):
            venue = event.get("location", "")
            address = f"{venue}, Hamburg, Germany" if venue else "Hamburg, Germany"
            # Only geocode the first 5 events to avoid slowdowns/rate limits
            if idx < 5:
                lat, lon = geocode_address(address)
            else:
                lat, lon = None, None
            if lat is None or lon is None:
                # fallback to dummy coordinates if geocoding fails or skipped
                lat = round(random.uniform(53.45, 53.65), 6)
                lon = round(random.uniform(9.8, 10.2), 6)

            formatted_event = {
                "title": event.get("titel", ""),
                "start_date": event.get("datum_iso", ""),
                "end_date": event.get("datum_iso", ""),
                "location": "Hamburg",
                "venue": venue,
                "time": event.get("zeit", ""),
                "category": event.get("kategorie", ""),
                "id": event.get("id", ""),
                "image": event.get("bild_url", "https://example.com/default.jpg"),
                "lat": lat,
                "lon": lon
            }

            event_date = formatted_event["start_date"][:10]
            match = next((w for w in weather_list if w['date'] == event_date), None)
            if match:
                formatted_event["weather_temp"] = match['temp']
                formatted_event["weather_icon"] = condition_to_emoji(match['condition'])
            else:
                formatted_event["weather_temp"] = "N/A"
                formatted_event["weather_icon"] = "🚫"

            formatted_events.append(formatted_event)

        if formatted_events:
            print("🔍 Sample weather info:", formatted_events[0].get("weather_temp"), formatted_events[0].get("weather_icon"))

        return formatted_events
    except Exception as e:
        print("❌ Error fetching events:", e)
        return []

@app.route("/", methods=["GET"])
def index():
    events = fetch_hamburg_events()

    date_filter = request.args.get("date", "").strip()
    time_filter = request.args.get("time_of_day", "").strip()
    category_filter = request.args.get("category", "").strip()
    venue_filter = request.args.get("venue", "").strip()
    lang = request.args.get("lang", "de")

    translations = {
        'de': {
            'date': 'Datum',
            'time_of_day': 'Tageszeit',
            'category': 'Kategorie',
            'venue': 'Ort/Straße',
            'filter': 'Filtern',
            'clear_filters': 'Alle Filter löschen',
            'events_found': 'Veranstaltung(en) gefunden',
            'upcoming_events': 'Kommende Veranstaltungen in Hamburg',
            'no_events': 'Keine Veranstaltungen für die gewählten Kriterien.',
            'time_morning': 'Morgen (6-12)',
            'time_afternoon': 'Nachmittag (12-17)',
            'time_evening': 'Abend (17-23)',
            'category_select': '-- Kategorie wählen --',
            'location_select': '-- Ort wählen --',
            'open_gmaps': 'In Google Maps öffnen',
            'weather': 'Wetter',
            'support_us': '💖 Unterstützen',
            'time_not_specified': 'Zeit nicht angegeben'
        },
        'en': {
            'date': 'Date',
            'time_of_day': 'Time of Day',
            'category': 'Category',
            'venue': 'Location/Street',
            'filter': 'Filter',
            'clear_filters': 'Clear All Filters',
            'events_found': 'event(s) found',
            'upcoming_events': 'Upcoming Events in Hamburg',
            'no_events': 'No events available for the selected criteria.',
            'time_morning': 'Morning (6-12)',
            'time_afternoon': 'Afternoon (12-17)',
            'time_evening': 'Evening (17-23)',
            'category_select': '-- Select Category --',
            'location_select': '-- Select Location --',
            'open_gmaps': 'Open in Google Maps',
            'weather': 'Weather',
            'support_us': '💖 Support Us',
            'time_not_specified': 'Time not specified'
        }
    }
    t = translations.get(lang, translations['de'])

    def filter_event(event):
        if date_filter and event["start_date"][:10] != date_filter:
            return False
        if time_filter:
            try:
                event_hour = int(event.get("time", "").split(":")[0])
                if time_filter == "morning" and not (6 <= event_hour < 12):
                    return False
                elif time_filter == "afternoon" and not (12 <= event_hour < 17):
                    return False
                elif time_filter == "evening" and not (17 <= event_hour <= 23):
                    return False
            except:
                return False
        if category_filter and category_filter.lower() not in event.get("category", "").lower():
            return False
        if venue_filter and venue_filter.lower() not in event.get("venue", "").lower():
            return False
        return True

    filtered_events = [e for e in events if filter_event(e)]
    categories = sorted(set(e['category'] for e in events if e['category']))

    # Debug: Print first few events to console
    print(f"📊 Total events: {len(events)}, Filtered: {len(filtered_events)}")
    if filtered_events:
        print(f"🔍 First event coordinates: lat={filtered_events[0].get('lat')}, lon={filtered_events[0].get('lon')}")

    # Build language switcher URLs preserving all filters
    from urllib.parse import urlencode
    args = request.args.to_dict()
    args_de = args.copy()
    args_en = args.copy()
    args_de['lang'] = 'de'
    args_en['lang'] = 'en'
    lang_switcher_de_url = '?' + urlencode(args_de)
    lang_switcher_en_url = '?' + urlencode(args_en)

    return render_template("index.html", events=filtered_events, date_filter=date_filter,
                           time_filter=time_filter, category_filter=category_filter,
                           venue_filter=venue_filter, categories=categories, lang=lang, t=t,
                           lang_switcher_de_url=lang_switcher_de_url, lang_switcher_en_url=lang_switcher_en_url)

@app.route("/test-map")
def test_map():
    """Test route to check if Leaflet works at all"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            #test-map {
                height: 400px;
                width: 100%;
                border: 2px solid red;
            }
        </style>
    </head>
    <body>
        <h1>Test Map - If this works, Leaflet is fine</h1>
        <div id="test-map"></div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            console.log('Starting test map...');
            setTimeout(() => {
                try {
                    const map = L.map('test-map').setView([53.5511, 9.9937], 12);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; OpenStreetMap contributors'
                    }).addTo(map);
                    
                    // Add a test marker
                    L.marker([53.5511, 9.9937]).addTo(map)
                        .bindPopup('Hamburg Test Marker');
                        
                    console.log('Test map created successfully!');
                } catch (error) {
                    console.error('Test map error:', error);
                    document.getElementById('test-map').innerHTML = '<div style="padding:20px;color:red;">Error: ' + error.message + '</div>';
                }
            }, 1000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
