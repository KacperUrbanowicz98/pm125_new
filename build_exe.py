# build_exe.py
import PyInstaller.__main__
import os

project_name = "TestAutomatyczny"
icon_path = "reconext_logo.ico"  # Opcjonalnie - jeśli masz ikonę

# Wszystkie pliki graficzne do dołączenia
data_files = [
    ('reconext_logo.jpg', '.'),
    ('logo.png', '.'),
    ('flag_pl.png', '.'),
    ('flag_en.png', '.'),
    ('flag_ua.png', '.'),
]

# Utwórz listę argumentów dla PyInstaller
pyinstaller_args = [
    'gui.py',
    '--name=' + project_name,
    '--onefile',
    '--windowed',  # BEZ KONSOLI
    '--clean',
    '--noconfirm',
]

# Dodaj ikonę jeśli istnieje
if os.path.exists(icon_path):
    pyinstaller_args.append(f'--icon={icon_path}')

# Dodaj pliki graficzne
for data_file, target_dir in data_files:
    if os.path.exists(data_file):
        pyinstaller_args.append(f'--add-data={data_file};{target_dir}')

# Dodaj ukryte importy (jeśli potrzebne)
hidden_imports = [
    'PIL._tkinter_finder',
    'tkinter',
    'tkinter.ttk',
    'PIL.Image',
    'PIL.ImageTk',
]

for module in hidden_imports:
    pyinstaller_args.append(f'--hidden-import={module}')

# Uruchom PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\n✅ Build zakończony! EXE znajduje się w folderze: dist/")
