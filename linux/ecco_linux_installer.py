#!/usr/bin/env python3
import os, sys, shutil, subprocess, urllib.request, zipfile, tempfile, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

REPO_URL = "https://github.com"
LAUNCHER_ZIP_URL = "https://github.com"

class EccoLinuxInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Установка — Ecco the Dolphin: Defender of the Future (Linux)")
        self.geometry("640x480")
        self.resizable(False, False)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.dirname(self.base_dir)
        ico_png = os.path.join(self.repo_root, "windows", "ecco.png")
        if os.path.exists(ico_png):
            try:
                self.iconphoto(True, tk.PhotoImage(file=ico_png))
            except Exception:
                pass
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
        frm = tk.Frame(self)
        frm.pack(fill="x", **pad)
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
            ws = os.path.expanduser("~/.cache/ecco_recomp_build"); os.makedirs(ws, exist_ok=True)
            self._set_progress(15, "Клонирование dreamcomp (ветка linux-ecco)...")
            dc_dir = os.path.join(ws, "dreamcomp")
            if not os.path.isdir(dc_dir):
                subprocess.run(["git", "clone", "-b", "linux-ecco", "--recurse-submodules", "https://github.com", dc_dir], check=True)
            port_dir = os.path.join(dc_dir, "ports", "ecco-the-dolphin-defender-of-the-future-recomp")
            if os.path.isfile(os.path.join(self.repo_root, "CMakeLists.txt")):
                shutil.rmtree(port_dir, ignore_errors=True)
                shutil.copytree(self.repo_root, port_dir, ignore=shutil.ignore_patterns(".git"))
            elif not os.path.isdir(port_dir):
                subprocess.run(["git", "clone", REPO_URL, port_dir], check=True)
            self._set_progress(30, "Настройка Python venv...")
            venv_dir = os.path.join(dc_dir, ".venv"); py_bin = os.path.join(venv_dir, "bin", "python")
            if not os.path.isfile(py_bin):
                subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
                subprocess.run([py_bin, "-m", "pip", "install", "-e", os.path.join(dc_dir, "engine/tools/dcdisc[test]"), "pillow"], check=True)
            self._set_progress(50, "Компиляция нативного движка Ecco (C++20)...")
            subprocess.run([py_bin, os.path.join(dc_dir, "tools/dc.py"), "setup", port_dir, "--disc", eu], check=True)
            subprocess.run([py_bin, os.path.join(dc_dir, "tools/dc.py"), "build", port_dir], check=True)
            self._set_progress(75, "Загрузка DC PC лаунчера с GitHub...")
            tmp_zip = os.path.join(tempfile.gettempdir(), "ecco_launcher_linux.zip")
            urllib.request.urlretrieve(LAUNCHER_ZIP_URL, tmp_zip)
            with zipfile.ZipFile(tmp_zip, "r") as zf: zf.extractall(out_dir)
            os.makedirs(os.path.join(out_dir, "engine"), exist_ok=True); os.makedirs(os.path.join(out_dir, "disc"), exist_ok=True)
            b_dst = os.path.join(out_dir, "engine/ecco-the-dolphin-defender-of-the-future-recomp")
            shutil.copy2(os.path.join(port_dir, "build/game/ecco-the-dolphin-defender-of-the-future-recomp"), b_dst); os.chmod(b_dst, 0o755)
            shutil.copy2(eu, os.path.join(out_dir, "disc", "ecco_eu" + os.path.splitext(eu)[1]))
            if ru and os.path.isfile(ru):
                self._set_progress(88, "Компиляция cdirip и распаковка Paradox RUS...")
                t_dir = os.path.join(out_dir, "tools"); os.makedirs(t_dir, exist_ok=True)
                c_src = os.path.join(port_dir, "linux/cdirip")
                c_files = [os.path.join(c_src, f) for f in os.listdir(c_src) if f.endswith(".c")]
                subprocess.run(["gcc", "-O2", *c_files, "-o", os.path.join(t_dir, "cdirip")], check=True)
                env = os.environ.copy(); env["PATH"] = t_dir + ":" + env.get("PATH", "")
                subprocess.run([py_bin, os.path.join(port_dir, "tools/extract_paradox_mod.py"), ru, os.path.join(out_dir, "profiles/paradox_rus/dreamcomp/ecco/mods/rus_paradox")], env=env, check=True)
            self._set_progress(96, "Создание ярлыков .desktop...")
            run_sh = os.path.join(out_dir, "Ecco_the_Dolphin.sh")
            with open(run_sh, "w", encoding="utf-8") as sf: sf.write(f"#!/usr/bin/env bash\ncd \"{out_dir}\"\nexec python3 \"{out_dir}/launcher.py\" \"$@\"\n")
            os.chmod(run_sh, 0o755)
            ico = os.path.join(out_dir, "ecco.png")
            if not os.path.isfile(ico) and os.path.isfile(os.path.join(port_dir, "windows/ecco.png")): shutil.copy2(os.path.join(port_dir, "windows/ecco.png"), ico)
            de = f"[Desktop Entry]\nType=Application\nName=Ecco the Dolphin: Defender of the Future\nExec=\"{run_sh}\"\nIcon={ico}\nTerminal=false\nCategories=Game;\n"
            if self.create_menu.get():
                ad = os.path.expanduser("~/.local/share/applications"); os.makedirs(ad, exist_ok=True)
                with open(os.path.join(ad, "ecco-the-dolphin.desktop"), "w", encoding="utf-8") as df: df.write(de)
            if self.create_desktop.get() and os.path.isdir(os.path.expanduser("~/Desktop")):
                dp = os.path.expanduser("~/Desktop/Ecco the Dolphin.desktop")
                with open(dp, "w", encoding="utf-8") as df: df.write(de)
                os.chmod(dp, 0o755)
            self._set_progress(100, "Готово!")
            self.after(0, lambda: (messagebox.showinfo("Готово", f"Игра установлена в:\n{out_dir}"), self.destroy()))
        except Exception as exc:
            self.after(0, lambda: (messagebox.showerror("Ошибка", str(exc)), self.install_btn.config(state="normal")))

if __name__ == "__main__":
    EccoLinuxInstaller().mainloop()