def mock_predict(image):
    # AI가 작동하는 척 1초 대기
    import time
    time.sleep(1) 
    # 가짜 결과 반환
    return {"part_name": "가짜 롤러", "serial": "FAKE-123", "conf": 0.99}