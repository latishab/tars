"""
Weather App — TARS display
Fetches location via IP geolocation, weather via Open-Meteo (no API key needed).
Data refreshes in a background thread so the render loop never blocks.
"""
import pygame
import threading
import time
import math
import urllib.request
import json
from pathlib import Path
from datetime import datetime, timezone

_UI_DIR = Path(__file__).parent.parent

# ── WMO weather code descriptions ─────────────────────────────────────────
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
    96: ("T-STORM + HAIL","TST"),
    99: ("T-STORM + HAIL","TST"),
}

# Grouped condition → accent color (R, G, B)
_CODE_COLOR = {
    "CLR": (255, 200, 60),   # amber/yellow — sunny
    "PCL": (180, 220, 255),  # light blue — partly cloudy
    "OVC": (140, 160, 180),  # grey — overcast
    "FOG": (120, 140, 140),  # muted teal — fog
    "DRZ": (100, 200, 220),  # cyan drizzle
    "RAN": ( 80, 160, 255),  # blue rain
    "SNW": (220, 235, 255),  # white snow
    "SHW": (100, 180, 255),  # shower blue
    "TST": (220, 80,  255),  # purple storm
}

_WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "TARS/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class WeatherApp:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        self.bg      = (5, 15, 20)
        self.cyan    = (0, 230, 255)
        self.dim     = (0, 70, 90)
        self.muted   = (40, 80, 95)
        self.white   = (210, 225, 235)

        try:
            self.font_xl   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 80)
            self.font_lg   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 36)
            self.font_md   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 22)
            self.font_sm   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 15)
            self.font_xs   = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 12)
        except Exception:
            self.font_xl   = pygame.font.SysFont("monospace", 80)
            self.font_lg   = pygame.font.SysFont("monospace", 36)
            self.font_md   = pygame.font.SysFont("monospace", 22)
            self.font_sm   = pygame.font.SysFont("monospace", 15)
            self.font_xs   = pygame.font.SysFont("monospace", 12)

        # Weather data (written only by background thread)
        self._data = None
        self._error = None
        self._loading = True
        self._last_fetch = 0
        self._fetch_interval = 600   # refresh every 10 min
        self._lock = threading.Lock()

        # Animated scan line
        self._scan_y = 0
        self._anim_t = 0.0

    def reset(self):
        self._loading = True
        self._data = None
        self._error = None
        self._last_fetch = 0
        self._kick_fetch()

    def _kick_fetch(self):
        t = threading.Thread(target=self._fetch_weather, daemon=True)
        t.start()

    def _fetch_weather(self):
        try:
            # 1. IP geolocation
            geo = _fetch_json("http://ip-api.com/json/?fields=city,country,countryCode,lat,lon,status")
            if geo.get("status") != "success":
                raise RuntimeError("geolocation failed")

            lat  = geo["lat"]
            lon  = geo["lon"]
            city = geo["city"]
            country = geo["country"]

            # 2. Open-Meteo weather
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
                f"weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
                f"&timezone=auto&forecast_days=4"
            )
            w = _fetch_json(url)
            cur = w["current"]
            daily = w["daily"]

            code   = cur["weather_code"]
            short  = _WMO.get(code, ("UNKNOWN", "??"))[1]
            label  = _WMO.get(code, ("UNKNOWN", "??"))[0]
            color  = _CODE_COLOR.get(short, self.cyan)

            # Build 4-day forecast (skip today index 0 if we want tomorrow+)
            forecast = []
            for i in range(1, min(4, len(daily["time"]))):
                day_code  = daily["weather_code"][i]
                day_label = _WMO.get(day_code, ("??", "??"))[1]
                day_color = _CODE_COLOR.get(day_label, self.cyan)
                dt_obj    = datetime.fromisoformat(daily["time"][i])
                forecast.append({
                    "day":   _WEEKDAYS[dt_obj.weekday()],
                    "hi":    round(daily["temperature_2m_max"][i]),
                    "lo":    round(daily["temperature_2m_min"][i]),
                    "code":  day_label,
                    "color": day_color,
                })

            data = {
                "city":     city,
                "country":  country,
                "lat":      lat,
                "lon":      lon,
                "temp":     round(cur["temperature_2m"]),
                "feels":    round(cur["apparent_temperature"]),
                "humidity": cur["relative_humidity_2m"],
                "wind":     round(cur["wind_speed_10m"]),
                "code":     code,
                "label":    label,
                "color":    color,
                "forecast": forecast,
                "updated":  datetime.now(timezone.utc).strftime("%H:%M UTC"),
            }

            with self._lock:
                self._data = data
                self._error = None
                self._loading = False
                self._last_fetch = time.time()

        except Exception as e:
            with self._lock:
                self._error = str(e)[:40]
                self._loading = False

    def update(self, dt=0.016):
        self._anim_t += dt
        self._scan_y = (self._scan_y + int(dt * 60 + 0.5)) % self.height

        # Periodic refresh
        with self._lock:
            since = time.time() - self._last_fetch
            needs_fetch = (not self._loading) and (since >= self._fetch_interval)

        if needs_fetch:
            with self._lock:
                self._loading = True
            self._kick_fetch()

    def render(self):
        self.screen.fill(self.bg)
        self._draw_grid()

        with self._lock:
            data    = self._data
            error   = self._error
            loading = self._loading

        if loading and data is None:
            self._draw_loading()
        elif error and data is None:
            self._draw_error(error)
        else:
            self._draw_weather(data)

    # ── Background grid ────────────────────────────────────────────────────

    def _draw_grid(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        grid_color = (0, 60, 80, 22)
        step = 40
        for x in range(0, self.width, step):
            pygame.draw.line(surf, grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, step):
            pygame.draw.line(surf, grid_color, (0, y), (self.width, y))
        # Animated horizontal scan line
        scan_surf = pygame.Surface((self.width, 2), pygame.SRCALPHA)
        scan_surf.fill((0, 230, 255, 18))
        surf.blit(scan_surf, (0, self._scan_y))
        self.screen.blit(surf, (0, 0))

    # ── Loading state ──────────────────────────────────────────────────────

    def _draw_loading(self):
        dots = "." * (int(self._anim_t * 2) % 4)
        text = self.font_sm.render(f"ACQUIRING TELEMETRY{dots}", True, self.dim)
        r = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, r)

    def _draw_error(self, msg):
        self._blit_center("WEATHER LINK LOST", self.font_sm, (220, 60, 60), self.height // 2 - 20)
        self._blit_center(msg, self.font_xs, self.muted, self.height // 2 + 10)

    # ── Main weather layout ────────────────────────────────────────────────

    def _draw_weather(self, d):
        cx = self.width // 2
        color = d["color"]

        # ── Header bar ────────────────────────────────────
        pygame.draw.line(self.screen, self.dim, (16, 28), (self.width - 16, 28), 1)
        label_surf = self.font_xs.render("TARS WEATHER", True, self.muted)
        self.screen.blit(label_surf, (16, 14))
        upd_surf = self.font_xs.render(d["updated"], True, self.muted)
        self.screen.blit(upd_surf, (self.width - upd_surf.get_width() - 16, 14))

        # ── Location ───────────────────────────────────────
        city_surf = self.font_md.render(d["city"].upper(), True, self.white)
        self.screen.blit(city_surf, city_surf.get_rect(centerx=cx, top=38))

        country_surf = self.font_xs.render(
            f"{d['country'].upper()}  {d['lat']:.2f}N {abs(d['lon']):.2f}{'W' if d['lon'] < 0 else 'E'}",
            True, self.muted
        )
        self.screen.blit(country_surf, country_surf.get_rect(centerx=cx, top=66))

        # ── Divider ────────────────────────────────────────
        pygame.draw.line(self.screen, self.dim, (16, 90), (self.width - 16, 90), 1)

        # ── Big temperature ────────────────────────────────
        temp_str = f"{d['temp']:+d}" if d['temp'] < 0 else str(d['temp'])
        temp_surf = self.font_xl.render(temp_str, True, color)
        deg_surf  = self.font_lg.render("°C", True, tuple(max(0, c - 60) for c in color))
        temp_x = cx - (temp_surf.get_width() + deg_surf.get_width()) // 2
        self.screen.blit(temp_surf, (temp_x, 100))
        self.screen.blit(deg_surf, (temp_x + temp_surf.get_width() + 2, 118))

        # ── Condition ──────────────────────────────────────
        # Animated bracket pulse
        pulse = 0.5 + 0.5 * math.sin(self._anim_t * 2.0)
        bracket_alpha = int(80 + 100 * pulse)
        cond_surf = self.font_sm.render(f"[ {d['label']} ]", True, color)
        cond_surf.set_alpha(180 + int(40 * pulse))
        self.screen.blit(cond_surf, cond_surf.get_rect(centerx=cx, top=192))

        # ── Stats row ──────────────────────────────────────
        pygame.draw.line(self.screen, self.dim, (16, 225), (self.width - 16, 225), 1)

        stats = [
            ("FEELS", f"{d['feels']:+d}°" if d['feels'] < 0 else f"{d['feels']}°"),
            ("HUMID", f"{d['humidity']}%"),
            ("WIND",  f"{d['wind']}km/h"),
        ]
        col_w = self.width // 3
        for i, (key, val) in enumerate(stats):
            x = i * col_w + col_w // 2
            k_surf = self.font_xs.render(key, True, self.muted)
            v_surf = self.font_sm.render(val, True, self.cyan)
            self.screen.blit(k_surf, k_surf.get_rect(centerx=x, top=234))
            self.screen.blit(v_surf, v_surf.get_rect(centerx=x, top=252))

        pygame.draw.line(self.screen, self.dim, (16, 280), (self.width - 16, 280), 1)

        # ── Forecast ───────────────────────────────────────
        forecast_y = 295
        self._blit_label("3-DAY FORECAST", 295)
        forecast_y = 315

        row_h = 62
        for i, fc in enumerate(d["forecast"][:3]):
            y = forecast_y + i * row_h
            fc_color = fc["color"]

            # Row background on hover-ish alternation
            if i % 2 == 0:
                bg_s = pygame.Surface((self.width - 32, row_h - 4), pygame.SRCALPHA)
                bg_s.fill((0, 40, 55, 40))
                self.screen.blit(bg_s, (16, y))

            # Day
            day_surf = self.font_sm.render(fc["day"], True, self.white)
            self.screen.blit(day_surf, (28, y + 12))

            # Condition badge
            badge_surf = self.font_xs.render(fc["code"], True, fc_color)
            self.screen.blit(badge_surf, (badge_surf.get_rect(centerx=cx, top=y + 14)))

            # Hi / Lo
            hi_surf = self.font_sm.render(f"{fc['hi']}°", True, fc_color)
            lo_surf = self.font_xs.render(f"{fc['lo']}°", True, self.muted)
            self.screen.blit(hi_surf, (self.width - 80, y + 10))
            self.screen.blit(lo_surf, (self.width - 36, y + 14))

            # Mini temp bar
            bar_w = 120
            bar_x = cx - bar_w // 2
            bar_y = y + 36
            pygame.draw.line(self.screen, self.dim, (bar_x, bar_y), (bar_x + bar_w, bar_y), 2)
            spread = max(1, fc['hi'] - fc['lo'])
            fill_w = int(bar_w * min(1.0, spread / 20.0))
            pygame.draw.line(self.screen, fc_color, (bar_x, bar_y), (bar_x + fill_w, bar_y), 2)

        # ── Bottom border ──────────────────────────────────
        pygame.draw.line(self.screen, self.dim,
                         (16, forecast_y + 3 * row_h + 4),
                         (self.width - 16, forecast_y + 3 * row_h + 4), 1)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _blit_center(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(centerx=self.width // 2, top=y))

    def _blit_label(self, text, y):
        surf = self.font_xs.render(text, True, self.muted)
        self.screen.blit(surf, (16, y))

    def cleanup(self):
        pass
