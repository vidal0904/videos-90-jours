"""Affiche le mot-clé du CTA comme on doit le taper : « commente quatre-vingt-dix jours » → « 90 JOURS ».

    python3 -I scripts/mot-cle.py assets/voice/<nom>.words.json

Fusionne les mots « 90 » + « jours » qui suivent « commente » en un seul mot affiché « « 90 JOURS » »
(horaires du premier au dernier) ; les indices des mots suivants baissent de 1.
"""
import json
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
mots = json.loads(p.read_text(encoding="utf-8"))
i = 0
while i < len(mots) - 2:
    a, b, c = mots[i:i + 3]
    if a["text"].lower() == "commente" and b["text"] == "90" and c["text"].rstrip(",.").lower() == "jours":
        fin = c["text"][len("jours"):]
        mots[i + 1:i + 3] = [{"id": "", "text": "« 90 JOURS »" + fin, "start": b["start"], "end": c["end"]}]
    i += 1
for k, m in enumerate(mots):
    m["id"] = f"w{k}"
p.write_text(json.dumps(mots, ensure_ascii=False, indent=1), encoding="utf-8")
print(p, "→", " ".join(m["text"] for m in mots[-10:]))
