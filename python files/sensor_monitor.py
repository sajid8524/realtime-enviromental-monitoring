import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ThingSpeak API URL (Replace with your Channel ID)
CHANNEL_ID = "2844187"
THINGSPEAK_API_KEY = "UM0W4WVKM37Y357S"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=20"

def fetch_thingspeak_data():
    """Fetches data from ThingSpeak API and returns a DataFrame."""
    response = requests.get(THINGSPEAK_URL)
    
    if response.status_code == 200:
        data = response.json()
        feeds = data["feeds"]
        
        # Convert JSON data to pandas DataFrame
        df = pd.DataFrame(feeds)
        
        # Convert timestamp to datetime format
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        # Rename columns
        df = df.rename(columns={"field1": "Temperature", "field2": "Humidity", "field3": "Air Quality"})
        
        # Convert values to numeric (ignore errors if empty)
        df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
        df["Humidity"] = pd.to_numeric(df["Humidity"], errors="coerce")
        df["Air Quality"] = pd.to_numeric(df["Air Quality"], errors="coerce")
        
        return df
    else:
        print(f"❌ Error fetching data: {response.status_code}")
        return pd.DataFrame()

def plot_sensor_data(df):
    """Plots temperature, humidity, and air quality."""
    plt.figure(figsize=(10, 5))
    
    plt.plot(df["created_at"], df["Temperature"], label="🌡 Temperature (°C)", color="red", marker="o")
    plt.plot(df["created_at"], df["Humidity"], label="💧 Humidity (%)", color="blue", marker="s")
    plt.plot(df["created_at"], df["Air Quality"], label="🌍 Air Quality", color="green", marker="^")

    plt.xlabel("Time")
    plt.ylabel("Sensor Readings")
    plt.title("📊 Sensor Data from ThingSpeak")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

# Fetch and plot data
df = fetch_thingspeak_data()
if not df.empty:
    plot_sensor_data(df)
else:
    print("❌ No data available to plot.")
