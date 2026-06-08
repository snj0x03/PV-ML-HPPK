import os
import io
import base64
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from PIL import Image

from ultralytics import YOLO
from database import (
    SessionLocal, Part, DetectionLog, DetectionFeedback, BoundingBox,
    init_db, clear_detection_history,
)

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "best_v11.pt")

model = YOLO(MODEL_PATH)

IMAGES_DIR = os.path.join(BASE_DIR, "data", "detection_images")
os.makedirs(IMAGES_DIR, exist_ok=True)


def save_result_image(img: Image.Image, original_filename: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    safe_name = os.path.splitext(os.path.basename(original_filename))[0][:40]
    filename = f"{ts}_{uid}_{safe_name}.jpg"
    path = os.path.join(IMAGES_DIR, filename)
    img.save(path, format="JPEG")
    return path


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalysisResult(BaseModel):
    detection_id: int
    part_name: str
    serial_number: str
    confidence: float
    message: str
    image_base64: str


class FeedbackRequest(BaseModel):
    detection_id: int
    is_correct: bool
    comment: str | None = None


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def main_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/predict", response_model=AnalysisResult)
async def predict_part(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"[predict] request: {file.filename}")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        results = model(image, conf=0.01)
        result = results[0]

        if len(result.boxes) > 0:
            plotted_bgr = result.plot()
            plotted_rgb = Image.fromarray(plotted_bgr[..., ::-1])
            buf = io.BytesIO()
            plotted_rgb.save(buf, format="JPEG")
            img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

            saved_path = save_result_image(Image.fromarray(plotted_bgr[..., ::-1]), file.filename)

            # top-1 box (highest confidence — YOLO returns sorted by conf desc)
            best_box = result.boxes[0]
            class_id   = int(best_box.cls[0].item())
            confidence = float(best_box.conf[0].item())

            part_info = db.query(Part).filter(Part.class_id == class_id).first()

            log = DetectionLog(
                image_filename=file.filename,
                class_id=class_id,
                confidence=round(confidence, 4),
                part_id=part_info.id if part_info else None,
                result_image_path=saved_path,
            )
            db.add(log)
            db.flush()  # get log.id before committing

            xywhn = result.boxes.xywhn.cpu().numpy()
            cls   = result.boxes.cls.cpu().numpy()
            conf  = result.boxes.conf.cpu().numpy()
            for i in range(len(result.boxes)):
                db.add(BoundingBox(
                    detection_log_id=log.id,
                    class_id=int(cls[i]),
                    confidence=round(float(conf[i]), 4),
                    x_center=float(xywhn[i][0]),
                    y_center=float(xywhn[i][1]),
                    width=float(xywhn[i][2]),
                    height=float(xywhn[i][3]),
                ))

            db.commit()
            db.refresh(log)

            if part_info:
                return AnalysisResult(
                    detection_id=log.id,
                    part_name=part_info.part_name,
                    serial_number=part_info.serial_number or "N/A",
                    confidence=round(confidence, 4),
                    message="Part identified successfully.",
                    image_base64=img_str,
                )
            else:
                return AnalysisResult(
                    detection_id=log.id,
                    part_name=f"Unregistered Part (Class {class_id})",
                    serial_number="N/A",
                    confidence=round(confidence, 4),
                    message="Part detected but not found in the database.",
                    image_base64=img_str,
                )
        else:
            saved_path = save_result_image(image, file.filename)

            log = DetectionLog(
                image_filename=file.filename,
                class_id=None,
                confidence=0.0,
                part_id=None,
                result_image_path=saved_path,
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            return AnalysisResult(
                detection_id=log.id,
                part_name="Unknown",
                serial_number="N/A",
                confidence=0.0,
                message="No part detected in the image.",
                image_base64=img_str,
            )

    except Exception as e:
        print(f"[predict] error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/feedback")
async def submit_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    log = db.query(DetectionLog).filter(DetectionLog.id == body.detection_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Detection log not found.")

    feedback = DetectionFeedback(
        detection_log_id=body.detection_id,
        is_correct=body.is_correct,
        comment=body.comment,
    )
    db.add(feedback)
    db.commit()

    return {"message": "Feedback saved.", "feedback_id": feedback.id}


@app.delete("/admin/clear-db")
async def clear_db(db: Session = Depends(get_db)):
    """Clear all detection history (logs, bounding boxes, feedbacks) and saved result images. Parts are preserved."""
    clear_detection_history(db)

    deleted_files = 0
    for filename in os.listdir(IMAGES_DIR):
        filepath = os.path.join(IMAGES_DIR, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
            deleted_files += 1

    return {"message": f"Detection history cleared. {deleted_files} result image(s) deleted. Parts are preserved."}
