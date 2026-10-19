KEYS = [
    {"i": 0, "label": "W", "x": 1.0, "y": 0.0, "w": 1.0},
    {"i": 1, "label": "A", "x": 0.0, "y": 1.0, "w": 1.0},
    {"i": 2, "label": "S", "x": 1.0, "y": 1.0, "w": 1.0},
    {"i": 3, "label": "D", "x": 2.0, "y": 1.0, "w": 1.0},
    {"i": 4, "label": "SHIFT", "x": 0.0, "y": 2.0, "w": 1.0},
    {"i": 5, "label": "CTRL", "x": 1.0, "y": 2.0, "w": 1.0},
    {"i": 6, "label": "SPACE", "x": 2.0, "y": 2.0, "w": 1.5},
]

GRID_W = 3.5
GRID_H = 3.0

LED_OF_KEY = {0: 1, 1: 6, 2: 3, 3: 2, 4: 4, 5: 5, 6: 0}
KEY_OF_LED = {v: k for k, v in LED_OF_KEY.items()}

ORIGINAL_CODES = {0: ord("w"), 1: ord("a"), 2: ord("s"), 3: ord("d"), 4: 0x81, 5: 0x80, 6: 0x20}

KEY_LABEL = {k["i"]: k["label"] for k in KEYS}

NEIGHBORS = {
    0: [1, 2, 3],
    1: [0, 2, 4, 5],
    2: [0, 1, 3],
    3: [0, 2, 5, 6],
    4: [1, 5],
    5: [1, 4, 6],
    6: [3, 5],
}

CONNECTOR_SIDE = {
    0: "top",
    1: "left",
    2: "center",
    3: "right",
    4: "left",
    5: "center",
    6: "right",
}
