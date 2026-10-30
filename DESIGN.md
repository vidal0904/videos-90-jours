# DESIGN.md — identité visuelle des vidéos « 90 jours »

## Format
- Vertical **1080 × 1920** (9:16), 30 fps. Durée 20 à 45 s selon le script.
- Zones sûres TikTok / Reels / Shorts : garder textes et éléments clés entre **y = 220** et **y = 1520**, et à plus de **80 px** des bords gauche/droit. Rien d'important dans les 400 px du bas (interface des plateformes).

## Couleurs (reprises du PDF)
| Rôle | Hex |
|---|---|
| Vert forêt (fond principal) | `#1E3B2C` |
| Vert forêt 2 | `#2C5240` |
| Sauge | `#8FA68A` |
| Sauge claire (fonds de cartes) | `#EEF2EA` |
| Terracotta (accent, boutons, chiffres clés) | `#C2643F` |
| Terracotta clair | `#F7E7DC` |
| Sable | `#F6F1E7` |
| Crème | `#FBF8F2` |
| Doré doux (italiques sur fond vert) | `#E3CFA6` |
| Encre (texte) | `#23271F` |

Règle : fonds vert forêt ou crème. Un seul accent terracotta par écran.

## Typographie
- Titres : **Lora** (Google Fonts), 600 ; mots-clés en *Lora italique* doré `#E3CFA6` sur fond vert, ou terracotta sur fond crème.
- Texte et sous-titres : **Inter** 500-700.
- Sous-titres de voix off : Inter 700, 64-72 px, blanc avec contour/ombre douce, 2 lignes max, mot prononcé surligné en terracotta (karaoké).
- Grands chiffres (316, 70, 12, 13, 90) : Lora 600, 220-320 px.

## Motion
- Rythme : une idée par plan, coupe ou transition toutes les 1,2 à 2,5 s.
- Entrées : glissement vertical court (24-40 px) + fondu, easing `power3.out`, 0,35-0,5 s.
- Chiffres : compteur qui monte (0 → 70) en 0,8 s.
- Pages du PDF : présentées comme des feuilles avec ombre portée douce (`0 30px 60px rgba(0,0,0,.35)`), légère rotation (±2°), zoom lent (Ken Burns 100 → 108 %), zooms ciblés sur une zone (menu, liste de courses).
- Assiette : les 3 segments apparaissent l'un après l'autre (légumes, protéines, féculents) puis le point « bonnes graisses ».
- Motifs décoratifs : cercles concentriques fins en sauge à 15 % d'opacité, petites feuilles (comme sur les ouvertures de parties du PDF).
- Fin : bouclable (la dernière image rappelle la première) pour favoriser le revisionnage.

## Voix off
- Français, voix féminine chaleureuse, posée, 30-40 ans, tutoiement, débit naturel (≈ 150 mots/min).
- Pas de ton « pub agressive ». Sourire dans la voix, pauses courtes après les phrases-clés.
- Musique : lo-fi / acoustique douce, -18 à -22 dB sous la voix.
