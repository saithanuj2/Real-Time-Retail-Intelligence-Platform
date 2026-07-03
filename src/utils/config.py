import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

# =============================================================================
# DATA PATHS
# =============================================================================

RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")
EXPORT_PATH = os.path.join(BASE_DIR, "data", "exports")

# =============================================================================
# INPUT FILES
# =============================================================================

ORDERS_FILE = os.path.join(RAW_DATA_PATH, "orders.csv")
ORDER_PRODUCTS_FILE = os.path.join(RAW_DATA_PATH, "order_products__prior.csv")
PRODUCTS_FILE = os.path.join(RAW_DATA_PATH, "products.csv")
AISLES_FILE = os.path.join(RAW_DATA_PATH, "aisles.csv")
DEPARTMENTS_FILE = os.path.join(RAW_DATA_PATH, "departments.csv")

# =============================================================================
# KAFKA
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

KAFKA_TOPIC = "retail_orders"

# =============================================================================
# SPARK
# =============================================================================

SPARK_MASTER = "spark://spark-master:7077"

CHECKPOINT_PATH = os.path.join(
    PROCESSED_DATA_PATH,
    "checkpoints"
)

# =============================================================================
# STREAMING
# =============================================================================

BATCH_SIZE = 500

STREAM_DELAY = 0.001

STREAM_RECORD_LIMIT = 100000