"""
Generuje assets/banner.svg: glowny baner profilu, w calosci wygenerowany
(nie recznie rysowany) - kurnik + wentylator zostaja stale, ale srodkowa
czesc to prawdziwy luk dnia dla Grabianowa (52.133N, 22.283E), liczony
rownaniem wschodu slonca (Wikipedia: "Sunrise equation"), bez zadnego
zewnetrznego API. Uruchamiane co 6h przez .github/workflows/banner.yml.
"""
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LAT = 52.133
LON = 22.283
TZ = ZoneInfo("Europe/Warsaw")
J2000 = 2451545.0

BROILERS = "50,000+"


def to_julian(dt_utc: datetime) -> float:
    return dt_utc.timestamp() / 86400.0 + 2440587.5


def from_julian(j: float) -> datetime:
    return datetime.fromtimestamp((j - 2440587.5) * 86400.0, tz=timezone.utc)


def sun_times(date_utc_noon: datetime, lat: float, lon: float):
    j_date = to_julian(date_utc_noon)
    n = math.floor(j_date - J2000 - 0.0009 + lon / 360.0 + 0.5) - lon / 360.0 + 0.0009
    j_star = J2000 + n

    def d(x):
        return math.radians(x)

    M = math.radians((357.5291 + 0.98560028 * (j_star - J2000)) % 360)
    C = 1.9148 * math.sin(M) + 0.0200 * math.sin(2 * M) + 0.0003 * math.sin(3 * M)
    lam = math.radians((math.degrees(M) + 102.9372 + C + 180) % 360)
    j_transit = j_star + 0.0053 * math.sin(M) - 0.0069 * math.sin(2 * lam)

    delta = math.asin(math.sin(lam) * math.sin(d(23.4397)))
    phi = math.radians(lat)
    cos_omega = (math.sin(d(-0.833)) - math.sin(phi) * math.sin(delta)) / (
        math.cos(phi) * math.cos(delta)
    )
    cos_omega = max(-1.0, min(1.0, cos_omega))
    omega = math.degrees(math.acos(cos_omega))

    j_rise = j_transit - omega / 360.0
    j_set = j_transit + omega / 360.0
    return from_julian(j_rise), from_julian(j_set)


def frac_of_day(dt_local: datetime) -> float:
    return (dt_local.hour * 3600 + dt_local.minute * 60 + dt_local.second) / 86400.0


def build_svg(now_local, sunrise_local, sunset_local) -> str:
    day_len = sunset_local - sunrise_local
    hh, rem = divmod(int(day_len.total_seconds()), 3600)
    mm = rem // 60

    # day-arc geometry, inside the translate(210,0) group, matching the
    # old ensemble-lines footprint: x in [0,480], ground at y=88, peak y=26
    X0, X1 = 0, 480
    GROUND = 88
    PEAK = 26
    rise_f = frac_of_day(sunrise_local)
    set_f = frac_of_day(sunset_local)
    now_f = frac_of_day(now_local)
    daytime = rise_f < now_f < set_f

    def x_of(f):
        return X0 + f * (X1 - X0)

    def y_on_arc(f):
        if f <= rise_f or f >= set_f:
            return GROUND
        t = (f - rise_f) / (set_f - rise_f)
        return GROUND - math.sin(t * math.pi) * (GROUND - PEAK)

    pts = []
    steps = 60
    for i in range(steps + 1):
        f = i / steps
        pts.append((x_of(f), y_on_arc(f)))
    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    sun_x, sun_y = x_of(now_f), y_on_arc(now_f)
    sun_color = "#e2a33d" if daytime else "#8a8a8a"

    rise_x = x_of(rise_f)
    set_x = x_of(set_f)

    status_line2 = (
        f"{BROILERS} broilers online · daylight {hh}h {mm:02d}m "
        f"({sunrise_local.strftime('%H:%M')}–{sunset_local.strftime('%H:%M')}) "
        f"· agents: scout·builder·refuter green"
    )
    cursor_x = 8 + int(len(status_line2) * 7.55)

    return f"""<svg width="900" height="220" viewBox="0 0 900 220" xmlns="http://www.w3.org/2000/svg" font-family="'Fira Code','SF Mono',Consolas,monospace">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#151310"/>
    </linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="0.4"/></filter>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">
      <path d="M26,0 L0,0 0,26" fill="none" stroke="#1c1a16" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="900" height="220" fill="url(#bg)"/>
  <rect width="900" height="220" fill="url(#grid)">
    <animateTransform attributeName="transform" type="translate" from="0 0" to="26 26" dur="9s" repeatCount="indefinite"/>
  </rect>
  <rect x="0.5" y="0.5" width="899" height="219" fill="none" stroke="#2a2a2a"/>

  <!-- coop silhouette, left -->
  <g transform="translate(40,40)" stroke="#5a5a5a" stroke-width="1.5" fill="none">
    <path d="M0,140 L0,70 L60,20 L120,70 L120,140 Z"/>
    <line x1="0" y1="140" x2="120" y2="140"/>
    <line x1="20" y1="140" x2="20" y2="95" />
    <line x1="20" y1="95" x2="45" y2="95"/>
    <line x1="45" y1="95" x2="45" y2="140"/>
    <g stroke="#e2a33d" stroke-width="1">
      <circle cx="60" cy="20" r="6" opacity="0">
        <animate attributeName="r" values="6;38" dur="3s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.65;0" dur="3s" repeatCount="indefinite"/>
      </circle>
      <circle cx="60" cy="20" r="6" opacity="0">
        <animate attributeName="r" values="6;38" dur="3s" begin="1.5s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.65;0" dur="3s" begin="1.5s" repeatCount="indefinite"/>
      </circle>
    </g>
    <circle cx="60" cy="45" r="14" stroke="#6a6a6a"/>
    <g transform="translate(60,45)" filter="url(#glow)">
      <g>
        <path d="M0,0 L0,-12 L4,-9 Z" fill="#e2a33d" stroke="none"/>
        <path d="M0,0 L12,0 L9,4 Z" fill="#6a6a6a" stroke="none"/>
        <path d="M0,0 L0,12 L-4,9 Z" fill="#6a6a6a" stroke="none"/>
        <path d="M0,0 L-12,0 L-9,-4 Z" fill="#6a6a6a" stroke="none"/>
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="5s" repeatCount="indefinite"/>
      </g>
      <circle r="2" fill="#e2a33d"/>
    </g>
  </g>

  <!-- live day arc: real sunrise/sunset for Grabianow, center-right -->
  <g transform="translate(210,0)" fill="none" stroke-linecap="round">
    <line x1="{X0}" y1="{GROUND}" x2="{X1}" y2="{GROUND}" stroke="#2a2a2a" stroke-width="1"/>
    <path d="{path_d}" stroke="#5a5a5a" stroke-width="1.6"/>
    <line x1="{rise_x:.1f}" y1="{GROUND-3}" x2="{rise_x:.1f}" y2="{GROUND+3}" stroke="#4a4a4a"/>
    <line x1="{set_x:.1f}" y1="{GROUND-3}" x2="{set_x:.1f}" y2="{GROUND+3}" stroke="#4a4a4a"/>
    <text x="{rise_x:.1f}" y="{GROUND+18}" fill="#6a6a6a" font-size="11" text-anchor="middle">{sunrise_local.strftime('%H:%M')}</text>
    <text x="{set_x:.1f}" y="{GROUND+18}" fill="#6a6a6a" font-size="11" text-anchor="middle">{sunset_local.strftime('%H:%M')}</text>
    <circle cx="{sun_x:.1f}" cy="{sun_y:.1f}" r="5" fill="{sun_color}" filter="url(#glow)">
      <animate attributeName="r" values="5;8;5" dur="2.2s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- terminal status line, bottom -->
  <g transform="translate(40,168)">
    <rect x="-4" y="-14" width="820" height="24" fill="#000" opacity="0.3"/>
    <text x="0" y="4" fill="#e2a33d" font-size="13">
      <tspan fill="#6a6a6a">$</tspan> status --farm --code
    </text>
    <text x="0" y="26" fill="#d9d9d9" font-size="13">{status_line2}</text>
    <rect x="{cursor_x}" y="14" width="8" height="14" fill="#e2a33d">
      <animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>
</svg>
"""


def main():
    now_local = datetime.now(TZ)
    noon_local = now_local.replace(hour=12, minute=0, second=0, microsecond=0)
    noon_utc = noon_local.astimezone(timezone.utc)
    sunrise_utc, sunset_utc = sun_times(noon_utc, LAT, LON)
    sunrise_local = sunrise_utc.astimezone(TZ)
    sunset_local = sunset_utc.astimezone(TZ)
    svg = build_svg(now_local, sunrise_local, sunset_local)

    import os
    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "banner.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out_path}")
    print(f"sunrise={sunrise_local} sunset={sunset_local} now={now_local}")


if __name__ == "__main__":
    main()
