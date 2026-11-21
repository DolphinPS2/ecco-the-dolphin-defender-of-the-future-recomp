================================================================================
ПАСПОРТ ПРОЕКТА ДЛЯ ИИ-АССИСТЕНТА И РАЗРАБОТЧИКА (ECCO THE DOLPHIN PC PORT)
================================================================================
Если начинается новый диалог, просто покажи этот файл (X:\ECCOEXE\AI_CONTEXT_README.txt)
или дай ссылку на репозиторий GitHub — здесь собрана вся структура и прямые ссылки.

1. ПРЯМЫЕ ССЫЛКИ НА GITHUB (МОЖНО ЧИТАТЬ НАПРЯМУЮ В НОВОМ ДИАЛОГЕ):
- Главная страница репозитория:
  https://github.com
- Текущий пререлиз v1.5-beta (Windows & Linux, 8 ассетов):
  https://github.com/releases/tag/v1.5
- Прямой текст паспорта проекта (Raw):
  https://githubusercontent.com
- Прямой текст плана развития v1.6 (Raw):
  https://githubusercontent.com
- Исходник патчера Paradox RUS с фиксом музыки (Raw):
  https://githubusercontent.com
- Исходник Windows 2K-лаунчера (Raw):
  https://githubusercontent.com
- Исходник кроссплатформенного лаунчера Win/Linux (Raw):
  https://githubusercontent.com
- Скрипт онлайн-установщика Inno Setup v1.5 (Raw):
  https://githubusercontent.com

2. КАРТА ПАПОК НА ДИСКЕ X:\ECCOEXE:
- X:\ECCOEXE\AI_CONTEXT_README.txt       -> Этот главный документ-шпаргалка.
- X:\ECCOEXE\PROJECT_CONTEXT.md          -> Подробная техническая документация.
- X:\ECCOEXE\1.4\src_backup\             -> Актуальные исходники (launcher.py, extract_paradox_mod.py, online_installer_v15.iss).
- X:\ECCOEXE\1.4\setup_build\            -> Ресурсы Inno Setup (ecco.ico, sun_fall.mp3, sonic.bmp, textecco.bmp).
- X:\ECCOEXE\1.5_BUILD\                  -> Сборочная папка PyInstaller для Windows (Ecco_the_Dolphin.exe).
- X:\ECCOEXE\GITHUB_RELEASE_v15\         -> Готовые файлы релиза v1.5 для Windows (src\ и release_assets\).
- X:\ECCOEXE\LINUX_v15\                  -> Готовые файлы релиза v1.5 для Linux (Ecco_the_Dolphin_Linux_Setup_v15.run, zip-архивы).
- X:\ECCOEXE\Ecco_ISO\                   -> Тестовые образы Dreamcast (Europe .chd и Paradox RUS .cdi).
- X:\ECCOEXE\GIT_ECCO\                   -> Локальный клон GitHub-репозитория (авторизован через gh CLI под DolphinPS2).
- X:\ECCOEXE\ARCHIVE_ENGINE_FROM_C\      -> Перенесённый архив из C:\Users\dolph\Downloads\Engine (для сверки, удалять постепенно после тестов).

3. ЧТО СДЕЛАНО В РЕЛИЗЕ v1.5-BETA (WINDOWS & LINUX):
- Лечение музыки Paradox RUS: извлекаются ТОЛЬКО 48 уровней (.GDE) с русской озвучкой и шрифтами; сломанные MUSIC_*.AFS и SOUND с пиратского диска не копируются, папка mods/rus_paradox очищается перед каждым переносом -> играет полный оригинальный саундтрек.
- Поддержка образов .cdi (встроенный чистый парсер Python), .gdi и .chd (через chdman).
- 2K-лаунчер: подводная волна переноса [F2 / Y] (видна только при выборе Русской Версии), неблокирующий выбор диска, живой подводный маячок SEGANET • DREAMPIPE.NET (https://dreampipe.net), автофокус поверх Проводника при запуске, старт игры по кнопке Start (0, 7, 9, 11).
- На GitHub в релизе v1.5 загружены все 6 файлов проекта (+ 2 исходника GitHub = Assets 8), включая chdman_win64.zip.

4. ТЕКУЩИЙ СТАТУС И ПЛАН НА v1.6:
- ШАГ 1 (БЛИЖАЙШИЙ): Перезагрузиться в Linux и протестировать X:\ECCOEXE\LINUX_v15\Ecco_the_Dolphin_Linux_Setup_v15.run (установка, перенос Paradox RUS, Vulkan, геймпад).
- ШАГ 2 (v1.6): Сделать в лаунчере Менеджер сохранений VMU ([F3 / X]):
  * Экспорт и импорт карты памяти vmu_a1.bin (128 КБ) с автобэкапом vmu_a1.bin.bak.
  * Перепаковка и импорт отдельных слотов .VMI / .VMS (совместимость с Flycast, Redream, GameFAQs, Dreamcast).
  * Клонирование прогресса между профилями Europe и Paradox RUS в один клик.
- ШАГ 3 (v1.6+): Интерактивный HD-оверлей экрана VMU в C++-движке по нажатию шифтов (LB / RB) и повторное скрытие курсора мыши при возврате на стик/крестовину геймпада.
================================================================================
