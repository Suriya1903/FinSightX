from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


class FraudModel:
    """
    Handles loading and inference for the FinSightX
    fraud detection machine-learning model.
    """

    def __init__(self) -> None:
        default_model_path = (
            Path(__file__).resolve().parents[2]
            / "models"
            / "fraud_random_forest.joblib"
        )

        self.model_path = Path(
            os.getenv(
                "MODEL_PATH",
                str(default_model_path),
            )
        )

        self.model_version = os.getenv(
            "MODEL_VERSION",
            "unknown",
        )

        self.model = None

    def load(self) -> None:
        """
        Load the trained fraud model from disk.
        """

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Fraud model not found at: {self.model_path}"
            )

        self.model = joblib.load(
            self.model_path
        )

    def predict(
        self,
        features: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run fraud prediction for one transaction.
        """

        if self.model is None:
            raise RuntimeError(
                "Fraud model has not been loaded."
            )

        feature_row = {
            "amount": float(
                features["amount"]
            ),
            "amount_band_code": int(
                features["amount_band_code"]
            ),
            "is_high_risk_merchant_category": int(
                features[
                    "is_high_risk_merchant_category"
                ]
            ),
            "has_device": int(
                features["has_device"]
            ),
            "has_location": int(
                features["has_location"]
            ),
            "customer_is_active": int(
                features["customer_is_active"]
            ),
            "is_inr": int(
                features["is_inr"]
            ),
            "is_pending": int(
                features["is_pending"]
            ),
            "transaction_hour": int(
                features["transaction_hour"]
            ),
            "transaction_day_of_week": int(
                features[
                    "transaction_day_of_week"
                ]
            ),
            "is_weekend": int(
                features["is_weekend"]
            ),
            "is_night_transaction": int(
                features["is_night_transaction"]
            ),
            "transaction_velocity": int(
                features["transaction_velocity"]
            ),
            "recent_transaction_amount": float(
                features[
                    "recent_transaction_amount"
                ]
            ),
            "high_velocity_amount": float(
                features["high_velocity_amount"]
            ),
            "merchant_category": (
                str(
                    features.get(
                        "merchant_category",
                        "Unknown",
                    )
                ).strip()
                or "Unknown"
            ),
            "currency": (
                str(
                    features.get(
                        "currency",
                        "UNKNOWN",
                    )
                ).strip().upper()
                or "UNKNOWN"
            ),
            "transaction_status": (
                str(
                    features.get(
                        "transaction_status",
                        "UNKNOWN",
                    )
                ).strip().upper()
                or "UNKNOWN"
            ),
        }

        dataframe = pd.DataFrame(
            [feature_row]
        )

        raw_prediction = int(
            self.model.predict(dataframe)[0]
        )

        probabilities = self.model.predict_proba(
            dataframe
        )[0]

        classes = list(
            self.model.classes_
        )

        probability_by_class = {
            int(label): float(probability)
            for label, probability in zip(
                classes,
                probabilities,
            )
        }

        fraud_probability = probability_by_class.get(
            1,
            0.0,
        )

        legitimate_probability = probability_by_class.get(
            0,
            0.0,
        )

        model_threshold = 0.5

        if fraud_probability >= model_threshold:
            prediction = "FRAUD"
            ml_risk_level = "HIGH"
        else:
            prediction = "LEGITIMATE"

            if fraud_probability >= 0.30:
                ml_risk_level = "MEDIUM"
            else:
                ml_risk_level = "LOW"

        return {
            "model_name": "fraud_random_forest",
            "model_version": self.model_version,
            "prediction": prediction,
            "fraud_probability": fraud_probability,
            "legitimate_probability": legitimate_probability,
            "risk_level": ml_risk_level,
            "model_threshold": model_threshold,
        }