import logging
import os
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    trim,
    when,
)


# ==========================================================
# Logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(
    "finsightx-lake-warehouse"
)


# ==========================================================
# MinIO Configuration
# ==========================================================

MINIO_ENDPOINT = os.getenv(
    "MINIO_ENDPOINT",
    "http://minio:9000",
)

MINIO_BUCKET = os.getenv(
    "MINIO_BUCKET",
    "finsightx-data",
)

MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
    "minioadmin",
)

MINIO_SECRET_KEY = os.getenv(
    "MINIO_SECRET_KEY",
    "change_me",
)


PROCESSED_PATH = (
    f"s3a://{MINIO_BUCKET}/processed/transactions"
)


# ==========================================================
# PostgreSQL Configuration
# ==========================================================

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "postgres",
)

POSTGRES_PORT = os.getenv(
    "POSTGRES_PORT",
    "5432",
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "finsightx",
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "finsightx",
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "change_me",
)


POSTGRES_JDBC_URL = (
    f"jdbc:postgresql://"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


JDBC_DRIVER = "org.postgresql.Driver"


# ==========================================================
# Staging Table
# ==========================================================

STAGING_TABLE = (
    "analytics.stg_processed_transactions"
)


# ==========================================================
# Spark Session
# ==========================================================

def create_spark_session() -> SparkSession:
    logger.info(
        "Creating Spark session for lake-to-warehouse load..."
    )

    spark = (
        SparkSession.builder
        .appName(
            "FinSightX-Lake-To-Warehouse"
        )
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            MINIO_ENDPOINT,
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            MINIO_ACCESS_KEY,
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            MINIO_SECRET_KEY,
        )
        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true",
        )
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )
        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            "false",
        )
        .config(
            "spark.sql.adaptive.enabled",
            "false",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    logger.info(
        "Spark session created successfully."
    )

    return spark


# ==========================================================
# Read Processed Data Lake
# ==========================================================

def read_processed_transactions(
    spark: SparkSession,
):
    logger.info(
        "Reading processed transactions from: %s",
        PROCESSED_PATH,
    )

    df = (
        spark.read
        .format("parquet")
        .load(PROCESSED_PATH)
    )

    logger.info(
        "Processed transaction schema:"
    )

    df.printSchema()

    record_count = df.count()

    logger.info(
        "Processed transactions loaded: %s",
        record_count,
    )

    return df


# ==========================================================
# Validate Processed Transactions
# ==========================================================

def validate_processed_transactions(df):
    """
    Validate processed lake records before they enter
    PostgreSQL staging.

    Required fields:

        transaction_id
        customer_id
        merchant_name

    Records missing these fields are rejected because
    they cannot safely become warehouse transactions.
    """

    logger.info(
        "Validating processed transaction records..."
    )

    total_count = df.count()

    # ------------------------------------------------------
    # Identify invalid records
    # ------------------------------------------------------

    validation_df = (
        df.withColumn(
            "_transaction_id_valid",
            when(
                col("transaction_id").isNotNull()
                & (
                    trim(
                        col("transaction_id")
                    ) != ""
                ),
                True,
            ).otherwise(False),
        )
        .withColumn(
            "_customer_id_valid",
            when(
                col("customer_id").isNotNull()
                & (
                    trim(
                        col("customer_id")
                    ) != ""
                ),
                True,
            ).otherwise(False),
        )
        .withColumn(
            "_merchant_name_valid",
            when(
                col("merchant_name").isNotNull()
                & (
                    trim(
                        col("merchant_name")
                    ) != ""
                ),
                True,
            ).otherwise(False),
        )
    )

    # ------------------------------------------------------
    # Count rejected records
    # ------------------------------------------------------

    invalid_df = validation_df.filter(
        ~(
            col("_transaction_id_valid")
            & col("_customer_id_valid")
            & col("_merchant_name_valid")
        )
    )

    invalid_count = invalid_df.count()

    valid_df = validation_df.filter(
        col("_transaction_id_valid")
        & col("_customer_id_valid")
        & col("_merchant_name_valid")
    )

    valid_count = valid_df.count()

    logger.info(
        "Validation completed | total=%s | valid=%s | rejected=%s",
        total_count,
        valid_count,
        invalid_count,
    )

    # ------------------------------------------------------
    # Log rejected records
    # ------------------------------------------------------

    if invalid_count > 0:

        logger.warning(
            "Rejected %s invalid processed transaction(s).",
            invalid_count,
        )

        logger.warning(
            "Rejected transaction details:"
        )

        (
            invalid_df
            .select(
                "transaction_id",
                "customer_id",
                "amount",
                "merchant_name",
                "transaction_date",
                "data_quality_status",
            )
            .show(
                20,
                truncate=False,
            )
        )

    else:

        logger.info(
            "No invalid processed transaction records found."
        )

    # ------------------------------------------------------
    # Remove validation helper columns
    # ------------------------------------------------------

    valid_df = valid_df.drop(
        "_transaction_id_valid",
        "_customer_id_valid",
        "_merchant_name_valid",
    )

    return valid_df, invalid_count


# ==========================================================
# Prepare Warehouse Staging Data
# ==========================================================

def prepare_staging_dataframe(df):
    logger.info(
        "Preparing dataframe for PostgreSQL staging..."
    )

    staging_df = (
        df.select(
            col("transaction_id"),
            col("customer_id"),
            col("amount"),
            col("currency"),
            col("merchant_name"),
            col("merchant_category"),
            col("location"),
            col("device_id"),
            col("event_type"),
            col("event_version"),
            col("event_id"),
            col("occurred_at"),
            col("transaction_date"),
            col("transaction_year"),
            col("transaction_month"),
            col("transaction_day"),
            col("amount_band"),
            col("data_quality_status"),
            col("processing_layer"),
        )
        .withColumn(
            "loaded_at",
            lit(
                datetime.now(
                    timezone.utc
                ).replace(
                    tzinfo=None
                )
            ),
        )
    )

    return staging_df


# ==========================================================
# Write to PostgreSQL
# ==========================================================

def write_to_postgres(
    staging_df,
) -> None:

    logger.info(
        "Writing validated processed data to PostgreSQL..."
    )

    (
        staging_df.write
        .format("jdbc")
        .option(
            "url",
            POSTGRES_JDBC_URL,
        )
        .option(
            "dbtable",
            STAGING_TABLE,
        )
        .option(
            "user",
            POSTGRES_USER,
        )
        .option(
            "password",
            POSTGRES_PASSWORD,
        )
        .option(
            "driver",
            JDBC_DRIVER,
        )
        .option(
            "batchsize",
            "1000",
        )
        .mode("overwrite")
        .save()
    )

    logger.info(
        "PostgreSQL staging load completed successfully."
    )


# ==========================================================
# Main
# ==========================================================

def main():

    logger.info(
        "=================================================="
    )

    logger.info(
        "FinSightX Lake-to-Warehouse Pipeline"
    )

    logger.info(
        "=================================================="
    )

    spark = None

    try:

        # --------------------------------------------------
        # Create Spark session
        # --------------------------------------------------

        spark = create_spark_session()

        # --------------------------------------------------
        # Read processed lake data
        # --------------------------------------------------

        processed_df = (
            read_processed_transactions(
                spark
            )
        )

        # --------------------------------------------------
        # Validate lake data
        # --------------------------------------------------

        valid_df, rejected_count = (
            validate_processed_transactions(
                processed_df
            )
        )

        # --------------------------------------------------
        # Count valid records
        # --------------------------------------------------

        valid_count = valid_df.count()

        if valid_count == 0:
            raise ValueError(
                "No valid processed transactions remain "
                "after data-quality validation."
            )

        # --------------------------------------------------
        # Prepare staging dataframe
        # --------------------------------------------------

        staging_df = (
            prepare_staging_dataframe(
                valid_df
            )
        )

        # --------------------------------------------------
        # Write valid records to PostgreSQL
        # --------------------------------------------------

        write_to_postgres(
            staging_df
        )

        # --------------------------------------------------
        # Final pipeline summary
        # --------------------------------------------------

        logger.info(
            "=================================================="
        )

        logger.info(
            "Lake-to-warehouse pipeline completed successfully."
        )

        logger.info(
            "Total lake records   : %s",
            processed_df.count(),
        )

        logger.info(
            "Valid records        : %s",
            valid_count,
        )

        logger.info(
            "Rejected records     : %s",
            rejected_count,
        )

        logger.info(
            "Staging table        : %s",
            STAGING_TABLE,
        )

        logger.info(
            "=================================================="
        )

    except Exception:

        logger.exception(
            "Lake-to-warehouse pipeline failed."
        )

        raise

    finally:

        if spark is not None:

            logger.info(
                "Stopping Spark session..."
            )

            spark.stop()


if __name__ == "__main__":
    main()
