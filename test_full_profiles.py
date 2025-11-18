# test_full_profiles.py - Test wszystkich profili napięcia
from hardware_interface import PM125Interface
import time

CONSOLE_PATH = r"C:\Users\kacper.urbanowicz\Downloads\USBPDAPI_1.0.1016 (1)\USBPDConsole Release\USBPDConsole.exe"

# Profile do testowania (index, napięcie, min, max)
PROFILES = [
    (1, 5.0, 4.75, 5.5),
    (2, 9.0, 8.55, 9.45),
    (3, 12.0, 11.4, 12.6),
    (4, 15.0, 14.25, 15.75)
]

TEST_DURATION = 5.0  # sekundy na profil
LOAD_MA = 2000  # 2A obciążenie
MEASUREMENT_INTERVAL = 0.2

try:
    print("=== TEST WSZYSTKICH PROFILI PM125 ===\n")

    pm125 = PM125Interface(console_path=CONSOLE_PATH)

    all_results = []

    for profile_idx, nominal_v, min_v, max_v in PROFILES:
        print(f"\n{'=' * 50}")
        print(f"TEST PROFILU {nominal_v}V (Index {profile_idx})")
        print(f"Zakres: {min_v}V - {max_v}V")
        print(f"{'=' * 50}")

        # Ustaw profil
        if not pm125.set_profile(profile_idx):
            print(f"✗ Błąd ustawiania profilu {profile_idx}")
            continue

        time.sleep(1.0)  # Stabilizacja napięcia

        # Ustaw obciążenie
        if not pm125.set_load(LOAD_MA):
            print(f"✗ Błąd ustawiania obciążenia")
            continue

        time.sleep(0.5)

        # Zbieranie pomiarów
        measurements = []
        start_time = time.time()
        profile_pass = True

        print(f"\nPomiary (obciążenie {LOAD_MA}mA):")
        print(f"{'Czas[s]':<10} {'Napięcie[V]':<15} {'Prąd[A]':<12} {'Status'}")
        print("-" * 50)

        while time.time() - start_time < TEST_DURATION:
            elapsed = time.time() - start_time

            data = pm125.read_measurements()
            if data:
                voltage = data['voltage']
                current = data['current']
                in_range = min_v <= voltage <= max_v

                measurements.append({
                    'time': elapsed,
                    'voltage': voltage,
                    'current': current,
                    'in_range': in_range
                })

                if not in_range:
                    profile_pass = False

                status = "✓ OK" if in_range else "✗ FAIL"
                print(f"{elapsed:<10.2f} {voltage:<15.2f} {current:<12.3f} {status}")

            time.sleep(MEASUREMENT_INTERVAL)

        # Resetuj obciążenie
        pm125.set_load(0)
        time.sleep(0.5)

        # Statystyki
        if measurements:
            voltages = [m['voltage'] for m in measurements]
            avg_voltage = sum(voltages) / len(voltages)
            min_measured = min(voltages)
            max_measured = max(voltages)

            print(f"\nStatystyki profilu {nominal_v}V:")
            print(f"  Średnie napięcie: {avg_voltage:.2f}V")
            print(f"  Min/Max: {min_measured:.2f}V / {max_measured:.2f}V")
            print(f"  Pomiarów: {len(measurements)}")
            print(f"  Wynik: {'✓ PASS' if profile_pass else '✗ FAIL'}")

            all_results.append({
                'profile': nominal_v,
                'pass': profile_pass,
                'avg_voltage': avg_voltage,
                'measurements': len(measurements)
            })

    # Podsumowanie
    print(f"\n{'=' * 50}")
    print("PODSUMOWANIE TESTÓW")
    print(f"{'=' * 50}")

    for result in all_results:
        status = "✓ PASS" if result['pass'] else "✗ FAIL"
        print(f"Profil {result['profile']:>4.0f}V: {status} (średnia: {result['avg_voltage']:.2f}V)")

    all_pass = all(r['pass'] for r in all_results)
    print(f"\n{'=' * 50}")
    print(f"WYNIK KOŃCOWY: {'✓✓✓ PASS ✓✓✓' if all_pass else '✗✗✗ FAIL ✗✗✗'}")
    print(f"{'=' * 50}")

    pm125.disconnect()

except Exception as e:
    print(f"\n✗ BŁĄD: {e}")
    import traceback

    traceback.print_exc()
