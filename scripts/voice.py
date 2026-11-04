"""French voiceover with word timings.

    python3 -I scripts/voice.py assets/voice/<name>.txt [--moteur elevenlabs|piper|kokoro] [--speed 1.0]

Voix retenue pour la série : ElevenLabs « Claire – Warm, Pretty and Charming » (fr-FR),
modèle eleven_multilingual_v2. La clé est ajoutée par le proxy de l'environnement
(secret réseau sur api.elevenlabs.io, en-tête xi-api-key) : elle n'apparaît jamais ici.
Piper « siwis » et Kokoro restent disponibles hors ligne.

Writes assets/voice/<name>.wav and assets/voice/<name>.words.json
([{id, text, start, end}], seconds), the shape the captions build expects.
Timings come from the engine itself (ElevenLabs: per-character alignment of the
with-timestamps endpoint; Piper: alignment output patched in memory; Kokoro: a
`duration` output, see export-timed-model.py), so they match the audio exactly.
"""
import argparse
import base64
import json
import pathlib
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

CACHE = pathlib.Path.home() / ".cache/hyperframes/tts"
MODEL = CACHE / "models/kokoro-v1.0-timed.onnx"
VOICES = CACHE / "voices/voices-v1.0.bin"
VOICE = "ff_siwis"  # the only French voice in Kokoro: female, fr-FR
PIPER = pathlib.Path.home() / ".cache/piper/voice-fr-siwis-medium/fr-siwis-medium.onnx"
ELEVEN_VOICE = "6vTyAgAT8PncODBcLjRf"  # Claire – Warm, Pretty and Charming (bibliothèque, fr-FR)
ELEVEN_MODEL = "eleven_multilingual_v2"

ap = argparse.ArgumentParser()
ap.add_argument("script")
ap.add_argument("--moteur", choices=["elevenlabs", "piper", "kokoro"], default="elevenlabs")
ap.add_argument("--voix-id", default=ELEVEN_VOICE)
ap.add_argument("--stabilite", type=float, default=0.5)
ap.add_argument("--style", type=float, default=0.2)
ap.add_argument("--par-phrase", action="store_true", help="ElevenLabs : une requête par phrase, pauses entre phrases")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--voice", default=VOICE)
# Pauses un peu plus longues que Kokoro par défaut : « pauses courtes après les phrases-clés »
ap.add_argument("--pause-phrase", type=float, default=0.38)
ap.add_argument("--garder-phrases", type=int, default=0,
                help="ElevenLabs --par-phrase : garde la voix et les mots déjà générés des N premières phrases "
                     "(<nom>.wav / .words.json) et ne génère que les phrases suivantes")
ap.add_argument("--pause-virgule", type=float, default=0.14)
args = ap.parse_args()

src = pathlib.Path(args.script)
text = " ".join(src.read_text(encoding="utf-8").split())
PHRASES = [p for p in re.split(r"(?<=[.!?…])\s+", text) if p]
if args.garder_phrases and not (args.moteur == "elevenlabs" and args.par_phrase):
    sys.exit("--garder-phrases ne marche qu'avec --moteur elevenlabs --par-phrase")
# Ce qu'on génère vraiment (tout le texte, ou seulement les phrases après celles qu'on garde)
a_dire = " ".join(PHRASES[args.garder_phrases:])
# En français « ? », « ! », « : » et « ; » sont détachés par une espace : on les colle
# (espace insécable) au mot précédent, ce ne sont pas des mots prononcés
words = []
for token in a_dire.split(" "):
    if words and all(c in "?!:;»" for c in token):
        words[-1] += "\u00a0" + token
    else:
        words.append(token)

# Écrit comme on le dit pour la voix, affiché comme on le lit dans les sous-titres
AFFICHAGE = {"quatre-vingt-dix": "90", "quatre-vingts": "80", "soixante-dix": "70", "douze": "12", "dix": "10",
             "treize": "13", "quinze": "15", "trente": "30", "quatre-vingt-dix-neuf": "99", "vingt": "20",
             "vingt-trois": "23", "vingt-quatre": "24", "soixante": "60", "cent": "100"}
# Nombres en plusieurs mots : fusionnés en un seul mot affiché (horaires du premier au dernier).
# Comparés aux mots écrits (avant AFFICHAGE), les plus longs d'abord.
AFFICHAGE_MULTI = {("trois", "cent", "seize"): "316", ("un", "pour", "cent"): "1\u00a0%",
                   ("quatre-vingts", "pour", "cent"): "80\u00a0%", ("vingt", "pour", "cent"): "20\u00a0%",
                   ("quatre-vingt", "vingt"): "80/20", ("onze", "heures"): "11\u00a0h", ("deux", "minutes"): "2 minutes",
                   ("jour", "zéro"): "jour 0", ("jour", "un"): "jour 1", ("jour", "deux"): "jour 2", ("jour", "trois"): "jour 3",
                   ("jour", "quatre"): "jour 4", ("jour", "cinq"): "jour 5", ("jour", "six"): "jour 6", ("jour", "sept"): "jour 7",
                   ("trois", "questions"): "3 questions", ("quatre", "phrases"): "4 phrases", ("sept", "missions"): "7 missions",
                   ("cinq", "raisons"): "5 raisons", ("deux", "questions"): "2 questions", ("trois", "premières"): "3 premières",
                   ("trois", "habitudes"): "3 habitudes", ("quatre", "à", "douze"): "4 à 12"}


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


def elevenlabs_appel(texte, avant="", apres=""):
    corps = {
        "text": texte,
        "model_id": ELEVEN_MODEL,
        "voice_settings": {
            "stability": args.stabilite,
            "similarity_boost": 0.75,
            "style": args.style,
            "use_speaker_boost": True,
            "speed": args.speed,
        },
    }
    # Phrases voisines : l'intonation reste continue quand on génère phrase par phrase
    if avant:
        corps["previous_text"] = avant
    if apres:
        corps["next_text"] = apres
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{args.voix_id}/with-timestamps"
           "?output_format=mp3_44100_128")
    # curl passe par le proxy de l'environnement, qui ajoute la clé
    r = subprocess.run(
        ["curl", "-sS", "--fail-with-body", "-X", "POST", url, "-H", "Content-Type: application/json",
         "--data-binary", "@-"],
        input=json.dumps(corps).encode(), capture_output=True,
    )
    if r.returncode:
        sys.exit(f"ElevenLabs : {r.stdout.decode()[:400]} {r.stderr.decode()[:200]}")
    rep = json.loads(r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        mp3, wav = pathlib.Path(tmp, "v.mp3"), pathlib.Path(tmp, "v.wav")
        mp3.write_bytes(base64.b64decode(rep["audio_base64"]))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav], check=True)
        audio, sr = sf.read(wav, dtype="float32")
    al = rep["alignment"]
    # Un « phonème » par caractère : les espaces séparent les mots, comme pour les autres moteurs
    phs = [Ph(c, a, b) for c, a, b in zip(al["characters"], al["character_start_times_seconds"],
                                          al["character_end_times_seconds"])]
    return audio, sr, phs


def elevenlabs_phonemes():
    if not args.par_phrase:
        return elevenlabs_appel(text)
    # Une requête par phrase, puis `--pause-phrase` secondes de silence entre les phrases
    phrases = PHRASES
    morceaux, phs, t0, sr = [], [], 0.0, 44100
    for i, phrase in enumerate(phrases):
        if i < args.garder_phrases:
            continue
        audio, sr, ph = elevenlabs_appel(phrase, " ".join(phrases[:i]), " ".join(phrases[i + 1:]))
        phs += [Ph(p.phoneme, p.start + t0, p.end + t0) for p in ph]
        morceaux.append(audio)
        t0 += len(audio) / sr
        if i < len(phrases) - 1:
            morceaux.append(np.zeros(int(args.pause_phrase * sr), dtype=np.float32))
            t0 += args.pause_phrase
            phs.append(Ph(" ", t0, t0))
    return np.concatenate(morceaux), sr, phs


moteurs = {"elevenlabs": elevenlabs_phonemes, "piper": piper_phonemes, "kokoro": kokoro_phonemes}
audio, sr, phonemes = moteurs[args.moteur]()

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
    {"id": f"w{i}", "text": affiche(w), "ecrit": w, "start": round(ph[0].start, 3), "end": round(ph[-1].end, 3)}
    for i, (w, ph) in enumerate(zip(words, spoken))
]
nu = lambda t: t.rstrip(".,;:!?…\u00a0»").lower()
for suite, chiffre in sorted(AFFICHAGE_MULTI.items(), key=lambda kv: -len(kv[0])):
    i = 0
    while i <= len(out) - len(suite):
        bloc = out[i:i + len(suite)]
        if tuple(nu(m["ecrit"]) for m in bloc) == suite:
            fin = bloc[-1]["ecrit"][len(bloc[-1]["ecrit"].rstrip(".,;:!?…\u00a0»")):]
            debut = chiffre[0].upper() + chiffre[1:] if bloc[0]["ecrit"][:1].isupper() else chiffre
            out[i:i + len(suite)] = [{"text": debut + fin, "ecrit": " ".join(m["ecrit"] for m in bloc),
                                      "start": bloc[0]["start"], "end": bloc[-1]["end"]}]
        i += 1
wav = src.with_suffix(".wav")
if args.garder_phrases:
    # On recolle : ancienne voix jusqu'au milieu du silence avant la 1re phrase régénérée, puis la suite
    anciens = json.loads(src.with_suffix(".words.json").read_text(encoding="utf-8"))
    ancien_audio, sr0 = sf.read(wav, dtype="float32")
    if sr0 != sr:
        sys.exit(f"fréquences différentes : {sr0} / {sr}")
    fins = [i for i, m in enumerate(anciens) if re.search(r"[.!?…]$", m["text"])]
    if len(fins) <= args.garder_phrases - 1:
        sys.exit(f"l'ancienne voix n'a que {len(fins)} phrases")
    k = fins[args.garder_phrases - 1] + 1
    coupe = (anciens[k - 1]["end"] + anciens[k]["start"]) / 2
    marge = 0.15
    decal = coupe + marge
    print(f"garde w0–w{k - 1} (… {' '.join(m['text'] for m in anciens[k - 3:k])}), coupe à {coupe:.2f}s")
    garde = ancien_audio[: int(coupe * sr)].copy()
    garde[-int(0.01 * sr):] *= np.linspace(1, 0, int(0.01 * sr), dtype=np.float32)  # pas de clic au raccord
    audio = np.concatenate([garde, np.zeros(int(marge * sr), dtype=np.float32), audio])
    out = anciens[:k] + [{**m, "start": round(m["start"] + decal, 3), "end": round(m["end"] + decal, 3)} for m in out]
out = [{"id": f"w{i}", "text": m["text"], "start": m["start"], "end": m["end"]} for i, m in enumerate(out)]
sf.write(wav, audio, sr)
src.with_suffix(".words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{wav} {len(audio) / sr:.2f}s, {len(out)} words")
