from flask import Flask, render_template
import requests
import http.client
import json
from codecs import encode
from datetime import datetime, timedelta
 
app = Flask(__name__)

def fetch_hamburg_events():
    """Fetch real events from wasgehtapp.de API"""
    try:
        conn = http.client.HTTPSConnection("www.wasgehtapp.de")
        dataList = []
        boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
        
        # Build the multipart form data
        dataList.append(encode('--' + boundary))
        dataList.append(encode('Content-Disposition: form-data; name=mail;'))
        dataList.append(encode('Content-Type: {}'.format('text/plain')))
        dataList.append(encode(''))
        dataList.append(encode("ghaith.alshathi.24@nithh.onmicrosoft.com"))
        dataList.append(encode('--' + boundary))
        dataList.append(encode('Content-Disposition: form-data; name=passwort;'))
        dataList.append(encode('Content-Type: {}'.format('text/plain')))
        dataList.append(encode(''))
        dataList.append(encode("Gatetomba90"))
        dataList.append(encode('--'+boundary+'--'))
        dataList.append(encode(''))
        
        body = b'\r\n'.join(dataList)
        headers = {
            'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
        }
        
        # Make the request
        conn.request("POST", "/export.php", body, headers)
        res = conn.getresponse()
        data = res.read()
        response_text = data.decode("utf-8")
        
        # Parse the JSON response
        events_data = json.loads(response_text)
        
        if 'data' in events_data and isinstance(events_data['data'], list):
            raw_events = events_data['data']
            
            # Convert to the format expected by your Flask app
            formatted_events = []
            for event in raw_events:
                formatted_event = {
                    "title": event.get("titel", ""),
                    "start_date": event.get("datum_iso", ""),
                    "end_date": event.get("datum_iso", ""),  # Same as start for single-day events
                    "location": "Hamburg",  # All events are in Hamburg
                    "venue": event.get("location", ""),  # Specific venue
                    "time": event.get("zeit", ""),
                    "category": event.get("kategorie", ""),
                    "id": event.get("id", ""),
                    "image": "https://example.com/default.jpg"  # Default image
                }
                formatted_events.append(formatted_event)
            
            print(f"✅ Successfully fetched {len(formatted_events)} events from API")
            return formatted_events
            
        else:
            print("❌ Unexpected API response format")
            return get_fallback_events()
            
    except Exception as e:
        print(f"❌ Error fetching events from API: {e}")
        return get_fallback_events()

def get_fallback_events():
    """Fallback events in case API fails"""
    return [
        {
            "title": "Eagles Of Death Metal",
            "start_date": "2025-06-08",
            "end_date": "2025-06-08",
            "location": "Hamburg",
            "venue": "Venue TBA",
            "time": "20:00",
            "category": "musik",
            "image": "https://example.com/eagles.jpg"
        },
        {
            "title": "Chris Brown - Breezy Bowl XX",
            "start_date": "2025-06-11",
            "end_date": "2025-06-11",
            "location": "Hamburg",
            "venue": "Venue TBA",
            "time": "19:00",
            "category": "musik",
            "image": "https://example.com/chrisbrown.jpg"
        }
    ]

def get_weather_forecast():
    api_key = 'f82e99474e42cf049967aa24ccd739fa'
    city = 'Hamburg'
    url = f'http://api.openweathermap.org/data/2.5/forecast/daily?q={city}&cnt=10&appid={api_key}&units=metric&lang=ar'
 
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['list']
    except Exception as e:
        print("Error fetching weather data:", e)
        return []
 
@app.route('/')
def index():
    # Fetch real events from the API
    events = fetch_hamburg_events()
    
    # Filter events by date range (you can adjust this as needed)
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=30)  # Show events for the next 30 days
 
    filtered_events = []
    for event in events:
        try:
            event_date = datetime.strptime(event['start_date'], "%Y-%m-%d").date()
            if start_date <= event_date <= end_date:
                filtered_events.append(event)
        except (ValueError, KeyError):
            # Skip events with invalid dates
            continue
    
    # Sort events by date
    filtered_events.sort(key=lambda x: x['start_date'])
 
    weather = get_weather_forecast()
    
    print(f"Displaying {len(filtered_events)} events")
    return render_template('index.html', events=filtered_events, weather=weather)

@app.route('/refresh')
def refresh_events():
    """Manual refresh endpoint to test event fetching"""
    events = fetch_hamburg_events()
    return {
        "status": "success",
        "message": f"Fetched {len(events)} events",
        "sample_events": events[:3]  # Show first 3 events
    }
 
if __name__ == '__main__':
    app.run(debug=True)