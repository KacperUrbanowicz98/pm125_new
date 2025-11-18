# test_runner.py - WERSJA FINALNA z min/max
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from config import TestConfig, VoltageProfile
from hardware_interface import PM125Interface


class TimeoutException(Exception):
    """Wyjątek rzucany przy przekroczeniu timeout"""
    pass


@dataclass
class ProfileTestResult:
    """Wynik testu pojedynczego profilu"""
    profile_name: str
    nominal_voltage: float
    measurements_no_load: List[Dict[str, float]] = field(default_factory=list)
    measurements_with_load: List[Dict[str, float]] = field(default_factory=list)
    status: str = "PENDING"

    def add_measurement(self, time_sec: float, voltage: float, current: float, phase: str):
        """
        Dodaj pomiar do listy
        phase: 'no_load' lub 'with_load'
        """
        measurement = {
            'time': time_sec,
            'voltage': voltage,
            'current': current
        }

        if phase == 'no_load':
            self.measurements_no_load.append(measurement)
        else:
            self.measurements_with_load.append(measurement)

    def finalize(self, min_v: float, max_v: float):
        """Określ czy test PASS/FAIL"""
        all_measurements = self.measurements_no_load + self.measurements_with_load

        if not all_measurements:
            self.status = "NO_DATA"
            return

        all_in_range = all(
            min_v <= m['voltage'] <= max_v
            for m in all_measurements
        )
        self.status = "PASS" if all_in_range else "FAIL"

    def get_average_voltage(self) -> float:
        """Średnie napięcie ze WSZYSTKICH pomiarów"""
        all_measurements = self.measurements_no_load + self.measurements_with_load
        if not all_measurements:
            return 0.0
        return sum(m['voltage'] for m in all_measurements) / len(all_measurements)

    def get_average_voltage_with_load(self) -> float:
        """Średnie napięcie TYLKO z obciążeniem"""
        if not self.measurements_with_load:
            return 0.0
        return sum(m['voltage'] for m in self.measurements_with_load) / len(self.measurements_with_load)

    def get_min_voltage(self) -> float:
        """Minimalne napięcie z obciążeniem"""
        if not self.measurements_with_load:
            return 0.0
        return min(m['voltage'] for m in self.measurements_with_load)

    def get_max_voltage(self) -> float:
        """Maksymalne napięcie z obciążeniem"""
        if not self.measurements_with_load:
            return 0.0
        return max(m['voltage'] for m in self.measurements_with_load)

    def get_average_current(self) -> float:
        """Średni prąd z pomiarów z obciążeniem"""
        if not self.measurements_with_load:
            return 0.0
        return sum(m['current'] for m in self.measurements_with_load) / len(self.measurements_with_load)


@dataclass
class FullTestResult:
    """Wynik kompletnego testu wszystkich profili"""
    timestamp: str
    hrid: str
    serial_number: str
    profile_results: Dict[str, ProfileTestResult]
    final_status: str
    test_duration: float

    # test_runner.py - w klasie FullTestResult
    def to_csv_row(self) -> List[str]:
        """Konwertuj wynik do wiersza CSV - PRZECINKI W LICZBACH"""
        profile_names = ['Profile 5V', 'Profile 9V', 'Profile 12V', 'Profile 15V']

        row = [
            self.timestamp,
            self.hrid,
            self.serial_number
        ]

        # Dla każdego profilu: Wynik, Min, Max
        for name in profile_names:
            result = self.profile_results.get(name)
            if result and result.status not in ["TIMEOUT", "CANCELLED", "ERROR", "NO_DATA"]:
                row.append(result.status)
                # PRZECINEK zamiast KROPKI
                row.append(f"{result.get_min_voltage():.2f}".replace('.', ','))
                row.append(f"{result.get_max_voltage():.2f}".replace('.', ','))
            else:
                row.append(result.status if result else "SKIPPED")
                row.append("N/A")
                row.append("N/A")

        # Wynik końcowy i czas (PRZECINEK)
        row.append(self.final_status)
        row.append(f"{self.test_duration:.2f}".replace('.', ','))

        return row


class TestRunner:
    """Klasa zarządzająca testami"""

    def __init__(self, config: TestConfig, hardware: PM125Interface):
        self.config = config
        self.hardware = hardware
        self.current_result: Optional[FullTestResult] = None
        self.test_timeout = 60

    def test_single_profile(
            self,
            profile: VoltageProfile,
            progress_callback=None
    ) -> ProfileTestResult:
        """
        Test jednego profilu - DWUETAPOWY z INSTANT LOAD
        """
        result = ProfileTestResult(
            profile_name=profile.name,
            nominal_voltage=profile.nominal
        )

        print(f"\n{'=' * 60}")
        print(f"Test profilu: {profile.name}")
        print(f"Zakres: {profile.min_voltage}V - {profile.max_voltage}V")
        print(f"Obciążenie: {profile.load_current_ma}mA")
        print(f"{'=' * 60}")

        if not self.hardware.set_profile(profile.index):
            result.status = "PROFILE_ERROR"
            print(f"✗ Błąd ustawiania profilu #{profile.index}")
            return result

        time.sleep(0.5)

        # ===== ETAP 1: BEZ OBCIĄŻENIA =====
        print(f"\n--- ETAP 1: BEZ OBCIĄŻENIA (0mA) ---")

        self.hardware.set_load(0, instant=True)
        time.sleep(0.1)

        start_time = time.time()

        print(f"{'Czas[s]':<10} {'Napięcie[V]':<15} {'Prąd[A]':<12} {'Status'}")
        print("-" * 50)

        while time.time() - start_time < profile.test_duration_no_load:
            elapsed = time.time() - start_time

            measurements = self.hardware.read_measurements()

            if measurements:
                voltage = measurements['voltage']
                current = measurements['current']

                result.add_measurement(elapsed, voltage, current, 'no_load')

                in_range = profile.is_in_range(voltage)
                status_str = "✓ OK" if in_range else "✗ FAIL"

                print(f"{elapsed:<10.2f} {voltage:<15.2f} {current:<12.3f} {status_str}")

                if progress_callback:
                    progress_callback(
                        elapsed=elapsed,
                        voltage=voltage,
                        current=current,
                        profile_name=f"{profile.name} (0mA)",
                        in_range=in_range
                    )

            time.sleep(self.config.measurement_interval)

        # ===== ETAP 2: Z OBCIĄŻENIEM =====
        print(f"\n--- ETAP 2: Z OBCIĄŻENIEM ({profile.load_current_ma}mA) ---")
        print(f"⚡ INSTANT skok na {profile.load_current_ma}mA...")

        if not self.hardware.set_load(profile.load_current_ma, instant=True):
            result.status = "LOAD_ERROR"
            print(f"✗ Błąd ustawiania obciążenia")
            return result

        time.sleep(0.05)

        start_time = time.time()

        print(f"{'Czas[s]':<10} {'Napięcie[V]':<15} {'Prąd[A]':<12} {'Status'}")
        print("-" * 50)

        while time.time() - start_time < profile.test_duration_with_load:
            elapsed = time.time() - start_time

            measurements = self.hardware.read_measurements()

            if measurements:
                voltage = measurements['voltage']
                current = measurements['current']

                result.add_measurement(elapsed, voltage, current, 'with_load')

                in_range = profile.is_in_range(voltage)
                status_str = "✓ OK" if in_range else "✗ FAIL"

                print(f"{elapsed:<10.2f} {voltage:<15.2f} {current:<12.3f} {status_str}")

                if progress_callback:
                    progress_callback(
                        elapsed=elapsed,
                        voltage=voltage,
                        current=current,
                        profile_name=f"{profile.name} ({profile.load_current_ma}mA)",
                        in_range=in_range
                    )

            time.sleep(self.config.measurement_interval)

        result.finalize(profile.min_voltage, profile.max_voltage)

        # Statystyki
        print(f"\nStatystyki:")
        print(f"  Pomiarów bez obciążenia: {len(result.measurements_no_load)}")
        print(f"  Pomiarów z obciążeniem: {len(result.measurements_with_load)}")
        print(f"  Średnie napięcie: {result.get_average_voltage_with_load():.2f}V")
        print(f"  Min napięcie: {result.get_min_voltage():.2f}V")
        print(f"  Max napięcie: {result.get_max_voltage():.2f}V")
        print(f"  Średni prąd: {result.get_average_current():.3f}A")
        print(f"  Wynik: {result.status}")

        self.hardware.set_load(0, instant=True)
        time.sleep(0.1)

        return result

    def run_full_test(
            self,
            hrid: str,
            serial_number: str,
            progress_callback=None
    ) -> FullTestResult:
        """Wykonaj pełny test wszystkich profili z TIMEOUT"""
        start_time = time.time()
        profile_results = {}

        print("\n" + "=" * 60)
        print(f"START TESTU (timeout: {self.test_timeout}s)")
        print(f"HRID: {hrid}")
        print(f"Numer seryjny: {serial_number}")
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        profiles = self.config.get_profiles()

        try:
            for profile in profiles:
                elapsed = time.time() - start_time
                if elapsed > self.test_timeout:
                    raise TimeoutException(f"Test przekroczył {self.test_timeout}s")

                result = self.test_single_profile(profile, progress_callback)
                profile_results[profile.name] = result

        except TimeoutException as e:
            print(f"\n✗ TIMEOUT: {e}")
            for profile in profiles:
                if profile.name not in profile_results:
                    timeout_result = ProfileTestResult(
                        profile_name=profile.name,
                        nominal_voltage=profile.nominal
                    )
                    timeout_result.status = "TIMEOUT"
                    profile_results[profile.name] = timeout_result

        except KeyboardInterrupt:
            print(f"\n✗ Test przerwany przez użytkownika")
            for profile in profiles:
                if profile.name not in profile_results:
                    cancelled_result = ProfileTestResult(
                        profile_name=profile.name,
                        nominal_voltage=profile.nominal
                    )
                    cancelled_result.status = "CANCELLED"
                    profile_results[profile.name] = cancelled_result

        except Exception as e:
            print(f"\n✗ NIEOCZEKIWANY BŁĄD: {e}")
            import traceback
            traceback.print_exc()

            for profile in profiles:
                if profile.name not in profile_results:
                    error_result = ProfileTestResult(
                        profile_name=profile.name,
                        nominal_voltage=profile.nominal
                    )
                    error_result.status = "ERROR"
                    profile_results[profile.name] = error_result

        all_pass = all(
            r.status == "PASS"
            for r in profile_results.values()
        )
        final_status = "PASS" if all_pass else "FAIL"

        test_duration = time.time() - start_time

        test_result = FullTestResult(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hrid=hrid,
            serial_number=serial_number,
            profile_results=profile_results,
            final_status=final_status,
            test_duration=test_duration
        )

        # RESET
        print("\n" + "=" * 60)
        print("RESET: Powrót na profil 5V, 0mA")
        print("=" * 60)
        try:
            self.hardware.set_profile(1)
            time.sleep(0.3)
            self.hardware.set_load(0, instant=True)
        except Exception as e:
            print(f"⚠ Błąd resetu hardware: {e}")

        # Podsumowanie
        print("\n" + "=" * 60)
        print("PODSUMOWANIE TESTU")
        print("=" * 60)
        for name, result in profile_results.items():
            if result.status == "TIMEOUT":
                print(f"⏱ {name}: TIMEOUT")
            elif result.status == "CANCELLED":
                print(f"⊗ {name}: CANCELLED")
            elif result.status == "ERROR":
                print(f"✗ {name}: ERROR")
            else:
                status_symbol = "✓" if result.status == "PASS" else "✗"
                print(f"{status_symbol} {name}: {result.status} "
                      f"(min: {result.get_min_voltage():.2f}V, "
                      f"max: {result.get_max_voltage():.2f}V)")
        print("=" * 60)
        print(f"WYNIK KOŃCOWY: {final_status}")
        print(f"Czas trwania: {test_duration:.2f}s")
        print("=" * 60 + "\n")

        self.current_result = test_result
        return test_result
