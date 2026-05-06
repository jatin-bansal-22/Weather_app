import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# API Key
#API_KEY = "9b4ec332e433dcc34ddb0529124981d8"
API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    st.error("API key not found.")
    st.stop()

# Page config
st.set_page_config(page_title="Weather Information System")

st.title("🌤 WEATHER INFORMATION SYSTEM")

# Sidebar menu
menu = st.sidebar.selectbox(
    "Menu",
    ["Check Weather", "5-Day Forecast", "View History", "Clear History"]
)

# Emoji dictionary
weather_emojis = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Haze": "🌫️"
}

# -------- SINGLE CITY WEATHER --------
def show_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except:
        st.error("Network error.")
        return

    if str(data.get("cod")) != "200":
        st.error(f"City not found: {data.get('message', 'Something went wrong')}")
        return

    temperature = round(data["main"]["temp"])
    humidity    = data["main"]["humidity"]
    condition   = data["weather"][0]["main"]
    wind_speed  = data["wind"]["speed"]

    emoji = weather_emojis.get(condition, "")

    if temperature >= 30:
        temp_emoji = "🔥"
    elif temperature <= 10:
        temp_emoji = "❄️"
    else:
        temp_emoji = "🙂"

    # -------- DISPLAY --------
    st.success(f"Weather in {city}")
    st.write(f"**Condition:** {condition} {emoji}")
    st.write(f"**Temperature:** {temperature} °C {temp_emoji}")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Speed:** {wind_speed} m/s")

    # -------- ALERT --------
    if temperature >= 35:
        st.error("⚠ Extreme Heat Alert 🔥")
    elif temperature <= 5:
        st.warning("⚠ Extreme Cold Alert ❄️")

    # -------- GRAPH --------
    values = [temperature, humidity, wind_speed]
    labels  = ["Temp (°C)", "Humidity (%)", "Wind (m/s)"]

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values)
    plt.title(f"Weather Details for {city}")
    plt.ylabel("Values")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for i, v in enumerate(values):
        plt.text(i, v + 0.5, str(v), ha='center')

    st.pyplot(plt)
    plt.close()

    # -------- SAVE HISTORY --------
    with open("history.txt", "a") as file:
        file.write(
            f"{city} | {condition} | {temperature}°C | Humidity:{humidity}% | Wind:{wind_speed} m/s\n"
        )

# -------- MULTI CITY COMPARISON --------
def compare_cities(cities):
    temps        = []
    valid_cities = []

    for city in cities:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

        try:
            response = requests.get(url, timeout=5)
            data     = response.json()

            if str(data.get("cod")) == "200":
                temperature = round(data["main"]["temp"])
                temps.append(temperature)
                valid_cities.append(city)
            else:
                st.warning(f"'{city}' not found — skipping.")

        except:
            st.error("Network error.")
            return

    if temps:
        st.subheader("📊 City Comparison")

        plt.figure(figsize=(7, 4))
        plt.bar(valid_cities, temps)
        plt.title("Temperature Comparison Between Cities")
        plt.ylabel("Temperature (°C)")

        for i, v in enumerate(temps):
            plt.text(i, v + 0.5, str(v), ha='center')

        st.pyplot(plt)
        plt.close()

# -------- 5-DAY FORECAST --------
def show_forecast(city):
    # OpenWeatherMap free plan gives forecast every 3 hours for 5 days
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=5)
        data     = response.json()
    except:
        st.error("Network error.")
        return

    if str(data.get("cod")) != "200":
        st.error(f"City not found: {data.get('message', 'Something went wrong')}")
        return

    # -------- EXTRACT DATA --------
    # API returns one entry every 3 hours — we pick one per day (noon reading)
    daily = {}

    for entry in data["list"]:
        # entry["dt_txt"] looks like "2024-04-11 12:00:00"
        date_str  = entry["dt_txt"].split(" ")[0]   # "2024-04-11"
        time_str  = entry["dt_txt"].split(" ")[1]   # "12:00:00"

        # Only take the 12:00 reading as the representative for that day
        if time_str == "12:00:00" and date_str not in daily:
            daily[date_str] = {
                "temp"      : round(entry["main"]["temp"]),
                "humidity"  : entry["main"]["humidity"],
                "condition" : entry["weather"][0]["main"],
                "wind"      : entry["wind"]["speed"]
            }

    # If no noon readings found (can happen for today), fall back to first reading per day
    if not daily:
        for entry in data["list"]:
            date_str = entry["dt_txt"].split(" ")[0]
            if date_str not in daily:
                daily[date_str] = {
                    "temp"      : round(entry["main"]["temp"]),
                    "humidity"  : entry["main"]["humidity"],
                    "condition" : entry["weather"][0]["main"],
                    "wind"      : entry["wind"]["speed"]
                }

    # -------- DISPLAY FORECAST TABLE --------
    st.success(f"5-Day Forecast for {city}")
    st.markdown("---")

    dates  = list(daily.keys())
    temps  = [daily[d]["temp"]     for d in dates]
    humids = [daily[d]["humidity"] for d in dates]

    # Show each day as a card-style row
    for date in dates:
        info      = daily[date]
        emoji     = weather_emojis.get(info["condition"], "")
        # Format date nicely: "2024-04-11" → "Thu, Apr 11"
        formatted = datetime.strptime(date, "%Y-%m-%d").strftime("%a, %b %d")

        st.write(
            f"**{formatted}** — {info['condition']} {emoji} | "
            f"🌡 {info['temp']}°C | "
            f"💧 {info['humidity']}% | "
            f"💨 {info['wind']} m/s"
        )

    st.markdown("---")

    # -------- LINE CHART: TEMPERATURE --------
    st.subheader("🌡 Temperature Trend (Next 5 Days)")

    # Format dates nicely for x-axis labels
    formatted_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%a %d") for d in dates]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(formatted_dates, temps, marker='o', color='tomato', linewidth=2, markersize=7)

    # Add temperature value labels above each point
    for i, temp in enumerate(temps):
        ax.annotate(f"{temp}°C", (formatted_dates[i], temp),
                    textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)

    ax.set_title(f"Temperature Forecast — {city}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # -------- LINE CHART: HUMIDITY --------
    st.subheader("💧 Humidity Trend (Next 5 Days)")

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(formatted_dates, humids, marker='s', color='steelblue', linewidth=2, markersize=7)

    for i, h in enumerate(humids):
        ax2.annotate(f"{h}%", (formatted_dates[i], h),
                     textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)

    ax2.set_title(f"Humidity Forecast — {city}")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Humidity (%)")
    ax2.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

# ==============================
#           MAIN
# ==============================

# -------- CHECK WEATHER --------
if menu == "Check Weather":
    st.subheader("Check Weather")

    search_input = st.text_input(
        "🔍 Enter city or cities (comma separated for comparison):",
        placeholder="e.g. Delhi   or   Delhi, Mumbai, Patiala"
    )

    cities = [c.strip() for c in search_input.split(",") if c.strip()]

    if cities:
        if len(cities) == 1:
            show_weather(cities[0])
        else:
            compare_cities(cities)
    

# -------- 5-DAY FORECAST --------
elif menu == "5-Day Forecast":
    st.subheader("5-Day Forecast")

    forecast_input = st.text_input(
        "🔍 Enter city name:",
        placeholder="e.g. Patiala"
    )

    if forecast_input.strip():
        show_forecast(forecast_input.strip())
    else:
        st.info("Enter a city name above to see the 5-day forecast.")

# -------- VIEW HISTORY --------
elif menu == "View History":
    st.subheader("Search History")

    try:
        with open("history.txt", "r") as file:
            history = file.read()
            if history.strip() == "":
                st.info("No history available.")
            else:
                st.text(history)
    except FileNotFoundError:
        st.info("No history file found.")

# -------- CLEAR HISTORY --------
elif menu == "Clear History":
    st.subheader("Clear History")

    if st.button("Clear History"):
        open("history.txt", "w").close()
        st.success("History cleared.")
