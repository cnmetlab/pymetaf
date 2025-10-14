#!/usr/bin/env python
# coding: utf-8
"""测试 METAR 报文格式验证功能"""

import pytest
from pymetaf import validate_metar


class TestValidation:
    """测试 validate_metar 函数"""
    
    def test_valid_metars(self):
        """测试合法的 METAR 报文"""
        valid_metars = [
            "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
            "METAR ZBAA 310630Z 09002MPS 050V140 8000 -SHRA NSC 19/14 Q1007 NOSIG=",
            "METAR ZBAA 301630Z 00000MPS CAVOK 16/16 Q1009 NOSIG=",  # Calm wind
            "METAR RCQC 301730Z NIL=",
            "SPECI ZBHD 311029Z 30009MPS 7000 -TSRA SCT030CB BKN046 25/17 Q1007 NOSIG=",
            "METAR RCMQ 010400Z 02020G30KT 9999 VCSH SCT004 BKN014 BKN040 15/09 Q1018 NOSIG=",
            
            # TREND cases
            "METAR ZBAA 241400Z 14002MPS 090V210 9999 -TSRA SCT005 FEW033CB BKN040 25/24 Q1006 RESHRA BECMG TL1440 NSW=",
            "METAR ZBAA 310630Z 09002MPS 050V140 8000 -SHRA NSC 19/14 Q1007 TEMPO 2000 RA BR=",
            "METAR ZBAA 310630Z 09002MPS 050V140 8000 -SHRA NSC 19/14 Q1007 BECMG FM1630 TL1730 CAVOK=",
            
            # RMK cases
            "METAR RCKH 040200Z 36005KT 2200 -DZ FEW006 BKN030 OVC050 12/09 Q1025 TEMPO 3200 RMK RA AMT T=",
            "METAR RCFN 290630Z 07009KT 030V110 9999 FEW015 FEW025TCU SCT080 BKN180 31/25 Q1006 NOSIG RMK TCU SW-W A2971=",
            "METAR RCMQ 200600Z 35017KT 9999 FEW006 SCT012 BKN100 31/25 Q0999 NOSIG RMK A2952 QFF1000.5HPA=",
            "METAR RCMQ 222000Z 34003KT 0300 -RA FG VV001 15/15 Q1011 RMK A2988 RA AMT T VIS S 0300M RVR N/A=",
            "METAR RCTP 150700Z 23003KT 2000 -DZ BR SCT005 BKN008 OVC030 21/20 Q1010 NOSIG RMK RA AMT T=",
            "METAR VMMC 220000Z 20008KT 9999 3500S FU FEW002 SCT010 26/25 Q1009 NOSIG RMK RWY 34 FU=",
            
            # AUTO and missing data
            "METAR ZJSY 171900Z AUTO 12003MPS //// // ///////// 27/25 Q1006=",
            "METAR VMMC 230030Z 36017KT 330V030 6000 FEW020 BKN080 27/22 Q//// NOSIG=",  # Q//// missing data
        ]
        
        for metar in valid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"
    
    def test_invalid_qnh_format(self):
        """测试气压组格式错误"""
        invalid_metars = [
            ("METAR ZBTJ 290200Z 35009MPS CAVOK M04/M27 Q102NOSIG=", "Q102NOSIG"),
            ("METAR ZBTJ 080200Z 36010MPS CAVOK M01/M19 Q105 NOSIG=", "Q105"),
            ("METAR ZGOW 132100Z 31004MPS 7000 NSC 06/03 Q10 NOSIG=", "Q10"),
            ("METAR ZBYN 031600Z 10002MPS CAVOK 14/M03 Q101=", "Q101"),
        ]
        
        for metar, expected_field in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid QNH not detected in: {metar}"
            assert expected_field in error_msg or "QNH" in error_msg
    
    def test_invalid_time_format(self):
        """测试时间组格式错误"""
        invalid_metars = [
            ("METAR ZGSZ 551800Z AUTO 17004MPS //// // ////// 29/28 Q1004 NOSIG=", 55),  # 日期错误
            ("ZBTJ 17004MPS 5000 FU SKC 11/M02 Q1015 NOSIG=", "17004MPS"),  # 缺少时间组
            ("ZSSS 022000 14003MPS CAVOK 15/10 1014=", "022000"),  # 时间组格式异常
        ]
        
        for metar, expected in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid time format not detected in: {metar}"
    
    def test_invalid_wind_format(self):
        """测试风组格式错误"""
        invalid_metars = [
            "METAR ZBTJ 131200Z 00000PS CAVOK M04/M11 Q1028 NOSIG=",  # 00000PS错误
            "METAR ZSSS 151100Z 0003MPS 2500 HZ SKC 03/M07 Q1025 NOSIG=",  # 0003MPS错误
            "METAR ZSSS 151700Z 1003MPS 6000 SKC M01/M05 Q1027 NOSIG=",  # 1003MPS错误
        ]
        
        for metar in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid wind format not detected in: {metar}"
    
    def test_invalid_characters(self):
        """测试包含非法字符"""
        invalid_metars = [
            "METAR ZGGG 110700Z 01005MPS 340V050 8000 SCT012 9?4:30 17/14 Q1011 NOSIG=",  # ? 和 :
            "METAR ZBTJ 112300Z 00000MPS 0100 R3?0100V0350 FZFG SKC M02/M02 Q1017 NOSIG=",  # ?
            "METAR ZBTJ 230700Z 33006MPS CAVOK 14/M34 Q1016 NOSIG.=",  # .
            "METAR ZYTL 300700Z (8 4.0' :-=",  # ( . ' :
        ]
        
        for metar in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid characters not detected in: {metar}"
            assert "invalid characters" in error_msg.lower()
    
    def test_invalid_endings(self):
        """测试异常的末尾字段"""
        invalid_metars = [
            ("METAR ZGOW 140900Z 08001MPS CAVOK 14/04 Q1018 NOSI=", "NOSI"),
            ("ZSAM 280100Z VRB02MPS 9999 BKN026 OVC050 18/14 Q1016 OSIG=", "OSIG"),
            ("ZGSZ 030400Z 09003MPS 5000 -RA BR SCT010 OVC030 23/22 Q1013 NOSIG DUPE=", "DUPE"),
            ("ZLXY 112300Z 01002MPS 3000 DU SKC 17/06 Q1009 TE G=", "TE G"),
        ]
        
        for metar, expected_ending in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid ending not detected in: {metar}"
    
    def test_isolated_values(self):
        """测试孤立的数字或字符"""
        invalid_metars = [
            "METAR ZGOW 140100Z 33006MPS CAVOK 003 Q1023 NOSIG=",  # 孤立的003
            "ZLXY 050900Z 2 09005MPS CAVOK 31/27 Q1004 NOSIG=",  # 孤立数字2
        ]
        
        for metar in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Isolated value not detected in: {metar}"
    
    def test_invalid_cloud_format(self):
        """测试错误的云组格式"""
        metar = "METAR ZGGG 110500Z 35003MPS 310V030 1100 R03/P1500 -SHRA BR FEW026TCU KN026 19/17 Q1012 TEMPO 1500 SHRA SCT025CB OVC030="
        is_valid, error_msg = validate_metar(metar)
        assert not is_valid, f"Invalid cloud format (KN026) not detected"
        assert "KN026" in error_msg
    
    def test_short_text(self):
        """测试报文太短"""
        invalid_metars = [
            "ZYTX 0103=",
            "ZSSS 302OH=",
        ]
        
        for metar in invalid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Short text not detected in: {metar}"
    
    def test_nil_reports(self):
        """测试 NIL 报文"""
        valid_nil_metars = [
            "METAR RCQC 301730Z NIL=",
            "METAR RCMQ 080500Z NIL",
        ]
        
        for metar in valid_nil_metars:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid NIL METAR incorrectly identified as invalid: {metar}"
    
    def test_trend_validation(self):
        """测试趋势报验证"""
        # Valid TREND cases
        valid_trends = [
            "METAR ZBAA 241400Z 14002MPS 9999 -TSRA SCT005 Q1006 BECMG TL1440 NSW=",
            "METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 TEMPO 2000 RA BR=",
            "METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 BECMG FM1630 TL1730 CAVOK=",
            "METAR RCKH 040200Z 36005KT 2200 -DZ FEW006 Q1025 TEMPO 3200 RMK RA AMT T=",  # TEMPO with visibility only
        ]
        
        for metar in valid_trends:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid TREND METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"
        
        # Invalid TREND cases
        invalid_trends = [
            ("METAR RCMQ 250430Z 01013KT 9000 VCSH SCT003 Q1023 FM0430 8000 -RA RMK A3023 VCSH NE=", "FM without BECMG/TEMPO"),
            ("METAR ZSFZ 120400Z 04005MPS 3800 -TSRA BR BKN003 SCT020CB OVC033 21/20 Q1010 FM0530 -SHRA BKN010 FEW020CB OVC040=", "FM without BECMG/TEMPO"),
            ("METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 TEMPO R06/0800U=", "RVR in TREND"),
            ("METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 BECMG Q1012=", "QNH in TREND"),
        ]
        
        for metar, description in invalid_trends:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid TREND not detected: {metar} ({description})"
    
    def test_rmk_free_text(self):
        """测试 RMK 自由文本"""
        # Valid RMK cases - RMK is free text, various content allowed
        valid_rmk = [
            "METAR RCFN 290630Z 07009KT 9999 FEW015 Q1006 NOSIG RMK TCU SW-W A2971=",  # Direction range
            "METAR RCMQ 200600Z 35017KT 9999 FEW006 Q0999 NOSIG RMK A2952 QFF1000.5HPA=",  # QFF field
            "METAR RCMQ 222000Z 34003KT 0300 -RA FG VV001 Q1011 RMK A2988 RA AMT T VIS S 0300M RVR N/A=",  # Complex RMK
            "METAR RCTP 150700Z 23003KT 2000 -DZ BR SCT005 Q1010 NOSIG RMK RA AMT T=",  # AMT T (trace)
            "METAR VMMC 220000Z 20008KT 9999 FU FEW002 Q1009 NOSIG RMK RWY 34 FU=",  # Weather code in RMK
            "METAR RCNN 211400Z 09008KT 9999 VCSH SCT012 Q1008 NOSIG RMK A2981 CB N-NE=",  # Direction range
            "METAR RCMQ 230900Z 25008KT 9999 VCSH FEW010 Q1009 NOSIG RMK A2982 VCSH E TCU E=",  # Multiple directions
        ]
        
        for metar in valid_rmk:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid RMK METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"
        
        # Invalid: TREND in RMK (position error)
        invalid_rmk = [
            "METAR RCKH 192000Z 06004KT 6000 FEW015 Q1019 NOSIG RMK A3009 BECMG 4500 BR=",
            "METAR ZBAA 192000Z 06004KT 6000 FEW015 Q1019 NOSIG RMK A3009 TEMPO 4500 BR=",
        ]
        
        for metar in invalid_rmk:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"TREND in RMK not detected: {metar}"
            assert "TREND keyword" in error_msg and "RMK section" in error_msg
    
    def test_auto_and_missing_data(self):
        """测试 AUTO 和缺测数据"""
        valid_metars = [
            "METAR ZJSY 171900Z AUTO 12003MPS //// // ///////// 27/25 Q1006=",
            "METAR VMMC 230030Z 36017KT 330V030 6000 FEW020 BKN080 27/22 Q//// NOSIG=",
            "METAR ZYQQ 081700Z AUTO /////MPS //// // ////// M05/M07 Q1006=",
        ]
        
        for metar in valid_metars:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid AUTO/missing data METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"
    
    def test_spelling_errors(self):
        """测试拼写错误"""
        spelling_errors = [
            ("METAR VHHH 280100Z 09008KT 060V160 7000 FEW008 Q1011 EMPO 4000 SHRA=", "EMPO"),
            ("METAR ZSHC 270130Z VRB02MPS 2500 BR NSC Q1032 ECMG 3000 BR=", "ECMG"),
            ("METAR RCMQ 311200Z 16005KT 6000 -RA SCT003 Q1009 BCECMG TL1200 6000 -RA BKN016 RMK A2982=", "BCECMG"),
            ("METAR ZBYN 191330Z 00000MPS 5000 -RA BR SCT033 25/23 Q1006 TRMPO 2500 RA BR=", "TRMPO"),
            # BECMG spelling errors
            ("METAR ZSOF 172000Z 08002MPS 3500 BR NSC 11/09 Q1025 BCNG TL2100 2500=", "BCNG"),
            ("METAR ZSOF 171900Z 07002MPS 4000 BR NSC 11/09 Q1025 BECMFG TL2100 2500=", "BECMFG"),
            ("METAR ZSOF 132200Z 29002MPS 2600 BR NSC 10/07 Q1024 BECMGG TL2330 3000=", "BECMGG"),
            ("METAR ZSOF 200100Z 34002MPS 300V040 1400 R33/1400U -RA BR BKN005 OVC040 10/09 Q1022 BECMGA AT0300 1500=", "BECMGA"),
            ("METAR ZSOF 302000Z 01001MPS 3000 BR FEW046 21/21 Q1009 BGECMG TL2100 2000=", "BGECMG"),
            ("METAR ZSNJ 012200Z 07002MPS 2200 BR NSC 03/02 Q1028 BECGG TL2330 3000=", "BECGG"),
            ("METAR ZSNJ 131400Z 00000MPS 2000 R06/0900V1700N BR NSC 01/M01 Q1027 BEEMG TL1530 1400=", "BEEMG"),
            ("METAR ZSNJ 252200Z 06002MPS 1200 R24/1100N R25/1300N BR FEW006 SCT023 23/22 Q1014 BEMG TL2330 2000=", "BEMG"),
            ("METAR ZSNJ 192200Z 06001MPS 1700 R06/1000V1800U R07/P2000 BR NSC 16/16 Q1013 MECMG TL2330 3000 HZ=", "MECMG"),
            ("METAR ZSNJ 250900Z 26003MPS 3000 HZ FEW029 07/M02 Q1023 BECMF TL1030 2500=", "BECMF"),
            ("METAR ZSNJ 251000Z 24002MPS 210V280 8000 BKN010 OVC026 22/20 Q1011 BECMGM TL1130 BKN020=", "BECMGM"),
            # More BECMG spelling errors
            ("METAR ZSNB 071500Z 19005MPS 2000 +TSRA BR FEW009 BKN016 FEW033CB OVC050 24/24 Q1000 BCEMG TL1630 3000 -SHRA BR=", "BCEMG"),
            ("METAR ZSNB 122100Z VRB01MPS 4000 BR SCT033 09/06 Q1021 BCEMG TL2230 2500=", "BCEMG"),
            ("METAR ZSFZ 241800Z 33002MPS 5000 HZ NSC 19/09 Q1014 BECNG TL1930 2900=", "BECNG"),
            ("METAR ZSFZ 241700Z 02002MPS 6000 NSC 20/09 Q1014 BECNG TL1830 2900=", "BECNG"),
            ("METAR ZUGY 100700Z 03004MPS 9999 SCT010 BKN020 OVC033 21/20 Q1010 BECML TL0730 -TSRA=", "BECML"),
        ]
        
        for metar, expected_error in spelling_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Spelling error not detected: {metar}"
            assert expected_error in error_msg or "Spelling error" in error_msg
    
    def test_complex_weather_phenomena(self):
        """测试复杂天气现象组合"""
        # Valid complex weather phenomenon codes
        complex_weather = [
            "METAR ZUGY 120100Z 04002MPS 010V070 1500 -FZDZSN BR SCT003 BKN005 OVC023 M04/M05 Q1018 NOSIG=",  # -FZDZSN
            "METAR ZUGY 171000Z 03003MPS 340V060 2000 -TSPLRA BR FEW003 SCT004 BKN015 FEW023CB 00/M01 Q1016 RESHRA BECMG TL1100 6000 NSW=",  # -TSPLRA
            "METAR ZUGY 241500Z 06003MPS 7000 -SHRASN FEW004 BKN015 FEW020TCU OVC026 01/M00 Q1024 NOSIG=",  # -SHRASN
            "METAR ZUGY 241300Z 04005MPS 9999 -TSRASN FEW005 BKN015 FEW023CB OVC030 02/01 Q1023 BECMG TL1430 NSW=",  # -TSRASN
        ]
        
        for metar in complex_weather:
            is_valid, error_msg = validate_metar(metar)
            assert is_valid, f"Valid complex weather METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"
    
    def test_suspicious_fields(self):
        """测试可疑的异常字段"""
        # Invalid fields that should be detected
        suspicious_metars = [
            "METAR ZYTL 281630Z 16003MPS 120V190 4000 BR SCIISTL04 NOSIG=",  # SCIISTL04 invalid field
            "METAR ZPPP 161600Z 02002MPS 9999 SCT040 OCCGCRY QUXQQ Q1019 NOSIG=",  # OCCGCRY and QUXQQ
            "METAR ZYTX 241500Z 14002MPS CASACI32 ZBBB 241500=",  # CASACI32 invalid field
        ]
        
        for metar in suspicious_metars:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Suspicious field not detected: {metar}"
            assert "Suspicious field" in error_msg or "QNH" in error_msg

