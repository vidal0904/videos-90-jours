"""Nappe douce lo-fi générée localement (déterministe, aucune source externe).

    python3 -I scripts/music-pad.py <durée_s> assets/music/<nom>.wav [--piano]

--piano : notes de piano espacées (harmoniques qui s'éteignent), sans nappe — pour les
vidéos lentes et douces.

Accords Fmaj7 · Am7 · Dm7 · B♭maj7 en nappe lente + arpège feutré + léger souffle.
Le niveau final (-18 à -22 dB sous la voix, DESIGN.md) se règle au mixage.
"""
import sys
import numpy as np
import soundfile as sf

dur, out = float(sys.argv[1]), sys.argv[2]
PIANO = "--piano" in sys.argv[3:]
SR = 44100
t = np.arange(int(dur * SR)) / SR
rng = np.random.default_rng(90)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


ACCORDS = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 53, 57, 60], [46, 50, 53, 57]]  # F, Am, Dm, B♭
mesure = 60 / 72 * 4  # 72 bpm, 4 temps
nappe = np.zeros_like(t)
arpege = np.zeros_like(t)
n_mesures = int(np.ceil(dur / mesure))
for m in range(n_mesures):
    accord = ACCORDS[m % 4]
    t0 = m * mesure
    seg = (t >= t0) & (t < t0 + mesure + 1.2)
    tt = t[seg] - t0
    env = np.minimum(tt / 0.9, 1) * np.exp(-np.maximum(tt - mesure, 0) / 0.4)
    for note in accord:
        f = hz(note)
        for detune in (-0.12, 0.12):
            nappe[seg] += env * np.sin(2 * np.pi * (f + detune) * tt) * 0.06
    # arpège : croches, notes de l'accord une octave au-dessus, attaque douce
    for k in range(8):
        tk = t0 + k * mesure / 8
        s = (t >= tk) & (t < tk + 1.0)
        tt2 = t[s] - tk
        f = hz(accord[[0, 2, 1, 3, 2, 1, 3, 2][k]] + 12)
        arpege[s] += np.sin(2 * np.pi * f * tt2) * np.exp(-tt2 * 5) * np.minimum(tt2 / 0.01, 1) * 0.05

if PIANO:
    # Piano doux : une note toutes les deux croches, timbre à 3 harmoniques, extinction lente
    nappe[:] = 0
    arpege[:] = 0
    for m in range(n_mesures):
        accord = ACCORDS[m % 4]
        for k in range(4):
            tk = m * mesure + k * mesure / 4
            s_ = (t >= tk) & (t < tk + 3.0)
            tt2 = t[s_] - tk
            f = hz(accord[[0, 2, 1, 3][k]] + 12)
            env = np.exp(-tt2 * 1.4) * np.minimum(tt2 / 0.006, 1)
            arpege[s_] += (np.sin(2 * np.pi * f * tt2) + 0.45 * np.sin(4 * np.pi * f * tt2) * np.exp(-tt2 * 2)
                           + 0.2 * np.sin(6 * np.pi * f * tt2) * np.exp(-tt2 * 3)) * env * 0.05
        # basse tenue, très légère
        s_ = (t >= m * mesure) & (t < m * mesure + mesure + 1)
        tt2 = t[s_] - m * mesure
        arpege[s_] += np.sin(2 * np.pi * hz(accord[0] - 12) * tt2) * np.exp(-tt2 * 0.6) * 0.04

souffle = np.convolve(rng.normal(0, 1, len(t)), np.ones(30) / 30, mode="same") * 0.004
mix = nappe + arpege + (0 if PIANO else souffle)
# filtre passe-bas doux (un pôle) pour l'effet feutré
a = np.exp(-2 * np.pi * 2800 / SR)
y = np.empty_like(mix)
acc = 0.0
for i, x in enumerate(mix):
    acc = (1 - a) * x + a * acc
    y[i] = acc
fade = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 1.5)
y *= fade
y /= np.abs(y).max() * 1.25
gauche = y
droite = np.roll(y, int(0.012 * SR))  # léger élargissement stéréo
sf.write(out, np.stack([gauche, droite], 1), SR)
print(out, f"{dur}s")
