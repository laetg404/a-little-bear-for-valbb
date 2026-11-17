import math
import random
import turtle
import tkinter as tk

# Un osito para ti ♡
# ESPACIO: pausa/continuar | ESC: salir
#
# Se usa turtle para la ventana, el teclado y el temporizador, y el canvas
# de Tk (que turtle ya trae) para dibujar: así los degradados, las curvas
# suaves y la animación van fluidos.

W, H = 1000, 700
FPS = 30
random.seed(24)

screen = turtle.Screen()
screen.setup(W, H)
screen.title("Un osito para ti ♡")
screen.bgcolor("#FBE9EC")
screen.tracer(0, 0)
cv = screen.getcanvas()

frame = 0
paused = False
running = True
CUR = "static"          # etiqueta con la que se dibuja ("static" o "anim")

# ================================================================ AJUSTES DE POSICIÓN DE LA CABEZA
# Cambia estos números a tu gusto (las unidades son píxeles; + sube, - baja).
HEAD_DY = -32     # posición vertical de TODA la cabeza (orejas, cara y ojos)
BOW_Y = -74       # altura del moño (más negativo = más abajo)
# =====================================================================

# ------------------------------------------------------------------ paleta
FUR = "#B77B52"
FUR_D = "#8B5A3A"
FUR_L = "#CF9A6E"
CREAM = "#EDCFAB"
CREAM_D = "#D8B38B"
PINK = "#E8788F"
PINK_D = "#B84A64"
INK = "#3E2620"

LETTERS = "Valbb"
# (letra, x del nudo, y del nudo, fase, velocidad, escala, color, mano)
BALLOONS = [
    (LETTERS[0], -300, 105, 0.0, 0.90, 1.05, "#F28DA6", 0),
    (LETTERS[1], -175, 190, 1.7, 0.75, 0.95, "#7DB7E8", 0),
    (LETTERS[2],  170, 190, 2.8, 0.85, 1.00, "#F7CD5B", 1),
    (LETTERS[3],  285, 125, 4.2, 1.00, 1.00, "#B79AE0", 1),
    (LETTERS[4],  385,  50, 5.0, 0.70, 0.90, "#7FD1B0", 1),
]
HAND_OFFSETS = {"Va": [-4, 3], "lbb": [-5, 0, 5]}

# ---------------------------------------------------------------- utilidades
def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))

def shade(c, t):
    return mix(c, "#000000", t)

def tint(c, t):
    return mix(c, "#FFFFFF", t)

OY = 0.0                         # desplazamiento vertical temporal (cabeza)

def _flat(pts):
    out = []
    for x, y in pts:
        out += [x, -(y + OY)]   # el canvas de turtle tiene la Y invertida
    return out

def poly(pts, fill="", outline="", w=1, smooth=False):
    return cv.create_polygon(_flat(pts), fill=fill, outline=outline,
                             width=w, smooth=smooth, tags=CUR)

def ellpts(cx, cy, rx, ry, rot=0.0, n=40, egg=0.0):
    r = math.radians(rot)
    c, s = math.cos(r), math.sin(r)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        px = rx * math.sin(t) * (1 + egg * math.cos(t))
        py = ry * math.cos(t)
        pts.append((cx + px * c - py * s, cy + px * s + py * c))
    return pts

def ell(cx, cy, rx, ry, fill="", outline="", w=1, rot=0.0, n=40):
    if rot == 0:
        cy += OY
        return cv.create_oval(cx - rx, -(cy + ry), cx + rx, -(cy - ry),
                              fill=fill, outline=outline, width=w, tags=CUR)
    return poly(ellpts(cx, cy, rx, ry, rot, n), fill, outline, w)

def line(pts, color, w=2, smooth=True):
    return cv.create_line(_flat(pts), fill=color, width=w, smooth=smooth,
                          capstyle="round", joinstyle="round", tags=CUR)

def bez(p0, p1, p2, p3, n=18):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return pts

def spline(pts, closed=True, n=8):
    """Curva suave (Catmull-Rom) que pasa por los puntos dados."""
    m = len(pts)
    out = []
    for i in range(m if closed else m - 1):
        if closed:
            p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        else:
            p0 = pts[i - 1] if i > 0 else pts[0]
            p1, p2 = pts[i], pts[i + 1]
            p3 = pts[i + 2] if i + 2 < m else pts[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t
                       + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out

def sym(half):
    """Mitad derecha (de arriba a abajo, empezando y acabando en x=0) -> contorno completo."""
    return half + [(-x, y) for x, y in reversed(half[1:-1])]

def scale_pts(pts, cx, cy, k, dx=0.0, dy=0.0):
    return [(cx + (x - cx) * k + dx, cy + (y - cy) * k + dy) for x, y in pts]

def shaded(pts, cx, cy, base=FUR, k=0.93, dx=-3, dy=4, w=2.5):
    """Silueta con borde, sombra abajo-derecha y color base arriba-izquierda."""
    poly(pts, shade(base, .22), FUR_D, w)
    poly(scale_pts(pts, cx, cy, k, dx, dy), base)

def _dir(x, y, cx, cy, rng, jitter):
    dx, dy = x - cx, y - cy
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    j = rng.uniform(-jitter, jitter)
    c, s = math.cos(j), math.sin(j)
    return ux * c - uy * s, ux * s + uy * c

def tufts(pts, cx, cy, n, rin, rout, color, w, rng):
    """Mechoncitos que sobresalen del contorno (se dibujan ANTES del relleno)."""
    for _ in range(n):
        x, y = rng.choice(pts)
        ux, uy = _dir(x, y, cx, cy, rng, .45)
        L = rng.uniform(.6, 1.0) * rout
        line([(x - ux * rin, y - uy * rin), (x + ux * L, y + uy * L)], color, w, smooth=False)

def strokes(pts, cx, cy, n, lo, hi, color, w, rng):
    """Pelitos cortos hacia dentro desde el borde."""
    for _ in range(n):
        x, y = rng.choice(pts)
        ux, uy = _dir(x, y, cx, cy, rng, .35)
        L = rng.uniform(lo, hi)
        mx, my = x - ux * L * .5 - uy * 2, y - uy * L * .5 + ux * 2
        line([(x - ux * 2, y - uy * 2), (mx, my), (x - ux * L, y - uy * L)], color, w)

def text(x, y, s, color, font, anchor="center"):
    return cv.create_text(x, -y, text=s, fill=color, font=font,
                          anchor=anchor, tags=CUR)

def heart_pts(x, y, s, rot=0.0, n=48):
    r = math.radians(rot)
    c, sn = math.cos(r), math.sin(r)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        hx = 16 * math.sin(a) ** 3
        hy = (13 * math.cos(a) - 5 * math.cos(2 * a)
              - 2 * math.cos(3 * a) - math.cos(4 * a))
        hx, hy = hx * s, hy * s
        pts.append((x + hx * c - hy * sn, y + hx * sn + hy * c))
    return pts

def heart(x, y, s, color, outline="", w=1, rot=0.0):
    return poly(heart_pts(x, y, s, rot), color, outline, w)

def star(x, y, R, color, k=4):
    r = R * 0.28
    pts = []
    for i in range(2 * k):
        a = math.pi * i / k - math.pi / 2
        rad = R if i % 2 == 0 else r
        pts.append((x + rad * math.cos(a), y + rad * math.sin(a)))
    return poly(pts, color)

# ------------------------------------------------------------------- escena
def sky_color(t):
    stops = [(0.0, "#B9DBF2"), (0.5, "#F6E2EE"), (1.0, "#FFF0DC")]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0))
    return stops[-1][1]

def flower(x, y, s, petal):
    line([(x, y), (x, y - 13 * s)], "#8DB87B", 2, smooth=False)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        ell(x + 6 * s * math.cos(a), y + 6 * s * math.sin(a), 4.6 * s, 4.6 * s, petal)
    ell(x, y, 3.6 * s, 3.6 * s, "#F7D774")

def draw_background():
    # cielo en degradado
    n, top, bot = 50, 360, -280
    h = (top - bot) / n
    for i in range(n):
        y1 = top - i * h
        cv.create_rectangle(-520, -y1, 520, -(y1 - h) + 1,
                            fill=sky_color(i / (n - 1)), outline="", tags=CUR)
    # solecito suave
    base = sky_color((360 - 262) / 640)
    for rad, a in [(120, .18), (92, .30), (68, .50), (46, 1.0)]:
        ell(-425, 262, rad, rad, mix(base, "#FFF0B8", a))
    # colinas
    ell(-330, -330, 500, 130, "#D4E7C6")
    ell(380, -345, 520, 130, "#C8E0B8")
    ell(0, -525, 820, 255, "#B9D8A4", "#A9CC95", 2)
    # hierba
    for _ in range(95):
        x, y = random.uniform(-480, 480), random.uniform(-348, -284)
        line([(x, y), (x + random.uniform(-3, 3), y + random.uniform(7, 13))],
             random.choice(["#9CC48A", "#8FBA7C", "#A8CE95"]), 1.6, smooth=False)
    # flores
    petals = ["#F4A6B8", "#FFFFFF", "#F7C1CD", "#C7B5E8", "#F9D3A5"]
    placed = 0
    while placed < 16:
        x, y = random.uniform(-470, 470), random.uniform(-345, -290)
        if abs(x) < 150 and y > -322:
            continue
        flower(x, y, random.uniform(.8, 1.15), random.choice(petals))
        placed += 1

HEAD_HALF = [(0, 134), (42, 132), (80, 120), (104, 98), (115, 66), (116, 32), (121, 10),
             (108, -2), (94, -26), (64, -45), (28, -55), (0, -57)]
BODY_HALF = [(0, -86), (46, -90), (78, -108), (98, -146), (106, -190), (100, -232),
             (78, -262), (40, -278), (0, -282)]
BELLY_HALF = [(0, -130), (34, -138), (60, -170), (66, -212), (50, -252), (0, -268)]
MUZZLE_HALF = [(0, 28), (24, 26), (44, 14), (54, -6), (48, -30), (24, -44), (0, -48)]
NOSE_HALF = [(0, 32), (11, 32), (19, 26), (15, 16), (6, 9), (0, 7)]
def draw_bear():
    rng = random.Random(7)
    fur_mid = mix(FUR, FUR_D, .4)
    ell(0, -304, 150, 16, "#A3C58F")                       # sombra en el suelo

    # cuerpo rechoncho
    body = spline(sym(BODY_HALF))
    tufts(body, 0, -185, 16, 3, 5, FUR_D, 1.6, rng)
    shaded(body, 0, -185, k=.95, dx=-4, dy=4)
    strokes(body, 0, -185, 18, 7, 11, fur_mid, 1.3, rng)

    # barriguita
    belly = spline(sym(BELLY_HALF))
    poly(belly, CREAM, CREAM_D, 1.5)
    poly(scale_pts(belly, 0, -200, .84, -2, 3), tint(CREAM, .35))
    heart(0, -204, .62, PINK, PINK_D, 1.5)
    heart(-4, -199, .2, "#F7B3C2")

    # patas (delante del cuerpo)
    for sx in (-1, 1):
        fx, fy = sx * 64, -280
        shaded(ellpts(fx, fy, 56, 30, rot=-sx * 8, n=48), fx, fy, k=.9)
        ell(fx + sx * 2, fy - 6, 31, 17, CREAM, CREAM_D, 1.5, rot=-sx * 8)
        for dx in (-20, 0, 20):
            ell(fx + dx, fy + 20, 6.5, 6, CREAM, CREAM_D, 1)

    global OY
    OY = HEAD_DY                                           # --- empieza la cabeza
    # orejas
    for sx in (-1, 1):
        ex, ey = sx * 80, 112
        shaded(ellpts(ex, ey, 39, 37, n=36), ex, ey, k=.9)
        poly(ellpts(ex - sx * 3, ey - 4, 24, 22, n=28), "#C98563")
        poly(ellpts(ex - sx * 3, ey - 2, 21, 19, n=28), "#E3A47F")

    # cabeza
    head = spline(sym(HEAD_HALF))
    tufts(head, 0, 39, 18, 3, 5, FUR_D, 1.6, rng)
    shaded(head, 0, 39, k=.95, dx=-4, dy=5)
    poly(ellpts(-30, 92, 62, 26, rot=14, n=32), mix(FUR, FUR_L, .5))
    poly(ellpts(-36, 95, 40, 15, rot=14, n=30), FUR_L)
    strokes(head, 0, 39, 22, 8, 12, fur_mid, 1.3, rng)
    line([(-7, 131), (-3, 143), (6, 145), (13, 139)], FUR_D, 2.2)   # remolino

    # mejillas, hocico, nariz y boca
    for sx in (-1, 1):
        ell(sx * 74, -8, 16, 10, "#F0A3A0")
    muzzle = spline(sym(MUZZLE_HALF))
    poly(muzzle, CREAM, CREAM_D, 1.8)
    poly(scale_pts(muzzle, 0, -8, .8, -2, 3), tint(CREAM, .3))
    poly(spline(sym(NOSE_HALF)), INK, "#2A1812", 1)
    poly(ellpts(-6, 27, 6.5, 2.8, rot=-10, n=16), "#8C6D63")
    line([(0, 7), (0, -8)], INK, 2.6)
    line(bez((0, -8), (-6, -21), (-21, -21), (-29, -9)), INK, 2.6, smooth=False)
    line(bez((0, -8), (6, -21), (21, -21), (29, -9)), INK, 2.6, smooth=False)

    OY = 0.0                                               # --- termina la cabeza

    # moño con colitas
    by = BOW_Y
    for sx in (-1, 1):
        tail = spline([(sx * 4, by - 8), (sx * 20, by - 28), (sx * 30, by - 40),
                       (sx * 17, by - 44), (sx * 5, by - 24)])
        poly(tail, "#D85A78", PINK_D, 1.5)
    for sx in (-1, 1):
        lobe = spline([(0, by), (sx * 14, by + 14), (sx * 36, by + 19), (sx * 48, by + 5),
                       (sx * 43, by - 12), (sx * 24, by - 19), (sx * 9, by - 11)])
        poly(lobe, PINK, PINK_D, 2)
        poly(scale_pts(lobe, sx * 28, by, .55, -sx * 1, 2), tint(PINK, .25))
        line([(sx * 12, by), (sx * 36, by + 7)], PINK_D, 1.3)
        line([(sx * 12, by), (sx * 34, by - 7)], PINK_D, 1.3)
    ell(0, by, 10, 12, "#D85A78", PINK_D, 2)

def draw_static_text():
    font = ("Georgia", 22, "italic")
    text(1, 311, "A little something for you", "#FFFFFF", font)
    text(0, 313, "A little something for you", "#6F4E5A", font)
    font2 = ("Georgia", 17, "italic")
    text(1, -334, "For you, with all my love. ♡", "#E8F3DF", font2)
    text(0, -332, "For you, with all my love. ♡", "#8A4F63", font2)

# ---------------------------------------------------------- partes animadas
CLOUDS = [(-380, 160, 1.0, .25), (80, 255, .8, .18),
          (330, 140, 1.15, .30), (-60, 215, .65, .22)]

HEARTS = []
for _i in range(8):
    _side = -1 if _i % 2 else 1
    HEARTS.append((_side * random.uniform(235, 470), random.uniform(.5, 1.1),
                   random.uniform(0, 560), random.uniform(.35, .6),
                   random.choice(["#F4A6B8", "#F7C1CD", "#EE8FA8", "#F9D3A5"])))

SPARKS = []
while len(SPARKS) < 16:
    _x, _y = random.uniform(-470, 470), random.uniform(-200, 330)
    if abs(_x) < 200 and _y < 165:
        continue
    if _y > 292:
        continue
    SPARKS.append((_x, _y, random.uniform(5, 9), random.uniform(0, 6.28)))

def cloud(cx, cy, s):
    shapes = [(0, -6, 60, 16), (-32, 6, 26, 20), (2, 16, 34, 26), (34, 4, 26, 19)]
    for col, off in (("#E8E3F0", -5), ("#FFFFFF", 0)):
        for dx, dy, rx, ry in shapes:
            ell(cx + dx * s, cy + (dy + off) * s, rx * s, ry * s, col)

def draw_ambient(f):
    for x0, y, s, sp in CLOUDS:
        x = ((x0 + f * sp + 700) % 1400) - 700
        cloud(x, y, s)
    for x, y, r, ph in SPARKS:
        k = 0.35 + 0.65 * abs(math.sin(f * .07 + ph))
        star(x, y, r * k, "#F6CF72")
    for hx, sp, off, size, col in HEARTS:
        y = -230 + ((f * sp * 1.2 + off) % 560)
        x = hx + 16 * math.sin(f * .03 + off)
        heart(x, y, size, col, rot=10 * math.sin(f * .04 + off))

def draw_string(kx, ky, hand, phase):
    hx, hy = hand
    sway = 10 * math.sin(f_now() * .045 + phase)
    p0, p3 = (kx, ky), (hx, hy + 10)
    p1 = (p0[0] + (p3[0] - p0[0]) * .33 + sway * .5, p0[1] + (p3[1] - p0[1]) * .33)
    p2 = (p0[0] + (p3[0] - p0[0]) * .66 - sway * .3, p0[1] + (p3[1] - p0[1]) * .66)
    line(bez(p0, p1, p2, p3, 16), "#8E766B", 1.4, smooth=False)

def balloon(kx, ky, s, color, tilt, letter):
    rx, ry = 34 * s, 44 * s
    th = math.radians(tilt)
    c, sn = math.cos(th), math.sin(th)
    ccx = kx - sn * (ry + 3)
    ccy = ky + c * (ry + 3)

    def Wd(pts):                       # local -> mundo
        return [(ccx + x * c - y * sn, ccy + x * sn + y * c) for x, y in pts]

    dark, edge, light = shade(color, .25), shade(color, .4), tint(color, .38)
    poly(Wd(ellpts(0, 0, rx, ry, n=48, egg=.08)), dark, edge, 1.2)
    poly(Wd(ellpts(-.05 * rx, .05 * ry, rx * .93, ry * .93, n=48, egg=.08)), color)
    poly(Wd(ellpts(-.28 * rx, .30 * ry, rx * .50, ry * .45, rot=-30, n=32)), light)
    poly(Wd(ellpts(-.44 * rx, .52 * ry, rx * .13, ry * .24, rot=-35, n=20)), "#FFFFFF")
    poly(Wd([(0, -ry + 1), (-5 * s, -ry - 6 * s), (5 * s, -ry - 6 * s)]), dark, edge, 1)
    lx, ly = Wd([(0, .03 * ry)])[0]
    fs = max(12, int(30 * s))
    font = ("Georgia", fs, "bold")
    text(lx + 1.6, ly - 1.6, letter, shade(color, .38), font)
    text(lx, ly, letter, "#FFFFFF", font)

def arm(shoulder, hand):
    sx, sy = shoulder
    hx, hy = hand
    L = math.hypot(hx - sx, hy - sy)
    dx, dy = (hx - sx) / L, (hy - sy) / L
    nx, ny = -dy, dx
    if ny < 0:
        nx, ny = -nx, -ny

    def P(t, w):
        return (sx + dx * L * t + nx * w, sy + dy * L * t + ny * w)

    rs, rp = 31, 32
    caps = (-90, -60, -30, 0, 30, 60, 90)
    pts = []
    for a in caps:                                        # hombro redondeado
        r = math.radians(a)
        pts.append((sx + (nx * math.sin(r) - dx * math.cos(r)) * rs,
                    sy + (ny * math.sin(r) - dy * math.cos(r)) * rs))
    pts += [P(.35, 27), P(.68, 23)]                       # se afina en la muñeca
    for a in reversed(caps):                              # manita abultada
        r = math.radians(a)
        pts.append((hx + (dx * math.cos(r) + nx * math.sin(r)) * rp,
                    hy + (dy * math.cos(r) + ny * math.sin(r)) * rp))
    pts += [P(.68, -23), P(.35, -27)]
    sp = spline(pts, closed=True, n=6)
    cx, cy = (sx + hx) / 2, (sy + hy) / 2
    shaded(sp, cx, cy, k=.92, dx=-2, dy=3)
    line([P(t, 12) for t in (.2, .38, .55)], FUR_L, 7)
    for off in (-10, 10):                                 # deditos
        a = (hx + nx * off + dx * 10, hy + ny * off + dy * 10)
        b = (hx + nx * off + dx * 25, hy + ny * off + dy * 25)
        line([a, b], FUR_D, 1.8)

def draw_eyes(f):
    global OY
    OY = HEAD_DY
    gx = 1.5 * math.sin(f * .02)
    blink = (f % 150) < 5
    for sx in (-1, 1):
        x = sx * 40 + gx
        if blink:
            line([(x - 9, 49), (x, 41), (x + 9, 49)], INK, 3)
        else:
            ell(x, 46, 8.8, 10.8, "#2A1914")
            ell(x + 3, 51, 3.3, 3.3, "#FFFFFF")
            ell(x - 3, 41, 1.7, 1.7, "#FFFFFF")
    OY = 0.0

_frame_ref = [0]
def f_now():
    return _frame_ref[0]

def draw_frame(f):
    global CUR
    _frame_ref[0] = f
    CUR = "anim"
    cv.delete("anim")
    draw_ambient(f)

    hands = [(-150, -52 + 4 * math.sin(f * .06)),
             (150, -52 + 4 * math.sin(f * .06 + 1.3))]
    count = [0, 0]
    pos = []
    for letter, x0, y0, ph, spd, s, col, hand in BALLOONS:
        kx = x0 + 6 * math.sin(f * .025 + ph)
        ky = y0 + 11 * math.sin(f * .045 * spd + ph)
        tilt = 6 * math.sin(f * .04 + ph)
        offs = HAND_OFFSETS["Va"] if hand == 0 else HAND_OFFSETS["lbb"]
        ox = offs[count[hand]]
        count[hand] += 1
        hx, hy = hands[hand]
        draw_string(kx, ky, (hx + ox, hy), ph)
        pos.append((kx, ky, s, col, tilt, letter))
    for kx, ky, s, col, tilt, letter in pos:
        balloon(kx, ky, s, col, tilt, letter)

    arm((-86, -126), hands[0])
    arm((86, -126), hands[1])
    draw_eyes(f)

# ------------------------------------------------------------------ control
def animate():
    global frame
    if not running:
        return
    try:
        if not paused:
            frame += 1
            draw_frame(frame)
        screen.update()
        screen.ontimer(animate, 1000 // FPS)
    except (turtle.Terminator, tk.TclError):
        pass

def toggle_pause():
    global paused
    paused = not paused

def close():
    global running
    running = False
    try:
        screen.bye()
    except turtle.Terminator:
        pass

draw_background()
draw_bear()
draw_static_text()
draw_frame(0)
screen.update()
screen.listen()
screen.onkey(toggle_pause, "space")
screen.onkey(close, "Escape")
screen.ontimer(animate, 1000 // FPS)
try:
    screen.mainloop()
except turtle.Terminator:
    pass