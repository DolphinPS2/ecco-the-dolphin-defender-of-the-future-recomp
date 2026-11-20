# Архитектура сборки, локализации и резервных копий (v1.4)

## 1. Как работает двуязычное меню (Europe Original / Paradox RUS)
- При запуске через 2K-лаунчер (`Ecco_the_Dolphin.exe`) для профиля **Paradox RUS** переменная `APPDATA` указывает на `profiles/paradox_rus`, а для **Europe Original** — на `profiles/europe`.
- В `dreamcomp/src/frontend/menu_ui.cpp` функция `tr_lookup()` проверяет, содержит ли `APPDATA` строку `paradox_rus` (или задана переменная `DREAMCOMP_LANG=ru`).
- Если условие выполнено, движок загружает словарь `engine/frontend/lang_ru.ini` (UTF-8) и переводит все вкладки (**Общие / Управление / Графика / Звук / Моды**), кнопки геймпада, описания настроек, окно выхода и экран **О программе** (`Dolphin_PS2.`).
- Для **Europe Original** меню остаётся на оригинальном английском.

## 2. Как отредактировать перевод без перекомпиляции
1. Откройте `engine/frontend/lang_ru.ini` в Блокноте (кодировка UTF-8).
2. Измените любой текст справа от знака `=` и сохраните файл.

## 3. Команды быстрой пересборки на Windows
- **Движок (`ninja`, ~5 сек):**
  `ninja -C "C:\Users\dolph\Downloads\Engine\build\dreamcomp\ports\ecco-the-dolphin-defender-of-the-future-recomp\build"`
- **2K-лаунчер (`PyInstaller --onedir`):**
  `python -m PyInstaller --noconfirm --onedir --windowed --icon "ecco.ico" --name "Ecco_the_Dolphin" windows/launcher.py`
- **Онлайн-установщик (`Inno Setup 6`):**
  `"C:\Users\dolph\AppData\Local\Programs\Inno Setup 6\ISCC.exe" windows/online_installer_v14.iss`

## 4. Структура локальных резервных копий (`X:\ECCOEXE\`)
- `X:\ECCOEXE\1.3\` — эталонная сборка v1.3 с английским меню.
- `X:\ECCOEXE\1.4\` — релиз v1.4 с двуязычным меню, исходниками и заметками.
