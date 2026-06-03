FROM ultralytics/ultralytics:latest

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /workspace/app/
COPY models/ /workspace/models/

WORKDIR /workspace/app

# DB 시딩 후 서버 자동 시작
CMD ["sh", "-c", "python seed_db.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
