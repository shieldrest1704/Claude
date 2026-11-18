"""Animated route map: a kid walking from home to school. Renders MP4 via ffmpeg."""
import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, S, FPS = 1280, 720, 2, 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "kid_to_school.mp4"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = lambda p, sz: ImageFont.truetype(p, sz * S)

GRASS, ROAD, BLOCK = (168, 214, 140), (92, 98, 110), (226, 222, 205)
ROUTE, KIDSHIRT = (255, 120, 40), (60, 120, 230)
RH = [160, 380, 600]; RV = [200, 520, 840, 1120]; RW = 44

def s(*v): return [x * S for x in v]

# ---------- static map ----------
def draw_house(d, x, y, body, roof):
    d.rectangle(s(x-30, y-20, x+30, y+25), fill=body, outline=(80,60,50), width=S*2)
    d.polygon(s(x-38, y-18, x, y-48, x+38, y-18), fill=roof, outline=(80,50,40))
    d.rectangle(s(x-7, y+3, x+7, y+25), fill=(120,80,50))
    d.rectangle(s(x+13, y-10, x+25, y+2), fill=(200,230,255), outline=(80,60,50))

def draw_tree(d, x, y, r=16):
    d.ellipse(s(x-r+3, y-r+6, x+r+3, y+r+6), fill=(120,170,100))
    d.ellipse(s(x-r, y-r, x+r, y+r), fill=(70,150,70), outline=(40,110,50), width=S*2)

def build_map():
    im = Image.new("RGB", (W*S, H*S), GRASS); d = ImageDraw.Draw(im)
    # sidewalks / blocks edges
    for y in RH: d.rectangle(s(0, y-RW/2-6, W, y+RW/2+6), fill=BLOCK)
    for x in RV: d.rectangle(s(x-RW/2-6, 0, x+RW/2+6, H), fill=BLOCK)
    for y in RH: d.rectangle(s(0, y-RW/2, W, y+RW/2), fill=ROAD)
    for x in RV: d.rectangle(s(x-RW/2, 0, x+RW/2, H), fill=ROAD)
    for y in RH:
        for x in range(0, W, 40): d.rectangle(s(x, y-1.5, x+20, y+1.5), fill=(240,240,240))
    for x in RV:
        for y in range(0, H, 40): d.rectangle(s(x-1.5, y, x+1.5, y+20), fill=(240,240,240))
    for x in RV:
        for y in RH: d.rectangle(s(x-RW/2, y-RW/2, x+RW/2, y+RW/2), fill=ROAD)
    # zebra crossings at the traffic light corner
    for i in range(6):
        d.rectangle(s(866, 362+i*7, 884, 365+i*7), fill="white")
        d.rectangle(s(822+i*7, 404, 825+i*7, 420), fill="white")
    # park (block x 520-840, y 380-600)
    d.rounded_rectangle(s(552, 412, 808, 568), radius=20*S, fill=(120,190,100))
    d.ellipse(s(640, 450, 740, 520), fill=(110,180,230), outline=(70,140,200), width=S*3)
    for (x, y) in [(580,440),(590,540),(780,440),(770,545),(700,550),(610,490)]: draw_tree(d, x, y)
    # houses & trees
    draw_house(d, 100, 655, (255,210,150), (200,70,60))           # HOME
    for (x, y, b, r) in [(280,670,(200,220,250),(90,110,170)), (420,670,(250,230,200),(150,90,60)),
                         (100,480,(230,200,240),(120,80,150)), (100,270,(255,240,180),(180,120,50)),
                         (650,670,(210,240,210),(70,130,80)), (980,670,(250,220,220),(170,60,80)),
                         (1200,480,(220,230,250),(80,90,140)), (980,270,(255,230,190),(160,100,60))]:
        draw_house(d, x, y, b, r)
    for (x, y) in [(40,540),(160,420),(40,320),(300,80),(400,250),(680,250),(700,90),(1200,280),
                   (1220,640),(900,520),(1050,450),(260,520),(1200,60),(60,60),(560,670),(780,670)]:
        draw_tree(d, x, y, 14)
    # bakery (block x 200-520, y 380-600)
    d.rectangle(s(400, 500, 490, 568), fill=(250,240,220), outline=(110,70,50), width=S*2)
    for i in range(6):
        d.rectangle(s(400+i*15, 486, 415+i*15, 502), fill=(230,80,90) if i % 2 == 0 else "white")
    d.text(s(445, 530), "BAKERY", font=font(FB, 11), fill=(110,70,50), anchor="mm")
    # school (block x 840-1120, y 0-160)
    d.rectangle(s(890, 40, 1070, 132), fill=(235,120,90), outline=(120,50,40), width=S*3)
    d.polygon(s(880, 42, 980, 8, 1080, 42), fill=(150,60,50))
    for xx in (905, 935, 1025, 1055):
        for yy in (55, 92): d.rectangle(s(xx-8, yy, xx+8, yy+16), fill=(210,235,255), outline=(120,50,40))
    d.rectangle(s(962, 96, 998, 132), fill=(110,70,40))
    d.text(s(980, 75), "SCHOOL", font=font(FB, 14), fill="white", anchor="mm")
    d.line(s(1095, 20, 1095, 135), fill=(80,80,80), width=S*3)
    d.polygon(s(1095, 22, 1120, 30, 1095, 38), fill=(240,60,60))
    return im

# ---------- route ----------
PTS = [(100, 640), (100, 600), (520, 600), (520, 380), (840, 380), (840, 160), (980, 160), (980, 134)]
SEG = [math.dist(a, b) for a, b in zip(PTS, PTS[1:])]
TOTAL = sum(SEG)
LIGHT_D = sum(SEG[:4]) - 18           # stop just before the corner
SPEED, PAUSE = 135.0, 2.0
T_INTRO, T_OUTRO = 2.0, 3.5
T_WALK = TOTAL / SPEED + PAUSE
DUR = T_INTRO + T_WALK + T_OUTRO

def dist_at(t):
    w = t - T_INTRO
    if w <= 0: return 0.0, False
    d1 = w * SPEED
    if d1 < LIGHT_D: return d1, False
    if w < LIGHT_D / SPEED + PAUSE: return LIGHT_D, True
    return min(TOTAL, (w - PAUSE) * SPEED), False

def point_at(dd):
    for (a, b), L in zip(zip(PTS, PTS[1:]), SEG):
        if dd <= L:
            f = dd / L if L else 0
            return (a[0] + (b[0]-a[0])*f, a[1] + (b[1]-a[1])*f), (b[0]-a[0], b[1]-a[1])
        dd -= L
    return PTS[-1], (0, -1)

def path_upto(dd):
    out, acc = [PTS[0]], 0
    for (a, b), L in zip(zip(PTS, PTS[1:]), SEG):
        if acc + L >= dd:
            out.append(point_at(dd)[0]); return out
        out.append(b); acc += L
    return out

STOPS = [("Home", 0, (100, 690)), ("Bakery", 470, (445, 590)), ("Park", 720, (680, 420)),
         ("Traffic light", LIGHT_D, (900, 440)), ("School!", TOTAL, (980, 20))]

# ---------- dynamic drawing ----------
def draw_kid(d, x, y, t, moving, dirx):
    ph = math.sin(t * 14) if moving else 0
    bob = abs(ph) * 2.5
    y -= bob
    d.ellipse(s(x-13, y+20+bob, x+13, y+27+bob), fill=(60,90,50))
    # legs
    d.line(s(x-5, y+8, x-5 - ph*5, y+22+bob), fill=(40,50,80), width=S*5)
    d.line(s(x+5, y+8, x+5 + ph*5, y+22+bob), fill=(40,50,80), width=S*5)
    # backpack (behind, toward back side)
    bx = x - 10*dirx if dirx else x + 11
    d.rounded_rectangle(s(bx-7, y-8, bx+7, y+10), radius=3*S, fill=(250,200,40), outline=(160,110,0), width=S)
    # body
    d.rounded_rectangle(s(x-10, y-10, x+10, y+12), radius=5*S, fill=KIDSHIRT, outline=(30,60,140), width=S)
    # arms
    d.line(s(x-10, y-6, x-14 + ph*4, y+6), fill=(250,205,170), width=S*4)
    d.line(s(x+10, y-6, x+14 - ph*4, y+6), fill=(250,205,170), width=S*4)
    # head
    d.ellipse(s(x-11, y-33, x+11, y-11), fill=(250,205,170), outline=(170,120,90), width=S)
    d.chord(s(x-12, y-35, x+12, y-15), 180, 360, fill=(90,55,30))
    ex = 2.5 * dirx
    d.ellipse(s(x-5+ex, y-24, x-2+ex, y-21), fill="black")
    d.ellipse(s(x+2+ex, y-24, x+5+ex, y-21), fill="black")
    d.arc(s(x-5+ex, y-22, x+5+ex, y-15), 20, 160, fill=(150,60,60), width=S*2)

def draw_light(d, green):
    x, y = 872, 345
    d.line(s(x, y, x, y+30), fill=(60,60,60), width=S*3)
    d.rounded_rectangle(s(x-9, y-34, x+9, y+2), radius=4*S, fill=(40,40,40))
    d.ellipse(s(x-6, y-31, x+6, y-19), fill=(240,50,50) if not green else (90,40,40))
    d.ellipse(s(x-6, y-15, x+6, y-3), fill=(60,230,90) if green else (40,80,50))

def label(d, text, x, y, a):
    f = font(FB, 15)
    tw = d.textlength(text, font=f) / S
    col = lambda c: tuple(int(255 + (v-255)*a) for v in c)
    d.rounded_rectangle(s(x - tw/2 - 10, y - 13, x + tw/2 + 10, y + 13), radius=12*S,
                        fill=col((255,255,255)), outline=col(ROUTE), width=S*2)
    d.text(s(x, y), text, font=f, fill=col((60,40,30)), anchor="mm")

def pin(d, x, y, color):
    d.ellipse(s(x-9, y-9, x+9, y+9), fill=color, outline="white", width=S*3)

def ease(u): u = max(0, min(1, u)); return u*u*(3-2*u)

def render(base, t, rng_conf):
    im = base.copy(); d = ImageDraw.Draw(im)
    dd, waiting = dist_at(t)
    w = t - T_INTRO
    green = not (waiting or (dd < LIGHT_D))
    draw_light(d, green)
    # cars on side roads
    for i, (lane, sp, off, colr) in enumerate([(1120+11, 110, 0, (230,60,60)), (200-11, -95, 300, (60,140,230)),
                                                (1120-11, -80, 500, (250,190,40))]):
        cy = (t * sp + off) % (H + 120) - 60
        x = lane
        d.rounded_rectangle(s(x-10, cy-18, x+10, cy+18), radius=5*S, fill=colr, outline=(40,40,40), width=S)
        d.rectangle(s(x-7, cy-8, x+7, cy+6), fill=(190,220,240))
    # planned route (faint dashed) + travelled route
    for (a, b) in zip(PTS, PTS[1:]):
        L = math.dist(a, b); n = int(L // 14)
        for k in range(n):
            if k % 2: continue
            f0, f1 = k*14/L, min(1, (k*14+8)/L)
            d.line(s(a[0]+(b[0]-a[0])*f0, a[1]+(b[1]-a[1])*f0, a[0]+(b[0]-a[0])*f1, a[1]+(b[1]-a[1])*f1),
                   fill=(255,255,255), width=S*4)
    tr = path_upto(dd)
    if len(tr) > 1:
        d.line([c*S for p in tr for c in p], fill=ROUTE, width=S*8, joint="curve")
    pin(d, *PTS[0], (60,170,90)); pin(d, *PTS[-1], (220,60,60))
    # stop labels pop in as passed
    for name, sd, (lx, ly) in STOPS:
        if name == "Home": a = ease(t / 0.6)
        else:
            reach = T_INTRO + (sd / SPEED if sd <= LIGHT_D else sd / SPEED + PAUSE)
            a = ease((t - reach + 0.2) / 0.4)
        if a > 0: label(d, name, lx, ly, a)
    # kid
    (kx, ky), (vx, vy) = point_at(dd)
    moving = 0 < w and not waiting and dd < TOTAL
    dirx = 1 if vx > 0 else (-1 if vx < 0 else 0)
    draw_kid(d, kx, ky - 14, t, moving, dirx)
    if waiting:
        d.text(s(kx - 30, ky - 64), "Wait for green!" if not green else "", font=font(FB, 14),
               fill=(200,30,30), anchor="mm", stroke_width=S*3, stroke_fill="white")
    # HUD
    frac = dd / TOTAL
    mins = 40 + 20 * frac
    clock = f"7:{int(mins):02d} AM" if mins < 60 else "8:00 AM"
    d.rounded_rectangle(s(20, 20, 290, 118), radius=14*S, fill=(255,255,255), outline=(200,200,200), width=S*2)
    d.text(s(36, 34), "WALK TO SCHOOL", font=font(FB, 15), fill=(90,90,90))
    d.text(s(36, 56), clock, font=font(FB, 28), fill=(40,40,40))
    d.text(s(36, 92), f"{frac*1.1:.2f} km of 1.10 km", font=font(FR, 13), fill=(90,90,90))
    d.rounded_rectangle(s(180, 66, 274, 78), radius=6*S, fill=(230,230,230))
    if frac > 0: d.rounded_rectangle(s(180, 66, 180 + 94*frac, 78), radius=6*S, fill=ROUTE)
    im = im.resize((W, H), Image.LANCZOS)
    # intro / outro overlays
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    if t < T_INTRO + 0.5:
        a = 1 - ease((t - 1.4) / 1.0)
        od.rectangle((0, 0, W, H), fill=(20, 30, 50, int(150*a)))
        od.text((W/2, H/2 - 20), "A Kid's Walk to School", font=ImageFont.truetype(FB, 54),
                fill=(255,255,255,int(255*a)), anchor="mm")
        od.text((W/2, H/2 + 40), "Home  →  Bakery  →  Park  →  Traffic light  →  School", font=ImageFont.truetype(FR, 24),
                fill=(255,230,200,int(255*a)), anchor="mm")
    t_end = T_INTRO + T_WALK
    if t > t_end:
        a = ease((t - t_end) / 0.6)
        for i in range(60):
            r = random.Random(i)
            cx = r.uniform(0, W); sp = r.uniform(120, 260)
            cy = -20 + (t - t_end) * sp + r.uniform(-200, 0)
            c = r.choice([(255,90,90), (255,200,40), (80,200,120), (80,150,255), (220,110,240)])
            ang = (t * r.uniform(2, 6)); sz = r.uniform(5, 9)
            od.polygon([(cx + sz*math.cos(ang + k*math.pi/2), cy + sz*0.6*math.sin(ang + k*math.pi/2)) for k in range(4)],
                       fill=c + (255,))
        bw, bh = 560, 120
        sc = 0.7 + 0.3 * ease((t - t_end) / 0.5)
        x0, y0 = W/2 - bw*sc/2, H/2 - bh*sc/2
        od.rounded_rectangle((x0, y0, x0 + bw*sc, y0 + bh*sc), radius=24, fill=(255,255,255,int(240*a)),
                             outline=ROUTE + (int(255*a),), width=5)
        od.text((W/2, H/2 - 18*sc), "Made it to school!", font=ImageFont.truetype(FB, int(40*sc)),
                fill=(50,40,30,int(255*a)), anchor="mm")
        od.text((W/2, H/2 + 28*sc), "1.1 km  ·  20 minutes  ·  right on time", font=ImageFont.truetype(FR, int(22*sc)),
                fill=(110,90,70,int(255*a)), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")

def main():
    base = build_map()
    n = int(DUR * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(render(base, i / FPS, None).tobytes())
    p.stdin.close(); p.wait()
    print(f"wrote {OUT}: {n} frames, {DUR:.1f}s")

if __name__ == "__main__":
    main()
