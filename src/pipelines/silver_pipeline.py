import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from src.utils.config import PROCESSED_DATA_PATH


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailSilverPipeline")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    bronze_path = os.path.join(PROCESSED_DATA_PATH, "bronze_orders")
    silver_path = os.path.join(PROCESSED_DATA_PATH, "silver_orders")

    bronze_df = spark.read.format("delta").load(bronze_path)

    silver_df = (
        bronze_df
        .dropDuplicates(["order_id", "product_id", "add_to_cart_order"])
        .filter(col("order_id").isNotNull())
        .filter(col("user_id").isNotNull())
        .filter(col("product_id").isNotNull())
        .filter(col("order_number") > 0)
        .filter((col("order_dow") >= 0) & (col("order_dow") <= 6))
        .filter((col("order_hour_of_day") >= 0) & (col("order_hour_of_day") <= 23))
        .filter(col("add_to_cart_order") > 0)
        .filter((col("reordered") == 0) | (col("reordered") == 1))
        .withColumn("silver_processed_timestamp", current_timestamp())
    )

    silver_df.write.format("delta").mode("overwrite").save(silver_path)

    print("Silver pipeline completed.")
    print(f"Silver Delta data written to: {silver_path}")
    print(f"Silver record count: {silver_df.count()}")


if __name__ == "__main__":
    main()