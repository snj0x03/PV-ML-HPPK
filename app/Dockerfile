# 1. AI 팀원이 YOLO v8을 학습시킬 수 있도록 공식 GPU 지원 환경을 베이스로 가져옵니다.
FROM ultralytics/ultralytics:latest

# 2. 컨테이너 내부의 기본 작업 디렉토리(폴더)를 설정합니다.
WORKDIR /app

# 3. 파이썬 패키지 설치를 위해 requirements.txt 파일을 먼저 복사합니다.
# (SQLAlchemy, PyMySQL 등이 적힌 파일입니다)
COPY requirements.txt /app/

# 4. 필수 파이썬 패키지들을 컨테이너 내부에 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# 5. 현재 내 프로젝트 폴더의 모든 소스코드와 데이터셋을 도커 컴퓨터 안으로 복사합니다.
COPY . /app

# 6. 컨테이너가 켜졌을 때 기본적으로 실행될 명령어를 지정합니다.
CMD ["bash"]