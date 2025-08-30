import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv(".env")

celery_app = Celery("tasks")
celery_app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")

celery_app.autodiscover_tasks(['workers'])