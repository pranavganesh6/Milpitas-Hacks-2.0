from together import Together
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

# ROUTE 0: Serve Frontend
@app.route("/")
def home():
    return render_template("index.html")

TOGETHER_API_KEY = "INSERT_YOUR_API_KEY_HERE"
client = Together(api_key=TOGETHER_API_KEY)

# ROUTE 1: Chatbot Endpoint
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data["messages"]
    location = data.get("location")
    user_prompt = messages[-1]["content"].lower()
    messages.insert(0, {
        "role": "system",
        "content":
            "You are a chatbot designed to assist users through specific step-by-step instructions for specific emergencies that require the user to stay silent, such as reporting domestic abuse, kidnappings, active shooters, etc."
            "Your only output should be the instructions, nothing else."
            "The instructions should be numbered, brief, and easy to follow so that even under extreme pressure it can still be followed. Here is an example of a prompt and how you should respond:"
            "Prompt: I got locked in a room by my abusive uncle and I hear yelling and glass breaking. How do I get out of the room?"
            "Response: 1. Look for any weak spots in the lock. If the lock is inside, find a thin material such as a paper clip and/or coat hanger that is metal."
            "2. Stick the thin piece of metal into the lock. It should open."
            "3. Get out and run. I've already contacted emergency services. Stay safe, and keep running. Try and get out of the house if you can. "
            "You will provide instructions and ONLY instructions. Nothing else matters. Do not comfort the user. Your only job is to tell them what to do in the emergency."
            " In the case where the user or another person is in a life-threatening situation, or has a fatal injury, you will suggest to them to use the panic button,"
            " which is a feature on the website the user will access you through. If the user clicks the panic button, the website will alert the local authorities based on the user's responses, location, and the timestamp. The website already tracks the user's location, but you can prompt the user for more information on their specific location."
            "Meanwhile, the Blue Escape & Alert Authorities button will do the same thing as the panic button, but also close the website after tipping emergency services so that anyone who walks in on the user cannot see them signaling for help."
            " You will assess the severity of the situation based on the user's prompt. If the situation seems life-threatening, only then will you direct them to the panic button."
    })

    danger_keywords = ["shooter", "bleeding", "stabbed", "abuse", "dying", "help", "gun", "kidnap", "danger"]
    is_dangerous = any(word in user_prompt for word in danger_keywords)

    if is_dangerous and location:
        print("PANIC ALERT TRIGGERED")
        print("Location:", location)
        print("Time:", datetime.now().isoformat())

    stream = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=messages,
        stream=False
    )
    return jsonify({"reply": stream.choices[0].message.content})

@app.route("/api/location-info", methods=["POST"])
def location_info():
    data = request.get_json()
    loc = data.get("location", {})
    lat, lon = loc.get("latitude"), loc.get("longitude")
    geo = Nominatim(user_agent="safe_support_app").reverse(f"{lat}, {lon}")
    addr = geo.raw.get("address", {})
    city = addr.get("city") or addr.get("town") or addr.get("village") or ""
    country = addr.get("country", "")
    return jsonify({"city": city, "country": country})

# A default style mapping: everything defaults to "112", with overrides
EMERGENCY_NUMBERS = {
    # North America
    "US": "911", "CA": "911", "MX": "066", "BR": "190",
    # Oceania
    "AU": "000", "NZ": "111",
    # East Asia
    "CN": "110", "JP": "119", "KR": "112",
    # South Asia
    "IN": "112", "PK": "15", "BD": "999",
    # Middle East
    "AE": "112", "SA": "999", "IL": "100",
    # Africa (common)
    "ZA": "10111", "NG": "112", "EG": "122",
    # Latin America
    "AR": "911", "CO": "123", "CL": "131",
}
# Fallback for all others: "112"

# ROUTE 2: Domestic Emergency Endpoint
@app.route("/api/domestic-emergency", methods=["POST"])
def handle_de():
    data = request.get_json()
    loc = data.get("location", {})
    lat, lon = loc.get("latitude"), loc.get("longitude")

    geo = Nominatim(user_agent="safe_support_app").reverse(f"{lat}, {lon}")
    iso = geo.raw.get("address", {}).get("country_code", "").upper()

    number = EMERGENCY_NUMBERS.get(iso, "112")

    print(f"Domestic Emergency for {iso} → dialing {number}")
    return jsonify({"status": "DE number resolved", "country": iso, "number": number})

# ROUTE 3: Panic Button Endpoint
@app.route("/api/panic", methods=["POST"])
def handle_panic():
    data = request.get_json()
    print("Panic Button Activated:")
    print(data)
    return jsonify({"status": "Panic alert received"})

if __name__ == "__main__":
    app.run(debug=True)
