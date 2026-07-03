import os

from pyspark.sql import SparkSession

from src.utils.config import PROCESSED_DATA_PATH


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailPipelineValidation")
        .config(
            "spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension"
        )
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
        .getOrCreate()
    )


def print_table_stats(name, path, spark):
    print("=" * 70)
    print(f"{name}")
    print("=" * 70)

    df = spark.read.format("delta").load(path)

    print(f"Rows    : {df.count()}")
    print(f"Columns : {len(df.columns)}")

    df.printSchema()

    print("\nSample Records")
    df.show(5, truncate=False)
    print()


def main():

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    bronze_path = os.path.join(PROCESSED_DATA_PATH, "bronze_orders")
    silver_path = os.path.join(PROCESSED_DATA_PATH, "silver_orders")

    gold_product = os.path.join(
        PROCESSED_DATA_PATH,
        "gold",
        "product_metrics",
    )

    gold_customer = os.path.join(
        PROCESSED_DATA_PATH,
        "gold",
        "customer_metrics",
    )

    gold_hourly = os.path.join(
        PROCESSED_DATA_PATH,
        "gold",
        "hourly_metrics",
    )

    print("\nRETAIL LAKEHOUSE VALIDATION\n")

    print_table_stats("BRONZE", bronze_path, spark)
    print_table_stats("SILVER", silver_path, spark)
    print_table_stats("GOLD - PRODUCT", gold_product, spark)
    print_table_stats("GOLD - CUSTOMER", gold_customer, spark)
    print_table_stats("GOLD - HOURLY", gold_hourly, spark)

    print("=" * 70)
    print("ALL PIPELINES VALIDATED SUCCESSFULLY")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()