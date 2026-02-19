from shared.saga.worker import SagaWorker
from app.services.rabbitmq import rabbitmq_publisher
from app.core.config import settings

_saga_worker = None

def get_saga_worker() -> SagaWorker:
    global _saga_worker
    if _saga_worker is None:
        _saga_worker = SagaWorker(
            db_url=settings.db.url,
            publisher=rabbitmq_publisher,
            service_name=settings.service_name,
            poll_interval=1,
            batch_size=100
        )
    return _saga_worker