# scripts/predictor.py

import pandas as pd
from joblib import load
from scripts.features import extract_from_list


class Predictor:
    """Carga modelo y permite predecir sobre segmentos."""

    def __init__(self, model_path: str):
        self.pipe = load(model_path)

    def predict_segment(self, samples: list):
        """
        samples: lista de [ts,yaw,pitch,roll]
        Devuelve (tag, prob).
        """
        feat = extract_from_list(samples)
        df = pd.DataFrame([feat])
        y_pred = self.pipe.predict(df)[0]
        prob = self.pipe.predict_proba(df)[0][y_pred]
        return y_pred, prob
