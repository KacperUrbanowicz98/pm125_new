# hardware_interface.py - KOMPLETNA WERSJA Z INSTANT LOAD
import subprocess
import os
import re
import time
from typing import Optional, List, Dict


class PM125Interface:
    """Interfejs do testera PassMark PM125 przez USBPDConsole.exe"""

    def __init__(self, console_path: str = None, device_serial: str = None):
        """
        console_path: ścieżka do USBPDConsole.exe
        device_serial: numer seryjny urządzenia PM125 (np. "PMPD111111")
                      Jeśli None, użyje pierwszego dostępnego
        """
        if console_path is None:
            console_path = r"C:\Users\kacper.urbanowicz\Downloads\USBPDAPI_1.0.1016 (1)\USBPDConsole Release\USBPDConsole.exe"

        if not os.path.exists(console_path):
            raise FileNotFoundError(
                f"Nie znaleziono USBPDConsole.exe: {console_path}\n"
                f"Zaktualizuj ścieżkę w config.py lub hardware_interface.py"
            )

        self.console_path = console_path
        self.device_serial = device_serial if device_serial else "Any"
        self.connected = False
        self.current_profile = None

        # Test połączenia
        if not self._test_connection():
            raise ConnectionError(
                "Nie można połączyć z PM125.\n"
                "Sprawdź czy:\n"
                "1. Urządzenie jest podłączone przez Monitoring Port (USB Micro B)\n"
                "2. Sterowniki są zainstalowane\n"
                "3. Zasilacz jest podłączony do portu SINK"
            )

        self.connected = True
        info = self.get_device_info()
        print(f"✓ Połączono z PM125 (Serial: {info.get('serial', 'N/A')})")

    def _run_command(self, *args, timeout: int = 5) -> Optional[str]:
        """
        Uruchom komendę USBPDConsole
        Zwraca output lub None jeśli błąd
        """
        try:
            cmd = [self.console_path, '-d', self.device_serial] + list(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"Błąd komendy (return code {result.returncode}): {error_msg}")
                return None

        except subprocess.TimeoutExpired:
            print(f"Timeout wykonania komendy: {' '.join(args)}")
            return None
        except Exception as e:
            print(f"Błąd wykonania komendy: {e}")
            return None

    def _test_connection(self) -> bool:
        """Test czy urządzenie jest połączone"""
        output = self._run_command('-c')
        if output and 'STATUS:CONNECTED' in output:
            return True
        return False

    def disconnect(self):
        """Rozłącz urządzenie (ustaw obciążenie na 0)"""
        if self.connected:
            self.set_load(0)
            self.connected = False
            print("✓ Rozłączono z PM125 (obciążenie = 0mA)")

    def get_available_profiles(self) -> List[Dict[str, any]]:
        """
        Pobierz listę dostępnych profili
        Zwraca: lista dict z 'index', 'voltage_mv', 'current_ma', 'type'
        """
        output = self._run_command('-p')

        if not output:
            print("Błąd pobierania profili")
            return []

        profiles = []
        lines = output.split('\n')

        for idx, line in enumerate(lines, start=1):
            if 'VOLTAGE' in line or 'mV' in line:
                voltage_match = re.search(r'(\d+)\s*mV', line)
                current_match = re.search(r'(\d+)\s*mA', line)

                if voltage_match:
                    profiles.append({
                        'index': idx,
                        'voltage_mv': int(voltage_match.group(1)),
                        'current_ma': int(current_match.group(1)) if current_match else 0,
                        'type': 'FIXED'
                    })

        return profiles

    def set_profile(self, profile_index: int) -> bool:
        """
        Wybierz profil napięcia przez indeks
        profile_index: 1=5V, 2=9V, 3=12V, 4=15V (zazwyczaj)
        """
        try:
            output = self._run_command('-v', str(profile_index))

            if output is not None:
                self.current_profile = profile_index
                time.sleep(0.5)
                print(f"✓ Ustawiono profil #{profile_index}")
                return True

            print(f"✗ Nie udało się ustawić profilu #{profile_index}")
            return False

        except Exception as e:
            print(f"Błąd ustawiania profilu: {e}")
            return False

    def set_profile_by_voltage(self, voltage: float) -> bool:
        """
        Wybierz profil po napięciu (5, 9, 12, 15V)
        """
        voltage_to_index = {
            5.0: 1,
            9.0: 2,
            12.0: 3,
            15.0: 4
        }

        profile_index = voltage_to_index.get(voltage)

        if profile_index is None:
            print(f"✗ Nieznane napięcie: {voltage}V")
            print(f"Dostępne: {list(voltage_to_index.keys())}")
            return False

        return self.set_profile(profile_index)

    def set_load(self, current_ma: int, instant: bool = True) -> bool:
        """
        Ustaw obciążenie w mA

        Args:
            current_ma: 0-5000 mA
            instant: True = instant jump (używa -q quick load)
                    False = slow ramp (używa -l normal load)
        """
        if not 0 <= current_ma <= 5000:
            print(f"✗ Prąd {current_ma}mA poza zakresem 0-5000mA")
            return False

        try:
            if instant:
                # -q = quick load (instant jump bez slope)
                output = self._run_command('-q', str(current_ma))
            else:
                # -l = normal load (slow ramp)
                output = self._run_command('-l', str(current_ma))

            if output is not None:
                # Bardzo krótkie opóźnienie dla instant
                time.sleep(0.05 if instant else 0.1)
                return True

            return False

        except Exception as e:
            print(f"Błąd ustawiania obciążenia: {e}")
            return False

    def read_measurements(self) -> Optional[Dict[str, float]]:
        """
        Odczytaj napięcie i prąd jednocześnie
        Zwraca: {'voltage': float, 'current': float} w V i A
        """
        output = self._run_command('-s')

        if not output:
            return None

        try:
            # Parsuj napięcie (w mV)
            voltage_match = re.search(r'VOLTAGE[:\s]+(\d+)\s*mV', output)
            if not voltage_match:
                print(f"Nie znaleziono napięcia w: {output}")
                return None
            voltage_mv = int(voltage_match.group(1))

            # Parsuj prąd (w mA)
            current_match = re.search(r'MEASURED CURRENT[:\s]+(\d+)\s*mA', output)
            if not current_match:
                print(f"Nie znaleziono prądu w: {output}")
                return None
            current_ma = int(current_match.group(1))

            return {
                'voltage': voltage_mv / 1000.0,
                'current': current_ma / 1000.0
            }

        except Exception as e:
            print(f"Błąd parsowania pomiarów: {e}")
            return None

    def read_voltage(self) -> Optional[float]:
        """Odczytaj tylko napięcie"""
        measurements = self.read_measurements()
        return measurements['voltage'] if measurements else None

    def read_current(self) -> Optional[float]:
        """Odczytaj tylko prąd"""
        measurements = self.read_measurements()
        return measurements['current'] if measurements else None

    def get_device_info(self) -> Dict[str, str]:
        """Pobierz informacje o urządzeniu"""
        info = {'serial': self.device_serial}

        output = self._run_command('-r')
        if output:
            info['config'] = output

            serial_match = re.search(r'SERIAL[:\s]+(\w+)', output)
            if serial_match:
                info['serial'] = serial_match.group(1)

        return info

    def get_connection_status(self) -> Dict[str, any]:
        """Pobierz szczegółowy status połączenia"""
        output = self._run_command('-c')

        if not output:
            return {'connected': False}

        status = {
            'connected': 'STATUS:CONNECTED' in output
        }

        if status['connected']:
            voltage_match = re.search(r'SET VOLTAGE[:\s]+(\d+)\s*mV', output)
            if voltage_match:
                status['set_voltage_mv'] = int(voltage_match.group(1))
                status['set_voltage_v'] = status['set_voltage_mv'] / 1000.0

            current_match = re.search(r'MAX CURRENT[:\s]+(\d+)\s*mA', output)
            if current_match:
                status['max_current_ma'] = int(current_match.group(1))
                status['max_current_a'] = status['max_current_ma'] / 1000.0

        return status

    def find_all_devices(self) -> List[str]:
        """Znajdź wszystkie podłączone urządzenia PM125"""
        output = self._run_command('-f')

        if not output:
            return []

        serials = re.findall(r'SERIAL[:\s]+(\w+)', output)
        return serials


def test_device_connection(console_path: str = None) -> bool:
    """Szybki test czy PM125 jest dostępny"""
    try:
        device = PM125Interface(console_path=console_path)
        info = device.get_device_info()
        print(f"✓ Urządzenie znalezione: {info.get('serial')}")
        device.disconnect()
        return True
    except Exception as e:
        print(f"✗ Błąd połączenia: {e}")
        return False


def find_devices(console_path: str = None) -> List[str]:
    """Znajdź wszystkie podłączone urządzenia"""
    try:
        device = PM125Interface(console_path=console_path)
        devices = device.find_all_devices()
        print(f"Znaleziono {len(devices)} urządzeń: {devices}")
        return devices
    except Exception as e:
        print(f"✗ Błąd wyszukiwania: {e}")
        return []
