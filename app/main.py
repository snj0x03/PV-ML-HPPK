
import os
import io
import torch
import base64  # 💡 이미지를 텍스트로 변환하기 위해 추가
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from PIL import Image

from ultralytics import YOLO
from database import SessionLocal, Part

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 무적의 프로젝트 최상위 절대 경로 계산 (이사 가도 안 터짐)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "best.pt")

model = YOLO(MODEL_PATH)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 💡 응답 규격에 바운딩 박스가 그려진 이미지 칸(image_base64)을 추가합니다!
class AnalysisResult(BaseModel):
    part_name: str
    serial_number: str
    model_number: str
    confidence: float
    message: str
    image_base64: str  # 👈 프론트엔드에서 바로 <img src="...">로 띄울 수 있는 데이터

@app.get("/")
async def main_page():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.post("/predict", response_model=AnalysisResult)
async def predict_part(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"📸 AI 분석 및 시각화 요청 수신: {file.filename}")
    
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        results = model(image, conf=0.01)
        result = results[0]
        
        # 🟢 기본값으로 원본 이미지를 Base64로 인코딩해둡니다 (못 찾았을 때를 대비)
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        if len(result.boxes) > 0:
            # 🎯 1. YOLO가 바운딩 박스를 그린 가상 이미지를 가져옵니다! (OpenCV BGR 배열 형태)
            plotted_img_bgr = result.plot() 
            
            # 🎯 2. OpenCV 형태를 파이썬 이미지 객체(PIL)로 바꾼 뒤 RGB로 정렬합니다.
            plotted_img_rgb = Image.fromarray(plotted_img_bgr[..., ::-1]) 
            
            # 🎯 3. 그려진 이미지를 메모리 버퍼에 JPEG로 세이브합니다.
            buffered_plot = io.BytesIO()
            plotted_img_rgb.save(buffered_plot, format="JPEG")
            
            # 🎯 4. 최종적으로 프론트엔드가 알아들을 수 있는 문자열로 변환(Encoding)합니다.
            img_str = base64.b64encode(buffered_plot.getvalue()).decode("utf-8")
            
            # 가장 신뢰도 높은 첫 번째 부품 정보 추출
            best_box = result.boxes[0]
            class_id = int(best_box.cls[0].item())
            confidence = float(best_box.conf[0].item())
            
            temp_db_name = f"YOLO_Class_{class_id}"
            part_info = db.query(Part).filter(Part.part_name == temp_db_name).first()
            
            if part_info:
                return AnalysisResult(
                    part_name=part_info.part_name,
                    serial_number=part_info.serial_number,
                    model_number=part_info.model_number,
                    confidence=round(confidence, 4),
                    message="AI 부품 식별 및 바운딩 박스 시각화 완료!",
                    image_base64=img_str  # 👈 박스가 그려진 이미지 전달
                )
            else:
                return AnalysisResult(
                    part_name=f"YOLO_Class_{class_id} (DB 미등록)",
                    serial_number="N/A",
                    model_number="N/A",
                    confidence=round(confidence, 4),
                    message="AI가 부품 박스는 쳤으나 DB에 상세 정보가 없습니다.",
                    image_base64=img_str
                )
        else:
            return AnalysisResult(
                part_name="Unknown",
                serial_number="N/A",
                model_number="N/A",
                confidence=0.0,
                message="사진에서 부품을 발견하지 못해 박스를 그리지 못했습니다.",
                image_base64=img_str  # 원본 이미지 전달
            )
            
    except Exception as e:
        print(f"🚨 에러 발생: {str(e)}")
        return AnalysisResult(
            part_name="Error", serial_number="Error", model_number="Error",
            confidence=0.0, message=f"처리 중 오류 발생: {str(e)}", image_base64=""
        )