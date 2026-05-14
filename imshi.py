 if part_key in predict_db:
        info = predict_db[part_key]
        return AnalysisResult(
            part_name=info["name"],
            serial_number=info["serial"],
            confidence=1.0, # 직접 지정했으므로 확신도 100%
            message="테스트 모드: 지정하신 부품 정보입니다."