from src.producers.producer_service import RetailOrderProducerService

from src.utils.logger import get_logger

from src.utils.config import STREAM_RECORD_LIMIT


logger = get_logger(__name__)


def main():

    logger.info("Retail Kafka Producer started")

    producer_service = RetailOrderProducerService()

    producer_service.stream_events(
        limit=STREAM_RECORD_LIMIT
    )

    logger.info("Retail Kafka Producer finished")


if __name__ == "__main__":
    main()