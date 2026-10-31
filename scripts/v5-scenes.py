"""Génère les scènes « chiffre + vraies pages » de la vidéo 5 (décompte exact, BRIEF §2).

Chaque scène : un compteur Lora géant terracotta (0 → N en 0,8 s) avec son libellé, puis les
vraies pages du PDF, chacune posée sur le mot qui la nomme dans la voix. Les instants sont en
secondes locales à la scène (instant vidéo − début de la scène).
"""
P = "capture/pages/"

SCENES = {
    "v5-chapitres": dict(debut=5.45, n=15, t=0.08, libelle="chapitres", sous=None, pages=[
        ("chapitre-10-sucre-p70.png", "Chapitre 10, gérer les envies de sucre", 330, 625, 420, -2, 0.95, None)]),
    "v5-semaines": dict(debut=8.9, n=12, t=0.7, libelle="semaines", sous=None, pages=[
        ("semaine-1-p91.png", "Semaine 1, poser les fondations", 330, 640, 420, 2, 1.35, 2.5),
        ("menu-s1-p94.png", "Menu", 76, 760, 220, -3, 2.7, None),
        ("courses-s1-p95.png", "Courses", 308, 780, 220, 2, 3.9, None),
        ("journal-s1-p96.png", "Journal", 540, 760, 220, -2, 4.55, None),
        ("bilan-s1-p97.png", "Bilan", 772, 780, 220, 3, 5.4, None)]),
    "v5-recettes": dict(debut=15.35, n=70, t=0.1, libelle="recettes", sous="dont <b id=\"v5r-30\">30</b> végétariennes", sous_t=1.5, pages=[
        ("index-recettes-p200.png", "Index des 70 recettes", 200, 720, 420, -3, 0.75, None),
        ("recette-b7-pancakes-p209.png", "Fiche recette B7, pancakes banane-avoine", 450, 735, 420, 3, 1.9, None)]),
    "v5-outils": dict(debut=18.5, n=13, t=0.1, libelle="outils à imprimer", sous=None, pages=[
        ("outil-01-calendrier-p295.png", "Calendrier des 90 jours", 270, 600, 250, -3, 1.45, None),
        ("outil-04-tracker-m1-p298.png", "Tracker d'habitudes", 560, 610, 250, 2, 2.2, None),
        ("outil-07-defi-30-jours-p305.png", "Défi motivation 30 jours", 270, 970, 250, 2, 3.55, None),
        ("outil-certificat-p315.png", "Certificat de parcours", 560, 980, 250, -2, 4.25, None)]),
}

# Libellés des 4 vignettes de la semaine (au-dessus de chaque page)
ETIQUETTES = {"Menu": "Menu", "Courses": "Courses", "Journal": "Journal", "Bilan": "Bilan"}


def scene(nom, d):
    pages = []
    for i, (src, alt, x, y, w, rot, t, sortie) in enumerate(d["pages"]):
        etiq = f'<span class="v5-etiquette">{ETIQUETTES[alt]}</span>' if alt in ETIQUETTES else ""
        pages.append(
            f'    <div id="{nom}-p{i}" class="v5-feuille" data-t="{t}" data-rot="{rot}"'
            f'{f" data-sortie=\"{sortie}\"" if sortie else ""} style="left: {x}px; top: {y}px; width: {w}px">'
            f'<img src="{P}{src}" alt="{alt}" />{etiq}</div>'
        )
    sous = f'\n    <p id="{nom}-sous" class="v5-sous titre" data-t="{d["sous_t"]}"><em>{d["sous"]}</em></p>' if d["sous"] else ""
    return f'''<!-- Vidéo 5 · {str(d["debut"]).replace(".", ",")} s · « {d["n"]} {d["libelle"]} » (BRIEF §2) + vraies pages.
     Généré par scripts/v5-scenes.py : modifier là-bas puis relancer. -->
<template>
  <link rel="stylesheet" href="assets/design/tokens.css" />
  <style>
    #root {{
      position: absolute;
      inset: 0;
    }}
    .v5-compteur {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      top: 220px;
      text-align: center;
    }}
    .v5-chiffre {{
      font-size: 250px;
      color: var(--terracotta);
    }}
    .v5-libelle {{
      margin-top: 4px;
      font-size: 70px;
      color: var(--creme);
    }}
    .v5-sous {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      top: 590px;
      text-align: center;
      font-size: 56px;
    }}
    .v5-sous b {{
      font-weight: 600;
    }}
    .v5-feuille {{
      position: absolute;
      aspect-ratio: 1 / 1.4142;
      border-radius: 6px;
      background: #fff;
      box-shadow: var(--ombre-page), 0 0 0 2px rgba(251, 248, 242, 0.22);
    }}
    .v5-feuille img {{
      width: 100%;
      height: 100%;
      display: block;
      border-radius: 6px;
    }}
    .v5-etiquette {{
      position: absolute;
      left: 0;
      right: 0;
      top: -30px;
      width: fit-content;
      margin: 0 auto;
      padding: 6px 18px 8px;
      border-radius: 999px;
      background: var(--sauge-claire);
      color: var(--vert-foret);
      font-family: var(--font-texte);
      font-weight: 700;
      font-size: 30px;
    }}
  </style>
  <div id="root" data-composition-id="{nom}" data-width="1080" data-height="1920">
    <div class="v5-compteur">
      <div id="{nom}-n" class="v5-chiffre chiffre" data-valeur="{d["n"]}" data-t="{d["t"]}">0</div>
      <div class="v5-libelle titre">{d["libelle"]}</div>
    </div>{sous}
    <div data-layout-allow-overlap>
{chr(10).join(pages)}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // Compteur 0 → N en 0,8 s sur le chiffre dans la voix
    const n = document.getElementById("{nom}-n");
    const c = {{ v: 0 }};
    const t0 = parseFloat(n.dataset.t);
    tl.fromTo(".v5-compteur", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, Math.max(0, t0 - 0.1));
    tl.fromTo(c, {{ v: 0 }}, {{ v: Number(n.dataset.valeur), duration: 0.8, ease: "power2.out", onUpdate: () => (n.textContent = Math.round(c.v)) }}, t0);
    // Sous-titre éventuel (« dont 30 végétariennes ») avec son propre petit compteur
    const sous = document.querySelector(".v5-sous");
    if (sous) {{
      const ts = parseFloat(sous.dataset.t);
      tl.fromTo(sous, {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }}, ts);
      const b = sous.querySelector("b");
      const cb = {{ v: 0 }};
      tl.fromTo(cb, {{ v: 0 }}, {{ v: Number(b.textContent), duration: 0.6, ease: "power2.out", onUpdate: () => (b.textContent = Math.round(cb.v)) }}, ts);
    }}
    // Chaque vraie page sort par le bas et se pose sur son mot ; certaines repartent
    document.querySelectorAll(".v5-feuille").forEach((f) => {{
      const t = parseFloat(f.dataset.t);
      const r = parseFloat(f.dataset.rot);
      tl.fromTo(f, {{ opacity: 0, y: 260, rotation: 0 }}, {{ opacity: 1, y: 0, rotation: r, duration: 0.45, ease: "power3.out" }}, t);
      if (f.dataset.sortie) tl.to(f, {{ opacity: 0, y: -40, scale: 0.9, duration: 0.3, ease: "power2.in" }}, parseFloat(f.dataset.sortie));
    }});
    window.__timelines["{nom}"] = tl;
  </script>
</template>
'''


if __name__ == "__main__":
    for nom, d in SCENES.items():
        open(f"compositions/{nom}.html", "w").write(scene(nom, d))
        print(f"compositions/{nom}.html")
