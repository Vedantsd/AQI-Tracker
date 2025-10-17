from flask import Flask, jsonify, render_template, request
import time
import threading
import requests
import smtplib
import os
import mimetypes
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
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "city": None
}

def send_otp_email(receiver):
    """Send OTP via email"""
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = "HIGH AQI Warning"

    body = f"""
    The AQI is too high today, you may burn, go back home!!!
    """
    
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False, str(e)
    

def send_bulk_email():
    with open("emails.csv") as csv_file:
        data = csv_file.read()
        emails = data.split(',')
        for email in emails: 
            email.replace('\n', '')
            email.replace(',', '')
            send_otp_email(email)


def fetch_location_data():
    apis = [
        {
            'url': 'https://ipinfo.io/json',
            'city_key': 'city',
            'country_key': 'country',
            'lat_key': None  
        },
    ]
        
    for api in apis:
        try:
            print(f"Trying API: {api['url']}")
            response = requests.get(api['url'], timeout=10)
                
            if response.status_code == 200:
                data = response.json()
                print(f"API Response: {data}")
                    
                city = data.get(api['city_key'], 'Unknown')
                country = data.get(api['country_key'], 'Unknown')
                st = f"{city}, {country}"
                return st
        except:
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
        temp = data.get("temperature")
        hum = data.get("humidity")

        if aqi is None:
            return jsonify({"status": "error", "message": "Missing 'aqi' in request"}), 400

        latest_sensor_data.update({
            "aqi": aqi,
            "temperature": temp,
            "humidity": hum,
            "timestamp": time.time(),
            "city": city
        })

        print(f"Received from ESP32 -> AQI: {aqi}, Temp: {temp}, Humidity: {hum}")

        return jsonify({"status": "success", "message": "Data received"}), 200

    except Exception as e:
        print(f"Error receiving data: {e}")
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
