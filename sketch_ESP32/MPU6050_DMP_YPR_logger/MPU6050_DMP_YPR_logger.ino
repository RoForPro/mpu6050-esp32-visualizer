#include "Wire.h"
#include "MPU6050_6Axis_MotionApps20.h"

MPU6050 mpu;

#define INTERRUPT_PIN 25
volatile bool mpuInterrupt = false;

uint8_t mpuIntStatus;
uint8_t devStatus;
uint16_t packetSize;
uint16_t fifoCount;
uint8_t fifoBuffer[64];

Quaternion q;
VectorFloat gravity;
float ypr[3];

void dmpDataReady() {
  mpuInterrupt = true;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);  // ESP32 SDA/SCL
  Wire.setClock(100000);  // Frecuencia I2C segura

  mpu.initialize();
  pinMode(INTERRUPT_PIN, INPUT);

  devStatus = mpu.dmpInitialize();

  mpu.setXGyroOffset(220);
  mpu.setYGyroOffset(76);
  mpu.setZGyroOffset(-85);
  mpu.setZAccelOffset(1688);

  if (devStatus == 0) {
    mpu.setDMPEnabled(true);
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), dmpDataReady, RISING);
    mpuIntStatus = mpu.getIntStatus();
    packetSize = mpu.dmpGetFIFOPacketSize();
    Serial.println("timestamp_ms,yaw,pitch,roll");  // encabezado CSV
  } else {
    Serial.print("Error DMP: ");
    Serial.println(devStatus);
    while (1);
  }
}

void loop() {
  if (!mpuInterrupt) return;

  mpuInterrupt = false;
  mpuIntStatus = mpu.getIntStatus();
  fifoCount = mpu.getFIFOCount();

  if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
    mpu.resetFIFO();
    //Serial.println("FIFO overflow");
    return;
  }

  if (mpuIntStatus & 0x02) {
    while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();

    mpu.getFIFOBytes(fifoBuffer, packetSize);
    fifoCount -= packetSize;

    mpu.dmpGetQuaternion(&q, fifoBuffer);
    mpu.dmpGetGravity(&gravity, &q);
    mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);

    unsigned long timestamp = millis();

    Serial.print(timestamp); Serial.print(",");
    Serial.print(ypr[0] * 180.0 / PI, 2); Serial.print(",");
    Serial.print(ypr[1] * 180.0 / PI, 2); Serial.print(",");
    Serial.println(ypr[2] * 180.0 / PI, 2);
  }
}
