# Delays the kick so the pulse lands when a Bluetooth speaker actually plays the beat.
# BlackHole hands TouchDesigner the audio instantly; the speaker plays it ~150-250 ms later.
# Time-stamped, so the delay is exact even if the frame rate dips.
from collections import deque
buf = deque(maxlen=1200)          # (time, value) pairs, several seconds of history

def onFrameStart(frame):
	c = op('controls').par
	src = op(c.Kicksource.eval() or 'kick')
	v = float(src[0]) if src is not None and src.numChans else 0.0
	if not c.Kickon.eval():
		v = 0.0
	now = absTime.seconds
	buf.append((now, v))
	target = now - c.Syncdelay.eval()/1000.0
	out = buf[0][1]
	for t, val in reversed(buf):
		if t <= target:
			out = val
			break
	op('kick_synced').par.const0value = out
	return
