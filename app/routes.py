from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import uuid
import os

from app.redis_client import redis_client
from app.tasks import process_image_task
from app.auth.dependencies import get_current_user
from app.logger import logger

from app.db.crud import create_image_job, get_job_for_user, get_user_by_email
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.models import Image
from app.db.database import get_db
from sqlalchemy.orm import Session

from fastapi import Query
from datetime import datetime

from app.code.config import MEDIA_DIR


router = APIRouter()

import os




@router.post("/remove-bg")
async def remove_background(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, user_email)

    job_id = str(uuid.uuid4())

    base_dir = os.path.join(MEDIA_DIR, f"users/user_{user.id}")
    original_dir = os.path.join(base_dir, "original")
    processed_dir = os.path.join(base_dir, "processed")

    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    original_path = os.path.join(original_dir, f"{job_id}.png")
    processed_path = os.path.join(processed_dir, f"{job_id}.png")


    input_bytes = await file.read()
    with open(original_path, "wb") as f:
        f.write(input_bytes)

    image = Image(
        user_id=user.id,
        job_id=job_id,
        original_path=original_path,
        processed_path=processed_path,
        status="processing"
    )
    db.add(image)
    db.commit()

    redis_client.set(job_id, "processing")

    process_image_task.delay(
        original_path,
        processed_path,
        job_id
    )
    print("DB SESSION ID (remove-bg):", id(db))

    return {
        "job_id": job_id,
        "status": "queued"
    }


@router.get("/status/{job_id}")
def get_job_status(
    job_id: str,
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    image = (
        db.query(Image)
        .filter(
            Image.job_id == job_id,
            Image.user_id == user.id
        )
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="Job not found")

    status = redis_client.get(job_id)

    if status:
        return {
            "job_id": job_id,
            "status": status
        }

    return {
        "job_id": job_id,
        "status": image.status
    }


@router.get("/download/{job_id}")
def download_image(
    job_id: str,
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("=== DOWNLOAD DEBUG START ===")
    print("Job ID:", job_id)
    print("User email from token:", user_email)
    print("FastAPI CWD:", os.getcwd())
    print("This file (__file__):", __file__)
    print("DB SESSION ID (download):", id(db))


    user = get_user_by_email(db, user_email)
    print("User object:", user)
    if user:
        print("User ID:", user.id)

    job = get_job_for_user(db, job_id, user.id if user else None)
    print("Job from DB:", job)

    if not job:
        print("❌ Job NOT found in DB")
        raise HTTPException(status_code=404, detail="Image not found")

    print("Job status:", job.status)
    print("Original path from DB:", job.original_path)
    print("Processed path from DB:", job.processed_path)

    print("Original exists:", os.path.exists(job.original_path))
    print("Processed exists:", os.path.exists(job.processed_path))

    if job.processed_path:
        print("Processed dir exists:",
              os.path.exists(os.path.dirname(job.processed_path)))

    print("=== DOWNLOAD DEBUG END ===")

    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Not ready: {job.status}")

    if not os.path.exists(job.processed_path):
        raise HTTPException(status_code=404, detail="Processed file not found")

    return FileResponse(
        path=job.processed_path,
        media_type="image/png",
        filename=f"{job_id}.png"
    )


@router.get("/images")
def list_user_images(
    cursor: datetime | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    query = (
        db.query(Image)
        .filter(Image.user_id == user.id)
        .order_by(Image.created_at.desc())
    )

    if cursor:
        query = query.filter(Image.created_at < cursor)

    images = query.limit(limit + 1).all()

    has_more = len(images) > limit
    items = images[:limit]

    next_cursor = (
        items[-1].created_at.isoformat()
        if has_more else None
    )

    return {
        "items": [
            {
                "job_id": img.job_id,
                "status": img.status,
                "created_at": img.created_at,
                "download_url": f"/download/{img.job_id}"
            }
            for img in items
        ],
        "next_cursor": next_cursor,
        "has_more": has_more
    }


@router.get("/me")
def get_me(user_email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_email(db, user_email)
    return {
        "id": user.id,
        "email": user.email
    }
    
@router.delete("/images/{job_id}")
def delete_image(
    job_id: str,
    user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, user_email)

    image = (
        db.query(Image)
        .filter(Image.job_id == job_id, Image.user_id == user.id)
        .first()
    )

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    for path in [image.original_path, image.processed_path]:
        if path and os.path.exists(path):
            os.remove(path)

    db.delete(image)
    db.commit()

    return {"message": "Image deleted"}
