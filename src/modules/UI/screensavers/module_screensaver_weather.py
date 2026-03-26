"""
Weather Screensaver — TARS display
Atmospheric Recon HUD aesthetic.
Fetches location via IP geolocation, weather via Open-Meteo (no API key needed).
Data refreshes in a background thread so the render loop never blocks.
"""
import pygame
import threading
import time
import math
import random
import urllib.request
import json
from pathlib import Path
from datetime import datetime, timezone

_UI_DIR   = Path(__file__).parent.parent           # UI/
_ASSETS   = Path(__file__).parent.parent / "assets" # UI/assets/

# ── WMO weather codes ──────────────────────────────────────────────────────
_WMO = {
    0:  ("CLEAR SKY",     "CLR"),
    1:  ("MAINLY CLEAR",  "CLR"),
    2:  ("PARTLY CLOUDY", "PCL"),
    3:  ("OVERCAST",      "OVC"),
    45: ("FOG",           "FOG"),
    48: ("ICING FOG",     "FOG"),
    51: ("LIGHT DRIZZLE", "DRZ"),
    53: ("DRIZZLE",       "DRZ"),
    55: ("HEAVY DRIZZLE", "DRZ"),
    61: ("LIGHT RAIN",    "RAN"),
    63: ("RAIN",          "RAN"),
    65: ("HEAVY RAIN",    "RAN"),
    71: ("LIGHT SNOW",    "SNW"),
    73: ("SNOW",          "SNW"),
    75: ("HEAVY SNOW",    "SNW"),
    77: ("SNOW GRAINS",   "SNW"),
    80: ("RAIN SHOWERS",  "SHW"),
    81: ("SHOWERS",       "SHW"),
    82: ("HEAVY SHOWERS", "SHW"),
    85: ("SNOW SHOWERS",  "SNW"),
    86: ("HEAVY SNOW SHW","SNW"),
    95: ("THUNDERSTORM",  "TST"),
    96: ("T-STORM/HAIL",  "TST"),
    99: ("T-STORM/HAIL",  "TST"),
}

# Condition color palettes — (primary, glow, dim)
_PALETTE = {
    "CLR": ((255, 200,  50), (255, 140,  0),  (80, 55,  5)),
    "PCL": ((160, 210, 255), (80,  160, 220), (20, 40, 70)),
    "OVC": ((120, 140, 165), (70,  90,  110), (20, 28, 38)),
    "FOG": ((160, 180, 180), (80,  100, 100), (18, 25, 25)),
    "DRZ": ((80,  200, 230), (40,  140, 180), (10, 35, 50)),
    "RAN": ((60,  150, 255), (30,  90,  200), ( 8, 22, 55)),
    "SNW": ((210, 230, 255), (140, 175, 220), (25, 35, 55)),
    "SHW": ((80,  180, 255), (40,  110, 200), (10, 28, 55)),
    "TST": ((210,  60, 255), (140,  20, 180), (35,  5, 55)),
}

_WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "TARS/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ── Particle systems ───────────────────────────────────────────────────────

class _RainParticle:
    __slots__ = ('x', 'y', 'speed', 'length', 'alpha')
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(-h, 0)
        self.speed = random.uniform(8, 18)
        self.length = random.randint(8, 22)
        self.alpha = random.randint(60, 140)

class _SnowParticle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'r', 'alpha', 'phase')
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(-h, 0)
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(0.8, 2.2)
        self.r  = random.uniform(1.0, 3.5)
        self.alpha = random.randint(80, 200)
        self.phase = random.uniform(0, math.tau)

class _SparkParticle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'r')
    def __init__(self, w, h):
        self.x = random.uniform(w * 0.2, w * 0.8)
        self.y = random.uniform(h * 0.1, h * 0.5)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-3.0, -0.5)
        self.max_life = random.uniform(30, 80)
        self.life = self.max_life
        self.r = random.uniform(1.0, 2.5)


# ── Main screensaver ───────────────────────────────────────────────────────

class WeatherAnimation:
    def __init__(self, screen, width, height, show_time=False):
        self.screen = screen
        self.width  = width
        self.height = height
        self.cx     = width // 2

        # Fonts
        try:
            self.f_temp   = pygame.font.Font(str(_ASSETS / "astrolab.ttf"), 72)
            self.f_unit   = pygame.font.Font(str(_ASSETS / "astrolab.ttf"), 32)
            self.f_city   = pygame.font.Font(str(_ASSETS / "astrolab.ttf"), 28)
        except Exception:
            self.f_temp   = pygame.font.SysFont("monospace", 72, bold=True)
            self.f_unit   = pygame.font.SysFont("monospace", 32)
            self.f_city   = pygame.font.SysFont("monospace", 28)

        try:
            self.f_label  = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 13)
            self.f_value  = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 16)
            self.f_cond   = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 14)
            self.f_day    = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 13)
        except Exception:
            self.f_label  = pygame.font.SysFont("monospace", 13)
            self.f_value  = pygame.font.SysFont("monospace", 16)
            self.f_cond   = pygame.font.SysFont("monospace", 14)
            self.f_day    = pygame.font.SysFont("monospace", 13)

        try:
            self.f_coord  = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 14)
            self.f_meta   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 13)
        except Exception:
            self.f_coord  = pygame.font.SysFont("monospace", 14)
            self.f_meta   = pygame.font.SysFont("monospace", 13)

        # State
        self._data    = None
        self._error   = None
        self._loading = True
        self._last_fetch   = 0
        self._fetch_interval = 600
        self._lock    = threading.Lock()

        # Animation
        self._t       = 0.0
        self._ring_angle = 0.0
        self._particles  = []
        self._bg_surface = None  # cached static bg

        self._kick_fetch()

    def reset(self):
        pass  # fetch already started in __init__

    def _kick_fetch(self):
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _fetch_weather(self):
        try:
            geo = _fetch_json("http://ip-api.com/json/?fields=city,country,lat,lon,status")
            if geo.get("status") != "success":
                raise RuntimeError("geolocation failed")

            lat, lon = geo["lat"], geo["lon"]

            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
                f"weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
                f"&timezone=auto&forecast_days=4"
            )
            w   = _fetch_json(url)
            cur = w["current"]
            daily = w["daily"]

            code  = cur["weather_code"]
            short = _WMO.get(code, ("UNKNOWN", "??"))[1]

            forecast = []
            for i in range(1, min(4, len(daily["time"]))):
                dc    = daily["weather_code"][i]
                ds    = _WMO.get(dc, ("??", "??"))[1]
                dt_obj = datetime.fromisoformat(daily["time"][i])
                forecast.append({
                    "day":   _WEEKDAYS[dt_obj.weekday()],
                    "hi":    round(daily["temperature_2m_max"][i]),
                    "lo":    round(daily["temperature_2m_min"][i]),
                    "short": ds,
                    "label": _WMO.get(dc, ("??", "??"))[0],
                })

            data = {
                "city":     geo["city"],
                "country":  geo["country"],
                "lat":      lat,
                "lon":      lon,
                "temp":     round(cur["temperature_2m"]),
                "feels":    round(cur["apparent_temperature"]),
                "humidity": cur["relative_humidity_2m"],
                "wind":     round(cur["wind_speed_10m"]),
                "code":     code,
                "short":    short,
                "label":    _WMO.get(code, ("UNKNOWN", "??"))[0],
                "forecast": forecast,
                "updated":  datetime.now(timezone.utc).strftime("%H:%M"),
            }

            with self._lock:
                self._data       = data
                self._error      = None
                self._loading    = False
                self._last_fetch = time.time()
                self._bg_surface = None  # invalidate cached bg

        except Exception as e:
            with self._lock:
                self._error   = str(e)[:44]
                self._loading = False

    # ── Update ────────────────────────────────────────────────────────────

    def update(self):
        self._t          += 0.016
        self._ring_angle  = (self._ring_angle + 0.4) % 360

        with self._lock:
            short   = self._data["short"] if self._data else "CLR"
            loading = self._loading
            since   = time.time() - self._last_fetch

        if not loading and since >= self._fetch_interval:
            with self._lock:
                self._loading = True
            self._kick_fetch()

        self._update_particles(short)

    def _update_particles(self, short):
        W, H = self.width, self.height
        target = 0

        if short in ("RAN", "SHW", "DRZ"):
            target = 60
            if len(self._particles) < target:
                self._particles.append(_RainParticle(W, H))
            for p in self._particles[:]:
                p.y += p.speed
                p.x += p.speed * 0.18
                if p.y > H + 30:
                    self._particles.remove(p)

        elif short in ("SNW",):
            target = 55
            if len(self._particles) < target:
                self._particles.append(_SnowParticle(W, H))
            for p in self._particles[:]:
                p.phase += 0.03
                p.x += p.vx + math.sin(p.phase) * 0.4
                p.y += p.vy
                if p.y > H + 10:
                    self._particles.remove(p)

        elif short in ("TST",):
            target = 18
            if len(self._particles) < target:
                self._particles.append(_SparkParticle(W, H))
            for p in self._particles[:]:
                p.x   += p.vx
                p.y   += p.vy
                p.vy  += 0.12
                p.life -= 1
                if p.life <= 0 or p.y > H:
                    self._particles.remove(p)

        else:
            # Clear / other: slowly drain
            if len(self._particles) > 0:
                self._particles.pop()

    # ── Render ────────────────────────────────────────────────────────────

    def render(self):
        with self._lock:
            data    = self._data
            error   = self._error
            loading = self._loading

        short   = data["short"] if data else "CLR"
        palette = _PALETTE.get(short, _PALETTE["CLR"])
        pri, glow, bg_tint = palette

        # Background
        self.screen.fill((4, 8, 16))
        self._draw_bg_atmosphere(bg_tint)

        if loading and data is None:
            self._draw_loading(pri)
            return
        if error and data is None:
            self._draw_error(error)
            return

        self._draw_particles(short, pri)
        self._draw_top_chrome(data, pri)
        self._draw_temp_ring(data, pri, glow)
        self._draw_condition_badge(data, pri)
        self._draw_stats(data, pri)
        self._draw_forecast(data)
        self._draw_footer(data)

    # ── Drawing primitives ────────────────────────────────────────────────

    def _draw_bg_atmosphere(self, bg_tint):
        """Soft radial atmosphere glow at top."""
        r, g, b = bg_tint
        for radius in range(260, 0, -20):
            alpha = max(0, int(22 * (1 - radius / 260)))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (radius, radius), radius)
            self.screen.blit(s, (self.cx - radius, 120 - radius))

    def _draw_particles(self, short, pri):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        r, g, b = pri

        if short in ("RAN", "SHW", "DRZ"):
            for p in self._particles:
                alpha = min(255, p.alpha)
                ex = p.x + p.length * 0.18
                ey = p.y + p.length
                pygame.draw.line(surf, (r, g, b, alpha),
                                 (int(p.x), int(p.y)), (int(ex), int(ey)), 1)

        elif short == "SNW":
            for p in self._particles:
                pygame.draw.circle(surf, (r, g, b, p.alpha),
                                   (int(p.x), int(p.y)), max(1, int(p.r)))

        elif short == "TST":
            for p in self._particles:
                fade = int(255 * (p.life / p.max_life))
                pygame.draw.circle(surf, (r, g, b, fade),
                                   (int(p.x), int(p.y)), max(1, int(p.r)))

        self.screen.blit(surf, (0, 0))

    def _draw_top_chrome(self, data, pri):
        W = self.width
        r, g, b = pri
        dim = (r // 6, g // 6, b // 6)
        dim2 = (r // 3, g // 3, b // 3)

        # Horizontal top line
        pygame.draw.line(self.screen, dim2, (16, 32), (W - 16, 32), 1)

        # Corner brackets — top left (above text row)
        pygame.draw.line(self.screen, pri, (8, 6), (28, 6), 2)
        pygame.draw.line(self.screen, pri, (8, 6), (8, 20), 2)
        # top right
        pygame.draw.line(self.screen, pri, (W - 28, 6), (W - 8, 6), 2)
        pygame.draw.line(self.screen, pri, (W - 8, 6), (W - 8, 20), 2)

        # "ATMO RECON" label — sits between the bracket verticals
        lbl = self.f_label.render("ATMO  RECON", True, dim2)
        self.screen.blit(lbl, (32, 10))

        # Update time (top right) — inset from right bracket
        upd = self.f_label.render(f"UPD {data['updated']} UTC", True, dim2)
        self.screen.blit(upd, (W - upd.get_width() - 32, 10))

        # City name
        city_s = self.f_city.render(data["city"].upper(), True, (210, 225, 235))
        self.screen.blit(city_s, city_s.get_rect(centerx=self.cx, top=40))

        # Coordinates
        lat_str = f"{data['lat']:.2f}{'N' if data['lat'] >= 0 else 'S'}  "
        lon_str = f"{abs(data['lon']):.2f}{'E' if data['lon'] >= 0 else 'W'}"
        coord_s = self.f_coord.render(lat_str + lon_str, True, dim2)
        self.screen.blit(coord_s, coord_s.get_rect(centerx=self.cx, top=82))

        # Separator
        pygame.draw.line(self.screen, dim, (40, 102), (W - 40, 102), 1)

    def _draw_temp_ring(self, data, pri, glow):
        """Spinning segmented ring + giant temperature in center."""
        CX, CY = self.cx, 220
        R_OUTER = 130
        R_INNER = 100
        r, g, b   = pri
        gr, gg, gb = glow

        # Outer ambient glow ring
        for dr in range(16, 0, -2):
            alpha = int(18 * (1 - dr / 16))
            s = pygame.Surface(((R_OUTER + dr) * 2, (R_OUTER + dr) * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha),
                               (R_OUTER + dr, R_OUTER + dr), R_OUTER + dr, 1)
            self.screen.blit(s, (CX - R_OUTER - dr, CY - R_OUTER - dr))

        # Dim base ring
        s = pygame.Surface((R_OUTER * 2 + 4, R_OUTER * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (r // 8, g // 8, b // 8, 80),
                           (R_OUTER + 2, R_OUTER + 2), R_OUTER, 1)
        self.screen.blit(s, (CX - R_OUTER - 2, CY - R_OUTER - 2))

        # Spinning arc segments
        n_segs  = 24
        gap_deg = 6
        seg_deg = (360 / n_segs) - gap_deg
        offset  = self._ring_angle

        for i in range(n_segs):
            start_deg = offset + i * (360 / n_segs)
            brightness = 0.25 + 0.75 * (i / n_segs)  # trail fade
            alpha = int(200 * brightness)
            sr = int(r * brightness)
            sg = int(g * brightness)
            sb = int(b * brightness)
            seg_surf_size = (R_OUTER + 4) * 2
            ss = pygame.Surface((seg_surf_size, seg_surf_size), pygame.SRCALPHA)
            pygame.draw.arc(
                ss, (sr, sg, sb, alpha),
                pygame.Rect(2, 2, R_OUTER * 2, R_OUTER * 2),
                math.radians(start_deg),
                math.radians(start_deg + seg_deg),
                2,
            )
            self.screen.blit(ss, (CX - R_OUTER - 2, CY - R_OUTER - 2))

        # Slower counter-rotating inner ring (dashes)
        n_inner = 12
        i_offset = -self._ring_angle * 0.4
        for i in range(n_inner):
            start_deg = i_offset + i * (360 / n_inner)
            ss = pygame.Surface((R_INNER * 2 + 4, R_INNER * 2 + 4), pygame.SRCALPHA)
            pygame.draw.arc(
                ss, (gr, gg, gb, 70),
                pygame.Rect(2, 2, R_INNER * 2, R_INNER * 2),
                math.radians(start_deg),
                math.radians(start_deg + 10),
                1,
            )
            self.screen.blit(ss, (CX - R_INNER - 2, CY - R_INNER - 2))

        # Temperature text
        temp_val = str(data["temp"])
        temp_s = self.f_temp.render(temp_val, True, (240, 248, 255))

        # Glow behind text
        for goff in range(6, 0, -2):
            glow_s = self.f_temp.render(temp_val, True, (r, g, b))
            glow_s.set_alpha(20 * goff)
            gr_rect = glow_s.get_rect(center=(CX + goff, CY + goff))
            self.screen.blit(glow_s, gr_rect)
            gr_rect = glow_s.get_rect(center=(CX - goff, CY - goff))
            self.screen.blit(glow_s, gr_rect)

        temp_rect = temp_s.get_rect(center=(CX, CY))
        self.screen.blit(temp_s, temp_rect)

        # Degree + unit superscript
        unit_s = self.f_unit.render("°C", True, (r, g, b))
        self.screen.blit(unit_s, (temp_rect.right - 2, temp_rect.top + 10))

        # Feels-like tag below temp (inside ring)
        feels_str = f"FEELS  {data['feels']:+d}°" if data['feels'] < 0 else f"FEELS  {data['feels']}°"
        feels_s = self.f_label.render(feels_str, True, (r // 2, g // 2, b // 2))
        self.screen.blit(feels_s, feels_s.get_rect(centerx=CX, top=CY + 52))

    def _draw_condition_badge(self, data, pri):
        """Pulsing condition label below the ring."""
        CY_BADGE = 368
        r, g, b = pri
        pulse = 0.65 + 0.35 * math.sin(self._t * 2.2)

        label = data["label"].upper()

        # Background pill
        pill_w = min(self.width - 60, 280)
        pill_h = 28
        pill_x = self.cx - pill_w // 2
        pill_y = CY_BADGE - pill_h // 2
        pill_s = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pill_s.fill((r // 8, g // 8, b // 8, int(140 * pulse)))
        # top/bottom border lines
        pygame.draw.line(pill_s, (r, g, b, int(120 * pulse)),
                         (0, 0), (pill_w, 0), 1)
        pygame.draw.line(pill_s, (r, g, b, int(120 * pulse)),
                         (0, pill_h - 1), (pill_w, pill_h - 1), 1)
        self.screen.blit(pill_s, (pill_x, pill_y))

        # Condition text
        cond_s = self.f_cond.render(f"[ {label} ]", True, (r, g, b))
        cond_s.set_alpha(int(200 + 55 * pulse))
        self.screen.blit(cond_s, cond_s.get_rect(centerx=self.cx, centery=CY_BADGE))

        # Divider
        dim = (r // 6, g // 6, b // 6)
        pygame.draw.line(self.screen, dim, (16, 390), (self.width - 16, 390), 1)

    def _draw_stats(self, data, pri):
        """3-column stats: humidity / wind — below condition."""
        Y0 = 398
        r, g, b = pri
        dim = (r // 3, g // 3, b // 3)

        cols = [
            ("HUMIDITY", f"{data['humidity']}%"),
            ("WIND",     f"{data['wind']} km/h"),
            ("PRESSURE", "---"),        # placeholder; extend if needed
        ]

        col_w = self.width // 3
        for i, (key, val) in enumerate(cols):
            cx = i * col_w + col_w // 2

            # Vertical separator (except first)
            if i > 0:
                pygame.draw.line(self.screen, dim,
                                 (i * col_w, Y0 + 2), (i * col_w, Y0 + 54), 1)

            k_s = self.f_label.render(key, True, (r * 2 // 3, g * 2 // 3, b * 2 // 3))
            v_s = self.f_value.render(val, True, (r, g, b))
            self.screen.blit(k_s, k_s.get_rect(centerx=cx, top=Y0 + 4))
            self.screen.blit(v_s, v_s.get_rect(centerx=cx, top=Y0 + 20))

        # Bottom divider
        pygame.draw.line(self.screen, dim, (16, Y0 + 62), (self.width - 16, Y0 + 62), 1)

    def _draw_forecast(self, data):
        """3-day forecast rows with temperature range bars."""
        Y0   = 475
        W    = self.width
        pad  = 20
        row_h = 78

        # Section label
        lbl_s = self.f_label.render("3 - D A Y  O U T L O O K", True, (30, 55, 70))
        self.screen.blit(lbl_s, lbl_s.get_rect(centerx=self.cx, top=Y0))
        Y0 += 16

        for i, fc in enumerate(data["forecast"][:3]):
            y = Y0 + i * row_h
            short   = fc["short"]
            palette = _PALETTE.get(short, _PALETTE["CLR"])
            pri_fc, _, _ = palette
            r, g, b  = pri_fc

            # Row bg (alternating)
            if i % 2 == 0:
                bg = pygame.Surface((W - 32, row_h - 6), pygame.SRCALPHA)
                bg.fill((r // 20, g // 20, b // 20, 60))
                self.screen.blit(bg, (16, y + 2))

            # Day name
            day_s = self.f_day.render(fc["day"], True, (180, 200, 210))
            self.screen.blit(day_s, (pad + 4, y + 14))

            # Condition short
            cond_s = self.f_day.render(fc["label"][:14].upper(), True, (r // 2, g // 2, b // 2))
            self.screen.blit(cond_s, (pad + 4, y + 30))

            # Hi temperature
            hi_s = self.f_value.render(f"{fc['hi']}°", True, (r, g, b))
            self.screen.blit(hi_s, (W - 90, y + 10))

            # Lo temperature
            lo_s = self.f_label.render(f"{fc['lo']}°", True, (r // 3, g // 3, b // 3))
            self.screen.blit(lo_s, (W - 40, y + 14))

            # Temperature range bar
            bar_x  = 80
            bar_w  = W - 80 - 110
            bar_y  = y + 50
            spread = max(1, fc["hi"] - fc["lo"])
            fill   = int(bar_w * min(1.0, spread / 22.0))

            # Track line
            pygame.draw.line(self.screen, (r // 10, g // 10, b // 10),
                             (bar_x, bar_y), (bar_x + bar_w, bar_y), 2)
            # Fill glow (two passes: wide dim + narrow bright)
            if fill > 0:
                s_glow = pygame.Surface((fill, 6), pygame.SRCALPHA)
                s_glow.fill((r, g, b, 35))
                self.screen.blit(s_glow, (bar_x, bar_y - 2))
                pygame.draw.line(self.screen, (r, g, b),
                                 (bar_x, bar_y), (bar_x + fill, bar_y), 2)

        # Divider after forecast
        last_y = Y0 + 3 * row_h + 4
        pygame.draw.line(self.screen, (10, 22, 32), (16, last_y), (W - 16, last_y), 1)

    def _draw_footer(self, data):
        """Country + update meta at bottom."""
        W  = self.width
        Y0 = self.height - 82

        # Bottom corner brackets
        dim2 = (30, 55, 70)
        pygame.draw.line(self.screen, dim2, (14, self.height - 14), (34, self.height - 14), 2)
        pygame.draw.line(self.screen, dim2, (14, self.height - 28), (14, self.height - 14), 2)
        pygame.draw.line(self.screen, dim2, (W - 34, self.height - 14), (W - 14, self.height - 14), 2)
        pygame.draw.line(self.screen, dim2, (W - 14, self.height - 28), (W - 14, self.height - 14), 2)

        country_s = self.f_coord.render(data["country"].upper(), True, (50, 80, 95))
        self.screen.blit(country_s, country_s.get_rect(centerx=self.cx, top=Y0))

        meta_str = f"LAST FETCH  {data['updated']} UTC  ·  OPEN-METEO"
        meta_s = self.f_meta.render(meta_str, True, (22, 40, 52))
        self.screen.blit(meta_s, meta_s.get_rect(centerx=self.cx, top=Y0 + 20))

    # ── Loading / error states ─────────────────────────────────────────────

    def _draw_loading(self, pri=(0, 200, 220)):
        r, g, b = pri
        dots = "." * (int(self._t * 1.8) % 4)
        CX, CY = self.cx, self.height // 2

        # Spinning indicator
        for i in range(8):
            angle = math.radians(self._ring_angle + i * 45)
            ix = CX + int(30 * math.cos(angle))
            iy = CY - 60 + int(30 * math.sin(angle))
            alpha = int(255 * (i / 8))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (3, 3), 3)
            self.screen.blit(s, (ix - 3, iy - 3))

        lbl_s = self.f_cond.render(f"ACQUIRING DATA{dots}", True, (r // 3, g // 3, b // 3))
        self.screen.blit(lbl_s, lbl_s.get_rect(centerx=CX, top=CY))

    def _draw_error(self, msg):
        CX, CY = self.cx, self.height // 2
        e1 = self.f_cond.render("WEATHER LINK LOST", True, (180, 40, 40))
        e2 = self.f_label.render(msg, True, (60, 30, 30))
        self.screen.blit(e1, e1.get_rect(centerx=CX, top=CY - 14))
        self.screen.blit(e2, e2.get_rect(centerx=CX, top=CY + 10))

    def cleanup(self):
        self._particles.clear()
