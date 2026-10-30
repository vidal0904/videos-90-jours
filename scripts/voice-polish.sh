#!/usr/bin/env bash
# Adoucit une voix Kokoro : moins de brillance métallique, un peu de chaleur, une petite
# pièce, niveau normalisé. Ne déplace aucun mot (les horaires restent valides).
#   scripts/voice-polish.sh assets/voice/<nom>.wav   → assets/voice/<nom>.final.wav
set -euo pipefail
in="$1"; out="${in%.wav}.final.wav"
ffmpeg -v error -y -i "$in" -af "\
highpass=f=75,\
equalizer=f=190:t=q:w=1.0:g=2.5,\
equalizer=f=3200:t=q:w=1.4:g=-2,\
deesser=i=0.35,\
lowpass=f=10500,\
acompressor=threshold=-20dB:ratio=2.2:attack=12:release=180:makeup=2,\
aecho=0.85:0.6:23|41:0.10|0.06,\
loudnorm=I=-16:TP=-1.5:LRA=9" -ar 44100 "$out"
echo "$out"
