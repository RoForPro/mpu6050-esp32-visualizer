# ui/widgets/training_widget.py

import os

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QDialogButtonBox,QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QTextEdit, QDialogButtonBox,
    QPushButton, QTextEdit, QLabel, QComboBox
)
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# Matplotlib imports
from matplotlib.figure import Figure
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import config
from core.features import extract_features
from core.training import TrainingController


class ConfusionInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guía de la matriz de confusión")
        self.resize(500, 400)

        text = QTextEdit(self)
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Guía de interpretación de la matriz de confusión</h2>
        <p>La matriz de confusión muestra de un vistazo cómo se comporta tu modelo al comparar las etiquetas reales con las predichas:</p>
        <ul>
          <li>
            <strong>Diagonal principal:</strong><br>
            Casos correctamente clasificados.  
            <em>Cuantos más valores altos veas aquí, mejor es la precisión global.</em>
          </li>
          <li>
            <strong>Falsos positivos (FP):</strong><br>
            Muestras que el modelo asignó a una clase por error.  
            <em>Revisa las filas fuera de la diagonal.</em>
          </li>
          <li>
            <strong>Falsos negativos (FN):</strong><br>
            Casos que el modelo no detectó.  
            <em>Revisa las columnas fuera de la diagonal.</em>
          </li>
          <li>
            <strong>Precisión (Precision):</strong><br>
            TP / (TP + FP). <em>Alta precision = pocos FP.</em>
          </li>
          <li>
            <strong>Exhaustividad (Recall):</strong><br>
            TP / (TP + FN). <em>Alto recall = pocos FN.</em>
          </li>
          <li>
            <strong>Desbalanceo:</strong><br>
            Clases con pocos ejemplos reales pueden necesitar más datos o técnicas de balanceo.
          </li>
          <li>
            <strong>Patrones de confusión:</strong><br>
            Observa qué clases se confunden sistemáticamente para mejorar features o clases.
          </li>
        </ul>
        <p><em>Usa esta guía tras cada entrenamiento para pulir tu modelo.</em></p>
        """)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(text, stretch=1)
        layout.addWidget(buttons)

class MultiConfusionMatrixWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.matrices = []
        self.idx = 0

        # Título y botón +INFO
        self.title = QLabel("", alignment=Qt.AlignCenter)
        self.btn_info = QPushButton("+ INFO")
        self.btn_info.setToolTip("Cómo interpretar la matriz de confusión")
        self.btn_info.clicked.connect(self._show_info)

        hdr_layout = QHBoxLayout()
        hdr_layout.addWidget(self.title, stretch=1)
        hdr_layout.addWidget(self.btn_info)

        # Figura
        self.fig = Figure(figsize=(4,4))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        # Navegación Prev/Next
        self.btn_prev = QPushButton("« Prev")
        self.btn_next = QPushButton("Next »")
        self.btn_prev.clicked.connect(self.prev)
        self.btn_next.clicked.connect(self.next)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.setAlignment(Qt.AlignCenter)

        # Layout principal
        main = QVBoxLayout(self)
        main.addLayout(hdr_layout)
        main.addWidget(self.canvas, stretch=1)
        main.addLayout(nav_layout)

    def _show_info(self):
        dlg = ConfusionInfoDialog(self)
        dlg.exec_()

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

        # Limpia figure y axes
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)

        im = self.ax.imshow(cm, interpolation='nearest', aspect='auto')
        self.fig.colorbar(im, ax=self.ax)

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
        self.canvas.draw()

    def prev(self):
        self.idx = (self.idx - 1) % len(self.matrices)
        self._update_display()

    def next(self):
        self.idx = (self.idx + 1) % len(self.matrices)
        self._update_display()


class ScatterInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guía de interpretación del scatter")
        self.resize(500, 400)

        text = QTextEdit(self)
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Guía de interpretación del scatter</h2>
            <p>Al comparar dos parámetros de tus repeticiones en un gráfico de dispersión, puedes obtener información valiosa:</p>
            <ul>
              <li>
                <strong>Separabilidad entre clases:</strong><br>
                Si los puntos de distintas etiquetas (“correcto” vs. “incorrecto”) forman nubes claramente separadas, esa combinación de features es muy discriminativa.  
                <em>Implica que con esos dos valores tu modelo podrá diferenciar bien las técnicas.</em>
              </li>
              <li>
                <strong>Correlación y redundancia:</strong><br>
                Si los puntos caen casi sobre una línea recta, quiere decir que ambos parámetros varían de forma conjunta.  
                <em>Podrías prescindir de uno para simplificar el modelo sin perder información.</em>
              </li>
              <li>
                <strong>Interacciones no lineales:</strong><br>
                Si la frontera entre clases tiene forma curva o en “gota”, un clasificador lineal (SVM lineal, regresión logística) podría no ser suficiente.  
                <em>Sería mejor usar un kernel no lineal o un modelo de red neuronal.</em>
              </li>
              <li>
                <strong>Detección de sub-clusters:</strong><br>
                Observa si dentro de la clase “incorrecto” (o “correcto”) hay varios grupos aislados.  
                <em>Podría indicar distintos tipos de error o estilos de ejecución que aún no clasificaste por separado.</em>
              </li>
              <li>
                <strong>Valores atípicos (outliers):</strong><br>
                Puntos muy aislados pueden ser lecturas erróneas del sensor o etiquetas mal asignadas.  
                <em>Revisa esos casos antes de entrenar tu modelo.</em>
              </li>
              <li>
                <strong>Rangos de variación:</strong><br>
                El eje horizontal y vertical muestran los mínimos y máximos de cada parámetro.  
                <em>Si uno de los ejes apenas se extiende, puede que esa feature aporte poca diversidad.</em>
              </li>
            </ul>
            <p><em>Prueba distintas parejas de parámetros hasta encontrar aquellas que desplieguen las nubes de puntos más separadas y homogéneas. Así optimizarás tu selección de features y mejorarás la precisión de tu modelo.</em></p>
            """)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(text, stretch=1)
        lay.addWidget(buttons)


class FeatureScatterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.X = None
        self.y = None

        # Comboboxes
        self.combo_x = QComboBox()
        self.combo_y = QComboBox()
        self.combo_x.setMinimumWidth(200)
        self.combo_y.setMinimumWidth(200)

        # Botón + INFO
        self.btn_info = QPushButton("+ INFO")
        self.btn_info.setToolTip("Cómo interpretar este scatter")
        self.btn_info.clicked.connect(self._show_info)

        # Canvas Matplotlib
        self.fig = Figure(figsize=(4, 4))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        # Layout de controles
        top = QHBoxLayout()
        top.addWidget(QLabel("Eje X:"))
        top.addWidget(self.combo_x)
        top.addSpacing(20)
        top.addWidget(QLabel("Eje Y:"))
        top.addWidget(self.combo_y)
        top.addSpacing(20)
        top.addWidget(self.btn_info)
        top.addStretch()

        # Layout principal
        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas, stretch=1)

    def _show_info(self):
        dlg = ScatterInfoDialog(self)
        dlg.exec_()

    def load_data(self, X: pd.DataFrame, y: pd.Series):
        # … (igual que antes)
        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)
        self.combo_x.clear();
        self.combo_y.clear()
        cols = list(X.columns)
        self.combo_x.addItems(cols);
        self.combo_y.addItems(cols)
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

        x = self.X[fx].values;
        y = self.X[fy].values;
        labels = self.y.values
        self.ax.clear()
        for cls in np.unique(labels):
            mask = labels == cls
            self.ax.scatter(x[mask], y[mask], label=str(cls))
        self.ax.set_xlabel(fx);
        self.ax.set_ylabel(fy)
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
        self.scatter_widget = FeatureScatterWidget()
        plots_layout = QHBoxLayout()
        plots_layout.addWidget(self.confusion_multi, stretch=1)
        plots_layout.addWidget(self.scatter_widget, stretch=1)

        # Área de logs abajo
        self.log_area = QTextEdit();
        self.log_area.setReadOnly(True)

        # Montaje final
        main = QVBoxLayout(self)
        main.addLayout(top_layout)
        main.addLayout(plots_layout, stretch=3)
        main.addWidget(self.log_area, stretch=1)

        # Preparar controller
        csv_path = os.path.join(config.DATA_FOLDER, config.CSV_FILENAME)
        model_path = config.MODEL_PATH
        algos = {
            "SVM (lineal)": SVC(kernel="linear", probability=True, random_state=42),
            "Árbol de decisión": DecisionTreeClassifier(random_state=42),
            "KNN": KNeighborsClassifier(n_neighbors=5)
        }
        self.ctrl = TrainingController(
            csv_path=csv_path,
            model_output_path=model_path,
            algorithms=algos
        )
        self.ctrl.log.connect(self._append_log)
        self.ctrl.finished.connect(self._on_finished)
        self.btn_train.clicked.connect(self._on_btn_train_click)

    def _on_btn_train_click(self):
        self.log_area.clear()
        self.ctrl.start_training()

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
            df = df.rename(columns={'etiqueta': 'label'})
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
