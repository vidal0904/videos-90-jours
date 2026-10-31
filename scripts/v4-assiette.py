"""Génère le dessin de l'assiette 50/25/25 (vidéo 4) pour deux scènes : v4-assiette et v4-fin.

Reprend capture/brand/assiette-equilibree-50-25-25.svg à l'identique (viewBox 100, mêmes
couleurs), mais chaque part est un cercle à trait épais dont on anime le tracé : la part se
remplit en balayant comme une aiguille. Circonférence réelle (pas de pathLength sur un cercle).
"""
import math

C = round(2 * math.pi * 21, 2)  # rayon du trait 21, épaisseur 42 → secteur plein de rayon 42
PARTS = {
    # id: (couleur, fraction, rotation de départ en degrés depuis 3 h dans le sens horaire)
    "proteines": ("#C2643F", 0.25, -90),
    "feculents": ("#E3CFA6", 0.25, 0),
    "legumes": ("#8FA68A", 0.5, 90),
}


def svg(prefixe):
    parts = "\n".join(
        f'        <circle id="{prefixe}-{nom}" class="{prefixe}-part" cx="50" cy="50" r="21" fill="none" '
        f'stroke="{coul}" stroke-width="42" stroke-dasharray="{round(frac * C, 2)} {C}" '
        f'transform="rotate({rot} 50 50)" data-longueur="{round(frac * C, 2)}" />'
        for nom, (coul, frac, rot) in PARTS.items()
    )
    return f'''<svg id="{prefixe}-svg" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r="48" fill="#fff" stroke="#D7DBD1" stroke-width="1" />
{parts}
        <g id="{prefixe}-joints" stroke="#fff" stroke-width="1.6">
          <line x1="50" y1="50" x2="50" y2="7" /><line x1="50" y1="50" x2="93" y2="50" /><line x1="50" y1="50" x2="50" y2="93" />
        </g>
        <circle id="{prefixe}-graisses" cx="88" cy="18" r="7" fill="#B8945A" />
      </svg>'''


if __name__ == "__main__":
    print(svg("ass"))
