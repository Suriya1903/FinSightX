"""
FinSightX - Fraud Detection Model Training with MLflow

Phase 7D:
- Load synthetic historical fraud data
- Validate the dataset
- Split into train / validation / test sets
- Train Random Forest
- Evaluate the model
- Track parameters with MLflow
- Track metrics with MLflow
- Track artifacts with MLflow
- Log the trained model with MLflow

MLflow 3.x uses a SQLite backend for local experiment tracking.

Important:
risk_score_rule_based and risk_level are excluded because they were
used to generate the synthetic fraud label. Including them would cause
data leakage.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from mlflow.models import infer_signature

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


# ===================================================================
# PROJECT PATHS
# ===================================================================

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
    / "fraud_random_forest_mlflow.joblib"
)

METRICS_FILE = (
    MODEL_DIR
    / "fraud_model_mlflow_metrics.json"
)

FEATURE_IMPORTANCE_FILE = (
    MODEL_DIR
    / "fraud_feature_importance_mlflow.csv"
)

EXPERIMENT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "experiments"
)

MLFLOW_DATABASE = (
    EXPERIMENT_DIR
    / "mlflow.db"
)

MLFLOW_ARTIFACT_DIR = (
    EXPERIMENT_DIR
    / "artifacts"
)

MLFLOW_EXPERIMENT_NAME = (
    "FinSightX-Fraud-Detection"
)


# ===================================================================
# MODEL CONFIGURATION
# ===================================================================

RANDOM_STATE = 42

TEST_SIZE = 0.15

VALIDATION_SIZE = 0.15

NUMBER_OF_TREES = 300

TARGET_COLUMN = "fraud_label"


# ===================================================================
# FEATURES
# ===================================================================

IDENTIFIER_COLUMNS = [
    "transaction_id",
    "customer_id",
    "device_id",
]

RAW_DESCRIPTION_COLUMNS = [
    "merchant_name",
    "location_name",
]

LEAKAGE_COLUMNS = [
    "risk_score_rule_based",
    "risk_level",
]

TIMESTAMP_COLUMNS = [
    "transaction_created_at",
]

CATEGORICAL_FEATURES = [
    "merchant_category",
    "currency",
    "transaction_status",
]

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


# ===================================================================
# MLFLOW CONFIGURATION
# ===================================================================


def configure_mlflow() -> None:
    """Configure MLflow with a local SQLite tracking backend."""

    EXPERIMENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MLFLOW_ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # MLflow 3.x requires a database backend instead of the old
    # filesystem tracking backend.
    tracking_uri = (
        f"sqlite:///{MLFLOW_DATABASE.as_posix()}"
    )

    mlflow.set_tracking_uri(
        tracking_uri
    )

    mlflow.set_experiment(
        MLFLOW_EXPERIMENT_NAME
    )

    print("-" * 70)
    print("MLflow Configuration")
    print("-" * 70)

    print()
    print(
        f"Tracking database : "
        f"{MLFLOW_DATABASE}"
    )

    print(
        f"Experiment        : "
        f"{MLFLOW_EXPERIMENT_NAME}"
    )

    print(
        f"Artifact directory: "
        f"{MLFLOW_ARTIFACT_DIR}"
    )

    print()


# ===================================================================
# DATASET VALIDATION
# ===================================================================


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Validate the training dataset."""

    print("-" * 70)
    print("STEP 1 - Dataset Validation")
    print("-" * 70)

    if dataframe.empty:
        raise ValueError(
            "Training dataset is empty."
        )

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Target column "
            f"'{TARGET_COLUMN}' is missing."
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
            "Missing feature columns: "
            + ", ".join(
                missing_features
            )
        )

    missing_target_values = (
        dataframe[TARGET_COLUMN]
        .isna()
        .sum()
    )

    if missing_target_values > 0:
        raise ValueError(
            f"Target contains "
            f"{missing_target_values} "
            "missing values."
        )

    unique_labels = sorted(
        dataframe[TARGET_COLUMN]
        .unique()
        .tolist()
    )

    if unique_labels != [0, 1]:
        raise ValueError(
            "Target must contain both "
            f"classes 0 and 1. Found: "
            f"{unique_labels}"
        )

    print()
    print(
        "Dataset validation passed."
    )

    print()
    print(
        f"Rows    : {len(dataframe)}"
    )

    print(
        f"Columns : {len(dataframe.columns)}"
    )

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


# ===================================================================
# PREPROCESSOR
# ===================================================================


def build_preprocessor() -> ColumnTransformer:
    """Create preprocessing pipeline."""

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

    return ColumnTransformer(
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


# ===================================================================
# MODEL EVALUATION
# ===================================================================


def evaluate_model(
    model_pipeline: Pipeline,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Evaluate validation and test performance."""

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

    validation_precision = (
        precision_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        )
    )

    validation_recall = (
        recall_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        )
    )

    validation_f1 = (
        f1_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        )
    )

    validation_roc_auc = (
        roc_auc_score(
            y_validation,
            validation_probabilities,
        )
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

    test_accuracy = (
        accuracy_score(
            y_test,
            test_predictions,
        )
    )

    test_precision = (
        precision_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    )

    test_recall = (
        recall_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    )

    test_f1 = (
        f1_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    )

    test_roc_auc = (
        roc_auc_score(
            y_test,
            test_probabilities,
        )
    )

    matrix = confusion_matrix(
        y_test,
        test_predictions,
    )

    report = classification_report(
        y_test,
        test_predictions,
        target_names=[
            "LEGITIMATE",
            "FRAUD",
        ],
        zero_division=0,
    )

    print()
    print("Validation metrics:")

    print(
        f"Precision : "
        f"{validation_precision:.4f}"
    )

    print(
        f"Recall    : "
        f"{validation_recall:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{validation_f1:.4f}"
    )

    print(
        f"ROC-AUC   : "
        f"{validation_roc_auc:.4f}"
    )

    print()
    print("Test metrics:")

    print(
        f"Accuracy  : "
        f"{test_accuracy:.4f}"
    )

    print(
        f"Precision : "
        f"{test_precision:.4f}"
    )

    print(
        f"Recall    : "
        f"{test_recall:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{test_f1:.4f}"
    )

    print(
        f"ROC-AUC   : "
        f"{test_roc_auc:.4f}"
    )

    print()
    print("Confusion matrix:")

    print(matrix)

    print()
    print("Classification report:")

    print(report)

    return {
        "validation_precision": float(
            validation_precision
        ),
        "validation_recall": float(
            validation_recall
        ),
        "validation_f1": float(
            validation_f1
        ),
        "validation_roc_auc": float(
            validation_roc_auc
        ),
        "test_accuracy": float(
            test_accuracy
        ),
        "test_precision": float(
            test_precision
        ),
        "test_recall": float(
            test_recall
        ),
        "test_f1": float(
            test_f1
        ),
        "test_roc_auc": float(
            test_roc_auc
        ),
        "true_negatives": int(
            matrix[0, 0]
        ),
        "false_positives": int(
            matrix[0, 1]
        ),
        "false_negatives": int(
            matrix[1, 0]
        ),
        "true_positives": int(
            matrix[1, 1]
        ),
    }


# ===================================================================
# FEATURE IMPORTANCE
# ===================================================================


def save_feature_importance(
    model_pipeline: Pipeline,
) -> pd.DataFrame:
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

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    cleaned_names = [
        name
        .replace(
            "numerical__",
            "",
        )
        .replace(
            "categorical__",
            "",
        )
        for name in feature_names
    ]

    importances = (
        classifier.feature_importances_
    )

    dataframe = pd.DataFrame(
        {
            "feature": cleaned_names,
            "importance": importances,
        }
    )

    dataframe = (
        dataframe
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    dataframe[
        "importance_percentage"
    ] = (
        dataframe["importance"]
        * 100
    )

    dataframe.to_csv(
        FEATURE_IMPORTANCE_FILE,
        index=False,
    )

    print()
    print("Top 15 features:")

    print(
        dataframe
        .head(15)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "Feature importance saved to:"
    )

    print(
        FEATURE_IMPORTANCE_FILE
    )

    return dataframe


# ===================================================================
# MAIN
# ===================================================================


def main() -> None:
    print("=" * 70)
    print(
        "FinSightX Fraud Detection - Phase 7D"
    )
    print(
        "Random Forest + MLflow Experiment Tracking"
    )
    print("=" * 70)

    print()

    # ---------------------------------------------------------------
    # Create directories
    # ---------------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Configure MLflow
    # ---------------------------------------------------------------

    configure_mlflow()

    # ---------------------------------------------------------------
    # Load dataset
    # ---------------------------------------------------------------

    print("-" * 70)
    print("Loading training dataset")
    print("-" * 70)

    if not TRAINING_DATA_FILE.exists():
        raise FileNotFoundError(
            "Training dataset not found:\n"
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
    # Validate
    # ---------------------------------------------------------------

    validate_dataset(
        dataframe
    )

    # ---------------------------------------------------------------
    # Prepare X and y
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
        f"Model features : "
        f"{len(feature_columns)}"
    )

    print()
    print("Excluded leakage columns:")

    for column in LEAKAGE_COLUMNS:
        print(
            f"  - {column}"
        )

    # ---------------------------------------------------------------
    # Split data
    # ---------------------------------------------------------------

    print("-" * 70)
    print(
        "STEP 3 - Train / Validation / Test Split"
    )
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
    print(
        f"Training fraud     : "
        f"{y_train.sum()}"
    )

    print(
        f"Validation fraud   : "
        f"{y_validation.sum()}"
    )

    print(
        f"Test fraud         : "
        f"{y_test.sum()}"
    )

    # ---------------------------------------------------------------
    # Build model
    # ---------------------------------------------------------------

    print("-" * 70)
    print(
        "STEP 4 - Building ML Pipeline"
    )
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
        "Algorithm      : Random Forest"
    )

    print(
        f"Trees          : "
        f"{NUMBER_OF_TREES}"
    )

    print(
        "Class weight   : balanced"
    )

    print(
        "Random state   : 42"
    )

    # ---------------------------------------------------------------
    # Start MLflow run
    # ---------------------------------------------------------------

    with mlflow.start_run(
        run_name="random-forest-baseline",
    ) as run:

        print()
        print(
            "MLflow run started."
        )

        print(
            f"Run ID : "
            f"{run.info.run_id}"
        )

        # -----------------------------------------------------------
        # Tags
        # -----------------------------------------------------------

        mlflow.set_tags(
            {
                "project": "FinSightX",
                "phase": "7D",
                "model_type": (
                    "Random Forest"
                ),
                "problem_type": (
                    "Binary Classification"
                ),
                "dataset_type": (
                    "Synthetic Historical Data"
                ),
                "environment": "local",
            }
        )

        # -----------------------------------------------------------
        # Parameters
        # -----------------------------------------------------------

        mlflow.log_params(
            {
                "algorithm": (
                    "RandomForestClassifier"
                ),
                "n_estimators": (
                    NUMBER_OF_TREES
                ),
                "random_state": (
                    RANDOM_STATE
                ),
                "class_weight": (
                    "balanced"
                ),
                "max_features": "sqrt",
                "min_samples_leaf": 2,
                "test_size": TEST_SIZE,
                "validation_size": (
                    VALIDATION_SIZE
                ),
                "total_records": (
                    len(dataframe)
                ),
                "feature_count": (
                    len(feature_columns)
                ),
                "fraud_records": (
                    int(y.sum())
                ),
                "fraud_rate": (
                    float(y.mean())
                ),
            }
        )

        # -----------------------------------------------------------
        # Train
        # -----------------------------------------------------------

        print()
        print(
            "Training model..."
        )

        model_pipeline.fit(
            x_train,
            y_train,
        )

        print()
        print(
            "Model training completed."
        )

        # -----------------------------------------------------------
        # Evaluate
        # -----------------------------------------------------------

        metrics = evaluate_model(
            model_pipeline=model_pipeline,
            x_validation=x_validation,
            y_validation=y_validation,
            x_test=x_test,
            y_test=y_test,
        )

        # -----------------------------------------------------------
        # Log metrics
        # -----------------------------------------------------------

        mlflow.log_metrics(
            {
                "validation_precision": (
                    metrics[
                        "validation_precision"
                    ]
                ),
                "validation_recall": (
                    metrics[
                        "validation_recall"
                    ]
                ),
                "validation_f1": (
                    metrics[
                        "validation_f1"
                    ]
                ),
                "validation_roc_auc": (
                    metrics[
                        "validation_roc_auc"
                    ]
                ),
                "test_accuracy": (
                    metrics[
                        "test_accuracy"
                    ]
                ),
                "test_precision": (
                    metrics[
                        "test_precision"
                    ]
                ),
                "test_recall": (
                    metrics[
                        "test_recall"
                    ]
                ),
                "test_f1": (
                    metrics[
                        "test_f1"
                    ]
                ),
                "test_roc_auc": (
                    metrics[
                        "test_roc_auc"
                    ]
                ),
            }
        )

        # -----------------------------------------------------------
        # Feature importance
        # -----------------------------------------------------------

        save_feature_importance(
            model_pipeline
        )

        # -----------------------------------------------------------
        # Save model locally
        # -----------------------------------------------------------

        joblib.dump(
            model_pipeline,
            MODEL_FILE,
        )

        print()
        print(
            "Model saved locally:"
        )

        print(
            MODEL_FILE
        )

        # -----------------------------------------------------------
        # Save metrics locally
        # -----------------------------------------------------------

        metrics_payload = {
            "project": "FinSightX",
            "phase": "7D",
            "mlflow_run_id": (
                run.info.run_id
            ),
            "model": {
                "algorithm": (
                    "RandomForestClassifier"
                ),
                "n_estimators": (
                    NUMBER_OF_TREES
                ),
                "random_state": (
                    RANDOM_STATE
                ),
                "class_weight": (
                    "balanced"
                ),
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
                "fraud_records": int(
                    y.sum()
                ),
                "fraud_rate": float(
                    y.mean()
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

        # -----------------------------------------------------------
        # Log artifacts
        # -----------------------------------------------------------

        mlflow.log_artifact(
            str(MODEL_FILE),
            artifact_path="model",
        )

        mlflow.log_artifact(
            str(METRICS_FILE),
            artifact_path="metrics",
        )

        mlflow.log_artifact(
            str(FEATURE_IMPORTANCE_FILE),
            artifact_path="feature_importance",
        )

        # -----------------------------------------------------------
        # Dataset metadata
        # -----------------------------------------------------------

        dataset_metadata = (
            EXPERIMENT_DIR
            / "training_dataset_metadata.json"
        )

        with open(
            dataset_metadata,
            "w",
            encoding="utf-8",
        ) as metadata_file:

            json.dump(
                {
                    "dataset": (
                        "fraud_training_dataset.parquet"
                    ),
                    "records": int(
                        len(dataframe)
                    ),
                    "features": (
                        feature_columns
                    ),
                    "fraud_records": int(
                        y.sum()
                    ),
                    "fraud_rate": float(
                        y.mean()
                    ),
                    "random_state": (
                        RANDOM_STATE
                    ),
                },
                metadata_file,
                indent=4,
            )

        mlflow.log_artifact(
            str(dataset_metadata),
            artifact_path="dataset",
        )

        # -----------------------------------------------------------
        # Log MLflow model
        # -----------------------------------------------------------

        sample_input = (
            x_train.head(5)
        )

        sample_output = (
            model_pipeline.predict(
                sample_input
            )
        )

        signature = infer_signature(
            sample_input,
            sample_output,
        )

        mlflow.sklearn.log_model(
    sk_model=model_pipeline,
    name="fraud_random_forest",
    signature=signature,
    input_example=sample_input,
    skops_trusted_types=[
        "numpy.dtype",
        "sklearn.tree._tree.Tree",
    ],
)

        # -----------------------------------------------------------
        # Print run information
        # -----------------------------------------------------------

        print()
        print("-" * 70)
        print(
            "MLflow Run Information"
        )
        print("-" * 70)

        print()
        print(
            f"Experiment : "
            f"{MLFLOW_EXPERIMENT_NAME}"
        )

        print(
            f"Run ID     : "
            f"{run.info.run_id}"
        )

        print()
        print("Metrics tracked:")

        print(
            f"Test Accuracy  : "
            f"{metrics['test_accuracy']:.4f}"
        )

        print(
            f"Test Precision : "
            f"{metrics['test_precision']:.4f}"
        )

        print(
            f"Test Recall    : "
            f"{metrics['test_recall']:.4f}"
        )

        print(
            f"Test F1        : "
            f"{metrics['test_f1']:.4f}"
        )

        print(
            f"Test ROC-AUC   : "
            f"{metrics['test_roc_auc']:.4f}"
        )

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "PHASE 7D COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)

    print()
    print(
        "MLflow experiment:"
    )

    print(
        MLFLOW_EXPERIMENT_NAME
    )

    print()
    print(
        "MLflow database:"
    )

    print(
        MLFLOW_DATABASE
    )

    print()
    print(
        "MLflow artifacts:"
    )

    print(
        MLFLOW_ARTIFACT_DIR
    )

    print()
    print(
        "Model:"
    )

    print(
        MODEL_FILE
    )

    print()
    print(
        "Metrics:"
    )

    print(
        METRICS_FILE
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()