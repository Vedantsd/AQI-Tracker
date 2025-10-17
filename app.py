from flask import Flask, jsonify, render_template, request
import time
import threading

app = Flask(__name__)

# In-memory storage for the latest sensor data
latest_sensor_data = {
    "aqi": None,
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "city": None
}


def get_user_city_from_ip():
    """Optional: Keep IP lookup for user display."""
    try:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if not client_ip or client_ip.startswith(('127.', '192.168.', '172.', '10.', '::1')):
            return "Local Network"
        return client_ip
    except Exception:
        return "Unknown"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/receive_data', methods=['POST'])
def receive_data():
    """Receive air quality sensor data from ESP32."""
    global latest_sensor_data

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        # Extract expected fields
        aqi = data.get("aqi")
        temp = data.get("temperature")
        hum = data.get("humidity")

        # Validate required data
        if aqi is None:
            return jsonify({"status": "error", "message": "Missing 'aqi' in request"}), 400

        latest_sensor_data.update({
            "aqi": aqi,
            "temperature": temp,
            "humidity": hum,
            "timestamp": time.time(),
            "city": get_user_city_from_ip()
        })

        print(f"Received from ESP32 -> AQI: {aqi}, Temp: {temp}, Humidity: {hum}")

        return jsonify({"status": "success", "message": "Data received"}), 200

    except Exception as e:
        print(f"Error receiving data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/airquality', methods=['GET'])
def air_quality_api():
    """Return the latest real sensor data."""
    if latest_sensor_data["aqi"] is None:
        return jsonify({"status": "error", "message": "No sensor data received yet"}), 404

    return jsonify({
        "status": "success",
        "data": latest_sensor_data
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
