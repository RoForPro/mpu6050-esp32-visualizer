import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns


def extract_features(df):
    """
    Extrae características simples (media, desviación estándar y rango) para cada eje: yaw, pitch y roll,
    a partir de los datos de una repetición (DataFrame con datos de la repetición).
    Devuelve un diccionario con las características extraídas.
    """
    features = {}
    for axis in ["yaw", "pitch", "roll"]:
        features[f'{axis}_mean'] = df[axis].mean()
        features[f'{axis}_std'] = df[axis].std()
        features[f'{axis}_range'] = df[axis].max() - df[axis].min()
    return features


def main():
    # Cargar el CSV de datos etiquetados
    csv_filename = "datos_ejercicio.csv"
    df = pd.read_csv(csv_filename)

    # Validar columnas esperadas
    expected_columns = {"rep_id", "timestamp", "yaw", "pitch", "roll", "etiqueta"}
    if not expected_columns.issubset(df.columns):
        raise ValueError(f"El CSV no contiene las columnas esperadas: {expected_columns}")

    # Agrupar los datos por repetición y extraer características para cada una
    feature_list = []
    labels = []
    grouped = df.groupby("rep_id")
    for rep_id, group in grouped:
        features = extract_features(group)
        feature_list.append(features)
        # Se asume que todas las filas de una repetición tienen la misma etiqueta
        labels.append(group["etiqueta"].iloc[0])

    # Convertir a DataFrame para las características
    features_df = pd.DataFrame(feature_list)
    print("Características extraídas:")
    print(features_df.head())

    # Codificar la etiqueta: asignamos 1 a "correcto" y 0 a "incorrecto"
    mapping = {"correcto": 1, "incorrecto": 0}
    y = np.array([mapping[label] for label in labels])
    X = features_df.values

    # Dividir en conjunto de entrenamiento y test (por ejemplo, 70% entrenamiento, 30% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Estandarizar las características
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Entrenar un clasificador SVM
    clf = SVC(kernel="linear", random_state=42)
    clf.fit(X_train_scaled, y_train)
    y_pred = clf.predict(X_test_scaled)

    # Evaluar el modelo
    acc = accuracy_score(y_test, y_pred)
    print(f"\nExactitud: {acc:.2f}")
    print("\nInforme de clasificación:")
    print(classification_report(y_test, y_pred, target_names=["incorrecto", "correcto"]))

    # Matriz de confusión
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["incorrecto", "correcto"],
                yticklabels=["incorrecto", "correcto"])
    plt.xlabel("Predicción")
    plt.ylabel("Valor real")
    plt.title("Matriz de confusión")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
