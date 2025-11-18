# config.py - KOMPLETNA WERSJA Z IMPORTAMI
import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any


@dataclass
class VoltageProfile:
    """Profil napięcia do testowania"""
    nominal: float
    min_voltage: float
    max_voltage: float
    test_duration_no_load: float
    test_duration_with_load: float
    load_current_ma: int
    name: str
    index: int

    def is_in_range(self, voltage: float) -> bool:
        return self.min_voltage <= voltage <= self.max_voltage

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nominal': self.nominal,
            'min_voltage': self.min_voltage,
            'max_voltage': self.max_voltage,
            'test_duration_no_load': self.test_duration_no_load,
            'test_duration_with_load': self.test_duration_with_load,
            'load_current_ma': self.load_current_ma,
            'name': self.name,
            'index': self.index
        }


@dataclass
class TestConfig:
    console_path: str = r"C:\Users\kacper.urbanowicz\Downloads\USBPDAPI_1.0.1016 (1)\USBPDConsole Release\USBPDConsole.exe"
    device_serial: str = None

    profiles: List[dict] = field(default_factory=lambda: [
        {
            'nominal': 5.0,
            'min_voltage': 4.75,
            'max_voltage': 5.5,
            'test_duration_no_load': 2.5,
            'test_duration_with_load': 2.5,
            'load_current_ma': 3000,
            'name': 'Profile 5V',
            'index': 1
        },
        {
            'nominal': 9.0,
            'min_voltage': 8.55,
            'max_voltage': 9.45,
            'test_duration_no_load': 2.5,
            'test_duration_with_load': 2.5,
            'load_current_ma': 3000,
            'name': 'Profile 9V',
            'index': 2
        },
        {
            'nominal': 12.0,
            'min_voltage': 11.4,
            'max_voltage': 12.6,
            'test_duration_no_load': 2.5,
            'test_duration_with_load': 2.5,
            'load_current_ma': 3000,
            'name': 'Profile 12V',
            'index': 3
        },
        {
            'nominal': 15.0,
            'min_voltage': 14.25,
            'max_voltage': 15.75,
            'test_duration_no_load': 2.5,
            'test_duration_with_load': 2.5,
            'load_current_ma': 2400,
            'name': 'Profile 15V',
            'index': 4
        }
    ])

    measurement_interval: float = 0.05
    max_csv_rows: int = 1_000_000

    valid_hrids: List[str] = field(default_factory=lambda: [
        "44963", "12100667", "81705", "45216", "45061", "12100171",
        "12100741", "81560", "81563", "81564", "45233", "12101333",
        "12101111", "12100174", "12100475", "12101090", "12100587",
        "12101094", "45016", "TEST", "12100524", "12101639",
        "12101644", "45466", "12100269", "12101487", "45518", "12101673"
    ])

    def save(self, filename: str = "test_config.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filename: str = "test_config.json"):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        except FileNotFoundError:
            print(f"Plik {filename} nie istnieje, tworzę domyślną konfigurację...")
            config = cls()
            config.save(filename)
            return config
        except Exception as e:
            print(f"Błąd wczytywania konfiguracji: {e}")
            return cls()

    def get_profiles(self) -> List[VoltageProfile]:
        return [VoltageProfile(**p) for p in self.profiles]

    def validate(self) -> bool:
        errors = []
        import os

        if not os.path.exists(self.console_path):
            errors.append(f"USBPDConsole.exe nie istnieje: {self.console_path}")

        if not self.profiles:
            errors.append("Brak profili")

        for profile in self.profiles:
            if profile['min_voltage'] >= profile['max_voltage']:
                errors.append(f"Profil {profile['name']}: min >= max")
            if not 0 <= profile['load_current_ma'] <= 5000:
                errors.append(f"Profil {profile['name']}: prąd 0-5000mA")

        if errors:
            print("BŁĘDY:")
            for e in errors:
                print(f"  - {e}")
            return False
        return True
