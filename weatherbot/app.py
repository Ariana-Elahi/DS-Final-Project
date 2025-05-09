from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import re

app = Flask(__name__)

# Load and clean 2016 dataset from final_weather_comparison (1).csv
try:
    local_data = pd.read_csv("final_weather_comparison (1).csv")
    local_data.rename(columns={
        "Station.State_dataset": "Station.State",
        "Date.Year_dataset": "Date.Year",
        "Date.Month_dataset": "Date.Month",
        "Data.Precipitation_dataset": "Data.Precipitation",
        "Data.Temperature.Avg Temp_dataset": "Data.Temperature.Avg Temp",
        "Data.Wind.Speed_dataset": "Data.Wind.Speed",
        "Data.Wind.Direction_dataset": "Data.Wind.Direction"
    }, inplace=True)
except FileNotFoundError:
    print("Warning: CSV not found.")
    local_data = pd.DataFrame()

WEATHER_API_KEY = "23b0589184d4491b85923455251903"

def get_current_weather(location):
    try:
        url = "http://api.weatherapi.com/v1/current.json"
        params = {"key": WEATHER_API_KEY, "q": location}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        current = data["current"]
        return {
            "Location": data["location"]["name"],
            "Region": data["location"]["region"],
            "Temperature": current["temp_f"],
            "Humidity": current["humidity"],
            "Precipitation": current["precip_mm"],
            "Wind Speed": current["wind_mph"],
            "Wind Direction": current["wind_dir"],
            "UV Index": current["uv"],
            "Time": current["last_updated"]
        }
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").lower()
    match = re.search(r"in ([a-zA-Z ]+?)(?: in|$)", user_input)
    location = match.group(1).strip().title() if match else ""

    # === Live WeatherAPI section ===
    if any(term in user_input for term in ["current", "uv", "humidity", "wind", "precipitation", "temperature"]) and "2016" not in user_input:
        if location:
            result = get_current_weather(location)
            if "error" in result:
                return jsonify({"response": f"Weather API error: {result['error']}"})
            if "uv" in user_input:
                return jsonify({"response": f"UV Index in {result['Location']}, {result['Region']}: {result['UV Index']}"})
            if "humidity" in user_input:
                return jsonify({"response": f"Humidity in {result['Location']}, {result['Region']}: {result['Humidity']}%"})
            if "wind speed" in user_input:
                return jsonify({"response": f"Wind speed in {result['Location']}, {result['Region']}: {result['Wind Speed']} mph"})
            if "wind direction" in user_input:
                return jsonify({"response": f"Wind direction in {result['Location']}, {result['Region']}: {result['Wind Direction']}"})
            if "precipitation" in user_input:
                return jsonify({"response": f"Precipitation in {result['Location']}, {result['Region']}: {result['Precipitation']} mm"})
            if "temperature" in user_input:
                return jsonify({"response": f"Temperature in {result['Location']}, {result['Region']}: {result['Temperature']}°F"})
            if "current weather" in user_input:
                return jsonify({"response": f"Current weather in {result['Location']}, {result['Region']}:\n"
                                            f"- Temperature: {result['Temperature']}°F\n"
                                            f"- Humidity: {result['Humidity']}%\n"
                                            f"- Wind: {result['Wind Speed']} mph {result['Wind Direction']}\n"
                                            f"- Precipitation: {result['Precipitation']} mm\n"
                                            f"- UV Index: {result['UV Index']}\n"
                                            f"- Time: {result['Time']}"})
        return jsonify({"response": "Please specify a location for live weather info."})

    # === Historical March 2016 (CSV) section ===
    if "march 2016" in user_input or "2016" in user_input:
        if location:
            filtered = local_data[
                (local_data["Station.State"].str.lower() == location.lower()) &
                (local_data["Date.Year"] == 2016) &
                (local_data["Date.Month"] == 3)
            ]
            if filtered.empty:
                return jsonify({"response": f"No data found for {location} in March 2016."})

            if "temperature" in user_input:
                temp = filtered["Data.Temperature.Avg Temp"].mean()
                return jsonify({"response": f"March 2016 average temperature in {location}: {temp:.2f}°F"})
            if "precipitation" in user_input:
                precip = filtered["Data.Precipitation"].mean()
                return jsonify({"response": f"March 2016 average precipitation in {location}: {precip:.2f} in"})
            if "wind speed" in user_input:
                wind_speed = filtered["Data.Wind.Speed"].mean()
                return jsonify({"response": f"March 2016 average wind speed in {location}: {wind_speed:.2f} mph"})
            if "wind direction" in user_input:
                wind_dir = filtered["Data.Wind.Direction"].mean()
                return jsonify({"response": f"March 2016 average wind direction in {location}: {wind_dir:.2f}°"})

            # Fallback to temp + precip
            temp = filtered["Data.Temperature.Avg Temp"].mean()
            precip = filtered["Data.Precipitation"].mean()
            return jsonify({"response": f"March 2016 weather in {location}:\n"
                                        f"- Temp: {temp:.2f}°F\n- Precip: {precip:.2f} in"})
        return jsonify({"response": "Please specify a U.S. state for March 2016 data."})

    return jsonify({"response": "Try asking:\n"
                                "- 'humidity in California'\n"
                                "- 'temperature in Texas in March 2016'\n"
                                "- 'UV index in Florida'"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
