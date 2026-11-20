#!/usr/bin/env python3
import os, sys, time, shutil, subprocess, urllib.request, zipfile, tempfile, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ENGINE_ZIP_URL = "https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.4/Ecco_the_Dolphin_Engine_Linux64.zip"
LAUNCHER_ZIP_URL = "https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.4/Ecco_the_Dolphin_DC_PC_Launcher_Win_Linux.zip"

class EccoLinuxInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Установка — Ecco the Dolphin: Defender of the Future (Linux)")
        self.geometry("640x480")
        self.resizable(False, False)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.dirname(self.base_dir)
        self.install_dir = tk.StringVar(value=os.path.expanduser("~/Games/Ecco_the_Dolphin"))
        self.eu_disc = tk.StringVar()
        self.ru_disc = tk.StringVar()
        self.create_menu = tk.BooleanVar(value=True)
        self.create_desktop = tk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}
        tk.Label(self, text="Ecco the Dolphin: Defender of the Future (Linux PC Port)", font=("Sans", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(self, text="Нативный порт Dreamcast + DC PC графический лаунчер (Europe & Paradox RUS)", fg="#444").pack(anchor="w", padx=16, pady=(0, 10))
        frm = tk.Frame(self); frm.pack(fill="x", **pad)
        tk.Label(frm, text="Папка установки:").pack(anchor="w")
        r1 = tk.Frame(frm); r1.pack(fill="x", pady=2)
        tk.Entry(r1, textvariable=self.install_dir).pack(side="left", fill="x", expand=True)
        tk.Button(r1, text="Обзор...", command=lambda: self.install_dir.set(filedialog.askdirectory() or self.install_dir.get())).pack(side="right", padx=(6, 0))
        tk.Label(frm, text="Европейский образ диска (Europe .chd / .cue / .gdi, обязательно):").pack(anchor="w", pady=(8, 0))
        r2 = tk.Frame(frm); r2.pack(fill="x", pady=2)
        tk.Entry(r2, textvariable=self.eu_disc).pack(side="left", fill="x", expand=True)
        tk.Button(r2, text="Обзор...", command=lambda: self.eu_disc.set(filedialog.askopenfilename() or self.eu_disc.get())).pack(side="right", padx=(6, 0))
        tk.Label(frm, text="Русский образ диска (Paradox RUS .cdi / .chd / .gdi, по желанию):").pack(anchor="w", pady=(8, 0))
        r3 = tk.Frame(frm); r3.pack(fill="x", pady=2)
        tk.Entry(r3, textvariable=self.ru_disc).pack(side="left", fill="x", expand=True)
        tk.Button(r3, text="Обзор...", command=lambda: self.ru_disc.set(filedialog.askopenfilename() or self.ru_disc.get())).pack(side="right", padx=(6, 0))
        chk = tk.Frame(self); chk.pack(fill="x", **pad)
        tk.Checkbutton(chk, text="Создать ярлык в меню приложений Linux (.desktop)", variable=self.create_menu).pack(anchor="w")
        tk.Checkbutton(chk, text="Создать ярлык на Рабочем столе", variable=self.create_desktop).pack(anchor="w")
        self.status_var = tk.StringVar(value="Готово к установке. Выберите папку и образы дисков.")
        tk.Label(self, textvariable=self.status_var, fg="#0b5394").pack(anchor="w", padx=16, pady=(8, 2))
        self.prog = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.prog.pack(fill="x", padx=16, pady=4)
        bf = tk.Frame(self); bf.pack(fill="x", padx=16, pady=12)
        self.install_btn = tk.Button(bf, text="Установить", width=16, command=self._start)
        self.install_btn.pack(side="right")
        tk.Button(bf, text="Отмена", width=12, command=self.destroy).pack(side="right", padx=8)

    def _set_progress(self, val, text):
        self.after(0, lambda: (self.prog.configure(value=val), self.status_var.set(text)))

    def _download_with_progress(self, url, dst, label, p_start, p_end):
        t0 = time.time()
        last_ui = [0.0]
        def hook(blocks, block_size, total_size):
            now = time.time()
            if now - last_ui[0] < 0.2 and blocks * block_size < total_size:
                return
            last_ui[0] = now
            done = min(blocks * block_size, total_size) if total_size > 0 else blocks * block_size
            mb_done = done / (1024 * 1024)
            spd = (done / max(now - t0, 0.01)) / (1024 * 1024)
            if total_size > 0:
                pct = int(done * 100 / total_size)
                mb_tot = total_size / (1024 * 1024)
                bar_val = p_start + (p_end - p_start) * (done / total_size)
                self._set_progress(bar_val, f"{label}: {pct}% ({mb_done:.1f} / {mb_tot:.1f} МБ, {spd:.2f} МБ/с)")
            else:
                self._set_progress(p_start, f"{label}: {mb_done:.1f} МБ ({spd:.2f} МБ/с)")
        urllib.request.urlretrieve(url, dst, reporthook=hook)

    def _start(self):
        eu = self.eu_disc.get().strip()
        if not eu or not os.path.isfile(eu):
            messagebox.showerror("Ошибка", "Укажите существующий европейский образ диска (Europe).")
            return
        self.install_btn.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            out_dir = os.path.abspath(os.path.expanduser(self.install_dir.get().strip()))
            eu = os.path.abspath(self.eu_disc.get().strip())
            ru = os.path.abspath(self.ru_disc.get().strip()) if self.ru_disc.get().strip() else ""
            os.makedirs(out_dir, exist_ok=True)
            tmp_l = os.path.join(tempfile.gettempdir(), "ecco_launcher_linux.zip")
            self._download_with_progress(LAUNCHER_ZIP_URL, tmp_l, "Загрузка DC PC лаунчера", 5, 45)
            self._set_progress(47, "Распаковка графического лаунчера...")
            with zipfile.ZipFile(tmp_l, "r") as zf: zf.extractall(out_dir)

            tmp_e = os.path.join(tempfile.gettempdir(), "ecco_engine_linux.zip")
            self._download_with_progress(ENGINE_ZIP_URL, tmp_e, "Загрузка движка Linux x64", 50, 72)
            self._set_progress(74, "Распаковка бинарника движка...")
            with zipfile.ZipFile(tmp_e, "r") as zf: zf.extractall(out_dir)
            b_dst = os.path.join(out_dir, "engine/ecco-the-dolphin-defender-of-the-future-recomp")
            os.chmod(b_dst, 0o755)

            self._set_progress(78, "Копирование европейского образа диска...")
            os.makedirs(os.path.join(out_dir, "disc"), exist_ok=True)
            shutil.copy2(eu, os.path.join(out_dir, "disc", "ecco_eu" + os.path.splitext(eu)[1]))

            if ru and os.path.isfile(ru):
                self._set_progress(85, "Распаковка русского перевода и озвучки Paradox RUS...")
                t_dir = os.path.join(out_dir, "tools"); os.makedirs(t_dir, exist_ok=True)
                os.chmod(os.path.join(t_dir, "cdirip"), 0o755)
                env = os.environ.copy(); env["PATH"] = t_dir + ":" + env.get("PATH", "")
                subprocess.run([sys.executable, os.path.join(self.repo_root, "tools/extract_paradox_mod.py"), ru, os.path.join(out_dir, "profiles/paradox_rus/dreamcomp/ecco/mods/rus_paradox")], env=env, check=True)

            self._set_progress(95, "Создание ярлыков .desktop...")
            for fn in os.listdir(out_dir):
                if fn.startswith("media\\"):
                    os.makedirs(os.path.join(out_dir, "media"), exist_ok=True)
                    shutil.move(os.path.join(out_dir, fn), os.path.join(out_dir, "media", fn[6:]))
            run_sh = os.path.join(out_dir, "Ecco_the_Dolphin.sh")
            with open(run_sh, "w", encoding="utf-8") as sf: sf.write(f"#!/usr/bin/env bash\ncd \"{out_dir}\"\nexec python3 \"{out_dir}/launcher.py\" \"$@\"\n")
            os.chmod(run_sh, 0o755)
            ico_src = os.path.join(out_dir, "ecco_icon.png")
            ico_dir = os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps")
            os.makedirs(ico_dir, exist_ok=True)
            ico_dst = os.path.join(ico_dir, "ecco-the-dolphin.png")
            if os.path.isfile(ico_src): shutil.copy2(ico_src, ico_dst)
            de = f"[Desktop Entry]\nVersion=1.0\nType=Application\nName=Ecco the Dolphin: Defender of the Future\nComment=Native PC Port (Europe & Paradox RUS)\nExec={run_sh}\nIcon=ecco-the-dolphin\nPath={out_dir}\nTerminal=false\nStartupNotify=true\nCategories=Game;AdventureGame;\n"
            if self.create_menu.get():
                ad = os.path.expanduser("~/.local/share/applications"); os.makedirs(ad, exist_ok=True)
                mp = os.path.join(ad, "ecco-the-dolphin.desktop")
                with open(mp, "w", encoding="utf-8") as df: df.write(de)
                os.chmod(mp, 0o755)
                subprocess.run(["update-desktop-database", ad], stderr=subprocess.DEVNULL)
            if self.create_desktop.get():
                dp = os.path.join(subprocess.getoutput("xdg-user-dir DESKTOP").strip() or os.path.expanduser("~/Desktop"), "Ecco the Dolphin.desktop")
                with open(dp, "w", encoding="utf-8") as df: df.write(de)
                os.chmod(dp, 0o755)
                subprocess.run(["gio", "set", dp, "metadata::trusted", "true"], stderr=subprocess.DEVNULL)
            subprocess.run(["gtk-update-icon-cache", "-f", "-t", os.path.expanduser("~/.local/share/icons/hicolor")], stderr=subprocess.DEVNULL)
            subprocess.run(["kbuildsycoca6", "--noincremental"], stderr=subprocess.DEVNULL)
            self._set_progress(100, "Готово!")
            self.after(0, lambda: (messagebox.showinfo("Готово", f"Игра успешно установлена в:\n{out_dir}"), self.destroy()))
        except Exception as exc:
            self.after(0, lambda msg=str(exc): (messagebox.showerror("Ошибка", msg), self.install_btn.config(state="normal")))

if __name__ == "__main__":
    EccoLinuxInstaller().mainloop()
