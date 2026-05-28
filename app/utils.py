import io
import os
from PIL import Image
from ultralytics import YOLO

# 현재 파일 위치 기준으로 모델 경로 지정 (서버 켤 때 한 번만 로드)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")

# AI 모델 로드 (메모리에 상주)
model = YOLO(MODEL_PATH)

def process_and_predict(file_content: bytes):
    """
    바이너리 이미지를 받아 AI 추론을 돌리고,
    예측 결과와 사각형(BBox)이 그려진 이미지를 반환합니다.
    """
    # 1. 바이트 데이터를 PIL 이미지로 변환
    image = Image.open(io.BytesIO(file_content))
    
    # 2. AI 모델 추론 시작
    results = model(image)[0]
    
    # 3. 결과 데이터 추출
    detected_key = "unknown"
    confidence = 0.0
    
    # 무언가 검출되었다면 가장 확실한 첫 번째 객체 정보 가져오기
    if len(results.boxes) > 0:
        box = results.boxes[0]
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        
        # 모델 팀이 정의한 클래스 이름 리스트에서 매핑 (예: 0번 -> part1)
        detected_key = f"part{class_id + 1}" 

    # 4. [중요] 이미지 위에 BBox 사각형 그리기
    # results.plot()은 BBox가 그려진 이미지의 numpy 배열을 반환합니다.
    plotted_array = results.plot()
    output_image = Image.fromarray(plotted_array[..., ::-1]) # BGR을 RGB로 변환
    
    # 5. 그려진 이미지를 다시 브라우저로 보낼 수 있게 바이트로 변환
    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    return detected_key, confidence, img_bytes