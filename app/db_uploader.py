import os
from database import SessionLocal, init_db, Part, Image, BoundingBox

def upload_yolo_data(target_dir: str):
    db = SessionLocal()
    
    images_dir = os.path.join(target_dir, "images")
    labels_dir = os.path.join(target_dir, "labels")
    
    if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
        print(f"❌ 에러: {target_dir} 내부에 images 또는 labels 폴더가 없습니다.")
        db.close()
        return

    print(f"📂 YOLO v8 데이터 업로드 시작 점검 완료. 대상 폴더: {target_dir}")

    # 이미지 파일 목록 가져오기
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    uploaded_count = 0
    
    for file_name in image_files:
        image_path = os.path.join(images_dir, file_name)
        
        # 1. 중복 등록 방지
        existing_img = db.query(Image).filter(Image.file_path == image_path).first()
        if existing_img:
            continue
            
        # 2. 로보플로우 증강 여부 판별
        is_aug = any(keyword in file_name for keyword in ['_aug', 'mixup', 'mosaic'])
        
        # 3. 짝꿍 텍스트 라벨 파일 찾기
        base_name = os.path.splitext(file_name)[0]
        label_file_name = f"{base_name}.txt"
        label_path = os.path.join(labels_dir, label_file_name)
        
        if not os.path.exists(label_path):
            continue
            
        # 4. 라벨 파일 읽기
        with open(label_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if not lines:
            continue
            
        # 5. 첫 번째 줄의 Class ID로 부품 장부 매핑
        first_line = lines[0].strip().split()
        if not first_line:
            continue
            
        class_id = int(first_line[0])
        part_name = f"YOLO_Class_{class_id}"
        
        # 부품이 없으면 새로 만듭니다 (serial_number=None 기본 설정으로 에러 원천 차단)
        part = db.query(Part).filter(Part.part_name == part_name).first()
        if not part:
            part = Part(
                part_name=part_name,  
                serial_number="미지정"
            )
            db.add(part)
            db.flush()

        # 6. 이미지 등록
        db_image = Image(
            part_id=part.id,
            file_path=image_path,
            is_augmented=is_aug
        )
        db.add(db_image)
        db.flush()

        # 7. 바운딩 박스들 등록
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
                
            _, cx, cy, w, h = map(float, parts)
            
            db_bbox = BoundingBox(
                image_id=db_image.id,
                x_center=cx,
                y_center=cy,
                width=w,
                height=h
            )
            db.add(db_bbox)
        
        uploaded_count += 1

    db.commit()
    db.close()
    print(f"\n🎉 [성공] 총 {uploaded_count}장의 이미지와 바운딩 박스를 데이터베이스에 완벽히 등록했습니다!")

if __name__ == "__main__":
    # 💡 항상 최신 완벽한 구조의 깨끗한 DB 파일을 먼저 생성합니다.
    init_db()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 로보플로우 데이터가 저장된 진짜 train 폴더 위치 고정
    TARGET_DIRECTORY = os.path.join(current_dir, "roboflow_data", "train")
    
    if not os.path.exists(TARGET_DIRECTORY):
        print("\n" + "="*60)
        print("❌ [경로 경고] 로보플로우 데이터 폴더를 찾을 수 없습니다!")
        print(f"현재 코드가 바라보는 주소: {TARGET_DIRECTORY}")
        print("프로젝트 폴더 안에 roboflow_data 폴더를 만들고 그 안에 train 폴더를 넣어주세요.")
        print("="*60 + "\n")
    else:
        upload_yolo_data(TARGET_DIRECTORY)