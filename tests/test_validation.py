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
            assert (
                is_valid
            ), f"Valid METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"

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
            (
                "METAR ZGSZ 551800Z AUTO 17004MPS //// // ////// 29/28 Q1004 NOSIG=",
                55,
            ),  # 日期错误
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
            (
                "ZGSZ 030400Z 09003MPS 5000 -RA BR SCT010 OVC030 23/22 Q1013 NOSIG DUPE=",
                "DUPE",
            ),
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
            assert (
                is_valid
            ), f"Valid NIL METAR incorrectly identified as invalid: {metar}"

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
            assert (
                is_valid
            ), f"Valid TREND METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"

        # Invalid TREND cases
        invalid_trends = [
            (
                "METAR RCMQ 250430Z 01013KT 9000 VCSH SCT003 Q1023 FM0430 8000 -RA RMK A3023 VCSH NE=",
                "FM without BECMG/TEMPO",
            ),
            (
                "METAR ZSFZ 120400Z 04005MPS 3800 -TSRA BR BKN003 SCT020CB OVC033 21/20 Q1010 FM0530 -SHRA BKN010 FEW020CB OVC040=",
                "FM without BECMG/TEMPO",
            ),
            (
                "METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 TEMPO R06/0800U=",
                "RVR in TREND",
            ),
            (
                "METAR ZBAA 310630Z 09002MPS 8000 -SHRA NSC Q1007 BECMG Q1012=",
                "QNH in TREND",
            ),
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
            assert (
                is_valid
            ), f"Valid RMK METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"

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
            assert (
                is_valid
            ), f"Valid AUTO/missing data METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"

    def test_spelling_errors(self):
        """测试拼写错误"""
        spelling_errors = [
            (
                "METAR VHHH 280100Z 09008KT 060V160 7000 FEW008 Q1011 EMPO 4000 SHRA=",
                "EMPO",
            ),
            ("METAR ZSHC 270130Z VRB02MPS 2500 BR NSC Q1032 ECMG 3000 BR=", "ECMG"),
            (
                "METAR RCMQ 311200Z 16005KT 6000 -RA SCT003 Q1009 BCECMG TL1200 6000 -RA BKN016 RMK A2982=",
                "BCECMG",
            ),
            (
                "METAR ZBYN 191330Z 00000MPS 5000 -RA BR SCT033 25/23 Q1006 TRMPO 2500 RA BR=",
                "TRMPO",
            ),
            # NOSIG double letter errors
            ("METAR ZBAA 141400Z 14002MPS 9999 SCT005 Q1006 NNOSIG=", "NNOSIG"),
            ("METAR ZBAA 141400Z 14002MPS 9999 SCT005 Q1006 NOSSIG=", "NOSSIG"),
            # BECMG spelling errors
            (
                "METAR ZSOF 172000Z 08002MPS 3500 BR NSC 11/09 Q1025 BCNG TL2100 2500=",
                "BCNG",
            ),
            (
                "METAR ZSOF 171900Z 07002MPS 4000 BR NSC 11/09 Q1025 BECMFG TL2100 2500=",
                "BECMFG",
            ),
            (
                "METAR ZSOF 132200Z 29002MPS 2600 BR NSC 10/07 Q1024 BECMGG TL2330 3000=",
                "BECMGG",
            ),
            (
                "METAR ZSOF 200100Z 34002MPS 300V040 1400 R33/1400U -RA BR BKN005 OVC040 10/09 Q1022 BECMGA AT0300 1500=",
                "BECMGA",
            ),
            (
                "METAR ZSOF 302000Z 01001MPS 3000 BR FEW046 21/21 Q1009 BGECMG TL2100 2000=",
                "BGECMG",
            ),
            (
                "METAR ZSNJ 012200Z 07002MPS 2200 BR NSC 03/02 Q1028 BECGG TL2330 3000=",
                "BECGG",
            ),
            (
                "METAR ZSNJ 131400Z 00000MPS 2000 R06/0900V1700N BR NSC 01/M01 Q1027 BEEMG TL1530 1400=",
                "BEEMG",
            ),
            (
                "METAR ZSNJ 252200Z 06002MPS 1200 R24/1100N R25/1300N BR FEW006 SCT023 23/22 Q1014 BEMG TL2330 2000=",
                "BEMG",
            ),
            (
                "METAR ZSNJ 192200Z 06001MPS 1700 R06/1000V1800U R07/P2000 BR NSC 16/16 Q1013 MECMG TL2330 3000 HZ=",
                "MECMG",
            ),
            (
                "METAR ZSNJ 250900Z 26003MPS 3000 HZ FEW029 07/M02 Q1023 BECMF TL1030 2500=",
                "BECMF",
            ),
            (
                "METAR ZSNJ 251000Z 24002MPS 210V280 8000 BKN010 OVC026 22/20 Q1011 BECMGM TL1130 BKN020=",
                "BECMGM",
            ),
            # More BECMG spelling errors
            (
                "METAR ZSNB 071500Z 19005MPS 2000 +TSRA BR FEW009 BKN016 FEW033CB OVC050 24/24 Q1000 BCEMG TL1630 3000 -SHRA BR=",
                "BCEMG",
            ),
            (
                "METAR ZSNB 122100Z VRB01MPS 4000 BR SCT033 09/06 Q1021 BCEMG TL2230 2500=",
                "BCEMG",
            ),
            (
                "METAR ZSFZ 241800Z 33002MPS 5000 HZ NSC 19/09 Q1014 BECNG TL1930 2900=",
                "BECNG",
            ),
            (
                "METAR ZSFZ 241700Z 02002MPS 6000 NSC 20/09 Q1014 BECNG TL1830 2900=",
                "BECNG",
            ),
            (
                "METAR ZUGY 100700Z 03004MPS 9999 SCT010 BKN020 OVC033 21/20 Q1010 BECML TL0730 -TSRA=",
                "BECML",
            ),
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
            assert (
                is_valid
            ), f"Valid complex weather METAR incorrectly identified as invalid: {metar}\nError: {error_msg}"

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

    def test_additional_validations(self):
        """测试额外的验证规则"""
        # 孤立数字末尾
        isolated_digit = [
            "METAR ZGOW 191600Z 00000MPS 3000 BR NSC 22/21 Q1017 NOSIG 9 =",
            "METAR ZGOW 191600Z 00000MPS 3000 BR NSC 22/21 Q1017 NOSIG 3 =",
        ]

        for metar in isolated_digit:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Isolated digit not detected: {metar}"
            assert "Isolated digit at ending" in error_msg

        # 可疑短字段 (数字+字母)
        suspicious_short = [
            "METAR ZSOF 170300Z VRB02MPS CAVOK 0K 20/10 Q1038 NOSIG=",
            "METAR ZSOF 170300Z VRB02MPS CAVOK 1A 20/10 Q1038 NOSIG=",
        ]

        for metar in suspicious_short:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Suspicious short field not detected: {metar}"
            assert "Suspicious field" in error_msg

        # 温度格式错误 (+ 前缀)
        invalid_temp = [
            "METAR ZSOF 170300Z VRB02MPS CAVOK 20/10 +3/M12 Q1038 NOSIG=",
        ]

        for metar in invalid_temp:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid temperature format not detected: {metar}"
            assert "Invalid temperature format" in error_msg

        # NOSIG 拼写变体
        nosig_variants = [
            "METAR ZUGY 240500Z 02002MPS 7000 NSC 13/M01 Q1028 NOAISIG=",
            "METAR ZUGY 240500Z 02002MPS 7000 NSC 13/M01 Q1028 NOAI SIG=",
            "METAR ZYTX 230330Z 20003MPS 170V250 6000 NSC 02/M12 Q1022 NOSZ CHECK TEXT NEW ENDING ADDED ZBBBXMXX=",  # NOSZ + TREND乱码
        ]

        for metar in nosig_variants:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"NOSIG variant not detected: {metar}"
            assert "NOAI" in error_msg or "NOSZ" in error_msg

        # 能见度格式错误
        invalid_vis = [
            "METAR ZYTL 301930Z 30003MPS 60008P FEW033 M04/M10 Q1026 NOSIG=",
            "METAR ZYTL 301930Z 30003MPS 12345AB FEW033 M04/M10 Q1026 NOSIG=",
        ]

        for metar in invalid_vis:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Invalid visibility not detected: {metar}"
            assert "Invalid visibility format" in error_msg

        # TREND 中的可疑字段
        trend_suspicious = [
            "METAR ZUUU 092200Z 00000MPS 2700 BR NSC 02/02 Q1023 BECMG TL2350 K JHHHHH=",
            "METAR ZUUU 092200Z 00000MPS 2700 BR NSC 02/02 Q1023 BECMG TL2350 CHECK TEXT=",
        ]

        for metar in trend_suspicious:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Suspicious TREND field not detected: {metar}"
            assert "Suspicious field in TREND" in error_msg

    def test_fixable_errors(self):
        """测试可修复的错误（这些报文在修复前应该是异常的）"""
        # VR/VRB 前导零
        vr_errors = [
            "METAR RCSS 241530Z VR001KT 9999 -RA FEW008 BKN100 26/24 Q1013 NOSIG=",  # VR001KT
            "METAR ZLLL 060500Z VRB002MPS CAVOK 06/M19 Q1024 NOSIG=",  # VRB002MPS
        ]

        for metar in vr_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"VR/VRB error not detected: {metar}"

        # 云组高度错误、温度格式错误、BECMG粘连
        combined_errors = [
            "METAR ZGHA 280100Z VRB01MPS 0300 FG BKN0 20/10 Q1022 NOSIG=",  # BKN0 (1位高度)
            "METAR ZGHA 280100Z VRB01MPS 0300 FG BKN020 0/10 Q1022 NOSIG=",  # 0/10 (温度位数不足)
            "METAR ZGHA 280100Z VRB01MPS 0300 FG BKN020 20/10 Q1022 BECMGTL0130 0900=",  # BECMGTL0130 (粘连)
            "METAR ZGHA 280100Z VRB01MPS 0300 R18R/0550V0700N R18L/0500V0700U FG BKN0 0/10 Q1022 BECMGTL0130 0900=",  # 综合错误
        ]
        for metar in combined_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Error not detected: {metar}\nError: {error_msg}"

        # 风组格式错误（不完整阵风、错误单位）
        wind_errors = [
            "SPECI RCMQ 270025Z 000G UKT 2400 BR BKN002 BKN008 27/27 Q1010 BECMG TL0040 3000 BR BKN002 RMK A2984=",  # 000G UKT
            "METAR ZYTL 020900Z 01006M=",  # 01006M (不完整单位)
        ]
        for metar in wind_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Wind error not detected: {metar}\nError: {error_msg}"
            assert "Invalid wind format" in error_msg

        # 报文太短（缺少观测数据）
        too_short = [
            "METAR ZBYN 100800Z 29006MPS=",
        ]
        for metar in too_short:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Too short not detected: {metar}\nError: {error_msg}"
            assert "Missing observation data" in error_msg

        # 无效字段（DUPE等）
        invalid_field_errors = [
            "METAR ZGSZ 180700Z 16004MPS 9999 SCT018 BKN050 27/25 Q1007 NOSIG DUPE=",
        ]
        for metar in invalid_field_errors:
            is_valid, error_msg = validate_metar(metar)
            assert (
                not is_valid
            ), f"Invalid field not detected: {metar}\nError: {error_msg}"
            assert "DUPE" in error_msg

        # 重复报头
        duplicate_headers = [
            "METAR ZPPP METAR ZPPP 280600Z 24007MPS 9999 SCT030 25/04 Q1013 NOSIG=",
            "METAR METAR ZBAA 111400Z 15001MPS 4000 BR BKN023 M02/M05 Q1030 NOSIG=",
            "METAR SPECI ZSHC 190608Z 27006MPS 9999 SHRA BKN023 FEW023TCU 30/25 Q1003 NOSIG=",
        ]

        for metar in duplicate_headers:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Duplicate header not detected: {metar}"

        # COR 位置错误
        cor_position = [
            "METAR VHHH COR 140730Z 12008KT 090V180 CAVOK 24/11 Q1015 WS RWY07L NOSIG=",
        ]

        for metar in cor_position:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"COR position error not detected: {metar}"

        # 风速单位空格分隔
        wind_spacing = [
            "METAR ZGSZ 100800Z 21003M P S 170V230 5000 HZ SKC 28/19 Q1014 NOSIG=",
        ]

        for metar in wind_spacing:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Wind spacing error not detected: {metar}"

        # 风组格式错误
        wind_format = [
            "METAR ZYTX 151300Z 1800C 41MPS 6000 NSC M13/M19 Q1030 NOSIG=",  # 1800C + 41MPS
        ]

        for metar in wind_format:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Wind format error not detected: {metar}"
            assert "Invalid wind format" in error_msg

        # QNH 相关错误
        qnh_errors = [
            "METAR RCKH 030400Z 34007KT 7000 FEW012 SCT020 BKN060 22/13 Q1 012 NOSIG=",  # Q1 012
            "METAR ZSNJ 262000Z 04002MPS 3000 BR NSC 20/18 Q1016N NOSIG=",  # Q1016N
            "METAR ZJHK 280830Z 32006MPS 5000 BR NSC 09/M02 Q1028NOSIT=",  # Q1028NOSIT
            "METAR ZJHK 280830Z 32006MPS 5000 BR NSC 09/M02 Q1011BECMG TL0930 3000=",  # Q1011BECMG
            "METAR ZJHK 280830Z 32006MPS 5000 BR NSC 09/M02 Q1010NOSIG=",  # Q1010NOSIG
        ]

        for metar in qnh_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"QNH error not detected: {metar}"

        # NOSIG 间距错误
        nosig_spacing = [
            "METAR ZSQD 110100Z 20001MPS 6000 SKC M01/M07 Q1038 N NOSIG=",  # N NOSIG
            "METAR ZJHK 280830Z 32006MPS 5000 BR NSC 09/M02 Q1020 NOS IG=",  # NOS IG
        ]

        for metar in nosig_spacing:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"NOSIG spacing error not detected: {metar}"

        # 云组拼写错误
        cloud_errors = [
            "METAR ZJHK 280830Z 32006MPS 5000 FE023 09/M02 Q1020 NOSIG=",  # FE023
            "METAR ZJHK 280830Z 32006MPS 5000 BCF000 09/M02 Q1020 NOSIG=",  # BCF000 (只有1个字符匹配，不应该修复)
        ]

        for metar in cloud_errors:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Cloud spelling error not detected: {metar}"

        # 嵌入报文
        embedded = [
            "METAR ZSAM 250400Z 03003MPS 9999 FE023 32/23 Q1002 NOSIG SQD 250400Z 02004MPS 9999 BKN023 29/20 Q1004 NOSIG ZUUU NI=",
        ]

        for metar in embedded:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Embedded reports not detected: {metar}"

        # 问号
        question_marks = [
            "METAR RCNN 250000Z 02002KT 9999 FEW012 SCT040 BKN120? 28/23 Q1012 NOSIG=",
            "METAR RCNN 270730Z 30005G?KT 6000 -TSRA SCT010 FEW012CB BKN021 BKN040 27/24 Q1009 NOSIG=",
            "METAR RCMQ 222000Z 02020G30KT 9999 -RA FEW010?BKN020 BKN040 20/16 Q1008 RMK A2979=",
        ]

        for metar in question_marks:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Question mark not detected: {metar}"

        # 缺少报文头
        missing_header = [
            "ZBAA 111200Z 15001MPS 4000 BR BKN023 M02/M05 Q1030 NOSIG=",
            "ZBAA 111215Z 15001MPS 4000 BR BKN023 M02/M05 Q1030 NOSIG=",
        ]

        for metar in missing_header:
            is_valid, error_msg = validate_metar(metar)
            assert not is_valid, f"Missing header not detected: {metar}"
