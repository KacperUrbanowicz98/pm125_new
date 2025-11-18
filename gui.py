import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import tkinter.simpledialog
from PIL import Image, ImageTk
from threading import Thread
import time
import os
import sys
from collections import deque, Counter
import logging
from datetime import datetime, timedelta
import glob

from config import TestConfig
from hardware_interface import PM125Interface
from test_runner import TestRunner
from database import CSVDatabase

log_filename = f"psu19_log_{datetime.now().strftime('%Y%m%d')}.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(log_filename, encoding='utf-8')]
)
logger = logging.getLogger(__name__)


def cleanup_old_logs(days=7):
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = glob.glob("psu19_log_*.txt")
        deleted_count = 0
        for log_file in log_files:
            try:
                date_str = log_file.replace("psu19_log_", "").replace(".txt", "")
                file_date = datetime.strptime(date_str, "%Y%m%d")
                if file_date < cutoff_date:
                    os.remove(log_file)
                    deleted_count += 1
                    logger.info(f"Usunięto stary log: {log_file}")
            except Exception as e:
                logger.warning(f"Nie można usunąć {log_file}: {e}")
        if deleted_count > 0:
            logger.info(f"Wyczyszczono {deleted_count} starych logów")
    except Exception as e:
        logger.error(f"Błąd czyszczenia logów: {e}")


cleanup_old_logs(days=7)

COLORS = {
    'primary': '#4267B2',
    'primary_dark': '#3D5A98',
    'primary_light': '#5B7FD4',
    'accent': '#3ABF6F',
    'accent_dark': '#2ECC71',
    'success': '#2ECC71',
    'error': '#E74C3C',
    'warning': '#F39C12',
    'background': '#F5F7FA',
    'card_bg': '#FFFFFF',
    'text_dark': '#2C3E50',
    'text_light': '#7F8C8D',
    'border': '#E0E6ED',
    'header_text': '#FFFFFF'
}


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_logo(file_path, size=(200, 45)):
    try:
        original_image = Image.open(file_path)
        logo_image = original_image.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(logo_image)
    except Exception as e:
        logger.warning(f"Nie można załadować logo {file_path}: {e}")
        return None


LANGUAGES = {
    'pl': {
        'app_title': "PSU19 Tester",
        'enter_hrid': "Podaj swój numer HRID:",
        'confirm_hrid': "Zatwierdź HRID",
        'scan_serial': "Zeskanuj numer seryjny:",
        'logout': "Wyloguj",
        'about': "Autor: Kacper Urbanowicz",
        'wrong_hrid': "Wprowadziłeś nieprawidłowy HRID. Spróbuj jeszcze raz.",
        'hrid_accepted': "HRID {hrid} zatwierdzony. Możesz wprowadzić numer seryjny.",
        'about_window': "PSU19 Tester v1.0\nAutor: Kacper Urbanowicz\n\nAplikacja do automatyzacji testów zasilaczy USB PD.",
        'final_result': "Wynik końcowy",
        'test_in_progress': "TEST W TRAKCIE",
        'test_wait': "Trwa testowanie zasilacza...\nProszę czekać.",
        'time_label': "Czas",
        'result_pass': "TEST ZAKOŃCZONY - PASS",
        'result_fail': "TEST ZAKOŃCZONY - FAIL",
        'test_time': "Czas testu: {time:.2f}s",
        'profile_results': "Wyniki profili:",
        'avg_voltage': "Śr. napięcie",
        'daily_stats': "📊 Statystyki dzienne",
        'recent_tests': "Historia testów",
        'serial': "Numer seryjny",
        'result': "Wynik",
        'time': "Czas",
        'date': "Data",
        'no_tests': "Brak testów",
        'retry_test': "Powtórz test",
        'serial_short': "Numer seryjny zbyt krótki (min. 5 znaków)!",
        'duplicate_warning': "Serial {serial} był już testowany {count} raz(y)!\n\nKontynuować?",
        'duplicate_error': "Serial {serial} został już przetestowany {count} razy!\n\nLimit: 2 próby.\n\nNie można kontynuować.",
        'engineering_mode': "Tryb Inżynieryjny",
        'password_prompt': "Podaj hasło:",
        'wrong_password': "Nieprawidłowe hasło!",
        'logs': "Logi",
        'refresh': "Odśwież",
        'clear': "Wyczyść",
        'statistics': "Statystyki",
        'current_session': "Statystyki bieżącej sesji",
        'total_tests': "Testów łącznie:",
        'paths': "Ścieżki",
        'changes_require_restart': "⚠️ UWAGA: Zmiany wymagają restartu aplikacji",
        'console_path': "Ścieżka do USBPDConsole.exe:",
        'pm125_serial': "Serial PM125 (auto jeśli puste):",
        'csv_folder': "Folder do CSV raportów:",
        'browse': "Przeglądaj",
        'save_paths': "Zapisz ścieżki",
        'hrid_management': "HRID",
        'available_hrids': "Aktualnie dostępne HRID",
        'new_hrid': "Nowy HRID:",
        'add': "Dodaj",
        'remove': "Usuń",
        'config': "Konfiguracja",
        'test_timeout': "Timeout testu [s]:",
        'measurement_interval': "Interwał pomiarów [s]:",
        'test_duration_no_load': "Czas testu bez obciążenia [s]:",
        'test_duration_with_load': "Czas testu z obciążeniem [s]:",
        'save_config': "Zapisz konfigurację",
        'success': "Sukces",
        'paths_saved': "Ścieżki zapisane!\n\nZrestartuj aplikację aby zastosować zmiany.",
        'config_saved': "Konfiguracja zapisana!\n\nZrestartuj aplikację aby zastosować zmiany.",
        'file_locked': "Plik zajęty",
        'csv_locked': "Plik CSV zajęty",
        'close_excel': "Plik CSV jest otwarty w Excelu!\n\nZamknij Excel i spróbuj ponownie.",
        'ok_retry': "OK - Spróbuję ponownie",
        'select_hrid_remove': "Wybierz HRID do usunięcia!",
        'confirm_remove_hrid': "Potwierdzenie",
        'remove_hrid_ask': "Usunąć HRID: {hrid}?",
        'hrid_added': "OK",
        'hrid_add_success': "Dodano HRID: {hrid}",
        'hrid_exists_warning': "Ostrzeżenie",
        'hrid_already_exists': "Ten HRID już istnieje!",
        'enter_hrid_error': "Błąd",
        'enter_hrid': "Podaj HRID!",
    },
    'en': {
        'app_title': "PSU19 Tester",
        'enter_hrid': "Enter your HRID number:",
        'confirm_hrid': "Confirm HRID",
        'scan_serial': "Scan serial number:",
        'logout': "Logout",
        'about': "Author: Kacper Urbanowicz",
        'wrong_hrid': "Invalid HRID. Try again.",
        'hrid_accepted': "HRID {hrid} accepted. You can scan the serial number.",
        'about_window': "PSU19 Tester v1.0\nAuthor: Kacper Urbanowicz\n\nUSB PD Power Supply Testing Application.",
        'final_result': "Final result",
        'test_in_progress': "TEST IN PROGRESS",
        'test_wait': "Testing power supply...\nPlease wait.",
        'time_label': "Time",
        'result_pass': "TEST COMPLETED - PASS",
        'result_fail': "TEST COMPLETED - FAIL",
        'test_time': "Test time: {time:.2f}s",
        'profile_results': "Profile results:",
        'avg_voltage': "Avg voltage",
        'daily_stats': "📊 Daily Statistics",
        'recent_tests': "Test History",
        'serial': "Serial Number",
        'result': "Result",
        'time': "Time",
        'date': "Date",
        'no_tests': "No tests yet",
        'retry_test': "Retry test",
        'serial_short': "Serial number too short (min. 5 characters)!",
        'duplicate_warning': "Serial {serial} has already been tested {count} time(s)!\n\nContinue?",
        'duplicate_error': "Serial {serial} has been tested {count} times!\n\nLimit: 2 attempts.\n\nCannot continue.",
        'engineering_mode': "Engineering Mode",
        'password_prompt': "Enter password:",
        'wrong_password': "Wrong password!",
        'logs': "Logs",
        'refresh': "Refresh",
        'clear': "Clear",
        'statistics': "Statistics",
        'current_session': "Current session statistics",
        'total_tests': "Total tests:",
        'paths': "Paths",
        'changes_require_restart': "⚠️ Changes require app restart",
        'console_path': "Path to USBPDConsole.exe:",
        'pm125_serial': "PM125 Serial (auto if empty):",
        'csv_folder': "CSV Reports Folder:",
        'browse': "Browse",
        'save_paths': "Save paths",
        'hrid_management': "HRID",
        'available_hrids': "Available HRIDs",
        'new_hrid': "New HRID:",
        'add': "Add",
        'remove': "Remove",
        'config': "Configuration",
        'test_timeout': "Test timeout [s]:",
        'measurement_interval': "Measurement interval [s]:",
        'test_duration_no_load': "Test duration no load [s]:",
        'test_duration_with_load': "Test duration with load [s]:",
        'save_config': "Save configuration",
        'success': "Success",
        'paths_saved': "Paths saved!\n\nRestart app to apply changes.",
        'config_saved': "Configuration saved!\n\nRestart app to apply changes.",
        'file_locked': "File locked",
        'csv_locked': "CSV File locked",
        'close_excel': "CSV file is open in Excel!\n\nClose Excel and try again.",
        'ok_retry': "OK - Retry",
        'select_hrid_remove': "Select HRID to remove!",
        'confirm_remove_hrid': "Confirm",
        'remove_hrid_ask': "Remove HRID: {hrid}?",
        'hrid_added': "OK",
        'hrid_add_success': "HRID added: {hrid}",
        'hrid_exists_warning': "Warning",
        'hrid_already_exists': "HRID already exists!",
        'enter_hrid_error': "Error",
        'enter_hrid': "Enter HRID!",
    },
    'ua': {
        'app_title': "PSU19 Tester",
        'enter_hrid': "Введіть свій HRID:",
        'confirm_hrid': "Підтвердити HRID",
        'scan_serial': "Скануйте серійний номер:",
        'logout': "Вийти",
        'about': "Автор: Kacper Urbanowicz",
        'wrong_hrid': "Ви ввели неправильний HRID. Спробуйте ще раз.",
        'hrid_accepted': "HRID {hrid} підтверджено. Можна зчитати серійний номер.",
        'about_window': "PSU19 Tester v1.0\nАвтор: Kacper Urbanowicz\n\nДодаток для тестування блоків живлення USB PD.",
        'final_result': "Кінцевий результат",
        'test_in_progress': "ТЕСТ ВИКОНУЄТЬСЯ",
        'test_wait': "Тестування блоку живлення...\nБудь ласка, зачекайте.",
        'time_label': "Час",
        'result_pass': "ТЕСТ ЗАВЕРШЕНО - PASS",
        'result_fail': "ТЕСТ ЗАВЕРШЕНО - FAIL",
        'test_time': "Час тесту: {time:.2f}с",
        'profile_results': "Результати профілів:",
        'avg_voltage': "Сер. напруга",
        'daily_stats': "📊 Щоденна статистика",
        'recent_tests': "Історія тестів",
        'serial': "Серійний номер",
        'result': "Результат",
        'time': "Час",
        'date': "Дата",
        'no_tests': "Немає тестів",
        'retry_test': "Повторити тест",
        'serial_short': "Серійний номер занадто короткий (мін. 5 символів)!",
        'duplicate_warning': "Серійний {serial} вже тестували {count} раз(ів)!\n\nПродовжити?",
        'duplicate_error': "Серійний {serial} тестували {count} разів!\n\nЛіміт: 2 спроби.\n\nНеможливо продовжити.",
        'engineering_mode': "Інженерний режим",
        'password_prompt': "Введіть пароль:",
        'wrong_password': "Неправильний пароль!",
        'logs': "Логи",
        'refresh': "Оновити",
        'clear': "Очистити",
        'statistics': "Статистика",
        'current_session': "Статистика поточної сесії",
        'total_tests': "Всього тестів:",
        'paths': "Шляхи",
        'changes_require_restart': "⚠️ Зміни потребують перезавантаження",
        'console_path': "Шлях до USBPDConsole.exe:",
        'pm125_serial': "Серійний PM125 (авто якщо порожньо):",
        'csv_folder': "Папка звітів CSV:",
        'browse': "Огляд",
        'save_paths': "Зберегти шляхи",
        'hrid_management': "HRID",
        'available_hrids': "Доступні HRID",
        'new_hrid': "Новий HRID:",
        'add': "Додати",
        'remove': "Видалити",
        'config': "Конфігурація",
        'test_timeout': "Час очікування тесту [s]:",
        'measurement_interval': "Інтервал вимірювання [s]:",
        'test_duration_no_load': "Тривалість тесту без навантаження [s]:",
        'test_duration_with_load': "Тривалість тесту з навантаженням [s]:",
        'save_config': "Зберегти конфігурацію",
        'success': "Успіх",
        'paths_saved': "Шляхи збережені!\n\nПеревантажте додаток",
        'config_saved': "Конфігурація збережена!\n\nПеревантажте додаток",
        'file_locked': "Файл заблокований",
        'csv_locked': "Файл CSV заблокований",
        'close_excel': "Файл CSV відкритий в Excel!\n\nЗакрийте Excel і спробуйте ще раз.",
        'ok_retry': "OK - Спробую ще раз",
        'select_hrid_remove': "Виберіть HRID для видалення!",
        'confirm_remove_hrid': "Підтвердження",
        'remove_hrid_ask': "Видалити HRID: {hrid}?",
        'hrid_added': "OK",
        'hrid_add_success': "HRID додано: {hrid}",
        'hrid_exists_warning': "Попередження",
        'hrid_already_exists': "Такий HRID вже існує!",
        'enter_hrid_error': "Помилка",
        'enter_hrid': "Введіть HRID!",
    }
}


class TestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PSU19 Tester - Reconext")
        self.root.geometry("900x760")
        self.root.minsize(850, 710)
        self.root.configure(bg=COLORS['background'])

        self.current_lang = 'pl'
        self.logged_hrid = None
        self.test_window = None
        self.last_test_serial = None
        self.test_history = deque(maxlen=5)
        self.daily_stats = {'pass': 0, 'fail': 0, 'total': 0}
        self.serial_test_count = Counter()
        self.debug_mode = False
        self.debug_key_sequence = []
        self.test_in_progress = False

        self.root.bind('<Control-Shift-D>', self._debug_key_pressed)

        logger.info("=== APLIKACJA URUCHOMIONA ===")

        try:
            self.config = TestConfig.load()
            logger.info("Konfiguracja załadowana")
        except Exception as e:
            logger.error(f"Błąd ładowania konfiguracji: {e}", exc_info=True)
            messagebox.showerror("Error", f"Cannot load config:\n{e}")
            self.root.destroy()
            return

        try:
            self.hardware = PM125Interface(console_path=self.config.console_path,
                                           device_serial=self.config.device_serial)
            logger.info("Połączono z PM125")
        except Exception as e:
            logger.error(f"Błąd połączenia: {e}", exc_info=True)
            messagebox.showerror("Error", f"Cannot connect to PM125:\n{e}")
            self.root.destroy()
            return

        self.runner = TestRunner(self.config, self.hardware)
        self.database = CSVDatabase()
        self._build_ui()

    def _build_ui(self):
        header_frame = tk.Frame(self.root, bg=COLORS['primary'], height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        try:
            reconext_logo = load_logo(resource_path("reconext_logo.jpg"), size=(55, 55))
            if reconext_logo:
                logo_label = tk.Label(header_frame, image=reconext_logo, bg=COLORS['primary'])
                logo_label.image = reconext_logo
                logo_label.pack(side=tk.LEFT, padx=20)
        except Exception as e:
            logger.warning(f"Logo error: {e}")

        title_label = tk.Label(header_frame, text=LANGUAGES[self.current_lang]['app_title'], font=("Arial", 22, "bold"),
                               fg=COLORS['header_text'], bg=COLORS['primary'])
        title_label.pack(side=tk.LEFT, padx=10)

        try:
            flags_frame = tk.Frame(header_frame, bg=COLORS['primary'])
            flags_frame.pack(side=tk.RIGHT, padx=20)

            flag_pl_img = ImageTk.PhotoImage(Image.open(resource_path("flag_pl.png")).resize((32, 24), Image.LANCZOS))
            flag_en_img = ImageTk.PhotoImage(Image.open(resource_path("flag_en.png")).resize((32, 24), Image.LANCZOS))
            flag_ua_img = ImageTk.PhotoImage(Image.open(resource_path("flag_ua.png")).resize((32, 24), Image.LANCZOS))

            for flag_img, lang in [(flag_pl_img, 'pl'), (flag_en_img, 'en'), (flag_ua_img, 'ua')]:
                btn = tk.Button(flags_frame, image=flag_img, command=lambda l=lang: self._update_language(l),
                                borderwidth=0, bg=COLORS['primary'], activebackground=COLORS['primary_dark'],
                                cursor="hand2")
                btn.image = flag_img
                btn.pack(side=tk.LEFT, padx=4)
        except Exception as e:
            logger.warning(f"Flags error: {e}")

        main_container = tk.Frame(self.root, bg=COLORS['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        login_card = tk.Frame(main_container, bg=COLORS['card_bg'], relief=tk.FLAT, borderwidth=0)
        login_card.pack(fill=tk.X, pady=(0, 15))
        shadow = tk.Frame(login_card, bg=COLORS['border'], height=2)
        shadow.pack(fill=tk.X, side=tk.BOTTOM)

        login_content = tk.Frame(login_card, bg=COLORS['card_bg'])
        login_content.pack(padx=20, pady=15)

        self.label_hrid = tk.Label(login_content, text=LANGUAGES[self.current_lang]['enter_hrid'], font=("Arial", 11),
                                   fg=COLORS['text_dark'], bg=COLORS['card_bg'])
        self.label_hrid.pack(pady=(0, 8))

        entry_frame = tk.Frame(login_content, bg=COLORS['card_bg'])
        entry_frame.pack(pady=(0, 15))

        self.entry_hrid = tk.Entry(entry_frame, font=("Arial", 14), width=16, justify="center", relief=tk.SOLID,
                                   borderwidth=2, fg=COLORS['text_dark'])
        self.entry_hrid.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_hrid.focus_set()
        self.entry_hrid.bind("<Return>", lambda e: self._confirm_hrid())

        self.button_hrid = tk.Button(entry_frame, text=LANGUAGES[self.current_lang]['confirm_hrid'],
                                     command=self._confirm_hrid, bg=COLORS['primary'], fg="white",
                                     font=("Arial", 10, "bold"), relief=tk.FLAT, padx=15, pady=6, cursor="hand2",
                                     activebackground=COLORS['primary_dark'])
        self.button_hrid.pack(side=tk.LEFT)

        self.button_logout = tk.Button(login_content, text=LANGUAGES[self.current_lang]['logout'], command=self._logout,
                                       bg=COLORS['error'], fg="white", font=("Arial", 9), relief=tk.FLAT, padx=12,
                                       pady=4, cursor="hand2", activebackground="#C0392B")
        self.button_logout.pack()

        scan_card = tk.Frame(main_container, bg=COLORS['card_bg'], relief=tk.FLAT, borderwidth=0)
        scan_card.pack(fill=tk.X, pady=(0, 15))
        shadow2 = tk.Frame(scan_card, bg=COLORS['border'], height=2)
        shadow2.pack(fill=tk.X, side=tk.BOTTOM)

        scan_content = tk.Frame(scan_card, bg=COLORS['card_bg'])
        scan_content.pack(padx=20, pady=15)

        self.serial_label = tk.Label(scan_content, text=LANGUAGES[self.current_lang]['scan_serial'],
                                     font=("Arial", 12, "bold"), fg=COLORS['text_dark'], bg=COLORS['card_bg'],
                                     state="disabled")
        self.serial_label.pack(pady=(0, 10))

        serial_frame = tk.Frame(scan_content, bg=COLORS['card_bg'])
        serial_frame.pack()

        self.entry_serial = tk.Entry(serial_frame, font=("Arial", 18), width=28, justify="center", relief=tk.SOLID,
                                     borderwidth=2, fg=COLORS['text_dark'], state="disabled")
        self.entry_serial.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_serial.bind("<Return>", lambda e: self._start_test())
        self.entry_serial.bind("<KeyRelease>", self._uppercase_serial)

        self.button_scan = tk.Button(serial_frame, text="✓ Zatwierdź", command=self._start_test, bg=COLORS['primary'],
                                     fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, padx=15, pady=6,
                                     cursor="hand2", activebackground=COLORS['primary_dark'], state="disabled")
        self.button_scan.pack(side=tk.LEFT)

        stats_card = tk.Frame(main_container, bg=COLORS['card_bg'], relief=tk.FLAT, borderwidth=0)
        stats_card.pack(fill=tk.X, pady=(0, 15))
        shadow_stats = tk.Frame(stats_card, bg=COLORS['border'], height=2)
        shadow_stats.pack(fill=tk.X, side=tk.BOTTOM)

        stats_content = tk.Frame(stats_card, bg=COLORS['card_bg'])
        stats_content.pack(padx=20, pady=12)

        self.stats_header = tk.Label(stats_content, text=LANGUAGES[self.current_lang]['daily_stats'],
                                     font=("Arial", 11, "bold"), fg=COLORS['primary'], bg=COLORS['card_bg'])
        self.stats_header.pack(pady=(0, 10))

        stats_grid = tk.Frame(stats_content, bg=COLORS['card_bg'])
        stats_grid.pack()

        pass_frame = tk.Frame(stats_grid, bg=COLORS['card_bg'], relief=tk.SOLID, borderwidth=1)
        pass_frame.grid(row=0, column=0, padx=10)
        tk.Label(pass_frame, text="✓ PASS", font=("Arial", 9, "bold"), fg=COLORS['success'], bg=COLORS['card_bg']).pack(
            padx=15, pady=(8, 4))
        self.pass_count_label = tk.Label(pass_frame, text="0", font=("Arial", 20, "bold"), fg=COLORS['success'],
                                         bg=COLORS['card_bg'])
        self.pass_count_label.pack(padx=15, pady=(0, 8))

        fail_frame = tk.Frame(stats_grid, bg=COLORS['card_bg'], relief=tk.SOLID, borderwidth=1)
        fail_frame.grid(row=0, column=1, padx=10)
        tk.Label(fail_frame, text="✗ FAIL", font=("Arial", 9, "bold"), fg=COLORS['error'], bg=COLORS['card_bg']).pack(
            padx=15, pady=(8, 4))
        self.fail_count_label = tk.Label(fail_frame, text="0", font=("Arial", 20, "bold"), fg=COLORS['error'],
                                         bg=COLORS['card_bg'])
        self.fail_count_label.pack(padx=15, pady=(0, 8))

        rate_frame = tk.Frame(stats_grid, bg=COLORS['card_bg'], relief=tk.SOLID, borderwidth=1)
        rate_frame.grid(row=0, column=2, padx=10)
        tk.Label(rate_frame, text="📈 PASS Rate", font=("Arial", 9, "bold"), fg=COLORS['accent'],
                 bg=COLORS['card_bg']).pack(padx=15, pady=(8, 4))
        self.pass_rate_label = tk.Label(rate_frame, text="0.0%", font=("Arial", 20, "bold"), fg=COLORS['accent'],
                                        bg=COLORS['card_bg'])
        self.pass_rate_label.pack(padx=15, pady=(0, 8))

        history_card = tk.Frame(main_container, bg=COLORS['card_bg'], relief=tk.FLAT, borderwidth=0)
        history_card.pack(fill=tk.BOTH, expand=True)
        shadow3 = tk.Frame(history_card, bg=COLORS['border'], height=2)
        shadow3.pack(fill=tk.X, side=tk.BOTTOM)

        history_header = tk.Frame(history_card, bg=COLORS['card_bg'])
        history_header.pack(fill=tk.X, padx=20, pady=(15, 8))

        self.history_title = tk.Label(history_header, text="📋 " + LANGUAGES[self.current_lang]['recent_tests'],
                                      font=("Arial", 11, "bold"), fg=COLORS['primary'], bg=COLORS['card_bg'])
        self.history_title.pack(side=tk.LEFT)

        history_content = tk.Frame(history_card, bg=COLORS['card_bg'])
        history_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Treeview", background=COLORS['card_bg'], foreground=COLORS['text_dark'], rowheight=28,
                        fieldbackground=COLORS['card_bg'], borderwidth=0, font=("Arial", 9))
        style.configure("Custom.Treeview.Heading", background=COLORS['primary_light'], foreground=COLORS['header_text'],
                        font=("Arial", 9, "bold"), borderwidth=0)
        style.map('Custom.Treeview', background=[('selected', COLORS['border'])])

        columns = ('date', 'serial', 'result', 'time')
        self.history_tree = ttk.Treeview(history_content, columns=columns, show='headings', height=4, selectmode='none',
                                         style="Custom.Treeview")

        self.history_tree.heading('date', text=LANGUAGES[self.current_lang]['date'])
        self.history_tree.heading('serial', text=LANGUAGES[self.current_lang]['serial'])
        self.history_tree.heading('result', text=LANGUAGES[self.current_lang]['result'])
        self.history_tree.heading('time', text=LANGUAGES[self.current_lang]['time'])

        self.history_tree.column('date', width=120, anchor='center')
        self.history_tree.column('serial', width=350, anchor='w')
        self.history_tree.column('result', width=100, anchor='center')
        self.history_tree.column('time', width=80, anchor='center')

        scrollbar = ttk.Scrollbar(history_content, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_tree.tag_configure('pass', foreground=COLORS['success'], font=("Arial", 9, "bold"))
        self.history_tree.tag_configure('fail', foreground=COLORS['error'], font=("Arial", 9, "bold"))

        self.no_tests_label = tk.Label(history_content, text=LANGUAGES[self.current_lang]['no_tests'],
                                       font=("Arial", 12), fg=COLORS['text_light'], bg=COLORS['card_bg'])

        footer = tk.Frame(self.root, bg=COLORS['background'], height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.author_label = tk.Label(footer, text=LANGUAGES[self.current_lang]['about'], font=("Arial", 9),
                                     fg=COLORS['text_light'], bg=COLORS['background'], cursor="hand2")
        self.author_label.pack(side=tk.LEFT, padx=15, pady=8)
        self.author_label.bind("<Button-1>", lambda e: self._show_about())

        try:
            logo_image = load_logo(resource_path("logo.png"), size=(150, 35))
            if logo_image:
                logo_label = tk.Label(footer, image=logo_image, bg=COLORS['background'])
                logo_label.image = logo_image
                logo_label.pack(side=tk.RIGHT, padx=15, pady=5)
        except Exception as e:
            logger.warning(f"Footer logo error: {e}")

    def _update_stats(self):
        total = self.daily_stats['total']
        pass_count = self.daily_stats['pass']
        fail_count = self.daily_stats['fail']
        pass_rate = (pass_count / total * 100) if total > 0 else 0

        self.pass_count_label.config(text=str(pass_count))
        self.fail_count_label.config(text=str(fail_count))
        self.pass_rate_label.config(text=f"{pass_rate:.1f}%")

    def _uppercase_serial(self, event):
        current_text = self.entry_serial.get()
        if current_text != current_text.upper():
            cursor_position = self.entry_serial.index(tk.INSERT)
            self.entry_serial.delete(0, tk.END)
            self.entry_serial.insert(0, current_text.upper())
            self.entry_serial.icursor(cursor_position)

    def _add_to_history(self, serial: str, result: str, test_time: float, test_date: str):
        self.test_history.append({'date': test_date, 'serial': serial.upper(), 'result': result, 'time': test_time})
        self._refresh_history_display()

    def _refresh_history_display(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if len(self.test_history) > 0:
            self.no_tests_label.pack_forget()

            for test_data in reversed(self.test_history):
                result_icon = "✓ PASS" if test_data['result'] == "PASS" else "✗ FAIL"
                time_str = f"{test_data['time']:.1f}s"

                date_str = test_data['date']
                try:
                    date_parts = date_str.split()
                    date_only = date_parts[0].split('-')
                    time_only = date_parts[1].split(':')
                    formatted_date = f"{date_only[2]}.{date_only[1]} {time_only[0]}:{time_only[1]}"
                except:
                    formatted_date = date_str

                tag = 'pass' if test_data['result'] == "PASS" else 'fail'
                self.history_tree.insert('', 'end', values=(formatted_date, test_data['serial'], result_icon, time_str),
                                         tags=(tag,))
        else:
            self.no_tests_label.place(relx=0.5, rely=0.5, anchor='center')

    def _update_language(self, lang: str):
        self.current_lang = lang
        self.label_hrid.config(text=LANGUAGES[lang]['enter_hrid'])
        self.button_hrid.config(text=LANGUAGES[lang]['confirm_hrid'])
        self.serial_label.config(text=LANGUAGES[lang]['scan_serial'])
        self.button_logout.config(text=LANGUAGES[lang]['logout'])
        self.author_label.config(text=LANGUAGES[lang]['about'])

        self.stats_header.config(text=LANGUAGES[lang]['daily_stats'])
        self.history_title.config(text="📋 " + LANGUAGES[lang]['recent_tests'])

        self.history_tree.heading('date', text=LANGUAGES[lang]['date'])
        self.history_tree.heading('serial', text=LANGUAGES[lang]['serial'])
        self.history_tree.heading('result', text=LANGUAGES[lang]['result'])
        self.history_tree.heading('time', text=LANGUAGES[lang]['time'])
        self.no_tests_label.config(text=LANGUAGES[lang]['no_tests'])

        logger.info(f"Język zmieniony na: {lang}")

    def _confirm_hrid(self):
        hrid = self.entry_hrid.get().strip()

        if hrid not in self.config.valid_hrids:
            messagebox.showwarning("Error", LANGUAGES[self.current_lang]['wrong_hrid'])
            logger.warning(f"Nieprawidłowy HRID: {hrid}")
            return

        self.logged_hrid = hrid
        self.entry_hrid.config(state="disabled")
        self.serial_label.config(state="normal")
        self.entry_serial.config(state="normal")
        self.button_scan.config(state="normal")
        self.entry_serial.focus_set()

        messagebox.showinfo("OK", LANGUAGES[self.current_lang]['hrid_accepted'].format(hrid=hrid))
        logger.info(f"HRID zatwierdzony: {hrid}")

    def _logout(self):
        logger.info(f"Wylogowano: {self.logged_hrid}")
        logger.info(f"Statystyki sesji: {self.daily_stats}")

        self.daily_stats = {'pass': 0, 'fail': 0, 'total': 0}
        self._update_stats()
        self.serial_test_count.clear()

        self.logged_hrid = None
        self.entry_hrid.config(state="normal")
        self.entry_hrid.delete(0, tk.END)
        self.entry_hrid.focus_set()
        self.entry_serial.config(state="disabled")
        self.entry_serial.delete(0, tk.END)
        self.button_scan.config(state="disabled")
        self.serial_label.config(state="disabled")

    def _validate_serial(self, serial: str) -> bool:
        if len(serial) < 5:
            messagebox.showwarning("Error", LANGUAGES[self.current_lang]['serial_short'])
            logger.warning(f"Serial za krótki: {serial}")
            return False

        current_count = self.serial_test_count[serial]
        if current_count >= 2:
            messagebox.showerror("Limit exceeded", LANGUAGES[self.current_lang]['duplicate_error'].format(serial=serial,
                                                                                                          count=current_count))
            logger.error(f"Limit duplikatów: {serial}")
            return False

        if current_count > 0:
            result = messagebox.askyesno("Warning",
                                         LANGUAGES[self.current_lang]['duplicate_warning'].format(serial=serial,
                                                                                                  count=current_count))
            if not result:
                logger.info(f"Test anulowany: {serial}")
                return False

        logger.info(f"Walidacja OK: {serial}")
        return True

    def _lock_ui(self):
        self.test_in_progress = True
        self.entry_hrid.config(state="disabled")
        self.entry_serial.config(state="disabled")
        self.button_hrid.config(state="disabled")
        self.button_logout.config(state="disabled")
        self.button_scan.config(state="disabled")

    def _unlock_ui(self):
        self.test_in_progress = False
        if self.logged_hrid:
            self.entry_serial.config(state="normal")
            self.button_scan.config(state="normal")
            self.entry_serial.focus_set()
        else:
            self.entry_hrid.config(state="normal")
            self.button_hrid.config(state="normal")
        self.button_logout.config(state="normal")

    def _start_test(self, retry_serial=None):
        if retry_serial:
            serial = retry_serial
        else:
            serial = self.entry_serial.get().strip().upper()

        if not serial:
            return

        if not self._validate_serial(serial):
            return

        self._lock_ui()
        logger.info(f"=== START TESTU === Serial: {serial}, HRID: {self.logged_hrid}")
        Thread(target=self._run_test_thread, args=(serial,), daemon=True).start()

    def _run_test_thread(self, serial: str):
        try:
            self.root.after(0, self._create_test_window)
            time.sleep(0.1)

            result = self.runner.run_full_test(hrid=self.logged_hrid, serial_number=serial, progress_callback=None)
            logger.info(f"Test zakończony: {result.final_status}, czas: {result.test_duration:.2f}s")

            save_success = self.database.save_result(result, max_retries=3, retry_delay=1.0)
            logger.info(f"Wynik zapisu: {save_success}")

            if not save_success:
                logger.warning("Wyświetlam okno Excel")
                self.root.after(0, self._show_excel_open_dialog)

            self.daily_stats['total'] += 1
            if result.final_status == "PASS":
                self.daily_stats['pass'] += 1
            else:
                self.daily_stats['fail'] += 1

            self.serial_test_count[serial] += 1
            self.last_test_serial = serial

            self.root.after(0, self._update_stats)
            self.root.after(0, self._add_to_history, serial, result.final_status, result.test_duration,
                            result.timestamp)

            if hasattr(self, 'test_window') and self.test_window and self.test_window.winfo_exists():
                self.test_window.destroy()

            time.sleep(0.2)
            self.root.after(0, self._show_final_result, result, save_success)

        except Exception as e:
            logger.error(f"BŁĄD: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error:\n{str(e)}")
        finally:
            self.root.after(0, self._unlock_ui)

    def _create_test_window(self):
        self.test_window = tk.Toplevel(self.root)
        self.test_window.title("TEST")
        self.test_window.geometry("500x300")
        self.test_window.configure(bg=COLORS['background'])

        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        self.test_window.geometry(f"+{root_x + 200}+{root_y + 180}")
        self.test_window.protocol("WM_DELETE_WINDOW", lambda: None)

        header_frame = tk.Frame(self.test_window, bg=COLORS['primary'], height=65)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="⚙️ " + LANGUAGES[self.current_lang]['test_in_progress'],
                 font=("Arial", 20, "bold"), fg="white", bg=COLORS['primary']).pack(expand=True)

        content_frame = tk.Frame(self.test_window, bg=COLORS['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(content_frame, text=LANGUAGES[self.current_lang]['test_wait'], font=("Arial", 12),
                 fg=COLORS['text_dark'], bg=COLORS['background']).pack(pady=(10, 20))

        self.progress_canvas = tk.Canvas(content_frame, width=400, height=30, bg="white", highlightthickness=1,
                                         highlightbackground=COLORS['border'])
        self.progress_canvas.pack(pady=20)

        self.progress_position = 0
        self.progress_direction = 1
        self._animate_progress()

        self.time_label = tk.Label(content_frame, text=f"{LANGUAGES[self.current_lang]['time_label']}: 00:00",
                                   font=("Arial", 14, "bold"), fg=COLORS['accent'], bg=COLORS['background'])
        self.time_label.pack(pady=15)

        self.test_start_time = time.time()
        self._update_test_timer()

    def _animate_progress(self):
        if not hasattr(self, 'progress_canvas') or not self.test_window or not self.test_window.winfo_exists():
            return

        try:
            self.progress_canvas.delete("all")
            self.progress_canvas.create_rectangle(0, 0, 400, 30, fill="#EEEEEE", outline=COLORS['border'])

            bar_width = 100
            self.progress_canvas.create_rectangle(self.progress_position, 3, self.progress_position + bar_width, 27,
                                                  fill=COLORS['primary'], outline="")

            self.progress_position += self.progress_direction * 6

            if self.progress_position >= 400 - bar_width:
                self.progress_direction = -1
            elif self.progress_position <= 0:
                self.progress_direction = 1

            self.test_window.after(40, self._animate_progress)
        except:
            pass

    def _update_test_timer(self):
        if not hasattr(self, 'time_label') or not self.test_window or not self.test_window.winfo_exists():
            return

        try:
            elapsed = time.time() - self.test_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)

            self.time_label.config(text=f"{LANGUAGES[self.current_lang]['time_label']}: {minutes:02d}:{seconds:02d}")
            self.test_window.after(1000, self._update_test_timer)
        except:
            pass

    def _show_excel_open_dialog(self):
        excel_win = tk.Toplevel(self.root)
        excel_win.title("⚠️ File locked")
        excel_win.geometry("450x200")
        excel_win.configure(bg=COLORS['background'])
        excel_win.transient(self.root)
        excel_win.grab_set()

        header = tk.Frame(excel_win, bg=COLORS['error'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚠️ CSV File locked", font=("Arial", 16, "bold"), fg="white", bg=COLORS['error']).pack(
            expand=True)

        content = tk.Frame(excel_win, bg=COLORS['background'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(content, text=LANGUAGES[self.current_lang]['close_excel'], font=("Arial", 12), fg=COLORS['text_dark'],
                 bg=COLORS['background'], justify=tk.CENTER).pack(pady=(0, 20))

        tk.Button(content, text="OK - " + LANGUAGES[self.current_lang]['ok_retry'], command=excel_win.destroy,
                  bg=COLORS['primary'], fg="white", font=("Arial", 11, "bold"), padx=20, pady=8, cursor="hand2").pack()

        excel_win.geometry(f"+{self.root.winfo_x() + 225}+{self.root.winfo_y() + 200}")

    def _show_final_result(self, result, save_success=True):
        result_window = tk.Toplevel(self.root)
        result_window.title(LANGUAGES[self.current_lang]['final_result'])

        is_fail = result.final_status == "FAIL"
        window_height = 520 if is_fail else 450
        if not save_success:
            window_height += 50

        result_window.geometry(f"500x{window_height}")
        result_window.configure(bg=COLORS['background'])

        root_x = self.root.winfo_x() + 200
        root_y = self.root.winfo_y() + 100
        result_window.geometry(f"+{root_x}+{root_y}")

        is_pass = result.final_status == "PASS"
        header_color = COLORS['success'] if is_pass else COLORS['error']
        header_text = LANGUAGES[self.current_lang]['result_pass'] if is_pass else LANGUAGES[self.current_lang][
            'result_fail']
        header_icon = "✓" if is_pass else "✗"

        header_frame = tk.Frame(result_window, bg=header_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text=f"{header_icon} {header_text}", font=("Arial", 22, "bold"), fg="white",
                 bg=header_color).pack(expand=True)

        content_frame = tk.Frame(result_window, bg=COLORS['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        if not save_success:
            warning_frame = tk.Frame(content_frame, bg="#FFF3CD", relief=tk.SOLID, borderwidth=1)
            warning_frame.pack(fill=tk.X, pady=(0, 15))
            tk.Label(warning_frame, text="⚠ CSV backup\nClose Excel and merge!", font=("Arial", 10, "bold"),
                     fg="#856404", bg="#FFF3CD", pady=8).pack()

        tk.Label(content_frame, text=LANGUAGES[self.current_lang]['test_time'].format(time=result.test_duration),
                 font=("Arial", 12), fg=COLORS['text_light'], bg=COLORS['background']).pack(pady=(0, 15))

        tk.Frame(content_frame, height=2, bg=COLORS['border']).pack(fill=tk.X, pady=10)

        tk.Label(content_frame, text=LANGUAGES[self.current_lang]['profile_results'], font=("Arial", 11, "bold"),
                 fg=COLORS['text_dark'], bg=COLORS['background']).pack(pady=(5, 10))

        profiles_frame = tk.Frame(content_frame, bg=COLORS['background'])
        profiles_frame.pack(fill=tk.X)

        for profile_name, profile_result in result.profile_results.items():
            profile_row = tk.Frame(profiles_frame, bg=COLORS['background'])
            profile_row.pack(fill=tk.X, pady=3)

            if profile_result.status == "TIMEOUT":
                status_icon, status_color = "⏱", COLORS['warning']
            else:
                status_icon = "✓" if profile_result.status == "PASS" else "✗"
                status_color = COLORS['success'] if profile_result.status == "PASS" else COLORS['error']

            tk.Label(profile_row, text=status_icon, font=("Arial", 14, "bold"), fg=status_color,
                     bg=COLORS['background'], width=2).pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(profile_row, text=profile_name, font=("Arial", 10), fg=COLORS['text_dark'],
                     bg=COLORS['background'], width=12, anchor='w').pack(side=tk.LEFT)

            if profile_result.status not in ["TIMEOUT", "ERROR"]:
                avg_v = profile_result.get_average_voltage_with_load()
                tk.Label(profile_row, text=f"{LANGUAGES[self.current_lang]['avg_voltage']}: {avg_v:.2f}V",
                         font=("Arial", 9), fg=COLORS['text_light'], bg=COLORS['background']).pack(side=tk.LEFT,
                                                                                                   padx=(10, 0))

        if is_fail:
            tk.Frame(content_frame, height=2, bg=COLORS['border']).pack(fill=tk.X, pady=15)
            tk.Button(content_frame, text=f"🔄 {LANGUAGES[self.current_lang]['retry_test']}",
                      command=lambda: self._retry_test(result_window), bg=COLORS['warning'], fg="white",
                      font=("Arial", 12, "bold"), relief=tk.FLAT, padx=25, pady=10, cursor="hand2").pack(pady=10)

        def close_and_reset():
            result_window.destroy()
            self.entry_serial.delete(0, tk.END)
            self.entry_serial.focus_set()

        if is_pass:
            result_window.after(5000, close_and_reset)

    def _retry_test(self, result_window):
        result_window.destroy()
        logger.info(f"RETRY: {self.last_test_serial}")
        self.serial_test_count[self.last_test_serial] -= 1
        self._start_test(retry_serial=self.last_test_serial)

    def _debug_key_pressed(self, event):
        current_time = time.time()
        self.debug_key_sequence = [t for t in self.debug_key_sequence if current_time - t < 2]
        self.debug_key_sequence.append(current_time)
        if len(self.debug_key_sequence) >= 3:
            self._activate_debug_mode()
            self.debug_key_sequence = []

    def _activate_debug_mode(self):
        password = tk.simpledialog.askstring(LANGUAGES[self.current_lang]['engineering_mode'],
                                             LANGUAGES[self.current_lang]['password_prompt'], show='*')
        if password == "reconext2025":
            self.debug_mode = True
            logger.info("=== ENGINEERING MODE ===")
            self._show_debug_window()
        else:
            messagebox.showerror("Error", LANGUAGES[self.current_lang]['wrong_password'])
            logger.warning("Wrong password")

    def _browse_file(self, var, title):
        file = filedialog.askopenfilename(title=title)
        if file:
            var.set(file)

    def _browse_folder(self, var, title):
        folder = filedialog.askdirectory(title=title)
        if folder:
            var.set(folder)

    def _show_debug_window(self):
        debug_win = tk.Toplevel(self.root)
        debug_win.title(f"🔧 {LANGUAGES[self.current_lang]['engineering_mode']}")
        debug_win.geometry("900x700")
        debug_win.configure(bg=COLORS['card_bg'])

        header = tk.Frame(debug_win, bg='#000000', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"🔧 {LANGUAGES[self.current_lang]['engineering_mode'].upper()}",
                 font=("Arial", 20, "bold"), bg='#000000', fg="white").pack(expand=True)

        style = ttk.Style()
        style.configure('Debug.TNotebook', background=COLORS['card_bg'])
        style.configure('Debug.TNotebook.Tab', background=COLORS['card_bg'], foreground=COLORS['text_dark'],
                        padding=[10, 5])
        style.map('Debug.TNotebook.Tab', background=[('selected', COLORS['primary_light'])])

        notebook = ttk.Notebook(debug_win, style='Debug.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        log_tab = tk.Frame(notebook, bg=COLORS['card_bg'])
        notebook.add(log_tab, text=f"📄 {LANGUAGES[self.current_lang]['logs']}")

        log_frame = tk.Frame(log_tab, bg=COLORS['card_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_text = tk.Text(log_frame, font=("Courier", 9), wrap=tk.WORD, bg=COLORS['card_bg'], fg=COLORS['text_dark'])
        log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.config(yscrollcommand=scrollbar.set)

        try:
            with open(log_filename, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-100:]:
                    log_text.insert(tk.END, line)
                log_text.see(tk.END)
        except Exception as e:
            log_text.insert(tk.END, f"Error: {e}")

        log_btn_frame = tk.Frame(log_tab, bg=COLORS['card_bg'])
        log_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(log_btn_frame, text=f"🔄 {LANGUAGES[self.current_lang]['refresh']}",
                  command=lambda: self._debug_refresh_logs(log_text), bg=COLORS['primary'], fg="white",
                  font=("Arial", 10, "bold"), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(log_btn_frame, text=f"🗑️ {LANGUAGES[self.current_lang]['clear']}",
                  command=lambda: self._debug_clear_logs(log_text), bg=COLORS['error'], fg="white",
                  font=("Arial", 10, "bold"), padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        stats_tab = tk.Frame(notebook, bg=COLORS['card_bg'])
        notebook.add(stats_tab, text=f"📊 {LANGUAGES[self.current_lang]['statistics']}")

        stats_content = tk.Frame(stats_tab, bg=COLORS['card_bg'])
        stats_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        daily_frame = tk.LabelFrame(stats_content, text=LANGUAGES[self.current_lang]['current_session'],
                                    font=("Arial", 12, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_dark'])
        daily_frame.pack(fill=tk.X, pady=(0, 20))

        stats_grid = tk.Frame(daily_frame, bg=COLORS['card_bg'])
        stats_grid.pack(padx=20, pady=20)

        total = self.daily_stats['total']
        pass_count = self.daily_stats['pass']
        fail_count = self.daily_stats['fail']
        pass_rate = (pass_count / total * 100) if total > 0 else 0

        labels = [(LANGUAGES[self.current_lang]['total_tests'], str(total), COLORS['primary']),
                  ("PASS:", str(pass_count), COLORS['success']), ("FAIL:", str(fail_count), COLORS['error']),
                  ("PASS Rate:", f"{pass_rate:.1f}%", COLORS['accent'])]
        for row, (label, value, color) in enumerate(labels):
            tk.Label(stats_grid, text=label, font=("Arial", 12), bg=COLORS['card_bg'], fg=COLORS['text_dark']).grid(
                row=row, column=0, sticky='w', padx=10, pady=5)
            tk.Label(stats_grid, text=value, font=("Arial", 14, "bold"), bg=COLORS['card_bg'], fg=color).grid(row=row,
                                                                                                              column=1,
                                                                                                              sticky='e',
                                                                                                              padx=10,
                                                                                                              pady=5)

        paths_tab = tk.Frame(notebook, bg=COLORS['card_bg'])
        notebook.add(paths_tab, text=f"📁 {LANGUAGES[self.current_lang]['paths']}")

        paths_content = tk.Frame(paths_tab, bg=COLORS['card_bg'])
        paths_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(paths_content, text=LANGUAGES[self.current_lang]['changes_require_restart'],
                 font=("Arial", 11, "bold"), bg="#FFF3CD", fg="#856404", pady=10).pack(fill=tk.X, pady=(0, 20))

        paths_form = tk.Frame(paths_content, bg=COLORS['card_bg'])
        paths_form.pack(fill=tk.BOTH, expand=True)

        console_var = tk.StringVar(value=str(self.config.console_path))
        device_var = tk.StringVar(value=str(self.config.device_serial or ""))
        csv_var = tk.StringVar(value=str(os.path.dirname(self.database.current_filename)))

        paths = [(LANGUAGES[self.current_lang]['console_path'], console_var, "file"),
                 (LANGUAGES[self.current_lang]['pm125_serial'], device_var, None),
                 (LANGUAGES[self.current_lang]['csv_folder'], csv_var, "folder")]

        for row, (label, var, browse_type) in enumerate(paths):
            tk.Label(paths_form, text=label, font=("Arial", 11), bg=COLORS['card_bg'], fg=COLORS['text_dark']).grid(
                row=row, column=0, sticky='nw', pady=10)
            tk.Entry(paths_form, textvariable=var, font=("Arial", 10), width=50).grid(row=row, column=1, sticky='ew',
                                                                                      padx=10, pady=10)
            if browse_type:
                tk.Button(paths_form, text=f"📂 {LANGUAGES[self.current_lang]['browse']}",
                          command=lambda v=var, t=browse_type: (
                              self._browse_file(v, f"Select {t}") if t == "file" else self._browse_folder(v, LANGUAGES[
                                  self.current_lang]['csv_folder'])), bg=COLORS['accent'], fg="white",
                          font=("Arial", 9), padx=10).grid(row=row, column=2, padx=5, pady=10)

        def save_paths():
            try:
                self.config.console_path = console_var.get()
                self.config.device_serial = device_var.get() or None
                self.config.save()
                logger.info("Paths changed")
                messagebox.showinfo(LANGUAGES[self.current_lang]['success'],
                                    LANGUAGES[self.current_lang]['paths_saved'])
            except Exception as e:
                logger.error(f"Error: {e}")
                messagebox.showerror(LANGUAGES[self.current_lang]['enter_hrid_error'], f"Cannot save:\n{e}")

        tk.Button(paths_content, text=f"💾 {LANGUAGES[self.current_lang]['save_paths']}", command=save_paths,
                  bg=COLORS['success'], fg="white", font=("Arial", 12, "bold"), padx=30, pady=10).pack(pady=20)

        hrid_tab = tk.Frame(notebook, bg=COLORS['card_bg'])
        notebook.add(hrid_tab, text=f"👤 {LANGUAGES[self.current_lang]['hrid_management']}")

        hrid_content = tk.Frame(hrid_tab, bg=COLORS['card_bg'])
        hrid_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        hrid_frame = tk.LabelFrame(hrid_content, text=LANGUAGES[self.current_lang]['available_hrids'],
                                   font=("Arial", 12, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_dark'])
        hrid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        hrid_list = tk.Listbox(hrid_frame, font=("Arial", 10), height=6, bg='#F9F9F9')
        hrid_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for hrid in self.config.valid_hrids:
            hrid_list.insert(tk.END, hrid)

        add_frame = tk.Frame(hrid_content, bg=COLORS['card_bg'])
        add_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(add_frame, text=LANGUAGES[self.current_lang]['new_hrid'], font=("Arial", 10), bg=COLORS['card_bg'],
                 fg=COLORS['text_dark']).pack(side=tk.LEFT, padx=(0, 10))

        new_hrid_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=new_hrid_var, font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=(0, 10))

        def add_hrid():
            hrid = new_hrid_var.get().strip()
            if hrid:
                if hrid not in self.config.valid_hrids:
                    self.config.valid_hrids.append(hrid)
                    self.config.save()
                    hrid_list.insert(tk.END, hrid)
                    new_hrid_var.set("")
                    logger.info(f"HRID added: {hrid}")
                    messagebox.showinfo(LANGUAGES[self.current_lang]['hrid_added'],
                                        LANGUAGES[self.current_lang]['hrid_add_success'].format(hrid=hrid))
                else:
                    messagebox.showwarning(LANGUAGES[self.current_lang]['hrid_exists_warning'],
                                           LANGUAGES[self.current_lang]['hrid_already_exists'])
            else:
                messagebox.showwarning(LANGUAGES[self.current_lang]['enter_hrid_error'],
                                       LANGUAGES[self.current_lang]['enter_hrid'])

        tk.Button(add_frame, text=f"➕ {LANGUAGES[self.current_lang]['add']}", command=add_hrid, bg=COLORS['accent'],
                  fg="white", font=("Arial", 9, "bold"), padx=10).pack(side=tk.LEFT, padx=(0, 10))

        def remove_hrid():
            selection = hrid_list.curselection()
            if selection:
                idx = selection[0]
                hrid = hrid_list.get(idx)
                if messagebox.askyesno(LANGUAGES[self.current_lang]['confirm_remove_hrid'],
                                       LANGUAGES[self.current_lang]['remove_hrid_ask'].format(hrid=hrid)):
                    self.config.valid_hrids.remove(hrid)
                    self.config.save()
                    hrid_list.delete(idx)
                    logger.info(f"HRID removed: {hrid}")
            else:
                messagebox.showwarning(LANGUAGES[self.current_lang]['enter_hrid_error'],
                                       LANGUAGES[self.current_lang]['select_hrid_remove'])

        tk.Button(add_frame, text=f"➖ {LANGUAGES[self.current_lang]['remove']}", command=remove_hrid,
                  bg=COLORS['error'], fg="white", font=("Arial", 9, "bold"), padx=10).pack(side=tk.LEFT)

        config_tab = tk.Frame(notebook, bg=COLORS['card_bg'])
        notebook.add(config_tab, text=f"⚙️ {LANGUAGES[self.current_lang]['config']}")

        config_content = tk.Frame(config_tab, bg=COLORS['card_bg'])
        config_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(config_content, text=LANGUAGES[self.current_lang]['changes_require_restart'],
                 font=("Arial", 11, "bold"), bg="#FFF3CD", fg="#856404", pady=10).pack(fill=tk.X, pady=(0, 20))

        form_frame = tk.Frame(config_content, bg=COLORS['card_bg'])
        form_frame.pack(fill=tk.BOTH, expand=True)

        timeout_var = tk.StringVar(value=str(self.runner.test_timeout))
        interval_var = tk.StringVar(value=str(self.config.measurement_interval))

        first_profile = None
        for profile in self.config.get_profiles():
            first_profile = profile
            break

        no_load_var = tk.StringVar(value=str(first_profile.test_duration_no_load) if first_profile else "2.5")
        with_load_var = tk.StringVar(value=str(first_profile.test_duration_with_load) if first_profile else "2.5")

        configs = [(LANGUAGES[self.current_lang]['test_timeout'], timeout_var),
                   (LANGUAGES[self.current_lang]['measurement_interval'], interval_var),
                   (LANGUAGES[self.current_lang]['test_duration_no_load'], no_load_var),
                   (LANGUAGES[self.current_lang]['test_duration_with_load'], with_load_var)]

        for row, (label, var) in enumerate(configs):
            tk.Label(form_frame, text=label, font=("Arial", 11), bg=COLORS['card_bg'], fg=COLORS['text_dark']).grid(
                row=row, column=0, sticky='w', pady=10)
            tk.Entry(form_frame, textvariable=var, font=("Arial", 11), width=10).grid(row=row, column=1, sticky='w',
                                                                                      padx=20, pady=10)

        def save_config():
            try:
                self.runner.test_timeout = int(timeout_var.get())
                self.config.measurement_interval = float(interval_var.get())

                no_load_time = float(no_load_var.get())
                with_load_time = float(with_load_var.get())

                for profile in self.config.profiles:
                    profile.test_duration_no_load = no_load_time
                    profile.test_duration_with_load = with_load_time

                self.config.save()
                logger.info("Config changed")
                messagebox.showinfo(LANGUAGES[self.current_lang]['success'],
                                    LANGUAGES[self.current_lang]['config_saved'])
            except Exception as e:
                logger.error(f"Error: {e}")
                messagebox.showerror(LANGUAGES[self.current_lang]['enter_hrid_error'], f"Cannot save:\n{e}")

        tk.Button(config_content, text=f"💾 {LANGUAGES[self.current_lang]['save_config']}", command=save_config,
                  bg=COLORS['success'], fg="white", font=("Arial", 12, "bold"), padx=30, pady=10).pack(pady=20)

    def _debug_refresh_logs(self, log_text):
        log_text.delete('1.0', tk.END)
        try:
            with open(log_filename, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-100:]:
                    log_text.insert(tk.END, line)
                log_text.see(tk.END)
            logger.info("Logs refreshed")
        except Exception as e:
            log_text.insert(tk.END, f"Error: {e}")

    def _debug_clear_logs(self, log_text):
        log_text.delete('1.0', tk.END)
        logger.info("=== LOGS CLEARED ===")
        messagebox.showinfo("OK", "Logs cleared")

    def _show_about(self):
        messagebox.showinfo("About", LANGUAGES[self.current_lang]['about_window'])

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if hasattr(self, 'hardware') and self.hardware:
                self.hardware.disconnect()
            logger.info(f"=== APP CLOSED === Stats: {self.daily_stats}")


def main():
    app = TestGUI()
    app.run()


if __name__ == "__main__":
    main()
