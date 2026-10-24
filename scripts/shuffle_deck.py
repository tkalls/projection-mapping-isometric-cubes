# shuf: which clip plays on which face. Faces change one after another (Stagger), every Autoshuffle seconds.
import random, glob
DIR = '/Users/tobi/TD-Lab/corner_clips/'
_files = None
def files():
	global _files
	if _files is None:
		_files = sorted(glob.glob(DIR + '*.mp4'))
	return _files

def pick(face, step, seed):
	# A shuffled deck, re-dealt after every full pass so the sequence never repeats.
	# All three faces read the SAME deck for a given step, a third of the deck apart,
	# so they can never show the same clip at once; every clip visits every face.
	fl = files()
	n = len(fl)
	gap = max(1, n // 3)
	cycle = step // n
	order = list(range(n))
	random.Random(seed*100003 + cycle*7919).shuffle(order)
	return fl[order[(step + face*gap) % n]]

def clip(face, frame=0):
	c = op('controls').par
	lock = c.Lockclip.eval()
	if lock and lock != 'off':
		return DIR + lock + '.mp4'
	auto = c.Autoshuffle.eval(); stag = c.Stagger.eval(); seed = int(c.Seed.eval())
	step = int((absTime.seconds - face*stag)//auto) if auto > 0 else 0
	return pick(face, step, seed)
