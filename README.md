# mpu6050-esp32-visualizer

Este proyecto está licenciado bajo CC BY-NC-SA 4.0. Más información: https://creativecommons.org/licenses/by-nc-sa/4.0/


## Versión 2.0:


## Versión 1.1: Pruebas repositorio

## Versión 1.0: Primera versión estable con visualización en tiempo real
# PIPELINE DE CAPTURA Y CLASIFICACIÓN – FASE 0

## 🎯 Objetivo de la fase
Validar el flujo completo del sistema con un único sensor, un ejercicio ficticio, y etiquetas simples de “correcto” / “incorrecto”. Esto permitirá tener una primera IA funcional y testear el ciclo completo de captura, visualización, segmentación, entrenamiento y evaluación.

---

## 1. Captura
- **Sensor**: MPU6050 conectado a ESP32 (I2C)
- **Frecuencia de muestreo esperada**: ~100-200 Hz (según el código del ESP32)
- **Datos enviados**: `timestamp, yaw, pitch, roll`
- **Formato CSV de guardado**:  
  `rep_id, timestamp, yaw, pitch, roll, etiqueta`
- **Etiquetas posibles**: `correcto`, `incorrecto`

---

## 2. Preprocesamiento
- Agrupación por repetición (`rep_id`)
- Normalización del tiempo (inicio de repetición = 0)
- Posibilidad de descartar outliers en un futuro
- Separación en `train` y `test`

---

## 3. Segmentación
- Segmentación manual mediante teclado:
  - `q` para iniciar repetición correcta
  - `w` para finalizar repetición correcta
  - `e` para iniciar repetición incorrecta
  - `r` para finalizar repetición incorrecta
- Se registra cada repetición completa con un `rep_id`

---

## 4. Etiquetado
- En tiempo real mediante teclado
- 📷 Posible validación posterior mediante vídeo (sincronización manual por ahora)
- Se evalúa visualmente cada repetición con Matplotlib para asegurar la coherencia

---

## 5. Extracción de características
Por cada repetición se calculan:
- **yaw / pitch / roll**:
  - Media
  - Desviación estándar
  - Rango

🔜 Ampliaciones previstas:
- Duración (tiempo total)
- Velocidad media
- Aceleración angular estimada
- Número de picos
- Energía de la señal

---

## 6. Entrenamiento
- Librería: `scikit-learn`
- Modelos probados:
  - SVM (Support Vector Machine) con kernel lineal
- Métricas utilizadas:
  - Accuracy (exactitud global)
  - Precision, Recall, F1-score por clase
  - Matriz de confusión

🔜 Próximos modelos:
- Árboles de decisión (interpretable)
- Random Forest
- KNN
- Regresión logística
- Deep Learning (Keras) cuando haya más datos

---

## 7. Evaluación
- División 70/30 entre train/test
- Visualización de matriz de confusión
- Análisis de errores
- Validación cruzada en el futuro

--
# Conexión del MPU6050 al ESP32

El sensor MPU6050 se comunica mediante el protocolo I2C. Además, se puede utilizar un pin de interrupción para notificaciones como disponibilidad de nuevos datos.

### Sketch del MPU6050

Se puede encontrar en ./sketch/MPU6050_DMP_YPR_logger/MPU6050_DMP_YPR_logger.ino

### 🧠 Pines del MPU6050

| Pin MPU6050 | Función                       | Conexión en ESP32                                                      |
|-------------|-------------------------------|------------------------------------------------------------------------|
| **VCC**     | Alimentación                  | 3.3V del ESP32                                                         |
| **GND**     | Tierra                        | GND del ESP32                                                          |
| **SCL**     | Clock de I2C                  | GPIO 22 (SCL del ESP32)                                                |
| **SDA**     | Datos de I2C                  | GPIO 21 (SDA del ESP32)                                                |
| **INT**     | Interrupción por interrupciones de datos  | GPIO 25 (INT del ESP32)                                                 |
| **XDA**     | Datos I2C para magnetómetro (no usado)     | No conectado                                                           |
| **XCL**     | Clock I2C para magnetómetro (no usado)     | No conectado                                                           |
| **AD0** o **ADO** | Dirección I2C: LOW = `0x68`, HIGH = `0x69` | GND (recomendado usar `0x68` con lo que puede permanecer no conectado) |

> ⚠️ Si usas más de un MPU6050 en el mismo bus I2C, puedes conectar AD0 a 3.3V en uno de ellos para usar `0x69` como dirección secundaria.
