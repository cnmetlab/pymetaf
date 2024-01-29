GET_FIELD_TEXT_CASE = [
    {
        "kwargs": {
            "field": "kind",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "METAR",
    },
    {
        "kwargs": {
            "field": "icao",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "ZBAA",
    },
    {
        "kwargs": {
            "field": "time",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "311400Z",
    },
    {
        "kwargs": {
            "field": "wind",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "01002MPS",
    },
    {
        "kwargs": {
            "field": "temp/dew",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "14/12",
    },
    {
        "kwargs": {
            "field": "qnh",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "Q1009",
    },
    {
        "kwargs": {
            "field": "cavok",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "CAVOK",
    },
    {
        "kwargs": {
            "field": "observ",
            "text": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009 NOSIG=",
        },
        "result": "METAR ZBAA 311400Z 01002MPS CAVOK 14/12 Q1009",
    },
    {
        "kwargs": {
            "field": "observ",
            "text": "METAR ZBCZ 161200Z AUTO 22004MPS 8000 // ////// 21/19 Q1008=",
        },
        "result": "METAR ZBCZ 161200Z AUTO 22004MPS 8000 // ////// 21/19 Q1008",
    },
    {
        "kwargs": {
            "field": "vis",
            "text": "METAR ZUUU 160930Z 01004MPS 340V040 5000 -SHRA BR FEW006 FEW026CB SCT026 23/23 Q1001 RESHRA NOSIG=",
        },
        "result": "5000",
    },
    {
        "kwargs": {
            "field": "weather",
            "text": "METAR ZUUU 160930Z 01004MPS 340V040 5000 -SHRA BR FEW006 FEW026CB SCT026 23/23 Q1001 RESHRA NOSIG=",
            "mod": "first",
        },
        "result": "-SHRA",
    },
    {
        "kwargs": {
            "field": "weather",
            "text": "METAR ZUUU 160930Z 01004MPS 340V040 5000 -SHRA BR FEW006 FEW026CB SCT026 23/23 Q1001 RESHRA NOSIG=",
            "mod": "all",
        },
        "result": ["-SHRA", "BR", "RESHRA"],
    },
    {
        "kwargs": {
            "field": "wind",
            "text": "METAR ZUUU 160930Z 01004MPS 340V040 5000 -SHRA BR FEW006 FEW026CB SCT026 23/23 Q1001 RESHRA NOSIG=",
        },
        "result": "01004MPS 340V040",
    },
    {
        "kwargs": {
            "field": "cloud",
            "text": "METAR ZUUU 160930Z 01004MPS 340V040 5000 -SHRA BR FEW006 FEW026CB SCT026 23/23 Q1001 RESHRA NOSIG=",
            "mod": "all",
        },
        "result": ["FEW006", "FEW026CB", "SCT026"],
    },
    {
        "kwargs": {
            "field": "cloud",
            "text": "METAR ZUUU 161030Z 02005MPS 330V050 8000 FEW006 FEW026TCU SCT026 24/22 Q1002 NOSIG=",
            "mod": "all",
        },
        "result": ["FEW006", "FEW026TCU", "SCT026"],
    },
    {
        "kwargs": {
            "field": "wind",
            "text": "METAR ZBHD 311500Z VRB03MPS 3000 TS BR FEW040CB 22/19 Q1006 NOSIG",
        },
        "result": "VRB03MPS",
    },
    {
        "kwargs": {
            "field": "wind",
            "text": "METAR ZYAS 250500Z 21009G14MPS 6000 NSC 18/08 Q1018 NOSIG",
        },
        "result": "21009G14MPS",
    },
    {
        "kwargs": {
            "field": "vvis",
            "text": "METAR ZSYC 242300Z 26001MPS 0150 R06/0200N FG VV003 10/09 Q1024 NOSIG",
        },
        "result": "VV003",
    },
]
