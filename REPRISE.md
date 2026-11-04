# Reprendre le projet dans une nouvelle session

Sources de vérité : `BRIEF-EBOOK.md` (contenu, règles absolues) et `DESIGN.md` (identité visuelle).

## Structure
- `index.html` — racine de la vidéo en cours (une seule racine par projet HyperFrames).
- `videos/video-0N.html` — racine de chaque vidéo (voir `videos/LISEZMOI.md`).
- `compositions/` — scènes (`v1-*`, `v2-*`) et composants partagés (`components/` : fond vert, page du PDF, compteur).
- `assets/design/tokens.css` — couleurs, polices Lora + Inter, zones sûres.
- `capture/pages/` — les 23 vraies pages du PDF ; `capture/brand/` — SVG de l'assiette.
- `assets/voice/` — scripts voix off (`.txt`), audio, horaires mot à mot (`.words.json`).
- `scripts/` — voix (`voice.py`), polissage (`voice-polish.sh`), sous-titres karaoké (`build-captions.mjs`), musique (`music-pad.py`).

## Outils à réinstaller (le conteneur est neuf à chaque session)
    npx hyperframes --version
    apt-get install -y espeak-ng && pip install kokoro-onnx soundfile onnx piper-tts
    # voix Piper « siwis » medium (voix 6, utilisée jusqu'ici)
    mkdir -p ~/.cache/piper && cd ~/.cache/piper && \
      curl -sSL -o v.tar.gz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-fr-siwis-medium.tar.gz && \
      mkdir -p voice-fr-siwis-medium && tar xzf v.tar.gz -C voice-fr-siwis-medium

## Étape suivante prévue
Passer la voix off à ElevenLabs (clé dans la variable `ELEVENLABS_API_KEY`, domaine
`api.elevenlabs.io` autorisé), avec les horaires mot à mot de l'endpoint `with-timestamps`,
puis recaler et re-rendre la vidéo 1, puis la vidéo 2.

## Séries 2 et 3 (vidéos générées par blocs)

Fabriquer ou refaire une vidéo `s2-XX` / `s3-XX` :

```bash
python3 -I scripts/voice.py assets/voice/s3-01.txt --par-phrase --speed 1.0 --pause-phrase 0.4
python3 -I scripts/mot-cle.py assets/voice/s3-01.words.json          # « commente 90 jours » → « 90 JOURS »
bash scripts/voice-polish.sh assets/voice/s3-01.wav --leger
python3 scripts/sous-titres-serie.py s3-01
python3 -I scripts/serie2.py s3-01                                     # scènes + racine videos/s3-01.html (+ musique si besoin)
cp videos/s3-01.html index.html && npx hyperframes render -q draft -f 30 -o renders/s3-01-brouillon.mp4
```

- Changer seulement la fin d'une voix déjà validée : modifier la dernière phrase du `.txt`, puis
  `voice.py … --garder-phrases N` (N = nombre de phrases gardées telles quelles). Seule la suite est régénérée.
- CTA, message privé automatique et règles d'honnêteté : `VENTE-REELS.md`.
