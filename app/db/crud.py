from sqlalchemy.orm import Session
from app.db.models import User
from app.db.models import Image

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, hashed_password: str):
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_image_job(
    db: Session,
    job_id: str,
    user_id: int,
    original_path: str
):
    job = Image(
        job_id=job_id,
        user_id=user_id,
        original_path=original_path,
        status="processing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_image_job_status(
    db: Session,
    job_id: str,
    status: str,
    output_path: str | None = None
):
    job = db.query(Image).filter(Image.job_id == job_id).first()
    if not job:
        return None

    job.status = status
    if output_path:
        job.output_path = output_path

    db.commit()
    return job


def get_user_image_jobs(db: Session, user_id: int):
    return db.query(Image).filter(Image.user_id == user_id).all()


def get_job_for_user(db: Session, job_id: str, user_id: int):
    return (
        db.query(Image)
        .filter(
            Image.job_id == job_id,
            Image.user_id == user_id
        )
        .first()
    )



