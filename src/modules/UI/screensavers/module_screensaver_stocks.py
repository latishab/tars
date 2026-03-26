"""
Stock Market screensaver — TARS display
Market Recon HUD. Fetches live quotes via Yahoo Finance (no API key needed).
Data refreshes in a background thread so the render loop never blocks.
"""
import pygame
import threading
import time
import math
import urllib.request
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

_UI_DIR = Path(__file__).parent.parent
_ASSETS = Path(__file__).parent.parent / "assets"

_UP    = (40,  210, 105)
_DOWN  = (220,  55,  55)
_FLAT  = (130, 145, 160)
_AMBER = (200, 145,  30)
_DIM   = (38,   55,  70)
_BG    = (5,    7,   12)

_FEATURED  = "SPUS"
_WATCHLIST = ["SPWO", "GLD", "NVDA", "AAPL"]


def _fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _col(pct):
    if pct > 0.05:
        return _UP
    if pct < -0.05:
        return _DOWN
    return _FLAT


def _fmt_price(p):
    if p >= 10000:
        return f"{p:,.0f}"
    if p >= 1000:
        return f"{p:,.2f}"
    return f"{p:.2f}"


def _fmt_pct(pct):
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _fmt_chg(chg):
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:.2f}"


class StocksAnimation:
    def __init__(self, screen, width, height, show_time=False):
        self.screen = screen
        self.width  = width
        self.height = height
        self.cx     = width // 2

        # Fonts
        try:
            self.f_price  = pygame.font.Font(str(_ASSETS / "astrolab.ttf"), 64)
            self.f_symbol = pygame.font.Font(str(_ASSETS / "astrolab.ttf"), 26)
        except Exception:
            self.f_price  = pygame.font.SysFont("monospace", 64, bold=True)
            self.f_symbol = pygame.font.SysFont("monospace", 26)

        try:
            self.f_label  = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 13)
            self.f_value  = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 16)
            self.f_change = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 18)
            self.f_row    = pygame.font.Font(str(_UI_DIR / "pixelmix.ttf"), 15)
        except Exception:
            self.f_label  = pygame.font.SysFont("monospace", 13)
            self.f_value  = pygame.font.SysFont("monospace", 16)
            self.f_change = pygame.font.SysFont("monospace", 18)
            self.f_row    = pygame.font.SysFont("monospace", 15)

        try:
            self.f_meta = pygame.font.Font(str(_UI_DIR / "mono.ttf"), 13)
        except Exception:
            self.f_meta = pygame.font.SysFont("monospace", 13)

        # State
        self._data        = None
        self._error       = None
        self._loading     = True
        self._lock        = threading.Lock()
        self._last_fetch  = 0
        self._fetch_interval = 60

        # Animation
        self._t           = 0.0
        self._spin_angle  = 0.0
        self._flash_t     = 0.0
        self._tick_x      = float(width)
        self._tick_surf   = None
        self._tick_w      = 0

        self._kick_fetch()

    def reset(self):
        pass

    def _kick_fetch(self):
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_chart(self, symbol, interval="5m", range_="1d"):
        """Fetch v8 chart — returns (meta, closes)."""
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?interval={interval}&range={range_}"
        )
        raw    = _fetch_json(url)
        result = raw["chart"]["result"][0]
        meta   = result["meta"]
        closes = result["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        return meta, closes

    def _meta_to_quote(self, sym, meta, closes):
        price  = meta.get("regularMarketPrice", 0.0)
        prev   = meta.get("chartPreviousClose", price) or price
        change = price - prev
        pct    = (change / prev * 100) if prev else 0.0
        return {
            "symbol": sym,
            "name":   meta.get("shortName", sym)[:22],
            "price":  price,
            "change": change,
            "pct":    pct,
            "high":   meta.get("regularMarketDayHigh", 0.0),
            "low":    meta.get("regularMarketDayLow", 0.0),
            "open":   meta.get("chartPreviousClose", 0.0),
            "volume": meta.get("regularMarketVolume", 0),
            "state":  meta.get("currentTradingPeriod", {}).get("regular", {}).get("timezone", ""),
            "chart":  closes,
        }

    def _fetch_data(self):
        try:
            # Featured: intraday sparkline (5m/1d)
            f_meta, f_closes = self._fetch_chart(_FEATURED, "5m", "1d")
            featured = self._meta_to_quote(_FEATURED, f_meta, f_closes)

            # Detect market state from trading period timestamps
            tp = f_meta.get("currentTradingPeriod", {})
            now_ts = time.time()
            reg = tp.get("regular", {})
            if reg.get("start", 0) <= now_ts <= reg.get("end", 0):
                featured["state"] = "REGULAR"
            elif tp.get("pre", {}).get("start", 0) <= now_ts <= tp.get("pre", {}).get("end", 0):
                featured["state"] = "PRE"
            elif tp.get("post", {}).get("start", 0) <= now_ts <= tp.get("post", {}).get("end", 0):
                featured["state"] = "POST"
            else:
                featured["state"] = "CLOSED"

            # Watchlist: daily (1d/5d) — 5 daily closes for mini sparkline
            watchlist = []
            for sym in _WATCHLIST:
                try:
                    w_meta, w_closes = self._fetch_chart(sym, "1d", "5d")
                    q = self._meta_to_quote(sym, w_meta, w_closes)
                    watchlist.append(q)
                except Exception:
                    pass

            # News headlines via Yahoo Finance RSS
            news = []
            try:
                rss_url = ("https://feeds.finance.yahoo.com/rss/2.0/headline"
                           "?s=SPY,AAPL,NVDA&region=US&lang=en-US")
                rss_req  = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(rss_req, timeout=6) as resp:
                    root = ET.fromstring(resp.read())
                now_dt = datetime.now(timezone.utc)
                for item in root.iter("item"):
                    title = (item.findtext("title") or "").strip()
                    pub   = item.findtext("pubDate") or ""
                    src   = item.findtext("source") or "Yahoo Finance"
                    if not title:
                        continue
                    age = ""
                    try:
                        pub_dt = parsedate_to_datetime(pub)
                        delta  = now_dt - pub_dt
                        mins   = int(delta.total_seconds() / 60)
                        if mins < 60:
                            age = f"{mins}m ago"
                        elif mins < 1440:
                            age = f"{mins // 60}h ago"
                        else:
                            age = f"{mins // 1440}d ago"
                    except Exception:
                        pass
                    news.append({"title": title, "source": src, "age": age})
                    if len(news) >= 2:
                        break
            except Exception:
                pass

            now  = datetime.now(timezone.utc).strftime("%H:%M")
            data = {"featured": featured, "watchlist": watchlist, "news": news, "updated": now}

            with self._lock:
                self._data       = data
                self._error      = None
                self._loading    = False
                self._last_fetch = time.time()
                self._tick_surf  = None   # invalidate ticker cache

        except Exception as e:
            with self._lock:
                self._error   = str(e)[:52]
                self._loading = False

    # ── Loop ───────────────────────────────────────────────────────────────

    def update(self):
        self._t          += 1.0 / 30.0
        self._spin_angle  = (self._spin_angle + 1.5) % 360
        self._flash_t     = (self._flash_t + 0.05) % math.tau

        # Scroll ticker left
        self._tick_x -= 1.5
        if self._tick_w > 0 and self._tick_x < -self._tick_w:
            self._tick_x = float(self.width)

        with self._lock:
            needs = not self._loading and (time.time() - self._last_fetch > self._fetch_interval)
        if needs:
            with self._lock:
                self._loading = True
            self._kick_fetch()

    def render(self):
        self.screen.fill(_BG)
        with self._lock:
            data    = self._data
            loading = self._loading
            error   = self._error

        if loading and data is None:
            self._draw_loading()
            return
        if error and data is None:
            self._draw_error(error)
            return

        self._draw_header(data)
        self._draw_featured(data["featured"])
        end_y = self._draw_watchlist(data["watchlist"])
        self._draw_news(data.get("news", []), end_y)
        self._draw_ticker(data)

    # ── Loading / error ────────────────────────────────────────────────────

    def _draw_loading(self):
        CX, CY = self.cx, self.height // 2
        R = 28
        for i in range(12):
            a = math.radians(self._spin_angle + i * 30)
            alpha = int(255 * (i + 1) / 12)
            x = int(CX + R * math.cos(a))
            y = int(CY + R * math.sin(a))
            c = (int(_AMBER[0] * alpha / 255),
                 int(_AMBER[1] * alpha / 255),
                 int(_AMBER[2] * alpha / 255))
            pygame.draw.circle(self.screen, c, (x, y), 3)
        lbl = self.f_label.render("ACQUIRING MARKET DATA", True, _DIM)
        self.screen.blit(lbl, lbl.get_rect(centerx=CX, top=CY + 44))

    def _draw_error(self, msg):
        CX, CY = self.cx, self.height // 2
        e1 = self.f_value.render("MARKET LINK LOST", True, _DOWN)
        e2 = self.f_label.render(msg, True, (80, 40, 40))
        self.screen.blit(e1, e1.get_rect(centerx=CX, top=CY - 14))
        self.screen.blit(e2, e2.get_rect(centerx=CX, top=CY + 10))

    # ── Header ─────────────────────────────────────────────────────────────

    def _draw_header(self, data):
        W     = self.width
        state = data["featured"].get("state", "CLOSED")
        s_col = _UP if state == "REGULAR" else _AMBER

        # Corner brackets
        pygame.draw.line(self.screen, _AMBER, (8, 6),      (28, 6),      2)
        pygame.draw.line(self.screen, _AMBER, (8, 6),      (8, 20),      2)
        pygame.draw.line(self.screen, _AMBER, (W - 28, 6), (W - 8, 6),   2)
        pygame.draw.line(self.screen, _AMBER, (W - 8, 6),  (W - 8, 20),  2)

        lbl = self.f_label.render("MARKET  RECON", True, _DIM)
        self.screen.blit(lbl, (32, 10))

        upd = self.f_label.render(f"{state}  {data['updated']} UTC", True, s_col)
        self.screen.blit(upd, (W - upd.get_width() - 32, 10))

        pygame.draw.line(self.screen, (18, 28, 38), (16, 32), (W - 16, 32), 1)

    # ── Featured ───────────────────────────────────────────────────────────

    def _draw_featured(self, f):
        W   = self.width
        col = _col(f["pct"])

        # Symbol + name
        sym_s  = self.f_symbol.render(f["symbol"], True, (210, 220, 235))
        name_s = self.f_label.render(f["name"].upper(), True, (65, 88, 108))
        self.screen.blit(sym_s, (16, 40))
        self.screen.blit(name_s, (16 + sym_s.get_width() + 10, 50))

        # Large price
        price_s = self.f_price.render(_fmt_price(f["price"]), True, (220, 230, 240))
        self.screen.blit(price_s, (16, 66))

        # Change badge (top-right)
        chg_str = _fmt_pct(f["pct"])
        chg_s   = self.f_change.render(chg_str, True, col)
        bw = chg_s.get_width() + 16
        bh = chg_s.get_height() + 8
        bx = W - bw - 16
        by = 72
        badge = pygame.Surface((bw, bh), pygame.SRCALPHA)
        badge.fill((col[0] // 6, col[1] // 6, col[2] // 6, 200))
        self.screen.blit(badge, (bx, by))
        pygame.draw.rect(self.screen, col, (bx, by, bw, bh), 1)
        self.screen.blit(chg_s, (bx + 8, by + 4))

        # Absolute change
        abs_s = self.f_label.render(_fmt_chg(f["change"]), True, col)
        self.screen.blit(abs_s, (W - abs_s.get_width() - 16, by + bh + 5))

        # H / L / O row
        hl_y = 156
        items = [
            ("H", _fmt_price(f["high"]),  (60, 190, 80),  (110, 230, 130)),
            ("L", _fmt_price(f["low"]),   (190, 50, 50),  (225, 90,  90)),
            ("O", _fmt_price(f["open"]),  (80, 120, 160), (130, 170, 210)),
        ]
        cx = 16
        for lbl_txt, val_txt, lbl_col, val_col in items:
            ls = self.f_label.render(lbl_txt, True, lbl_col)
            vs = self.f_label.render(val_txt, True, val_col)
            self.screen.blit(ls, (cx, hl_y))
            cx += ls.get_width() + 4
            self.screen.blit(vs, (cx, hl_y))
            cx += vs.get_width() + 20

        # Sparkline
        self._draw_sparkline(f["chart"], col, 16, 182, W - 32, 85)

        # Separator
        pygame.draw.line(self.screen, (14, 22, 32), (16, 276), (W - 16, 276), 1)

    def _draw_sparkline(self, prices, col, x, y, w, h):
        if len(prices) < 2:
            lbl = self.f_label.render("AWAITING DATA", True, _DIM)
            self.screen.blit(lbl, lbl.get_rect(centerx=x + w // 2, top=y + h // 2 - 7))
            return

        lo   = min(prices)
        hi   = max(prices)
        span = (hi - lo) or 1.0

        def pt(i, p):
            px = x + int(i * w / (len(prices) - 1))
            py = y + h - int((p - lo) / span * h)
            return (px, py)

        points = [pt(i, p) for i, p in enumerate(prices)]

        # Filled area under line
        poly = [(x, y + h)] + points + [(x + w, y + h)]
        fill = pygame.Surface((w, h), pygame.SRCALPHA)
        local = [(px - x, py - y) for px, py in poly]
        pygame.draw.polygon(fill, (col[0] // 7, col[1] // 7, col[2] // 7, 140), local)
        self.screen.blit(fill, (x, y))

        # Open-price zero line
        open_y = y + h - int((prices[0] - lo) / span * h)
        pygame.draw.line(self.screen, (28, 42, 52), (x, open_y), (x + w, open_y), 1)

        # Line: glow pass + bright pass
        pygame.draw.lines(self.screen, (col[0] // 3, col[1] // 3, col[2] // 3), False, points, 3)
        pygame.draw.lines(self.screen, col, False, points, 1)

        # Pulsing last-price dot
        lx, ly = points[-1]
        pygame.draw.circle(self.screen, col, (lx, ly), 3)
        pulse_r = 5 + int(abs(math.sin(self._flash_t)) * 3)
        pulse_a = int(abs(math.sin(self._flash_t)) * 160)
        pulse_surf = pygame.Surface((pulse_r * 2 + 2, pulse_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surf, (*col, pulse_a), (pulse_r + 1, pulse_r + 1), pulse_r, 1)
        self.screen.blit(pulse_surf, (lx - pulse_r - 1, ly - pulse_r - 1))

    # ── Watchlist ──────────────────────────────────────────────────────────

    def _draw_watchlist(self, watchlist):
        W   = self.width
        Y0  = 302
        ROW = 74

        sec = self.f_label.render("W A T C H L I S T", True, (38, 58, 72))
        self.screen.blit(sec, sec.get_rect(centerx=self.cx, top=Y0 - 18))

        for i, item in enumerate(watchlist):
            y   = Y0 + i * ROW
            col = _col(item["pct"])

            if i > 0:
                pygame.draw.line(self.screen, (11, 18, 26), (16, y), (W - 16, y), 1)

            # Symbol (left)
            sym_s  = self.f_row.render(item["symbol"], True, (175, 195, 215))
            name_s = self.f_label.render(item["name"].upper(), True, (45, 65, 82))
            self.screen.blit(sym_s,  (16, y + 8))
            self.screen.blit(name_s, (16, y + 28))

            # Price + pct (right)
            price_s = self.f_row.render(_fmt_price(item["price"]), True, (190, 205, 222))
            pct_s   = self.f_label.render(_fmt_pct(item["pct"]), True, col)
            self.screen.blit(price_s, (W - price_s.get_width() - 16, y + 8))
            self.screen.blit(pct_s,   (W - pct_s.get_width() - 16,   y + 28))

            # 5-day mini sparkline (center)
            prices = item.get("chart", [])
            if len(prices) >= 2:
                sw  = 148
                sx  = W - sw - 90
                sh  = 30
                sy  = y + (ROW - sh) // 2
                lo  = min(prices)
                hi  = max(prices)
                rng = (hi - lo) or 1.0
                pts = [
                    (sx + int(j * sw / (len(prices) - 1)),
                     sy + sh - int((p - lo) / rng * sh))
                    for j, p in enumerate(prices)
                ]
                dim = (col[0] // 4, col[1] // 4, col[2] // 4)
                pygame.draw.lines(self.screen, dim, False, pts, 3)
                pygame.draw.lines(self.screen, col, False, pts, 1)
                pygame.draw.circle(self.screen, col, pts[-1], 3)

        divider_y = Y0 + len(watchlist) * ROW + 4
        pygame.draw.line(self.screen, (14, 22, 32),
                         (16, divider_y), (W - 16, divider_y), 1)
        return divider_y

    # ── News headlines ─────────────────────────────────────────────────────

    def _draw_news(self, news, after_y):
        if not news:
            return
        W   = self.width
        ROW = 42   # enough room for headline + source line + gap between items

        # Section label — 18px below the watchlist divider
        label_y = after_y + 18
        sec = self.f_label.render("M A R K E T  N E W S", True, (38, 58, 72))
        self.screen.blit(sec, sec.get_rect(centerx=self.cx, top=label_y))

        # First news row starts below the label
        Y0 = label_y + 32

        for i, item in enumerate(news):
            y = Y0 + i * ROW

            # Bullet
            bul = self.f_label.render("▸", True, _AMBER)
            self.screen.blit(bul, (16, y))

            # Headline — truncate to fit
            headline = item["title"]
            max_w    = W - 52
            hl_surf  = self.f_label.render(headline, True, (160, 178, 195))
            while hl_surf.get_width() > max_w and len(headline) > 10:
                headline = headline[:-4] + "…"
                hl_surf  = self.f_label.render(headline, True, (160, 178, 195))
            self.screen.blit(hl_surf, (30, y))

            # Source + age
            meta_str = f"{item['source']}  {item['age']}".strip()
            meta_s   = self.f_meta.render(meta_str, True, (42, 62, 78))
            self.screen.blit(meta_s, (30, y + 16))

    # ── Scrolling ticker ───────────────────────────────────────────────────

    def _draw_ticker(self, data):
        W = self.width

        # Build once (or after data refresh)
        if self._tick_surf is None:
            all_items = [data["featured"]] + data["watchlist"]
            pad = 36
            total_w = 0
            rendered = []
            for item in all_items:
                col = _col(item["pct"])
                ss = self.f_meta.render(item["symbol"], True, (155, 175, 200))
                ps = self.f_meta.render(f" {_fmt_price(item['price'])}", True, (195, 208, 220))
                cs = self.f_meta.render(f" {_fmt_pct(item['pct'])}", True, col)
                sp = self.f_meta.render("  ·  ", True, (28, 42, 52))
                rendered.append((ss, ps, cs, sp))
                total_w += ss.get_width() + ps.get_width() + cs.get_width() + sp.get_width() + pad

            th   = 26
            surf = pygame.Surface((total_w, th), pygame.SRCALPHA)
            surf.fill((7, 11, 17, 210))
            cx = 0
            for ss, ps, cs, sp in rendered:
                cy = (th - ss.get_height()) // 2
                surf.blit(ss, (cx, cy)); cx += ss.get_width() + 3
                surf.blit(ps, (cx, cy)); cx += ps.get_width()
                surf.blit(cs, (cx, cy)); cx += cs.get_width()
                surf.blit(sp, (cx, cy)); cx += sp.get_width() + pad

            self._tick_surf = surf
            self._tick_w    = total_w

        ty = self.height - 55
        strip = pygame.Surface((W, 26), pygame.SRCALPHA)
        strip.fill((7, 11, 17, 210))
        self.screen.blit(strip, (0, ty))
        pygame.draw.line(self.screen, (22, 34, 46), (0, ty), (W, ty), 1)

        x = int(self._tick_x)
        self.screen.blit(self._tick_surf, (x, ty))
        if x + self._tick_w < W:
            self.screen.blit(self._tick_surf, (x + self._tick_w, ty))

        # Bottom corner brackets
        bc = (38, 58, 76)
        pygame.draw.line(self.screen, bc, (8,     self.height - 8),  (28,    self.height - 8),  2)
        pygame.draw.line(self.screen, bc, (8,     self.height - 22), (8,     self.height - 8),  2)
        pygame.draw.line(self.screen, bc, (W - 28, self.height - 8), (W - 8, self.height - 8),  2)
        pygame.draw.line(self.screen, bc, (W - 8, self.height - 22), (W - 8, self.height - 8),  2)
