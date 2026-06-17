import os
import io
import base64
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from PIL import Image

from ultralytics import YOLO
from database import (
        SessionLocal, DetectionLog, ClassificationLog, Part,
    init_db, clear_detection_history,
)

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_DET_PATH = os.path.join(PROJECT_ROOT, "models", "best_v26_det.pt")
MODEL_CLS_PATH = os.path.join(PROJECT_ROOT, "models", "best_v26_cls.pt")

model_det = YOLO(MODEL_DET_PATH)
model_cls = YOLO(MODEL_CLS_PATH)

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


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def main_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/detect")
async def detect(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"[Predict] request: {file.filename}")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        results = model_det(image, conf=0.25)

        plotted_bgr = results[0].plot()
        plotted_rgb = Image.fromarray(plotted_bgr[..., ::-1])
        buf = io.BytesIO()
        plotted_rgb.save(buf, format="JPEG")
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

        saved_path = save_result_image(Image.fromarray(plotted_bgr[..., ::-1]), file.filename)

        bboxes = [] 
        conf = []
        classes = []
        for result in results:
            bboxes = result.boxes.xywhn.cpu().numpy().tolist()
            conf = result.boxes.conf.cpu().numpy().tolist()
            classes = result.boxes.cls.cpu().numpy().tolist()

        n = len(classes)
        srl = []
        msg = []
        send = []

        # Database Commit & Message
        for i in range(n):
            qry = db.query(Part).filter(Part.class_id == classes[i]).first()
            srl.append(qry.serial_number)
            msg.append(qry.part_desc)
            send.append({
                "class": qry.serial_number,
                "confidence": conf[i],
                "bbox": bboxes[i]
            })
                        
        log = DetectionLog(
            image_url=saved_path,
            result=send
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return {"image": img_str, "conf": conf, "cls": srl, "message": msg}

    except Exception as e:
        print(f"[predict] error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/classify")
async def classify(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"[Predict] request: {file.filename}")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        results = model_cls(image, conf=0.25)

        plotted_bgr = results[0].plot()
        plotted_rgb = Image.fromarray(plotted_bgr[..., ::-1])
        buf = io.BytesIO()
        plotted_rgb.save(buf, format="JPEG")
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

        saved_path = save_result_image(Image.fromarray(plotted_bgr[..., ::-1]), file.filename)

        conf = []
        classes = []
        for result in results:
            probs = result.probs
            conf = probs.top5conf.cpu().numpy().tolist()
            classes = [result.names[i] for i in probs.top5]


        n = len(classes)
        msg = []
        send = []

        # Database Commit & Message
        for i in range(n):
            qry = db.query(Part).filter(Part.serial_number == classes[i]).first()
            msg.append(qry.part_desc)
            send.append({
                "class": classes[i],
                "confidence": conf[i],
            })
                        
        log = ClassificationLog(
            image_url=saved_path,
            result=send
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return {"image": img_str, "conf": conf, "cls": classes, "message": msg}

    except Exception as e:
        print(f"[predict] error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

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
