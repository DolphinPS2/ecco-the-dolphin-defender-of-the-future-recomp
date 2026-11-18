#!/usr/bin/env python3
import os, sys, time, math, shutil, subprocess, threading
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
import pygame
from pygame._sdl2.video import Window, Renderer, Texture

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
DISC_PATH = next((os.path.join(BASE_DIR, "disc", f) for f in os.listdir(os.path.join(BASE_DIR, "disc")) if f.startswith("ecco_eu.")), os.path.join(BASE_DIR, "disc", "ecco_eu.chd"))
BIN_PATH = os.path.join(ENGINE_DIR, "ecco-the-dolphin-defender-of-the-future-recomp.exe")
FFMPEG_BIN = os.path.join(BASE_DIR, "runtime", "ffmpeg.exe") if os.path.exists(os.path.join(BASE_DIR, "runtime", "ffmpeg.exe")) else "ffmpeg"
FFPLAY_BIN = os.path.join(BASE_DIR, "runtime", "ffplay.exe") if os.path.exists(os.path.join(BASE_DIR, "runtime", "ffplay.exe")) else "ffplay"
TOML_PATH = os.path.join(ENGINE_DIR, "ecco.toml")
W, H, UI_FPS, VID_FPS = 2560, 1440, 60, 30

def setup_portable_env(choice_name):
    return os.path.join(BASE_DIR, "profiles", choice_name)

def run_engine(choice):
    prof_name = "europe" if choice == 0 else "paradox_rus"
    prof_dir = setup_portable_env(prof_name)
    os.chdir(ENGINE_DIR)
    env = os.environ.copy()
    if os.name == "nt":
        env["APPDATA"] = prof_dir
    else:
        env["XDG_CONFIG_HOME"] = prof_dir
    cmd = [BIN_PATH, "--config", TOML_PATH, "--disc", DISC_PATH, "--window", "--fullscreen", "--widescreen", "--scale", "3", "--interpolate-auto", "--soft-clip"]
    if os.name == "nt":
        cmd += ["--present-path", "dxgi"]
    mod_dir = os.path.join(prof_dir, "dreamcomp", "ecco", "mods", "rus_paradox")
    if choice == 1 and os.path.isdir(mod_dir):
        cmd += ["--mod", mod_dir]
    kw = {"creationflags": subprocess.DETACHED_PROCESS} if os.name == "nt" else {}
    subprocess.Popen(cmd, env=env, **kw)
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
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=self.frame_bytes * 2, creationflags=subprocess.CREATE_NO_WINDOW)
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
    if os.path.exists(intro): subprocess.run([FFPLAY_BIN, "-fs", "-autoexit", "-noborder", "-loglevel", "quiet", intro], creationflags=subprocess.CREATE_NO_WINDOW)
    pygame.init(); pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=1024); pygame.joystick.init()
    joys = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for j in joys: j.init()
    win = Window("Ecco the Dolphin: Defender of the Future", size=(W, H), fullscreen_desktop=True, borderless=True)
    renderer = Renderer(win, vsync=True); renderer.logical_size = (W, H); clock = pygame.time.Clock()
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
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE): launching = True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
                    elif e.key == pygame.K_ESCAPE: snd_back and snd_back.play(); time.sleep(0.25); running = False
                elif e.type == pygame.MOUSEMOTION:
                    if r_eu.collidepoint(e.pos) and sel != 0: sel = 0; snd_sel and snd_sel.play()
                    elif r_ru.collidepoint(e.pos) and sel != 1: sel = 1; snd_sel and snd_sel.play()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if r_eu.collidepoint(e.pos): sel, launching = 0, True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
                    elif r_ru.collidepoint(e.pos): sel, launching = 1, True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700)
        if not launching:
            for j in joys:
                if not j.get_init(): continue
                nb = j.get_numbuttons()
                if (nb > 0 and j.get_button(0)) or (nb > 7 and j.get_button(7)): launching = True; snd_ok and snd_ok.play(); pygame.mixer.fadeout(700); break
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








