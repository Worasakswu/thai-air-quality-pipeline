"""Dashboard แสดงค่าฝุ่น PM2.5 จากฐานข้อมูล air_quality"""
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Thai Air Quality", page_icon="🌫️", layout="wide")


@st.cache_data(ttl=600)
def load_data():
    conn = psycopg2.connect(dbname="mydb")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT city, measured_at, pm2_5, pm10 "
                "FROM air_quality ORDER BY measured_at"
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=["city", "measured_at", "pm2_5", "pm10"])


st.title("🌫️ Thai Air Quality Dashboard")
st.caption("ค่าฝุ่น PM2.5 รายชั่วโมง (µg/m³) จาก Open-Meteo API")

df = load_data()
if df.empty:
    st.warning("ยังไม่มีข้อมูล ลองรัน python etl.py ก่อน")
    st.stop()

all_cities = sorted(df["city"].unique())
cities = st.sidebar.multiselect("เลือกเมือง", all_cities, default=all_cities)
if not cities:
    st.info("เลือกอย่างน้อย 1 เมืองจากแถบด้านซ้าย")
    st.stop()
df = df[df["city"].isin(cities)]

# ค่าล่าสุดของแต่ละเมือง
st.subheader("ค่าล่าสุด")
latest = df.sort_values("measured_at").groupby("city").tail(1)
for col, row in zip(st.columns(len(latest)), latest.itertuples()):
    col.metric(row.city, f"{row.pm2_5:.1f}")

# กราฟเส้นตามเวลา
st.subheader("PM2.5 รายชั่วโมง")
trend = df.pivot_table(index="measured_at", columns="city", values="pm2_5")
st.line_chart(trend)

# ค่าเฉลี่ยแต่ละเมือง
st.subheader("ค่าเฉลี่ย PM2.5 แต่ละเมือง")
avg = df.groupby("city")["pm2_5"].mean().sort_values(ascending=False)
st.bar_chart(avg)

with st.expander("ดูข้อมูลดิบ"):
    st.dataframe(df.sort_values("measured_at", ascending=False), use_container_width=True)
