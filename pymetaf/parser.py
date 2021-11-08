# coding: utf-8
"""航空天气报文解析程序
本程序可以解析处理的报文包括：
    1、例行天气报告（METAR）
    2、特选天气报告（SPECI）
    3、机场天气报告（TAF）
"""
import re
from datetime import datetime, timezone

FIELD_PATTERNS = {
    # 报文类型
    'kind':             r'(METAR( COR)?|SPECI( COR)?|TAF( AMD( CNL)?| COR)?)',
    # 发报时间
    'time':             r'\d{6}Z',
    # 机场编码
    'icao':             r'\b[A-Z]{4}\b',
    # 风向风速（风速变化）
    'wind':             r'(\d{3}|VRB)\d{2}[G\d{2}]*(MPS|KT)( \d{3}V\d{3})?',
    # 温度/露点温度
    'temp/dew':         r'\bM?\d{2}/M?\d{2}\b',
    # 修正海平面气压
    'qnh':              r'[AQ]\d{4}',
    # 自动观测标识
    'auto':             r'AUTO',
    # 修正报标识
    'correct':          r'COR',
    # 好天气
    'cavok':            r'CAVOK',
    # 跑道视程
    'rvr':              r'R\d{2}[RLC]?/(\d{4}V)?[PM]?\d{4}[UDN]?',
    # 垂直能见度
    'vvis':             r'VV\d{3}',
    # 能见度
    'vis':              r'(?<=\s)\d{4}[A-Z]*\b',
    # 云量云高
    'cloud':            r'(FEW|SCT|BKN|OVC|SKC|NSC)(\d{3})?([A-Za-z]*)?',
    # 天气现象l
    'weather':          (r'(?<=\s)(?:\+|-|VC|RE)?'
                         r'(MI|BC|PR|DR|BL|SH|TS|FZ)?'
                         r'(DZ|RA|SN|SG|IC|PL|GR|GS)?'
                         r'(BR|FG|FU|VA|DU|SA|HZ)?'
                         r'(PO|SQ|FC|SS|DS)?(?=\s)'),
    # 风切变
    'wshear':           r'WS (LDG |TKOF |ALL )?RWY\d+[LRC]?',
    # 趋势
    'trend':            r'(TEMPO|BECMG|NOSIG).*?(?= TEMPO| BECMG| NOSIG|=)',
    # 变化起止时间
    'vartime':          r'(FM|TL|AT)\d{4}',
    # 当前观测
    'observ':           r'(METAR|SPECI|TAF).*?(?= TEMPO| BECMG| NOSIG)',
    # 预报有效时间
    'validtime':        r'\b\d{6}\b',
    # 预报取消标识
    'cancel':           r'CNL',
    # 修复预报标识
    'amend':            r'AMD',
    # 预报温度
    'txtn':             r'TXM?\d+/M?\d+Z\sTNM?\d+/M?\d+Z'
}


def get_field_text(field, text, mod='first'):
    """提取文本字段

    Args:
        field (str): 报文字段名称，选项如下(中括号内的字段不一定会出现)：
                    'observ'       非趋势部分全部字段
                    'kind'         报文种类
                    'icao'         机场ICAO码
                    'time'         发报时间
                    'wind'         风向风速 [风速变化]
                    'temp/dew'     温度/露点温度
                    'qnh'          修正海平面气压
                    'trend'        单个变化趋势部分全部字段
                    'cavok'        [好天气标识]
                    'auto'         [自动观测标识]
                    'correct'      [修正报标识]
                    'rvr'          [跑道视程]
                    'vvis'         [垂直能见度]
                    'vis'          [能见度]
                    'cloud'        [云量云高[云形]]
                    'weather'      [天气现象]
                    'wshear'       [跑道风切变]
                    'vartime'      [趋势变化起止时间]
                    'validtime'    预报有效时间
                    'cancel'       [预报取消标识]
                    'amend'        [预报修正标识]
                    'nsw'          [重要天气现象结束标识]
                    'prob'         [概率预报组]
                    'txtn'         预报气温组
        text (str): 所要查找的原始报文字符串
        mod (str, optional): 匹配模式，可供选择的选项有'first'和'all', 
                             'first'表示匹配第一个，'all'表示匹配所有. Defaults to 'first'.

    Returns:
        str: 从原始报文中提取出的相应字段，若mod为'first'则结果返回字符串`str`；
             若mod为'all'，则返回列表`list`；
             若原始报文中无相应字段则返回None

    Examples:
    >>> text = 'METAR ZSNJ 030500Z 24002MPS 330V030 1000 R06/1300U R07/1300N BR FEW005 15/14 Q1017 NOSIG='
    >>> get_field_text('wind', text)
    '24002MPS 330V030'
    >>> get_field_text('rvr', text)
    'R06/1300U'
    """

    if mod == 'first':
        match = re.search(FIELD_PATTERNS[field], text)
        if match:
            result = match.group()
        else:
            result = None
    elif mod == 'all':
        iter = re.finditer(FIELD_PATTERNS[field], text)
        matchs = []
        while True:
            try:
                match = next(iter)
            except StopIteration:
                break
            else:
                matchs.append(match.group())
        if matchs:
            result = matchs
        else:
            result = None

    if field == 'observ' and not result:
        result = text.replace('=', '')

    return result


def parse_text(text, year, month):
    """报文文本解析

    Args:
        text (str): 待解析的报文文本，支持METAR和TAF报文格式
        year (int): 年份，由于报文不提供年份和月份的信息，因此解析报文时需要用户自己提供该报文的年信息。
        month (int): 月份，由于报文不提供年份和月份的信息，因此解析报文时需要用户自己提供该报文的月信息。

    Returns:
        dict: 解析后的数据字典
    """
    dataset = {}
    dataset['kind'] = get_field_text('kind', text)
    dataset['icao'] = get_field_text('icao', text)

    # 时间字段
    timestr = get_field_text('time', text)
    day = int(timestr[:2])
    hour = int(timestr[2:4])
    minute = int(timestr[4:6])

    dataset['datetime'] = datetime(
        year, month, day, hour, minute, 0, tzinfo=timezone.utc).isoformat()

    no_trend_text = get_field_text('observ', text)

    # 风向风速
    windstr = get_field_text('wind', no_trend_text)
    wind_items = windstr.split(' ')

    # wdws: 风向风速
    wdws = wind_items[0]
    if len(wind_items) > 1:
        wdrg_str = wind_items[1]  # wdrg: 风向范围，该字段很少出现
        dir1 = int(wdrg_str[:3])
        dir2 = int(wdrg_str[4:])
        wdrg = (dir1, dir2)
    else:
        wdrg = None
    wd_str = wdws[:3]    # 风向
    if wd_str == 'VRB':
        wd = None
    elif wd_str.isdigit():
        wd = int(wd_str)

    ws = int(wdws[3:5])   # 风速
    if wdws[5] == 'G':
        # 带有阵风的示例：METAR ZBXH 250700Z 25008G13MPS 9999 FEW040 13/M18 Q1015 NOSIG
        gust = int(wdws[6:8])   # 阵风
        unit = wdws[8:]    # 阵风单位
    else:
        gust = None
        unit = wdws[5:]

    if unit == 'KT':
        # 以KT作为风速单位的示例：METAR VHHH 250630Z 30009KT 270V340 9999 FEW022 26/16 Q1015 NOSIG
        # 将knots转为m/s
        if ws:
            ws = int(int(ws) * 0.5144444)
        if gust:
            gust = int(int(gust) * 0.5144444)

    dataset['wind_direction'] = wd
    dataset['wind_direction_units'] = 'degree'
    dataset['wind_speed'] = ws
    dataset['wind_speed_units'] = 'm/s'
    dataset['gust'] = gust
    dataset['wind_direction_range'] = wdrg

    # 能见度字段
    visstr = get_field_text('vis', no_trend_text)
    if visstr:
        if visstr == '9999':
            dataset['visibility'] = 99999  # 能见度大于10000用99999代替
        elif visstr == '0000':
            dataset['visibility'] = 50
        else:
            dataset['visibility'] = int(visstr)
    else:
        # CAVOK 设为 99999
        dataset['visibility'] = 99999

    dataset['visibility_units'] = 'm'

    # 好天气（CAVOK）
    cavok = get_field_text('cavok', no_trend_text)
    if cavok:
        dataset['cavok'] = True
    else:
        dataset['cavok'] = False

    # 温度/露点
    tempstr = get_field_text('temp/dew', no_trend_text)
    if tempstr:
        temp, dewtemp = tempstr.split('/')
        temp = int(temp.replace('M', '-'))
        dewtemp = int(dewtemp.replace('M', '-'))
    else:
        temp = None
        dewtemp = None

    dataset['temperature'] = temp
    dataset['dew_temperature'] = dewtemp
    dataset['temperature_units'] = 'degree C'

    # 修正海平面气压
    qnhstr = get_field_text('qnh', no_trend_text)
    if qnhstr:
        if qnhstr.startswith('Q'):
            qnh = int(qnhstr[1:])  # 清除0值补位
        elif qnhstr.startswith('A'): 
            qnh = int(int(qnhstr[1:]) * 33.8638)  # inHg -> hPa
            dataset['qnh'] = qnh
    else:
        dataset['qnh'] = None

    dataset['qnh_units'] = 'hPa'

    # 云量/云高
    cloudstrs = get_field_text('cloud', no_trend_text, mod='all')
    if cloudstrs:
        cloudstrs = sorted(cloudstrs)
        cloudgroups = []
        for cloudstr in cloudstrs:
            if 'CB' in cloudstr:
                cloud_type = 'cumulonimbus'
            elif 'TCU' in cloudstr:
                cloud_type = 'altocumulus'
            else:
                cloud_type = None

            cloudstr = cloudstr.replace('CB', '')
            cloudstr = cloudstr.replace('///', '')
            cloudstr = cloudstr.replace('TCU', '')

            if len(cloudstr) == 3:
                # 不带云高的示例：METAR ZBHH 242100Z 05002MPS 7000 NSC 01/M04 Q1023 NOSIG
                height = None
            else:
                # 带有云高的示例：METAR ZBDS 250000Z 29003MPS 9999 FEW040 04/M08 Q1023 NOSIG
                height = int(cloudstr[3:]) * 20
            mask = cloudstr[:3]
            cloud_record = {'cloud_mask': mask,
                            'cloud_height': height,
                            'cloud_height_units': 'm',
                            'cloud_type': cloud_type}

            cloudgroups.append(cloud_record)
    else:
        cloudgroups = None
    dataset['cloud'] = cloudgroups

    # 天气现象
    dataset['weather'] = get_field_text('weather', no_trend_text, mod='all')
    if get_field_text('auto', no_trend_text):
        dataset['auto'] = True
    else:
        dataset['auto'] = False

    # TODO 趋势报解析
    return dataset


if __name__ == '__main__':
    pass
