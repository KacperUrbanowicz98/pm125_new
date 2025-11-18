# database.py - WERSJA Z LOGGEREM
import csv
import os
import time
import logging
from typing import List
from datetime import datetime

# ===== KONFIGURACJA LOGGERA =====
logger = logging.getLogger(__name__)


class CSVDatabase:
    def __init__(self, base_filename: str = "raport_testow", max_rows: int = 1_000_000):
        self.base_filename = base_filename
        self.max_rows = max_rows
        self.current_index = 1
        self.current_filename = f"{base_filename}_{self.current_index}.csv"

        while os.path.exists(self.current_filename):
            row_count = self._count_rows(self.current_filename)
            if row_count >= max_rows:
                self.current_index += 1
                self.current_filename = f"{base_filename}_{self.current_index}.csv"
            else:
                break

    def _count_rows(self, filename: str) -> int:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 0
        except Exception as e:
            print(f"Błąd liczenia wierszy: {e}")
            logger.error(f"Błąd liczenia wierszy: {e}")
            return 0

    def _get_headers(self) -> List[str]:
        """NAGŁÓWKI BEZ POLSKICH ZNAKÓW"""
        return [
            "Data i godzina",
            "HRID",
            "Numer seryjny",

            "5V - Wynik",
            "5V - Min napiecie [V]",
            "5V - Max napiecie [V]",

            "9V - Wynik",
            "9V - Min napiecie [V]",
            "9V - Max napiecie [V]",

            "12V - Wynik",
            "12V - Min napiecie [V]",
            "12V - Max napiecie [V]",

            "15V - Wynik",
            "15V - Min napiecie [V]",
            "15V - Max napiecie [V]",

            "Wynik koncowy",
            "Czas testu [s]"
        ]

    def save_result(self, test_result, max_retries: int = 3, retry_delay: float = 1.0):
        """Zapisz wynik testu do CSV z retry"""
        row_count = self._count_rows(self.current_filename)
        if row_count >= self.max_rows:
            self.current_index += 1
            self.current_filename = f"{self.base_filename}_{self.current_index}.csv"

        file_exists = os.path.exists(self.current_filename)

        for attempt in range(max_retries):
            try:
                # ŚREDNIK jako delimiter (polski Excel)
                with open(self.current_filename, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)

                    if not file_exists:
                        writer.writerow(self._get_headers())

                    writer.writerow(test_result.to_csv_row())

                print(f"✓ Wynik zapisany do: {self.current_filename}")
                logger.info(f"Wynik zapisany do: {self.current_filename}")
                return True

            except PermissionError as e:
                print(f"⚠ Próba {attempt + 1}/{max_retries}: Plik zajęty (Excel otwarty?)")
                logger.warning(f"PermissionError (próba {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    print(f"   Ponawiam za {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print("✗ Nie udało się zapisać do głównego pliku")
                    logger.error(f"BŁĄD ZAPISU: Plik zajęty po {max_retries} próbach")
                    return False

            except IOError as e:
                print(f"⚠ IOError (próba {attempt + 1}/{max_retries}): {e}")
                logger.warning(f"IOError (próba {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    print(f"   Ponawiam za {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"BŁĄD ZAPISU: IOError po {max_retries} próbach")
                    return False

            except Exception as e:
                print(f"✗ Błąd zapisu (próba {attempt + 1}/{max_retries}): {e}")
                logger.error(f"Błąd zapisu (próba {attempt + 1}/{max_retries}): {e}", exc_info=True)

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return False

        return False

    def _save_to_backup(self, test_result) -> bool:
        """Zapisz do pliku backup gdy główny plik jest zajęty"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.base_filename}_BACKUP_{timestamp}.csv"

        try:
            with open(backup_filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(self._get_headers())
                writer.writerow(test_result.to_csv_row())

            print(f"✓ BACKUP: Wynik zapisany do: {backup_filename}")
            logger.warning(f"BACKUP: Wynik zapisany do: {backup_filename}")
            print(f"⚠ UWAGA: Zamknij Excel i połącz pliki ręcznie!")
            return False

        except Exception as e:
            print(f"✗ KRYTYCZNY BŁĄD: Nie udało się zapisać nawet do backup: {e}")
            logger.critical(f"KRYTYCZNY BŁĄD zapisu do backup: {e}", exc_info=True)
            return False
