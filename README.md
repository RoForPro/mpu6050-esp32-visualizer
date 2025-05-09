# mpu6050-esp32-visualizer

Este proyecto está licenciado bajo CC BY-NC-SA 4.0. Más información: https://creativecommons.org/licenses/by-nc-sa/4.0/

## Versión 2.1:

Añadir elemento gráficos.


## Versión 2.0:

## ✅ Objetivo de esta versión

Validar un pipeline completo de clasificación binaria (**correcto** vs. **incorrecto**) de repeticiones usando un único sensor IMU (MPU6050), orientado a ejercicios simples (prototipo tipo "S").

---

## 🧪 Dataset utilizado

- Sensor colocado en: **muñeca derecha** realizando un curl de bíceps donde cada repetición dura 4" (correcto-completo, incorrecto-medio rango)
- N.º de repeticiones: **20 correctas** + **20 incorrectas**.
- Etiquetado en tiempo real mediante teclado.
- Datos registrados: `timestamp, yaw, pitch, roll, etiqueta`
- Formato CSV: una fila por muestra, agrupadas por `rep_id`

---

## 🧠 Características extraídas por repetición

Para cada repetición, el sistema agrupa todas las muestras y calcula las siguientes **23 características** (features) que resumen la ejecución:

### 📊 Estadísticas básicas (por eje: yaw, pitch, roll)
- `mean`: valor medio de la señal
- `std`: desviación estándar (variabilidad)
- `range`: diferencia entre el valor máximo y mínimo

### ⏱️ Dinámicas (por eje)
- `velocity_mean`: velocidad angular media (`Δángulo / Δtiempo`)
- `velocity_max`: velocidad angular máxima (pico de velocidad)
- `num_peaks`: número de picos detectados en la curva del eje (con `scipy.signal.find_peaks`)

### ⌛ Duración total de la repetición
- `duration`: duración total en segundos (`t_final − t_inicial`)

### 🔗 Correlación entre ejes
- `corr_yaw_pitch`
- `corr_yaw_roll`
- `corr_pitch_roll`

### ⚡ Energía total
- `energy_total`: suma de la energía (cuadrado RMS) de yaw, pitch y roll

---

## 🤖 Modelos comparados

Se entrenan y comparan **3 clasificadores** con `scikit-learn`:

1. **SVM (Support Vector Machine)** – lineal  
   - Encuentra un plano óptimo que separa las clases.
   - Robusto con pocas muestras y alto número de características.

2. **Árbol de decisión**  
   - Clasifica haciendo preguntas como “¿roll_range > 35?”
   - Muy interpretable, útil para entender reglas.

3. **KNN (k=5)**  
   - Clasifica en función de los 5 vecinos más cercanos.
   - Requiere más muestras para rendir bien.

---

## 📉 Métricas utilizadas

Tras dividir el dataset en entrenamiento y test (70/30), se calcula:

- **Accuracy**: % de aciertos globales.
- **Precision**: de todas las veces que el modelo predijo una clase, ¿cuántas eran correctas?
- **Recall**: de todas las veces que una clase era real, ¿cuántas fueron detectadas?
- **F1-score**: promedio balanceado entre precisión y recall.
- **support**: número real de muestras de cada clase en el conjunto de test.

### 📌 Matriz de confusión

Cada modelo genera una matriz 2x2:

|                      | Predicho: Incorrecto | Predicho: Correcto   |
|----------------------|----------------------|----------------------|
| **Real: Incorrecto** | Verdaderos negativos | Falsos negativos     |
| **Real: Correcto**   | Falsos positivos     | Verdaderos positivos |

---

## 🧠 Interpretación de resultados

- Un buen clasificador tendrá la **diagonal principal con valores altos** (aciertos) y ceros fuera de ella.
- El análisis conjunto de **accuracy + matriz de confusión** + **F1-score por clase** permite entender si el modelo está sesgado (p. ej. solo acierta una clase) o equilibrado.

---


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

| Pin MPU6050       | Función                                    | Conexión en ESP32                                                      |
|-------------------|--------------------------------------------|------------------------------------------------------------------------|
| **VCC**           | Alimentación                               | 3.3V del ESP32                                                         |
| **GND**           | Tierra                                     | GND del ESP32                                                          |
| **SCL**           | Clock de I2C                               | GPIO 22 (SCL del ESP32)                                                |
| **SDA**           | Datos de I2C                               | GPIO 21 (SDA del ESP32)                                                |
| **INT**           | Interrupción por interrupciones de datos   | GPIO 25 (INT del ESP32)                                                |
| **XDA**           | Datos I2C para magnetómetro (no usado)     | No conectado                                                           |
| **XCL**           | Clock I2C para magnetómetro (no usado)     | No conectado                                                           |
| **AD0** o **ADO** | Dirección I2C: LOW = `0x68`, HIGH = `0x69` | GND (recomendado usar `0x68` con lo que puede permanecer no conectado) |

> ⚠️ Si usas más de un MPU6050 en el mismo bus I2C, puedes conectar AD0 a 3.3 V en uno de ellos para usar `0x69` como dirección secundaria.
