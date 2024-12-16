"""Define constant variables."""

DOMAIN = "crestron_tsw760"
PLATFORMS = ["sensor", "switch", "number", "text"]

ENTITIES_TO_EXPOSE = [
    {
        "type": "switch",
        "name": "Camera IsEnabled",
        "value_path": ["Device", "Camera", "IsEnabled"],
    },
    {
        "type": "switch",
        "name": "Auto-Brightness",
        "value_path": ["Device", "Display", "Lcd", "AutoBrightness", "IsEnabled"],
    },
    {
        "type": "switch",
        "name": "Enter Standby",
        "value_path": ["Device", "DeviceOperations", "EnterStandby"],
    },
    {
        "type": "switch",
        "name": "Exit Standby",
        "value_path": ["Device", "DeviceOperations", "ExitStandby"],
    },
    {
        "type": "number",
        "name": "Brightness",
        "value_path": ["Device", "Display", "Lcd", "Brightness"],
        "native_min_value": 0,
        "native_max_value": 100,
    },
    {
        "type": "number",
        "name": "Volume",
        "value_path": ["Device", "Display", "Audio", "Volume"],
        "native_min_value": 0,
        "native_max_value": 100,
    },
    {
        "type": "sensor",
        "name": "Display Status",
        "value_path": ["Device", "Display", "CurrentState"],
    },
    {
        "type": "text",
        "name": "EMS URL",
        "value_path": ["Device", "ThirdPartyApplications", "EMSUrl"],
    },
]
