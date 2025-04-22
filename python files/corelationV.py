import pysqlcipher3.dbapi2 as sqlite
import pandas as pd
from scipy.stats import pearsonr

# Database Credentials
DB_PASSWORD = "hi"
DB_PATH = "sensor_data_encrypted.db"

def fetch_sensor_data():
    """Fetch temperature, humidity, and air quality data from the encrypted database."""
    try:
        # Connect to the encrypted SQLite database
        conn = sqlite.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Unlock the encrypted database with the password
        cursor.execute(f"PRAGMA key = '{DB_PASSWORD}';")

        # Fetch the data
        query = "SELECT temperature, humidity, air_quality FROM sensor_data"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            print("⚠ No data found in the database!")
            return None
        
        return df

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def correlation_analysis(df):
    """Calculates and prints Pearson correlation between temperature, humidity, and air quality."""
    print("\n🔍 Correlation Analysis:")

    if df is not None:
        temp_hum_corr, _ = pearsonr(df['temperature'], df['humidity'])
        temp_air_corr, _ = pearsonr(df['temperature'], df['air_quality'])
        hum_air_corr, _ = pearsonr(df['humidity'], df['air_quality'])

        print(f"📈 Temperature ↔ Humidity: {temp_hum_corr:.2f}")
        print(f"🔥 Temperature ↔ Air Quality: {temp_air_corr:.2f}")
        print(f"💧 Humidity ↔ Air Quality: {hum_air_corr:.2f}")

        # Interpretation
        print("\n📊 Interpretation:")
        for name, value in [("Temp-Humidity", temp_hum_corr), ("Temp-Air Quality", temp_air_corr), ("Humidity-Air Quality", hum_air_corr)]:
            if value > 0.5:
                print(f"✅ {name}: Strong Positive Correlation")
            elif 0.0 < value <= 0.5:
                print(f"⚠ {name}: Weak Positive Correlation")
            elif -0.5 <= value < 0.0:
                print(f"⚠ {name}: Weak Negative Correlation")
            else:
                print(f"❌ {name}: Strong Negative Correlation")

# Direct execution without needing a main function
data = fetch_sensor_data()
if data is not None:
    correlation_analysis(data)

