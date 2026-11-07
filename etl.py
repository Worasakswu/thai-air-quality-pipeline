"""ETL pipeline: ดึงค่าฝุ่น PM2.5/PM10 ของเมืองในไทยจาก Open-Meteo แล้วบันทึกลง PostgreSQL"""
import requests
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
CITIES = {
    "Bangkok": (13.75, 100.50),
    "Chiang Mai": (18.79, 98.98),
    "Khon Kaen": (16.43, 102.83),
    "Phuket": (7.88, 98.39),
}


def extract(city, lat, lon, past_days=1):
    """ดึงข้อมูลรายชั่วโมงย้อนหลัง 1 วันจาก API"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10",
        "timezone": "Asia/Bangkok",
        "past_days": past_days,
        "forecast_days": 1,
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    df = pd.DataFrame(response.json()["hourly"])
    df["city"] = city
    return df


def transform(df):
    """แปลงชนิดข้อมูล ตัดค่าพยากรณ์อนาคตและแถวที่ไม่มีค่าออก"""
    df = df.rename(columns={"time": "measured_at"})
    df["measured_at"] = pd.to_datetime(df["measured_at"])
    now = pd.Timestamp.now(tz="Asia/Bangkok").tz_localize(None)
    df = df[df["measured_at"] <= now]
    df = df.dropna(subset=["pm2_5", "pm10"])
    return df[["city", "measured_at", "pm2_5", "pm10"]]


def load(df):
    """บันทึกลง PostgreSQL ข้ามแถวที่มีอยู่แล้ว"""
    rows = list(df.itertuples(index=False, name=None))
    sql = """
        INSERT INTO air_quality (city, measured_at, pm2_5, pm10)
        VALUES %s
        ON CONFLICT (city, measured_at) DO NOTHING
    """
    conn = psycopg2.connect(dbname="mydb")
    try:
        with conn, conn.cursor() as cur:
            execute_values(cur, sql, rows, page_size=1000)
            return cur.rowcount
    finally:
        conn.close()


def main():
    past_days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    frames = [extract(city, lat, lon, past_days) for city, (lat, lon) in CITIES.items()]
    df = transform(pd.concat(frames, ignore_index=True))
    inserted = load(df)
    print(f"ดึงมา {len(df)} แถว, บันทึกใหม่ {inserted} แถว")


if __name__ == "__main__":
    main()
