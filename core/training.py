# core/training.py

import os
import pandas as pd
import numpy as np
import threading
from joblib import dump
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from PyQt5.QtCore import QObject, pyqtSignal

from core.features import extract_features
import config

class TrainingController(QObject):
    """
    Controller Qt que entrena modelos en un hilo aparte,
    emite logs y notifica al acabar con las métricas.
    """
    log = pyqtSignal(str)               # mensajes de estado
    finished = pyqtSignal(dict, str)    # (results_dict, best_model_name)

    def __init__(
        self,
        csv_path: str,
        model_output_path: str,
        algorithms: dict,
        test_size: float = 0.3,
        random_state: int = 42
    ):
        super().__init__()
        self.csv_path = csv_path
        self.model_output_path = model_output_path
        self.algorithms = algorithms
        self.test_size = test_size
        self.random_state = random_state

    def start_training(self):
        """Arranca el hilo de entrenamiento."""
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        # 1) Carga de datos
        self.log.emit("⏳ Cargando datos...")
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            self.log.emit(f"✖ Error leyendo CSV: {e}")
            return

        # Renombrar si existe 'etiqueta'
        if 'etiqueta' in df.columns and 'label' not in df.columns:
            df = df.rename(columns={'etiqueta': 'label'})

        # Validación mínima
        required = {'rep_id','timestamp','yaw','pitch','roll','label'}
        if not required.issubset(df.columns):
            self.log.emit(f"✖ Faltan columnas en CSV: {required - set(df.columns)}")
            return

        # Extraer features
        feats, labels = [], []
        for rid, group in df.groupby('rep_id'):
            feats.append(extract_features(group))
            labels.append(group['label'].iloc[0])
        X = pd.DataFrame(feats)
        y = pd.Series(labels)
        n_reps, n_feat = X.shape
        self.log.emit(f"✅ Datos: {n_reps} repeticiones, {n_feat} features.")

        # 2) Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        # 3) Recorrer algoritmos
        self.log.emit("⏳ Entrenando modelos...")
        results = {}
        best_name, best_acc = None, -np.inf

        for name, estimator in self.algorithms.items():
            self.log.emit(f"• {name} …")
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("clf",  estimator)
            ])
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            acc = accuracy_score(y_test, y_pred)

            # Cross-validation (máx 5 folds o mínimos según clases)
            min_count = y.value_counts().min()
            cv = min(5, int(min_count)) if min_count >= 2 else 2
            cv_scores = cross_val_score(
                pipe, X, y,
                cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=self.random_state),
                scoring="accuracy"
            )

            cm = confusion_matrix(y_test, y_pred)
            cr = classification_report(y_test, y_pred, zero_division=0)

            results[name] = {
                "accuracy":       acc,
                "cv_mean":        cv_scores.mean(),
                "cv_std":         cv_scores.std(),
                "confusion":      cm,
                "report":         cr,
                "pipeline":       pipe
            }

            self.log.emit(f"   → acc={acc:.2f}, cv={cv_scores.mean():.2f}±{cv_scores.std():.2f}")
            if acc > best_acc:
                best_acc, best_name = acc, name

        # 4) Guardado del mejor pipeline
        if best_name:
            out_dir = os.path.dirname(self.model_output_path)
            os.makedirs(out_dir, exist_ok=True)
            dump(results[best_name]["pipeline"], self.model_output_path)
            self.log.emit(f"✅ Mejor modelo: {best_name} (acc={best_acc:.2f})")
            self.log.emit(f"💾 Guardado en: {self.model_output_path}")
        else:
            self.log.emit("⚠️ No se encontró modelo válido.")

        # 5) Emitir señal de acabado
        self.finished.emit(results, best_name)
