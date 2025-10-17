from flask import Flask, jsonify, render_template, request 
import random
import time
import requests 

app = Flask(__name__)

def get_user_city_from_ip():
    try:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if client_ip in ['127.0.0.1', '::1'] or client_ip.startswith('192.168.') or client_ip.startswith('172.'):
             lookup_ip = ''
        else:
             lookup_ip = client_ip.split(',')[0].strip() 

        api_url = f"http://ip-api.com/json/{lookup_ip}"
        response = requests.get(api_url, timeout=3)
        response.raise_for_status() 
        
        data = response.json()
        
        if data.get('status') == 'success':
            city_name = data.get('city')
            region = data.get('regionName')
            
            if city_name and region:
                 return f"{city_name}, {region}"
            elif region:
                 return region
            else:
                 return "Unknown Location (IP Found)"
        
    except requests.exceptions.RequestException as e:
        print(f"GeoIP API failed (will use fallback): {e}")
    except Exception as e:
        print(f"An unexpected error occurred during GeoIP lookup: {e}")
        
    return "Fallback Location (IP Lookup Failed)" 


def get_air_quality_data(user_city):
    current_hour = time.localtime().tm_hour    
    base_aqi = random.randint(30, 90)
    if current_hour % 5 == 0 or random.random() < 0.2:
        aqi_value = random.randint(151, 250)
    else:
        aqi_value = base_aqi + random.randint(0, 50)
    
    aqi_value = min(aqi_value, 400)

    return {
        "aqi": aqi_value,
        "timestamp": time.time(),
        "city": user_city 
    }


# ------------ Flask Routes ------------- 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/airquality', methods=['GET'])
def air_quality_api():
    user_city = get_user_city_from_ip()    
    data = get_air_quality_data(user_city)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)