from flask import Flask, render_template, request
import http.client
import json
from urllib.parse import urlencode

app = Flask(__name__)

def fetch_hamburg_events():
    try:
        conn = http.client.HTTPSConnection("www.wasgehtapp.de")
        conn.request("GET", "/export.php?mail=ghaith.alshathi.24@nithh.onmicrosoft.com&passwort=Gatetomba90&columns=null", "", {
            'Cookie': 'lv=1747851903; v=1; vc=2'
        })
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        events_data = json.loads(data)

        formatted_events = []
        for event in events_data.get("data", []):
            formatted_events.append({
                "title": event.get("titel", ""),
                "start_date": event.get("datum_iso", ""),
                "end_date": event.get("datum_iso", ""),
                "location": "Hamburg",
                "venue": event.get("location", ""),
                "time": event.get("zeit", ""),
                "category": event.get("kategorie", ""),
                "id": event.get("id", ""),
                "image": event.get("bild_url", "https://example.com/default.jpg")
            })
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

    def filter_event(event):
        if date_filter and event["start_date"][:10] != date_filter:
            return False
        if time_filter and time_filter.lower() not in event.get("time", "").lower():
            return False
        if category_filter and category_filter.lower() not in event.get("category", "").lower():
            return False
        if venue_filter and venue_filter.lower() not in event.get("venue", "").lower():
            return False
        return True

    filtered_events = [e for e in events if filter_event(e)]
    categories = sorted(set(e['category'] for e in events if e['category']))

    return render_template("index.html", events=filtered_events, date_filter=date_filter,
                           time_filter=time_filter, category_filter=category_filter,
                           venue_filter=venue_filter, categories=categories)

if __name__ == "__main__":
    app.run(debug=True)
