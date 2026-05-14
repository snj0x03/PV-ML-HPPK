
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()

# 현재 파일의 절대 경로를 파악하여 index.html 위치를 잡습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 데이터 규격 정의 (응답용)
class AnalysisResult(BaseModel):
    part_name: str
    serial_number: str
    confidence: float
    message: str

# 2. 임시 데이터베이스 (부품 일부만)
predict_db = {
    "part1": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5PN77-67001"},
    "part2": {"name": "SVC_HP LaserJet CYM Managed Imaging Drum", "serial": "W9078-67001"},
    "part3": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "W9077-67001"},
    "part4": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "6SB85-67001"},
    "part5": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC96-13015A"},
    "part6": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5PN66-67001"},
    "part7": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5PN73-67003"},
    "part8": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "933853-011"},
    "part9": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5RC00-67001"},
    "part10": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "6CF14-67011"},
    "part11": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC97-05149A"},
    "part12": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK42-60104"},
    "part13": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5PN80-67002"},
    "part14": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC44-00150C"},
    "part15": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC44-00240C"},
    "part16": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK39-67002"},
    "part17": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK08-67014"},
    "part18": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC44-00236C"},
    "part19": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK08-67011"},
    "part20": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK08-67012"},
    "part21": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5QK03-50003"},
    "part22": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC90-01856A"},
    "part23": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "JC95-02247A"},
    "part24": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "6ER04-61001"},
    "part25": {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "8GS05-60128"}
}

# 3. 메인 페이지 (HTML 서빙)
@app.get("/")
async def main_page():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# 4. 이미지 업로드 및 분석 엔드포인트
@app.post("/predict", response_model=AnalysisResult)
async def predict_part(file: UploadFile = File(...),
    # [실습] 실제로는 여기서 파일을 저장하거나 AI 모델에게 전달합니다.
    part_key: str = Form (None)):
    #프론트에서 보낸 부품 키를 받는 부분. 일단 None을 박아 두었으나, 나중에 ...으로 수정해야함
    print(f"수신된 파일: {file.filename}")
    
    filename = file.filename.lower()


    # [가짜 로직] 들어간 이름에 따라 결과가 출력되게 끔 설정.
    if "part1" in filename:
        detected_key = "part1"
    elif "part2" in filename:
        detected_key = "part2"
    elif "part3" in filename:
        detected_key = "part3"

    # 4. 결과 도출
    if detected_key and detected_key in predict_db:
        info = predict_db[detected_key]
        return AnalysisResult(
            part_name=info["name"],
            serial_number=info["serial"],
            confidence=1.0,
            message=f"파일명({filename}) 부품 식별이 끝났습니다."
        )
    else:
        return AnalysisResult(
            part_name="Unknown",
            serial_number="0000-0000",
            confidence=0.0,
            message="사진을 인식하지 못했습니다. 다른 사진을 올려주세요."
        )