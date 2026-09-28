"""
FinSightX - Fraud Detection Model Training

Phase 7C:
- Load synthetic historical fraud data
- Validate the dataset
- Split into train / validation / test sets
- Preprocess numerical and categorical features
- Train a Random Forest classifier
- Evaluate using fraud-detection metrics
- Save the trained model
- Save evaluation metrics
- Save feature importance information

Important:
The rule-based risk score is intentionally excluded from model features
because it was used to generate the fraud label. Including it would cause
data leakage.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# -------------------------------------------------------------------
# Project paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAINING_DATA_FILE = (
    PROJECT_ROOT
    / "ml"
    / "training"
    / "fraud_training_dataset.parquet"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "models"
)

MODEL_FILE = (
    MODEL_DIR
    / "fraud_random_forest.joblib"
)

METRICS_FILE = (
    MODEL_DIR
    / "fraud_model_metrics.json"
)

FEATURE_IMPORTANCE_FILE = (
    MODEL_DIR
    / "fraud_feature_importance.csv"
)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

RANDOM_STATE = 42

TEST_SIZE = 0.15
VALIDATION_SIZE = 0.15

NUMBER_OF_TREES = 300

TARGET_COLUMN = "fraud_label"


# -------------------------------------------------------------------
# Feature configuration
# -------------------------------------------------------------------

# These columns are identifiers or descriptive fields and should not
# directly be used by the model.

IDENTIFIER_COLUMNS = [
    "transaction_id",
    "customer_id",
    "device_id",
]


# These columns contain raw descriptive information that is not needed
# for the first model.

RAW_DESCRIPTION_COLUMNS = [
    "merchant_name",
    "location_name",
]


# This column must explicitly be excluded because it was used to
# generate the fraud label.

LEAKAGE_COLUMNS = [
    "risk_score_rule_based",
    "risk_level",
]


# Timestamp is converted into useful numerical features already present
# in the dataset, so the raw timestamp is excluded.

TIMESTAMP_COLUMNS = [
    "transaction_created_at",
]


# Categorical features that will be one-hot encoded.

CATEGORICAL_FEATURES = [
    "merchant_category",
    "currency",
    "transaction_status",
]


# Numerical features used by the model.

NUMERICAL_FEATURES = [
    "amount",
    "amount_band_code",
    "is_high_risk_merchant_category",
    "has_device",
    "has_location",
    "customer_is_active",
    "is_inr",
    "is_pending",
    "transaction_hour",
    "transaction_day_of_week",
    "is_weekend",
    "is_night_transaction",
    "transaction_velocity",
    "recent_transaction_amount",
    "high_velocity_amount",
]


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------


def validate_dataset(dataframe: pd.DataFrame) -> None:
    """Validate the training dataset before model training."""

    print("-" * 70)
    print("STEP 1 - Dataset Validation")
    print("-" * 70)

    if dataframe.empty:
        raise ValueError(
            "Training dataset is empty."
        )

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' is missing."
        )

    required_features = (
        NUMERICAL_FEATURES
        + CATEGORICAL_FEATURES
    )

    missing_features = [
        column
        for column in required_features
        if column not in dataframe.columns
    ]

    if missing_features:
        raise ValueError(
            "Required feature columns are missing: "
            + ", ".join(missing_features)
        )

    missing_target_values = (
        dataframe[TARGET_COLUMN]
        .isna()
        .sum()
    )

    if missing_target_values > 0:
        raise ValueError(
            f"Target contains {missing_target_values} missing values."
        )

    unique_labels = sorted(
        dataframe[TARGET_COLUMN]
        .unique()
        .tolist()
    )

    if unique_labels != [0, 1]:
        raise ValueError(
            "Target must contain both classes 0 and 1. "
            f"Found: {unique_labels}"
        )

    print()
    print("Dataset validation passed.")
    print()
    print(f"Rows    : {len(dataframe)}")
    print(f"Columns : {len(dataframe.columns)}")

    print()
    print("Target distribution:")

    print(
        dataframe[TARGET_COLUMN]
        .value_counts()
        .sort_index()
        .rename(
            index={
                0: "LEGITIMATE",
                1: "FRAUD",
            }
        )
    )

    print()


# -------------------------------------------------------------------
# Preprocessing
# -------------------------------------------------------------------


def build_preprocessor() -> ColumnTransformer:
    """Build preprocessing pipeline for numerical and categorical data."""

    numerical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numerical",
                numerical_pipeline,
                NUMERICAL_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# -------------------------------------------------------------------
# Feature names
# -------------------------------------------------------------------


def get_feature_names(
    fitted_preprocessor: ColumnTransformer,
) -> np.ndarray:
    """Return feature names after preprocessing."""

    feature_names = (
        fitted_preprocessor
        .get_feature_names_out()
    )

    cleaned_names = []

    for name in feature_names:
        cleaned_name = (
            name
            .replace(
                "numerical__",
                "",
            )
            .replace(
                "categorical__",
                "",
            )
        )

        cleaned_names.append(
            cleaned_name
        )

    return np.array(
        cleaned_names,
        dtype=str,
    )


# -------------------------------------------------------------------
# Evaluation
# -------------------------------------------------------------------


def evaluate_model(
    model_pipeline: Pipeline,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Evaluate the trained model."""

    print("-" * 70)
    print("STEP 5 - Model Evaluation")
    print("-" * 70)

    # ---------------------------------------------------------------
    # Validation predictions
    # ---------------------------------------------------------------

    validation_predictions = (
        model_pipeline.predict(
            x_validation
        )
    )

    validation_probabilities = (
        model_pipeline.predict_proba(
            x_validation
        )[:, 1]
    )

    validation_precision = precision_score(
        y_validation,
        validation_predictions,
        zero_division=0,
    )

    validation_recall = recall_score(
        y_validation,
        validation_predictions,
        zero_division=0,
    )

    validation_f1 = f1_score(
        y_validation,
        validation_predictions,
        zero_division=0,
    )

    validation_roc_auc = roc_auc_score(
        y_validation,
        validation_probabilities,
    )

    # ---------------------------------------------------------------
    # Test predictions
    # ---------------------------------------------------------------

    test_predictions = (
        model_pipeline.predict(
            x_test
        )
    )

    test_probabilities = (
        model_pipeline.predict_proba(
            x_test
        )[:, 1]
    )

    test_accuracy = accuracy_score(
        y_test,
        test_predictions,
    )

    test_precision = precision_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    test_recall = recall_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    test_f1 = f1_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    test_roc_auc = roc_auc_score(
        y_test,
        test_probabilities,
    )

    test_confusion_matrix = confusion_matrix(
        y_test,
        test_predictions,
    )

    test_classification_report = (
        classification_report(
            y_test,
            test_predictions,
            target_names=[
                "LEGITIMATE",
                "FRAUD",
            ],
            zero_division=0,
        )
    )

    # ---------------------------------------------------------------
    # Print validation metrics
    # ---------------------------------------------------------------

    print()
    print("Validation metrics:")
    print(
        f"Precision : {validation_precision:.4f}"
    )
    print(
        f"Recall    : {validation_recall:.4f}"
    )
    print(
        f"F1 Score  : {validation_f1:.4f}"
    )
    print(
        f"ROC-AUC   : {validation_roc_auc:.4f}"
    )

    # ---------------------------------------------------------------
    # Print test metrics
    # ---------------------------------------------------------------

    print()
    print("Test metrics:")
    print(
        f"Accuracy  : {test_accuracy:.4f}"
    )
    print(
        f"Precision : {test_precision:.4f}"
    )
    print(
        f"Recall    : {test_recall:.4f}"
    )
    print(
        f"F1 Score  : {test_f1:.4f}"
    )
    print(
        f"ROC-AUC   : {test_roc_auc:.4f}"
    )

    print()
    print("Confusion matrix:")
    print(
        test_confusion_matrix
    )

    print()
    print("Classification report:")
    print(
        test_classification_report
    )

    # ---------------------------------------------------------------
    # Confusion matrix values
    # ---------------------------------------------------------------

    true_negatives = int(
        test_confusion_matrix[0, 0]
    )

    false_positives = int(
        test_confusion_matrix[0, 1]
    )

    false_negatives = int(
        test_confusion_matrix[1, 0]
    )

    true_positives = int(
        test_confusion_matrix[1, 1]
    )

    # ---------------------------------------------------------------
    # Return structured metrics
    # ---------------------------------------------------------------

    return {
        "validation": {
            "precision": float(
                validation_precision
            ),
            "recall": float(
                validation_recall
            ),
            "f1_score": float(
                validation_f1
            ),
            "roc_auc": float(
                validation_roc_auc
            ),
        },
        "test": {
            "accuracy": float(
                test_accuracy
            ),
            "precision": float(
                test_precision
            ),
            "recall": float(
                test_recall
            ),
            "f1_score": float(
                test_f1
            ),
            "roc_auc": float(
                test_roc_auc
            ),
        },
        "confusion_matrix": {
            "true_negatives": true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_positives": true_positives,
        },
        "test_samples": int(
            len(y_test)
        ),
        "test_fraud_samples": int(
            y_test.sum()
        ),
        "test_legitimate_samples": int(
            (y_test == 0).sum()
        ),
    }


# -------------------------------------------------------------------
# Feature importance
# -------------------------------------------------------------------


def save_feature_importance(
    model_pipeline: Pipeline,
) -> None:
    """Save Random Forest feature importance."""

    print("-" * 70)
    print("STEP 6 - Feature Importance")
    print("-" * 70)

    preprocessor = (
        model_pipeline
        .named_steps["preprocessor"]
    )

    classifier = (
        model_pipeline
        .named_steps["classifier"]
    )

    feature_names = get_feature_names(
        preprocessor
    )

    importances = (
        classifier.feature_importances_
    )

    feature_importance_dataframe = (
        pd.DataFrame(
            {
                "feature": feature_names,
                "importance": importances,
            }
        )
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    feature_importance_dataframe[
        "importance_percentage"
    ] = (
        feature_importance_dataframe[
            "importance"
        ]
        * 100
    )

    feature_importance_dataframe.to_csv(
        FEATURE_IMPORTANCE_FILE,
        index=False,
    )

    print()
    print("Top 15 features:")

    print(
        feature_importance_dataframe
        .head(15)
        .to_string(index=False)
    )

    print()
    print(
        "Feature importance saved to:"
    )
    print(
        FEATURE_IMPORTANCE_FILE
    )


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("FinSightX Fraud Detection - Phase 7C")
    print("Random Forest Model Training")
    print("=" * 70)

    print()
    print(
        f"Training dataset : {TRAINING_DATA_FILE}"
    )
    print(
        f"Model output     : {MODEL_FILE}"
    )
    print(
        f"Metrics output   : {METRICS_FILE}"
    )
    print()

    # ---------------------------------------------------------------
    # Create output directory
    # ---------------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------------

    print("-" * 70)
    print("Loading training dataset")
    print("-" * 70)

    if not TRAINING_DATA_FILE.exists():
        raise FileNotFoundError(
            "Training dataset was not found:\n"
            f"{TRAINING_DATA_FILE}"
        )

    dataframe = pd.read_parquet(
        TRAINING_DATA_FILE
    )

    print()
    print(
        f"Loaded {len(dataframe)} records."
    )

    # ---------------------------------------------------------------
    # Validate dataset
    # ---------------------------------------------------------------

    validate_dataset(
        dataframe
    )

    # ---------------------------------------------------------------
    # Build X and y
    # ---------------------------------------------------------------

    print("-" * 70)
    print("STEP 2 - Preparing Features")
    print("-" * 70)

    feature_columns = (
        NUMERICAL_FEATURES
        + CATEGORICAL_FEATURES
    )

    x = dataframe[
        feature_columns
    ].copy()

    y = dataframe[
        TARGET_COLUMN
    ].astype(int)

    print()
    print(
        f"Model features : {len(feature_columns)}"
    )

    print()
    print("Numerical features:")
    for feature in NUMERICAL_FEATURES:
        print(
            f"  - {feature}"
        )

    print()
    print("Categorical features:")
    for feature in CATEGORICAL_FEATURES:
        print(
            f"  - {feature}"
        )

    print()
    print("Excluded from model:")
    for feature in (
        IDENTIFIER_COLUMNS
        + RAW_DESCRIPTION_COLUMNS
        + LEAKAGE_COLUMNS
        + TIMESTAMP_COLUMNS
    ):
        print(
            f"  - {feature}"
        )

    # ---------------------------------------------------------------
    # First split:
    #
    # 85% temporary training/validation
    # 15% final test
    # ---------------------------------------------------------------

    print("-" * 70)
    print("STEP 3 - Train / Validation / Test Split")
    print("-" * 70)

    (
        x_train_validation,
        x_test,
        y_train_validation,
        y_test,
    ) = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # ---------------------------------------------------------------
    # Second split:
    #
    # From the remaining 85%, take 15% overall as validation.
    #
    # validation_fraction = 0.15 / 0.85
    # ---------------------------------------------------------------

    validation_fraction = (
        VALIDATION_SIZE
        / (
            1.0
            - TEST_SIZE
        )
    )

    (
        x_train,
        x_validation,
        y_train,
        y_validation,
    ) = train_test_split(
        x_train_validation,
        y_train_validation,
        test_size=validation_fraction,
        random_state=RANDOM_STATE,
        stratify=y_train_validation,
    )

    print()
    print("Dataset split:")
    print(
        f"Training   : {len(x_train)}"
    )
    print(
        f"Validation : {len(x_validation)}"
    )
    print(
        f"Test       : {len(x_test)}"
    )

    print()
    print("Fraud distribution:")

    print(
        f"Training fraud     : {y_train.sum()}"
    )

    print(
        f"Validation fraud   : {y_validation.sum()}"
    )

    print(
        f"Test fraud         : {y_test.sum()}"
    )

    # ---------------------------------------------------------------
    # Preprocessor
    # ---------------------------------------------------------------

    print("-" * 70)
    print("STEP 4 - Building ML Pipeline")
    print("-" * 70)

    preprocessor = (
        build_preprocessor()
    )

    classifier = RandomForestClassifier(
        n_estimators=NUMBER_OF_TREES,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
        max_features="sqrt",
        min_samples_leaf=2,
    )

    model_pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )

    print()
    print(
        "Algorithm : Random Forest"
    )

    print(
        f"Trees     : {NUMBER_OF_TREES}"
    )

    print(
        "Class weight : balanced"
    )

    print(
        "Random state : 42"
    )

    print()
    print(
        "Training model..."
    )

    # ---------------------------------------------------------------
    # Train
    # ---------------------------------------------------------------

    model_pipeline.fit(
        x_train,
        y_train,
    )

    print()
    print(
        "Model training completed."
    )

    # ---------------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------------

    metrics = evaluate_model(
        model_pipeline=model_pipeline,
        x_validation=x_validation,
        y_validation=y_validation,
        x_test=x_test,
        y_test=y_test,
    )

    # ---------------------------------------------------------------
    # Feature importance
    # ---------------------------------------------------------------

    save_feature_importance(
        model_pipeline
    )

    # ---------------------------------------------------------------
    # Save model
    # ---------------------------------------------------------------

    print("-" * 70)
    print("STEP 7 - Saving Model")
    print("-" * 70)

    joblib.dump(
        model_pipeline,
        MODEL_FILE,
    )

    print()
    print(
        "Model saved to:"
    )
    print(
        MODEL_FILE
    )

    # ---------------------------------------------------------------
    # Save metrics
    # ---------------------------------------------------------------

    metrics_payload = {
        "project": "FinSightX",
        "phase": "7C",
        "model": {
            "algorithm": "RandomForestClassifier",
            "n_estimators": NUMBER_OF_TREES,
            "random_state": RANDOM_STATE,
            "class_weight": "balanced",
            "max_features": "sqrt",
            "min_samples_leaf": 2,
        },
        "dataset": {
            "total_records": int(
                len(dataframe)
            ),
            "training_records": int(
                len(x_train)
            ),
            "validation_records": int(
                len(x_validation)
            ),
            "test_records": int(
                len(x_test)
            ),
            "total_fraud_records": int(
                y.sum()
            ),
            "fraud_rate": float(
                y.mean()
            ),
        },
        "features": {
            "numerical": NUMERICAL_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
            "excluded_identifier_columns": (
                IDENTIFIER_COLUMNS
            ),
            "excluded_description_columns": (
                RAW_DESCRIPTION_COLUMNS
            ),
            "excluded_leakage_columns": (
                LEAKAGE_COLUMNS
            ),
            "excluded_timestamp_columns": (
                TIMESTAMP_COLUMNS
            ),
        },
        "metrics": metrics,
    }

    with open(
        METRICS_FILE,
        "w",
        encoding="utf-8",
    ) as metrics_file:
        json.dump(
            metrics_payload,
            metrics_file,
            indent=4,
        )

    print()
    print(
        "Metrics saved to:"
    )
    print(
        METRICS_FILE
    )

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("PHASE 7C COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print()
    print("Model:")
    print(
        MODEL_FILE
    )

    print()
    print("Metrics:")
    print(
        METRICS_FILE
    )

    print()
    print("Feature importance:")
    print(
        FEATURE_IMPORTANCE_FILE
    )

    print()
    print("Final test performance:")

    print(
        f"Accuracy  : "
        f"{metrics['test']['accuracy']:.4f}"
    )

    print(
        f"Precision : "
        f"{metrics['test']['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{metrics['test']['recall']:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{metrics['test']['f1_score']:.4f}"
    )

    print(
        f"ROC-AUC   : "
        f"{metrics['test']['roc_auc']:.4f}"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()