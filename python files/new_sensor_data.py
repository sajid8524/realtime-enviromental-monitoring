import Adafruit_DHT
import time
import RPi.GPIO as GPIO
import requests
import spidev
import pysqlcipher3.dbapi2 as sqlite  # Secure database storage
from datetime import datetime
from twilio.rest import Client  # Twilio for SMS alerts

# -------------------------- Sensor Setup ----------------------------
DHT_SENSOR = Adafruit_DHT.DHT11  
DHT_PIN = 4  

# Alert System
LED_PIN = 22  
TEMP_THRESHOLD = 30.0  

# ThingSpeak API
THINGSPEAK_API_KEY = "UM0W4WVKM37Y357S"
THINGSPEAK_URL_BASE = "https://api.thingspeak.com/update"

# SPI Configuration for MCP3008 ADC
SPI_BUS = 0  
SPI_DEVICE = 0  

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1350000  

# Database Encryption Key
DB_PASSWORD = "hi"
DB_PATH = "sensor_data_encrypted.db"

# -------------------------- Twilio Configuration ----------------------------
TWILIO_ACCOUNT_SID = "AC936ad43513b73711a32fd3a599f12487"  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = "664078a51f1e327c6042d77d8b0b2a21"  # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = "+12542795363"  # Replace with your Twilio phone number
OWNER_PHONE_NUMBER = "+919652519218"  # Replace with the owner's phone number

# -------------------------- Data Masking ----------------------------
def mask_data(value, mask_char="*"):
    """Fully mask numeric values for secure logging."""
    return mask_char * len(str(value))

# -------------------------- Read ADC Data ----------------------------
def read_adc(channel):
    """Reads data from MCP3008 ADC."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7.")

    adc_response = spi.xfer2([1, (8 + channel) << 4, 0])  

    if len(adc_response) < 3:
        raise RuntimeError(f"SPI response too short: {adc_response}")

    result = ((adc_response[1] & 3) << 8) + adc_response[2]
    return result

# -------------------------- Secure Database Setup ----------------------------
def setup_database():
    """Initializes the encrypted database."""
    conn = sqlite.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA key = '{DB_PASSWORD}';")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        temperature REAL,
        humidity REAL,
        air_quality INTEGER
    )''')

    conn.commit()
    conn.close()

# -------------------------- Store Data Securely ----------------------------
def store_data(temperature, humidity, air_quality):
    """Stores real sensor data securely in the encrypted database."""
    try:
        conn = sqlite.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key = '{DB_PASSWORD}';")

        cursor.execute("INSERT INTO sensor_data (temperature, humidity, air_quality) VALUES (?, ?, ?)",
                       (temperature, humidity, air_quality))

        conn.commit()
        conn.close()
        print("✅ Data securely stored in database.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

# -------------------------- GPIO Setup ----------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Initialize Secure Database
setup_database()

# -------------------------- Track Last SMS Alert Time ----------------------------
last_sms_time = 0  # Store the timestamp of the last SMS sent

# -------------------------- Function to Send SMS Alert ----------------------------
def send_sms_alert(temp):
    """Sends an SMS alert when temperature exceeds the threshold using Twilio."""
    global last_sms_time
    current_time = time.time()

    # Send SMS only if 1 hour (3600 seconds) has passed since last SMS
    if current_time - last_sms_time >= 3600:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"🚨 ALERT: High Temperature Detected! Current Temp: {temp}°C",
            from_=TWILIO_PHONE_NUMBER,
            to=OWNER_PHONE_NUMBER
        )
        last_sms_time = current_time  # Update last alert time
        print(f"📱 SMS alert sent successfully! Message SID: {message.sid}")
    else:
        print("🕒 SMS alert skipped (Sent in the last 1 hour)")



# -------------------------- Main Loop ----------------------------
try:
    while True:
        # Read DHT11 Sensor Data
        humidity, temperature = None, None
        for attempt in range(5):
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                break
            time.sleep(2)

        if humidity is None or temperature is None:
            print("❌ Error: Unable to read DHT11 data.")
            continue  # Skip this cycle

        # Read Air Quality Data
        try:
            air_quality_reading = read_adc(0)
        except RuntimeError as e:
            print(f"❌ ADC Error: {e}")
            air_quality_reading = -1  

        print(f"🌡 Temperature: {temperature}°C, 💧 Humidity: {humidity}%, 🌍 Air Quality: {air_quality_reading}")

        # Send SMS Alert if Temperature Exceeds Threshold
        if temperature > TEMP_THRESHOLD:
            send_sms_alert(temperature)  # Send SMS alert via Twilio
            print("🚨 ALERT: High Temperature!")

        # Store Data Securely
        store_data(temperature, humidity, air_quality_reading)

        # Send Data to ThingSpeak (Real Values)
        params = {
            'api_key': THINGSPEAK_API_KEY,
            'field1': temperature,
            'field2': humidity,
            'field3': air_quality_reading
        }

        print(f"🔄 Sending to ThingSpeak -> Temp: {mask_data(temperature)}, Humidity: {mask_data(humidity)}, Air Quality: {mask_data(air_quality_reading)}")

        # Send Data to ThingSpeak
        try:
            response = requests.get(THINGSPEAK_URL_BASE, params=params, timeout=5)
            response.raise_for_status()
            print(f"✅ ThingSpeak Response: {response.status_code}")
        except requests.RequestException as e:
            print(f"❌ ThingSpeak Error: {e}")

        time.sleep(15)  # Wait before next reading

except KeyboardInterrupt:
    print("\n🛑 Program stopped by user.")
    spi.close()
    GPIO.cleanup()

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    spi.close()
    GPIO.cleanup()