"""French voiceover with word timings, offline.

    python3 -I scripts/voice.py assets/voice/<name>.txt [--moteur piper|kokoro] [--speed 1.0]

Voix retenue pour la série : Piper « siwis » medium (féminine, fr-FR), `--moteur piper`.

Writes assets/voice/<name>.wav and assets/voice/<name>.words.json
([{id, text, start, end}], seconds), the shape the captions build expects.
Timings come from the model's own phoneme durations (Piper: alignment output patched
in memory; Kokoro: a `duration` output, see export-timed-model.py), so they match the
audio exactly.
"""
import argparse
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

CACHE = pathlib.Path.home() / ".cache/hyperframes/tts"
MODEL = CACHE / "models/kokoro-v1.0-timed.onnx"
VOICES = CACHE / "voices/voices-v1.0.bin"
VOICE = "ff_siwis"  # the only French voice in Kokoro: female, fr-FR
PIPER = pathlib.Path.home() / ".cache/piper/voice-fr-siwis-medium/fr-siwis-medium.onnx"

ap = argparse.ArgumentParser()
ap.add_argument("script")
ap.add_argument("--moteur", choices=["piper", "kokoro"], default="piper")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--voice", default=VOICE)
# Pauses un peu plus longues que Kokoro par défaut : « pauses courtes après les phrases-clés »
ap.add_argument("--pause-phrase", type=float, default=0.38)
ap.add_argument("--pause-virgule", type=float, default=0.14)
args = ap.parse_args()

src = pathlib.Path(args.script)
text = " ".join(src.read_text(encoding="utf-8").split())
# En français « ? », « ! », « : » et « ; » sont détachés par une espace : on les colle
# (espace insécable) au mot précédent, ce ne sont pas des mots prononcés
words = []
for token in text.split(" "):
    if words and all(c in "?!:;»" for c in token):
        words[-1] += "\u00a0" + token
    else:
        words.append(token)

# Écrit comme on le dit pour la voix, affiché comme on le lit dans les sous-titres
AFFICHAGE = {"quatre-vingt-dix": "90", "quatre-vingts": "80", "soixante-dix": "70", "douze": "12"}


def affiche(mot):
    coeur = mot.rstrip(".,;:!?…\u00a0»")
    return AFFICHAGE.get(coeur.lower(), coeur) + mot[len(coeur):]

class Ph:
    """Un phonème et l'intervalle (s) où il est prononcé."""

    def __init__(self, phoneme, start, end):
        self.phoneme, self.start, self.end = phoneme, start, end


def kokoro_phonemes():
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(MODEL), str(VOICES))
    if not kokoro.has_timings:
        sys.exit(f"{MODEL} has no duration output: run scripts/export-timed-model.py")
    audio, sr, timings = kokoro.create_timed(
        text, args.voice, speed=args.speed, lang="fr-fr",
        sentence_pause=args.pause_phrase, clause_pause=args.pause_virgule,
    )
    return audio, sr, [Ph(t.phoneme, t.start, t.end) for t in timings]


def piper_phonemes():
    from piper import PiperVoice, SynthesisConfig
    from piper.const import BOS, PAD

    voice = PiperVoice.load(str(PIPER), include_alignments=True)
    id_map = voice.config.phoneme_id_map
    sr = voice.config.sample_rate
    cfg = SynthesisConfig(length_scale=1.0 / args.speed)
    morceaux, phs, t0 = [], [], 0.0
    for chunk in voice.synthesize(text, cfg, include_alignments=True):
        samples = chunk.phoneme_id_samples
        if samples is None:
            sys.exit("Piper n'a pas renvoyé d'alignements (pip install onnx)")
        # Même parcours que piper.phoneme_ids : BOS + PAD, puis id(s) + PAD par phonème
        # connu ; les phonèmes absents de la table (ex. le tilde nasal) n'ont pas d'id
        idx = len(id_map[BOS]) + len(id_map[PAD])
        pos = int(samples[:idx].sum())
        for ph in chunk.phonemes:
            if ph not in id_map:
                continue
            n = len(id_map[ph]) + len(id_map[PAD])
            debut = pos
            pos += int(samples[idx: idx + n].sum())
            idx += n
            phs.append(Ph(ph, t0 + debut / sr, t0 + pos / sr))
        morceaux.append(chunk.audio_float_array)
        t0 += len(chunk.audio_float_array) / sr
        # Une phrase par morceau : petite pause après chaque phrase
        morceaux.append(np.zeros(int(args.pause_phrase * sr), dtype=np.float32))
        t0 += args.pause_phrase
        phs.append(Ph(" ", t0, t0))
    return np.concatenate(morceaux[:-1]), sr, phs


audio, sr, phonemes = piper_phonemes() if args.moteur == "piper" else kokoro_phonemes()

# Phonemes come back as one stream; spaces separate the spoken words
spoken, current = [], []
for p in phonemes:
    if p.phoneme == " ":
        if current:
            spoken.append(current)
        current = []
    elif p.phoneme not in ".,;:!?…":
        current.append(p)
if current:
    spoken.append(current)

if len(spoken) != len(words):
    sys.exit(
        f"{len(words)} words in the script but {len(spoken)} spoken: "
        f"{[''.join(x.phoneme for x in w) for w in spoken]}\n"
        "Rewrite numbers/acronyms the way they are said, or join the words espeak merges."
    )

out = [
    {"id": f"w{i}", "text": affiche(w), "start": round(ph[0].start, 3), "end": round(ph[-1].end, 3)}
    for i, (w, ph) in enumerate(zip(words, spoken))
]
wav = src.with_suffix(".wav")
sf.write(wav, audio, sr)
src.with_suffix(".words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{wav} {len(audio) / sr:.2f}s, {len(out)} words")
