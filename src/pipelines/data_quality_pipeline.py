import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from src.utils.config import PROCESSED_DATA_PATH


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailDataQualityPipeline")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    bronze_path = os.path.join(PROCESSED_DATA_PATH, "bronze_orders")
    silver_path = os.path.join(PROCESSED_DATA_PATH, "silver_orders")
    quality_path = os.path.join(PROCESSED_DATA_PATH, "quality", "pipeline_metrics")

    bronze_df = spark.read.format("delta").load(bronze_path)
    silver_df = spark.read.format("delta").load(silver_path)

    bronze_count = bronze_df.count()
    silver_count = silver_df.count()
    duplicate_count = bronze_count - silver_count

    null_order_id = bronze_df.filter("order_id IS NULL").count()
    null_user_id = bronze_df.filter("user_id IS NULL").count()
    null_product_id = bronze_df.filter("product_id IS NULL").count()

    status = "SUCCESS" if silver_count > 0 and null_order_id == 0 else "FAILED"

    metrics = [
        ("bronze_record_count", bronze_count),
        ("silver_record_count", silver_count),
        ("duplicate_record_count", duplicate_count),
        ("null_order_id_count", null_order_id),
        ("null_user_id_count", null_user_id),
        ("null_product_id_count", null_product_id),
    ]

    metrics_df = spark.createDataFrame(metrics, ["metric_name", "metric_value"])

    metrics_df = (
        metrics_df
        .withColumn("pipeline_name", lit("retail_intelligence_platform"))
        .withColumn("pipeline_layer", lit("bronze_to_silver"))
        .withColumn("quality_status", lit(status))
        .withColumn("created_at", lit(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    )

    metrics_df.write.format("delta").mode("overwrite").save(quality_path)

    print("Data quality pipeline completed.")
    print(f"Quality metrics written to: {quality_path}")
    metrics_df.show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()