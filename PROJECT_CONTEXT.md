# Паспорт проекта: Ecco the Dolphin: Defender of the Future (PC Recomp + DC Launcher)

Этот файл является единой «памятью проекта» для разработчика и ИИ-ассистента. Если начать новый диалог и показать этот файл или ссылку на репозиторий `https://github.com`, вся структура и история решений будут восстановлены за 5 секунд.

---

## 1. Карта папок на рабочем ПК (`X:\ECCOEXE` и `C:\Users\dolph\Downloads\Engine`)
- **`X:\ECCOEXE\1.4\src_backup\`** — эталонные исходники Windows v1.4/v1.5 (`launcher.py`, `extract_paradox_mod.py`, `online_installer_v14.iss`, `online_installer_v15.iss`).
- **`X:\ECCOEXE\1.5_BUILD\`** — сборочная среда PyInstaller для Windows (`Ecco_the_Dolphin.exe`).
- **`X:\ECCOEXE\Ecco_ISO\`** — тестовые образы Dreamcast (`Ecco the Dolphin - Defender of the Future (Europe) (En,Fr,De,Es).chd` и `Ecco the Dolphin [Paradox].cdi`).
- **`X:\ECCOEXE\GITHUB_RELEASE_v15\`** — готовые артефакты Windows v1.5 (`src/` и `release_assets/`).
- **`X:\ECCOEXE\LINUX_v15\`** — готовые артефакты Linux v1.5 (`Ecco_the_Dolphin_Linux_Setup_v15.run`, `Ecco_the_Dolphin_DC_PC_Launcher_Win_Linux.zip`, `Ecco_the_Dolphin_Engine_Linux64.zip`).
- **`X:\ECCOEXE\GIT_ECCO\`** — локальный клон репозитория GitHub.
- **`C:\Users\dolph\Downloads\Engine\linux_v14_work\`** — нетронутый эталон сборки Linux v1.4.

---

## 2. Ключевые технические решения (что уже сделано в v1.5)
1. **Лечение музыки в русской версии Paradox RUS (`extract_paradox_mod.py`):**
   - На пиратском диске Paradox лежат битые/обрезанные аудиоархивы `MUSIC_*.AFS`, из-за которых в русской версии пропадала музыка.
   - `extract_paradox_mod.py` извлекает с русского образа **строго 48 файлов уровней (`.GDE`)** (русская озвучка и шрифты), полностью очищает папку `mods/rus_paradox` перед каждым новым переносом и не копирует `MUSIC_*.AFS` / `SOUND`, благодаря чему играет **полный оригинальный саундтрек** из европейского образа.
   - Поддерживаются форматы `.cdi` (встроенный чистый парсер ISO9660/CDI без внешних утилит), `.gdi` и `.chd` (через `chdman`).
2. **Кроссплатформенный 2K-лаунчер (`launcher.py`):**
   - Подводная волна прогресса переноса (`[F2 / Y] ПЕРЕНОС ПЕРЕВОДА И ОРИГИНАЛЬНОЙ МУЗЫКИ`), видимая только при выборе **Русской Версии**.
   - Неблокирующий диалог выбора образа диска в отдельном потоке/процессе (Windows: PowerShell `OpenFileDialog`; Linux: `zenity` / `kdialog` / `tkinter`).
   - Живой подводный маячок **`SEGANET • DREAMPIPE.NET`** (`https://dreampipe.net`) в глубине между кнопками.
   - Раздельные профили сохранений и настроек (`profiles/europe` и `profiles/paradox_rus`), запуск игры с геймпада по кнопке **Start** (`0, 7, 9, 11`).
3. **Установщики Windows и Linux:**
   - Windows: `Ecco_the_Dolphin_Online_Setup_v15.exe` (Inno Setup 6, скачивает `Ecco_the_Dolphin_Engine_Win64.zip` из релиза `v1.5` или берёт локально).
   - Linux: `Ecco_the_Dolphin_Linux_Setup_v15.run` (makeself + tkinter GUI, скачивает `Ecco_the_Dolphin_DC_PC_Launcher_Win_Linux.zip` и `Ecco_the_Dolphin_Engine_Linux64.zip` из релиза `v1.5`, создаёт `.desktop` ярлыки).

---

## 3. Что проверить при перезагрузке в Linux
1. Скопировать на Linux-раздел `X:\ECCOEXE\LINUX_v15\Ecco_the_Dolphin_Linux_Setup_v15.run` и образы из `X:\ECCOEXE\Ecco_ISO\`.
2. Запустить: `chmod +x Ecco_the_Dolphin_Linux_Setup_v15.run && ./Ecco_the_Dolphin_Linux_Setup_v15.run`.
3. Проверить установку, перенос перевода Paradox RUS (наличие 48 `.GDE` и полной музыки), запуск игры через Vulkan и работу геймпада.

---

## 4. План на следующие версии (v1.6+)
1. **Менеджер сохранений VMU в лаунчере (`F3 / X`):**
   - Экспорт и импорт карты памяти `vmu_a1.bin` (128 КБ) с автобэкапом (`vmu_a1.bin.bak`).
   - Перепаковка и импорт отдельных слотов `.VMI` / `.VMS` (совместимость с Flycast, Redream, GameFAQs, Dreamcast).
   - Клонирование прогресса между профилями `Europe` и `Paradox RUS` в один клик.
2. **Полиш UI и C++-движка:**
   - Повторное скрытие курсора мыши при возврате на стик/крестовину геймпада.
   - Интерактивный HD-оверлей экрана VMU в движке по нажатию шифтов (`LB` / `RB`).
