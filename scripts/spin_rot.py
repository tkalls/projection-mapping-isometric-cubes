# spin_rot: the cube's 3D orientation, recomputed every frame.
# Cube space: x, y = the two ceiling-crease directions, z = DOWN the vertical crease. Unit cube [0,1]^3.
# rot() returns the 3x3 rotation (column-major, 9 floats) that the cube_spin shader applies,
# plus the pivot and a scale so tipped poses (diamond) still fit the frame.
import math

def _axis_angle(ax, a):
	x, y, z = ax; n = math.sqrt(x*x + y*y + z*z) or 1.0; x, y, z = x/n, y/n, z/n
	c, s = math.cos(a), math.sin(a); oc = 1.0 - c
	return [[oc*x*x + c,   oc*x*y - z*s, oc*x*z + y*s],
	        [oc*x*y + z*s, oc*y*y + c,   oc*y*z - x*s],
	        [oc*x*z - y*s, oc*y*z + x*s, oc*z*z + c]]

def _mul(A, B):
	return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

# balanced on a corner: rotate the body diagonal (1,1,1) onto the vertical (0,0,1)
_DIAG = _axis_angle((1.0, -1.0, 0.0), -math.acos(1.0/math.sqrt(3.0)))

def _ease(u): return u*u*(3.0 - 2.0*u)

def _turn_angle():
	c = op('controls').par; t = absTime.seconds; mode = c.Spinmode.eval()
	if mode == 'continuous':
		return math.radians(t*c.Spinspeed.eval())
	if mode == 'steps':
		hold, move = c.Spinhold.eval(), c.Spinmove.eval()
		k, f = divmod(t, hold + move)
		u = 0.0 if f < hold else _ease((f - hold)/move)
		return math.radians((k + u)*90.0)
	return 0.0

def state():
	c = op('controls').par; t = absTime.seconds; axis = c.Spinaxis.eval()
	th = _turn_angle(); sp = c.Spinspeed.eval()/12.0          # 1.0 at the default speed
	piv, scale = (0.5, 0.5, 0.5), 1.0
	if c.Spinmode.eval() == 'off':
		R = _axis_angle((0, 0, 1), 0.0)
	elif axis == 'turntable':
		R = _axis_angle((0, 0, 1), th)
	elif axis == 'corner':
		R = _axis_angle((0, 0, 1), th); piv = (0.0, 0.0, 0.5)
	elif axis == 'tumble':
		R = _axis_angle((1.0, -1.0, 0.35), th)
	elif axis == 'multi':
		# three slow spins at rates that never line up, so the motion never exactly repeats
		R = _mul(_axis_angle((0, 0, 1), 0.21*sp*t), _mul(_axis_angle((1, 0, 0), 0.13*sp*t), _axis_angle((0, 1, 0), 0.08*sp*t)))
		scale = 0.82
	elif axis == 'figure8':
		# the spin axis itself traces a figure eight (a lemniscate of tilt), while the cube turns
		w = 0.35*sp
		tilt = _mul(_axis_angle((1, 0, 0), 0.45*math.sin(2.0*w*t)), _axis_angle((0, 1, 0), 0.55*math.sin(w*t)))
		R = _mul(tilt, _axis_angle((0, 0, 1), th))
		scale = 0.85
	elif axis == 'roll':
		R = _axis_angle((1, 0, 0), th); scale = 0.85                 # tips over: the bottom face comes round
	elif axis == 'edge':
		R = _axis_angle((1, 1, 0), th); scale = 0.8                  # through the midpoints of two opposite edges
	elif axis == 'diagonal':
		R = _axis_angle((1, 1, 1), th)                                # through two opposite corners: a spinning hexagon
	elif axis == 'rock':
		# a gentle sway around the isometric pose (never more than ~18 degrees), so the cube breathes in 3D
		# but always reads as the isometric cube: 92.8% average match to the hexagon, worst moment 88%
		R = _mul(_axis_angle((1, -1, 0), math.radians(18)*math.sin(0.45*sp*t)), _axis_angle((1, 1, -2), math.radians(14)*math.sin(0.31*sp*t)))
	elif axis == 'diamond':
		R = _mul(_axis_angle((0, 0, 1), th), _DIAG)
		scale = 0.66
	else:
		R = _axis_angle((0, 0, 1), th)
	scale *= c.Spinsize.eval()
	return R, piv, scale

_cache = {'frame': -1}
def rot(i, frame=0):
	if _cache['frame'] != absTime.frame:
		R, piv, scale = state()
		_cache.update(frame=absTime.frame, m=[R[r][col] for col in range(3) for r in range(3)], piv=piv, scale=scale)
	if i < 9: return _cache['m'][i]
	if i < 12: return _cache['piv'][i - 9]
	return _cache['scale']
