#include <WiFi.h>
#include <HTTPClient.h>

// ------------------------------------------------------------
const char* ssid = "Your wifi name";
const char* password = "your wifi password";
// ------------------------------------------------------------

const char* serverName = "http://<your network ip>:5000/receive_data"; 
const int airQ = 34;

float VREF = 3.3;
int ADC_RES = 4095;

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
  float gasConcentration = voltage * 1000;
  int aqi = calculateAQI(gasConcentration);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{\"aqi\": " + String(aqi) + ", \"temperature\": null, \"humidity\": null}";
    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.printf("POST Response: %d\n", httpResponseCode);
    } else {
      Serial.printf("POST failed: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
  }

  delay(1000); 
}

int calculateAQI(float concentration) {
  if (concentration <= 400)
    return map(concentration, 0, 400, 0, 50);
  else if (concentration <= 1000)
    return map(concentration, 400, 1000, 51, 100);
  else if (concentration <= 2000)
    return map(concentration, 1000, 2000, 101, 150);
  else if (concentration <= 5000)
    return map(concentration, 2000, 5000, 151, 200);
  else
    return 300;
}
