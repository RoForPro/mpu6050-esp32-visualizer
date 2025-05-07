import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Cargar CSV
csv_filename = "datos_ejercicio.csv"
df = pd.read_csv(csv_filename)
rep_ids = sorted(int(r) for r in df["rep_id"].unique())
print("Rep_ids en el CSV:", rep_ids)
print("Total de filas en CSV:", len(df))

# 2. Extracción de características
def extract_features(group):
    feat = {}
    t = (group["timestamp"].values - group["timestamp"].values[0]) / 1000.0
    feat["duration"] = t[-1] - t[0]
    for axis in ["yaw", "pitch", "roll"]:
        x = group[axis].values
        # Estadísticas básicas
        feat[f"{axis}_mean"]  = x.mean()
        feat[f"{axis}_std"]   = x.std()
        feat[f"{axis}_range"] = x.max() - x.min()
        # Dinámicas: velocidad
        dx = np.diff(x); dt = np.diff(t)
        vel = np.abs(dx/dt)
        feat[f"{axis}_vel_mean"] = vel.mean()
        feat[f"{axis}_vel_max"]  = vel.max()
        # Picos
        feat[f"{axis}_num_peaks"] = len(find_peaks(x)[0])
    # Correlaciones
    feat["corr_yaw_pitch"]  = np.corrcoef(group["yaw"],   group["pitch"])[0,1]
    feat["corr_yaw_roll"]   = np.corrcoef(group["yaw"],   group["roll"])[0,1]
    feat["corr_pitch_roll"] = np.corrcoef(group["pitch"], group["roll"])[0,1]
    # Energía total
    feat["energy_total"] = (group["yaw"]**2).mean() + (group["pitch"]**2).mean() + (group["roll"]**2).mean()
    return feat

features_list, labels = [], []
for rep_id, group in df.groupby("rep_id"):
    features_list.append(extract_features(group))
    labels.append(group["etiqueta"].iloc[0])

X = pd.DataFrame(features_list)
y = pd.Series(labels).map({"correcto":1, "incorrecto":0})

# Mostrar todas las columnas
pd.set_option('display.max_columns', None)
print(f"\nRepeticiones extraídas: {X.shape[0]}")
print("Características (primeras filas):")
print(X.head())

# 3. Split y escalado
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
scaler = StandardScaler().fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s  = scaler.transform(X_test)

# 4. Clasificadores
classifiers = {
    "SVM (lineal)":      SVC(kernel="linear", random_state=42),
    "Árbol de decisión": DecisionTreeClassifier(random_state=42),
    "KNN":               KNeighborsClassifier(n_neighbors=min(5, len(X_train)))
}

results = {}
for name, clf in classifiers.items():
    # 4a. Entrenamiento / test
    clf.fit(X_train_s, y_train)
    y_pred = clf.predict(X_test_s)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n{name} — Exactitud en test: {acc:.2f}")
    print(classification_report(y_test, y_pred, target_names=["incor","cor"], zero_division=0))

    # 4b. Validación cruzada
    # determinar cv = min(5, nº mínimo de muestras por clase)
    min_count = y.value_counts().min()
    cv = min(5, min_count) if min_count >= 2 else 2
    pipeline = Pipeline([('scl', StandardScaler()), ('clf', clf)])
    scores = cross_val_score(pipeline, X, y, cv=StratifiedKFold(n_splits=cv), scoring='accuracy')
    print(f"Validación cruzada ({cv}-fold): accuracy media {scores.mean():.2f} ± {scores.std():.2f}")

    # guardar resultados para la matriz
    cm = confusion_matrix(y_test, y_pred)
    results[name] = (acc, cm)

# 5. Mostrar matrices de confusión
fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 4))
for ax, (name, (_, cm)) in zip(axes, results.items()):
    sns.heatmap(cm, annot=True, fmt="d", ax=ax,
                xticklabels=["incor","cor"], yticklabels=["incor","cor"],
                cmap="Blues")
    ax.set_title(name)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Real")
plt.tight_layout()
plt.show()

# 6. Gráfico scatter interactivo
print("\n--- Gráfico de dispersión de dos características ---")
features = list(X.columns)
for i, f in enumerate(features):
    print(f"{i:2d}: {f}")
print("\nPulsa Enter para usar valores por defecto: 'duration' vs 'yaw_range'.")
ix = input("Índice de característica para el eje X: ")
iy = input("Índice de característica para el eje Y: ")
try:
    ix = int(ix) if ix.strip() else features.index("duration")
    iy = int(iy) if iy.strip() else features.index("yaw_range")
    feat_x, feat_y = features[ix], features[iy]
except:
    print("Índices inválidos, usando 'duration' vs 'yaw_range'.")
    feat_x, feat_y = "duration", "yaw_range"

plt.figure(figsize=(6,5))
colors = y.map({0:'red', 1:'green'})
plt.scatter(X[feat_x], X[feat_y], c=colors)
plt.xlabel(feat_x)
plt.ylabel(feat_y)
plt.title(f"Scatter: {feat_x} vs {feat_y}")
# leyenda
for val, col, label in [(1,'green','correcto'), (0,'red','incorrecto')]:
    plt.scatter([], [], c=col, label=label)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
