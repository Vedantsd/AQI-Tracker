#include <WiFi.h>
#include <HTTPClient.h>
#include <math.h>

// ------------------------------------------------------------
const char* ssid = "OPPO F17";
const char* password = "12345678";
// ------------------------------------------------------------

const char* serverName = "http://10.236.15.197:5000/receive_data"; 
const int airQ = 34;

float VREF = 3.3;
int ADC_RES = 4095;

float RLOAD = 10.0;
float RZERO = 10.0;  // Will be updated after 

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  int rawValue = analogRead(airQ);
  float voltage = (rawValue * VREF) / ADC_RES;

  // Calculate sensor resistance RS
  float RS = ((VREF * RLOAD) / voltage) - RLOAD;
  float ratio = RS / RZERO;

  float gasConcentration = voltage * 1000;
  int aqi = calculateAQI(gasConcentration);

  // Estimate gas concentrations
  float co2ppm = getCO2PPM(ratio);
  float smokeLevel = getSmokeIndex(voltage);

  Serial.print("Raw: "); Serial.print(rawValue);
  Serial.print(" | Voltage: "); Serial.print(voltage);
  Serial.print("V | CO2: "); Serial.print(co2ppm);
  Serial.print(" ppm | Smoke: "); Serial.print(smokeLevel);
  Serial.print(" | AQI: "); Serial.println(aqi);

  // Send to Flask server
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{\"aqi\": " + String(aqi) +
                      ", \"co2\": " + String(co2ppm) +
                      ", \"smoke\": " + String(smokeLevel) +
                      ", \"temperature\": null, \"humidity\": null}";

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.printf("POST Response: %d\n", httpResponseCode);
    } else {
      Serial.printf("POST failed: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
  }

  delay(2000); 
}

// ----------------------------
// Estimate CO2 concentration (ppm)
float getCO2PPM(float ratio) {
  // Empirical formula for MQ135 CO₂
  // log(ppm) = a * log(RS/R0) + b
  // Derived constants from datasheet curve
  float a = -2.769034857;
  float b = 2.066;
  float ppm = 116.6020682 * pow(ratio, a);
  return ppm;
}

// ----------------------------
// Estimate smoke level (0–100 scale)
float getSmokeIndex(float voltage) {
  // Convert voltage to a relative smoke index (arbitrary scale)
  // Higher voltage = more smoke
  float index = (voltage / VREF) * 100.0;
  if (index > 100) index = 100;
  return index;
}

// ----------------------------
// Estimate simple AQI from CO₂
int calculateAQI(float co2ppm) {
  if (co2ppm <= 400)
    return map(co2ppm, 0, 400, 0, 50);
  else if (co2ppm <= 1000)
    return map(co2ppm, 400, 1000, 51, 100);
  else if (co2ppm <= 2000)
    return map(co2ppm, 1000, 2000, 101, 150);
  else if (co2ppm <= 5000)
    return map(co2ppm, 2000, 5000, 151, 200);
  else
    return 300;
}
