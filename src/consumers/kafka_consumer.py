import json
from kafka import KafkaConsumer

from src.utils.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Retail Kafka Consumer started")

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="retail-intelligence-consumer-group",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        key_deserializer=lambda key: key.decode("utf-8") if key else None
    )

    message_count = 0

    for message in consumer:
        message_count += 1

        logger.info(
            f"Message {message_count} | "
            f"Partition: {message.partition} | "
            f"Offset: {message.offset} | "
            f"Key: {message.key} | "
            f"Value: {message.value}"
        )

        if message_count >= 10:
            break

    consumer.close()
    logger.info("Retail Kafka Consumer finished")


if __name__ == "__main__":
    main()