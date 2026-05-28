from database import SessionLocal, Part

def update_printer_parts():
    db = SessionLocal()
    
    # 💡 [여기에 40개의 부품 정보를 정리하시면 됩니다!]
    # 로보플로우의 Class ID 번호와 실제 부품 정보를 매핑하는 사전입니다.
    parts_data = {
        1: {"name": "SVC_HP LaserJet Fuser 220V Kit", "serial": "5PN77-67001"},
        2: {"name": "SVC_HP LaserJet CYM Managed Imaging Drum", "serial": "W9078-67001"},
        3: {"name": "SVC_HP LaserJet Black Managed Imaging Drum", "serial": "W9077-67001"},
        4: {"name": "SVC_HP LaserJet Toner Collection Unit", "serial": "6SB85-67001"},
        5: {"name": "Waste toner duct unit", "serial": "JC96-13015A"},
        6: {"name": "SVC_HP LaserJet Trays 2-x Roller Kit", "serial": "5PN66-67001"},
        7: {"name": "SVC_HP LaserJet Yellow Developer Unit", "serial": "5PN73-67003"},
        8: {"name": "Hard disk 500GB SED", "serial": "933853-011"},
        9: {"name": "HP LaserJet ADF Maintenance Kit", "serial": "5RC00-67001"},
        10: {"name": "Main PCA (Formatter)", "serial": "6CF14-67011"},
        11: {"name": "Laser scanner unit (LSU)", "serial": "JC97-05149A"},
        12: {"name": "Control panel (10.1 inch)", "serial": "5QK42-60104"},
        13: {"name": "SVC_T2 transfer assembly", "serial": "5PN80-67002"},
        14: {"name": "Low Voltage Power Supply (LVPS), 220V", "serial": "JC44-00150C"},
        15: {"name": "High Voltage Power Supply (HVPS)", "serial": "JC44-00240C"},
        16: {"name": "SVC_HPLJ 300ipm300shtFlw DADFhighspdScnr", "serial": "5QK39-67002"},
        17: {"name": "ADF Whole Unit Kit, Valiant A3", "serial": "5QK08-67014"},
        18: {"name": "Fuser drive board (FDB), 220V", "serial": "JC44-00236C"},
        19: {"name": "SVC-Flat Cable, Faro SICB 50pin", "serial": "5QK08-67011"},
        20: {"name": "SVC-Flat Cable, Faro SICB 68pin", "serial": "5QK08-67012"},
        21: {"name": "FLAT CABLE-LSU", "serial": "5QK03-50003"},
        22: {"name": "Exit unit", "serial": "JC90-01856A"},
        23: {"name": "Right door assembly", "serial": "JC95-02247A"},
        24: {"name": "Front cover assembly", "serial": "6ER04-61001"},
        25: {"name": "Registration unit assembly", "serial": "8GS05-60128"},
        26: {"name": "Registration sensor", "serial": "0604-001381"},
        27: {"name": "Feed 2 sensor", "serial": "0604-001490"},
        28: {"name": "Fuser, Exit drive assembly", "serial": "JC93-01850A"},
        29: {"name": "Drum, ITB motor", "serial": "JC31-00123C"},
        30: {"name": "Reservoir drive motor", "serial": "JC93-01659A"},
        31: {"name": "Tray 3 empty sensor", "serial": "3SJ00-60110"},
        32: {"name": "Duplex 1 motor", "serial": "JC93-00336A"},
        33: {"name": "Toner dispense motor", "serial": "SS216-80501"},
        34: {"name": "CPR shutter motor", "serial": "JC31-00078A"},
        35: {"name": "LVPS fan", "serial": "JC31-00198A"},
        36: {"name": "FDB fan", "serial": "JC31-00154A"},
        37: {"name": "LSU fan assembly", "serial": "JC93-01019A"},
        38: {"name": "Right door switch assembly", "serial": "JC93-01467A"},
        39: {"name": "Front door switch assembly", "serial": "JC93-00466A"},
        40: {"name": "Outer environment sensor assembly", "serial": "5QJ90-40002"}
    }

    print("🔄 데이터베이스 부품 정보 업데이트를 시작합니다...")
    
    updated_count = 0
    for class_id, info in parts_data.items():
        # 장부에서 'YOLO_Class_0' 같은 임시 이름을 가진 부품을 찾습니다.
        temp_name = f"YOLO_Class_{class_id}"
        part = db.query(Part).filter(Part.part_name == temp_name).first()
        
        if part:
            try:
                # 4칸 들여쓰기 규칙이 엄격하게 지켜져야 합니다.
                part.part_name = info["name"]
                part.serial_number = info["serial"]
                updated_count += 1
                print(f"  └ ✅ [{temp_name}] ➔ 이름: {info['name']} 로 변경 완료")
            except KeyError as e:
                # try와 완전히 시작 라인이 똑같아야 합니다.
                print(f"  └ ❌ [오류 발견] Class {class_id}번 데이터에 '{e}' 키가 없거나 오타가 있습니다!")
                continue
    else:
            print(f"  └ ⚠️ 알림: DB에서 {temp_name} 부품을 찾을 수 없습니다.")

    # 최종 장부 저장 및 닫기
    db.commit()
    db.close()
    print(f"\n🎉 성공: 총 {updated_count}개 부품의 이름, 시리얼넘버 업데이트 완료!")

if __name__ == "__main__":
    update_printer_parts()