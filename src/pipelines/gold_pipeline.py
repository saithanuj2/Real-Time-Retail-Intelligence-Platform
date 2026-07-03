import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, countDistinct, sum as spark_sum, round

from src.utils.config import PROCESSED_DATA_PATH


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailGoldPipeline")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    silver_path = os.path.join(PROCESSED_DATA_PATH, "silver_orders")
    gold_base_path = os.path.join(PROCESSED_DATA_PATH, "gold")

    silver_df = spark.read.format("delta").load(silver_path)

    product_metrics = (
        silver_df
        .groupBy("product_id")
        .agg(
            countDistinct("order_id").alias("total_orders"),
            countDistinct("user_id").alias("unique_users"),
            spark_sum("reordered").alias("total_reorders"),
            count("*").alias("total_product_events"),
        )
        .withColumn(
            "reorder_rate",
            round(col("total_reorders") / col("total_product_events"), 4)
        )
    )

    customer_metrics = (
        silver_df
        .groupBy("user_id")
        .agg(
            countDistinct("order_id").alias("total_orders"),
            count("*").alias("total_products"),
            spark_sum("reordered").alias("total_reorders"),
        )
        .withColumn(
            "avg_cart_size",
            round(col("total_products") / col("total_orders"), 2)
        )
        .withColumn(
            "reorder_rate",
            round(col("total_reorders") / col("total_products"), 4)
        )
    )

    hourly_metrics = (
        silver_df
        .groupBy("order_hour_of_day")
        .agg(
            countDistinct("order_id").alias("total_orders"),
            count("*").alias("total_products"),
            spark_sum("reordered").alias("total_reorders"),
            countDistinct("user_id").alias("unique_users"),
        )
        .withColumn(
            "reorder_rate",
            round(col("total_reorders") / col("total_products"), 4)
        )
        .orderBy("order_hour_of_day")
    )

    product_metrics.write.format("delta").mode("overwrite").save(
        os.path.join(gold_base_path, "product_metrics")
    )

    customer_metrics.write.format("delta").mode("overwrite").save(
        os.path.join(gold_base_path, "customer_metrics")
    )

    hourly_metrics.write.format("delta").mode("overwrite").save(
        os.path.join(gold_base_path, "hourly_metrics")
    )

    print("Gold pipeline completed.")
    print("Gold tables written:")
    print(f"- {os.path.join(gold_base_path, 'product_metrics')}")
    print(f"- {os.path.join(gold_base_path, 'customer_metrics')}")
    print(f"- {os.path.join(gold_base_path, 'hourly_metrics')}")


if __name__ == "__main__":
    main()