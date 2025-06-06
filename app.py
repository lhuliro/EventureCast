from flask import Flask, render_template
import http.client
import json

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
                "end_date": event.get("datum_iso", ""),  # same as start_date for one-day events
                "location": "Hamburg",  # static value for now
                "venue": event.get("location", ""),
                "time": event.get("zeit", ""),
                "category": event.get("kategorie", ""),
                "id": event.get("id", ""),
                "image": "https://example.com/default.jpg"  # placeholder image
            })
        return formatted_events
    except Exception as e:
        print("❌ Error fetching events:", e)
        return []

@app.route("/")
def index():
    events = fetch_hamburg_events()
    return render_template("index.html", events=events)

if __name__ == "__main__":
    app.run(debug=True)
