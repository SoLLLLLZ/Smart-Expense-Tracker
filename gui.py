"""Optional tkinter GUI for the Smart Expense Tracker."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
import calendar
import random
import math

from config import VALID_CATEGORIES, VALID_PAYMENT_METHODS, DATE_FORMAT
from models import Expense
import crud
import analytics


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEMES = {
    "tokyo_night": {
        "name":         "Tokyo Night",
        # ── Dark navy background ──────────────────────────────────────────
        "BG":           "#1a1b2e",
        "PANEL":        "#16172a",
        "CARD":         "#1f2041",
        # ── Accent colours ───────────────────────────────────────────────
        "ACCENT":       "#7aa2f7",   # bright blue   → used for primary actions
        "ACCENT2":      "#bb9af7",   # soft lavender  → amounts / highlights
        "ACCENT3":      "#9ece6a",   # green          → today / success
        # ── Text ─────────────────────────────────────────────────────────
        "TEXT":         "#c0caf5",   # near-white on dark
        "TEXT_DIM":     "#7a8ab0",
        "TEXT_ON_ACCENT": "#0d1117", # dark text when sitting on a light accent btn
        # ── Semantic ─────────────────────────────────────────────────────
        "DANGER":       "#f7768e",
        "DANGER_FG":    "#ffffff",
        "SUCCESS":      "#9ece6a",
        # ── Interactive ──────────────────────────────────────────────────
        "BTN_HOVER":    "#3d59a1",
        "SEL_BG":       "#3d59a1",
        # ── Table rows ───────────────────────────────────────────────────
        "STRIPE_A":     "#1a1b2e",
        "STRIPE_B":     "#1f2041",
        # ── Misc ─────────────────────────────────────────────────────────
        "SNOW":         "#c0caf5",
        "HEADING":      "#7aa2f7",
    },
    "sunrise": {
        "name":         "Gradient Sunrise",
        # ── Warm cream / peach light background ──────────────────────────
        "BG":           "#fff8f0",   # warm cream
        "PANEL":        "#fde8d8",   # soft peach panel
        "CARD":         "#fef3e8",   # lightest card surface
        # ── Accent colours ───────────────────────────────────────────────
        "ACCENT":       "#d45d00",   # deep burnt-orange  → primary actions
        "ACCENT2":      "#b5390a",   # deeper terracotta  → amounts / prices
        "ACCENT3":      "#e8850a",   # warm amber         → today / calendar
        # ── Text ─────────────────────────────────────────────────────────
        "TEXT":         "#2d1500",   # very dark warm-brown on cream
        "TEXT_DIM":     "#8a5c3a",   # medium warm-brown
        "TEXT_ON_ACCENT": "#ffffff", # white text when sitting on a dark accent btn
        # ── Semantic ─────────────────────────────────────────────────────
        "DANGER":       "#b5000a",
        "DANGER_FG":    "#ffffff",
        "SUCCESS":      "#1a6e2e",
        # ── Interactive ──────────────────────────────────────────────────
        "BTN_HOVER":    "#b34e00",
        "SEL_BG":       "#f5c4a0",
        # ── Table rows ───────────────────────────────────────────────────
        "STRIPE_A":     "#fff8f0",
        "STRIPE_B":     "#fde8d8",
        # ── Misc ─────────────────────────────────────────────────────────
        "SNOW":         "#d45d00",   # falling "embers" / snowflakes look warm
        "HEADING":      "#d45d00",
    },
}

# Active theme — mutable dict, mutated on toggle
T = dict(THEMES["tokyo_night"])


def _apply_theme(name: str):
    global T
    T.update(THEMES[name])


# ---------------------------------------------------------------------------
# Custom money-bill cursor (XBM bitmap)
# ---------------------------------------------------------------------------

_BILL_DATA = """
#define bill_width 32
#define bill_height 16
static unsigned char bill_bits[] = {
  0xff, 0xff, 0xff, 0xff,
  0x01, 0x00, 0x00, 0x80,
  0xfd, 0xf1, 0x8f, 0xbf,
  0x05, 0x12, 0x48, 0xa0,
  0xc5, 0xd3, 0xc9, 0xa3,
  0x05, 0x12, 0x48, 0xa0,
  0xc5, 0xd3, 0xc9, 0xa3,
  0x05, 0x12, 0x48, 0xa0,
  0xc5, 0xd3, 0xc9, 0xa3,
  0x05, 0x12, 0x48, 0xa0,
  0xc5, 0xd3, 0xc9, 0xa3,
  0x05, 0x12, 0x48, 0xa0,
  0xfd, 0xf1, 0x8f, 0xbf,
  0x01, 0x00, 0x00, 0x80,
  0xff, 0xff, 0xff, 0xff,
  0x00, 0x00, 0x00, 0x00
};
"""

_BILL_MASK = """
#define bill_width 32
#define bill_height 16
static unsigned char bill_bits[] = {
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0xff, 0xff, 0xff, 0xff,
  0x00, 0x00, 0x00, 0x00
};
"""


def _apply_money_cursor(widget):
    try:
        cursor = tk.BitmapImage(data=_BILL_DATA, maskdata=_BILL_MASK,
                                foreground=T["ACCENT2"], background=T["PANEL"])
        widget._money_cursor = cursor
        widget.config(cursor=cursor)
    except Exception:
        try:
            widget.config(cursor="hand2")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Snow canvas
# ---------------------------------------------------------------------------

class SnowCanvas(tk.Canvas):
    """Transparent-ish canvas that draws animated snowflakes over the background."""

    NUM_FLAKES = 80

    def __init__(self, parent, **kw):
        super().__init__(parent, highlightthickness=0, bd=0, **kw)
        self._flakes = []
        self._running = True
        self._init_flakes()
        self._animate()

    def _init_flakes(self):
        w = self.winfo_reqwidth() or 1060
        h = self.winfo_reqheight() or 120
        self._flakes = []
        for _ in range(self.NUM_FLAKES):
            self._flakes.append({
                "x":     random.uniform(0, w),
                "y":     random.uniform(-h, h),
                "r":     random.uniform(1.5, 4.0),
                "speed": random.uniform(0.5, 1.8),
                "drift": random.uniform(-0.4, 0.4),
                "alpha": random.uniform(0.4, 1.0),
            })

    def _animate(self):
        if not self._running:
            return
        self.delete("snow")
        w = self.winfo_width()  or 1060
        h = self.winfo_height() or 120

        snow_color = T["SNOW"]

        for f in self._flakes:
            f["y"] += f["speed"]
            f["x"] += f["drift"] + math.sin(f["y"] * 0.03) * 0.3
            if f["y"] > h + 6:
                f["y"] = random.uniform(-10, -2)
                f["x"] = random.uniform(0, w)
            if f["x"] < -6:
                f["x"] = w + 4
            elif f["x"] > w + 6:
                f["x"] = -4

            x, y, r = f["x"], f["y"], f["r"]
            self.create_oval(x - r, y - r, x + r, y + r,
                             fill=snow_color, outline="", tags="snow")

        self.after(33, self._animate)   # ~30 fps

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# Styled button helper
# ---------------------------------------------------------------------------

def _make_btn(parent, text, command,
              color=None, hover=None, fg=None,
              width=None, font=None, padx=14, pady=6):
    color = color or T["CARD"]
    hover = hover or T["BTN_HOVER"]
    fg    = fg    or "#000000"
    font  = font  or ("Segoe UI", 10, "bold")

    kw = dict(text=text, command=command, bg=color, fg=fg,
              font=font, relief="flat", bd=0, cursor="hand2",
              activebackground=hover, activeforeground=fg,
              padx=padx, pady=pady)
    if width:
        kw["width"] = width
    btn = tk.Button(parent, **kw)

    def _on_enter(_): btn.config(bg=hover)
    def _on_leave(_): btn.config(bg=color)
    btn.bind("<Enter>", _on_enter)
    btn.bind("<Leave>", _on_leave)
    return btn


# ---------------------------------------------------------------------------
# Add / Edit dialog
# ---------------------------------------------------------------------------

class ExpenseDialog(tk.Toplevel):
    def __init__(self, parent, expense: Expense = None):
        super().__init__(parent)
        self.result   = None
        self._expense = expense
        self.title("Edit Expense" if expense else "Add Expense")
        self.configure(bg=T["BG"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._populate(expense)
        self.wait_window()

    def _label(self, text, row):
        tk.Label(self, text=text, bg=T["BG"], fg=T["TEXT_DIM"],
                 font=("Segoe UI", 10), anchor="w").grid(
            row=row, column=0, sticky="w", padx=16, pady=6)

    def _entry(self, row, width=28):
        e = tk.Entry(self, width=width, bg=T["PANEL"], fg=T["TEXT"],
                     insertbackground=T["TEXT"], relief="flat",
                     font=("Segoe UI", 10), bd=4)
        e.grid(row=row, column=1, padx=16, pady=6, sticky="ew")
        return e

    def _build(self):
        self._entries = {}
        for i, (label, key) in enumerate([
            ("Date (YYYY-MM-DD)", "date"),
            ("Merchant",          "merchant"),
            ("Amount ($)",        "amount"),
        ]):
            self._label(label, i)
            self._entries[key] = self._entry(i)

        self._label("Category", 3)
        self._cat_var = tk.StringVar(value=VALID_CATEGORIES[0])
        ttk.Combobox(self, textvariable=self._cat_var,
                     values=VALID_CATEGORIES, state="readonly",
                     width=26).grid(row=3, column=1, padx=16, pady=6, sticky="ew")

        self._label("Payment Method", 4)
        self._pay_var = tk.StringVar(value=VALID_PAYMENT_METHODS[0])
        ttk.Combobox(self, textvariable=self._pay_var,
                     values=VALID_PAYMENT_METHODS, state="readonly",
                     width=26).grid(row=4, column=1, padx=16, pady=6, sticky="ew")

        bf = tk.Frame(self, bg=T["BG"])
        bf.grid(row=5, column=0, columnspan=2, pady=14)
        _make_btn(bf, "Save",   self._on_save,  color=T["ACCENT"],
                  hover=T["BTN_HOVER"], fg="#000000", width=10).pack(side="left", padx=6)
        _make_btn(bf, "Cancel", self.destroy,   color=T["CARD"],
                  hover=T["PANEL"], fg="#000000", width=10).pack(side="left", padx=6)

    def _populate(self, expense):
        if expense is None:
            self._entries["date"].insert(0, date.today().strftime(DATE_FORMAT))
            return
        self._entries["date"].insert(0, expense.date.strftime(DATE_FORMAT))
        self._entries["merchant"].insert(0, expense.merchant)
        self._entries["amount"].insert(0, str(expense.amount))
        self._cat_var.set(expense.category)
        self._pay_var.set(expense.payment_method)

    def _on_save(self):
        from datetime import datetime
        date_str   = self._entries["date"].get().strip()
        merchant   = self._entries["merchant"].get().strip()
        amount_str = self._entries["amount"].get().strip()
        category   = self._cat_var.get()
        pay_method = self._pay_var.get()

        try:
            parsed_date = datetime.strptime(date_str, DATE_FORMAT).date()
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.")
            return
        if not merchant:
            messagebox.showerror("Missing Field", "Merchant cannot be empty.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Amount must be a positive number.")
            return

        self.result = Expense(
            id=self._expense.id if self._expense else None,
            date=parsed_date, merchant=merchant, amount=amount,
            category=category, payment_method=pay_method,
            source=self._expense.source if self._expense else "manual",
        )
        self.destroy()


# ---------------------------------------------------------------------------
# Calendar screen
# ---------------------------------------------------------------------------

class CalendarScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Money Calendar")
        self.geometry("900x660")
        self.configure(bg=T["BG"])
        self.resizable(True, True)

        self._view   = tk.StringVar(value="month")
        self._today  = date.today()
        self._anchor = date(self._today.year, self._today.month, 1)

        self._build_controls()
        self._cf = tk.Frame(self, bg=T["BG"])
        self._cf.pack(fill="both", expand=True, padx=12, pady=8)
        self._render()

    # controls

    def _build_controls(self):
        bar = tk.Frame(self, bg=T["PANEL"], pady=6)
        bar.pack(fill="x")
        _make_btn(bar, "◀", self._go_prev, color=T["CARD"],
                  hover=T["ACCENT"], fg="#000000", padx=10, pady=4).pack(side="left", padx=6)
        _make_btn(bar, "▶", self._go_next, color=T["CARD"],
                  hover=T["ACCENT"], fg="#000000", padx=10, pady=4).pack(side="left")
        self._nav_lbl = tk.Label(bar, text="", bg=T["PANEL"],
                                 fg=T["TEXT"], font=("Segoe UI", 13, "bold"))
        self._nav_lbl.pack(side="left", padx=16)
        for lbl, val in [("Month", "month"), ("Week", "week"), ("Day", "day")]:
            _make_btn(bar, lbl, lambda v=val: self._set_view(v),
                      color=T["CARD"], hover=T["ACCENT"],
                      fg="#000000", padx=12, pady=4).pack(side="right", padx=4)
        _make_btn(bar, "Today", self._go_today,
                  color=T["ACCENT"], hover=T["BTN_HOVER"],
                  fg="#000000", padx=10, pady=4).pack(side="right", padx=8)

    def _set_view(self, v):
        self._view.set(v); self._render()

    def _go_today(self):
        self._anchor = date(self._today.year, self._today.month, 1)
        self._render()

    def _go_prev(self):
        v = self._view.get()
        if v == "month":
            m = self._anchor.month - 1 or 12
            y = self._anchor.year - (1 if self._anchor.month == 1 else 0)
            self._anchor = date(y, m, 1)
        elif v == "week":
            self._anchor -= timedelta(weeks=1)
        else:
            self._anchor -= timedelta(days=1)
        self._render()

    def _go_next(self):
        v = self._view.get()
        if v == "month":
            m = self._anchor.month % 12 + 1
            y = self._anchor.year + (1 if self._anchor.month == 12 else 0)
            self._anchor = date(y, m, 1)
        elif v == "week":
            self._anchor += timedelta(weeks=1)
        else:
            self._anchor += timedelta(days=1)
        self._render()

    # render

    def _render(self):
        for w in self._cf.winfo_children():
            w.destroy()
        expenses = crud.get_all_expenses()
        by_date: dict = {}
        for e in expenses:
            by_date.setdefault(e.date.strftime(DATE_FORMAT), []).append(e)
        v = self._view.get()
        if v == "month":
            self._render_month(by_date)
        elif v == "week":
            self._render_week(by_date)
        else:
            self._render_day(by_date)

    @staticmethod
    def _blend_color(c1, c2, t):
        r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            int(r1 + (r2-r1)*t), int(g1 + (g2-g1)*t), int(b1 + (b2-b1)*t))

    def _render_month(self, by_date):
        y, m = self._anchor.year, self._anchor.month
        self._nav_lbl.config(text=f"{calendar.month_name[m]}  {y}")

        # ── Day-of-week header row ──────────────────────────────────────
        hdr = tk.Frame(self._cf, bg=T["BG"])
        hdr.pack(fill="x", pady=(0, 1))
        for col, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            hdr.columnconfigure(col, weight=1, uniform="hdr")
            tk.Label(hdr, text=day_name, bg=T["CARD"], fg=T["HEADING"],
                     font=("Segoe UI", 10, "bold")).grid(
                row=0, column=col, sticky="nsew", padx=1, pady=1)

        # ── Calendar grid ───────────────────────────────────────────────
        grid_frame = tk.Frame(self._cf, bg=T["BG"])
        grid_frame.pack(fill="both", expand=True)

        cal = calendar.monthcalendar(y, m)
        num_weeks = len(cal)

        # All 7 columns and all week rows share equal weight
        for col in range(7):
            grid_frame.columnconfigure(col, weight=1, uniform="cal")
        for row in range(num_weeks):
            grid_frame.rowconfigure(row, weight=1, uniform="cal")

        max_total = max(
            (sum(e.amount for e in v) for v in by_date.values()), default=1
        )

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                # Empty placeholder for days outside the month
                if day == 0:
                    tk.Frame(grid_frame, bg=T["BG"]).grid(
                        row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
                    continue

                d        = date(y, m, day)
                key      = d.strftime(DATE_FORMAT)
                exps     = by_date.get(key, [])
                total    = sum(e.amount for e in exps)
                is_today = (d == date.today())

                if total > 0:
                    intensity = min(total / max_total, 1.0)
                    bg_color = self._blend_color(T["CARD"], T["ACCENT"], intensity * 0.7)
                else:
                    bg_color = T["STRIPE_B"] if (row_idx + col_idx) % 2 == 0 else T["STRIPE_A"]

                # Cell outer frame — fills the grid cell completely
                cell = tk.Frame(grid_frame, bg=bg_color,
                                highlightbackground=T["CARD"], highlightthickness=1)
                cell.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
                # Prevent content labels from resizing the cell
                cell.pack_propagate(False)

                day_fg = T["ACCENT2"] if is_today else T["TEXT"]
                tk.Label(cell, text=str(day), bg=bg_color,
                         fg=day_fg, font=("Segoe UI", 10, "bold"),
                         anchor="nw").pack(anchor="nw", padx=4, pady=(3, 0))
                if total > 0:
                    tk.Label(cell, text=f"${total:.2f}", bg=bg_color,
                             fg=T["ACCENT2"],
                             font=("Segoe UI", 9, "bold")).pack(anchor="center")
                    tk.Label(cell, text=f"{len(exps)} item{'s' if len(exps)>1 else ''}",
                             bg=bg_color, fg=T["TEXT_DIM"],
                             font=("Segoe UI", 8)).pack(anchor="center")
                cell.bind("<Button-1>", lambda _, dt=d: self._show_day(dt))
                for child in cell.winfo_children():
                    child.bind("<Button-1>", lambda _, dt=d: self._show_day(dt))

    def _render_week(self, by_date):
        anchor = self._anchor
        monday = anchor - timedelta(days=anchor.weekday())
        sunday = monday + timedelta(days=6)
        self._nav_lbl.config(
            text=f"Week of {monday.strftime('%b %d')} – {sunday.strftime('%b %d, %Y')}")
        container = tk.Frame(self._cf, bg=T["BG"])
        container.pack(fill="both", expand=True)
        for i in range(7):
            d        = monday + timedelta(days=i)
            key      = d.strftime(DATE_FORMAT)
            exps     = by_date.get(key, [])
            total    = sum(e.amount for e in exps)
            is_today = (d == date.today())
            bg       = T["ACCENT"] if is_today else T["CARD"]
            row      = tk.Frame(container, bg=bg, pady=6, padx=10,
                                highlightbackground=T["PANEL"], highlightthickness=1)
            row.pack(fill="x", padx=4, pady=2)
            tk.Label(row, text=d.strftime("%A, %b %d"), bg=bg,
                     fg=T["TEXT"], font=("Segoe UI", 10, "bold"),
                     width=22, anchor="w").pack(side="left")
            if total > 0:
                tk.Label(row, text=f"${total:.2f}", bg=bg,
                         fg=T["ACCENT2"], font=("Segoe UI", 10, "bold")).pack(
                    side="left", padx=12)
                tk.Label(row, text=f"  {len(exps)} expense(s)", bg=bg,
                         fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="left")
                for e in exps[:3]:
                    tk.Label(row, text=f"  • {e.merchant}  ${e.amount:.2f}",
                             bg=bg, fg=T["TEXT_DIM"],
                             font=("Segoe UI", 9)).pack(side="left", padx=4)
                if len(exps) > 3:
                    tk.Label(row, text=f"+{len(exps)-3} more",
                             bg=bg, fg=T["TEXT_DIM"],
                             font=("Segoe UI", 9)).pack(side="left")
            else:
                tk.Label(row, text="No spending", bg=bg,
                         fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(
                    side="left", padx=12)
            row.bind("<Button-1>", lambda _, dt=d: self._show_day(dt))

    def _render_day(self, by_date):
        d    = self._anchor
        self._nav_lbl.config(text=d.strftime("%A, %B %d, %Y"))
        key  = d.strftime(DATE_FORMAT)
        exps = by_date.get(key, [])
        total = sum(e.amount for e in exps)

        strip = tk.Frame(self._cf, bg=T["CARD"], pady=10)
        strip.pack(fill="x", padx=4, pady=(0, 8))
        tk.Label(strip, text=f"Total: ${total:.2f}", bg=T["CARD"],
                 fg=T["ACCENT2"], font=("Segoe UI", 13, "bold")).pack(
            side="left", padx=20)
        tk.Label(strip, text=f"{len(exps)} expense(s)", bg=T["CARD"],
                 fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="left")

        if not exps:
            tk.Label(self._cf, text="No expenses on this day.",
                     bg=T["BG"], fg=T["TEXT_DIM"],
                     font=("Segoe UI", 10)).pack(pady=40)
            return

        for e in exps:
            card = tk.Frame(self._cf, bg=T["CARD"], pady=8, padx=12,
                            highlightbackground=T["ACCENT"], highlightthickness=1)
            card.pack(fill="x", padx=6, pady=3)
            tk.Label(card, text=e.merchant, bg=T["CARD"], fg=T["TEXT"],
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(
                side="left", padx=(0, 16))
            tk.Label(card, text=f"${e.amount:.2f}", bg=T["CARD"],
                     fg=T["ACCENT2"], font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(card, text=f"  {e.category}", bg=T["CARD"],
                     fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="left", padx=8)
            tk.Label(card, text=e.payment_method, bg=T["CARD"],
                     fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="right")

    def _show_day(self, d: date):
        self._anchor = d
        self._view.set("day")
        self._render()


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class ExpenseTrackerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self._theme_name = "tokyo_night"
        _apply_theme(self._theme_name)

        self.title("💰 Smart Expense Tracker")
        self.geometry("1080x660")
        self.minsize(860, 520)
        self.configure(bg=T["BG"])

        self._time_filter = tk.StringVar(value="all")
        self._sort_col    = "date"
        self._sort_desc   = True
        self._iid_to_dbid: dict = {}

        self._style_treeview()
        self._build_header()
        self._build_snow()          # snow layer (sits below toolbar)
        self._build_toolbar()
        self._build_expense_table()
        self._build_status_bar()
        _apply_money_cursor(self)
        self.refresh_table()

    # ------------------------------------------------------------------
    # Theme toggle
    # ------------------------------------------------------------------

    def _toggle_theme(self):
        self._theme_name = "sunrise" if self._theme_name == "tokyo_night" else "tokyo_night"
        _apply_theme(self._theme_name)
        # Rebuild the entire UI in the new theme
        for widget in self.winfo_children():
            widget.destroy()
        self._time_filter = tk.StringVar(value="all")
        self._sort_col    = "date"
        self._sort_desc   = True
        self._iid_to_dbid = {}
        self.configure(bg=T["BG"])
        self._style_treeview()
        self._build_header()
        self._build_snow()
        self._build_toolbar()
        self._build_expense_table()
        self._build_status_bar()
        _apply_money_cursor(self)
        self.refresh_table()

    # ------------------------------------------------------------------
    # Treeview style
    # ------------------------------------------------------------------

    def _style_treeview(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                        background=T["STRIPE_A"],
                        foreground=T["TEXT"],
                        fieldbackground=T["STRIPE_A"],
                        rowheight=30,
                        font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=T["CARD"],
                        foreground=T["HEADING"],
                        font=("Segoe UI", 10, "bold"),
                        relief="flat", borderwidth=0)
        style.map("Treeview",
                  background=[("selected", T["SEL_BG"])],
                  foreground=[("selected", T["TEXT"])],
                  fieldbackground=[("disabled", T["STRIPE_A"])])
        style.map("Treeview.Heading",
                  background=[("active", T["ACCENT"])])

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        hdr = tk.Frame(self, bg=T["CARD"], height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="💰  Smart Expense Tracker",
                 bg=T["CARD"], fg=T["TEXT"],
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=20)
        # Theme toggle button in header
        label = "🌙 Tokyo Night" if self._theme_name == "sunrise" else "🌅 Sunrise"
        _make_btn(hdr, label, self._toggle_theme,
                  color=T["ACCENT"], hover=T["BTN_HOVER"],
                  fg="#000000", padx=12, pady=6).pack(side="right", padx=14)

    # ------------------------------------------------------------------
    # Snow layer
    # ------------------------------------------------------------------

    def _build_snow(self):
        # Snow canvas sits in a fixed-height strip beneath the header
        self._snow = SnowCanvas(self, bg=T["BG"], height=70)
        self._snow.pack(fill="x")

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=T["PANEL"], pady=6)
        tb.pack(fill="x")

        _make_btn(tb, "+ Add",       self.on_add_expense,
                  color=T["ACCENT"], hover=T["BTN_HOVER"],
                  fg="#000000").pack(side="left", padx=(10, 4))
        _make_btn(tb, "📷 Receipt",  self.on_upload_receipt,
                  color=T["CARD"],   hover=T["ACCENT"],
                  fg="#000000").pack(side="left", padx=4)
        _make_btn(tb, "✏ Edit",      self.on_edit_expense,
                  color=T["CARD"],   hover=T["ACCENT"],
                  fg="#000000").pack(side="left", padx=4)
        _make_btn(tb, "🗑 Delete",   self.on_delete_expense,
                  color=T["CARD"], hover=T["ACCENT"],
                  fg="#000000").pack(side="left", padx=4)
        _make_btn(tb, "📊 Report",   self.on_generate_report,
                  color=T["CARD"],   hover=T["ACCENT"],
                  fg="#000000").pack(side="left", padx=4)
        _make_btn(tb, "📅 Calendar", self.on_open_calendar,
                  color=T["ACCENT"], hover=T["BTN_HOVER"],
                  fg="#000000").pack(side="left", padx=4)

        tk.Frame(tb, bg=T["CARD"], width=2).pack(side="left", fill="y", padx=8)

        # Time filter
        tk.Label(tb, text="Filter:", bg=T["PANEL"],
                 fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="left", padx=(4, 2))
        for lbl, val in [("All","all"), ("Day","day"), ("Week","week"), ("Month","month")]:
            _make_btn(tb, lbl, lambda v=val: self._set_time_filter(v),
                      color=T["CARD"], hover=T["ACCENT"],
                      fg="#000000", padx=10, pady=4).pack(side="left", padx=2)

        tk.Frame(tb, bg=T["CARD"], width=2).pack(side="left", fill="y", padx=8)

        # Search
        tk.Label(tb, text="🔍", bg=T["PANEL"],
                 fg=T["TEXT_DIM"], font=("Segoe UI", 10)).pack(side="left", padx=(4, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh_table())
        tk.Entry(tb, textvariable=self._search_var, width=18,
                 bg=T["CARD"], fg=T["TEXT"], insertbackground=T["TEXT"],
                 relief="flat", font=("Segoe UI", 10), bd=4).pack(side="left", pady=2)
        _make_btn(tb, "✕", lambda: self._search_var.set(""),
                  color=T["PANEL"], hover=T["CARD"],
                  fg="#000000", padx=6, pady=4).pack(side="left", padx=2)

    def _set_time_filter(self, val):
        self._time_filter.set(val)
        self.refresh_table()

    # ------------------------------------------------------------------
    # Expense table
    # ------------------------------------------------------------------

    def _build_expense_table(self):
        columns = ("#", "date", "merchant", "amount", "category", "payment", "source")
        frame = tk.Frame(self, bg=T["BG"])
        frame.pack(fill="both", expand=True, padx=6, pady=4)

        self._tree = ttk.Treeview(frame, columns=columns,
                                   show="headings", selectmode="browse")

        for col, heading, width in [
            ("#",        "#",         45),
            ("date",     "Date",     105),
            ("merchant", "Merchant", 200),
            ("amount",   "Amount",    90),
            ("category", "Category", 150),
            ("payment",  "Payment",  130),
            ("source",   "Source",    70),
        ]:
            anchor = "e" if col == "amount" else ("center" if col == "#" else "w")
            self._tree.heading(col, text=heading,
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=width, anchor=anchor, minwidth=30)

        self._tree.tag_configure("even", background=T["STRIPE_A"])
        self._tree.tag_configure("odd",  background=T["STRIPE_B"])

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", lambda _: self.on_edit_expense())

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=T["CARD"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self._status_var, bg=T["CARD"],
                 fg=T["TEXT_DIM"], font=("Segoe UI", 10),
                 anchor="w").pack(side="left", padx=12, pady=4)

    # ------------------------------------------------------------------
    # Table helpers
    # ------------------------------------------------------------------

    def _date_range(self):
        v     = self._time_filter.get()
        today = date.today()
        if v == "day":
            return today, today
        elif v == "week":
            mon = today - timedelta(days=today.weekday())
            return mon, mon + timedelta(days=6)
        elif v == "month":
            return date(today.year, today.month, 1), today
        return None, None

    def refresh_table(self):
        search    = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        db_order  = "date" if self._sort_col == "#" else self._sort_col
        df, dt    = self._date_range()

        expenses = crud.search_expenses(
            merchant=search or None,
            date_from=df, date_to=dt,
            order_by=db_order,
            descending=self._sort_desc,
        )

        for row in self._tree.get_children():
            self._tree.delete(row)

        self._iid_to_dbid = {}
        for idx, e in enumerate(expenses, start=1):
            iid = str(idx)
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=iid, tags=(tag,), values=(
                idx,
                e.date.strftime(DATE_FORMAT),
                e.merchant,
                f"${e.amount:.2f}",
                e.category,
                e.payment_method,
                e.source,
            ))
            self._iid_to_dbid[iid] = e.id

        total = analytics.total_spending(expenses)
        fl    = self._time_filter.get().capitalize()
        self._status_var.set(
            f"  {len(expenses)} record(s)   |   Total ({fl}): ${total:.2f}"
        )

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col  = col
            self._sort_desc = True
        self.refresh_table()

    def _selected_db_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select an expense first.")
            return None
        return self._iid_to_dbid.get(sel[0])

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def on_add_expense(self):
        dialog = ExpenseDialog(self)
        if dialog.result:
            crud.insert_expense(dialog.result)
            self.refresh_table()

    def on_edit_expense(self):
        db_id = self._selected_db_id()
        if db_id is None:
            return
        expense = crud.get_expense_by_id(db_id)
        if expense is None:
            messagebox.showerror("Not Found", "Expense not found.")
            return
        dialog = ExpenseDialog(self, expense=expense)
        if dialog.result:
            crud.update_expense(
                db_id,
                date=dialog.result.date,
                merchant=dialog.result.merchant,
                amount=dialog.result.amount,
                category=dialog.result.category,
                payment_method=dialog.result.payment_method,
            )
            self.refresh_table()

    def on_delete_expense(self):
        db_id = self._selected_db_id()
        if db_id is None:
            return
        expense = crud.get_expense_by_id(db_id)
        if expense is None:
            return
        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete:\n{expense.merchant}  ${expense.amount:.2f}  ({expense.date})?"
        ):
            crud.delete_expense(db_id)
            self.refresh_table()

    def on_upload_receipt(self):
        try:
            from ocr import extract_text_from_image, is_tesseract_available
            from parser import parse_receipt_text
        except ImportError as exc:
            messagebox.showerror("Missing Dependency",
                                 f"{exc}\n\nRun: pip install pytesseract Pillow")
            return
        if not is_tesseract_available():
            messagebox.showerror("Tesseract Not Found",
                                 "Install: brew install tesseract")
            return
        path = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tiff *.bmp"), ("All", "*.*")])
        if not path:
            return
        try:
            raw_text = extract_text_from_image(path)
        except Exception as exc:
            messagebox.showerror("OCR Error", str(exc))
            return
        if not raw_text.strip():
            messagebox.showwarning("OCR Warning", "No text extracted from image.")
            return
        parsed = parse_receipt_text(raw_text)
        stub   = Expense(
            date=parsed["date"] or date.today(),
            merchant=parsed["merchant"] or "",
            amount=parsed["amount"] or 0.01,
            category=parsed["category"] or "Uncategorized",
            payment_method="other", source="ocr",
        )
        dialog = ExpenseDialog(self, expense=stub)
        if dialog.result:
            dialog.result.source = "ocr"
            crud.insert_expense(dialog.result)
            self.refresh_table()

    def on_generate_report(self):
        expenses = crud.get_all_expenses()
        report   = analytics.format_report(expenses)
        win      = tk.Toplevel(self)
        win.title("Analytics Report")
        win.geometry("520x520")
        win.configure(bg=T["BG"])
        text = tk.Text(win, wrap="word", font=("Courier New", 10),
                       bg=T["PANEL"], fg=T["TEXT"], relief="flat",
                       insertbackground=T["TEXT"], bd=12)
        text.pack(fill="both", expand=True, padx=8, pady=8)
        text.insert("1.0", report)
        text.config(state="disabled")

    def on_open_calendar(self):
        CalendarScreen(self)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def launch_gui():
    app = ExpenseTrackerApp()
    app.mainloop()
