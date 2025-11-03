from flask import Flask, jsonify, render_template, request
import time
import threading
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

city = "Unknown"
sender = os.getenv("email")
password = os.getenv("password")

latest_sensor_data = {
    "aqi": None,
    "co2": None,
    "smoke": None,
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "city": None
}

def send_otp_email(receiver):
    """Send AQI warning email"""
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = "⚠️ HIGH AQI Warning"

    body = """
    The AQI is too high today! Please stay indoors and avoid outdoor activities.
    """

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        print(f"✅ Email sent to {receiver}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def send_bulk_email():
    try:
        with open("emails.csv") as csv_file:
            data = csv_file.read()
            emails = data.split(',')
            for email in emails:
                email = email.strip()
                if email:
                    send_otp_email(email)
    except FileNotFoundError:
        print("⚠️ emails.csv not found. Skipping email notifications.")


def fetch_location_data():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=10)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', 'Unknown')
            country = data.get('country', 'Unknown')
            return f"{city}, {country}"
    except Exception as e:
        print(f"⚠️ Location fetch failed: {e}")
    return "Unknown"





@app.route('/')
def index():
    return render_template('index.html')

@app.route('/receive_data', methods=['POST'])
def receive_data():
    global latest_sensor_data

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        aqi = data.get("aqi")
        co2 = data.get("co2")
        smoke = data.get("smoke")
        temp = data.get("temperature")
        hum = data.get("humidity")

        if aqi is None:
            return jsonify({"status": "error", "message": "Missing 'aqi' in request"}), 400

        latest_sensor_data.update({
            "aqi": aqi,
            "co2": co2,
            "smoke": smoke,
            "temperature": temp,
            "humidity": hum,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "city": city
        })

        print(f"📡 Received -> AQI: {aqi}, CO2: {co2} ppm, Smoke: {smoke}, Temp: {temp}, Hum: {hum}")

        if aqi and aqi > 150:
            threading.Thread(target=send_bulk_email).start()

        return jsonify({"status": "success", "message": "Data received"}), 200

    except Exception as e:
        print(f"❌ Error receiving data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/airquality', methods=['GET'])
def air_quality_api():
    if latest_sensor_data["aqi"] is None:
        return jsonify({"status": "error", "message": "No sensor data received yet"}), 404

    return jsonify({
        "status": "success",
        "data": latest_sensor_data
    })

if __name__ == '__main__':
    city = fetch_location_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
    