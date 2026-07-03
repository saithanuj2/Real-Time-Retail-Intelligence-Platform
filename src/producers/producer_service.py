import json
import time
import pandas as pd
from kafka import KafkaProducer

from src.utils.config import (
    ORDERS_FILE,
    ORDER_PRODUCTS_FILE,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    BATCH_SIZE,
    STREAM_DELAY
)

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RetailOrderProducerService:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: str(key).encode("utf-8")
        )

    def load_data(self):
        logger.info("Loading Instacart datasets...")

        orders = pd.read_csv(ORDERS_FILE)
        order_products = pd.read_csv(ORDER_PRODUCTS_FILE)

        logger.info(f"Orders loaded: {len(orders)}")
        logger.info(f"Order products loaded: {len(order_products)}")

        retail_events = order_products.merge(
            orders,
            on="order_id",
            how="inner"
        )

        logger.info(f"Merged retail events: {len(retail_events)}")

        return retail_events

    def build_event(self, row):
        return {
            "order_id": int(row["order_id"]),
            "user_id": int(row["user_id"]),
            "product_id": int(row["product_id"]),
            "order_number": int(row["order_number"]),
            "order_dow": int(row["order_dow"]),
            "order_hour_of_day": int(row["order_hour_of_day"]),
            "days_since_prior_order": (
                None
                if pd.isna(row["days_since_prior_order"])
                else float(row["days_since_prior_order"])
            ),
            "add_to_cart_order": int(row["add_to_cart_order"]),
            "reordered": int(row["reordered"])
        }

    def stream_events(self, limit=None):
        retail_events = self.load_data()

        if limit:
            retail_events = retail_events.head(limit)

        logger.info("Starting Kafka event streaming...")

        sent_count = 0

        for _, row in retail_events.iterrows():
            event = self.build_event(row)

            self.producer.send(
                topic=KAFKA_TOPIC,
                key=event["order_id"],
                value=event
            )

            sent_count += 1

            if sent_count % BATCH_SIZE == 0:
                self.producer.flush()
                logger.info(f"Streamed {sent_count} events to Kafka")

            time.sleep(STREAM_DELAY)

        self.producer.flush()
        logger.info(f"Streaming completed. Total events sent: {sent_count}")