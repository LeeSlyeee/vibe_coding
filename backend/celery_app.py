from celery import Celery
from config import Config

def make_celery(app_name=__name__):
    """
    Create and configure a Celery instance.
    This instance will be used by both the Flask app (client) 
    and the Celery worker (consumer).
    """
    
    # Initialize Celery
    celery = Celery(
        app_name,
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=['tasks'] # Load tasks from tasks.py
    )
    
    # Configure Celery
    celery.conf.update(
        result_expires=3600,
        enable_utc=False,
        timezone='Asia/Seoul',
    )

    return celery

# Create a global Celery instance (used by the worker process)
celery_app = make_celery()
