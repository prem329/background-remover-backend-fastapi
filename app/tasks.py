from rembg import remove
from app.redis_client import redis_client
from app.logger import logger
import os

from app.celery_app import celery_app

from app.db.database import SessionLocal
from app.db.crud import update_image_job_status
from app.db.models import Image

from app.code.config import MEDIA_DIR


@celery_app.task(name="app.tasks.process_image_task")
def process_image_task(original_path, processed_path, job_id):
    db = SessionLocal()
    try:
        os.makedirs(os.path.dirname(processed_path), exist_ok=True)

        with open(original_path, "rb") as f:
            input_bytes = f.read()

        output_bytes = remove(input_bytes)

        with open(processed_path, "wb") as f:
            f.write(output_bytes)

        image = db.query(Image).filter(Image.job_id == job_id).first()
        if image:
            image.status = "completed"
            image.processed_path = processed_path
            db.commit()

        redis_client.set(job_id, "completed")

    except Exception as e:
        image = db.query(Image).filter(Image.job_id == job_id).first()
        if image:
            image.status = "failed"
            db.commit()
        redis_client.set(job_id, "failed")
        raise e
    finally:
        db.close()
