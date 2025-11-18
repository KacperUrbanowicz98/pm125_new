# setup_config.py - uruchom ponownie żeby utworzyć nową konfigurację
from config import TestConfig

config = TestConfig()

# ZMIEŃ na swoją ścieżkę!
config.console_path = r"C:\Users\kacper.urbanowicz\Downloads\USBPDAPI_1.0.1016 (1)\USBPDConsole Release\USBPDConsole.exe"

config.device_serial = None

config.valid_hrids = [
    "44963", "12100667", "81705", "45216", "45061", "12100171",
    "12100741", "81560", "81563", "81564", "45233", "12101333",
    "12101111", "12100174", "12100475", "12101090", "12100587",
    "12101094", "45016", "TEST", "12100524", "12101639",
    "12101644", "45466", "12100269", "12101487", "45518", "12101673"
]

config.save()
print("✓ Konfiguracja zapisana z dwuetapowym testem!")
print("\nParametry testu:")
print("  5V:  2.5s @ 0mA + 2.5s @ 3000mA")
print("  9V:  2.5s @ 0mA + 2.5s @ 3000mA")
print(" 12V:  2.5s @ 0mA + 2.5s @ 3000mA")
print(" 15V:  2.5s @ 0mA + 2.5s @ 2400mA")
print("\nPo teście: powrót na 5V @ 0mA")
