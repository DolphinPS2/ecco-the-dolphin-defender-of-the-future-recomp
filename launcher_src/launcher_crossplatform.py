#!/usr/bin/env python3
import os, sys, time, math, shutil, subprocess, threading, webbrowser
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
import pygame
from pygame._sdl2.video import Window, Renderer, Texture

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
DISC_PATH = os.path.join(BASE_DIR, "disc", "ecco_eu.chd")
BIN_PATH = os.path.join(ENGINE_DIR, "ecco-the-dolphin-defender-of-the-future-recomp" + (".exe" if os.name == "nt" else ""))
FFMPEG_BIN = (os.path.join(BASE_DIR, "runtime", "ffmpeg.exe") if os.name == "nt" else "ffmpeg") if os.path.exists((os.path.join(BASE_DIR, "runtime", "ffmpeg.exe") if os.name == "nt" else "ffmpeg")) else "ffmpeg"
FFPLAY_BIN = os.path.join(BASE_DIR, "runtime", "ffplay.exe") if os.path.exists(os.path.join(BASE_DIR, "runtime", "ffplay.exe")) else "ffplay"
TOML_PATH = os.path.join(ENGINE_DIR, "ecco.toml")
W, H, UI_FPS, VID_FPS = 2560, 1440, 60, 30

def setup_portable_env(choice_name):
    return os.path.join(BASE_DIR, "profiles", choice_name)

def run_engine(choice):
    prof_name = "europe" if choice == 0 else "paradox_rus"
    prof_root = setup_portable_env(prof_name)
    cfg_dir = os.path.join(prof_root, "dreamcomp", "ecco")
    os.makedirs(cfg_dir, exist_ok=True)
    settings_path = os.path.join(cfg_dir, "settings.ini")
    vmu_path = os.path.join(cfg_dir, "vmu_a1.bin")
    mod_dir = os.path.join(cfg_dir, "mods", "rus_paradox")
    os.chdir(ENGINE_DIR)
    env = os.environ.copy()
    env["APPDATA"] = prof_root; env["XDG_CONFIG_HOME"] = prof_root; env["LD_LIBRARY_PATH"] = ENGINE_DIR + ":" + env.get("LD_LIBRARY_PATH", "")
    args = [BIN_PATH, "--config", TOML_PATH, "--disc", DISC_PATH, "--settings", settings_path, "--vmu", vmu_path, "--window", "--fullscreen", "--widescreen", "--scale", "3", "--interpolate-auto", "--soft-clip", "--present-path", ("dxgi" if os.name == "nt" else "vulkan")]
    if choice == 1 and os.path.isdir(mod_dir):
        args += ["--mod", mod_dir]
    subprocess.Popen(args, env=env, start_new_session=True)
    time.sleep(0.5)
    pygame.quit()
    sys.exit(0)

class GPUVideoStream:
    def __init__(self, renderer, path, width, height, alpha=True, delay=0.0):
        self.renderer, self.path, self.w, self.h, self.alpha = renderer, path, width, height, alpha
        self.pix_fmt = "rgba" if alpha else "rgb24"
        self.frame_bytes = width * height * (4 if alpha else 3)
        self.delay, self.proc, self.running = delay, None, True
        self.lock, self.latest_data, self.dirty = threading.Lock(), None, False
        surf = pygame.Surface((width, height), pygame.SRCALPHA if alpha else 0)
        if alpha: surf.fill((0, 0, 0, 0))
        self.tex = Texture.from_surface(renderer, surf); self.tex.blend_mode = pygame.BLENDMODE_BLEND
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        if self.delay > 0: time.sleep(self.delay)
        if not self.running: return
        cmd = [FFMPEG_BIN, "-loglevel", "quiet", "-stream_loop", "-1"] + (["-c:v", "libvpx-vp9"] if self.alpha else [])
        vf = f"scale={self.w}:{self.h}:flags=bilinear,fps={VID_FPS}" + (",unpremultiply=inplace=1" if self.alpha else "")
        cmd += ["-i", self.path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", self.pix_fmt, "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=self.frame_bytes * 2, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        interval, next_t = 1.0 / VID_FPS, time.time()
        while self.running:
            data = self.proc.stdout.read(self.frame_bytes)
            if len(data) != self.frame_bytes: break
            with self.lock: self.latest_data, self.dirty = data, True
            next_t += interval; sd = next_t - time.time()
            if sd > 0: time.sleep(sd)
            else: next_t = time.time()

    def get_tex(self):
        if self.dirty:
            with self.lock: data, self.dirty = self.latest_data, False
            if data:
                s = pygame.image.frombuffer(data, (self.w, self.h), "RGBA" if self.alpha else "RGB")
                self.tex = Texture.from_surface(self.renderer, s); self.tex.blend_mode = pygame.BLENDMODE_BLEND
        return self.tex

    def close(self):
        self.running = False
        if self.proc:
            try: self.proc.terminate(); self.proc.wait(timeout=1)
            except Exception: self.proc.kill()

def main():
    if "--europe" in sys.argv: run_engine(0)
    elif "--paradox" in sys.argv: run_engine(1)
    setup_portable_env("paradox_rus")
    intro = os.path.join(MEDIA_DIR, "intro_2k.mp4")
    if os.path.exists(intro): subprocess.run([FFPLAY_BIN, "-fs", "-autoexit", "-noborder", "-loglevel", "quiet", intro], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    pygame.init(); pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=1024); pygame.joystick.init(); pygame.font.init()
    joys = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for j in joys: j.init()
    win = Window("Ecco the Dolphin: Defender of the Future", size=(W, H), fullscreen_desktop=True, borderless=True)
    renderer = Renderer(win, vsync=True); renderer.logical_size = (W, H); clock = pygame.time.Clock()
    ui_font = pygame.font.SysFont("DejaVu Sans", 26, bold=True)
    net_font = pygame.font.SysFont("DejaVu Sans", 18, bold=True)
    patch_state = {"active": False, "done": False, "prog": 0.0, "vis_prog": 0.0, "text": "", "color": (185, 235, 255)}
    def draw_dreampipe_beacon(t_anim, mpos):
        bw, bh = 380, 44; bx, by = (W - bw) // 2, 1085; rect = pygame.Rect(bx, by, bw, bh)
        hovered = rect.collidepoint(mpos); surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pulse = 0.5 + 0.5 * math.sin(t_anim * 1.6); alpha = 165 if hovered else int(26 + 34 * pulse)
        col = (180, 240, 255) if hovered else (130, 205, 245)
        glyphs = [net_font.render(ch, True, col) for ch in "SEGANET • DREAMPIPE.NET"]
        cx = (bw - sum(g.get_width() for g in glyphs)) // 2 + int(math.sin(t_anim * 1.1) * 5.0)
        for i, g in enumerate(glyphs):
            g.set_alpha(alpha); surf.blit(g, (cx, (bh - g.get_height()) // 2 + int(math.sin(t_anim * 2.2 + i * 0.45) * 3.0))); cx += g.get_width()
        tex = Texture.from_surface(renderer, surf); tex.blend_mode = pygame.BLENDMODE_BLEND; renderer.blit(tex, dest=rect); return rect
    def draw_progress_bar(t_anim):
        if sel != 1 and not patch_state["active"]: return pygame.Rect(0, 0, 0, 0)
        bar_w, bar_h = 1040, 64; bx, by = (W - bar_w) // 2, H - 96; rect = pygame.Rect(bx, by, bar_w, bar_h)
        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA); tp = patch_state["prog"]
        vp = min(tp, patch_state["vis_prog"] + 0.0045) if patch_state["vis_prog"] < tp else tp; patch_state["vis_prog"] = vp
        if vp > 0.005:
            for wx in range(0, int(bar_w * max(0.0, min(1.0, vp))), 12):
                pygame.draw.circle(surf, (70, 195, 255, 48), (wx + 6, bar_h - 10 + int(math.sin(t_anim * 3.0 + wx * 0.025) * 3.0)), 4)
        pulse = 0.5 + 0.5 * math.sin(t_anim * 2.1)
        txt_alpha = int((65 if not patch_state["active"] else 110) + (70 if not patch_state["active"] else 75) * pulse)
        text_str = patch_state["text"] if (patch_state["active"] or patch_state.get("done")) else "[F2 / Y] ПЕРЕНОС ПЕРЕВОДА И ОРИГИНАЛЬНОЙ МУЗЫКИ"
        glyphs = [ui_font.render(ch, True, patch_state["color"]) for ch in text_str]; cx = (bar_w - sum(g.get_width() for g in glyphs)) // 2
        for idx, g in enumerate(glyphs):
            g.set_alpha(txt_alpha); surf.blit(g, (cx, (bar_h - g.get_height()) // 2 + int(math.sin(t_anim * 3.2 - idx * 0.38) * 4.5))); cx += g.get_width()
        tex = Texture.from_surface(renderer, surf); tex.blend_mode = pygame.BLENDMODE_BLEND; renderer.blit(tex, dest=rect); return rect

    def pick_disc_crossplatform():
        if os.name == "nt":
            ps = "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.Form; $f.TopMost=$true; $d=New-Object System.Windows.Forms.OpenFileDialog; if($d.ShowDialog($f) -eq 'OK'){Write-Output $d.FileName}"
            return subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True).stdout.strip()
        for cmd in (["zenity", "--file-selection", "--title=Выберите образ Paradox RUS (.cdi/.chd/.gdi)"], ["kdialog", "--getopenfilename", os.path.expanduser("~"), "*.cdi *.chd *.gdi *.cue"]):
            if shutil.which(cmd):
                return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        return subprocess.run([sys.executable, "-c", "import tkinter as tk; from tkinter import filedialog; r=tk.Tk(); r.withdraw(); print(filedialog.askopenfilename())"], capture_output=True, text=True).stdout.strip()
    def trigger_patch_dialog():
        if sel != 1 or patch_state["active"] or patch_state.get("dialog_open"): return
        patch_state["dialog_open"] = True
        def worker():
            try:
                p = pick_disc_crossplatform()
                if not p: patch_state["dialog_open"] = False; return
                patch_state.update({"active": True, "done": False, "prog": 0.02, "vis_prog": 0.0, "text": "ПЕРЕНОС ПЕРЕВОДА И ОРИГИНАЛЬНОЙ МУЗЫКИ: 0%", "color": (255, 240, 150)})
                def on_prog(cur, tot, fn):
                    pct = int((cur / max(1, tot)) * 100); patch_state["prog"] = cur / max(1, tot)
                    patch_state["text"] = f"ПЕРЕНОС ПЕРЕВОДА И ОРИГИНАЛЬНОЙ МУЗЫКИ: {cur}/{tot} ({pct}%)"
                tdir = os.path.join(BASE_DIR, "tools")
                if tdir not in sys.path: sys.path.insert(0, tdir)
                from extract_paradox_mod import extract_from_disc
                mod_out = os.path.join(setup_portable_env("paradox_rus"), "dreamcomp", "ecco", "mods", "rus_paradox")
                extract_from_disc(p, mod_out, on_progress=on_prog)
                patch_state.update({"active": False, "done": True, "prog": 1.0, "text": "ГОТОВО! ПЕРЕВОД И ОРИГИНАЛЬНАЯ МУЗЫКА ПЕРЕНЕСЕНЫ", "color": (140, 255, 185)})
            except Exception as ex:
                patch_state.update({"active": False, "done": True, "prog": 0.0, "text": f"ОШИБКА: {str(ex)[:45]}", "color": (255, 145, 145)})
            finally:
                patch_state["dialog_open"] = False
        threading.Thread(target=worker, daemon=True).start()

    def load_snd(n, v):
        p = os.path.join(MEDIA_DIR, n)
        if os.path.exists(p): s = pygame.mixer.Sound(p); s.set_volume(v); return s
        return None
    snd_sel, snd_ok, snd_back = load_snd("sfx_select.wav", 0.85), load_snd("sfx_confirm.wav", 0.95), load_snd("sfx_back.wav", 0.8)
    snd_surf, snd_mus = load_snd("surf.mp3", 0.42), load_snd("music.mp3", 0.75)
    if snd_surf: snd_surf.play(loops=-1, fade_ms=1200)
    if snd_mus: snd_mus.play(loops=-1, fade_ms=1500)
    streams = [
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "ocean_2k.mp4"), W, H, False),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "dolphin_3d.webm"), 1600, 1200, True),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "sega_logo.webm"), 680, 382, True),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "title_en.webm"), 1440, 810, True),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "title_ru.webm"), 1440, 810, True),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "btn_europe.webm"), 960, 540, True, 0.1),
        GPUVideoStream(renderer, os.path.join(MEDIA_DIR, "btn_paradox.webm"), 960, 540, True, 0.45),
    ]
    bg_s, dol_s, sega_s, ten_s, tru_s, eu_s, ru_s = streams
    fade_s = pygame.Surface((64, 64), pygame.SRCALPHA); fade_s.fill((0, 0, 0, 255))
    fade_tex = Texture.from_surface(renderer, fade_s); fade_tex.blend_mode = pygame.BLENDMODE_BLEND
    sel, focus, logo_focus, fade, launching, l_timer, joy_cd, t_anim = 1, 1.0, 1.0, 255.0, False, 0.0, 0.0, 0.0
    r_eu, r_ru = pygame.Rect(210, 940, 860, 380), pygame.Rect(1490, 940, 860, 380)
    badge_rect = pygame.Rect((W - 1040) // 2, H - 96, 1040, 64)
    net_rect = pygame.Rect((W - 380) // 2, 1085, 380, 44)
    running = True
    while running:
        dt = clock.tick(UI_FPS) / 1000.0; t_anim += dt; joy_cd = max(0.0, joy_cd - dt)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.JOYDEVICEADDED: j = pygame.joystick.Joystick(e.device_index); j.init(); joys.append(j)
            elif not launching:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a) and sel != 0: sel = 0; snd_sel and snd_sel.play()
                    elif e.key in (pygame.K_RIGHT, pygame.K_d) and sel != 1: sel = 1; snd_sel and snd_sel.play()
                    elif e.key == pygame.K_F2: snd_sel and snd_sel.play(); trigger_patch_dialog()
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE) and not patch_state['active']: launching = True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
                    elif e.key == pygame.K_ESCAPE: snd_back and snd_back.play(); time.sleep(0.25); running = False
                elif e.type == pygame.MOUSEMOTION:
                    if r_eu.collidepoint(e.pos) and sel != 0: sel = 0; snd_sel and snd_sel.play()
                    elif r_ru.collidepoint(e.pos) and sel != 1: sel = 1; snd_sel and snd_sel.play()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if net_rect.collidepoint(e.pos): snd_sel and snd_sel.play(); webbrowser.open('https://dreampipe.net')
                    elif badge_rect.collidepoint(e.pos): snd_sel and snd_sel.play(); trigger_patch_dialog()
                    elif r_eu.collidepoint(e.pos) and not patch_state['active']: sel, launching = 0, True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
                    elif r_ru.collidepoint(e.pos): sel, launching = 1, True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
        if not launching:
            for j in joys:
                if not j.get_init(): continue
                nb = j.get_numbuttons()
                if any(nb > b and j.get_button(b) for b in (0, 7, 9, 11)) and not patch_state['active']: launching = True;
                if (nb > 3 and j.get_button(3)) and joy_cd <= 0: joy_cd = 0.4; snd_sel and snd_sel.play(); trigger_patch_dialog(); break
                if False: snd_ok and snd_ok.play(); pygame.mixer.fadeout(700); break
                if (nb > 1 and j.get_button(1)) or (nb > 6 and j.get_button(6)): snd_back and snd_back.play(); time.sleep(0.25); running = False; break
                if joy_cd <= 0:
                    go_l, go_r = (nb > 13 and j.get_button(13)), (nb > 14 and j.get_button(14))
                    if j.get_numhats() > 0:
                        hx, hy = j.get_hat(0)
                        if hx < 0: go_l = True
                        elif hx > 0: go_r = True
                    for ax in (0, 6):
                        if j.get_numaxes() > ax:
                            v = j.get_axis(ax)
                            if v < -0.55: go_l = True
                            elif v > 0.55: go_r = True
                    if go_l and sel != 0: sel, joy_cd = 0, 0.22; snd_sel and snd_sel.play()
                    elif go_r and sel != 1: sel, joy_cd = 1, 0.22; snd_sel and snd_sel.play()
        focus += (float(sel) - focus) * min(1.0, dt * 10.0); logo_focus += (float(sel) - logo_focus) * min(1.0, dt * 3.0)
        renderer.clear()
        renderer.blit(bg_s.get_tex(), dest=pygame.Rect(0, 0, W, H))
        renderer.blit(dol_s.get_tex(), dest=pygame.Rect((W - 1600) // 2, (H - 1200) // 2 - 25, 1600, 1200))
        renderer.blit(sega_s.get_tex(), dest=pygame.Rect((W - 680) // 2, -35, 680, 382))
        lf = max(0.0, min(1.0, logo_focus)); smooth_lf = lf * lf * (3.0 - 2.0 * lf)
        a_ru, a_en = int(80 * smooth_lf), int(80 * (1.0 - smooth_lf)); ty = int(155 + math.sin(t_anim * 1.4) * 6)
        if a_en > 2: t1 = ten_s.get_tex(); t1.color = (195, 235, 255); t1.alpha = a_en; renderer.blit(t1, dest=pygame.Rect((W - 1440) // 2, ty, 1440, 810))
        if a_ru > 2: t2 = tru_s.get_tex(); t2.color = (195, 235, 255); t2.alpha = a_ru; renderer.blit(t2, dest=pygame.Rect((W - 1440) // 2, ty, 1440, 810))
        for idx, (st, cx) in enumerate(((eu_s, 640), (ru_s, 1920))):
            w_f = (1.0 - focus) if idx == 0 else focus; sc = 0.68 + 0.18 * w_f; sw, sh = int(960 * sc), int(540 * sc)
            tex = st.get_tex(); tex.color = (int(140 + 35 * w_f), int(185 + 30 * w_f), 238); tex.alpha = int(75 + 80 * w_f)
            renderer.blit(tex, dest=pygame.Rect(cx - sw // 2, int(1080 + 22 * (1.0 - w_f) - sh // 2), sw, sh))
        net_rect = draw_dreampipe_beacon(t_anim, pygame.mouse.get_pos())
        badge_rect = draw_progress_bar(t_anim)
        if not launching and fade > 0: fade = max(0.0, fade - dt * 320.0)
        elif launching:
            l_timer += dt; fade = min(255.0, fade + dt * 380.0)
            if l_timer >= 0.75:
                for s in streams: s.close()
                pygame.quit(); run_engine(sel)
        if fade > 0: fade_tex.alpha = int(fade); renderer.blit(fade_tex, dest=pygame.Rect(0, 0, W, H))
        renderer.present()
    for s in streams: s.close()
    pygame.quit()

if __name__ == "__main__": main()








