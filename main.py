"""MACRO PAD CONTROL CENTER - Kivy app for Android (Pydroid 3 compatible).

Single file, no internet, no desktop-only dependencies.
Settings are saved to a JSON file in the app's private storage.
"""
import copy
import json
import math
import os
import threading
import time
import urllib.request

from kivy.app import App
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform

# ----------------------------------------------------------------- constants
BG = (0.02, 0.02, 0.03, 1)
CARD = (0.07, 0.08, 0.11, 0.86)
FIELD = (0.12, 0.14, 0.20, 1)
ACC = (0.15, 0.48, 1.0, 1)
TXT = (1, 1, 1, 1)
DIM = (0.62, 0.68, 0.80, 1)

MENU_KEYS = ['home', 'music', 'shortcuts', 'profiles', 'display', 'settings']
THEMES = {  # name: (foreground, background)
    'White': ((1, 1, 1), (0, 0, 0)),
    'Blue': ((0.35, 0.7, 1), (0, 0, 0)),
    'Amber': ((1, 0.72, 0.1), (0, 0, 0)),
    'Green': ((0.3, 1, 0.45), (0, 0, 0)),
    'Inverted': ((0, 0, 0), (0.92, 0.96, 1)),
}
TIMEOUT_SECS = {'Never': 0, '10 sec': 10, '30 sec': 30, '1 min': 60, '5 min': 300}
TEXT_SIZES = {'Small': 7, 'Medium': 9, 'Large': 11}
CLOCK_SIZES = {'Small': 12, 'Medium': 15, 'Large': 18}

# key, label, kind, options
DISPLAY_ITEMS = [
    ('brightness', 'Brightness', 'slider', (5, 100)),
    ('text_size', 'Text size', 'choice', list(TEXT_SIZES)),
    ('show_clock', 'Show clock', 'bool', None),
    ('clock_format', 'Clock format', 'choice', ['24 hour', '12 hour']),
    ('theme', 'OLED theme', 'choice', list(THEMES)),
    ('animations', 'Animations', 'bool', None),
    ('timeout', 'Screen timeout', 'choice', list(TIMEOUT_SECS)),
    ('status_icons', 'Status icons', 'bool', None),
]

FUNCTIONS = ['Keyboard Shortcut', 'Launch App', 'Action', 'Text Macro', 'Media', 'None']
SHORTCUTS = ['Ctrl+C', 'Ctrl+V', 'Ctrl+X', 'Ctrl+Z', 'Ctrl+S', 'Ctrl+A', 'Ctrl+Shift+Esc',
             'Alt+Tab', 'Win+D', 'Win+L', 'Ctrl+Alt+Del', 'F5', 'Print Screen', 'Custom']
APPS_ACTIONS = ['Chrome', 'Spotify', 'Discord', 'OBS Studio', 'VS Code', 'Terminal',
                'File Explorer', 'Calculator', 'Steam', 'Zoom', 'Mute Mic', 'Screenshot',
                'Lock PC', 'Play/Pause', 'Next Track', 'Previous Track', 'Mute']
ENC_FUNCS = ['Volume', 'Brightness', 'Scroll', 'Zoom', 'Media Track', 'Custom']
ENC_ACTIONS = ['Volume Up', 'Volume Down', 'Brightness Up', 'Brightness Down', 'Scroll Up',
               'Scroll Down', 'Zoom In', 'Zoom Out', 'Next Track', 'Previous Track', 'Mute',
               'Play/Pause', 'Next Profile', 'Previous Profile', 'None']
ENC_DEFAULTS = {
    'Volume': ('Volume Up', 'Volume Down', 'Mute'),
    'Brightness': ('Brightness Up', 'Brightness Down', 'None'),
    'Scroll': ('Scroll Down', 'Scroll Up', 'Play/Pause'),
    'Zoom': ('Zoom In', 'Zoom Out', 'None'),
    'Media Track': ('Next Track', 'Previous Track', 'Play/Pause'),
    'Custom': ('None', 'None', 'None'),
}

# phone action -> command sent to the computer (see pc_server.py)
ACTION_PC = {
    'Volume Up': ('media', {'name': 'volup'}), 'Volume Down': ('media', {'name': 'voldown'}),
    'Mute': ('media', {'name': 'mute'}), 'Play/Pause': ('media', {'name': 'playpause'}),
    'Next Track': ('media', {'name': 'next'}), 'Previous Track': ('media', {'name': 'prev'}),
    'Scroll Up': ('scroll', {'amount': 300}), 'Scroll Down': ('scroll', {'amount': -300}),
    'Zoom In': ('key', {'combo': 'ctrl+plus'}), 'Zoom Out': ('key', {'combo': 'ctrl+minus'}),
    'Screenshot': ('key', {'combo': 'printscreen'}), 'Lock PC': ('key', {'combo': 'win+l'}),
}
APP_NAMES = APPS_ACTIONS[:10]

# 8x8 pixel icons for the OLED
_ICON_DATA = {
    'play': "..#...../..##..../..###.../..####../..###.../..##..../..#...../........",
    'pause': "......../.##..##./.##..##./.##..##./.##..##./.##..##./.##..##./........",
    'volume': "...#..../..##..#./####...#/####.#.#/####...#/..##..#./...#..../........",
    'mic': "..####../..####../..####../#.####.#/#.####.#/.######./...##.../..####..",
    'copy': "#####.../#...#.../#.#####./#.#...#./###...#./..#...#./..#####./........",
    'home': "...##.../..####../.######./########/.##..##./.##..##./.##..##./........",
    'star': "...##.../...##.../########/.######./..####../.##..##./.#....#./........",
    'bolt': "....##../...##.../..##..../.######./...##.../..##..../.##...../.#......",
    'grid': "###.###./###.###./###.###./......../###.###./###.###./###.###./........",
    'note': "...#####/...#...#/...#...#/...#...#/..##..##/.###.###/..#...#./........",
}
ICONS = {k: v.split('/') for k, v in _ICON_DATA.items()}

DEFAULT_EXPORT = ('/storage/emulated/0/Download/macropad_config.json'
                  if platform == 'android'
                  else os.path.join(os.path.expanduser('~'), 'macropad_config.json'))


# ------------------------------------------------------------- config / data
def _btn(name, func, shortcut, app, icon):
    return {'name': name, 'function': func, 'shortcut': shortcut, 'custom': '',
            'app': app, 'icon': icon, 'enabled': True}


def _enc(name, func):
    cw, ccw, pr = ENC_DEFAULTS[func]
    return {'name': name, 'function': func, 'cw': cw, 'ccw': ccw, 'press': pr, 'enabled': True}


def default_profile(name):
    return {
        'name': name,
        'buttons': [
            _btn('Copy', 'Keyboard Shortcut', 'Ctrl+C', 'Chrome', 'copy'),
            _btn('Paste', 'Keyboard Shortcut', 'Ctrl+V', 'Chrome', 'grid'),
            _btn('Mute Mic', 'Action', 'Ctrl+C', 'Mute Mic', 'mic'),
            _btn('Play', 'Media', 'Ctrl+C', 'Play/Pause', 'play'),
            _btn('Browser', 'Launch App', 'Ctrl+C', 'Chrome', 'home'),
            _btn('Discord', 'Launch App', 'Ctrl+C', 'Discord', 'bolt'),
        ],
        'encoders': [_enc('Volume', 'Volume'), _enc('Brightness', 'Brightness'),
                     _enc('Scroll', 'Scroll')],
    }


def default_config():
    return {
        'version': 1,
        'names': {'device': 'MACRO PAD', 'title': 'MACRO PAD',
                  'menu': ['HOME', 'MUSIC', 'SHORTCUTS', 'PROFILES', 'DISPLAY', 'SETTINGS']},
        'display': {'brightness': 80, 'text_size': 'Medium', 'show_clock': True,
                    'clock_format': '24 hour', 'theme': 'White', 'animations': True,
                    'timeout': 'Never', 'status_icons': True},
        'state': {'volume': 50, 'muted': False},
        'app': {'export_path': DEFAULT_EXPORT, 'wallpaper': '', 'wallpaper_dim': 55},
        'pc': {'enabled': False, 'host': '192.168.1.10', 'port': '8765', 'token': 'macropad'},
        'active_profile': 0,
        'profiles': [default_profile('Default'), default_profile('Gaming'),
                     default_profile('Work')],
    }


def merge(default, loaded):
    """Keep the structure of `default`, take values from `loaded` where types match."""
    if isinstance(default, dict) and isinstance(loaded, dict):
        return {k: (merge(v, loaded[k]) if k in loaded else copy.deepcopy(v))
                for k, v in default.items()}
    if type(default) is type(loaded):
        return loaded
    return copy.deepcopy(default)


def sanitize(raw):
    base = default_config()
    if not isinstance(raw, dict):
        raw = {}
    cfg = merge(base, raw)
    menu = cfg['names']['menu']
    if len(menu) != 6 or not all(isinstance(m, str) for m in menu):
        cfg['names']['menu'] = base['names']['menu']
    d = cfg['display']
    for key, _l, kind, opt in DISPLAY_ITEMS:
        if kind == 'choice' and d[key] not in opt:
            d[key] = base['display'][key]
    d['brightness'] = max(5, min(100, int(d['brightness'])))
    cfg['state']['volume'] = max(0, min(100, int(cfg['state']['volume'])))
    profiles = []
    src = raw.get('profiles')
    for p in (src if isinstance(src, list) else []):
        if not isinstance(p, dict):
            continue
        dp_ = default_profile(str(p.get('name', 'Profile')))
        q = merge(dp_, p)
        for key, n in (('buttons', 6), ('encoders', 3)):
            lst = p.get(key) if isinstance(p.get(key), list) else []
            q[key] = [merge(dp_[key][i], lst[i]) if i < len(lst) and isinstance(lst[i], dict)
                      else dp_[key][i] for i in range(n)]
        profiles.append(q)
    cfg['profiles'] = profiles or base['profiles']
    if not (0 <= cfg['active_profile'] < len(cfg['profiles'])):
        cfg['active_profile'] = 0
    return cfg


def APP():
    return App.get_running_app()


# ------------------------------------------------------------------ OLED view
VIEWS = []
_TEX = {}


def get_tex(txt, px):
    key = (txt, int(round(px)))
    t = _TEX.get(key)
    if t is None:
        if len(_TEX) > 400:
            _TEX.clear()
        cl = CoreLabel(text=txt, font_size=key[1], color=(1, 1, 1, 1))
        cl.refresh()
        t = cl.texture
        _TEX[key] = t
    return t


class OledView(Widget):
    """128x64 monochrome OLED simulator, drawn in OLED pixel coordinates."""

    def __init__(self, **kw):
        super().__init__(**kw)
        VIEWS.append(self)
        self.s, self.ox, self.oy = 1, 0, 0
        self.fg = self.bg = (1, 1, 1, 1)
        self.bind(pos=self.redraw, size=self.redraw)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            APP().wake()
            return True
        return False

    # --- primitives
    def rect(self, x, y, w, h, color=None):
        Color(*(color or self.fg))
        Rectangle(pos=(self.ox + x * self.s, self.oy + (64 - y - h) * self.s),
                  size=(w * self.s, h * self.s))

    def outline(self, x, y, w, h, color=None):
        self.rect(x, y, w, 1, color)
        self.rect(x, y + h - 1, w, 1, color)
        self.rect(x, y, 1, h, color)
        self.rect(x + w - 1, y, 1, h, color)

    def bar(self, x, y, w, h, pct, color=None):
        self.outline(x, y, w, h, color)
        self.rect(x + 1, y + 1, (w - 2) * max(0, min(100, pct)) / 100.0, h - 2, color)

    def icon(self, name, x, y, color=None):
        rows = ICONS.get(name)
        if not rows:
            return
        for r, line in enumerate(rows):
            c = 0
            while c < 8:
                if line[c] == '#':
                    e = c
                    while e < 8 and line[e] == '#':
                        e += 1
                    self.rect(x + c, y + r, e - c, 1, color)
                    c = e
                else:
                    c += 1

    def text(self, txt, x, y, size=8, anchor='l', color=None, maxw=126):
        txt = str(txt)
        if not txt.strip():
            return 0
        t = get_tex(txt, size * self.s)
        lim = maxw * self.s
        if t.width > lim and len(txt) > 1:
            n = max(1, int(len(txt) * lim / t.width) - 1)
            t = get_tex(txt[:n] + '.', size * self.s)
        X = self.ox + x * self.s
        if anchor == 'c':
            X -= t.width / 2.0
        elif anchor == 'r':
            X -= t.width
        Color(*(color or self.fg))
        Rectangle(texture=t, pos=(X, self.oy + (64 - y) * self.s - t.height), size=t.size)
        return t.width / self.s

    # --- frame
    def redraw(self, *_):
        app = APP()
        if app is None or not hasattr(app, 'nav') or self.width < 10:
            return
        d = app.cfg['display']
        fg, bg = THEMES[d['theme']]
        b = 0.15 + 0.85 * d['brightness'] / 100.0
        self.fg = tuple(c * b for c in fg) + (1,)
        self.bg = tuple(c * b for c in bg) + (1,)
        self.s = max(0.5, min((self.width - dp(14)) / 128.0, (self.height - dp(14)) / 64.0))
        self.ox = self.x + (self.width - 128 * self.s) / 2.0
        self.oy = self.y + (self.height - 64 * self.s) / 2.0
        self.canvas.clear()
        with self.canvas:
            Color(0.1, 0.11, 0.15, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(*self.bg)
            Rectangle(pos=(self.ox, self.oy), size=(128 * self.s, 64 * self.s))
            if app.asleep():
                return
            try:
                self.draw_screen(app)
            except Exception as exc:  # never kill the UI loop
                print('OLED draw error:', exc)

    def draw_screen(self, app):
        mode = app.nav['mode']
        if mode == 'home':
            self.page_home(app)
        elif mode == 'music':
            self.page_music(app)
        else:
            title, rows, sel = app.list_page(mode)
            self.draw_list(app, title, rows, sel)
        if time.time() < app.flash_until:
            l1, l2 = app.flash_text
            self.rect(8, 14, 112, 36, self.bg)
            self.outline(8, 14, 112, 36)
            self.outline(10, 16, 108, 32)
            self.text(l1, 64, 19, 9, 'c', maxw=100)
            self.text(l2, 64, 33, 8, 'c', maxw=100)

    def title_bar(self, app, title, extra=''):
        rh = TEXT_SIZES[app.cfg['display']['text_size']] + 3
        self.rect(0, 0, 128, rh)
        self.text(title, 3, 1, rh - 3, color=self.bg, maxw=90)
        if extra and app.cfg['display']['status_icons']:
            self.text(extra, 125, 1, max(6, rh - 4), 'r', color=self.bg, maxw=30)
        return rh

    def draw_list(self, app, title, rows, sel):
        fs = TEXT_SIZES[app.cfg['display']['text_size']]
        rh = self.title_bar(app, title, '%d/%d' % (sel + 1, len(rows)))
        vis = max(1, (64 - rh) // rh)
        start = max(0, min(sel - vis // 2, len(rows) - vis))
        has_icon = any(r[0] for r in rows)
        for i, (ic, left, right) in enumerate(rows[start:start + vis]):
            y = rh + i * rh
            on = (start + i) == sel
            col = self.bg if on else self.fg
            if on:
                self.rect(0, y, 128, rh)
            x = 3
            if has_icon:
                if ic:
                    self.icon(ic, 2, y + max(0, (rh - 8) // 2), col)
                x = 13
            rw = self.text(right, 125, y + 1, fs, 'r', col, maxw=60) if right else 0
            self.text(left, x, y + 1, fs, 'l', col, maxw=max(10, 123 - rw - x))

    def page_home(self, app):
        c = app.cfg
        d = c['display']
        t = time.time()
        anim = d['animations']
        icons = d['status_icons']
        ph = int(t * 3) % 6 if anim else -1
        for i in range(6):
            gx, gy = 4 + (i % 3) * 7, 4 + (i // 3) * 7
            if i == ph or not anim:
                self.rect(gx, gy, 5, 5)
            else:
                self.outline(gx, gy, 5, 5)
        self.text(c['names']['title'], 28, 2, 11, maxw=80)
        self.text(c['names']['device'], 28, 15, 7, maxw=95)
        if icons:
            self.outline(110, 3, 13, 7)
            self.rect(123, 5, 1, 3)
            self.rect(112, 5, 8, 3)
            if anim and int(t * 2) % 2:
                self.rect(103, 5, 3, 3)
        prof = app.profile['name']
        if d['show_clock']:
            fmt = '%H:%M' if d['clock_format'] == '24 hour' else '%I:%M %p'
            self.text(time.strftime(fmt).lstrip('0') if fmt != '%H:%M' else time.strftime(fmt),
                      64, 22, CLOCK_SIZES[d['text_size']], 'c')
            self.text('[ %s ]' % prof, 64, 44, 8, 'c', maxw=120)
        else:
            self.text('ACTIVE PROFILE', 64, 20, 7, 'c')
            self.text(prof, 64, 29, 14, 'c', maxw=124)
        st = c['state']
        vol = 0 if st['muted'] else st['volume']
        if icons:
            self.icon('volume', 2, 54)
            self.icon('star', 66, 54)
        else:
            self.text('VOL', 2, 55, 6)
            self.text('BRT', 66, 55, 6)
        self.bar(12 if icons else 16, 56, 48 if icons else 44, 6, vol)
        self.bar(76 if icons else 80, 56, 48 if icons else 44, 6, d['brightness'])

    def page_music(self, app):
        c = app.cfg
        t = time.time()
        rh = self.title_bar(app, c['names']['menu'][1], 'PLAY' if app.playing else 'PAUSE')
        self.icon('play' if app.playing else 'pause', 4, rh + 2)
        self.text('Track 01 - Demo Mix', 16, rh + 2, 8, maxw=108)
        for i in range(14):
            if app.playing and c['display']['animations']:
                h = 2 + (math.sin(t * 6 + i * 0.9) + 1) * 7
            else:
                h = 2
            self.rect(4 + i * 8, 50 - h, 5, h)
        st = c['state']
        vol = 0 if st['muted'] else st['volume']
        self.bar(4, 54, 100, 8, vol)
        self.text('MUTE' if st['muted'] else '%d%%' % vol, 124, 54, 8, 'r', maxw=20)


class Wall(Widget):
    """Wallpaper behind the whole app (cover-fit + dark overlay)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tex = None
        self.dim = 0.55
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        if not self.tex:
            return
        w, h = self.size
        iw, ih = self.tex.size
        wr, ir = w / float(h or 1), iw / float(ih or 1)
        if ir > wr:
            fw = wr / ir
            u = (1 - fw) / 2.0
            tc = (u, 0, u + fw, 0, u + fw, 1, u, 1)
        else:
            fh = ir / wr
            v = (1 - fh) / 2.0
            tc = (0, v, 1, v, 1, v + fh, 0, v + fh)
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=self.tex, pos=self.pos, size=self.size, tex_coords=tc)
            Color(0, 0, 0, self.dim)
            Rectangle(pos=self.pos, size=self.size)


# ------------------------------------------------------------------ UI helpers
def mk_label(text, size=14, color=TXT, h=28, bold=False, halign='left'):
    lb = Label(text=text, font_size=sp(size), color=color, size_hint_y=None, height=dp(h),
               halign=halign, valign='middle', bold=bold)
    lb.bind(size=lambda i, v: setattr(i, 'text_size', v))
    return lb


class Card(GridLayout):
    def __init__(self, **kw):
        kw.setdefault('cols', 1)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('padding', dp(12))
        kw.setdefault('spacing', dp(8))
        super().__init__(**kw)
        self.bind(minimum_height=self.setter('height'))
        with self.canvas.before:
            Color(*CARD)
            self._bg = RoundedRectangle(radius=[dp(16)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class RButton(Button):
    def __init__(self, bg=FIELD, **kw):
        kw['background_normal'] = ''
        kw['background_down'] = ''
        kw['background_color'] = (0, 0, 0, 0)
        kw.setdefault('color', TXT)
        kw.setdefault('font_size', sp(14))
        kw.setdefault('halign', 'center')
        super().__init__(**kw)
        self.bg = bg
        with self.canvas.before:
            self._c = Color(*bg)
            self._r = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._upd, size=self._upd, state=self._upd)
        self.bind(size=lambda i, v: setattr(i, 'text_size', v))

    def set_bg(self, col):
        self.bg = col
        self._upd()

    def _upd(self, *_):
        self._r.pos, self._r.size = self.pos, self.size
        b = self.bg
        self._c.rgba = (tuple(min(1, x + 0.15) for x in b[:3]) + (1,)) if self.state == 'down' else b


def row(title, widget, h=48, frac=0.58):
    r = BoxLayout(size_hint_y=None, height=dp(h), spacing=dp(8))
    lb = mk_label(title, 13, DIM, h)
    lb.size_hint_x = 1 - frac
    widget.size_hint_x = frac
    r.add_widget(lb)
    r.add_widget(widget)
    return r


def text_in(d, key, cb=None, hint=''):
    t = TextInput(text=str(d[key]), multiline=False, hint_text=hint, background_color=FIELD,
                  foreground_color=TXT, cursor_color=ACC, hint_text_color=DIM,
                  padding=[dp(10), dp(14), dp(10), dp(8)], font_size=sp(14), write_tab=False)

    def on(_i, v):
        d[key] = v
        if cb:
            cb(v)
        APP().changed()
    t.bind(text=on)
    return t


def spin(d, key, values, cb=None):
    s = Spinner(text=str(d[key]), values=values, background_normal='', background_color=FIELD,
                color=TXT, font_size=sp(14))

    def on(_i, v):
        d[key] = v
        if cb:
            cb(v)
        APP().changed()
    s.bind(text=on)
    return s


def switch(d, key, cb=None):
    sw = Switch(active=bool(d[key]))

    def on(_i, v):
        d[key] = v
        if cb:
            cb(v)
        APP().changed()
    sw.bind(active=on)
    return sw


def slider_row(title, d, key, lo, hi):
    r = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
    lb = mk_label(title, 13, DIM, 48)
    lb.size_hint_x = 0.34
    val = mk_label(str(d[key]), 13, TXT, 48, halign='right')
    val.size_hint_x = 0.14
    sl = Slider(min=lo, max=hi, value=d[key], step=1)

    def on(_i, v):
        d[key] = int(v)
        val.text = str(int(v))
        APP().changed()
    sl.bind(value=on)
    for w in (lb, sl, val):
        r.add_widget(w)
    return r


# --------------------------------------------------------------------- screens
class BaseScreen(Screen):
    title_text = ''
    compact = True

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        self.add_widget(root)
        root.add_widget(mk_label(self.title_text, 20, TXT, 34, bold=True))
        if self.compact:
            a = AnchorLayout(size_hint_y=None, height=dp(125))
            self.oled = OledView(size_hint=(None, None), size=(dp(250), dp(125)))
            a.add_widget(self.oled)
            root.add_widget(a)
        else:
            self.oled = OledView(size_hint_y=None)
            self.oled.bind(width=lambda i, w: setattr(i, 'height', w / 2.0))
            root.add_widget(self.oled)
        sv = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.box = GridLayout(cols=1, size_hint_y=None, spacing=dp(10),
                              padding=[0, 0, 0, dp(10)])
        self.box.bind(minimum_height=self.box.setter('height'))
        sv.add_widget(self.box)
        root.add_widget(sv)

    def on_pre_enter(self, *_):
        self.refresh()
        APP().wake()

    def refresh(self):
        self.box.clear_widgets()
        self.build()

    def build(self):
        pass


class OledScreen(BaseScreen):
    title_text = 'MACRO PAD CONTROL CENTER'
    compact = False

    def build(self):
        app = APP()
        c = Card()
        c.add_widget(mk_label('OLED controls', 16, TXT, 28, bold=True))
        r = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(8))
        r.add_widget(RButton(text='BACK', on_release=lambda *_: app.nav_back()))
        r.add_widget(RButton(text='UP', on_release=lambda *_: app.nav_move(-1)))
        r.add_widget(RButton(text='DOWN', on_release=lambda *_: app.nav_move(1)))
        r.add_widget(RButton(text='OK', bg=ACC, on_release=lambda *_: app.nav_ok()))
        c.add_widget(r)
        tip = mk_label('Home: OK opens the menu, UP/DOWN change volume.\n'
                       'Menu: UP/DOWN move, OK opens.  Display/Settings: OK changes the '
                       'value.  Tap the OLED to wake it.', 12, DIM, 64)
        c.add_widget(tip)
        self.box.add_widget(c)
        s = Card()
        s.add_widget(mk_label('Active profile: %s' % app.profile['name'], 14, TXT, 26))
        s.add_widget(mk_label('Config file: %s' % app.path, 11, DIM, 40))
        self.box.add_widget(s)


class ButtonsScreen(BaseScreen):
    title_text = 'Buttons'
    sel = 0

    def build(self):
        app = APP()
        p = app.profile
        b = p['buttons'][self.sel]
        c = Card()
        c.add_widget(mk_label('Tap a key to select and test it', 12, DIM, 22))
        g = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(150))
        self.keys = []
        for i, bt in enumerate(p['buttons']):
            k = RButton(text=bt['name'], bg=ACC if i == self.sel else FIELD,
                        on_release=lambda w, i=i: self.pick(i))
            self.keys.append(k)
            g.add_widget(k)
        c.add_widget(g)
        self.box.add_widget(c)
        e = Card()
        e.add_widget(mk_label('Button %d settings' % (self.sel + 1), 16, TXT, 28, bold=True))
        e.add_widget(row('Name', text_in(b, 'name', lambda v: setattr(self.keys[self.sel],
                                                                        'text', v))))
        e.add_widget(row('Function', spin(b, 'function', FUNCTIONS)))
        e.add_widget(row('Shortcut', spin(b, 'shortcut', SHORTCUTS)))
        e.add_widget(row('Custom keys / text', text_in(b, 'custom', hint='optional')))
        e.add_widget(row('App / action', spin(b, 'app', APPS_ACTIONS)))
        e.add_widget(row('OLED icon', spin(b, 'icon', list(ICONS))))
        e.add_widget(row('Enabled', switch(b, 'enabled')))
        self.box.add_widget(e)

    def pick(self, i):
        self.sel = i
        APP().press_button(i)
        self.refresh()


class EncodersScreen(BaseScreen):
    title_text = 'Rotary Encoders'

    def build(self):
        app = APP()
        for i, e in enumerate(app.profile['encoders']):
            c = Card()
            c.add_widget(mk_label('Encoder %d' % (i + 1), 16, TXT, 28, bold=True))
            c.add_widget(row('Name', text_in(e, 'name')))
            cw = spin(e, 'cw', ENC_ACTIONS)
            ccw = spin(e, 'ccw', ENC_ACTIONS)
            pr = spin(e, 'press', ENC_ACTIONS)

            def on_fn(v, cw=cw, ccw=ccw, pr=pr):
                cw.text, ccw.text, pr.text = ENC_DEFAULTS[v]
            c.add_widget(row('Function', spin(e, 'function', ENC_FUNCS, on_fn)))
            c.add_widget(row('Clockwise', cw))
            c.add_widget(row('Counter-clockwise', ccw))
            c.add_widget(row('Press', pr))
            c.add_widget(row('Enabled', switch(e, 'enabled')))
            t = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            for label, kind in (('CCW', 'ccw'), ('PRESS', 'press'), ('CW', 'cw')):
                t.add_widget(RButton(text=label, on_release=lambda w, i=i, k=kind:
                                     APP().encoder_event(i, k)))
            c.add_widget(t)
            self.box.add_widget(c)


class ProfilesScreen(BaseScreen):
    title_text = 'Profiles'
    new_name = 'New profile'

    def build(self):
        app = APP()
        c = Card()
        c.add_widget(mk_label('Create profile (copies the active one)', 13, DIM, 24))
        r = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        ti = TextInput(text=self.new_name, multiline=False, background_color=FIELD,
                       foreground_color=TXT, cursor_color=ACC, font_size=sp(14),
                       padding=[dp(10), dp(14), dp(10), dp(8)])
        ti.bind(text=lambda i, v: setattr(self, 'new_name', v))
        r.add_widget(ti)
        r.add_widget(RButton(text='+ Add', bg=ACC, size_hint_x=0.3,
                             on_release=lambda *_: self.add(ti.text)))
        c.add_widget(r)
        self.box.add_widget(c)
        for i, pr in enumerate(app.cfg['profiles']):
            active = i == app.cfg['active_profile']
            c = Card()
            r = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            n = text_in(pr, 'name')
            n.size_hint_x = 0.5
            r.add_widget(n)
            r.add_widget(RButton(text='Active' if active else 'Use', size_hint_x=0.25,
                                 bg=ACC if active else FIELD,
                                 on_release=lambda w, i=i: self.use(i)))
            r.add_widget(RButton(text='Del', size_hint_x=0.25, bg=(0.45, 0.12, 0.14, 1),
                                 on_release=lambda w, i=i: self.delete(i)))
            c.add_widget(r)
            self.box.add_widget(c)

    def add(self, name):
        app = APP()
        p = copy.deepcopy(app.profile)
        p['name'] = name.strip() or 'Profile %d' % (len(app.cfg['profiles']) + 1)
        app.cfg['profiles'].append(p)
        app.cfg['active_profile'] = len(app.cfg['profiles']) - 1
        app.changed()
        self.refresh()

    def use(self, i):
        APP().set_profile(i)
        self.refresh()

    def delete(self, i):
        app = APP()
        if len(app.cfg['profiles']) <= 1:
            app.flash('PROFILES', 'Keep at least 1')
            return
        del app.cfg['profiles'][i]
        a = app.cfg['active_profile']
        if a >= i and a > 0:
            app.cfg['active_profile'] = a - 1
        app.changed()
        self.refresh()


class SettingsScreen(BaseScreen):
    title_text = 'Settings'
    reset_armed = False

    def build(self):
        app = APP()
        c = app.cfg
        # --- display
        card = Card()
        card.add_widget(mk_label('Display', 16, TXT, 28, bold=True))
        for key, label, kind, opt in DISPLAY_ITEMS:
            d = c['display']
            if kind == 'slider':
                card.add_widget(slider_row(label, d, key, *opt))
            elif kind == 'bool':
                card.add_widget(row(label, switch(d, key)))
            else:
                card.add_widget(row(label, spin(d, key, opt)))
        self.box.add_widget(card)
        # --- names
        card = Card()
        card.add_widget(mk_label('Names', 16, TXT, 28, bold=True))
        card.add_widget(row('Device name', text_in(c['names'], 'device')))
        card.add_widget(row('OLED title', text_in(c['names'], 'title')))
        card.add_widget(mk_label('Menu names', 13, ACC, 24))
        for i in range(6):
            card.add_widget(row('Menu %d' % (i + 1), text_in(c['names']['menu'], i)))
        card.add_widget(mk_label('Profile names', 13, ACC, 24))
        for i, p in enumerate(c['profiles']):
            card.add_widget(row('Profile %d' % (i + 1), text_in(p, 'name')))
        card.add_widget(mk_label('Shortcut names (active profile)', 13, ACC, 24))
        for i, b in enumerate(app.profile['buttons']):
            card.add_widget(row('Button %d' % (i + 1), text_in(b, 'name')))
        card.add_widget(mk_label('Encoder names (active profile)', 13, ACC, 24))
        for i, e in enumerate(app.profile['encoders']):
            card.add_widget(row('Encoder %d' % (i + 1), text_in(e, 'name')))
        self.box.add_widget(card)
        # --- wallpaper
        card = Card()
        card.add_widget(mk_label('Wallpaper', 16, TXT, 28, bold=True))
        card.add_widget(row('Image path', text_in(c['app'], 'wallpaper', hint='/storage/emulated/0/...'), 52, 0.65))
        g = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(48))
        g.add_widget(RButton(text='Browse...', bg=ACC, on_release=lambda *_: self.browse()))
        g.add_widget(RButton(text='Remove', on_release=lambda *_: self.clear_wall()))
        card.add_widget(g)
        card.add_widget(slider_row('Darkness %', c['app'], 'wallpaper_dim', 0, 90))
        self.box.add_widget(card)
        # --- computer / spotify
        card = Card()
        card.add_widget(mk_label('Computer + Spotify', 16, TXT, 28, bold=True))
        card.add_widget(mk_label('Run pc_server.py on the computer (same Wi-Fi).', 12, DIM, 22))
        card.add_widget(row('Enable', switch(c['pc'], 'enabled')))
        card.add_widget(row('Computer IP', text_in(c['pc'], 'host')))
        card.add_widget(row('Port', text_in(c['pc'], 'port')))
        card.add_widget(row('Password', text_in(c['pc'], 'token')))
        card.add_widget(RButton(text='Test connection', bg=ACC, size_hint_y=None, height=dp(48),
                                on_release=lambda *_: self.test_pc()))
        self.pc_lbl = mk_label(app.pc_status or 'Not tested yet.', 12, DIM, 36)
        card.add_widget(self.pc_lbl)
        self.box.add_widget(card)
        # --- data
        card = Card()
        card.add_widget(mk_label('Save / Backup', 16, TXT, 28, bold=True))
        card.add_widget(row('Export / import path', text_in(c['app'], 'export_path'), 52, 0.6))
        g = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(112))
        g.add_widget(RButton(text='Save', bg=ACC, on_release=lambda *_: self.do_save()))
        self.reset_btn = RButton(text='Reset to default', bg=(0.45, 0.12, 0.14, 1),
                                 on_release=lambda *_: self.do_reset())
        g.add_widget(self.reset_btn)
        g.add_widget(RButton(text='Export', on_release=lambda *_: self.do_export()))
        g.add_widget(RButton(text='Import', on_release=lambda *_: self.do_import()))
        card.add_widget(g)
        self.status = mk_label('Auto-saves on every change.', 12, DIM, 40)
        card.add_widget(self.status)
        self.box.add_widget(card)

    def browse(self):
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup
        start = '/storage/emulated/0'
        if not os.path.isdir(start):
            start = os.path.expanduser('~')
        fc = FileChooserListView(path=start, filters=['*.png', '*.jpg', '*.jpeg'])
        box = BoxLayout(orientation='vertical', spacing=dp(6))
        box.add_widget(fc)
        pop = Popup(title='Choose wallpaper', content=box, size_hint=(0.95, 0.9))

        def ok(*_):
            if fc.selection:
                APP().cfg['app']['wallpaper'] = fc.selection[0]
                APP().changed()
                pop.dismiss()
                self.refresh()
        box.add_widget(RButton(text='Use this image', bg=ACC, size_hint_y=None, height=dp(52),
                               on_release=ok))
        pop.open()

    def clear_wall(self):
        APP().cfg['app']['wallpaper'] = ''
        APP().changed()
        self.refresh()

    def test_pc(self):
        app = APP()
        if not app.cfg['pc']['enabled']:
            self.pc_lbl.text = 'Turn on Enable first.'
            return
        app.pc_status = 'Connecting...'
        self.pc_lbl.text = app.pc_status
        app.pc_send('ping')
        Clock.schedule_once(lambda _dt: setattr(self.pc_lbl, 'text', app.pc_status), 2)

    def say(self, msg):
        self.status.text = msg

    def do_save(self):
        ok = APP().save()
        self.say('Saved: %s' % APP().path if ok else 'Save failed: %s' % APP().save_error)

    def do_reset(self):
        if not self.reset_armed:
            self.reset_armed = True
            self.reset_btn.text = 'Tap again to confirm'
            Clock.schedule_once(self._disarm, 3)
            return
        app = APP()
        path = app.cfg['app']['export_path']
        app.cfg = default_config()
        app.cfg['app']['export_path'] = path
        app.nav = {'mode': 'home', 'idx': 0, 'sub': 0}
        app.save()
        self._disarm()
        self.refresh()
        self.say('Defaults restored.')

    def _disarm(self, *_):
        self.reset_armed = False
        if hasattr(self, 'reset_btn'):
            self.reset_btn.text = 'Reset to default'

    def do_export(self):
        app = APP()
        path = app.cfg['app']['export_path']
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(app.cfg, f, indent=2)
            self.say('Exported to %s' % path)
        except Exception as exc:
            self.say('Export failed: %s\nTry another path.' % exc)

    def do_import(self):
        app = APP()
        path = app.cfg['app']['export_path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                new = sanitize(json.load(f))
            new['app']['export_path'] = path
            app.cfg = new
            app.save()
            self.refresh()
            self.say('Imported from %s' % path)
        except Exception as exc:
            self.say('Import failed: %s' % exc)


# ------------------------------------------------------------------------ app
class MacroPadApp(App):
    title = 'Macro Pad Control Center'

    # --- lifecycle
    def build(self):
        Window.clearcolor = BG
        if platform not in ('android', 'ios'):
            Window.size = (400, 780)  # phone-shaped window only when testing off-device
        try:
            Window.softinput_mode = 'below_target'
        except Exception:
            pass
        self.path = os.path.join(self.user_data_dir, 'macropad_config.json')
        self.save_error = ''
        self.cfg = self.load()
        self.nav = {'mode': 'home', 'idx': 0, 'sub': 0}
        self.playing = True
        self.last_act = time.time()
        self.flash_until = 0
        self.flash_text = ('', '')
        self._save_ev = None

        self.pc_status = ''
        self._wall_path = None
        root = FloatLayout()
        self.wall = Wall()
        root.add_widget(self.wall)
        col = BoxLayout(orientation='vertical')
        root.add_widget(col)
        self.sm = ScreenManager(transition=SlideTransition(duration=0.2))
        self.tabs = [('oled', 'OLED', OledScreen), ('buttons', 'Buttons', ButtonsScreen),
                     ('encoders', 'Encoders', EncodersScreen),
                     ('profiles', 'Profiles', ProfilesScreen),
                     ('settings', 'Settings', SettingsScreen)]
        for name, _l, cls in self.tabs:
            self.sm.add_widget(cls(name=name))
        col.add_widget(self.sm)
        bar = BoxLayout(size_hint_y=None, height=dp(58), padding=dp(6), spacing=dp(6))
        self.tab_btns = {}
        for name, label, _c in self.tabs:
            b = RButton(text=label, font_size=sp(12),
                        on_release=lambda w, n=name: self.goto(n))
            self.tab_btns[name] = b
            bar.add_widget(b)
        col.add_widget(bar)
        self.apply_wallpaper()
        self.goto('oled')
        Window.bind(on_keyboard=self.on_key)
        Clock.schedule_interval(self.tick, 0.1)
        return root

    def on_pause(self):
        self.save()
        return True

    def on_stop(self):
        self.save()

    def on_key(self, _w, key, *_a):
        if key == 27:  # Android back button
            if self.sm.current != 'oled':
                self.goto('oled')
                return True
            if self.nav['mode'] != 'home':
                self.nav_back()
                return True
        return False

    def goto(self, name):
        names = [t[0] for t in self.tabs]
        cur = self.sm.current if self.sm.current in names else name
        self.sm.transition.direction = 'left' if names.index(name) >= names.index(cur) else 'right'
        self.sm.current = name
        for n, b in self.tab_btns.items():
            b.set_bg(ACC if n == name else FIELD)

    def tick(self, _dt):
        for v in VIEWS:
            if v.get_root_window():
                v.redraw()

    # --- storage
    def load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return sanitize(json.load(f))
        except Exception:
            return sanitize({})

    def save(self):
        try:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, indent=2)
            os.replace(tmp, self.path)
            self.save_error = ''
            return True
        except Exception as exc:
            self.save_error = str(exc)
            return False

    def apply_wallpaper(self):
        a = self.cfg['app']
        p = a.get('wallpaper', '')
        if p != self._wall_path:
            self._wall_path = p
            tex = None
            if p and os.path.isfile(p):
                try:
                    tex = CoreImage(p).texture
                except Exception:
                    tex = None
            self.wall.tex = tex
        self.wall.dim = a.get('wallpaper_dim', 55) / 100.0
        self.wall.draw()

    def pc_send(self, cmd, **kw):
        pc = self.cfg['pc']
        if not pc['enabled']:
            return

        def work():
            try:
                body = json.dumps(dict(kw, cmd=cmd, token=pc['token'])).encode()
                req = urllib.request.Request('http://%s:%s/' % (pc['host'], pc['port']),
                                             data=body, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=3) as r:
                    self.pc_status = 'PC: ' + r.read().decode()[:60]
            except Exception as exc:
                self.pc_status = 'PC error: %s' % exc
        threading.Thread(target=work, daemon=True).start()

    def changed(self):
        if hasattr(self, 'wall'):
            self.apply_wallpaper()
        self.wake()
        if self._save_ev:
            self._save_ev.cancel()
        self._save_ev = Clock.schedule_once(lambda _dt: self.save(), 0.6)

    # --- state helpers
    @property
    def profile(self):
        return self.cfg['profiles'][self.cfg['active_profile']]

    def wake(self):
        self.last_act = time.time()

    def asleep(self):
        secs = TIMEOUT_SECS.get(self.cfg['display']['timeout'], 0)
        now = time.time()
        return secs > 0 and now - self.last_act > secs and now > self.flash_until

    def flash(self, l1, l2='', secs=1.6):
        self.flash_text = (str(l1), str(l2))
        self.flash_until = time.time() + secs
        self.wake()

    def set_profile(self, i):
        self.cfg['active_profile'] = i
        self.changed()
        self.flash('PROFILE', self.profile['name'])

    # --- actions
    def run_action(self, act):
        st, d = self.cfg['state'], self.cfg['display']
        if act in ACTION_PC:
            self.pc_send(ACTION_PC[act][0], **ACTION_PC[act][1])
        elif act in APP_NAMES:
            self.pc_send('open', name=act)
        if act in ('Volume Up', 'Volume Down'):
            st['volume'] = max(0, min(100, st['volume'] + (5 if act == 'Volume Up' else -5)))
            st['muted'] = False
            msg = 'Volume %d%%' % st['volume']
        elif act in ('Brightness Up', 'Brightness Down'):
            d['brightness'] = max(5, min(100, d['brightness'] + (5 if 'Up' in act else -5)))
            msg = 'Brightness %d%%' % d['brightness']
        elif act == 'Mute':
            st['muted'] = not st['muted']
            msg = 'Muted' if st['muted'] else 'Unmuted'
        elif act == 'Play/Pause':
            self.playing = not self.playing
            msg = 'Playing' if self.playing else 'Paused'
        elif act in ('Next Profile', 'Previous Profile'):
            n = len(self.cfg['profiles'])
            self.cfg['active_profile'] = (self.cfg['active_profile'] + (1 if 'Next' in act else -1)) % n
            msg = self.profile['name']
        else:
            msg = act
        self.changed()
        return msg

    def press_button(self, i):
        b = self.profile['buttons'][i]
        if not b['enabled']:
            self.flash(b['name'], 'DISABLED')
            return
        f = b['function']
        if f == 'Keyboard Shortcut':
            detail = b['custom'] or b['shortcut']
            self.pc_send('key', combo=detail)
        elif f == 'Launch App':
            detail = 'Open ' + b['app']
            self.pc_send('open', name=b['app'])
        elif f == 'Text Macro':
            detail = 'Type: ' + (b['custom'] or '...')
            self.pc_send('type', text=b['custom'])
        elif f in ('Action', 'Media'):
            detail = self.run_action(b['app'])
        else:
            detail = 'No action'
        self.flash(b['name'], detail)

    def encoder_event(self, i, kind):
        e = self.profile['encoders'][i]
        if not e['enabled']:
            self.flash(e['name'], 'DISABLED')
            return
        msg = self.run_action(e[kind])
        self.flash(e['name'], '%s: %s' % (kind.upper(), msg))

    # --- OLED navigation
    def disp_val(self, key, kind):
        v = self.cfg['display'][key]
        if kind == 'bool':
            return 'ON' if v else 'OFF'
        if kind == 'slider':
            return '%d%%' % v
        return v

    def list_page(self, mode):
        c, p, n = self.cfg, self.profile, self.nav
        if mode == 'menu':
            return c['names']['device'], [(None, m, '') for m in c['names']['menu']], n['idx']
        title = c['names']['menu'][MENU_KEYS.index(mode)]
        if mode == 'shortcuts':
            rows = [(b['icon'], b['name'], '' if b['enabled'] else 'OFF') for b in p['buttons']]
        elif mode == 'profiles':
            rows = [('star' if i == c['active_profile'] else None, pr['name'], '')
                    for i, pr in enumerate(c['profiles'])]
        elif mode == 'display':
            rows = [(None, lab, self.disp_val(k, kind)) for k, lab, kind, _o in DISPLAY_ITEMS]
        else:  # settings
            rows = [(None, 'Device', c['names']['device']), (None, 'Title', c['names']['title']),
                    (None, 'Profile', p['name'])]
            rows += [(None, e['name'], e['function']) for e in p['encoders']]
            rows += [('volume', 'Volume', '%d%%' % c['state']['volume']), ('bolt', 'Save config', '')]
        return title, rows, min(n['sub'], len(rows) - 1)

    def nav_move(self, delta):
        self.wake()
        n, m = self.nav, self.nav['mode']
        if m in ('home', 'music'):
            self.run_action('Volume Up' if delta < 0 else 'Volume Down')
        elif m == 'menu':
            n['idx'] = (n['idx'] + delta) % 6
        else:
            n['sub'] = (n['sub'] + delta) % len(self.list_page(m)[1])

    def nav_back(self):
        self.wake()
        n = self.nav
        n['mode'] = 'home' if n['mode'] in ('home', 'menu') else 'menu'

    def nav_ok(self):
        self.wake()
        n, m, c = self.nav, self.nav['mode'], self.cfg
        if m == 'home':
            n['mode'] = 'menu'
        elif m == 'menu':
            key = MENU_KEYS[n['idx']]
            n['mode'] = key
            n['sub'] = c['active_profile'] if key == 'profiles' else 0
        elif m == 'music':
            self.run_action('Play/Pause')
        elif m == 'shortcuts':
            self.press_button(n['sub'])
        elif m == 'profiles':
            self.set_profile(n['sub'])
        elif m == 'display':
            self.cycle_display(n['sub'])
        elif m == 'settings':
            s, st = n['sub'], c['state']
            if s == 2:
                self.set_profile((c['active_profile'] + 1) % len(c['profiles']))
            elif 3 <= s <= 5:
                e = self.profile['encoders'][s - 3]
                self.flash(e['name'], e['function'])
            elif s == 6:
                st['volume'] = 0 if st['volume'] >= 100 else min(100, (st['volume'] // 10 + 1) * 10)
                self.changed()
            elif s == 7:
                self.save()
                self.flash('SAVED', 'config.json')
            else:
                self.flash(c['names']['device' if s == 0 else 'title'], 'edit in phone app')

    def cycle_display(self, i):
        key, _lab, kind, opt = DISPLAY_ITEMS[i]
        d = self.cfg['display']
        if kind == 'bool':
            d[key] = not d[key]
        elif kind == 'slider':
            d[key] = 10 if d[key] >= opt[1] else min(opt[1], (d[key] // 10 + 1) * 10)
        else:
            d[key] = opt[(opt.index(d[key]) + 1) % len(opt)]
        self.changed()


if __name__ == '__main__':
    MacroPadApp().run()
