# pymetaf

[![Python package](https://github.com/cnmetlab/pymetaf/actions/workflows/python-package.yml/badge.svg)](https://github.com/cnmetlab/pymetaf/actions/workflows/python-package.yml)
[![PyPI version](https://badge.fury.io/py/pymetaf.svg)](https://badge.fury.io/py/pymetaf)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/Clarmy/pymetaf/issues)

This is a python package to parse raw METAR and TAF report text.

## Installation

1. Clone this repository and run `$ python setup.py install` in your terminal.
2. Use Pip `$ pip install pymetaf`

## Usage

```python
>>> from pymetaf import parse_text

>>> text = 'METAR ZYAS 250500Z 21009G14MPS 6000 NSC 18/08 Q1018 NOSIG'

>>> parse_text(text, 2021, 5)
{'kind': 'METAR',
 'icao': 'ZYAS',
 'datetime': '2021-05-25T05:00:00+00:00',
 'wind_direction': 210,
 'wind_direction_units': 'degree',
 'wind_speed': 9,
 'wind_speed_units': 'm/s',
 'gust': 14,
 'wind_direction_range': None,
 'cavok': False,
 'visibility': 6000,
 'visibility_units': 'm',
 'temperature': 18,
 'dew_temperature': 8,
 'temperature_units': 'degree C',
 'qnh': 1018,
 'qnh_units': 'hPa',
 'cloud': [{'cloud_mask': 0,
   'cloud_height': None,
   'cloud_height_units': 'm',
   'cloud_type': None}],
 'weather': ['Clear Sky'],
 'auto': False}
```

Enjoy it!