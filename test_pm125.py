# test_pm125.py - Test podstawowy
from hardware_interface import PM125Interface
import time

# ZMIEŃ na swoją ścieżkę!
CONSOLE_PATH = r"C:\Users\kacper.urbanowicz\Downloads\USBPDAPI_1.0.1016 (1)\USBPDConsole Release\USBPDConsole.exe"

try:
    print("=== TEST POŁĄCZENIA Z PM125 ===\n")

    # Połącz
    pm125 = PM125Interface(console_path=CONSOLE_PATH)

    # Info
    info = pm125.get_device_info()
    print(f"Serial: {info.get('serial')}")

    # Status
    status = pm125.get_connection_status()
    print(f"\nStatus połączenia:")
    print(f"  Połączony: {status['connected']}")
    if 'set_voltage_v' in status:
        print(f"  Napięcie: {status['set_voltage_v']}V")
        print(f"  Max prąd: {status['max_current_a']}A")

    # Test odczytu (bez obciążenia)
    print(f"\n=== TEST ODCZYTU (obciążenie 0mA) ===")
    measurements = pm125.read_measurements()
    if measurements:
        print(f"Napięcie: {measurements['voltage']:.2f}V")
        print(f"Prąd: {measurements['current']:.3f}A")

    # Test ustawienia obciążenia
    print(f"\n=== TEST OBCIĄŻENIA 500mA ===")
    pm125.set_load(500)
    time.sleep(1)
    measurements = pm125.read_measurements()
    if measurements:
        print(f"Napięcie: {measurements['voltage']:.2f}V")
        print(f"Prąd: {measurements['current']:.3f}A")

    # Resetuj
    pm125.set_load(0)
    pm125.disconnect()

    print("\n✓ TEST ZAKOŃCZONY POMYŚLNIE!")

except Exception as e:
    print(f"\n✗ BŁĄD: {e}")
    import traceback

    traceback.print_exc()
