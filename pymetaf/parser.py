# coding: utf-8
"""Aviation Weather Message Parsing Program
This program can parse and process the following messages:
    1. Routine Weather Reports (METAR)
    2. Special Weather Reports (SPECI)
    3. Terminal Aerodrome Forecasts (TAF)
"""
import re
from datetime import datetime, timezone

FIELD_PATTERNS = {
    # Message type
    "kind": r"(METAR( COR)?|SPECI( COR)?|TAF( AMD( CNL)?| COR)?)",
    # Report time
    "time": r"\d{6}Z",
    # Airport code
    "icao": r"\b[A-Z]{4}\b",
    # Wind direction and speed (wind speed variation)
    "wind": r"(\d{3}|VRB)\d{2}[G\d{2}]*(MPS|KT)( \d{3}V\d{3})?",
    # Temperature/Dew point temperature
    "temp/dew": r"\bM?\d{2}/M?\d{2}\b",
    # Altimeter setting pressure at sea level
    "qnh": r"[AQ]\d{4}",
    # Automated observation indicator
    "auto": r"AUTO",
    # Correction indicator
    "correct": r"COR",
    # Ceiling and visibility OK indicator
    "cavok": r"CAVOK",
    # Runway visual range
    "rvr": r"R\d{2}[RLC]?/(\d{4}V)?[PM]?\d{4}[UDN]?",
    # Vertical visibility
    "vvis": r"VV\d{3}",
    # Visibility
    "vis": r"\b(\d{1,2}SM|\d{4})\b(?!/)",
    # Cloud amount and height (cloud type)
    "cloud": r"(FEW|SCT|BKN|OVC|SKC|NSC)(\d{3})?([A-Za-z]*)?",
    # Weather phenomena
    "weather": (
        r"(?<=\s)(?:\+|-|VC|RE)?"
        r"(MI|BC|PR|DR|BL|SH|TS|FZ)?"
        r"(DZ|RA|SN|SG|IC|PL|GR|GS)?"
        r"(BR|FG|FU|VA|DU|SA|HZ)?"
        r"(PO|SQ|FC|SS|DS)?(?=\s)"
    ),
    # Wind shear
    "wshear": r"WS (LDG |TKOF |ALL )?RWY\d+[LRC]?",
    # Trend
    "trend": r"(TEMPO|BECMG|NOSIG).*?(?= TEMPO| BECMG| NOSIG|=)",
    # Change start and end time
    "vartime": r"(FM|TL|AT)\d{4}",
    # Current observation
    "observ": r"(METAR|SPECI|TAF).*?(?= TEMPO| BECMG| NOSIG)",
    # Forecast valid time
    "validtime": r"\b\d{6}\b",
    # Forecast cancellation indicator
    "cancel": r"CNL",
    # Forecast amendment indicator
    "amend": r"AMD",
    # Forecast temperature
    "txtn": r"TXM?\d+/M?\d+Z\sTNM?\d+/M?\d+Z",
    # Cancel report indicator
    "nil": r"NIL",
}


def validate_metar(text, strict_mode=False):
    """Validate METAR message format
    
    Args:
        text (str): The original METAR message text to validate
        strict_mode (bool): Whether to use strict mode.
                           True: RMK remarks section not allowed
                           False: Allow RMK remarks but check their validity
        
    Returns:
        tuple: (is_valid, error_message)
            is_valid (bool): Whether the message is valid
            error_message (str): Error message if invalid; None if valid
    
    Examples:
    >>> validate_metar("METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=")
    (True, None)
    >>> validate_metar("METAR ZBTJ 290200Z 35009MPS CAVOK M04/M27 Q102NOSIG=")
    (False, 'Invalid QNH format')
    """
    if not text or not isinstance(text, str):
        return False, "Empty or invalid input"
    
    # Remove possible trailing equals sign
    text_clean = text.rstrip("=").strip()
    
    # Check for line breaks (should be single line)
    if '\n' in text_clean or '\r' in text_clean:
        return False, "Contains line breaks (should be single line)"
    
    # Check for MK spelling error (should be RMK)
    if re.search(r'\sMK\s', text_clean):
        return False, "Spelling error: MK (should be RMK)"
    
    # Check if there is RMK remarks section
    # IMPORTANT: RMK must come AFTER TREND section, not before
    has_rmk = 'RMK' in text_clean
    if has_rmk:
        # Separate content before and after RMK
        parts_split = text_clean.split('RMK', 1)
        main_part = parts_split[0].strip()
        rmk_part = parts_split[1].strip() if len(parts_split) > 1 else ""
        
        # In strict mode, RMK section is not allowed
        if strict_mode:
            return False, "RMK remarks section not allowed in strict mode"
        
        # Check if TREND keywords (BECMG/TEMPO) appear in RMK section
        # This is a position error - TREND must come before RMK
        for keyword in ['BECMG', 'TEMPO']:
            if keyword in rmk_part:
                return False, f"TREND keyword {keyword} found in RMK section (should be before RMK)"
        
        # RMK is free text remarks - no other content validation
        # Just keep it as is for downstream processing
    else:
        main_part = text_clean
    
    # Check main part for invalid special characters (allowed: letters, numbers, space, /, +, -)
    invalid_chars = re.findall(r'[^A-Za-z0-9\s/+\-]', main_part)
    if invalid_chars:
        return False, f"Contains invalid characters: {set(invalid_chars)}"
    
    # Check common spelling errors (use word boundaries to avoid false positives)
    if re.search(r'\bEMPO\b', main_part):  # Should be TEMPO
        return False, "Spelling error: EMPO (should be TEMPO)"
    if re.search(r'\bTRMPO\b', main_part):  # Should be TEMPO
        return False, "Spelling error: TRMPO (should be TEMPO)"
    if re.search(r'\bECMG\b', main_part):  # Should be BECMG
        return False, "Spelling error: ECMG (should be BECMG)"
    if re.search(r'\bBCECMG\b', main_part):  # Should be BECMG
        return False, "Spelling error: BCECMG (should be BECMG)"
    
    # Check for various BECMG spelling errors
    becmg_errors = [
        'BCNG', 'BECNG', 'BCEMG', 'BECML', 'BECMFG', 'BECMGG', 'BECMGA', 'BGECMG', 
        'BECGG', 'BEEMG', 'BEMG', 'MECMG', 'BECMF', 'BECMGM'
    ]
    for error in becmg_errors:
        if re.search(r'\b' + error + r'\b', main_part):
            return False, f"Spelling error: {error} (should be BECMG)"
    
    # Check for placeholders
    if re.search(r'Q{5,}', main_part):  # QQQQQQQQ...
        return False, "Contains placeholder (repeated Q)"
    
    # Separate TREND section (NOSIG/BECMG/TEMPO) from main observation
    # TREND is at the end and contains change forecasts
    trend_keywords = ['NOSIG', 'BECMG', 'TEMPO']
    has_trend = False
    trend_start_idx = -1
    
    for keyword in trend_keywords:
        if keyword in main_part:
            has_trend = True
            # Find the position of the first trend keyword
            parts_temp = main_part.split()
            for i, part in enumerate(parts_temp):
                if part in trend_keywords:
                    trend_start_idx = i
                    break
            if trend_start_idx > 0:
                break
    
    # Separate main observation and trend parts
    if has_trend and trend_start_idx > 0:
        parts_all = main_part.split()
        main_obs_parts = parts_all[:trend_start_idx]
        trend_parts = parts_all[trend_start_idx:]
        main_obs_text = ' '.join(main_obs_parts)
    else:
        main_obs_text = main_part
        trend_parts = []
    
    # Check minimum message length
    if len(main_obs_text) < 20:
        return False, "METAR text too short"
    
    parts = main_obs_text.split()
    if len(parts) < 4:
        return False, "Missing essential fields"
    
    # Locate field indices
    idx = 0
    
    # 1. Check report type (first field should be METAR/SPECI/TAF)
    # If first field looks like ICAO code, report type is missing
    icao_pattern = re.compile(r'^[A-Z]{4}$')
    if icao_pattern.match(parts[idx]):
        return False, f"Missing report type (METAR/SPECI): starts with {parts[idx]}"
    
    if parts[idx] in ["METAR", "SPECI", "TAF"]:
        idx += 1
        # Check for COR
        if idx < len(parts) and parts[idx] == "COR":
            idx += 1
    else:
        return False, f"Invalid or missing report type: {parts[idx]}"
    
    # 2. Check ICAO code (must be 4 uppercase letters)
    if idx >= len(parts):
        return False, "Missing ICAO code"
    
    if not icao_pattern.match(parts[idx]):
        return False, f"Invalid ICAO code format: {parts[idx]}"
    idx += 1
    
    # 3. Check time group (must be 6 digits + Z, day part cannot exceed 31)
    if idx >= len(parts):
        return False, "Missing time group"
    
    time_pattern = re.compile(r'^(\d{2})(\d{4})Z$')
    time_match = time_pattern.match(parts[idx])
    if not time_match:
        return False, f"Invalid time format: {parts[idx]}"
    
    day = int(time_match.group(1))
    if day < 1 or day > 31:
        return False, f"Invalid day in time group: {day}"
    idx += 1
    
    # If it's a NIL report, we're done here
    if idx < len(parts) and parts[idx] == "NIL":
        return True, None
    
    # Check for AUTO
    if idx < len(parts) and parts[idx] == "AUTO":
        idx += 1
    
    # 4. Check wind group (may exist, check format)
    if idx < len(parts):
        wind_pattern = re.compile(r'^((\d{3}|VRB)\d{2}(G\d{2})?(MPS|KT)|/{5}(MPS|KT))$')
        # Check for wind-like fields with incorrect format
        wind_like_pattern = re.compile(r'^\d{1,5}(MPS|KT|PS)$')
        # Check for spacing errors like "12001MPSH4000" or "30007MPSG13"
        wind_spacing_error = re.compile(r'^\d{5}MPS[A-Z]|\d{5}MPSG\d+$')
        # Check for wind variation concatenation errors like "18003MPSV220"
        wind_var_error = re.compile(r'^\d{5}MPSV\d+$')
        
        if wind_pattern.match(parts[idx]):
            idx += 1
            # Check for possible wind direction variation
            if idx < len(parts):
                wind_var_pattern = re.compile(r'^\d{3}V\d{3}$')
                if wind_var_pattern.match(parts[idx]):
                    idx += 1
        elif wind_like_pattern.match(parts[idx]):
            # Looks like wind group but format is wrong
            return False, f"Invalid wind format: {parts[idx]}"
        elif wind_spacing_error.match(parts[idx]):
            # Wind group concatenated with other fields, missing space
            return False, f"Wind group spacing error: {parts[idx]}"
        elif wind_var_error.match(parts[idx]):
            # Wind variation information concatenated
            return False, f"Wind variation spacing error: {parts[idx]}"
    
    # 5. Check pressure group (if exists, must be Q or A followed by 4 digits or ////)
    # Search for pressure group anywhere in the message
    qnh_found = False
    qnh_pattern = re.compile(r'^[AQ]\d{4}$')
    qnh_missing_pattern = re.compile(r'^[AQ]/{4}$')  # Q//// or A//// means missing data
    
    # Known keywords that start with A or Q and are not QNH
    known_keywords = ['AUTO', 'AT']  # AT is for TREND time indicator like AT1600
    
    for part in parts:
        if part.startswith('Q') or part.startswith('A'):
            # Skip known keywords
            if part in known_keywords or part.startswith('AT') and len(part) == 6:
                continue
            
            if qnh_pattern.match(part):
                qnh_found = True
                break
            elif qnh_missing_pattern.match(part):
                # Q//// or A//// is valid (missing data indicator)
                qnh_found = True
                break
            else:
                # If starts with Q or A but format is wrong, this is an error
                return False, f"Invalid QNH format: {part}"
    
    # 6. Check for abnormal character combinations at end
    # End should be NOSIG, TEMPO, BECMG or other valid fields
    last_part = parts[-1]
    
    # If last field is a valid ending field, skip check
    valid_endings = ['NOSIG', 'TEMPO', 'BECMG', 'NIL']
    
    # Check for spacing errors like "NOSI G"
    if len(parts) >= 2:
        last_two_combined = parts[-2] + parts[-1]
        if last_two_combined in ['NOSIG', 'TEMPO', 'BECMG']:
            return False, f"Invalid spacing in ending: {parts[-2]} {parts[-1]}"
    
    # Check for single letter ending (without RMK, this is usually an error)
    # e.g. "Q1003 N=" or "FEW015 S="
    if not has_rmk and re.match(r'^[A-Z]$', last_part):
        return False, f"Invalid single letter ending: {last_part}"
    
    if last_part not in valid_endings:
        # Check if last field contains abnormal combinations
        invalid_endings = [
            r'^NOSIT$',  # NOSIG spelling error
            r'^NOSI$',  # NOSI (NOSIG missing G)
            r'^OSIG$',   # Missing N
            r'^DUPE$',   # Duplicate report marker, should not appear
        ]
        
        for pattern in invalid_endings:
            if re.search(pattern, last_part):
                return False, f"Invalid ending: {last_part}"
    
    # 7. Check for isolated single digits or letters (only in main observation, not in TREND)
    for i, part in enumerate(parts):
        # Skip known valid single letter/digit cases
        if part in ['M', 'P', 'U', 'D', 'N']:  # These are valid in certain contexts
            # Check context, if they are isolated (neither prev nor next are appropriate), report error
            if i > 0 and i < len(parts) - 1:
                # Check if in reasonable context
                prev_part = parts[i-1]
                next_part = parts[i+1]
                # If neither prev nor next is digit or RVR related, may be abnormal
                if not (prev_part.startswith('R') or next_part.isdigit()):
                    return False, f"Isolated character: {part}"
        
        # Check for isolated single digit
        if part.isdigit() and len(part) == 1:
            return False, f"Isolated digit: {part}"
    
    # 8. Check for obviously wrong fields in main observation (not in TREND)
    # TREND may contain time indicators like TL1440, FM1520, AT1600 which are valid
    for part in parts[idx:]:
        # Skip known valid formats
        if (qnh_pattern.match(part) or 
            re.match(r'^\d{4}$', part) or  # 4 digits (visibility)
            re.match(r'^[A-Z]+$', part) or
            re.match(r'^M?\d+/M?\d+$', part) or  # Temperature/dewpoint
            re.match(r'^R\d+', part) or  # RVR
            re.match(r'^\d{3}V\d{3}$', part) or  # Wind direction variation
            re.match(r'^(FEW|SCT|BKN|OVC|SKC|NSC)', part) or  # Cloud group
            re.match(r'^VV\d{3}$', part) or  # Vertical visibility
            re.match(r'^[/]+$', part)):  # Slashes (indicate missing data)
            continue
        
        # Check for isolated 2 or 3 digit numbers (not visibility or other valid formats)
        if re.match(r'^\d{2,3}$', part):
            # Check if in reasonable context
            # If not preceded by R (RVR), may be abnormal
            return False, f"Isolated numeric value: {part}"
        
        # Check for FM/TL/AT time indicators without BECMG/TEMPO
        # These indicate TREND section which must have BECMG or TEMPO first
        if re.match(r'^(FM|TL|AT)\d{4}$', part):
            # Check if there's a BECMG spelling error in the previous parts
            # Common BECMG spelling errors
            becmg_error_patterns = [
                'BCNG', 'BECNG', 'BCEMG', 'BECML', 'BECMFG', 'BECMGG', 'BECMGA', 'BGECMG', 
                'BECGG', 'BEEMG', 'BEMG', 'MECMG', 'BECMF', 'BECMGM', 'ECMG', 'BCECMG'
            ]
            # Check last few parts for BECMG spelling errors
            check_range = min(5, len(parts))
            for j in range(max(0, i - check_range), i):
                if parts[j] in becmg_error_patterns:
                    return False, f"Spelling error: {parts[j]} (should be BECMG)"
            
            # If no spelling error found, report time indicator error
            return False, f"Time indicator {part[:2]} must follow BECMG or TEMPO"
        
        # Check for wrong cloud group format (e.g. KN026 should be BKN026)
        cloud_like_pattern = re.compile(r'^[A-Z]{2,3}\d{3}')
        if cloud_like_pattern.match(part):
            valid_cloud_types = ['FEW', 'SCT', 'BKN', 'OVC', 'SKC', 'NSC', 'VV']
            if not any(part.startswith(ct) for ct in valid_cloud_types):
                return False, f"Invalid cloud group format: {part}"
        
        # Check for obviously abnormal mixed fields
        # Examples: OCCGCRY, QUXQQ, DEPPQMPS, etc.
        # But exclude valid weather phenomenon codes (can be long, e.g. -FZDZSN, -TSRASN)
        if len(part) > 6 and re.search(r'[A-Z]{6,}', part):
            # Check if it's a known valid field
            known_fields = ['NOSIG', 'CAVOK', 'BECMG', 'TEMPO']
            if part in known_fields or any(kf in part for kf in known_fields):
                continue
            
            # Check if it's a weather phenomenon code
            # Pattern: [+-]?(VC|RE)?(MI|BC|PR|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS)+(BR|FG|FU|VA|DU|SA|HZ)?(PO|SQ|FC|SS|DS)?
            weather_pattern = re.compile(
                r'^[+-]?'  # Intensity
                r'(VC|RE)?'  # Vicinity/Recent
                r'(MI|BC|PR|DR|BL|SH|TS|FZ)?'  # Descriptor
                r'(DZ|RA|SN|SG|IC|PL|GR|GS)+'  # Precipitation (one or more)
                r'(BR|FG|FU|VA|DU|SA|HZ)?'  # Obscuration
                r'(PO|SQ|FC|SS|DS)?$'  # Other
            )
            
            if weather_pattern.match(part):
                continue
            
            # May be abnormal field
            if not re.match(r'^[A-Z]{4}$', part):  # Not ICAO code
                return False, f"Suspicious field: {part}"
    
    # 9. Validate TREND section if present
    if has_trend and trend_parts:
        # Check structure: time indicators (FM/TL/AT) must follow BECMG/TEMPO
        # They cannot appear alone
        prev_keyword = None
        for i, part in enumerate(trend_parts):
            # Track change type keywords
            if part in ['BECMG', 'TEMPO']:
                prev_keyword = part
                continue
            
            # Time indicators must follow a change type keyword
            if re.match(r'^(FM|TL|AT)\d{4}$', part):
                if prev_keyword is None:
                    # FM/TL/AT without preceding BECMG/TEMPO is invalid
                    return False, f"Time indicator {part} without BECMG/TEMPO"
                continue
            
            # NOSIG stands alone, doesn't need validation
            if part == 'NOSIG':
                continue
            
            # Skip valid TREND elements (wind, visibility, weather, clouds, NSW, CAVOK)
            if (re.match(r'^(VRB|\d{3})\d{2}(G\d{2})?(MPS|KT)$', part) or  # Wind
                re.match(r'^\d{4}$', part) or  # Visibility
                re.match(r'^(FEW|SCT|BKN|OVC|SKC|NSC)', part) or  # Clouds
                part in ['NSW', 'CAVOK'] or  # No significant weather / CAVOK
                re.match(r'^[+-]?(VC|RE)?(MI|BC|PR|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS)?(BR|FG|FU|VA|DU|SA|HZ)?(PO|SQ|FC|SS|DS)?$', part)):  # Weather
                continue
            
            # Prohibited in TREND: RVR, QNH, temperature, wind shear
            if re.match(r'^R\d{2}', part):  # RVR
                return False, f"RVR not allowed in TREND: {part}"
            if re.match(r'^[AQ]\d{4}$', part):  # QNH
                return False, f"QNH not allowed in TREND: {part}"
            if re.match(r'^M?\d{2}/M?\d{2}$', part):  # Temperature/dewpoint
                return False, f"Temperature not allowed in TREND: {part}"
            if part.startswith('WS'):  # Wind shear
                return False, f"Wind shear not allowed in TREND: {part}"
            if re.match(r'^PROB\d{2}$', part):  # Probability (TAF only)
                return False, f"Probability group not allowed in TREND: {part}"
    
    # 10. Check for multiple isolated single letter fields at end (e.g. "TE G")
    # Only check main observation part, not TREND
    if len(parts) >= 2:
        last_two = ' '.join(parts[-2:])
        # Check if they are two isolated uppercase letters
        if re.match(r'^[A-Z]{1,2}\s+[A-Z]{1,2}$', last_two):
            # This may be an abnormal ending
            if parts[-2] not in valid_endings and parts[-1] not in valid_endings:
                return False, f"Invalid ending: {last_two}"
    
    return True, None


def miles_to_meters(miles):
    conversion_factor = 1609.34
    meters = miles * conversion_factor

    return meters


def get_field_text(field, text, mod="first"):
    """Extract text fields

    Args:
        field (str): Field name, options are as follows (fields in square brackets may not appear):
                    'observ'       All fields in the non-trend section
                    'kind'         Report type
                    'icao'         Airport ICAO code
                    'time'         Report time
                    'wind'         Wind direction and speed [wind speed variation]
                    'temp/dew'     Temperature/dew point temperature
                    'qnh'          Altimeter setting pressure at sea level
                    'trend'        All fields in a single trend section
                    'cavok'        [Ceiling and visibility OK]
                    'auto'         [Automated observation]
                    'correct'      [Correction]
                    'rvr'          [Runway visual range]
                    'vvis'         [Vertical visibility]
                    'vis'          [Visibility]
                    'cloud'        [Cloud amount and height [cloud type]]
                    'weather'      [Weather phenomena]
                    'wshear'       [Wind shear]
                    'vartime'      [Trend change start and end time]
                    'validtime'    Forecast valid time
                    'cancel'       [Forecast cancellation]
                    'amend'        [Forecast amendment]
                    'nsw'          [No significant weather]
                    'prob'         [Probability forecast]
                    'txtn'         Forecast temperature group
        text (str): The original message string to search
        mod (str, optional): Matching mode, options are 'first' and 'all',
                             'first' matches the first one, 'all' matches all. Defaults to 'first'.

    Returns:
        str: The corresponding field extracted from the original message.
             If mod is 'first', the result is returned as a string `str`;
             If mod is 'all', the result is returned as a list `list`;
             If the corresponding field is not found in the original message, None is returned.

    Examples:
    >>> text = 'METAR ZSNJ 030500Z 24002MPS 330V030 1000 R06/1300U R07/1300N BR FEW005 15/14 Q1017 NOSIG='
    >>> get_field_text('wind', text)
    '24002MPS 330V030'
    >>> get_field_text('rvr', text)
    'R06/1300U'
    """

    if mod == "first":
        match = re.search(FIELD_PATTERNS[field], text)
        if match:
            result = match.group()
        else:
            result = None
    elif mod == "all":
        iter = re.finditer(FIELD_PATTERNS[field], text)
        matches = []
        while True:
            try:
                match = next(iter)
            except StopIteration:
                break
            else:
                matches.append(match.group())
        if matches:
            result = matches
        else:
            result = None

    if field == "observ" and not result:
        result = text.replace("=", "")

    return result


def get_weather_description(code):
    intensity = ""
    if code.startswith("+"):
        intensity = "Heavy "
        code = code[1:]
    elif code.startswith("-"):
        intensity = "Light "
        code = code[1:]

    weather_codes = {
        "DZ": "Drizzle",
        "RA": "Rain",
        "SN": "Snow",
        "SG": "Snow Grains",
        "IC": "Ice Crystals",
        "PL": "Ice Pellets",
        "GR": "Hail",
        "GS": "Small Hail or Snow Pellets",
        "UP": "Unknown Precipitation",
        "BR": "Mist",
        "FG": "Fog",
        "FU": "Smoke",
        "VA": "Volcanic Ash",
        "DU": "Widespread Dust",
        "SA": "Sand",
        "HZ": "Haze",
        "PY": "Spray",
        "PO": "Dust/Sand Whirls",
        "SQ": "Squalls",
        "FC": "Funnel Cloud",
        "SS": "Sandstorm",
        "DS": "Duststorm",
        "SH": "Showers of",
        "TS": "Thunderstorm",
        "BL": "Blowing",
        "MI": "Shallow",
        "BC": "Patches",
        "PR": "Partial",
        "DR": "Low Drifting",
        "FZ": "Freezing",
        "VC": "In the Vicinity",
        "RE": "Recent",
    }

    description = ""
    while len(code) > 0:
        for key in weather_codes.keys():
            if code.startswith(key):
                description += weather_codes[key] + " "
                code = code[len(key) :]
                break

    return intensity + description.strip()


def parse_text(text, year, month):
    """Parse message text

    Args:
        text (str): The message text to parse, supports METAR and TAF message formats
        year (int): The year of the message. Since the message does not provide year and month information, the user needs to provide the year information when parsing the message.
        month (int): The month of the message. Since the message does not provide year and month information, the user needs to provide the month information of the message when parsing.

    Returns:
        dict: The parsed data dictionary
    """
    dataset = {}
    dataset["kind"] = get_field_text("kind", text)
    dataset["icao"] = get_field_text("icao", text)

    # Time field
    timestr = get_field_text("time", text)
    day = int(timestr[:2])
    hour = int(timestr[2:4])
    minute = int(timestr[4:6])

    dataset["datetime"] = datetime(
        year, month, day, hour, minute, 0, tzinfo=timezone.utc
    ).isoformat()

    no_trend_text = get_field_text("observ", text)

    # Return empty if NIL is present
    nil = get_field_text("nil", no_trend_text)
    if nil:
        return None

    # Wind direction and speed
    windstr = get_field_text("wind", no_trend_text)
    if windstr:
        wind_items = windstr.split(" ")
        # wdws: wind direction and speed
        wdws = wind_items[0]
        if len(wind_items) > 1:
            wdrg_str = wind_items[
                1
            ]  # wdrg: wind direction range, this field rarely appears
            dir1 = int(wdrg_str[:3])
            dir2 = int(wdrg_str[4:])
            wdrg = (dir1, dir2)
        else:
            wdrg = None
        wd_str = wdws[:3]  # wind direction
        if wd_str == "VRB":
            wd = None
        elif wd_str.isdigit():
            wd = int(wd_str)

        ws = int(wdws[3:5])  # wind speed

        # If wind speed is 0 and wind direction is 000, this is calm wind
        # In this case, wind direction should be None
        if ws == 0 and wd_str == "000":
            wd = None

        if wdws[5] == "G":
            # Example with gust: METAR ZBXH 250700Z 25008G13MPS 9999 FEW040 13/M18 Q1015 NOSIG
            gust = int(wdws[6:8])  # gust
            unit = wdws[8:]  # gust unit
        else:
            gust = None
            unit = wdws[5:]

        if unit == "KT":
            # Convert knots to m/s
            if ws:
                ws = int(int(ws) * 0.5144444)
            if gust:
                gust = int(int(gust) * 0.5144444)
    else:
        wd = None
        ws = None
        gust = None
        wdrg = None

    dataset["wind_direction"] = wd
    dataset["wind_direction_units"] = "degree"
    dataset["wind_speed"] = ws
    dataset["wind_speed_units"] = "m/s"
    dataset["gust"] = gust
    dataset["wind_direction_range"] = wdrg

    # Ceiling and visibility OK (CAVOK)
    cavok = get_field_text("cavok", no_trend_text)
    if cavok:
        dataset["cavok"] = True
    else:
        dataset["cavok"] = False

    # Visibility field
    visstr = get_field_text("vis", no_trend_text)
    if visstr:
        if visstr == "9999":
            dataset["visibility"] = (
                99999  # Represent visibility greater than 10000 as 99999
            )
        elif visstr == "0000":
            dataset["visibility"] = 50
        elif visstr.endswith("SM"):
            # Convert statute miles to meters
            visstr = visstr[:-2]
            vis = float(visstr)
            vis = miles_to_meters(vis)
            dataset["visibility"] = int(vis)
        else:
            dataset["visibility"] = int(visstr)
    elif cavok:
        # Set CAVOK visibility to 99999
        dataset["visibility"] = 99999
    else:
        dataset["visibility"] = None

    dataset["visibility_units"] = "m"

    # Temperature/Dew point
    tempstr = get_field_text("temp/dew", no_trend_text)
    if tempstr:
        temp, dewtemp = tempstr.split("/")
        temp = int(temp.replace("M", "-"))
        dewtemp = int(dewtemp.replace("M", "-"))
    else:
        temp = None
        dewtemp = None

    dataset["temperature"] = temp
    dataset["dew_temperature"] = dewtemp
    dataset["temperature_units"] = "degree C"

    # Altimeter setting
    qnhstr = get_field_text("qnh", no_trend_text)
    if qnhstr:
        if qnhstr.startswith("Q"):
            qnh = int(qnhstr[1:])  # Remove leading zeros
        elif qnhstr.startswith("A"):
            qnh = int(int(qnhstr[1:]) * 33.8638)  # inHg -> hPa

        dataset["qnh"] = qnh
    else:
        dataset["qnh"] = None

    dataset["qnh_units"] = "hPa"

    # Cloud amount/height
    cloudstrs = get_field_text("cloud", no_trend_text, mod="all")
    CLOUD_MASK = {
        "FEW": round(2 / 8, 2),
        "SCT": round(4 / 8, 2),
        "BKN": round(6 / 8, 2),
        "OVC": round(8 / 8, 2),
        "SKC": 0,
        "NSC": 0,
        "///": 0,
    }
    if cloudstrs:
        cloudstrs = sorted(cloudstrs)
        cloudgroups = []
        for cloudstr in cloudstrs:
            if "CB" in cloudstr:
                cloud_type = "cumulonimbus"
            elif "TCU" in cloudstr:
                cloud_type = "altocumulus"
            else:
                cloud_type = None

            cloudstr = cloudstr.replace("CB", "")
            cloudstr = cloudstr.replace("///", "")
            cloudstr = cloudstr.replace("TCU", "")

            if len(cloudstr) == 3:
                # Example without cloud height: METAR ZBHH 242100Z 05002MPS 7000 NSC 01/M04 Q1023 NOSIG
                height = None
            else:
                # Example with cloud height: METAR ZBDS 250000Z 29003MPS 9999 FEW040 04/M08 Q1023 NOSIG
                height = int(cloudstr[3:]) * 20
            mask = cloudstr[:3]

            cloud_record = {
                "cloud_mask": CLOUD_MASK[mask],
                "cloud_height": height,
                "cloud_height_units": "m",
                "cloud_type": cloud_type,
            }

            cloudgroups.append(cloud_record)
    else:
        cloudgroups = None
    dataset["cloud"] = cloudgroups

    # Weather phenomena
    weather_codes = get_field_text("weather", no_trend_text, mod="all")
    if weather_codes is not None:
        weather_descriptions = []
        for code in weather_codes:
            weather_descriptions.append(get_weather_description(code))

        dataset["weather"] = weather_descriptions
    else:
        if cloudgroups is None:
            dataset["weather"] = ["Clear Sky"]
        else:
            dataset["weather"] = ["Cloudy"]

        if cloudgroups is not None:
            for cloudgroup in cloudgroups:
                if cloudgroup["cloud_mask"] == 0:
                    dataset["weather"] = ["Clear Sky"]
                elif 0 < cloudgroup["cloud_mask"] < 1:
                    dataset["weather"] = ["Cloudy"]
                elif cloudgroup["cloud_mask"] == 1:
                    dataset["weather"] = ["Overcast"]

    if get_field_text("auto", no_trend_text):
        dataset["auto"] = True
    else:
        dataset["auto"] = False

    # TODO: Trend report parsing
    return dataset


if __name__ == "__main__":
    pass
