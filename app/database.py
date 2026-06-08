import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "local.db")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Part(Base):
    __tablename__ = "parts"
    id            = Column(Integer, primary_key=True, index=True)
    class_id      = Column(Integer, unique=True, nullable=True, index=True)
    part_name     = Column(String(100), unique=True, nullable=False)
    serial_number = Column(String(100), nullable=True)

    detection_logs = relationship("DetectionLog", back_populates="part")


class DetectionLog(Base):
    __tablename__ = "detection_logs"
    id                = Column(Integer, primary_key=True, index=True)
    timestamp         = Column(DateTime, default=datetime.now, nullable=False)
    image_filename    = Column(String(255), nullable=True)
    class_id          = Column(Integer, nullable=True)   # top-1 detected class
    confidence        = Column(Float, nullable=False)    # top-1 confidence
    part_id           = Column(Integer, ForeignKey("parts.id"), nullable=True)
    result_image_path = Column(String(500), nullable=True)

    part           = relationship("Part", back_populates="detection_logs")
    bounding_boxes = relationship("BoundingBox", back_populates="detection_log", cascade="all, delete-orphan")
    feedbacks      = relationship("DetectionFeedback", back_populates="detection_log", cascade="all, delete-orphan")


class BoundingBox(Base):
    """All bounding boxes from a single detection (YOLO normalized xywh format)."""
    __tablename__ = "bounding_boxes"
    id               = Column(Integer, primary_key=True, index=True)
    detection_log_id = Column(Integer, ForeignKey("detection_logs.id"), nullable=False)
    class_id         = Column(Integer, nullable=False)
    confidence       = Column(Float, nullable=False)
    x_center         = Column(Float, nullable=False)
    y_center         = Column(Float, nullable=False)
    width            = Column(Float, nullable=False)
    height           = Column(Float, nullable=False)

    detection_log = relationship("DetectionLog", back_populates="bounding_boxes")


class DetectionFeedback(Base):
    __tablename__ = "detection_feedbacks"
    id               = Column(Integer, primary_key=True, index=True)
    detection_log_id = Column(Integer, ForeignKey("detection_logs.id"), nullable=False)
    is_correct       = Column(Boolean, nullable=False)
    comment          = Column(Text, nullable=True)
    timestamp        = Column(DateTime, default=datetime.now, nullable=False)

    detection_log = relationship("DetectionLog", back_populates="feedbacks")


def init_db():
    Base.metadata.create_all(bind=engine)


def clear_detection_history(db):
    """Delete all detection logs, bounding boxes, and feedbacks. Parts are preserved."""
    db.query(DetectionFeedback).delete()
    db.query(BoundingBox).delete()
    db.query(DetectionLog).delete()
    db.commit()


if __name__ == "__main__":
    init_db()
    print(f"DB initialized: {DB_PATH}")
