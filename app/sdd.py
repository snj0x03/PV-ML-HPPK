# sdd.py 예시 코드
from ultralytics import YOLO

# 💡 모델 파일(.pt)의 경로를 우리가 방금 배치한 위치로 지정합니다!
model_path = "models/best.pt"

print(f"🔄 AI 모델을 로드 중입니다: {model_path}")
model = YOLO(model_path)
print("✅ AI 모델 로드 완료! 이제 부품을 탐지할 준비가 되었습니다.")

def predict_parts(image_path):
    # 이 함수를 호출하면 AI가 이미지 속 프린터 부품을 찾아내고 model_number를 매칭하게 됩니다.
    results = model(image_path)
    return results