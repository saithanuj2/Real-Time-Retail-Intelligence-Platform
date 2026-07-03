import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    DoubleType,
)

from src.utils.config import (
    KAFKA_TOPIC,
    PROCESSED_DATA_PATH,
)

KAFKA_BOOTSTRAP_SERVERS = "retail_kafka:29092"


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailBronzeStreamingPipeline")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    order_schema = StructType([
        StructField("order_id", IntegerType(), True),
        StructField("user_id", IntegerType(), True),
        StructField("product_id", IntegerType(), True),
        StructField("order_number", IntegerType(), True),
        StructField("order_dow", IntegerType(), True),
        StructField("order_hour_of_day", IntegerType(), True),
        StructField("days_since_prior_order", DoubleType(), True),
        StructField("add_to_cart_order", IntegerType(), True),
        StructField("reordered", IntegerType(), True),
    ])

    print("=" * 60)
    print("Kafka Bootstrap:", KAFKA_BOOTSTRAP_SERVERS)
    print("Kafka Topic:", KAFKA_TOPIC)
    print("=" * 60)

    kafka_stream_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    bronze_df = (
        kafka_stream_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(from_json(col("json_value"), order_schema).alias("data"))
        .select("data.*")
        .withColumn("ingestion_timestamp", current_timestamp())
    )

    bronze_output_path = os.path.join(PROCESSED_DATA_PATH, "bronze_orders")
    checkpoint_path = os.path.join(PROCESSED_DATA_PATH, "checkpoints", "bronze_orders")

    query = (
        bronze_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("path", bronze_output_path)
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime="10 seconds")
        .start()
    )

    print("Bronze streaming pipeline started...")
    print(f"Writing Bronze Delta data to: {bronze_output_path}")

    query.awaitTermination()


if __name__ == "__main__":
    main()