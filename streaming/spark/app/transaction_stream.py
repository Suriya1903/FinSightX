import logging

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    lit,
    regexp_replace,
    to_timestamp,
    trim,
    upper,
    when,
    year,
    month,
    dayofmonth,
    to_date,
)
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("finsightx-spark")


# ============================================================
# Configuration
# ============================================================

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "transaction.created"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_BUCKET = "finsightx-data"

MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "change_me"


# ------------------------------------------------------------
# Raw layer
# ------------------------------------------------------------

RAW_OUTPUT_PATH = (
    f"s3a://{MINIO_BUCKET}/raw/transactions"
)

RAW_CHECKPOINT_PATH = (
    f"s3a://{MINIO_BUCKET}/checkpoints/transactions"
)


# ------------------------------------------------------------
# Processed layer
# ------------------------------------------------------------

PROCESSED_OUTPUT_PATH = (
    f"s3a://{MINIO_BUCKET}/processed/transactions"
)

PROCESSED_CHECKPOINT_PATH = (
    f"s3a://{MINIO_BUCKET}/checkpoints/processed_transactions"
)


# ============================================================
# Kafka event schema
# ============================================================

transaction_schema = StructType(
    [
        StructField(
            "id",
            StringType(),
            True,
        ),
        StructField(
            "customer_id",
            StringType(),
            True,
        ),
        StructField(
            "amount",
            DoubleType(),
            True,
        ),
        StructField(
            "currency",
            StringType(),
            True,
        ),
        StructField(
            "merchant_name",
            StringType(),
            True,
        ),
        StructField(
            "merchant_category",
            StringType(),
            True,
        ),
        StructField(
            "location",
            StringType(),
            True,
        ),
        StructField(
            "device_id",
            StringType(),
            True,
        ),
    ]
)


event_schema = StructType(
    [
        StructField(
            "event_type",
            StringType(),
            True,
        ),
        StructField(
            "event_version",
            StringType(),
            True,
        ),
        StructField(
            "event_id",
            StringType(),
            True,
        ),
        StructField(
            "occurred_at",
            StringType(),
            True,
        ),
        StructField(
            "transaction",
            transaction_schema,
            True,
        ),
    ]
)


# ============================================================
# Spark session
# ============================================================

def create_spark_session() -> SparkSession:

    logger.info(
        "Creating Spark session..."
    )

    spark = (
        SparkSession.builder
        .appName(
            "FinSightX-Transaction-Streaming"
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


# ============================================================
# Kafka stream
# ============================================================

def create_kafka_stream(spark: SparkSession):

    logger.info(
        "Connecting to Kafka topic: %s",
        KAFKA_TOPIC,
    )

    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            KAFKA_BOOTSTRAP_SERVERS,
        )
        .option(
            "subscribe",
            KAFKA_TOPIC,
        )
        .option(
            "startingOffsets",
            "earliest",
        )
        .option(
            "failOnDataLoss",
            "false",
        )
        .load()
    )

    logger.info(
        "Connected to Kafka topic: %s",
        KAFKA_TOPIC,
    )

    return kafka_stream


# ============================================================
# Parse Kafka events
# ============================================================

def parse_transaction_events(kafka_stream):

    parsed_stream = (
        kafka_stream
        .select(
            col("timestamp").alias(
                "kafka_timestamp"
            ),
            col("partition"),
            col("offset"),
            col("value")
            .cast("string")
            .alias("json_value"),
        )
        .withColumn(
            "event",
            from_json(
                col("json_value"),
                event_schema,
            ),
        )
    )

    transactions = (
        parsed_stream
        .select(
            col("kafka_timestamp"),
            col("partition"),
            col("offset"),

            col(
                "event.event_type"
            ).alias("event_type"),

            col(
                "event.event_version"
            ).alias("event_version"),

            col(
                "event.event_id"
            ).alias("event_id"),

            to_timestamp(
                col(
                    "event.occurred_at"
                )
            ).alias("occurred_at"),

            col(
                "event.transaction.id"
            ).alias("transaction_id"),

            col(
                "event.transaction.customer_id"
            ).alias("customer_id"),

            col(
                "event.transaction.amount"
            ).alias("amount"),

            col(
                "event.transaction.currency"
            ).alias("currency"),

            col(
                "event.transaction.merchant_name"
            ).alias("merchant_name"),

            col(
                "event.transaction.merchant_category"
            ).alias(
                "merchant_category"
            ),

            col(
                "event.transaction.location"
            ).alias("location"),

            col(
                "event.transaction.device_id"
            ).alias("device_id"),
        )
    )

    return transactions


# ============================================================
# Processed transaction transformation
# ============================================================

def create_processed_stream(transactions):

    processed = (
        transactions

        # ----------------------------------------------------
        # Clean string fields
        # ----------------------------------------------------

        .withColumn(
            "transaction_id",
            trim(col("transaction_id")),
        )

        .withColumn(
            "customer_id",
            trim(col("customer_id")),
        )

        .withColumn(
            "currency",
            upper(
                trim(
                    col("currency")
                )
            ),
        )

        .withColumn(
            "merchant_name",
            trim(
                col("merchant_name")
            ),
        )

        .withColumn(
            "merchant_category",
            trim(
                col("merchant_category")
            ),
        )

        .withColumn(
            "location",
            trim(
                col("location")
            ),
        )

        .withColumn(
            "device_id",
            trim(
                col("device_id")
            ),
        )

        # ----------------------------------------------------
        # Normalize merchant category
        # ----------------------------------------------------

        .withColumn(
            "merchant_category",
            regexp_replace(
                col("merchant_category"),
                r"\s+",
                " ",
            ),
        )

        # ----------------------------------------------------
        # Transaction amount normalization
        # ----------------------------------------------------

        .withColumn(
            "amount",
            when(
                col("amount").isNull(),
                lit(0.0),
            )
            .otherwise(
                col("amount")
            ),
        )

        # ----------------------------------------------------
        # Transaction date
        # ----------------------------------------------------

        .withColumn(
            "transaction_date",
            to_date(
                col("occurred_at")
            ),
        )

        # ----------------------------------------------------
        # Date dimensions
        # ----------------------------------------------------

        .withColumn(
            "transaction_year",
            year(
                col("occurred_at")
            ),
        )

        .withColumn(
            "transaction_month",
            month(
                col("occurred_at")
            ),
        )

        .withColumn(
            "transaction_day",
            dayofmonth(
                col("occurred_at")
            ),
        )

        # ----------------------------------------------------
        # Amount classification
        # ----------------------------------------------------

        .withColumn(
            "amount_band",
            when(
                col("amount") < 1000,
                "LOW",
            )
            .when(
                col("amount") < 10000,
                "MEDIUM",
            )
            .when(
                col("amount") < 50000,
                "HIGH",
            )
            .otherwise(
                "VERY_HIGH"
            ),
        )

        # ----------------------------------------------------
        # Data quality flag
        # ----------------------------------------------------

        .withColumn(
            "data_quality_status",
            when(
                col("transaction_id").isNull(),
                "INVALID",
            )
            .when(
                col("customer_id").isNull(),
                "INVALID",
            )
            .when(
                col("amount").isNull(),
                "INVALID",
            )
            .when(
                col("amount") < 0,
                "INVALID",
            )
            .when(
                col("currency").isNull(),
                "INVALID",
            )
            .otherwise(
                "VALID"
            ),
        )

        # ----------------------------------------------------
        # Processing metadata
        # ----------------------------------------------------

        .withColumn(
            "processing_layer",
            lit("processed"),
        )
    )

    return processed


# ============================================================
# Main streaming pipeline
# ============================================================

def main():

    logger.info(
        "Starting FinSightX Spark Structured Streaming..."
    )

    spark = create_spark_session()

    # --------------------------------------------------------
    # Kafka source
    # --------------------------------------------------------

    kafka_stream = create_kafka_stream(
        spark
    )

    # --------------------------------------------------------
    # Parse events
    # --------------------------------------------------------

    transactions = parse_transaction_events(
        kafka_stream
    )

    # ========================================================
    # RAW STREAM
    # ========================================================

    raw_query = (
        transactions.writeStream
        .format("parquet")
        .outputMode("append")
        .option(
            "path",
            RAW_OUTPUT_PATH,
        )
        .option(
            "checkpointLocation",
            RAW_CHECKPOINT_PATH,
        )
        .trigger(
            processingTime="10 seconds"
        )
        .start()
    )

    logger.info(
        "Raw streaming pipeline started."
    )

    logger.info(
        "Raw Parquet path: %s",
        RAW_OUTPUT_PATH,
    )

    logger.info(
        "Raw checkpoint path: %s",
        RAW_CHECKPOINT_PATH,
    )

    # ========================================================
    # PROCESSED STREAM
    # ========================================================

    processed_transactions = create_processed_stream(
        transactions
    )

    processed_query = (
        processed_transactions.writeStream
        .format("parquet")
        .outputMode("append")
        .option(
            "path",
            PROCESSED_OUTPUT_PATH,
        )
        .option(
            "checkpointLocation",
            PROCESSED_CHECKPOINT_PATH,
        )
        .partitionBy(
            "transaction_year",
            "transaction_month",
            "transaction_day",
        )
        .trigger(
            processingTime="10 seconds"
        )
        .start()
    )

    logger.info(
        "Processed streaming pipeline started."
    )

    logger.info(
        "Processed Parquet path: %s",
        PROCESSED_OUTPUT_PATH,
    )

    logger.info(
        "Processed checkpoint path: %s",
        PROCESSED_CHECKPOINT_PATH,
    )

    logger.info(
        "FinSightX raw + processed streaming pipelines are running."
    )

    # --------------------------------------------------------
    # Keep both streaming queries alive.
    # --------------------------------------------------------

    spark.streams.awaitAnyTermination()


# ============================================================
# Application entry point
# ============================================================

if __name__ == "__main__":
    main()