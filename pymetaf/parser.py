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
            dataset[
                "visibility"
            ] = 99999  # Represent visibility greater than 10000 as 99999
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
