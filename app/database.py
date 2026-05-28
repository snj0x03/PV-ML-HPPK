import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 💡 절대 경로 고정: 어디서 실행하든 이 파일(database.py)이 있는 폴더에 DB 파일을 만듭니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "printer_parts.db")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. 부품 테이블 (에러 원인이던 serial_number 완벽 반영)
class Part(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String(100), unique=True, nullable=False)
    serial_number = Column(String(100), nullable=True) # 👈 에러 해결의 핵심 칸!

    images = relationship("Image", back_populates="part")

# 2. 이미지 테이블
class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    is_augmented = Column(Boolean, default=False)

    part = relationship("Part", back_populates="images")
    bounding_boxes = relationship("BoundingBox", back_populates="image", cascade="all, delete-orphan")

# 3. 바운딩 박스 테이블 (YOLO 비율 좌표 저장)
class BoundingBox(Base):
    __tablename__ = "bounding_boxes"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    x_center = Column(Float, nullable=False)
    y_center = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)

    image = relationship("Image", back_populates="bounding_boxes")

def init_db():
    """새로운 구조로 깨끗한 데이터베이스 파일을 생성하는 함수"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ 데이터베이스 파일 생성 완료! 위치: {DB_PATH}")

if __name__ == "__main__":
    init_db()