# scripts/training.py

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from joblib import dump
from scripts.features import extract_from_list


def train_model(csv_path: str, model_out: str):
    # Carga CSV etiquetado
    df = pd.read_csv(csv_path)
    # Extrae rep_id, etiqueta y muestras
    features, labels = [], []
    for rid, g in df.groupby("rep_id"):
        features.append(extract_from_list(g[["timestamp", "yaw", "pitch", "roll"]].values.tolist()))
        labels.append(g["etiqueta"].iloc[0])
    X = pd.DataFrame(features)
    y = pd.Series(labels).map({"Correcto": 1, "Incorrecto": 0})

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y)

    models = {
        "SVM": SVC(kernel="linear", probability=True),
        "Tree": DecisionTreeClassifier(),
        "KNN": KNeighborsClassifier(n_neighbors=min(5, len(X_train)))
    }
    best_acc, best_name, best_pipe = 0, None, None
    for name, clf in models.items():
        pipe = Pipeline([("scl", StandardScaler()), ("clf", clf)])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"{name} test acc: {acc:.2f}")
        print(classification_report(y_test, y_pred, target_names=["Inc", "Cor"]))
        print("Conf matrix:\n", confusion_matrix(y_test, y_pred))
        # CV
        cv = min(5, y.value_counts().min())
        scores = cross_val_score(pipe, X, y, cv=StratifiedKFold(cv), scoring='accuracy')
        print(f"CV {cv}-fold: {scores.mean():.2f}±{scores.std():.2f}\n")
        if acc > best_acc:
            best_acc, best_name, best_pipe = acc, name, pipe

    print(f"Best: {best_name} ({best_acc:.2f}), saving to {model_out}")
    dump(best_pipe, model_out)
