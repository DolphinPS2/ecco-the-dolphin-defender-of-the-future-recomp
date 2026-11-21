#!/usr/bin/env python3
import os, sys, time, shutil, signal, subprocess, urllib.request, zipfile, tempfile, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ENGINE_ZIP_URL = "https://github.com"
LAUNCHER_ZIP_URL = "https://github.com"

class FancyEccoLinuxInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Установка — Ecco the Dolphin: Defender of the Future (Linux PC Port)")
        self.geometry("760x530"); self.resizable(False, False); self.configure(bg="#eef5fc")
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.dirname(self.base_dir)
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.launch_dir = os.environ.get("LAUNCH_DIR", os.getcwd())
        self.install_dir = tk.StringVar(value=os.path.expanduser("~/Games/Ecco_the_Dolphin"))
        self.eu_disc, self.ru_disc = tk.StringVar(), tk.StringVar()
        self.create_menu, self.create_desktop = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
        self.music_proc, self.music_on, self.imgs = None, True, {}
        self._start_music(); self.protocol("WM_DELETE_WINDOW", self._on_close); self._build_ui()

    def _start_music(self):
        mp3 = os.path.join(self.assets_dir, "sun_fall.mp3")
        if os.path.exists(mp3) and shutil.which("ffplay"):
            self.music_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loop", "0", "-volume", "45", "-loglevel", "quiet", mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _toggle_music(self):
        if not self.music_proc: return
        self.music_on = not self.music_on
        self.music_proc.send_signal(signal.SIGCONT if self.music_on else signal.SIGSTOP)
        self.music_btn.config(text="🔊 Музыка: ВКЛ" if self.music_on else "🔇 Музыка: ВЫКЛ", bg="#1f5c99" if self.music_on else "#163a63")

    def _on_close(self):
        if self.music_proc:
            try: self.music_proc.terminate()
            except Exception: pass
        self.destroy()

    def _pick_dir(self):
        p = subprocess.run(["kdialog", "--getexistingdirectory", os.path.expanduser("~")], capture_output=True, text=True).stdout.strip() if shutil.which("kdialog") else filedialog.askdirectory()
        if p: self.install_dir.set(p)

    def _pick_file(self, var, title):
        sd = os.path.expanduser("~/Ecco_ISO") if os.path.isdir(os.path.expanduser("~/Ecco_ISO")) else os.path.expanduser("~")
        p = subprocess.run(["kdialog", "--getopenfilename", sd, "*.chd *.cdi *.gdi *.cue", "--title", title], capture_output=True, text=True).stdout.strip() if shutil.which("kdialog") else filedialog.askopenfilename(initialdir=sd, title=title)
        if p: var.set(p)

    def _build_ui(self):
        style = ttk.Style(self); style.theme_use("clam")
        style.configure("Ocean.Horizontal.TProgressbar", troughcolor="#d5e4f2", background="#0e76d9", thickness=18)
        left = tk.Frame(self, bg="#091e3a", width=215); left.pack(side="left", fill="y"); left.pack_propagate(False)
        tk.Label(left, text="SEGA DREAMCAST", fg="#5bb2ff", bg="#091e3a", font=("Sans", 10, "bold")).pack(pady=(16, 2))
        tk.Label(left, text="NATIVE PC PORT • v1.5", fg="#a9d4ff", bg="#091e3a", font=("Sans", 8, "bold")).pack(pady=(0, 10))
        sp = os.path.join(self.assets_dir, "sonic.png")
        if os.path.exists(sp):
            self.imgs["sonic"] = tk.PhotoImage(file=sp); tk.Label(left, image=self.imgs["sonic"], bg="#091e3a", bd=0).pack(pady=6)
        tk.Label(left, text="• Vulkan 60+ FPS\n• Широкий экран 21:9\n• Europe + Paradox RUS\n• Оригинальный OST", fg="#cfe6ff", bg="#091e3a", justify="left", font=("Sans", 9)).pack(padx=14, pady=12, anchor="w")
        self.music_btn = tk.Button(left, text="🔊 Музыка: ВКЛ", command=self._toggle_music, bg="#1f5c99", fg="white", relief="flat", font=("Sans", 9, "bold"), cursor="hand2", padx=10, pady=6)
        self.music_btn.pack(side="bottom", fill="x", padx=16, pady=16)

        right = tk.Frame(self, bg="#eef5fc"); right.pack(side="right", fill="both", expand=True)
        header = tk.Frame(right, bg="#103663", height=96); header.pack(fill="x"); header.pack_propagate(False)
        lp = os.path.join(self.assets_dir, "logo.png")
        if os.path.exists(lp):
            self.imgs["logo"] = tk.PhotoImage(file=lp); self.iconphoto(True, self.imgs["logo"])
            tk.Label(header, image=self.imgs["logo"], bg="#103663", bd=0).pack(side="left", padx=(18, 12), pady=10)
            tf = tk.Frame(header, bg="#103663"); tf.pack(side="left", fill="y", pady=18)
            tk.Label(tf, text="Ecco the Dolphin: Defender of the Future", fg="white", bg="#103663", font=("Sans", 13, "bold")).pack(anchor="w")
            tk.Label(tf, text="Нативный ПК-порт SEGA Dreamcast • Europe & Paradox RUS", fg="#8ec7ff", bg="#103663", font=("Sans", 9)).pack(anchor="w", pady=(2, 0))
        else:
            tk.Label(header, text="Ecco the Dolphin: Defender of the Future", fg="white", bg="#103663", font=("Sans", 14, "bold")).pack(side="left", padx=18)

        body = tk.Frame(right, bg="#eef5fc"); body.pack(fill="both", expand=True, padx=18, pady=10)
        def add_row(lbl, var, cmd, hint=""):
            tk.Label(body, text=lbl, bg="#eef5fc", fg="#0e2a47", font=("Sans", 9, "bold")).pack(anchor="w", pady=(6, 1))
            r = tk.Frame(body, bg="#eef5fc"); r.pack(fill="x")
            tk.Entry(r, textvariable=var, font=("Sans", 9), bg="white", fg="#111", relief="solid", bd=1).pack(side="left", fill="x", expand=True, ipady=4)
            tk.Button(r, text="Обзор...", command=cmd, bg="#1c64b0", fg="white", relief="flat", font=("Sans", 9, "bold"), padx=12, pady=3, cursor="hand2").pack(side="right", padx=(6, 0))
            if hint: tk.Label(body, text=hint, bg="#eef5fc", fg="#516c87", font=("Sans", 8)).pack(anchor="w")

        add_row("Папка установки игры:", self.install_dir, self._pick_dir)
        add_row("1. Европейский образ диска (Europe .chd / .cue / .gdi) [Обязательно]:", self.eu_disc, lambda: self._pick_file(self.eu_disc, "Выберите образ Europe"))
        add_row("2. Русский образ диска (Paradox RUS .cdi / .chd / .gdi) [По желанию]:", self.ru_disc, lambda: self._pick_file(self.ru_disc, "Выберите образ Paradox RUS"), "Извлекаются 48 уровней с русской озвучкой + полный оригинальный саундтрек")

        chk = tk.Frame(body, bg="#eef5fc"); chk.pack(fill="x", pady=(10, 4))
        tk.Checkbutton(chk, text="Создать ярлык в меню приложений Linux (.desktop)", variable=self.create_menu, bg="#eef5fc", fg="#0e2a47", selectcolor="white", font=("Sans", 9)).pack(anchor="w")
        tk.Checkbutton(chk, text="Создать ярлык на Рабочем столе", variable=self.create_desktop, bg="#eef5fc", fg="#0e2a47", selectcolor="white", font=("Sans", 9)).pack(anchor="w")
        self.status_var = tk.StringVar(value="Готово к установке. Укажите образы дисков и нажмите «Установить игру».")
        tk.Label(body, textvariable=self.status_var, bg="#eef5fc", fg="#0b5394", font=("Sans", 9, "bold")).pack(anchor="w", pady=(8, 3))
        self.prog = ttk.Progressbar(body, mode="determinate", maximum=100, style="Ocean.Horizontal.TProgressbar"); self.prog.pack(fill="x", pady=2)
        bf = tk.Frame(right, bg="#dfeaf5", height=54); bf.pack(side="bottom", fill="x"); bf.pack_propagate(False)
        self.install_btn = tk.Button(bf, text="Установить игру", command=self._start, bg="#0d7a3e", fg="white", relief="flat", font=("Sans", 10, "bold"), padx=18, pady=6, cursor="hand2"); self.install_btn.pack(side="right", padx=16, pady=10)
        tk.Button(bf, text="Отмена", command=self._on_close, bg="#6c7d8f", fg="white", relief="flat", font=("Sans", 9, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", pady=10)

    def _set_progress(self, val, text):
        self.after(0, lambda: (self.prog.configure(value=val), self.status_var.set(text)))

    def _get_pkg(self, fn, url, dst, lbl, p0, p1):
        for folder in (self.launch_dir, "/run/media/dolphin/WDC/ECCOEXE/LINUX_v15"):
            cand = os.path.join(folder, fn)
            if os.path.isfile(cand):
                self._set_progress((p0 + p1) / 2, f"{lbl}: копирование локального архива...")
                shutil.copy2(cand, dst); return
        urllib.request.urlretrieve(url, dst, reporthook=lambda b, bs, ts: self._set_progress(p0 + (p1 - p0) * min(1.0, (b * bs) / max(1, ts)), f"{lbl}: загрузка..."))

    def _start(self):
        eu = self.eu_disc.get().strip()
        if not eu or not os.path.isfile(eu):
            messagebox.showerror("Ошибка", "Укажите существующий европейский образ диска (Europe)."); return
        self.install_btn.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            out_dir = os.path.abspath(os.path.expanduser(self.install_dir.get().strip()))
            eu, ru = os.path.abspath(self.eu_disc.get().strip()), (os.path.abspath(self.ru_disc.get().strip()) if self.ru_disc.get().strip() else "")
            os.makedirs(out_dir, exist_ok=True)
            tmp_l = os.path.join(tempfile.gettempdir(), "ecco_l_v15.zip")
            self._get_pkg("Ecco_the_Dolphin_DC_PC_Launcher_Win_Linux.zip", LAUNCHER_ZIP_URL, tmp_l, "2K-лаунчер", 5, 45)
            with zipfile.ZipFile(tmp_l, "r") as zf: zf.extractall(out_dir)
            tmp_e = os.path.join(tempfile.gettempdir(), "ecco_e_v15.zip")
            self._get_pkg("Ecco_the_Dolphin_Engine_Linux64.zip", ENGINE_ZIP_URL, tmp_e, "Движок Linux x64", 50, 75)
            with zipfile.ZipFile(tmp_e, "r") as zf: zf.extractall(out_dir)
            os.chmod(os.path.join(out_dir, "engine", "ecco-the-dolphin-defender-of-the-future-recomp"), 0o755)
            os.makedirs(os.path.join(out_dir, "disc"), exist_ok=True)
            shutil.copy2(eu, os.path.join(out_dir, "disc", "ecco_eu" + os.path.splitext(eu)))
            if ru and os.path.isfile(ru):
                self._set_progress(85, "Перенос русской озвучки Paradox RUS и сохранение музыки...")
                subprocess.run([sys.executable, os.path.join(self.repo_root, "tools", "extract_paradox_mod.py"), ru, os.path.join(out_dir, "profiles", "paradox_rus", "dreamcomp", "ecco", "mods", "rus_paradox")], check=True)
            self._set_progress(95, "Создание ярлыков .desktop...")
            run_sh = os.path.join(out_dir, "Ecco_the_Dolphin.sh")
            open(run_sh, "w", encoding="utf-8").write(f"#!/usr/bin/env bash\ncd \"{out_dir}\"\nexec python3 \"{out_dir}/launcher.py\" \"$@\"\n")
            os.chmod(run_sh, 0o755)
            ico_src, ico_dir = os.path.join(out_dir, "ecco_icon.png"), os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps")
            os.makedirs(ico_dir, exist_ok=True)
            if os.path.isfile(ico_src): shutil.copy2(ico_src, os.path.join(ico_dir, "ecco-the-dolphin.png"))
            de = f"[Desktop Entry]\nVersion=1.0\nType=Application\nName=Ecco the Dolphin: Defender of the Future\nComment=Native PC Port (Europe & Paradox RUS)\nExec={run_sh}\nIcon=ecco-the-dolphin\nPath={out_dir}\nTerminal=false\nStartupNotify=true\nCategories=Game;AdventureGame;\n"
            if self.create_menu.get():
                ad = os.path.expanduser("~/.local/share/applications"); os.makedirs(ad, exist_ok=True)
                mp = os.path.join(ad, "ecco-the-dolphin.desktop"); open(mp, "w", encoding="utf-8").write(de); os.chmod(mp, 0o755)
                subprocess.run(["update-desktop-database", ad], stderr=subprocess.DEVNULL)
            if self.create_desktop.get():
                dp = os.path.join(subprocess.getoutput("xdg-user-dir DESKTOP").strip() or os.path.expanduser("~/Desktop"), "Ecco the Dolphin.desktop")
                open(dp, "w", encoding="utf-8").write(de); os.chmod(dp, 0o755)
                subprocess.run(["gio", "set", dp, "metadata::trusted", "true"], stderr=subprocess.DEVNULL)
            subprocess.run(["kbuildsycoca6", "--noincremental"], stderr=subprocess.DEVNULL)
            self._set_progress(100, "Установка завершена!")
            self.after(0, lambda: (messagebox.showinfo("Готово", f"Игра успешно установлена в:\n{out_dir}"), self._on_close()))
        except Exception as exc:
            self.after(0, lambda msg=str(exc): (messagebox.showerror("Ошибка", msg), self.install_btn.config(state="normal")))

if __name__ == "__main__":
    FancyEccoLinuxInstaller().mainloop()
