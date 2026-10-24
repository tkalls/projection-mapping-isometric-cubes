"""Builds the figures in docs/img/ from the same geometry the piece runs on.

    python3 docs/make_diagrams.py <frames_dir>

<frames_dir> holds 1280x720 PNG renders straight out of TouchDesigner (the cube, the sphere).
Clip thumbnails come from ~/TD-Lab/corner_clips. Each figure is written as an SVG, then
rendered to a 2x PNG with headless Chrome so the fonts in docs/fonts/ are baked in.
Needs ffmpeg and Google Chrome. Everything else is plain Python.
"""
import base64, math, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = sys.argv[1] if len(sys.argv) > 1 else 'frames'
CLIPS = os.path.expanduser('~/TD-Lab/corner_clips')
OUT = os.path.join(HERE, 'img')
SRC = os.path.join(HERE, 'figures-src')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# palette: purples + hot orange
BG, GRID, PANEL, EDGE = '#110a1d', '#1c1230', '#251740', '#3a2763'
BORDER, INK, MUTED, DIM = '#6c4ab0', '#ede2ff', '#a996d8', '#6f5c99'
HOT, YEL, LAV = '#ff6a2b', '#ffe14d', '#b79cff'
CEIL, LEFT, RIGHT = '#9b7bff', HOT, YEL          # the three faces, the same in every figure
SANS, MONO = "'Space Grotesk', sans-serif", "'JetBrains Mono', monospace"


# ---------- helpers -------------------------------------------------------------------
def jpeg(path, crop='720:720:280:0', size=360, q=3, seek=None):
    fd, tmp = tempfile.mkstemp(suffix='.jpg'); os.close(fd)
    cmd = ['ffmpeg', '-v', 'error', '-y'] + (['-ss', str(seek)] if seek is not None else [])
    cmd += ['-i', path, '-frames:v', '1', '-vf', f'crop={crop},scale={size}:{size}', '-q:v', str(q), tmp]
    subprocess.run(cmd, check=True)
    data = base64.b64encode(open(tmp, 'rb').read()).decode(); os.remove(tmp)
    return 'data:image/jpeg;base64,' + data

def frame(name, **kw): return jpeg(os.path.join(FRAMES, name), **kw)
def clip(name, seek=0.6, size=140): return jpeg(os.path.join(CLIPS, name + '.mp4'), crop='720:720:0:0', size=size, seek=seek)

def text(x, y, s, size=17, fill=INK, weight=400, anchor='start', family=None, italic=False, spacing=0):
    fam = f' font-family="{family}"' if family else ''
    it = ' font-style="italic"' if italic else ''
    ls = f' letter-spacing="{spacing}"' if spacing else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{fam}{it}{ls}>{s}</text>'

def mono(x, y, s, size=13, fill=MUTED, anchor='start', weight=500, spacing=0.5):
    return text(x, y, s, size, fill, weight, anchor, MONO, spacing=spacing)

def lines(x, y, rows, size=16, fill=MUTED, gap=1.5, **kw):
    return ''.join(text(x, y + i*size*gap, r, size, fill, **kw) for i, r in enumerate(rows))

def svg(w, h, body, tag):
    fonts = (f"@font-face{{font-family:'Space Grotesk';src:url('file://{HERE}/fonts/SpaceGrotesk.ttf');font-weight:300 700}}"
             f"@font-face{{font-family:'JetBrains Mono';src:url('file://{HERE}/fonts/JetBrainsMono.ttf');font-weight:100 800}}")
    grid = (f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1.2" fill="{GRID}"/></pattern>')
    head = mono(36, 44, tag, 13, DIM, weight=500, spacing=1.5)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{SANS}">'
            f'<style>{fonts}</style><defs>{grid}</defs>'
            f'<rect width="{w}" height="{h}" rx="20" fill="{BG}"/><rect width="{w}" height="{h}" rx="20" fill="url(#dots)"/>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="20" fill="none" stroke="{EDGE}"/>{head}{body}</svg>')

def box(x, y, w, h, fill=PANEL, stroke=EDGE, rx=14, sw=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def poly(pts, fill, stroke='none', sw=0, op=1.0, dash=None):
    d = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<polygon points="{d}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"{da}/>'

def line(x1, y1, x2, y2, stroke=INK, sw=2, dash=None, op=1.0):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{op}" stroke-linecap="round"{da}/>'

def dot(x, y, r=7, fill=INK, stroke=BG, sw=3): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

_ids = [0]
def image(x, y, w, h, href, rx=12, stroke=EDGE):
    _ids[0] += 1; cid = f'c{_ids[0]}'
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{href}" xlink:href="{href}" clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" stroke="{stroke}"/>')

def arrow(x1, y1, x2, y2, stroke=HOT, sw=2.5, head=10):
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head*math.cos(a - 0.45), y2 - head*math.sin(a - 0.45))
    p2 = (x2 - head*math.cos(a + 0.45), y2 - head*math.sin(a + 0.45))
    return line(x1, y1, x2, y2, stroke, sw) + poly([(x2, y2), p1, p2], stroke)

def iso(cx, cy, L):
    a = (cx + L*math.cos(math.radians(150)), cy - L*math.sin(math.radians(150)))
    b = (cx + L*math.cos(math.radians(30)),  cy - L*math.sin(math.radians(30)))
    return a, b, (cx, cy + L)

def add(p, q, o): return (p[0] + q[0] - o[0], p[1] + q[1] - o[1])
def lerp(p, q, t): return (p[0] + (q[0]-p[0])*t, p[1] + (q[1]-p[1])*t)

def save(name, w, h, body, tag):
    os.makedirs(SRC, exist_ok=True)
    src = os.path.join(SRC, name + '.svg'); open(src, 'w').write(svg(w, h, body, tag))
    png = os.path.join(OUT, name + '.png')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
                    '--default-background-color=00000000', f'--window-size={w},{h}', f'--screenshot={png}', 'file://' + src],
                   check=True, capture_output=True)
    print('wrote', png)


# ---------- fig 01: the corner --------------------------------------------------------
def fig_corner():
    W, H = 1200, 560
    b = ''; L = 150; cy = 300
    cx = 290
    a, bb, c = iso(cx, cy, L); e = 1.32
    a2, b2, c2 = lerp((cx, cy), a, e), lerp((cx, cy), bb, e), (cx, cy + L*e)
    b += poly([(cx, cy), a2, add(a2, b2, (cx, cy)), b2], CEIL, op=0.14)
    b += poly([(cx, cy), a2, (a2[0], a2[1] + L*e), c2], LEFT, op=0.10)
    b += poly([(cx, cy), b2, (b2[0], b2[1] + L*e), c2], RIGHT, op=0.08)
    b += poly([a, add(a, bb, (cx, cy)), bb, add(bb, c, (cx, cy)), c, add(a, c, (cx, cy))], 'none', LAV, 1.4, dash='4 6')
    for p in (a2, b2, c2): b += line(cx, cy, p[0], p[1], INK, 3)
    b += dot(cx, cy, 8, HOT)
    b += mono(cx, cy - 118, 'ceiling', 14, CEIL, 'middle', 700)
    b += mono(cx - 96, cy + 98, 'left wall', 14, LEFT, 'middle', 700)
    b += mono(cx + 96, cy + 98, 'right wall', 14, RIGHT, 'middle', 700)
    b += mono(cx + 16, cy + 5, 'corner point', 12, HOT)
    b += text(cx, 520, 'my room corner, looking up into it', 16, MUTED, 400, 'middle')
    b += text(600, 282, 'same seven lines.', 20, INK, 600, 'middle')
    b += text(600, 308, 'your brain picks one.', 20, INK, 600, 'middle')
    b += arrow(540, 340, 660, 340)
    cx = 910
    a, bb, c = iso(cx, cy, L)
    b += poly([(cx, cy), a, add(a, bb, (cx, cy)), bb], CEIL)
    b += poly([(cx, cy), a, add(a, c, (cx, cy)), c], LEFT)
    b += poly([(cx, cy), bb, add(bb, c, (cx, cy)), c], RIGHT)
    for p in (a, bb, c): b += line(cx, cy, p[0], p[1], BG, 3)
    b += text(cx, 520, 'or a solid cube poking out', 16, MUTED, 400, 'middle')
    save('01-corner', W, H, b, 'fig. 01  /  the corner')


# ---------- fig 02: four dots ---------------------------------------------------------
def fig_four_dots():
    W, H = 1200, 600
    b = ''; cx, cy, L = 330, 320, 205
    a, bb, c = iso(cx, cy, L)
    faces = (((cx, cy), a, add(a, bb, (cx, cy)), bb, CEIL), ((cx, cy), a, add(a, c, (cx, cy)), c, LEFT), ((cx, cy), bb, add(bb, c, (cx, cy)), c, RIGHT))
    for p0, p1, p2, p3, col in faces:
        b += poly([p0, p1, p2, p3], col, op=0.85)
        for k in range(1, 4):
            t = k/4
            b += line(*lerp(p0, p1, t), *lerp(p3, p2, t), BG, 1.2, op=0.35) + line(*lerp(p0, p3, t), *lerp(p1, p2, t), BG, 1.2, op=0.35)
    for p in (a, bb, c):
        q = lerp((cx, cy), p, 1.32); b += line(cx, cy, q[0], q[1], YEL, 1.5, '2 5')
    b += dot(cx, cy, 12, INK, HOT, 4)
    for p, lab, dx, dy in ((a, 'A', -18, -12), (bb, 'B', 18, -12), (c, 'C', 18, 8)):
        b += dot(p[0], p[1], 9, LAV, BG, 3)
        b += mono(p[0] + dx, p[1] + dy, lab, 20, INK, 'start' if dx > 0 else 'end', 800)
    b += mono(cx + 20, cy + 30, 'V', 20, INK, 'start', 800)
    tx = 650
    rows = [('V', 'the corner point, where ceiling and both walls meet'),
            ('A', 'one dot along the left ceiling crease'),
            ('B', 'one dot along the right ceiling crease'),
            ('C', 'one dot down the corner between the walls')]
    for i, (k, s) in enumerate(rows):
        y = 150 + i*52
        b += (f'<circle cx="{tx + 12}" cy="{y - 6}" r="12" fill="{INK}" stroke="{HOT}" stroke-width="3"/>' if k == 'V' else f'<circle cx="{tx + 12}" cy="{y - 6}" r="12" fill="{LAV}"/>') + mono(tx + 12, y - 1, k, 13, BG, 'middle', 800)
        b += text(tx + 38, y, s, 17, INK)
    b += box(tx, 380, 500, 150)
    b += mono(tx + 24, 414, 'the maths', 13, HOT, weight=700, spacing=1.5)
    b += lines(tx + 24, 446, ['each face = the four-sided shape between two arms.',
                              'every projector pixel asks “where am I inside this face?”',
                              '(inverse bilinear) and paints that spot of the video.'], 15.5, INK)
    save('02-four-dots', W, H, b, 'fig. 02  /  four dots')


# ---------- fig 03: a video on every face ---------------------------------------------
def fig_clips():
    W, H = 1200, 560
    b = image(40, 80, 440, 440, frame('rig_clips.png', crop='660:660:310:30', size=880))
    tx = 540
    b += mono(tx, 112, 'the deck', 13, HOT, weight=700, spacing=1.5)
    names = ['06_orbit_sun', '15_pink_five', '11_plexus_map', '18_goldfish', '07_liquid_light', '12_vinyl_record', '13_circuit_sphere', '17_octopus']
    for i, n in enumerate(names):
        b += image(tx + i*76, 136, 68, 68, clip(n), rx=10)
    b += text(tx + 8*76 + 4, 178, '+9', 18, MUTED, 600)
    for card, (col, lab) in enumerate(((CEIL, 'ceiling'), (LEFT, 'left'), (RIGHT, 'right'))):
        x = tx + card*76 + 34
        b += arrow(x, 258, x, 212, col, 2.5) + mono(x, 280, lab, 12, col, 'middle', 700)
    b += box(tx, 320, 610, 200)
    b += lines(tx + 26, 362, ['17 short loops, shuffled like a deck.',
                              'the three faces read the same deck a third of the way apart,',
                              'so two faces never show the same clip.',
                              'every 8 s they swap: ceiling first, then each wall 1.5 s later,',
                              'so the cube kind of turns over face by face.'], 16, INK, 1.55)
    save('03-clips', W, H, b, 'fig. 03  /  a video on every face')


# ---------- fig 04: the seat ----------------------------------------------------------
def fig_seat():
    W, H = 1200, 560
    b = ''
    px, py = 40, 80
    b += box(px, py, 330, 400) + mono(px + 22, py + 32, 'from above', 12, DIM, weight=600)
    vx, vy = px + 165, py + 80
    b += line(vx, vy, vx - 145, vy + 145, LEFT, 5) + line(vx, vy, vx + 145, vy + 145, RIGHT, 5) + dot(vx, vy, 8, HOT)
    b += line(vx, vy, vx, vy + 285, LAV, 1.6, '3 6')
    b += mono(vx - 10, vy + 54, '45°', 12, LAV, 'end') + mono(vx + 10, vy + 54, '45°', 12, LAV)
    b += f'<rect x="{vx - 20}" y="{vy + 180}" width="40" height="22" rx="5" fill="{INK}"/><circle cx="{vx}" cy="{vy + 180}" r="6" fill="{HOT}"/>'
    b += mono(vx + 30, vy + 196, 'projector', 12, INK)
    b += f'<circle cx="{vx}" cy="{vy + 280}" r="12" fill="none" stroke="{HOT}" stroke-width="3"/><circle cx="{vx}" cy="{vy + 280}" r="4" fill="{HOT}"/>'
    b += mono(vx + 22, vy + 285, 'you / the phone', 12, HOT, weight=700)
    sx = 400
    b += box(sx, py, 330, 400) + mono(sx + 22, py + 32, 'from the side', 12, DIM, weight=600)
    cx, cy = sx + 40, py + 80
    b += line(cx, cy, sx + 305, cy, CEIL, 5) + line(cx, cy, cx, py + 380, LEFT, 5) + dot(cx, cy, 8, HOT)
    ang = math.radians(35.26); D = 300
    ex, ey = cx + D*math.cos(ang), cy + D*math.sin(ang)
    b += line(cx, cy, ex, ey, LAV, 1.6, '3 6') + f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="12" fill="none" stroke="{HOT}" stroke-width="3"/>'
    b += f'<path d="M {cx + 74:.1f} {cy:.1f} A 74 74 0 0 1 {cx + 74*math.cos(ang):.1f} {cy + 74*math.sin(ang):.1f}" fill="none" stroke="{HOT}" stroke-width="2"/>'
    b += mono(cx + 86, cy + 34, '35°', 14, HOT, weight=700)
    b += mono(sx + 290, cy - 12, 'ceiling', 11, CEIL, 'end', 700) + mono(cx + 14, py + 372, 'wall', 11, LEFT, weight=700)
    b += mono(40, 516, '2.5 m from the corner = 2.0 m out, 1.4 m below the ceiling', 12, MUTED)
    bx = 770
    b += mono(bx, 112, 'what the projector throws', 12, DIM, weight=600)
    b += image(bx, 124, 180, 180, frame('seat_projector_view.png', crop='600:600:340:60', size=360))
    b += arrow(bx + 186, 214, bx + 210, 214)
    b += mono(bx + 215, 112, 'what your eye gets', 12, HOT, weight=700)
    b += image(bx + 215, 124, 180, 180, frame('seat_seat_view.png', crop='600:600:340:60', size=360), stroke=HOT)
    b += box(bx, 330, 395, 150)
    b += lines(bx + 22, 368, ['the picture leaves the projector bent', '(exaggerated here). the corner un-bends it,',
                              'so from the seat the sphere is round:'], 15, INK)
    b += mono(bx + 22, 460, 'measured 99.8% round', 14, HOT, weight=700)
    save('04-seat', W, H, b, 'fig. 04  /  one seat')


# ---------- fig 05: rotations ---------------------------------------------------------
ROWS = [('turntable', 'turntable', ['spins like a record player']),
        ('roll', 'roll', ['tips forward, so the bottom', 'face comes round (4th frame)']),
        ('tumble', 'tumble', ['tilted axis, every face', 'gets a turn']),
        ('diagonal', 'diagonal', ['spins on the line pointing', 'at you: a turning hexagon']),
        ('figure8', 'figure eight', ['the spin axis itself', 'draws an ∞']),
        ('diamond', 'diamond', ['balanced on one corner,', 'museum-display energy']),
        ('rock', 'rock', ['sways gently, never', 'leaves the cube shape'])]

def fig_rotations():
    W, rowh = 1200, 148
    H = 76 + rowh*len(ROWS) + 26
    b = ''
    for r, (key, name, desc) in enumerate(ROWS):
        y = 76 + r*rowh
        b += box(28, y, 1144, rowh - 12)
        b += mono(52, y + 30, f'0{r + 1}', 12, HOT, weight=700) + text(52, y + 62, name, 24, INK, 700) + lines(52, y + 88, desc, 14, MUTED, 1.45)
        for i, fi in enumerate((0, 5, 10, 15, 20, 25)):
            b += image(330 + i*138, y + 6, 124, 124, frame(f'{key}_{fi:02d}.png', crop='660:660:310:30', size=248), rx=10)
    save('05-rotations', W, H, b, 'fig. 05  /  seven ways to spin it')


# ---------- fig 06: scores ------------------------------------------------------------
def fig_scores():
    W, H = 1200, 600
    data = [('90° turntable steps', 95.7, 76, True, 'winner: real 3D turns, locks back in'),
            ('120° diagonal steps', 96.8, 74, False, 'higher, but a flat spin, no depth'),
            ('rock', 92.8, 19, False, 'never drops below 88%'),
            ('diagonal', 91.0, 22, False, ''), ('turntable', 86.4, 23, False, ''), ('roll', 85.7, 19, False, ''),
            ('multi-axis', 83.5, 6, False, ''), ('tumble', 83.2, 7, False, ''), ('figure eight', 81.8, 2, False, ''), ('diamond', 79.5, 0, False, '')]
    x0, y0, bw, gap = 290, 100, 440, 46
    b = mono(x0, y0 - 14, 'avg match to the hexagon', 12, DIM, weight=600) + mono(x0 + bw + 26, y0 - 14, 'near-perfect', 12, DIM, weight=600)
    for i, (name, val, near, win, note) in enumerate(data):
        y = y0 + i*gap
        b += text(x0 - 18, y + 24, name, 17, INK if win else MUTED, 700 if win else 500, 'end')
        w = bw*(val - 70)/30
        b += f'<rect x="{x0}" y="{y + 6}" width="{bw}" height="26" rx="7" fill="{PANEL}"/>'
        b += f'<rect x="{x0}" y="{y + 6}" width="{w:.1f}" height="26" rx="7" fill="{HOT if win else BORDER}"/>'
        b += mono(x0 + w - 10, y + 24, f'{val}%', 13, BG if win else INK, 'end', 800)
        b += mono(x0 + bw + 26, y + 24, f'{near}%', 14, HOT if win else MUTED, weight=700 if win else 500)
        if note: b += text(x0 + bw + 92, y + 24, note, 14.5, HOT if win else MUTED, 600 if win else 400)
    b += mono(x0, y0 + len(data)*gap + 18, 'bars start at 70%', 11, DIM)
    save('06-scores', W, H, b, 'fig. 06  /  which spin keeps the most cube')


# ---------- fig 07: the sphere --------------------------------------------------------
def fig_sphere():
    W, H = 1200, 470
    b = ''
    for i, (f, cap) in enumerate((('sphere_plain.png', 'one video wrapped round'),
                                  ('sphere_rest.png', 'cut out an eighth: three flat faces'),
                                  ('sphere_tumble.png', 'tumbling, the notch rolls away'))):
        x = 50 + i*375
        b += image(x, 76, 325, 325, frame(f, crop='600:600:340:60', size=650))
        b += mono(x, 430, f'0{i + 1}', 12, HOT, weight=700) + text(x + 32, 431, cap, 16, INK)
    save('07-sphere', W, H, b, 'fig. 07  /  a sphere with a slice missing')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in (fig_corner, fig_four_dots, fig_clips, fig_seat, fig_rotations, fig_scores, fig_sphere): f()
