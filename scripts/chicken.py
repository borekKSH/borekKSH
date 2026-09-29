"""
Generuje assets/chicken.svg: kurczak zjadajacy ziarenka po realnej siatce
kontrybucji GitHuba (borekKSH), zamiast standardowego weza.

Dane: publiczny fragment https://github.com/users/<user>/contributions
(dokladnie to, co widzi kazdy odwiedzajacy profil - zero tokenu, zero
sekretu). Jesli pobranie sie nie uda (chwilowy problem sieci/GitHuba),
skrypt konczy bez zapisu - poprzedni plik zostaje.

Uruchamiane co 6h przez .github/workflows/chicken.yml.
"""
import re
import sys
import urllib.request
from datetime import datetime, timezone

USER = "borekKSH"
WEEKS = 52
CELL = 14
PAD = 10
GRAIN_R = 2.6
SEC_PER_CELL = 0.09

CONTRIB_URL = f"https://github.com/users/{USER}/contributions"


def fetch_calendar():
    req = urllib.request.Request(CONTRIB_URL, headers={"User-Agent": "chicken-banner-bot"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    cells = re.findall(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"',
        html,
    )
    if not cells:
        cells = re.findall(
            r'data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"',
            html,
        )
        cells = [(d, lvl) for lvl, d in cells]
    if not cells:
        raise RuntimeError("nie znaleziono komorek kalendarza kontrybucji")
    by_date = {d: int(lvl) for d, lvl in cells}
    return by_date


def last_n_weeks_grid(by_date, weeks=WEEKS):
    """Zwraca siatke [tydzien][dzien_tygodnia(0=Pn..6=Nd)] = poziom (0-4),
    ostatnie `weeks` pelnych tygodni konczacych sie dzisiaj (wg UTC)."""
    today = datetime.now(timezone.utc).date()
    monday = today.fromordinal(today.toordinal() - today.weekday())  # ten tydzien, poniedzialek
    start = monday.fromordinal(monday.toordinal() - 7 * (weeks - 1))

    grid = [[0] * 7 for _ in range(weeks)]
    for w in range(weeks):
        for d in range(7):
            day = start.fromordinal(start.toordinal() + w * 7 + d)
            grid[w][d] = by_date.get(day.isoformat(), 0)
    return grid, start, today


def boustrophedon_path(weeks=WEEKS):
    """Kolejnosc odwiedzin (tydzien,dzien): calym wierszem (dniem tygodnia)
    przez wszystkie tygodnie w prawo, potem nizej i w lewo - jak maszyna do
    pisania. Dlugie, plynne odcinki poziome pasujace do szerokiej planszy,
    zamiast szybkiego skakania gora-dol w waskich kolumnach."""
    order = []
    for d in range(7):
        weeks_range = range(weeks) if d % 2 == 0 else range(weeks - 1, -1, -1)
        for w in weeks_range:
            order.append((w, d))
    return order


LEVEL_COLOR = {1: "#5a4520", 2: "#8a6620", 3: "#c98a20", 4: "#e2a33d"}


def build_svg(grid, order, generated_at) -> str:
    W = PAD * 2 + WEEKS * CELL
    H = PAD * 2 + 7 * CELL + 34  # + terminal line

    def cell_xy(w, d):
        return PAD + w * CELL, PAD + d * CELL

    cells_svg = []
    grains_svg = []
    n = len(order)
    for i, (w, d) in enumerate(order):
        x, y = cell_xy(w, d)
        level = grid[w][d]
        cells_svg.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL-2}" height="{CELL-2}" rx="2" '
            f'fill="#161310" stroke="#242018" stroke-width="1"/>'
        )
        if level > 0:
            cx, cy = x + (CELL - 2) / 2, y + (CELL - 2) / 2
            color = LEVEL_COLOR[level]
            t0 = i / n
            eps = 0.004
            keytimes = f"0;{max(t0-eps,0):.4f};{t0:.4f};{min(t0+eps,1):.4f};1"
            grains_svg.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{GRAIN_R + level*0.5:.1f}" fill="{color}">'
                f'<animate attributeName="opacity" values="1;1;1;0;0" '
                f'keyTimes="{keytimes}" dur="{n*SEC_PER_CELL:.2f}s" repeatCount="indefinite"/>'
                f"</circle>"
            )

    # sciezka ruchu kurczaka (srodki komorek), jedna linia lamana
    pts = []
    for (w, d) in order:
        x, y = cell_xy(w, d)
        pts.append(f"{x + (CELL-2)/2:.1f},{y + (CELL-2)/2:.1f}")
    motion_path = "M " + " L ".join(pts)
    keytimes_motion = ";".join(f"{i/(n-1):.5f}" for i in range(n))
    dur = n * SEC_PER_CELL

    # kierunek jazdy: wiersz parzysty -> w prawo (skala 1,1), nieparzysty -> w lewo (skala -1,1)
    # zeby dziob nie patrzyl w prawo, gdy kurczak faktycznie idzie w lewo
    row_starts = [r * WEEKS / n for r in range(7)]
    flip_keytimes = ";".join(f"{t:.5f}" for t in row_starts)
    flip_values = ";".join("1,1" if r % 2 == 0 else "-1,1" for r in range(7))

    eaten = sum(1 for w in range(WEEKS) for d in range(7) if grid[w][d] > 0)
    total = WEEKS * 7

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="'Fira Code','SF Mono',Consolas,monospace">
  <rect width="{W}" height="{H}" fill="#0a0a0a"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="#2a2a2a"/>

  {''.join(cells_svg)}
  {''.join(grains_svg)}

  <g>
    <animateMotion path="{motion_path}" keyTimes="{keytimes_motion}" dur="{dur:.2f}s" repeatCount="indefinite" calcMode="linear"/>
    <g>
      <animateTransform attributeName="transform" type="scale" values="{flip_values}" keyTimes="{flip_keytimes}" dur="{dur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="-6;6;-6" keyTimes="0;0.5;1" dur="0.4s" repeatCount="indefinite"/>
        <ellipse rx="5.5" ry="4.5" fill="#e6e6e6" stroke="#8a8a8a" stroke-width="0.8"/>
        <circle cx="3.2" cy="-2.4" r="2.6" fill="#e6e6e6" stroke="#8a8a8a" stroke-width="0.8"/>
        <path d="M6.2,-2.4 L9.4,-1.7 L6.2,-1.0 Z" fill="#e2a33d"/>
        <circle cx="2.6" cy="-3.0" r="0.55" fill="#141414"/>
        <path d="M2.5,1.2 C1.8,2.6 4.2,2.6 3.4,1.2" fill="none" stroke="#e2a33d" stroke-width="0.9"/>
      </g>
    </g>
  </g>

  <g transform="translate({PAD},{H-16})">
    <text x="0" y="0" fill="#8a8a8a" font-size="10.5">
      <tspan fill="#e2a33d">$</tspan> chicken --eat-grid &#183; {eaten}/{total} niepustych dni w ostatnich {WEEKS} tyg. &#183; {generated_at}
    </text>
  </g>
</svg>
"""


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        by_date = fetch_calendar()
    except Exception as e:
        print(f"pominieto: nie udalo sie pobrac kalendarza kontrybucji ({e})", file=sys.stderr)
        return

    grid, start, today = last_n_weeks_grid(by_date, WEEKS)
    order = boustrophedon_path(WEEKS)
    svg = build_svg(grid, order, generated_at)

    import os
    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "chicken.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out_path} (okno {start} .. {today})")


if __name__ == "__main__":
    main()
