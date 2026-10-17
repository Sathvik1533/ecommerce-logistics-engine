"""
Asynchronous background tasks executed by Celery workers.

Architectural Notice:
Tasks handle post-transaction work dispatched after order creation & inventory reservation,
such as third-party webhook dispatches, notification delivery, or cross-system warehouse
integrations.
"""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_order_confirmation_task(self, order_reference: str) -> dict[str, str]:
    """
    Asynchronously delivers customer notification and publishes external order event.
    """
    logger.info("Starting order confirmation task for reference: %s", order_reference)
    # TODO [Engineer Implementation]:
    # 1. Fetch order details from DB or payload.
    # 2. Integrate with email/SMS provider or outbound webhook.
    # 3. Handle transient errors with exponential backoff (`self.retry(...)`).
    return {"status": "SUCCESS", "order_reference": order_reference}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def initiate_fulfillment_pipeline_task(self, order_reference: str) -> dict[str, str]:
    """
    Triggers downstream warehouse management system (WMS) routing and label generation.
    """
    logger.info("Initiating fulfillment pipeline for reference: %s", order_reference)
    # TODO [Engineer Implementation]:
    # 1. Coordinate with warehouse fulfillment API.
    # 2. Transition stock allocation from RESERVED to COMMITTED upon warehouse acceptance.
    return {"status": "PENDING_DISPATCH", "order_reference": order_reference}
