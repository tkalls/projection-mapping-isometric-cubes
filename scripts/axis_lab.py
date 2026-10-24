"""Scores every spin mode in the seat view: how smooth the outline is, the biggest frame-to-frame
jump, and how many of the six faces you get to see.

    python3 scripts/axis_lab.py
"""
import math
def aa(ax, a):
    x, y, z = ax; n = math.sqrt(x*x+y*y+z*z) or 1; x, y, z = x/n, y/n, z/n
    c, s = math.cos(a), math.sin(a); oc = 1-c
    return [[oc*x*x+c, oc*x*y-z*s, oc*x*z+y*s], [oc*x*y+z*s, oc*y*y+c, oc*y*z-x*s], [oc*x*z-y*s, oc*y*z+x*s, oc*z*z+c]]
def mul(A, B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(A, v): return [sum(A[i][k]*v[k] for k in range(3)) for i in range(3)]
DIAG = aa((1,-1,0), -math.acos(1/math.sqrt(3)))
SPEED = 12.0
def rot(mode, t):
    th = math.radians(t*SPEED); sp = 1.0
    if mode == 'turntable': return aa((0,0,1), th)
    if mode == 'tumble':    return aa((1,-1,0.35), th)
    if mode == 'multi':     return mul(aa((0,0,1), .21*sp*t), mul(aa((1,0,0), .13*sp*t), aa((0,1,0), .08*sp*t)))
    if mode == 'figure8':
        w = .35*sp; return mul(mul(aa((1,0,0), .45*math.sin(2*w*t)), aa((0,1,0), .55*math.sin(w*t))), aa((0,0,1), th))
    if mode == 'diamond':   return mul(aa((0,0,1), th), DIAG)
    if mode == 'roll':      return aa((1,0,0), th)            # tips over a horizontal axis: the bottom comes round
    if mode == 'edge':      return aa((1,1,0), th)            # through the midpoints of two opposite edges
    if mode == 'diagonal':  return aa((1,1,1), th)            # through two opposite corners (the viewing axis)
# seat view: exact isometric projection (arms at 150, 30, 270 degrees)
A2 = [math.cos(math.radians(150)), math.sin(math.radians(150))]; B2 = [math.cos(math.radians(30)), math.sin(math.radians(30))]; C2 = [0, -1]
r1 = [A2[0], B2[0], C2[0]]; r2 = [A2[1], B2[1], C2[1]]
nv = [r1[1]*r2[2]-r1[2]*r2[1], r1[2]*r2[0]-r1[0]*r2[2], r1[0]*r2[1]-r1[1]*r2[0]]
if sum(nv) < 0: nv = [-x for x in nv]
def proj(p): return (sum(r1[i]*p[i] for i in range(3)), sum(r2[i]*p[i] for i in range(3)))
VERTS = [(x, y, z) for x in (0,1) for y in (0,1) for z in (0,1)]
FACES = {'top(z0)': (0,0,-1), 'bottom(z1)': (0,0,1), 'right(x0)': (-1,0,0), 'x1': (1,0,0), 'left(y0)': (0,-1,0), 'y1': (0,1,0)}
def hull_area(pts):
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    return abs(sum(h[i][0]*h[(i+1)%len(h)][1] - h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h))))/2
def score(mode, T=120.0, dt=0.05):
    areas, faces_n = [], []; seen = {k: 0 for k in FACES}
    n = int(T/dt)
    for i in range(n):
        R = rot(mode, i*dt)
        pts = [proj([sum(R[r][k]*(v[k]-0.5) for k in range(3)) for r in range(3)]) for v in VERTS]
        areas.append(hull_area(pts))
        vis = 0
        for name, N in FACES.items():
            Nw = mv(R, N)
            if sum(Nw[j]*nv[j] for j in range(3)) < -0.15:   # clearly facing the seat
                vis += 1; seen[name] += 1
        faces_n.append(vis)
    mean = sum(areas)/len(areas); sd = math.sqrt(sum((a-mean)**2 for a in areas)/len(areas))
    pop = max(abs(areas[i+1]-areas[i])/mean for i in range(len(areas)-1))*100
    shown = sum(1 for k in seen if seen[k] > 0.05*n)
    return {'mode': mode, 'smooth': round(100*(1 - sd/mean), 1), 'pop%': round(pop, 2), 'avg_faces': round(sum(faces_n)/len(faces_n), 2),
            'faces_seen_of_6': shown, 'bottom_shown%': round(100*seen['bottom(z1)']/n, 1)}
rows = [score(m) for m in ('turntable','tumble','multi','figure8','diamond','roll','edge','diagonal')]
for r in rows:
    r['score'] = round(0.6*r['smooth'] + 40*(r['faces_seen_of_6']/6) - 4*r['pop%'], 1)
rows.sort(key=lambda r: -r['score'])
print(f"{'mode':10} {'smooth%':>8} {'pop%':>6} {'avg faces':>9} {'faces seen':>10} {'bottom shown':>12} {'score':>6}")
for r in rows:
    print(f"{r['mode']:10} {r['smooth']:>8} {r['pop%']:>6} {r['avg_faces']:>9} {str(r['faces_seen_of_6'])+'/6':>10} {str(r['bottom_shown%'])+'%':>12} {r['score']:>6}")
