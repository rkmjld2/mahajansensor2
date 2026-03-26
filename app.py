import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Sensor Dashboard", layout="wide")
st.title("📊 Sensor Dashboard - TiDB Cloud")

# Database Connection
@st.cache_resource
def get_connection():
    secrets = st.secrets["tidb"]
    ca_path = "isrg_root_x1.pem"

    return pymysql.connect(
        host=secrets["host"],
        port=secrets["port"],
        user=secrets["user"],
        password=secrets["password"],
        database=secrets["database"],
        ssl={'ca': ca_path, 'verify_cert': True},
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# Create table if not exists
def init_table():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                temperature FLOAT,
                humidity FLOAT,
                device_id VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()

init_table()

# Sidebar - Manual Entry
st.sidebar.header("Add Manual Reading")
with st.sidebar.form("manual_entry"):
    temp = st.number_input("Temperature (°C)", value=25.0, format="%.2f")
    hum = st.number_input("Humidity (%)", value=60.0, format="%.2f")
    device = st.text_input("Device ID", value="Manual")
    submitted = st.form_submit_button("Insert Reading")
    
    if submitted:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO readings (temperature, humidity, device_id) VALUES (%s, %s, %s)", 
                       (temp, hum, device))
        st.success("Manual reading added!")

# Main Dashboard
st.header("Live Sensor Readings")

try:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM readings ORDER BY created_at DESC LIMIT 100", conn)
    conn.close()

    if not df.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Recent Data")
            st.dataframe(df.head(15), use_container_width=True)
        
        with col2:
            st.subheader("Summary")
            st.metric("Total Records", len(df))
            st.metric("Avg Temperature", f"{df['temperature'].mean():.2f} °C")
            st.metric("Avg Humidity", f"{df['humidity'].mean():.2f} %")

        # Charts
        st.subheader("Temperature & Humidity Trend")
        fig = px.line(df, x='created_at', y=['temperature', 'humidity'], 
                     markers=True, title="Sensor Data Over Time")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No data yet. Send data from ESP8266 or add manually.")

except Exception as e:
    st.error(f"Connection Error: {e}")

st.caption(f"Refreshed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")