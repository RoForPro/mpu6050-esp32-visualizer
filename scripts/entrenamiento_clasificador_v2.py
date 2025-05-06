import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Cargar CSV
csv_filename = "datos_ejercicio.csv"
df = pd.read_csv(csv_filename)
# Comprobar cuántas repeticiones tiene el CSV
rep_ids = [int(r) for r in df["rep_id"].unique()]
print("Rep_ids en el CSV:", sorted(rep_ids))
print("Total de filas en CSV:", len(df))

# 2. Función de extracción de características
def extract_features(group):
    feat = {}
    # Tiempos y ángulos
    t = group["timestamp"].values
    # Normalizar tiempo a segundos (si timestamp en ms, divide por 1000)
    t = (t - t[0]) / 1000.0
    duration = t[-1] - t[0]
    feat["duration"] = duration

    # Para cada eje
    for axis in ["yaw", "pitch", "roll"]:
        x = group[axis].values

        # Estadísticas básicas
        feat[f"{axis}_mean"] = x.mean()
        feat[f"{axis}_std"] = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()

        # Dinámicas: velocidad (derivada)
        # Vel = Δx / Δt
        dx = np.diff(x)
        dt = np.diff(t)
        vel = dx / dt
        vel_abs = np.abs(vel)
        feat[f"{axis}_vel_mean"] = vel_abs.mean()
        feat[f"{axis}_vel_max"] = vel_abs.max()

        # Número de picos en la señal del eje
        peaks, _ = find_peaks(x)
        feat[f"{axis}_num_peaks"] = len(peaks)

    # Multieje: correlaciones
    feat["corr_yaw_pitch"] = np.corrcoef(group["yaw"], group["pitch"])[0, 1]
    feat["corr_yaw_roll"] = np.corrcoef(group["yaw"], group["roll"])[0, 1]
    feat["corr_pitch_roll"] = np.corrcoef(group["pitch"], group["roll"])[0, 1]

    # Energía total: sum(RMS^2) de cada eje
    energy = (group["yaw"] ** 2).mean() + (group["pitch"] ** 2).mean() + (group["roll"] ** 2).mean()
    feat["energy_total"] = energy

    return feat


# 3. Construir matriz de características y vector de etiquetas
features_list = []
labels = []
for rep_id, group in df.groupby("rep_id"):
    features_list.append(extract_features(group))
    labels.append(group["etiqueta"].iloc[0])

X = pd.DataFrame(features_list)
# Repeticiones extraídas del .csv
print("Repeticiones extraídas (filas de X):", X.shape[0])
y = pd.Series(labels).map({"correcto": 1, "incorrecto": 0})

print("Características extraídas (primeras filas):")
pd.set_option('display.max_columns', None)  # Se mostrarán todas las columnas
print(X.head())

# 4. División train/test y escalado
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
scaler = StandardScaler().fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)

# 5. Definir clasificadores
classifiers = {
    "SVM (lineal)": SVC(kernel="linear", random_state=42),
    "Árbol de decisión": DecisionTreeClassifier(random_state=42),
    "KNN": KNeighborsClassifier(n_neighbors=min(5, len(X_train)))  # Inicialización directa
}

results = {}

for name, clf in classifiers.items():
    clf.fit(X_train_s, y_train)
    y_pred = clf.predict(X_test_s)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, target_names=["incor", "cor"], zero_division=np.nan)
    cm = confusion_matrix(y_test, y_pred)
    results[name] = (acc, report, cm)
    print(f"\n{name} — Exactitud: {acc:.2f}")
    print(classification_report(y_test, y_pred, target_names=["incor", "cor"], zero_division=np.nan))

# 6. Mostrar matrices de confusión
fig, axes = plt.subplots(1, len(classifiers), figsize=(5 * len(classifiers), 4))
for ax, (name, (_, _, cm)) in zip(axes, results.items()):
    sns.heatmap(cm, annot=True, fmt="d", ax=ax,
                xticklabels=["incor", "cor"], yticklabels=["incor", "cor"],
                cmap="Blues")
    ax.set_title(name)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Real")
plt.tight_layout()
plt.show()