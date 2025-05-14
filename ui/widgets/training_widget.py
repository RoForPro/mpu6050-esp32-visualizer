# ui/widgets/training_widget.py

import os
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt

import config
from core.training import TrainingController
from core.features import extract_features
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

# Matplotlib imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MultiConfusionMatrixWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.matrices = []   # list of (name, cm, class_names)
        self.idx = 0

        self.title = QLabel("", alignment=Qt.AlignCenter)
        self.fig = Figure(figsize=(4,4))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        self.btn_prev = QPushButton("« Prev")
        self.btn_next = QPushButton("Next »")
        self.btn_prev.clicked.connect(self.prev)
        self.btn_next.clicked.connect(self.next)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        nav = QHBoxLayout()
        nav.addWidget(self.btn_prev)
        nav.addWidget(self.btn_next)
        nav.setAlignment(Qt.AlignCenter)

        lay = QVBoxLayout(self)
        lay.addWidget(self.title)
        lay.addWidget(self.canvas, stretch=1)
        lay.addLayout(nav)

    def set_matrices(self, matrices):
        """
        :param matrices: list of (name, cm_array, class_names)
        """
        self.matrices = matrices
        self.idx = 0
        ok = len(self.matrices) > 0
        self.btn_prev.setEnabled(ok)
        self.btn_next.setEnabled(ok)
        if ok:
            self._update_display()

    def _update_display(self):
        name, cm, class_names = self.matrices[self.idx]
        self.title.setText(f"Matriz de Confusión – {name}")

        # 1) Limpiar TODO el figure (axes, colorbars, etc)
        self.fig.clear()

        # 2) Volver a crear el Axes principal
        self.ax = self.fig.add_subplot(111)

        # 3) Dibujar el heatmap
        im = self.ax.imshow(cm, interpolation='nearest', aspect='auto')

        # 4) Añadir solo UNA barra de color
        self.fig.colorbar(im, ax=self.ax)

        # 5) Rótulos y anotaciones
        n = len(class_names)
        self.ax.set_xticks(np.arange(n))
        self.ax.set_yticks(np.arange(n))
        self.ax.set_xticklabels(class_names, rotation=45, ha='right')
        self.ax.set_yticklabels(class_names)
        for i in range(n):
            for j in range(n):
                self.ax.text(j, i, str(cm[i,j]), ha='center', va='center')

        self.ax.set_xlabel('Predicha')
        self.ax.set_ylabel('Real')
        self.fig.tight_layout()

        # 6) Redibujar el canvas
        self.canvas.draw()

    def prev(self):
        self.idx = (self.idx - 1) % len(self.matrices)
        self._update_display()

    def next(self):
        self.idx = (self.idx + 1) % len(self.matrices)
        self._update_display()


class FeatureScatterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.X = None
        self.y = None

        self.combo_x = QComboBox()
        self.combo_y = QComboBox()
        # Más ancho para leer bien
        self.combo_x.setMinimumWidth(200)
        self.combo_y.setMinimumWidth(200)

        self.fig = Figure(figsize=(4,4))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        top = QHBoxLayout()
        top.addWidget(QLabel("Eje X:"))
        top.addWidget(self.combo_x)
        top.addSpacing(20)
        top.addWidget(QLabel("Eje Y:"))
        top.addWidget(self.combo_y)
        top.addStretch()

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas)

    def load_data(self, X: pd.DataFrame, y: pd.Series):
        self.X = X; self.y = y
        cols = list(X.columns)
        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)
        self.combo_x.clear(); self.combo_y.clear()
        self.combo_x.addItems(cols); self.combo_y.addItems(cols)
        if len(cols) >= 2:
            self.combo_x.setCurrentIndex(0)
            self.combo_y.setCurrentIndex(1)
        self.combo_x.blockSignals(False)
        self.combo_y.blockSignals(False)
        self.combo_x.currentIndexChanged.connect(self._update_plot)
        self.combo_y.currentIndexChanged.connect(self._update_plot)
        self._update_plot()

    def _update_plot(self):
        if self.X is None or self.y is None: return
        fx, fy = self.combo_x.currentText(), self.combo_y.currentText()
        if fx not in self.X.columns or fy not in self.X.columns: return

        x = self.X[fx].values; y = self.X[fy].values; labels = self.y.values
        self.ax.clear()
        for cls in np.unique(labels):
            mask = labels == cls
            self.ax.scatter(x[mask], y[mask], label=str(cls))
        self.ax.set_xlabel(fx); self.ax.set_ylabel(fy)
        self.ax.legend(loc='best')
        self.fig.tight_layout()
        self.canvas.draw()


class TrainingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Botón pequeño y alineado a la izquierda
        self.btn_train = QPushButton("Entrenar")
        self.btn_train.setFixedWidth(120)

        # Colocamos el botón en un HBox
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.btn_train)
        top_layout.addStretch()

        # Widgets de plots
        self.confusion_multi = MultiConfusionMatrixWidget()
        self.scatter_widget  = FeatureScatterWidget()
        plots_layout = QHBoxLayout()
        plots_layout.addWidget(self.confusion_multi, stretch=1)
        plots_layout.addWidget(self.scatter_widget,  stretch=1)

        # Área de logs abajo
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)

        # Montaje final
        main = QVBoxLayout(self)
        main.addLayout(top_layout)
        main.addLayout(plots_layout, stretch=3)
        main.addWidget(self.log_area, stretch=1)

        # Preparar controller
        csv_path   = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)
        model_path = config.MODEL_PATH
        algos = {
            "SVM (lineal)":      SVC(kernel="linear", probability=True, random_state=42),
            "Árbol de decisión": DecisionTreeClassifier(random_state=42),
            "KNN":               KNeighborsClassifier(n_neighbors=5)
        }
        self.ctrl = TrainingController(
            csv_path=csv_path,
            model_output_path=model_path,
            algorithms=algos
        )
        self.ctrl.log.connect(self._append_log)
        self.ctrl.finished.connect(self._on_finished)
        self.btn_train.clicked.connect(self.ctrl.start_training)

    def _append_log(self, text: str):
        self.log_area.append(text)

    def _on_finished(self, results: dict, best_name: str):
        self.log_area.append("\n🏁 Entrenamiento completado.")
        if not results:
            self.log_area.append("→ No hay resultados.")
            return

        # Obtener X,y para scatter y clases
        df = pd.read_csv(os.path.join(config.DATA_FOLDER, config.CSV_FILENAME))
        if 'etiqueta' in df.columns and 'label' not in df.columns:
            df = df.rename(columns={'etiqueta':'label'})
        feats, labels = [], []
        for _, grp in df.groupby('rep_id'):
            feats.append(extract_features(grp))
            labels.append(grp['label'].iloc[0])
        X = pd.DataFrame(feats)
        y = pd.Series(labels)
        classes = sorted(y.unique())

        # Preparar matrices para todos los algoritmos
        mats = []
        for name, info in results.items():
            mats.append((name, info['confusion'], classes))
        self.confusion_multi.set_matrices(mats)
        self.scatter_widget.load_data(X, y)
