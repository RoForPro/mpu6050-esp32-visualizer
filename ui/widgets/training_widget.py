# ui/widgets/training_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt

import config
from core.training import TrainingController
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

class TrainingWidget(QWidget):
    """
    Widget Qt para entrenar modelos desde la UI.
    Muestra logs en tiempo real y guarda el mejor pipeline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Botón y área de logs
        self.btn_train = QPushButton("Iniciar Entrenamiento")
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.btn_train)
        layout.addWidget(self.log_area)

        # Ruta de datos y salida de modelo
        csv_path = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)
        model_path = config.MODEL_PATH

        # Definición de algoritmos (extensible)
        algos = {
            "SVM (lineal)":      SVC(kernel="linear", probability=True, random_state=42),
            "Árbol de decisión": DecisionTreeClassifier(random_state=42),
            "KNN":               KNeighborsClassifier(n_neighbors=5)
            # más adelante: {"MLP": MLPClassifier(...), …}
        }

        # Controller de entrenamiento
        self.ctrl = TrainingController(
            csv_path=csv_path,
            model_output_path=model_path,
            algorithms=algos
        )
        self.ctrl.log.connect(self._append_log)
        self.ctrl.finished.connect(self._on_finished)

        # Conexión UI → Controller
        self.btn_train.clicked.connect(self.ctrl.start_training)

    def _append_log(self, text: str):
        """Añade una línea al log de la UI."""
        self.log_area.append(text)

    def _on_finished(self, results: dict, best_name: str):
        """Señal tras acabar el entrenamiento."""
        self.log_area.append("\n🏁 Entrenamiento completado.")
        if best_name:
            self.log_area.append(f"→ Modelo seleccionado: {best_name}")
        else:
            self.log_area.append("→ No se seleccionó ningún modelo.")
