import os

from pyspark.sql import SparkSession
from src.utils.config import PROCESSED_DATA_PATH, BASE_DIR


def create_spark_session():
    return (
        SparkSession.builder
        .appName("RetailExportToCSV")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def export_delta_to_csv(spark, input_path, output_path):
    (
        spark.read.format("delta").load(input_path)
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(output_path)
    )


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    exports_path = os.path.join(BASE_DIR, "data", "exports")

    tables = {
        "product_metrics": os.path.join(PROCESSED_DATA_PATH, "gold", "product_metrics"),
        "customer_metrics": os.path.join(PROCESSED_DATA_PATH, "gold", "customer_metrics"),
        "hourly_metrics": os.path.join(PROCESSED_DATA_PATH, "gold", "hourly_metrics"),
        "pipeline_quality_metrics": os.path.join(PROCESSED_DATA_PATH, "quality", "pipeline_metrics"),
    }

    for table_name, input_path in tables.items():
        output_path = os.path.join(exports_path, table_name)
        export_delta_to_csv(spark, input_path, output_path)
        print(f"Exported {table_name} to {output_path}")

    print("CSV export completed successfully.")
    spark.stop()


if __name__ == "__main__":
    main()