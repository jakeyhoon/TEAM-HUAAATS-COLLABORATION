"""Render a 60s vertical (1080x1920) captioned explainer: 'What If the Moon Just Vanished?'"""
import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_CAP = ImageFont.truetype(FONT, 78)
F_TAG = ImageFont.truetype(FONT, 44)
F_BIG = ImageFont.truetype(FONT, 120)
YEL = (255, 214, 64)
random.seed(7)

# ---------- shared assets ----------
STARS = [(random.randrange(W), random.randrange(H), random.choice([1, 1, 2, 2, 3]), random.random() * 6.28)
         for _ in range(420)]

def sky(top=(6, 8, 24), bottom=(18, 22, 54)):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img

SKY = sky()

def draw_stars(d, t, bright=1.0):
    for x, y, r, ph in STARS:
        b = int(255 * bright * (0.55 + 0.45 * math.sin(t * 2 + ph)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 20)))

def moon_img(R):
    m = Image.new("RGBA", (R * 2 + 120, R * 2 + 120), (0, 0, 0, 0))
    glow = Image.new("RGBA", m.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([30, 30, m.size[0] - 30, m.size[1] - 30], fill=(220, 225, 255, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    m.alpha_composite(glow)
    d = ImageDraw.Draw(m)
    c = 60
    d.ellipse([c, c, c + 2 * R, c + 2 * R], fill=(236, 236, 228, 255))
    rnd = random.Random(3)
    for _ in range(14):
        cr = rnd.randint(R // 14, R // 5)
        a, dist = rnd.random() * 6.28, rnd.random() * (R - cr)
        cx, cy = c + R + math.cos(a) * dist, c + R + math.sin(a) * dist
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(200, 200, 192, 255))
    return m

MOON = moon_img(190)
MOON_SM = moon_img(110)

def skyline(d, base, col=(10, 12, 20)):
    rnd = random.Random(11)
    x = 0
    while x < W:
        bw, bh = rnd.randint(60, 150), rnd.randint(120, 520)
        d.rectangle([x, base - bh, x + bw, H], fill=col)
        x += bw + rnd.randint(0, 12)
    # Marina-Bay-style three towers + deck, generic silhouette
    for i in range(3):
        bx = 640 + i * 110
        d.polygon([(bx, base), (bx + 60, base), (bx + 50, base - 640), (bx + 10, base - 640)], fill=col)
    d.rectangle([620, base - 680, 990, base - 640], fill=col)

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

# ---------- caption rendering ----------
def caption(img, text, t_in, t, y=1380, hi=(), font=F_CAP, maxw=940):
    """Pop-in caption; words in `hi` render yellow."""
    if t < t_in:
        return
    k = ease((t - t_in) / 0.25)
    d = ImageDraw.Draw(img)
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if d.textlength(test, font=font) > maxw and cur:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    lh = font.size + 18
    y0 = y - (len(lines) * lh) // 2 + int((1 - k) * 40)
    for li, line in enumerate(lines):
        lw = d.textlength(" ".join(line), font=font)
        x = (W - lw) / 2
        for w in line:
            col = YEL if w.strip(".,!?:").lower() in hi else (255, 255, 255)
            col = tuple(int(c * k) for c in col)
            d.text((x, y0 + li * lh), w, font=font, fill=col, stroke_width=7, stroke_fill=(0, 0, 0))
            x += d.textlength(w + " ", font=font)

def tag(img, text, t):
    """Small location/label chip at top."""
    d = ImageDraw.Draw(img)
    tw = d.textlength(text, font=F_TAG)
    x = (W - tw) / 2
    d.rounded_rectangle([x - 28, 150, x + tw + 28, 230], radius=40, fill=(0, 0, 0))
    d.text((x, 162), text, font=F_TAG, fill=YEL)

# ---------- scenes: (start, end, fn) ----------
def s_hook(t, lt):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    draw_stars(d, t)
    skyline(d, 1900)
    if lt < 2.0:
        img.paste(MOON, (W // 2 - MOON.width // 2, 420), MOON)
    elif lt < 2.25:  # flash
        f = 1 - (lt - 2.0) / 0.25
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.8 * f)
    caption(img, "Tonight, the Moon disappears.", 0.2, lt, hi={"moon"})
    caption(img, "No explosion. It's just gone.", 2.3, lt, y=1560, hi={"gone"})
    return img

def s_dark(t, lt):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    draw_stars(d, t, bright=1 - 0.4 * ease(lt / 4))
    skyline(d, 1900, col=(4, 5, 9))
    # person silhouette on a rooftop
    px, py = 300, 1500
    d.ellipse([px - 30, py - 160, px + 30, py - 100], fill=(0, 0, 0))
    d.rounded_rectangle([px - 40, py - 100, px + 40, py + 40], radius=20, fill=(0, 0, 0))
    d.rectangle([0, py + 40, W, H], fill=(0, 0, 0))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(img, dark, 0.35 * ease(lt / 4))
    caption(img, "Look up.", 0.2, lt, y=1000)
    caption(img, "The night just got darker.", 1.6, lt, y=1180, hi={"darker"})
    caption(img, "No more full moon. Ever.", 3.8, lt, y=1360, hi={"ever"})
    return img

def wave_scene(lt, amp_from, amp_to, label):
    img = Image.new("RGB", (W, H), (120, 180, 220))
    d = ImageDraw.Draw(img)
    for y in range(0, 900):
        c = int(150 + 80 * y / 900)
        d.line([(0, y), (W, y)], fill=(c - 60, c - 20, 255))
    amp = amp_from + (amp_to - amp_from) * ease((lt - 1.5) / 3)
    level = 1000 + amp * math.sin(lt * 1.6)
    # shore
    d.polygon([(0, 1300), (W, 1050), (W, H), (0, H)], fill=(222, 196, 140))
    pts = [(x, level + 18 * math.sin(x / 70 + lt * 3)) for x in range(0, W + 20, 20)]
    d.polygon(pts + [(W, H), (0, H)], fill=(20, 90, 160))
    # tide gauge
    d.rectangle([880, 600, 920, 1500], fill=(255, 255, 255))
    for k in range(0, 900, 100):
        d.line([(860, 600 + k), (940, 600 + k)], fill=(0, 0, 0), width=4)
    d.rectangle([880, level, 920, 1500], fill=(255, 90, 90))
    return img

def s_tides(t, lt):
    img = wave_scene(lt, 260, 85, "")
    tag(img, "TIDES", t)
    caption(img, "Tides shrink to about 1/3 of their size", 0.3, lt, y=1560, hi={"1/3"})
    caption(img, "Only the Sun is pulling the oceans now.", 4.8, lt, y=1760, hi={"sun"}, font=ImageFont.truetype(FONT, 62))
    return img

def s_chekjawa(t, lt):
    img = Image.new("RGB", (W, H), (70, 140, 190)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 700], fill=(150, 200, 235))
    d.rectangle([0, 700, W, 780], fill=(40, 90, 50))  # mangrove line
    for x in range(0, W, 40):
        d.ellipse([x - 30, 640, x + 40, 730], fill=(30, 80, 40))
    # flats: exposed before, covered after
    cover = ease((lt - 1) / 2.5)
    d.rectangle([0, 780, W, H], fill=(196, 170, 120))
    rnd = random.Random(5)
    for _ in range(26):
        x, y = rnd.randrange(60, W - 60), rnd.randrange(900, 1850)
        kind = rnd.random()
        if kind < 0.4:   # sea star
            for a in range(5):
                ang = a * 1.2566 + 0.3
                d.line([(x, y), (x + 34 * math.cos(ang), y + 34 * math.sin(ang))], fill=(230, 90, 60), width=14)
        elif kind < 0.7:  # crab
            d.ellipse([x - 22, y - 14, x + 22, y + 14], fill=(200, 60, 40))
        else:  # seagrass
            for k in range(4):
                d.line([(x + k * 8, y), (x + k * 8 + 6, y - 50)], fill=(60, 140, 60), width=6)
    water = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(water).rectangle([0, 780, W, H], fill=(30, 100, 160, int(200 * cover)))
    img = img.convert("RGBA"); img.alpha_composite(water); img = img.convert("RGB")
    tag(img, "CHEK JAWA, PULAU UBIN", t)
    caption(img, "The tidal flats barely uncover.", 0.4, lt, y=1250, hi={"barely"})
    caption(img, "Life here loses its rhythm.", 3.8, lt, y=1450, hi={"rhythm"})
    return img

CORALS = [(random.randrange(80, W - 80), random.randrange(1350, 1800)) for _ in range(18)]
EGGS = [(random.randrange(60, W - 60), random.random() * 900, random.random()) for _ in range(160)]

def s_coral(t, lt):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):
        c = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 10 * c), int(70 - 40 * c), int(130 - 70 * c)))
    for x, y in CORALS:
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.35
            d.line([(x, y), (x + 90 * math.cos(a), y + 90 * math.sin(a))], fill=(240, 120, 150), width=16)
    freeze = 4.2
    tt = min(lt, freeze)
    for ex, ey, ph in EGGS:
        yy = 1700 - ((ey + tt * 160 + ph * 300) % 1500)
        col = (255, 150, 190)
        if lt > freeze and int(lt * 10) % 2 == 0:  # glitch flicker
            ex += random.randint(-20, 20)
            col = (120, 120, 120)
        d.ellipse([ex - 9, yy - 9, ex + 9, yy + 9], fill=col)
    if lt > freeze:
        img = Image.blend(img, img.convert("L").convert("RGB"), ease((lt - freeze) / 0.8))
    tag(img, "SINGAPORE'S REEFS", t)
    caption(img, "Corals spawn together a few nights after a full moon.", 0.3, lt, y=560, hi={"full", "moon."})
    caption(img, "No moon. No signal.", 4.4, lt, y=860, hi={"signal."})
    return img

def s_tilt(t, lt):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    draw_stars(d, t, 0.7)
    cx, cy, R = W // 2, 700, 240
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(40, 110, 200))
    rnd = random.Random(2)
    for _ in range(7):
        a, r = rnd.random() * 6.28, rnd.random() * R * 0.7
        x, y, s = cx + r * math.cos(a), cy + r * math.sin(a), rnd.randint(50, 110)
        d.ellipse([x - s, y - s * 0.7, x + s, y + s * 0.7], fill=(70, 160, 90))
    wob = 23.4 + (6 + 22 * ease((lt - 2) / 5)) * math.sin(lt * 2.2) if lt > 2 else 23.4
    a = math.radians(wob)
    L = 380
    d.line([(cx - L * math.sin(a), cy + L * math.cos(a)), (cx + L * math.sin(a), cy - L * math.cos(a))],
           fill=(255, 214, 64), width=10)
    d.text((cx + 150, cy + 250), f"TILT {abs(wob):4.1f}°", font=F_TAG, fill=(255, 255, 255))
    caption(img, "The Moon keeps Earth's tilt steady.", 0.3, lt, y=1230, hi={"steady."})
    caption(img, "Without it, the tilt can drift over millions of years.", 3.0, lt, y=1480,
            hi={"drift"}, font=ImageFont.truetype(FONT, 62))
    caption(img, "Seasons could swing to extremes.", 6.2, lt, y=1720, hi={"extremes."}, font=ImageFont.truetype(FONT, 62))
    return img

def s_day(t, lt):
    img = Image.new("RGB", (W, H), (14, 14, 30)); d = ImageDraw.Draw(img)
    hours = 19 + 5 * ease(lt / 3.5)
    ago = 1.4 * (1 - ease(lt / 3.5))
    cx, cy, R = W // 2, 760, 300
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255), width=14)
    for k in range(12):
        a = k * math.pi / 6
        d.line([(cx + (R - 40) * math.sin(a), cy - (R - 40) * math.cos(a)),
                (cx + (R - 10) * math.sin(a), cy - (R - 10) * math.cos(a))], fill=(255, 255, 255), width=8)
    spin = lt * 9 if lt < 3.5 else 3.5 * 9
    d.line([(cx, cy), (cx + 240 * math.sin(spin), cy - 240 * math.cos(spin))], fill=YEL, width=14)
    d.line([(cx, cy), (cx + 160 * math.sin(spin / 12), cy - 160 * math.cos(spin / 12))], fill=(255, 255, 255), width=18)
    txt = f"1 day = {hours:4.1f} h"
    d.text(((W - d.textlength(txt, font=F_BIG)) / 2, 1110), txt, font=F_BIG, fill=(255, 255, 255))
    sub = f"{ago:3.1f} billion years ago" if ago > 0.05 else "today"
    d.text(((W - d.textlength(sub, font=F_TAG)) / 2, 1260), sub, font=F_TAG, fill=(180, 180, 200))
    caption(img, "The Moon has been stretching our days.", 0.3, lt, y=1480, hi={"stretching"})
    caption(img, "Without it, Earth's spin stops slowing down.", 3.6, lt, y=1700, hi={"stops"},
            font=ImageFont.truetype(FONT, 62))
    return img

def s_twist(t, lt):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    draw_stars(d, t)
    # earth bottom-left, moon top-right, ruler between
    d.ellipse([-200, 760, 240, 1200], fill=(40, 110, 200))
    drift = 70 * ease((lt - 2) / 4)
    mx, my = 640 + drift, 360 - drift * 0.9
    img.paste(MOON_SM, (int(mx), int(my)), MOON_SM)
    d = ImageDraw.Draw(img)
    x0, y0 = 220, 900
    x1, y1 = mx + MOON_SM.width // 2 - 60, my + MOON_SM.height // 2 + 60
    d.line([(x0, y0), (x1, y1)], fill=YEL, width=8)
    n = 18
    for k in range(1, n):
        px, py = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
        d.line([(px - 14, py - 14), (px + 14, py + 14)], fill=YEL, width=5)
    caption(img, "Plot twist:", 0.2, lt, y=1330, hi={"twist:"})
    caption(img, "The Moon is already leaving.", 1.2, lt, y=1500, hi={"leaving."})
    caption(img, "+3.8 cm every year", 3.0, lt, y=1740, hi={"+3.8", "cm"}, font=F_BIG)
    return img

SCENES = [(0, 4.5, s_hook), (4.5, 11, s_dark), (11, 19, s_tides), (19, 27, s_chekjawa),
          (27, 35, s_coral), (35, 45, s_tilt), (45, 53, s_day), (53, 60, s_twist)]
TOTAL = 60

def frame(t):
    for s, e, fn in SCENES:
        if s <= t < e:
            img = fn(t, t - s)
            # fade in/out 0.3s at scene boundaries
            edge = min(t - s, e - t)
            if edge < 0.3 and not (s == 0 and t - s < 0.3 and False):
                img = Image.blend(Image.new("RGB", (W, H)), img, edge / 0.3)
            return img
    return Image.new("RGB", (W, H))

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                       "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)
for i in range(TOTAL * FPS):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 300 == 0:
        print(f"{i / FPS:.0f}s", flush=True)
ff.stdin.close(); ff.wait()
print("done", ff.returncode)
