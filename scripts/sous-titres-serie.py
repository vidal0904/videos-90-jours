"""Reconstruit les sous-titres d'une vidéo des séries 2/3 (à relancer après chaque nouvelle voix).

    python3 -I scripts/sous-titres-serie.py s2-01 [s3-02 …]

Les sous-titres commencent au premier bloc (l'accroche affiche déjà la 1re phrase en grand).
"""
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, "scripts")
from serie2 import VIDEOS, resout  # noqa: E402

for base in sys.argv[1:]:
    mots = json.loads(pathlib.Path(f"assets/voice/{base}.words.json").read_text())
    depuis = resout(VIDEOS[base]["blocs"][0]["m"], mots)
    subprocess.run(["node", "scripts/build-captions.mjs", f"assets/voice/{base}.words.json",
                    f"compositions/{base}-sous-titres.html", "--depuis", str(depuis), "--bas", "1430",
                    "--decalage", "0.6", "--fond", "1"], check=True)
