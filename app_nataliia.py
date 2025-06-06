import http.client

conn = http.client.HTTPSConnection("www.wasgehtapp.de")
payload = ''
headers = {
  'Cookie': 'lv=1747851903; v=1; vc=2'
}
conn.request("GET", "/export.php?mail=ghaith.alshathi.24@nithh.onmicrosoft.com&passwort=Gatetomba90&columns=null", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

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