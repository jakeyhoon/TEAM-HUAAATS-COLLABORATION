"""Synthesize a 60s music bed + sound effects for the Moon short (no samples, no downloads).
Usage: python3 audio.py out.wav
"""
import sys, wave
import numpy as np

SR, DUR = 44100, 60.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(1)
mix = np.zeros((N, 2))

def at(sec):
    return int(sec * SR)

def add(sig, start, gain=1.0, pan=0.0):
    i = at(start)
    sig = sig[: max(0, N - i)]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[i:i + len(sig), 0] += sig * gain * l
    mix[i:i + len(sig), 1] += sig * gain * r

def env(n, a=0.01, r=0.2):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e

def lowpass(x, k):
    """Cheap one-pole lowpass, k in (0,1]: smaller = darker."""
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc); y[i] = acc
    return y

def note(freq, dur, kind="pad"):
    n = int(dur * SR); tt = np.arange(n) / SR
    if kind == "pad":
        s = sum(np.sin(2 * np.pi * freq * m * tt + d) / m for m, d in [(1, 0), (2, .3), (3, .7)])
        s += 0.6 * np.sin(2 * np.pi * freq * 1.003 * tt)
        return s * env(n, 1.2, 1.5)
    if kind == "pluck":
        return np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 6)

# ---------- music bed: slow minor progression (Am - F - C - G), 4s per chord ----------
CH = {"Am": [110, 130.81, 164.81], "F": [87.31, 110, 130.81], "C": [65.41, 98, 130.81], "G": [98, 123.47, 146.83]}
prog = ["Am", "F", "C", "G"]
for k in range(15):
    for f in CH[prog[k % 4]]:
        add(note(f, 4.8), k * 4.0, 0.05)
# soft plucked arpeggio from 11s on, sparse
arp = [440, 523.25, 659.25, 523.25]
for k in range(int(11 / 0.5), int(52 / 0.5)):
    add(note(arp[k % 4] * (0.5 if prog[int(k * 0.5 / 4) % 4] in ("F", "C") else 1), 0.6, "pluck"),
        k * 0.5, 0.05, pan=0.4 * np.sin(k))
# low heartbeat pulse in tilt/day scenes
for b in np.arange(35, 52.5, 1.0):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18), b, 0.35)
# music dips under the hook flash and drops out before the twist
duck = np.ones(N)
duck[at(2.0):at(3.5)] = np.linspace(0.2, 1, at(3.5) - at(2.0))
duck[at(52.0):at(53.0)] = np.linspace(1, 0.1, at(53.0) - at(52.0))
duck[at(53.0):at(54.5)] = np.linspace(0.1, 1, at(54.5) - at(53.0))
mix *= duck[:, None]

# ---------- sound effects ----------
def whoosh(dur=1.0, rise=True):
    n = int(dur * SR); x = rng.standard_normal(n)
    k = np.linspace(0.02, 0.4, n) if rise else np.linspace(0.4, 0.02, n)
    y = np.empty(n); acc = 0.0
    for i in range(n):
        acc += k[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, n)) ** 2

def impact():
    n = int(1.6 * SR); tt = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (90 * tt - 25 * tt ** 2)) * np.exp(-tt * 3)
    crack = rng.standard_normal(n) * np.exp(-tt * 30)
    return sweep + 0.4 * crack

def pop():
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 4000 * tt) * tt) * np.exp(-tt * 60)

def tick():
    n = int(0.03 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 3000 * tt) * np.exp(-tt * 200)

def glitch(dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * 220 * tt)) * (rng.random(n // 1000 + 1).repeat(1000)[:n] > 0.4)
    return sq * env(n, 0.005, 0.1) * 0.6

def waves(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    surf = lowpass(rng.standard_normal(n), 0.05)
    return surf * (0.5 + 0.5 * np.sin(2 * np.pi * tt / 4)) * env(n, 1.0, 1.0) * 3

add(whoosh(1.4), 0.7, 0.8)          # moon builds
add(impact(), 2.0, 0.9)             # moon vanishes
add(waves(8), 11, 0.35, pan=-0.3)   # tide scene
add(waves(8), 19, 0.25, pan=0.3)    # Chek Jawa
add(glitch(), 31.2, 0.35)           # coral spawning freezes
for k in np.arange(45, 48.5, 0.25):  # clock spins
    add(tick(), k, 0.25)
add(whoosh(1.5), 51.5, 0.7)          # riser into twist
add(impact(), 53.0, 0.6)
for c in [0.2, 2.3, 4.7, 6.1, 8.3, 11.3, 15.8, 19.4, 22.8, 27.3, 31.4,
          35.3, 38.0, 41.2, 45.3, 48.6, 53.2, 54.2, 56.0]:  # caption pop-ins
    add(pop(), c, 0.18)

# fade out + normalize
mix[-at(2.5):] *= np.linspace(1, 0, at(2.5))[:, None]
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", sys.argv[1])
