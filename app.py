from flask import Flask, render_template
import requests
import http.client
import json
from codecs import encode
from datetime import datetime, timedelta
from collections import defaultdict
 
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
                    "category": event.get("kategorie", "other"),  # Default to 'other' if no category
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
        },
        {
            "title": "Hamburg Food Festival",
            "start_date": "2025-06-15",
            "end_date": "2025-06-15",
            "location": "Hamburg",
            "venue": "City Center",
            "time": "12:00",
            "category": "food",
            "image": "https://example.com/food.jpg"
        },
        {
            "title": "Art Exhibition Opening",
            "start_date": "2025-06-20",
            "end_date": "2025-06-20",
            "location": "Hamburg",
            "venue": "Museum",
            "time": "18:00",
            "category": "kultur",
            "image": "https://example.com/art.jpg"
        }
    ]

def group_events_by_category(events, max_per_category=5):
    """Group events by category and limit to max_per_category per group"""
    grouped_events = defaultdict(list)
    
    # Sort all events by date first
    events.sort(key=lambda x: x.get('start_date', ''))
    
    # Group events by category
    for event in events:
        category = event.get('category', 'other').lower()
        if len(grouped_events[category]) < max_per_category:
            grouped_events[category].append(event)
    
    # Convert defaultdict to regular dict and sort categories
    result = dict(grouped_events)
    
    # Sort categories alphabetically, but put 'musik' first if it exists
    sorted_categories = sorted(result.keys())
    if 'musik' in sorted_categories:
        sorted_categories.remove('musik')
        sorted_categories.insert(0, 'musik')
    
    return {category: result[category] for category in sorted_categories}

def get_weather_for_date(target_date_str):
    """Get weather forecast for a specific date"""
    OPENWEATHER_API_KEY = 'f82e99474e42cf049967aa24ccd739fa'
    lat = 53.5511   # Hamburg latitude
    lon = 9.9937    # Hamburg longitude
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_from_now = (target_date - today).days
        
        # If the date is more than 5 days away, use estimated weather
        if days_from_now > 5:
            return get_estimated_weather_for_date(target_date_str)
        
        # If the date is within 5 days, try to get real forecast
        if days_from_now < 0:
            # Past date - return None or historical average
            return None
            
        # Use 5-day forecast API for dates within 5 days
        url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
        )
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Find forecast for the target date
        for item in data['list']:
            forecast_date = datetime.utcfromtimestamp(item['dt']).date()
            if forecast_date == target_date:
                temp = float(item['main']['temp'])
                return {
                    'temp_day': temp,
                    'temp_night': temp - 5.0,  # Estimate night temp
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'humidity': int(item['main']['humidity']),
                    'wind_speed': float(item['wind']['speed']),
                    'pop': float(item.get('pop', 0.0)) * 100  # Convert to percentage
                }
        
        # If exact date not found, return estimated weather
        return get_estimated_weather_for_date(target_date_str)
        
    except Exception as e:
        print(f"❌ Error fetching weather for {target_date_str}: {e}")
        return get_estimated_weather_for_date(target_date_str)

def get_estimated_weather_for_date(date_str):
    """Generate estimated weather for dates beyond forecast range"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        month = target_date.month
        
        # Hamburg seasonal averages
        seasonal_temps = {
            12: {'day': 4, 'night': 0},   # December
            1: {'day': 3, 'night': -1},   # January
            2: {'day': 5, 'night': 0},    # February
            3: {'day': 9, 'night': 3},    # March
            4: {'day': 14, 'night': 6},   # April
            5: {'day': 19, 'night': 10},  # May
            6: {'day': 22, 'night': 13},  # June
            7: {'day': 24, 'night': 15},  # July
            8: {'day': 24, 'night': 15},  # August
            9: {'day': 20, 'night': 12},  # September
            10: {'day': 14, 'night': 8},  # October
            11: {'day': 8, 'night': 4},   # November
        }
        
        temp_data = seasonal_temps.get(month, {'day': 15, 'night': 10})
        
        # Add some randomness to make it more realistic
        import random
        temp_variation = random.randint(-3, 3)
        
        return {
            'temp_day': float(temp_data['day'] + temp_variation),
            'temp_night': float(temp_data['night'] + temp_variation),
            'description': 'partly cloudy',
            'icon': '02d',
            'humidity': 65,
            'wind_speed': 3.5,
            'pop': 20.0  # 20% chance of precipitation
        }
    except Exception as e:
        print(f"❌ Error generating estimated weather: {e}")
        return {
            'temp_day': 15.0,
            'temp_night': 10.0,
            'description': 'partly cloudy',
            'icon': '02d',
            'humidity': 65,
            'wind_speed': 3.5,
            'pop': 20.0
        }

def get_weather_forecast():
    """Get weather forecast for display in the weather section"""
    OPENWEATHER_API_KEY = 'f82e99474e42cf049967aa24ccd739fa'
    lat = 53.5511   # Hamburg latitude
    lon = 9.9937    # Hamburg longitude
    
    # Try OneCall API first (for up to 8 days)
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts"
        f"&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        forecasts = data.get('daily', [])[:8]  # Get up to 8 days
        
        weather_data = []
        for day in forecasts:
            # Safely extract values with proper defaults
            temp_data = day.get('temp', {})
            weather_info = day.get('weather', [{}])
            
            weather_entry = {
                'readable_date': datetime.utcfromtimestamp(day['dt']).strftime('%Y-%m-%d'),
                'temp': {
                    'day': float(temp_data.get('day', 15)),
                    'night': float(temp_data.get('night', 10))
                },
                'weather': [{
                    'description': weather_info[0].get('description', 'partly cloudy') if weather_info else 'partly cloudy',
                    'icon': weather_info[0].get('icon', '01d') if weather_info else '01d'
                }],
                'humidity': int(day.get('humidity', 50)),
                'wind_speed': float(day.get('wind_speed', 3.0)),
                'pop': float(day.get('pop', 0.0)),
                'dt': int(day['dt'])
            }
            weather_data.append(weather_entry)
        
        print(f"✅ Successfully fetched weather for {len(weather_data)} days")
        return weather_data
        
    except Exception as e:
        print(f"❌ Error fetching weather from OneCall API: {e}")
        # Fallback to 5-day forecast API
        return get_fallback_weather_forecast()

def get_fallback_weather_forecast():
    """Fallback to 5-day forecast API"""
    OPENWEATHER_API_KEY = 'f82e99474e42cf049967aa24ccd739fa'
    lat = 53.5511
    lon = 9.9937
    
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=en"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Group 3-hourly forecasts by day and get daily averages
        daily_data = {}
        
        for item in data['list']:
            date_str = datetime.utcfromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'temps': [],
                    'humidity': [],
                    'wind_speed': [],
                    'weather_desc': [],
                    'pop': []
                }
            
            daily_data[date_str]['temps'].append(float(item['main']['temp']))
            daily_data[date_str]['humidity'].append(int(item['main']['humidity']))
            daily_data[date_str]['wind_speed'].append(float(item['wind']['speed']))
            daily_data[date_str]['weather_desc'].append(item['weather'][0]['description'])
            daily_data[date_str]['pop'].append(float(item.get('pop', 0.0)))
        
        # Convert to format similar to OneCall API
        weather_data = []
        for date_str, day_data in daily_data.items():
            if day_data['temps']:  # Make sure we have data
                avg_temp = sum(day_data['temps']) / len(day_data['temps'])
                avg_humidity = sum(day_data['humidity']) / len(day_data['humidity'])
                avg_wind = sum(day_data['wind_speed']) / len(day_data['wind_speed'])
                
                # Get most common weather description
                most_common_desc = max(set(day_data['weather_desc']), key=day_data['weather_desc'].count)
                max_pop = max(day_data['pop']) if day_data['pop'] else 0.0
                
                weather_entry = {
                    'readable_date': date_str,
                    'temp': {
                        'day': float(avg_temp),
                        'night': float(avg_temp - 5)  # Estimate night temp
                    },
                    'weather': [{
                        'description': most_common_desc,
                        'icon': '01d'  # Default icon
                    }],
                    'humidity': int(avg_humidity),
                    'wind_speed': float(avg_wind),
                    'pop': float(max_pop),
                    'dt': int(datetime.strptime(date_str, '%Y-%m-%d').timestamp())
                }
                weather_data.append(weather_entry)
        
        print(f"✅ Fallback weather fetched for {len(weather_data)} days")
        return weather_data
        
    except Exception as e:
        print(f"❌ Error fetching fallback weather: {e}")
        return get_default_weather()

def get_default_weather():
    """Provide default weather data if all APIs fail"""
    default_weather = []
    base_date = datetime.now().date()
    
    for i in range(7):
        date = base_date + timedelta(days=i)
        weather_entry = {
            'readable_date': date.strftime('%Y-%m-%d'),
            'temp': {
                'day': 18.0,
                'night': 12.0
            },
            'weather': [{
                'description': 'partly cloudy',
                'icon': '02d'
            }],
            'humidity': 65,
            'wind_speed': 3.5,
            'pop': 0.2,
            'dt': int(datetime.combine(date, datetime.min.time()).timestamp())
        }
        default_weather.append(weather_entry)
    
    print("📊 Using default weather data")
    return default_weather

def match_weather_to_events(events):
    """Get weather data for each event individually"""
    print(f"🔍 Matching weather for {len(events)} events")
    
    # Add weather info to each event
    for event in events:
        event_date = event.get('start_date', '')
        event_title = event.get('title', 'Unknown')
        print(f"🔍 Getting weather for event on {event_date}: {event_title}")
        
        if event_date:
            weather_data = get_weather_for_date(event_date)
            if weather_data:
                event['weather'] = weather_data
                print(f"✅ Weather found for {event_date}")
            else:
                event['weather'] = None
                print(f"❌ No weather data for {event_date}")
        else:
            event['weather'] = None
            print(f"❌ No date for event: {event_title}")
    
    return events
 
@app.route('/')
def index():
    try:
        # Fetch real events from the API
        events = fetch_hamburg_events()
        
        # Get weather forecast for the weather section
        weather_forecasts = get_weather_forecast()
        
        # Filter events by date range (show events for the next 30 days)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30)
    
        filtered_events = []
        for event in events:
            try:
                event_date_str = event.get('start_date', '')
                if event_date_str:
                    event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                    if start_date <= event_date <= end_date:
                        filtered_events.append(event)
            except (ValueError, KeyError) as e:
                print(f"⚠️ Skipping event with invalid date: {e}")
                continue
        
        # Match weather data to events (this now works for any date)
        events_with_weather = match_weather_to_events(filtered_events)
        
        # Group events by category (max 5 per category)
        grouped_events = group_events_by_category(events_with_weather, max_per_category=5)
        
        total_events = sum(len(event_list) for event_list in grouped_events.values())
        print(f"Displaying {total_events} events across {len(grouped_events)} categories")
        
        return render_template('index.html', grouped_events=grouped_events, weather_forecasts=weather_forecasts)
    
    except Exception as e:
        print(f"❌ Error in main route: {e}")
        # Return a basic error page or fallback data
        fallback_events = get_fallback_events()
        fallback_weather = get_default_weather()
        events_with_weather = match_weather_to_events(fallback_events)
        grouped_events = group_events_by_category(events_with_weather, max_per_category=5)
        
        return render_template('index.html', grouped_events=grouped_events, weather_forecasts=fallback_weather)

@app.route('/refresh')
def refresh_events():
    """Manual refresh endpoint to test event fetching"""
    try:
        events = fetch_hamburg_events()
        grouped_events = group_events_by_category(events, max_per_category=5)
        
        return {
            "status": "success",  
            "message": f"Fetched events across {len(grouped_events)} categories",
            "categories": {cat: len(event_list) for cat, event_list in grouped_events.items()},
            "sample_events": {cat: event_list[:2] for cat, event_list in grouped_events.items()}  # Show first 2 per category
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error refreshing events: {str(e)}"
        }
 
if __name__ == '__main__':
    app.run(debug=True)