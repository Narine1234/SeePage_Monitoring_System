#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

const char* ssid = "Your_Wifi";
const char* password = "Your Password";
const char* serverUrl = "http://your_Wifi's_IP:5000/update";

const int currentSensorPin = A0;
const int voltageSensorPin = A0 + 1;
const float currentSensitivity = 0.185;
const float overflowVoltage = 3.96;

const int numReadings = 10;
float currentReadings[numReadings];
int readIndex = 0;
float total = 0;
float averageCurrent = 0;

WiFiClient client;

void setup() {
  Serial.begin(9600);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");

  for (int i = 0; i < numReadings; i++) {
    currentReadings[i] = 0;
  }
}

void loop() {
  int currentSensorValue = analogRead(currentSensorPin); 
  float currentVoltage = currentSensorValue * (5.0 / 1023.0); 
  float current = (currentVoltage - 2.5) / currentSensitivity; 

  total -= currentReadings[readIndex];
  currentReadings[readIndex] = current;
  total += current;
  readIndex = (readIndex + 1) % numReadings;
  
  averageCurrent = total / numReadings;

  if (abs(averageCurrent) < 0.02) {
    averageCurrent = 0;
  }

  float voltageSensorValue = analogRead(voltageSensorPin); 
  float sensorVoltage = voltageSensorValue * (5.0 / 1023.0);  
  float meter = (-25.51 * sensorVoltage) + 100.20;

  Serial.print("Current: ");
  Serial.print(averageCurrent);
  Serial.println(" A");

  if (sensorVoltage > overflowVoltage) {
    Serial.println("Overflow");
    Serial.print(voltageSensorValue);
  } else {
    Serial.print("Meter: ");
    Serial.print(meter);
    Serial.println(" m");
  }

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(serverUrl) + "?current=" + String(averageCurrent) + "&meter=" + String(meter);
    http.begin(client, url);
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
      Serial.println(http.errorToString(httpResponseCode));
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }

  delay(1000);
}
