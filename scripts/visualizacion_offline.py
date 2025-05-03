import pandas as pd
import matplotlib.pyplot as plt

# Cargar el CSV con los datos de repetición
csv_filename = "datos_ejercicio.csv"
df = pd.read_csv(csv_filename)

# Verifica que el CSV tiene las columnas esperadas
expected_columns = {"rep_id", "timestamp", "yaw", "pitch", "roll", "etiqueta"}
if not expected_columns.issubset(df.columns):
    raise ValueError(f"El CSV no contiene las columnas esperadas: {expected_columns}")

# Agrupar los datos por repetición
grouped = df.groupby("rep_id")

# Recorrer cada grupo (cada repetición) para graficar los datos
for rep_id, group in grouped:
    etiqueta = group["etiqueta"].iloc[0]  # Asumimos que todas las filas de la repetición tienen la misma etiqueta

    # Opcional: normalizar el tiempo, haciendo que el inicio sea 0
    tiempo = group["timestamp"] - group["timestamp"].iloc[0]

    plt.figure(figsize=(10, 5))
    plt.plot(tiempo, group["yaw"], label="Yaw", marker="o")
    plt.plot(tiempo, group["pitch"], label="Pitch", marker="o")
    plt.plot(tiempo, group["roll"], label="Roll", marker="o")
    plt.title(f"Repetición {rep_id} - {etiqueta.capitalize()}")
    plt.xlabel("Tiempo (s) (normalizado)")
    plt.ylabel("Valor")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()  # Muestra el gráfico e interrumpe la ejecución hasta cerrarlo
