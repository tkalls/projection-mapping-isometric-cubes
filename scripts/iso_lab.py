"""How isometric does each spin stay? Compares the cube's outline, moment by moment, with the
perfect isometric hexagon (the pose that sits exactly on the room's creases).

    python3 scripts/iso_lab.py
"""
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'axis_lab.py')).read().split('rows = [score(m)')[0])   # reuse rot(), proj(), VERTS, nv, aa, mul
def ease(u): return u*u*(3-2*u)
D111 = (1, 1, 1)
def rot2(mode, t):
    if mode == 'diag_steps':
        hold, move = 4.0, 3.0; k, f = divmod(t, hold + move); u = 0.0 if f < hold else ease((f - hold)/move)
        return aa(D111, math.radians((k + u)*120.0))
    if mode == 'rock':
        # sway around the isometric pose on two axes perpendicular to the view, never more than ~20 degrees
        e1 = (1, -1, 0); e2 = (1, 1, -2)
        return mul(aa(e1, math.radians(18)*math.sin(0.45*t)), aa(e2, math.radians(14)*math.sin(0.31*t)))
    if mode == 'precess':
        # spin about the view diagonal while that axis wobbles ~12 degrees, like a spinning top
        tilt = mul(aa((1, -1, 0), math.radians(12)*math.sin(0.5*t)), aa((1, 1, -2), math.radians(12)*math.cos(0.5*t)))
        return mul(tilt, aa(D111, math.radians(t*12.0)))
    if mode == 'turn_steps':
        hold, move = 4.0, 3.0; k, f = divmod(t, hold + move); u = 0.0 if f < hold else ease((f - hold)/move)
        return aa((0, 0, 1), math.radians((k + u)*90.0))
    return rot(mode, t)
def silhouette(R):
    pts = [proj([sum(R[r][k]*(v[k]-0.5) for k in range(3)) for r in range(3)]) for v in VERTS]
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
def inside(poly, x, y):
    n = len(poly); s = 0
    for i in range(n):
        a, b = poly[i], poly[(i+1) % n]
        c = (b[0]-a[0])*(y-a[1]) - (b[1]-a[1])*(x-a[0])
        if c < 0: return False
    return True
REF = silhouette(aa((0, 0, 1), 0.0))          # the isometric hexagon at rest = the aligned corner
G = [(-1.2 + 2.4*i/59, -1.2 + 2.4*j/59) for i in range(60) for j in range(60)]
REFM = [inside(REF, x, y) for x, y in G]
def iou(R):
    P = silhouette(R); m = [inside(P, x, y) for x, y in G]
    inter = sum(1 for a, b in zip(m, REFM) if a and b); uni = sum(1 for a, b in zip(m, REFM) if a or b)
    return inter/uni
def depth_motion(R1, R2):
    # how much of the rotation between frames is genuinely 3D (tilting toward/away), not just spinning flat
    Rt = [[sum(R2[i][k]*R1[j][k] for k in range(3)) for j in range(3)] for i in range(3)]   # R2 * R1^T
    ang = math.acos(max(-1, min(1, (Rt[0][0] + Rt[1][1] + Rt[2][2] - 1)/2)))
    ax = (Rt[2][1]-Rt[1][2], Rt[0][2]-Rt[2][0], Rt[1][0]-Rt[0][1]); na = math.sqrt(sum(a*a for a in ax)) or 1
    nvn = math.sqrt(sum(a*a for a in nv)); along = abs(sum(ax[i]*nv[i] for i in range(3)))/(na*nvn)
    return ang*math.sqrt(max(0, 1 - along*along))
rows = []
for mode in ('diag_steps', 'rock', 'precess', 'diagonal', 'turn_steps', 'turntable', 'roll', 'tumble', 'multi', 'figure8', 'diamond'):
    vals, dm = [], 0.0; prev = None
    for i in range(0, 1200):
        t = i*0.1; R = rot2(mode, t); v = iou(R); vals.append(v)
        if prev is not None: dm += depth_motion(prev, R)
        prev = R
    rows.append((mode, sum(vals)/len(vals), sum(1 for v in vals if v > 0.95)/len(vals), min(vals), math.degrees(dm)/120.0))
rows.sort(key=lambda r: -r[1])
print(f"{'mode':11} {'avg match to hexagon':>20} {'time near-perfect':>17} {'worst moment':>12} {'3D turning (deg/s)':>18}")
for m, a, f, w, d in rows:
    print(f"{m:11} {a*100:>19.1f}% {f*100:>16.0f}% {w*100:>11.0f}% {d:>18.1f}")
