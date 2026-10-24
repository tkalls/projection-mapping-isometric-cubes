"""Builds the explainer diagrams in docs/img/ from the same geometry the piece runs on.

    python3 docs/make_diagrams.py <frames_dir>

<frames_dir> holds 1280x720 PNG renders straight out of TouchDesigner (the cube, the
sphere, the alignment pattern). Clip thumbnails are pulled from ~/TD-Lab/corner_clips.
Needs ffmpeg on the PATH. Everything else is plain Python.
"""
import base64, math, os, subprocess, sys, tempfile

FRAMES = sys.argv[1] if len(sys.argv) > 1 else 'frames'
CLIPS = os.path.expanduser('~/TD-Lab/corner_clips')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')

BG, PANEL, INK, MUTED = '#0d1017', '#151a23', '#e8ecf3', '#9aa4b2'
CEIL, LEFT, RIGHT, GOLD, PINK = '#4c8dff', '#ff8a3d', '#35d07f', '#ffd23f', '#ff4fa3'
FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"


# ---------- helpers -------------------------------------------------------------------
def jpeg(path, crop='720:720:280:0', size=360, q=4, seek=None):
    """A frame (or a video frame) as a base64 JPEG data URI."""
    fd, tmp = tempfile.mkstemp(suffix='.jpg'); os.close(fd)
    cmd = ['ffmpeg', '-v', 'error', '-y']
    if seek is not None: cmd += ['-ss', str(seek)]
    cmd += ['-i', path, '-frames:v', '1', '-vf', f'crop={crop},scale={size}:{size}', '-q:v', str(q), tmp]
    subprocess.run(cmd, check=True)
    data = base64.b64encode(open(tmp, 'rb').read()).decode(); os.remove(tmp)
    return 'data:image/jpeg;base64,' + data

def frame(name, **kw): return jpeg(os.path.join(FRAMES, name), **kw)
def clip(name, seek=0.6, size=110): return jpeg(os.path.join(CLIPS, name + '.mp4'), crop='720:720:0:0', size=size, seek=seek)

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">'
            f'<title>{title}</title><rect width="{w}" height="{h}" rx="18" fill="{BG}"/>{body}</svg>')

def text(x, y, s, size=18, fill=INK, weight=400, anchor='start', family=None, italic=False):
    fam = f' font-family="{family}"' if family else ''
    st = ' font-style="italic"' if italic else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{fam}{st}>{s}</text>'

def lines(x, y, rows, size=17, fill=MUTED, gap=1.45, **kw):
    return ''.join(text(x, y + i*size*gap, r, size, fill, **kw) for i, r in enumerate(rows))

def heading(n, s, sub=None):
    out = text(40, 58, f'<tspan fill="{GOLD}">{n}</tspan>  {s}', 30, INK, 700)
    if sub: out += text(40, 92, sub, 18, MUTED)
    return out

def poly(pts, fill, stroke='none', sw=0, op=1.0, dash=None):
    d = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<polygon points="{d}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"{da}/>'

def line(x1, y1, x2, y2, stroke=INK, sw=2, dash=None, op=1.0, cap='round'):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{op}" stroke-linecap="{cap}"{da}/>'

def dot(x, y, r=7, fill=INK, stroke=BG, sw=3): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def image(x, y, w, h, href, rx=10):
    cid = f'c{abs(hash((x, y, w, h))) % 10**8}'
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{href}" xlink:href="{href}" clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice"/>')

def arrow(x1, y1, x2, y2, stroke=INK, sw=2.5, head=11):
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head*math.cos(a - 0.45), y2 - head*math.sin(a - 0.45))
    p2 = (x2 - head*math.cos(a + 0.45), y2 - head*math.sin(a + 0.45))
    return line(x1, y1, x2, y2, stroke, sw) + poly([(x2, y2), p1, p2], stroke)

def iso(cx, cy, L):
    """The three isometric arms (screen space, y down): ceiling-left, ceiling-right, down."""
    a = (cx + L*math.cos(math.radians(150)), cy - L*math.sin(math.radians(150)))
    b = (cx + L*math.cos(math.radians(30)),  cy - L*math.sin(math.radians(30)))
    c = (cx, cy + L)
    return a, b, c

def add(p, q, o): return (p[0] + q[0] - o[0], p[1] + q[1] - o[1])

def save(name, s):
    path = os.path.join(OUT, name); open(path, 'w').write(s); print('wrote', path, f'{len(s)/1024:.0f} KB')


# ---------- 1. the corner ---------------------------------------------------------------
def d1_corner():
    W, H = 1200, 640
    b = heading('1', 'Every room corner is the inside of a cube',
                'Where your ceiling meets two walls, three flat surfaces meet at 90°, exactly like the inside of a box.')
    L = 150
    # left panel: the room corner, drawn with the SAME seven lines as the cube on the right
    cx, cy = 300, 335
    a, bb, c = iso(cx, cy, L)
    ext = 1.32
    a2 = (cx + (a[0]-cx)*ext, cy + (a[1]-cy)*ext); b2 = (cx + (bb[0]-cx)*ext, cy + (bb[1]-cy)*ext); c2 = (cx, cy + L*ext)
    b += poly([(cx, cy), a2, (a2[0] + b2[0] - cx, a2[1] + b2[1] - cy), b2], CEIL, op=0.16)
    b += poly([(cx, cy), a2, (a2[0], a2[1] + L*ext), c2], LEFT, op=0.14)
    b += poly([(cx, cy), b2, (b2[0], b2[1] + L*ext), c2], RIGHT, op=0.14)
    hexo = [a, add(a, bb, (cx, cy)), bb, add(bb, c, (cx, cy)), c, add(a, c, (cx, cy))]
    b += poly(hexo, 'none', INK, 1.5, dash='5 6')
    for p in (a2, b2, c2): b += line(cx, cy, p[0], p[1], INK, 3)
    b += dot(cx, cy, 8, GOLD)
    b += text(cx, cy - 120, 'ceiling', 19, CEIL, 700, 'middle')
    b += text(cx - 95, cy + 95, 'left wall', 19, LEFT, 700, 'middle')
    b += text(cx + 95, cy + 95, 'right wall', 19, RIGHT, 700, 'middle')
    b += text(cx + 16, cy + 6, 'corner point', 14, GOLD, 600)
    b += text(cx, 565, 'your room corner, looking up into it', 17, MUTED, 400, 'middle', italic=True)
    # middle: the flip
    b += text(600, 318, 'same lines,', 20, INK, 600, 'middle') + text(600, 344, 'two ways to see them', 20, INK, 600, 'middle')
    b += arrow(530, 378, 670, 378, GOLD, 3)
    # right panel: the cube popping out
    cx = 900
    a, bb, c = iso(cx, cy, L)
    b += poly([(cx, cy), a, add(a, bb, (cx, cy)), bb], CEIL, op=0.95)
    b += poly([(cx, cy), a, add(a, c, (cx, cy)), c], LEFT, op=0.85)
    b += poly([(cx, cy), bb, add(bb, c, (cx, cy)), c], RIGHT, op=0.7)
    for p in (a, bb, c): b += line(cx, cy, p[0], p[1], BG, 3)
    b += text(cx, 565, '…or a solid cube poking out', 17, MUTED, 400, 'middle', italic=True)
    b += text(40, 610, 'Your eyes cannot tell an inside corner from a cube\'s outside corner when the three faces look the same size.', 15, MUTED)
    b += text(40, 630, 'That is the Necker-cube illusion, and this whole project runs on it.', 15, MUTED)
    save('01-corner.svg', svg(W, H + 10, b, 'Every room corner is the inside of a cube'))


# ---------- 2. four dots ----------------------------------------------------------------
def d2_four_dots():
    W, H = 1200, 620
    b = heading('2', 'Four dots make the cube', 'One dot on the corner, one dot along each crease. The three faces are built from those four dots.')
    x0, y0, S = 60, 120, 460
    b += image(x0, y0, S, S, frame('rig_test.png', size=460))
    k = S/720; cx, cy, L = x0 + 360*k, y0 + 360*k, 300*k
    a, bb, c = iso(cx, cy, L)
    for p, lab, col in ((a, 'A', CEIL), (bb, 'B', RIGHT), (c, 'C', LEFT)):
        b += dot(p[0], p[1], 9, col, INK, 2) + text(p[0] + (14 if p[0] >= cx else -14), p[1] - 12, lab, 22, INK, 800, 'start' if p[0] >= cx else 'end')
    b += dot(cx, cy, 10, GOLD, INK, 2) + text(cx + 16, cy + 28, 'V', 22, GOLD, 800)
    tx = 580
    b += text(tx, 170, 'How you line it up', 24, INK, 700)
    steps = [('1', 'Put the white dot <tspan fill="%s" font-weight="700">V</tspan> on the room\'s corner point.' % GOLD),
             ('2', 'Turn each yellow guide line until it sits inside a crease.'),
             ('3', 'Choose how far <tspan fill="%s">A</tspan>, <tspan fill="%s">B</tspan> and <tspan fill="%s">C</tspan> reach along the creases.' % (CEIL, RIGHT, LEFT)),
             ('4', 'Done. The faces share their edges with the real creases,'),
             ('', 'so they can never drift apart.')]
    for i, (n, s) in enumerate(steps):
        y = 215 + i*40
        if n: b += f'<circle cx="{tx + 14}" cy="{y - 6}" r="14" fill="{PANEL}" stroke="{GOLD}" stroke-width="2"/>' + text(tx + 14, y, n, 16, GOLD, 700, 'middle')
        b += text(tx + 40, y, s, 18, INK)
    b += f'<rect x="{tx}" y="430" width="560" height="140" rx="14" fill="{PANEL}"/>'
    b += text(tx + 22, 465, 'The maths, in one breath', 17, GOLD, 700)
    b += lines(tx + 22, 495, ['Each face is the four-sided shape between two arms.',
                              'For every projector pixel the shader asks: “where am I inside this',
                              'face?” (inverse bilinear interpolation), then paints that spot', 'of the video there.'], 15.5, INK)
    save('02-four-dots.svg', svg(W, H, b, 'Four dots make the cube'))


# ---------- 3. a video on every face ----------------------------------------------------------
def d3_clips():
    W, H = 1200, 600
    b = heading('3', 'A video on every face', 'Short looping clips play on the faces and keep swapping, one face at a time.')
    x0, y0, S = 60, 120, 430
    b += image(x0, y0, S, S, frame('rig_clips.png', size=430))
    names = ['06_orbit_sun', '15_pink_five', '11_plexus_map', '18_goldfish', '07_liquid_light', '12_vinyl_record', '13_circuit_sphere', '17_octopus']
    tx = 540
    b += text(tx, 160, 'The deck', 22, INK, 700)
    b += lines(tx, 192, ['17 clips are shuffled like a deck of cards.',
                         'The three faces read the same deck, a third of the way apart,',
                         'so two faces never show the same clip at once.',
                         'After a full pass the deck is re-dealt, so the order never repeats.'], 16.5, MUTED)
    for i, n in enumerate(names):
        x = tx + i*78; y = 300
        b += image(x, y, 70, 70, clip(n, size=140), rx=8)
    # pointers to three faces
    for fi, (col, lab, card) in enumerate(((CEIL, 'ceiling', 0), (LEFT, 'left wall', 1), (RIGHT, 'right wall', 2))):
        x = tx + card*78 + 35
        b += arrow(x, 410, x, 376, col, 3) + text(x, 432, lab, 14, col, 700, 'middle')
    b += text(tx + 7*78 + 70, 342, '…', 26, MUTED, 700)
    b += f'<rect x="{tx}" y="465" width="600" height="95" rx="14" fill="{PANEL}"/>'
    b += lines(tx + 22, 500, ['Every 8 seconds the faces change: ceiling first, then each wall',
                              '1.5 seconds later, so the cube “turns over” face by face.'], 16, INK)
    save('03-clips.svg', svg(W, H, b, 'A video on every face'))


# ---------- 4. the seat -----------------------------------------------------------------
def d4_seat():
    W, H = 1200, 700
    b = heading('4', 'It only looks perfect from one seat', 'A projected illusion has one “sweet spot”. Film from there and it looks like a real object.')
    # top-down plan
    px, py = 70, 130
    b += f'<rect x="{px}" y="{py}" width="330" height="330" rx="14" fill="{PANEL}"/>' + text(px + 165, py + 28, 'from above', 15, MUTED, 600, 'middle')
    vx, vy = px + 165, py + 60
    b += line(vx, vy, vx - 150, vy + 150, LEFT, 5) + line(vx, vy, vx + 150, vy + 150, RIGHT, 5)
    b += dot(vx, vy, 8, GOLD)
    b += line(vx, vy, vx, vy + 255, GOLD, 2, '6 6')
    b += text(vx - 70, vy + 95, 'wall', 14, LEFT, 700, 'middle') + text(vx + 70, vy + 95, 'wall', 14, RIGHT, 700, 'middle')
    b += text(vx + 8, vy + 50, '45°', 14, GOLD, 700) + text(vx - 8, vy + 50, '45°', 14, GOLD, 700, 'end')
    b += f'<rect x="{vx - 20}" y="{vy + 170}" width="40" height="22" rx="5" fill="{INK}"/><circle cx="{vx}" cy="{vy + 170}" r="6" fill="{GOLD}"/>' + text(vx + 30, vy + 186, 'projector', 14, INK)
    b += f'<circle cx="{vx}" cy="{vy + 245}" r="12" fill="none" stroke="{PINK}" stroke-width="3"/><circle cx="{vx}" cy="{vy + 245}" r="4" fill="{PINK}"/>' + text(vx + 22, vy + 250, 'you (or the phone)', 14, PINK, 700)
    # side view
    sx, sy = 430, 130
    b += f'<rect x="{sx}" y="{sy}" width="330" height="330" rx="14" fill="{PANEL}"/>' + text(sx + 165, sy + 28, 'from the side', 15, MUTED, 600, 'middle')
    cx, cy = sx + 40, sy + 60
    b += line(cx, cy, sx + 310, cy, CEIL, 5) + line(cx, cy, cx, sy + 315, LEFT, 5) + dot(cx, cy, 8, GOLD)
    ang = math.radians(35.26); D = 290
    ex, ey = cx + D*math.cos(ang), cy + D*math.sin(ang)
    b += line(cx, cy, ex, ey, GOLD, 2, '6 6') + f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="12" fill="none" stroke="{PINK}" stroke-width="3"/>'
    b += f'<path d="M {cx + 70:.1f} {cy:.1f} A 70 70 0 0 1 {cx + 70*math.cos(ang):.1f} {cy + 70*math.sin(ang):.1f}" fill="none" stroke="{GOLD}" stroke-width="2"/>' + text(cx + 82, cy + 32, '35°', 15, GOLD, 700)
    b += text(sx + 250, cy - 12, 'ceiling', 13, CEIL, 700, 'middle') + text(cx + 14, sy + 300, 'wall', 13, LEFT, 700)
    b += lines(sx + 22, sy + 350, ['Sit on the line that leaves the corner', 'halfway between the walls, 35° down.', 'At 2.5 m: 2.0 m out, 1.4 m below the ceiling.'], 14, MUTED)
    # bent vs round
    bx = 800
    b += text(bx + 85, 162, 'the projector throws…', 16, INK, 700, 'middle')
    b += image(bx, 175, 170, 170, frame('seat_projector_view.png', size=340))
    b += text(bx + 285, 162, '…your eye gets', 16, INK, 700, 'middle')
    b += image(bx + 200, 175, 170, 170, frame('seat_seat_view.png', size=340))
    b += arrow(bx + 175, 260, bx + 196, 260, GOLD, 3)
    b += lines(bx, 380, ['The projector throws a deliberately bent', 'picture (exaggerated here). The corner',
                         'un-bends it, so from the seat the sphere', 'is a perfect circle: measured 99.8% round.'], 15, MUTED)
    b += f'<rect x="70" y="560" width="1060" height="105" rx="14" fill="{PANEL}"/>'
    b += lines(95, 595, ['How: the four dots tell us how the three real surfaces look to the projector. From the seat those same faces look like a',
                         'perfect isometric hexagon. So each object is drawn in that perfect “seat view”, then every projector pixel works out which',
                         'surface it lands on and where, and copies the matching spot. That is called anamorphic projection.'], 15.5, INK)
    save('04-seat.svg', svg(W, H, b, 'It only looks perfect from one seat'))


# ---------- 5. rotations ----------------------------------------------------------------
ROWS = [('turntable', 'Turntable', ['spins like a record player']),
        ('roll', 'Roll', ['tips forward, so the bottom', 'face comes round (4th frame)']),
        ('tumble', 'Tumble', ['turns on a tilted axis,', 'every face gets a turn']),
        ('diagonal', 'Diagonal', ['spins on the line pointing', 'at you: a turning hexagon']),
        ('figure8', 'Figure eight', ['the spin axis itself', 'draws an ∞']),
        ('diamond', 'Diamond', ['balanced on one corner,', 'like a museum display']),
        ('rock', 'Rock', ['sways gently, never', 'leaves the cube shape'])]

def d5_rotations():
    W, rowh = 1200, 150
    H = 120 + rowh*len(ROWS) + 30
    b = heading('5', 'Seven ways to spin it', 'Same cube, same videos. A small Python “motion engine” turns it a different way each time.')
    for r, (key, name, desc) in enumerate(ROWS):
        y = 120 + r*rowh
        b += f'<rect x="30" y="{y}" width="1140" height="{rowh - 12}" rx="14" fill="{PANEL}"/>'
        b += text(55, y + 52, name, 22, INK, 700) + lines(55, y + 82, desc, 14.5, MUTED)
        for i, fi in enumerate((0, 5, 10, 15, 20, 25)):
            b += image(330 + i*138, y + 7, 124, 124, frame(f'{key}_{fi:02d}.png', crop='660:660:310:30', size=248), rx=8)
    save('05-rotations.svg', svg(W, H, b, 'Seven ways to spin it'))


# ---------- 6. scores -------------------------------------------------------------------
def d6_scores():
    W, H = 1200, 640
    b = heading('6', 'Which spin keeps the most “cube”?', 'Each motion was simulated for 2 minutes and its outline compared with the perfect isometric hexagon.')
    data = [('90° turntable steps', 95.7, 76, True, 'winner: real 3D turns, locks back in'),
            ('120° diagonal steps', 96.8, 74, False, 'higher, but a flat spin, no depth'),
            ('Rock', 92.8, 19, False, 'never drops below 88%'),
            ('Diagonal', 91.0, 22, False, ''),
            ('Turntable', 86.4, 23, False, ''),
            ('Roll', 85.7, 19, False, ''),
            ('Multi-axis', 83.5, 6, False, ''),
            ('Tumble', 83.2, 7, False, ''),
            ('Figure eight', 81.8, 2, False, ''),
            ('Diamond', 79.5, 0, False, '')]
    x0, y0, bw, gap = 300, 130, 440, 46
    b += text(x0, y0 - 8, 'average match to the hexagon', 13, MUTED) + text(x0 + bw + 30, y0 - 8, 'time near-perfect', 13, MUTED)
    for i, (name, val, near, win, note) in enumerate(data):
        y = y0 + i*gap
        col = GOLD if win else CEIL
        b += text(x0 - 16, y + 24, name, 16.5, INK if win else MUTED, 700 if win else 500, 'end')
        w = bw*(val - 70)/30
        b += f'<rect x="{x0}" y="{y + 6}" width="{bw}" height="26" rx="6" fill="{PANEL}"/><rect x="{x0}" y="{y + 6}" width="{w:.1f}" height="26" rx="6" fill="{col}"/>'
        b += text(x0 + w - 8, y + 24, f'{val}%', 14, BG, 800, 'end')
        b += text(x0 + bw + 30, y + 24, f'{near}%', 15, INK if win else MUTED, 700 if win else 500)
        if note: b += text(x0 + bw + 95, y + 24, note, 13.5, GOLD if win else MUTED, 600 if win else 400)
    b += text(x0, y0 + len(data)*gap + 20, 'bars start at 70%', 12, MUTED, italic=True)
    save('06-scores.svg', svg(W, H, b, 'Which spin keeps the most cube'))


# ---------- 7. music --------------------------------------------------------------------
def d7_music():
    W, H = 1200, 560
    b = heading('7', 'It punches on the kick drum', 'Not on loudness: on the moment a bass hit starts.')
    boxes = [('Music', 'any app on the Mac', PINK), ('BlackHole', 'virtual audio cable', CEIL),
             ('Keep the bass', 'low-pass at 110 Hz', CEIL), ('Kick?', 'now vs last 1.2 s:\njump over 45%', GOLD),
             ('Wait 180 ms', 'for the Bluetooth\nspeaker to catch up', CEIL), ('Punch', 'cube +8% bigger,\nflash, creases glow', RIGHT)]
    x, y, w, h, g = 40, 140, 170, 120, 22
    for i, (t, s, col) in enumerate(boxes):
        bx = x + i*(w + g)
        b += f'<rect x="{bx}" y="{y}" width="{w}" height="{h}" rx="14" fill="{PANEL}" stroke="{col}" stroke-width="2"/>'
        b += text(bx + w/2, y + 40, t, 18, col, 700, 'middle')
        for j, part in enumerate(s.split('\n')): b += text(bx + w/2, y + 70 + j*20, part, 14, MUTED, 400, 'middle')
        if i < len(boxes) - 1: b += arrow(bx + w + 2, y + h/2, bx + w + g - 2, y + h/2, MUTED, 2, 8)
    b += image(210, 300, 220, 220, frame('rig_clips.png', size=440)) + text(320, 540, 'between beats', 15, MUTED, 600, 'middle')
    b += arrow(450, 410, 520, 410, GOLD, 3)
    b += image(540, 300, 220, 220, frame('rig_kick.png', size=440)) + text(650, 540, 'on the kick', 15, GOLD, 700, 'middle')
    b += lines(800, 350, ['Comparing the bass with its own recent', 'average means it follows the beat at any',
                          'volume. The delay was measured to the frame', 'inside TouchDesigner: 400 ms set, 400 ms got.'], 15, MUTED)
    save('07-music.svg', svg(W, H, b, 'It punches on the kick drum'))


# ---------- 8. the sphere ---------------------------------------------------------------
def d8_sphere():
    W, H = 1200, 520
    b = heading('8', 'Bonus: a sphere with a slice missing', 'A cube changes outline as it spins. A sphere is always a circle, so it tumbles more smoothly.')
    for i, (f, cap) in enumerate((('sphere_plain.png', 'a sphere: one video wrapped round'),
                                  ('sphere_rest.png', 'cut out an eighth: three flat faces'),
                                  ('sphere_tumble.png', 'tumbling: the notch rolls away'))):
        x = 60 + i*370
        b += image(x, 120, 300, 300, frame(f, size=600)) + text(x + 150, 450, cap, 16, INK, 600, 'middle')
    b += lines(60, 492, ['The three faces inside the notch meet at 90°, just like the ceiling and two walls: a tiny room corner, projected into the real one.'], 15.5, MUTED)
    save('08-sphere.svg', svg(W, H, b, 'A sphere with a slice missing'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in (d1_corner, d2_four_dots, d3_clips, d4_seat, d5_rotations, d6_scores, d7_music, d8_sphere): f()
