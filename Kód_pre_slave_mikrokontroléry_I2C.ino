#include <Wire.h>
#include <DHT.h>

#define SLAVE_ADDRESS 1
#define NUM_SENSORS 5
#define DHTTYPE DHT22

const int sensorPins[NUM_SENSORS] = {2, 3, 4, 5, 6};
DHT sensors[NUM_SENSORS] = {
  DHT(sensorPins[0], DHTTYPE),
  DHT(sensorPins[1], DHTTYPE),
  DHT(sensorPins[2], DHTTYPE),
  DHT(sensorPins[3], DHTTYPE),
  DHT(sensorPins[4], DHTTYPE)
};

int temperatureInts[NUM_SENSORS];  // Pole na uloženie teplôt vo formáte int
int humidityInts[NUM_SENSORS];     // Pole na uloženie vlhkosti vo formáte int

void setup() {
  Wire.begin(SLAVE_ADDRESS);  // Nastavenie adresy Slave
  Wire.onRequest(sendData);   // Nastavenie funkcie na spracovanie požiadavky od Mastera

  for (int i = 0; i < NUM_SENSORS; i++) {
    sensors[i].begin();  // Inicializácia senzorov
  }
}

void loop() {
  readSensors();  // Čítanie údajov zo senzorov
  delay(2000);    // Oneskorenie na stabilitu
}

void readSensors() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    float temp = sensors[i].readTemperature();  // Odčítanie teploty
    float hum = sensors[i].readHumidity();     // Odčítanie vlhkosti

    temperatureInts[i] = (int)(temp * 100);  
    humidityInts[i] = (int)(hum * 100);      
  }
}

void sendData() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    float temp = sensors[i].readTemperature();  
    float hum = sensors[i].readHumidity();     

    
    if (isnan(temp) || isnan(hum)) {
      // Ak je hodnota NaN, pošlite špeciálny kód chyby
      int errorCode = -999;  // Код помилки
      Wire.write((byte*)&errorCode, 2);  
      Wire.write((byte*)&errorCode, 2);  
    } else {
      // Якщо значення коректне, відправляємо їх
      temperatureInts[i] = (int)(temp * 100);  
      humidityInts[i] = (int)(hum * 100);      

      Wire.write((byte*)&temperatureInts[i], 2);  
      Wire.write((byte*)&humidityInts[i], 2);     
    }
  }
}

