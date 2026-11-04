"""Séries 2 et 3 — génère les vidéos de SCRIPTS-SERIE-2.md et SCRIPTS-SERIE-3.md à partir de blocs.

    python3 -I scripts/serie2.py [01 02 … s3-01 …]     # toutes par défaut (« 01 » = « s2-01 »)

Chaque vidéo = un fond, une musique, une accroche (image 0), une suite de blocs et une fin
(vraies pages + « Commente 90 JOURS », puis retour à l'image 0 pour une boucle sans couture).
La durée suit la voix (dernier mot + 1,6 s) et la musique est régénérée si elle ne colle plus.
Chaque bloc et chaque élément est calé sur un mot de la voix : `m` = indice du mot dans
assets/voice/s2-XX.words.json (instant vidéo = début du mot + DECALAGE).
Écrit compositions/s2-XX-*.html et videos/s2-XX.html (racine à copier dans index.html).
"""
import json
import math
import pathlib
import subprocess
import sys

import soundfile as sf

DECALAGE = 0.6  # la voix démarre 0,6 s après l'image 0 (l'accroche se lit d'abord)
P = "capture/pages/"
COUV = ("couverture.png", "Couverture du guide 90 jours")

# --------------------------------------------------------------------------------------
# Les 10 vidéos (contenu : SCRIPTS-SERIE-2.md ; chiffres : BRIEF-EBOOK.md §2)
# --------------------------------------------------------------------------------------
VIDEOS = {
    "s2-01": dict(titre="Faim ou envie ? Le test des 5 secondes", fond="vert", musique="nappe", mention=True, duree=28,
               accroche="Faim… ou juste envie&#8239;?<br /><em>Fais ce test.</em>",
               blocs=[
                   dict(type="colonnes", m=3, gauche="Faim", droite="Envie", items=[
                       ("droite", "arrive d'un coup", 8), ("droite", "un aliment précis", 16),
                       ("droite", "→ souvent émotionnelle", 22),
                       ("gauche", "monte doucement", 30), ("gauche", "plein d'aliments te vont", 33)]),
                   dict(type="cartes", m=38, titre="Dans le <em>doute</em>", items=[
                       ("1", "Un verre d'eau", None, 42), ("2", "Attends 10 minutes", None, 44),
                       ("3", "Quelques pas", None, 46), ("4", "Réévalue ta faim", None, 49)]),
               ],
               fin=dict(m=51, textes=[("Envoie ça à celle<br /><em>qui grignote le soir</em>", 51)],
                        pages=[("chapitre-10-sucre-p70.png", "Chapitre 10, gérer les envies de sucre", 59), COUV + (61,)], lien=65)),
    "s2-02": dict(titre="La règle des 24 h", fond="vert", musique="nappe", mention=True, duree=26,
               accroche="Un écart, ok.<br /><em>Deux jours de suite&#8239;?</em>",
               blocs=[
                   dict(type="chaine", m=4, piege=9, regle=13, titre_regle="Jamais <em>2 jours</em> de suite"),
                   dict(type="phrases", m=28, items=[("Au repas <em>suivant.</em>", 30), ("Pas lundi.<br /><em>Pas le mois prochain.</em>", 33),
                                                       ("Au repas <em>suivant.</em>", 39)]),
               ],
               fin=dict(m=42, textes=[("Enregistre<br /><em>cette règle</em>", 42)],
                        pages=[("outil-01-calendrier-p295.png", "Calendrier des 90 jours", 44), COUV + (55,)], lien=61)),
    "s2-03": dict(titre="80/20 sans s'interdire le chocolat", fond="vert", musique="nappe", mention=True, duree=26,
               accroche="Tu n'as pas besoin<br />de <em>supprimer le chocolat.</em>",
               blocs=[
                   dict(type="barre", m=8, titre="La règle <em>80/20</em>", t_titre=9, gauche=("80&#8239;%", "aliments nutritifs", 11),
                        droite=("20&#8239;%", "flexibilité", 14), pied=("sans culpabilité", 17)),
                   dict(type="grille", m=19, n=21, cols=7, taille=96, titre="Une <em>semaine</em>", t_titre=19,
                        accents=[5, 9, 20], t_accents=23, legende=("prévus et assumés", 26)),
                   dict(type="grille", m=29, n=100, cols=10, taille=52, titre="1 repas sur <em>100</em>", t_titre=31,
                        accents=[57], t_accents=31, grand=("1&#8239;%", 36)),
               ],
               fin=dict(m=37, textes=[("Envoie ça à ton amie<br /><em>qui s'interdit tout</em>", 37)],
                        pages=[COUV + (40,)], lien=52)),
    "s2-04": dict(titre="3 questions avant tes courses", fond="vert", musique="nappe", mention=True, duree=25,
               accroche="Avant le supermarché,<br /><em>pose-toi ces 3 questions.</em>",
               blocs=[
                   dict(type="cartes", m=6, titre="Avant les <em>courses</em>", items=[
                       ("1", "J'ai ma liste&#8239;?", None, 6), ("2", "J'ai faim&#8239;?", "Si oui, mange d'abord.", 12),
                       ("3", "Était-ce sur ma liste&#8239;?", "Devant chaque produit.", 21)]),
                   dict(type="page", m=37, src="courses-s1-p95.png", alt="Liste de courses de la semaine 1",
                        titre="12 listes <em>déjà calculées</em>", t_titre=41, zoom=(47, "35%", "30%", 1.25)),
               ],
               fin=dict(m=50, textes=[("Enregistre<br /><em>pour tes prochaines courses</em>", 50)],
                        pages=[COUV + (51,)], lien=55)),
    "s2-05": dict(titre="Le kit du Jour 0", fond="vert", musique="nappe", mention=False, duree=27,
               accroche="Avant le jour 1,<br /><em>il y a le jour 0.</em>",
               blocs=[
                   dict(type="compteur", m=8, n=15, libelle="minutes", sous=("pour poser ton point de départ", 11),
                        page=("kit-jour-0-p10.png", "Kit de démarrage, jour 0", 12)),
                   dict(type="cartes", m=16, titre="Ton <em>jour 0</em>", compact=True, items=[
                       (None, "Pourquoi tu commences", None, 16), (None, "Tes repères personnels", None, 19),
                       (None, "Des mesures, si tu le souhaites", None, 22), (None, "Tes 3 premières habitudes", None, 29),
                       (None, "Un engagement envers toi", None, 32)]),
                   dict(type="pastilles", m=37, titre="Tu y <em>reviens</em>", items=[("Jour 30", 42), ("Jour 60", 43), ("Jour 90", 45)],
                        pied=("pour voir le chemin parcouru", 47)),
               ],
               fin=dict(m=51, textes=[("Ton kit du <em>jour 0</em>", 51)],
                        pages=[("kit-jour-0-p10.png", "Kit de démarrage, jour 0", 52), COUV + (55,)], lien=59)),
    "s2-06": dict(titre="Une case vide n'est pas un échec", fond="creme", musique="piano", mention=False, duree=26,
               accroche="Tu as raté un jour&#8239;?<br /><em>Lis ça.</em>",
               blocs=[
                   dict(type="phrases", m=5, items=[("Une case vide<br />n'est pas un échec.", 5), ("C'est une <em>information.</em>", 12)]),
                   dict(type="tracker", m=15, n=14, vide=9, reprise=10, t_debut=15, t_fin=18, t_reprise=31,
                        questions=("Fatigue&#8239;? Imprévu&#8239;? Journée chargée&#8239;?", 19), pied=("Tu notes, tu ajustes, tu reprends.", 24)),
                   dict(type="phrases", m=34, items=[("Une journée non cochée<br /><em>n'efface rien.</em>", 34),
                                                       ("Les progrès lents<br /><em>restent des progrès.</em>", 40)]),
               ],
               fin=dict(m=46, textes=[("Envoie ça à quelqu'un<br /><em>qui en a besoin</em>", 46)],
                        pages=[("outil-04-tracker-m1-p298.png", "Tracker d'habitudes, mois 1", 55), COUV + (56,)], lien=59)),
    "s2-07": dict(titre="23 recettes en 15 minutes", fond="vert", musique="nappe", mention=True, duree=29,
               accroche="Pas le temps de cuisiner&#8239;?<br /><em>23 recettes en 15 minutes.</em>",
               blocs=[
                   dict(type="compteur", m=5, n=23, t_n=8, libelle="recettes express", sous=("≈ 15 minutes", 13)),
                   dict(type="cartes", m=18, titre=None, compact=True, items=[
                       ("Matin", "Omelette tomate & fines herbes", None, 18), ("Matin", "Yaourt grec & fruits rouges", None, 24),
                       ("Midi", "Salade de thon au citron", None, 31), ("Midi", "Wrap au thon & crudités", None, 37),
                       ("Soir", "Crevettes sautées & riz complet", None, 45)]),
               ],
               fin=dict(m=50, textes=[("Enregistre<br /><em>pour tes soirs sans énergie</em>", 50)],
                        pages=[("index-recettes-p200.png", "Index des 70 recettes", 58), COUV + (60,)], lien=64)),
    "s2-08": dict(titre="4 phrases quand tu doutes", fond="creme", musique="piano", mention=False, duree=23,
               accroche="Garde ces 4 phrases<br /><em>pour les jours difficiles.</em>",
               blocs=[
                   dict(type="phrases", m=7, carte=True, items=[
                       ("Un écart n'efface pas<br /><em>mes progrès.</em>", 7), ("Je choisis la régularité<br /><em>plutôt que la perfection.</em>", 13),
                       ("Je progresse<br /><em>à mon rythme.</em>", 21), ("Ma valeur ne dépend pas<br /><em>d'un chiffre.</em>", 26)]),
               ],
               fin=dict(m=34, textes=[("Enregistre-les<br /><em>ou envoie-les</em>", 34), ("24 affirmations<br /><em>+ 100 phrases</em>", 46)],
                        pages=[("outil-10-affirmations-p310.png", "24 affirmations positives", 42), COUV + (47,)], lien=54)),
    "s2-09": dict(titre="Et après le jour 90 ?", fond="vert", musique="nappe", mention=False, duree=24,
               accroche="Le plus important,<br /><em>c'est après le jour 90.</em>",
               blocs=[
                   dict(type="pastilles", m=12, titre="Un <em>bilan</em>", items=[("Jour 30", 21), ("Jour 60", 22), ("Jour 90", 24)]),
                   dict(type="cartes", m=25, titre="Une partie pour <em>durer</em>", items=[
                       (None, "L'effet yoyo", None, 31), (None, "Les écarts sans culpabilité", None, 33), (None, "La motivation", None, 37)]),
                   dict(type="phrases", m=39, items=[("Un plan pour les<br /><em>mois 4 à 12</em>", 39)]),
               ],
               fin=dict(m=46, textes=[("Les 3 habitudes<br /><em>que tu gardes</em>", 46)],
                        pages=[("outil-certificat-p315.png", "Certificat de parcours", 48), COUV + (52,)], lien=56)),
    "s2-10": dict(titre="Défi : 7 jours, 7 missions", fond="vert", musique="nappe", mention=True, duree=29,
               accroche="7 missions simples<br /><em>pour reprendre de l'élan.</em>",
               blocs=[
                   dict(type="cartes", m=6, titre="Défi <em>7 jours</em>", note="Adapte chaque mission à ta condition physique.",
                        compact=True, coche=True, items=[
                            ("1", "Bois suffisamment d'eau", None, 6), ("2", "Marche au moins 20 minutes", None, 10),
                            ("3", "Un légume à chaque repas", None, 16), ("4", "Une journée sans boisson sucrée", None, 22),
                            ("5", "Couche-toi pour une vraie nuit", None, 28), ("6", "Un repas maison", None, 34),
                            ("7", "5 raisons de prendre soin de toi", None, 38)]),
               ],
               fin=dict(m=46, textes=[("Enregistre<br /><em>et commence demain</em>", 46)],
                        pages=[("outil-07-defi-30-jours-p305.png", "Défi motivation 30 jours", 50), COUV + (53,)], lien=57)),
}

# --------------------------------------------------------------------------------------
# Série 3 — Reels de vente (SCRIPTS-SERIE-3.md, VENTE-REELS.md). Ancres : "@mot" = 1re occurrence du mot
# affiché (minuscules, sans ponctuation), "@mot#2" = 2e occurrence.
# --------------------------------------------------------------------------------------
VIDEOS.update({
    "s3-01": dict(titre="Ce que tu reçois vraiment", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Ce que tu reçois<br /><em>vraiment</em> dans mon guide.",
                  blocs=[
                      dict(type="compteur", m="@316", n=316, libelle="pages", sous=("à lire sur téléphone, tablette, ordi", "@pages")),
                      dict(type="pages", m="@12", items=[
                          ("menu-s1-p94.png", "Menu de la semaine 1", "12 menus<br /><em>déjà faits</em>", "@12"),
                          ("courses-s1-p95.png", "Liste de courses de la semaine 1", "12 listes de courses<br /><em>quantités pour 1</em>", "@12#2"),
                          ("index-recettes-p200.png", "Index des 70 recettes", "70 recettes<br /><em>dont 23 express</em>", "@70"),
                          ("outil-01-calendrier-p295.png", "Calendrier des 90 jours", "13 outils<br /><em>à imprimer</em>", "@13")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s3-02": dict(titre="Pour qui, pas pour qui", fond="creme", musique="piano", mention=True, duree=0,
                  accroche="Ce guide n'est pas<br /><em>pour tout le monde.</em>",
                  blocs=[
                      dict(type="colonnes", m="@il", gauche="Pour toi", droite="Pas pour toi", taille_titre=72, items=[
                          ("gauche", "Un cadre simple, jour après jour", "@cadre"),
                          ("gauche", "Arrêter de recommencer lundi", "@assez"),
                          ("gauche", "Sans compter les calories", "@compter"),
                          ("droite", "Un régime strict", "@régime"),
                          ("droite", "Un résultat promis d'avance", "@résultat")]),
                      dict(type="phrases", m="@ici", items=[("On construit<br /><em>des habitudes.</em>", "@ici")]),
                  ],
                  fin=dict(m="@si#5", textes=[], pages=[COUV + ("@si#5",)], lien=0)),
    "s3-03": dict(titre="Une semaine avec le guide", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Une semaine<br /><em>avec mon guide.</em>",
                  blocs=[
                      dict(type="pages", m="@dimanche", items=[
                          ("menu-s1-p94.png", "Menu de la semaine 1", "Dimanche&#8239;:<br /><em>le menu est prêt</em>", "@dimanche"),
                          ("courses-s1-p95.png", "Liste de courses de la semaine 1", "<em>La liste aussi</em>", "@liste"),
                          ("batch-cooking-p199.png", "Batch cooking du dimanche", "Batch cooking<br /><em>60 à 90 min</em>", "@batch"),
                          ("outil-02-checklist-p296.png", "Checklist quotidienne", "Chaque jour&#8239;:<br /><em>ta checklist</em>", "@chaque"),
                          ("journal-s1-p96.png", "Journal de la semaine 1", "Ton journal…", "@journal"),
                          ("bilan-s1-p97.png", "Bilan de la semaine 1", "<em>…et ton bilan</em>", "@bilan")]),
                      dict(type="phrases", m="@suivante", items=[("La semaine suivante,<br /><em>tout est prêt à nouveau.</em>", "@suivante")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s3-04": dict(titre="Encore un régime ? Non.", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Encore un régime&#8239;?<br /><em>Non. Voilà pourquoi.</em>",
                  blocs=[
                      dict(type="cartes", m="@aucun", titre="Pas un <em>régime</em>", items=[
                          ("1", "Aucun aliment interdit", None, "@aucun"),
                          ("2", "Aucune calorie à compter", "Aucune n'est indiquée&#8239;: c'est un choix.", "@aucune"),
                          ("3", "80&#8239;% nutritif, 20&#8239;% flexible", "Sans culpabilité.", "@80"),
                          ("4", "Après un écart", "On reprend au repas suivant, pas lundi.", "@après")]),
                      dict(type="phrases", m="@ce", items=[("Pas un régime&#8239;:<br /><em>un cadre de 90 jours.</em>", "@ce")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s3-05": dict(titre="Sans plan ou avec un plan ?", fond="creme", musique="piano", mention=True, duree=0,
                  accroche="Sans plan,<br /><em>ou avec un plan&#8239;?</em>",
                  blocs=[
                      dict(type="colonnes", m="@sans#2", gauche="Sans plan", droite="Avec le guide", taille_titre=66, items=[
                          ("gauche", "Courses au hasard", "@courses"),
                          ("droite", "Liste déjà calculée", "@liste"),
                          ("gauche", "On improvise chaque soir", "@improvises"),
                          ("droite", "Menu de la semaine prêt", "@menu"),
                          ("gauche", "Un écart → on recommence lundi", "@écart"),
                          ("droite", "Un écart → le repas suivant", "@reviens")]),
                      dict(type="phrases", m="@différence", items=[("La différence,<br /><em>c'est l'organisation.</em>", "@différence")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s3-06": dict(titre="3 questions avant de commencer", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="3 questions<br /><em>avant de commencer.</em>",
                  blocs=[
                      dict(type="cartes", m="@faut-il", titre="Tes <em>questions</em>", items=[
                          ("1", "Compter les calories&#8239;?", "Non. Aucune n'est indiquée.", "@faut-il"),
                          ("2", "Des heures en cuisine&#8239;?", "Non&#8239;: 23 recettes express.", "@faut-il#2"),
                          ("3", "Et si je rate un jour&#8239;?", "Tu reprends au repas suivant.", "@rate")]),
                  ],
                  fin=dict(m="@envie", textes=[], pages=[COUV + ("@envie",)], lien=0)),
})

# --------------------------------------------------------------------------------------
# Série 4 — SCRIPTS-SERIE-4.md (vraies pages : recettes B7, L20, D9, semaine 1, journal, bilan, p. 197, mois 1)
# --------------------------------------------------------------------------------------
VIDEOS.update({
    "s4-01": dict(titre="Pancakes banane-avoine, 3 ingrédients", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="3 ingrédients,<br /><em>une vraie gourmandise.</em>",
                  blocs=[
                      dict(type="cartes", m="@une#2", titre="Les <em>ingrédients</em>", compact=True, items=[
                          ("1", "Banane bien mûre", None, "@banane"), ("2", "Œufs", None, "@2 œufs"),
                          ("30 g", "Flocons d'avoine", None, "@30")]),
                      dict(type="cartes", m="@mixe", titre="La <em>recette</em>", compact=True, items=[
                          ("1", "Mixe le tout", None, "@mixe"), ("2", "Poêle légèrement huilée", None, "@chauffe"),
                          ("3", "Petites louches, 1 à 2 min par côté", None, "@verse")]),
                      dict(type="page", m="@le#2", src="recette-b7-pancakes-p209.png", alt="Recette B7, pancakes banane-avoine",
                           titre="Le <em>conseil</em>", t_titre="@conseil"),
                  ],
                  fin=dict(m="@enregistre", textes=[("Enregistre<br /><em>pour ce week-end</em>", "@enregistre")],
                           pages=[("index-recettes-p200.png", "Index des 70 recettes", "@recette"), COUV + ("@commente",)], lien=0)),
    "s4-02": dict(titre="Grand bowl au quinoa, à emporter", fond="creme", musique="piano", mention=True, duree=0,
                  accroche="Un bowl complet,<br /><em>à emporter.</em>",
                  blocs=[
                      dict(type="cartes", m="@du", titre="Grand bowl <em>au quinoa</em>", compact=True, items=[
                          (None, "Quinoa (100 g cuit)", None, "@quinoa"), (None, "Poulet grillé (120 g)", None, "@poulet"),
                          (None, "½ avocat", None, "@avocat"), (None, "1 tomate", None, "@tomate"),
                          (None, "½ concombre", None, "@concombre"), (None, "1 poignée de salade verte", None, "@salade"),
                          (None, "Huile d'olive, citron", None, "@d'huile")]),
                      dict(type="page", m="@cuis", src="recette-l20-bowl-quinoa-p243.png", alt="Recette L20, grand bowl au quinoa",
                           titre="En <em>3 étapes</em>", t_titre="@cuis"),
                      dict(type="phrases", m="@l'astuce", items=[
                          ("Le quinoa se garde<br /><em>4 jours au frais.</em>", "@l'astuce"),
                          ("Version végétarienne&#8239;:<br /><em>pois chiches ou tofu.</em>", "@version")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s4-03": dict(titre="Tu manges végétarien ?", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Tu manges végétarien&#8239;?<br /><em>Regarde ça.</em>",
                  blocs=[
                      dict(type="compteur", m="@dans", t_n="@30", n=30, libelle="recettes végétariennes", sous=("sur 70 recettes", "@70")),
                      dict(type="page", m="@par", src="recette-d9-tofu-p253.png", alt="Recette D9, tofu sauté aux légumes",
                           titre="Tofu sauté<br /><em>façon asiatique</em>", t_titre="@par"),
                      dict(type="cartes", m="@dore", titre="En <em>3 gestes</em>", compact=True, items=[
                          ("1", "Dore le tofu", None, "@dore"), ("2", "Légumes + gingembre", None, "@ajoute"),
                          ("3", "5 min, puis sauce soja", None, "@fais")]),
                      dict(type="phrases", m="@conseil", items=[("Presse le tofu<br /><em>dans un torchon.</em>", "@conseil")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[("recette-d9-tofu-p253.png", "Recette D9, tofu sauté", "@commente"),
                                                            COUV + ("@commente",)], lien=0)),
    "s4-04": dict(titre="4 recettes pour 7 jours", fond="creme", musique="piano", mention=True, duree=0,
                  accroche="Cuisiner tous les soirs&#8239;?<br /><em>Pas besoin.</em>",
                  blocs=[
                      dict(type="page", m="@dans", src="menu-s1-p94.png", alt="Menu de la semaine 1",
                           titre="2 portions&#8239;:<br /><em>ce soir + demain</em>", t_titre="@2"),
                      dict(type="compteur", m="@résultat", t_n="@4", n=4, libelle="recettes", sous=("pour 7 jours", "@7")),
                      dict(type="phrases", m="@et", items=[("Prévue pour 1 personne.<br /><em>Plusieurs&#8239;? Tu multiplies.</em>", "@et")]),
                  ],
                  fin=dict(m="@enregistre", textes=[("Enregistre<br /><em>l'idée</em>", "@enregistre")],
                           pages=[COUV + ("@commente",)], lien=0)),
    "s4-05": dict(titre="Ta semaine 1 : seulement 4 choses", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Ta semaine 1&#8239;:<br /><em>seulement 4 choses.</em>",
                  blocs=[
                      dict(type="cartes", m="@boire", titre="Semaine <em>1</em>", compact=True, coche=True, items=[
                          ("1", "Boire suffisamment d'eau", None, "@boire"), ("2", "Marcher au moins 20 minutes", None, "@marcher"),
                          ("3", "Noter tous tes repas", None, "@noter"), ("4", "Protéger ton sommeil (7 h et +)", None, "@protéger")]),
                      dict(type="page", m="@c'est#2", src="semaine-1-p91.png", alt="Semaine 1, poser les fondations",
                           titre="Une semaine,<br /><em>4 objectifs</em>", t_titre="@c'est#2"),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[COUV + ("@commente",)], lien=0)),
    "s4-06": dict(titre="Le journal du soir : 5 questions", fond="creme", musique="piano", mention=True, duree=0,
                  accroche="5 questions,<br /><em>2 minutes, chaque soir.</em>",
                  blocs=[
                      dict(type="cartes", m="@ai-je", titre="Le journal <em>du soir</em>", compact=True, items=[
                          ("Eau", "Ai-je bu suffisamment&#8239;?", None, "@ai-je"),
                          ("Marche", "Ai-je marché aujourd'hui&#8239;?", None, "@ai-je#2"),
                          ("Repas", "Ai-je mangé consciemment&#8239;?", None, "@ai-je#3"),
                          ("Sommeil", "Combien d'heures vais-je dormir&#8239;?", None, "@combien"),
                          ("Humeur", "Comment je me sens&#8239;?", None, "@comment")]),
                      dict(type="page", m="@c'est", src="journal-s1-p96.png", alt="Journal de la semaine 1",
                           titre="Journal <em>de la semaine</em>", t_titre="@c'est"),
                  ],
                  fin=dict(m="@enregistre", textes=[("Enregistre<br /><em>pour ce soir</em>", "@enregistre")],
                           pages=[COUV + ("@commente",)], lien=0)),
    "s4-07": dict(titre="Le bilan du dimanche", fond="vert", musique="nappe", mention=False, duree=0,
                  accroche="Le dimanche, ne regarde<br /><em>pas que ton poids.</em>",
                  blocs=[
                      dict(type="phrases", m="@dans", items=[("Le poids reste<br /><em>facultatif.</em>", "@dans")]),
                      dict(type="cartes", m="@note", titre="Note <em>aussi</em>", compact=True, items=[
                          (None, "Ton énergie", None, "@énergie"), (None, "Ton sommeil", None, "@sommeil"),
                          (None, "Ta motivation", None, "@motivation")]),
                      dict(type="phrases", m="@qu'est-ce", items=[
                          ("Qu'est-ce qui a<br /><em>bien fonctionné&#8239;?</em>", "@qu'est-ce"),
                          ("Qu'est-ce que<br /><em>j'ajuste&#8239;?</em>", "@qu'est-ce#2")]),
                  ],
                  fin=dict(m="@envoie", textes=[("Envoie ça<br /><em>à quelqu'un</em>", "@envoie")],
                           pages=[("bilan-s1-p97.png", "Bilan de la semaine 1", "@envoie"), COUV + ("@commente",)], lien=0)),
    "s4-08": dict(titre="3 phrases du guide à garder", fond="creme", musique="piano", mention=False, duree=0,
                  accroche="3 phrases<br /><em>à garder.</em>",
                  blocs=[
                      dict(type="phrases", m="@la", carte=True, taille=64, items=[
                          ("La meilleure version<br />de vous-même<br /><em>n'est pas une destination.<br />C'est une direction.</em>", "@la"),
                          ("Vous n'avez pas besoin<br />d'être parfait,<br /><em>seulement constant.</em>", "@vous"),
                          ("Les progrès lents<br /><em>restent des progrès.</em>", "@les#2")]),
                  ],
                  fin=dict(m="@envoie-les", textes=[("Envoie-les<br /><em>à celle qui en a besoin</em>", "@envoie-les")],
                           pages=[("outil-10-affirmations-p310.png", "24 affirmations positives", "@envoie-les"),
                                  COUV + ("@commente",)], lien=0)),
    "s4-09": dict(titre="Pourquoi aucune calorie dans le guide", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="Pourquoi aucune calorie<br /><em>dans mon guide&#8239;?</em>",
                  blocs=[
                      dict(type="cartes", m="@parce", titre="Les chiffres <em>varient</em>", compact=True, items=[
                          (None, "Selon les marques", None, "@marques"), (None, "Selon les tailles", None, "@tailles"),
                          (None, "Selon la cuisson", None, "@cuisson"), (None, "Et selon chaque personne", None, "@besoins")]),
                      dict(type="cartes", m="@à#2", titre="Des repères <em>concrets</em>", compact=True, coche=True, items=[
                          ("1", "La composition de l'assiette", None, "@composition"),
                          ("2", "Des portions pour 1 personne", None, "@portions"),
                          ("3", "Le temps de préparation", None, "@temps")]),
                      dict(type="phrases", m="@si", items=[("Tu as faim&#8239;?<br /><em>Plus de légumes ou de féculents.</em>", "@si")]),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[("bien-utiliser-recettes-p197.png", "Bien utiliser les recettes", "@commente"),
                                                            COUV + ("@commente",)], lien=0)),
    "s4-10": dict(titre="90 jours, une étape à la fois", fond="vert", musique="nappe", mention=True, duree=0,
                  accroche="90 jours,<br /><em>une étape à la fois.</em>",
                  blocs=[
                      dict(type="cartes", m="@mois", titre="3 mois, <em>3 étapes</em>", items=[
                          ("M1", "Installer les bases", "Sans tout changer en même temps.", "@mois"),
                          ("M2", "Renforcer tes habitudes", "Et sortir du mode régime.", "@mois#2"),
                          ("M3", "Consolider", "Et construire ton plan pour la suite.", "@mois#3")]),
                      dict(type="page", m="@chaque", src="ouverture-mois-1-p90.png", alt="Mois 1, installer les bases",
                           titre="Chaque semaine<br /><em>son objectif</em>", t_titre="@chaque"),
                  ],
                  fin=dict(m="@commente", textes=[], pages=[("semaine-1-p91.png", "Semaine 1, poser les fondations", "@commente"),
                                                            COUV + ("@commente",)], lien=0)),
})


def resout(x, mots):
    """Remplace les ancres "@mot" / "@mot#k" par l'indice du mot dans la voix."""
    if isinstance(x, str) and x.startswith("@"):
        cle, _, k = x[1:].partition("#")
        nu = lambda t: t.lower().rstrip(".,;:!?… »").split(" ")[0]
        trouves = [i for i, m in enumerate(mots) if nu(m["text"]) == cle]
        if len(trouves) < int(k or 1):
            sys.exit(f"ancre {x} introuvable")
        return trouves[int(k or 1) - 1]
    if isinstance(x, dict):
        return {c: resout(y, mots) for c, y in x.items()}
    if isinstance(x, (list, tuple)):
        return type(x)(resout(y, mots) for y in x)
    return x

# --------------------------------------------------------------------------------------
# Rendu
# --------------------------------------------------------------------------------------
THEMES = {
    "vert": dict(texte="var(--creme)", em="var(--dore)", carte="rgba(251, 248, 242, 0.08)", bord="rgba(251, 248, 242, 0.22)",
                 carte_texte="var(--creme)", detail="var(--dore)", pastille="var(--creme)", pastille_texte="var(--vert-foret)",
                 fond="compositions/components/fond-vert.html", fond_id="fond-vert"),
    "creme": dict(texte="var(--encre)", em="var(--vert-foret-2)", carte="var(--sauge-claire)", bord="rgba(30, 59, 44, 0.12)",
                  carte_texte="var(--encre)", detail="var(--vert-foret-2)", pastille="var(--vert-foret)", pastille_texte="var(--creme)",
                  fond="compositions/components/fond-creme.html", fond_id="fond-creme"),
}


def scene(nom, commentaire, css, html, js):
    return f'''<!-- {commentaire}
     Généré par scripts/serie2.py : modifier là-bas puis relancer. -->
<template>
  <link rel="stylesheet" href="assets/design/tokens.css" />
  <style>
    #root {{
      position: absolute;
      inset: 0;
    }}
{css}
  </style>
  <div id="root" data-composition-id="{nom}" data-width="1080" data-height="1920">
{html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{nom}"] = tl;
  </script>
</template>
'''


def css_commun(th):
    return f'''    .s2-titre {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      top: 240px;
      text-align: center;
      font-size: 80px;
      color: {th["texte"]};
    }}
    .s2-titre em, .s2-texte em {{
      color: {th["em"]};
    }}
    .s2-texte {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      text-align: center;
      color: {th["texte"]};
    }}'''


ENTREE = '{ opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }'


def rendu_accroche(nom, v, th, fin_t, replique=False):
    css = css_commun(th) + '''
    .s2-accroche {
      top: 560px;
      font-size: 92px;
    }'''
    html = f'    <p id="{nom}-acc" class="s2-texte s2-accroche titre">{v["accroche"]}</p>'
    js = f'    tl.to("#{nom}-acc", {{ opacity: 0, y: -30, duration: 0.3, ease: "power2.in" }}, {fin_t - 0.35:.2f});'
    return css, html, js


def html_feuille(id_, src, alt, extra_style):
    return (f'<div id="{id_}" class="s2-feuille" style="{extra_style}"><img src="{P}{src}" alt="{alt}" /></div>')


CSS_FEUILLE = '''    .s2-feuille {
      position: absolute;
      aspect-ratio: 1 / 1.4142;
      border-radius: 6px;
      overflow: hidden;
      background: #fff;
      box-shadow: var(--ombre-page), 0 0 0 2px rgba(251, 248, 242, 0.22);
    }
    .s2-feuille img {
      width: 100%;
      height: 100%;
      display: block;
    }'''


def rendu_bloc(nom, b, th, t0, T):
    """t0 : début absolu du bloc ; T(m) : instant absolu du mot m. Retourne css, html, js (instants locaux)."""
    L = lambda m, d=0.0: round(T(m) - t0 + d, 2)
    css, html, js = css_commun(th), [], []
    typ = b["type"]
    if typ == "cartes":
        compact = b.get("compact")
        h, gap, fs = (112, 14, 44) if compact else (150, 24, 50)
        if len(b["items"]) >= 7:  # liste longue : doit finir au-dessus des sous-titres
            h, gap, fs = 98, 10, 40
        top = 430 if b.get("titre") else 300
        if b.get("note"):
            top += 40
        css += f'''
    .s2-carte {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      height: {h}px;
      padding: 0 34px;
      border-radius: 26px;
      background: {th["carte"]};
      border: 2px solid {th["bord"]};
      display: flex;
      align-items: center;
      gap: 26px;
    }}
    .s2-num {{
      flex: none;
      min-width: {int(h * 0.6)}px;
      height: {int(h * 0.6)}px;
      padding: 0 14px;
      border-radius: 999px;
      background: {th["pastille"]};
      color: {th["pastille_texte"]};
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-texte);
      font-weight: 700;
      font-size: {int(fs * 0.7)}px;
    }}
    .s2-carte-texte {{
      font-family: var(--font-texte);
      font-weight: 600;
      font-size: {fs}px;
      line-height: 1.12;
      color: {th["carte_texte"]};
    }}
    .s2-carte-detail {{
      display: block;
      margin-top: 6px;
      font-size: 36px;
      color: {th["detail"]};
    }}
    .s2-case {{
      flex: none;
      width: {int(h * 0.5)}px;
      height: {int(h * 0.5)}px;
      border-radius: 12px;
      border: 4px solid {th["carte_texte"]};
      opacity: 0.7;
      position: relative;
    }}
    .s2-case svg {{
      position: absolute;
      inset: -4px;
      width: calc(100% + 8px);
      height: calc(100% + 8px);
      fill: none;
      stroke: var(--terracotta);
      stroke-width: 3.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .s2-note {{
      top: 345px;
      font-family: var(--font-texte);
      font-weight: 500;
      font-size: 32px;
      opacity: 0.8;
    }}'''
        if b.get("titre"):
            html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre"]}</p>')
            js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, 0.05);')
        if b.get("note"):
            html.append(f'    <p id="{nom}-note" class="s2-texte s2-note">{b["note"]}</p>')
            js.append(f'    tl.fromTo("#{nom}-note", {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.4 }}, 0.3);')
        for i, (num, texte, detail, m) in enumerate(b["items"]):
            y = top + i * (h + gap)
            tete = ""
            if b.get("coche"):
                tete = f'<span class="s2-case"><svg viewBox="0 0 24 24"><path id="{nom}-coche-{i}" d="M5 12.5l4.5 4.5 9.5-10" /></svg></span>'
            if num:
                tete += f'<span class="s2-num">{num}</span>'
            det = f'<span id="{nom}-det-{i}" class="s2-carte-detail">{detail}</span>' if detail else ""
            html.append(f'    <div id="{nom}-c{i}" class="s2-carte" style="top: {y}px">{tete}<p class="s2-carte-texte">{texte}{det}</p></div>')
            t = max(0.1, L(m, -0.15))
            js.append(f'    tl.fromTo("#{nom}-c{i}", {{ opacity: 0, x: 60 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "power3.out" }}, {t});')
            if b.get("coche"):
                js.append(f'    tl.fromTo("#{nom}-coche-{i}", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, {{ strokeDashoffset: 0, duration: 0.3, ease: "power2.out" }}, {t + 0.55:.2f});')
    elif typ == "colonnes":
        css += f'''
    .s2-col-titre em {{
      color: {th["em"]};
    }}
    .s2-col-titre {{
      position: absolute;
      top: 250px;
      width: 440px;
      text-align: center;
      font-size: {b.get("taille_titre", 96)}px;
      color: {th["texte"]};
    }}
    .s2-col-item {{
      position: absolute;
      width: 440px;
      padding: 22px 18px;
      border-radius: 24px;
      background: {th["carte"]};
      border: 2px solid {th["bord"]};
      text-align: center;
      font-family: var(--font-texte);
      font-weight: 600;
      font-size: 48px;
      line-height: 1.15;
      color: {th["carte_texte"]};
    }}
    #{nom}-sep {{
      position: absolute;
      left: 539px;
      top: 260px;
      width: 2px;
      height: 960px;
      background: {th["bord"]};
    }}'''
        html.append(f'    <span id="{nom}-sep"></span>')
        html.append(f'    <p id="{nom}-tg" class="s2-col-titre titre" style="left: 80px">{b["gauche"]}</p>')
        html.append(f'    <p id="{nom}-td" class="s2-col-titre titre" style="left: 560px"><em>{b["droite"]}</em></p>')
        js.append(f'    tl.fromTo(["#{nom}-tg", "#{nom}-td"], {ENTREE}, 0.05);')
        js.append(f'    tl.fromTo("#{nom}-sep", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.4, ease: "power2.out" }}, 0.1);')
        # Hauteur estimée de chaque case (~12 caractères par ligne à 48 px sur 440 px) : pas de chevauchement
        import re as _re
        haut = {"gauche": 440, "droite": 440}
        for i, (col, texte, m) in enumerate(b["items"]):
            x = 80 if col == "gauche" else 560
            y = haut[col]
            lignes = max(1, math.ceil(len(_re.sub(r"<[^>]+>|&#?\w+;", "x", texte)) / 12))
            haut[col] += max(190, 44 + 56 * lignes + 26)
            html.append(f'    <p id="{nom}-i{i}" class="s2-col-item" style="left: {x}px; top: {y}px">{texte}</p>')
            js.append(f'    tl.fromTo("#{nom}-i{i}", {ENTREE}, {max(0.1, L(m, -0.1))});')
    elif typ == "phrases":
        carte = b.get("carte")
        css += f'''
    .s2-phrase {{
      top: 660px;
      font-size: {b.get("taille", 84 if not carte else 76)}px;
      line-height: 1.2;
    }}''' + (f'''
    .s2-phrase {{
      left: 100px;
      right: 100px;
      padding: 60px 50px;
      border-radius: 36px;
      background: {th["carte"]};
    }}''' if carte else "")
        items = b["items"]
        for i, (texte, m) in enumerate(items):
            html.append(f'    <p id="{nom}-p{i}" class="s2-texte s2-phrase titre">{texte}</p>')
            t = max(0.05, L(m, -0.1))
            js.append(f'    tl.fromTo("#{nom}-p{i}", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "sine.out" }}, {t});')
            if i < len(items) - 1:
                js.append(f'    tl.to("#{nom}-p{i}", {{ opacity: 0, duration: 0.3, ease: "sine.in" }}, {max(t + 0.6, L(items[i + 1][1], -0.45))});')
        html.insert(0, '    <div data-layout-allow-overlap>')
        html.append('    </div>')
    elif typ == "page":
        css += CSS_FEUILLE + f'''
    #{nom}-cam {{
      position: absolute;
      inset: 0;
      transform-origin: {b["zoom"][1] if b.get("zoom") else "50%"} {b["zoom"][2] if b.get("zoom") else "45%"};
    }}'''
        html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre"]}</p>')
        html.append(f'    <div id="{nom}-cam" data-layout-allow-overflow>{html_feuille(nom + "-f", b["src"], b["alt"], "left: calc(50% - 250px); top: 470px; width: 500px")}</div>')
        js.append(f'    tl.fromTo("#{nom}-f", {{ opacity: 0, y: 200, rotation: 0 }}, {{ opacity: 1, y: 0, rotation: -2, duration: 0.45, ease: "power3.out" }}, 0.05);')
        js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, {max(0.1, L(b["t_titre"], -0.1))});')
        if b.get("zoom"):
            m, _, _, s = b["zoom"]
            js.append(f'    tl.fromTo("#{nom}-cam", {{ scale: 1 }}, {{ scale: {s}, duration: 0.7, ease: "power3.inOut" }}, {L(m, -0.2)});')
    elif typ == "compteur":
        css += f'''
    .s2-chiffre {{
      top: 220px;
      font-size: 250px;
      line-height: 1;
      color: var(--terracotta);
    }}
    .s2-libelle {{
      top: 480px;
      font-size: 70px;
    }}
    .s2-sous {{
      top: 580px;
      font-size: 54px;
    }}''' + (CSS_FEUILLE if b.get("page") else "")
        html.append(f'    <p id="{nom}-n" class="s2-texte s2-chiffre chiffre">0</p>')
        html.append(f'    <p id="{nom}-lib" class="s2-texte s2-libelle titre">{b["libelle"]}</p>')
        t_n = L(b.get("t_n", b["m"]))
        js.append(f'    tl.fromTo(["#{nom}-n", "#{nom}-lib"], {ENTREE}, {max(0.05, t_n - 0.1)});')
        js.append(f'''    const n = document.getElementById("{nom}-n");
    const c = {{ v: 0 }};
    tl.fromTo(c, {{ v: 0 }}, {{ v: {b["n"]}, duration: 0.8, ease: "power2.out", onUpdate: () => (n.textContent = Math.round(c.v)) }}, {max(0.05, t_n)});''')
        if b.get("sous"):
            html.append(f'    <p id="{nom}-sous" class="s2-texte s2-sous titre"><em>{b["sous"][0]}</em></p>')
            js.append(f'    tl.fromTo("#{nom}-sous", {ENTREE}, {L(b["sous"][1], -0.1)});')
        if b.get("page"):
            src, alt, m = b["page"]
            html.append("    " + html_feuille(nom + "-f", src, alt, "left: calc(50% - 210px); top: 690px; width: 420px"))
            js.append(f'    tl.fromTo("#{nom}-f", {{ opacity: 0, y: 200, rotation: 0 }}, {{ opacity: 1, y: 0, rotation: 2, duration: 0.45, ease: "power3.out" }}, {L(m, -0.1)});')
    elif typ == "barre":
        css += f'''
    #{nom}-barre {{
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      top: 640px;
      height: 150px;
      border-radius: 32px;
      overflow: hidden;
      background: {th["carte"]};
    }}
    .s2-seg {{
      position: absolute;
      top: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-titre);
      font-weight: 600;
      font-size: 60px;
      color: var(--creme);
      transform-origin: left center;
    }}
    .s2-seg-legende {{
      position: absolute;
      top: 820px;
      font-family: var(--font-texte);
      font-weight: 600;
      font-size: 42px;
      color: {th["texte"]};
    }}
    .s2-pied {{
      top: 1000px;
      font-size: 72px;
    }}'''
        html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre"]}</p>')
        html.append(f'''    <div id="{nom}-barre"><span id="{nom}-g" class="s2-seg" style="left: 0; width: 80%; background: var(--sauge); color: var(--vert-foret)">{b["gauche"][0]}</span><span id="{nom}-d" class="s2-seg" style="left: 80%; width: 20%; background: var(--terracotta)">{b["droite"][0]}</span></div>''')
        html.append(f'    <p id="{nom}-lg" class="s2-seg-legende" style="left: 80px">{b["gauche"][1]}</p>')
        html.append(f'    <p id="{nom}-ld" class="s2-seg-legende" style="right: 80px">{b["droite"][1]}</p>')
        html.append(f'    <p id="{nom}-pied" class="s2-texte s2-pied titre"><em>{b["pied"][0]}</em></p>')
        js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, {max(0.05, L(b["t_titre"], -0.1))});')
        js.append(f'    tl.fromTo(["#{nom}-g", "#{nom}-lg"], {{ opacity: 0, scaleX: 0 }}, {{ opacity: 1, scaleX: 1, duration: 0.6, ease: "power2.out" }}, {L(b["gauche"][2], -0.1)});')
        js.append(f'    tl.fromTo(["#{nom}-d", "#{nom}-ld"], {{ opacity: 0, scaleX: 0 }}, {{ opacity: 1, scaleX: 1, duration: 0.5, ease: "power2.out" }}, {L(b["droite"][2], -0.1)});')
        js.append(f'    tl.fromTo("#{nom}-pied", {ENTREE}, {L(b["pied"][1], -0.1)});')
    elif typ == "grille":
        n, cols, taille = b["n"], b["cols"], b["taille"]
        gap = 8 if taille < 80 else 14
        largeur = cols * taille + (cols - 1) * gap
        lignes = -(-n // cols)
        haut = 640 if b.get("grand") else 560
        css += f'''
    #{nom}-g {{
      position: absolute;
      left: calc(50% - {largeur // 2}px);
      top: {haut}px;
      width: {largeur}px;
      display: grid;
      grid-template-columns: repeat({cols}, {taille}px);
      grid-auto-rows: {taille}px;
      gap: {gap}px;
    }}
    .s2-cel {{
      border-radius: {max(6, taille // 7)}px;
      background: var(--sauge);
    }}
    .s2-grand {{
      top: 420px;
      font-size: 170px;
      line-height: 1;
      color: var(--terracotta);
    }}
    .s2-legende {{
      top: {haut + lignes * (taille + gap) + 40}px;
      font-size: 64px;
    }}'''
        html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre"]}</p>')
        cel = "".join(f'<span id="{nom}-c{i}" class="s2-cel"></span>' for i in range(n))
        html.append(f'    <div id="{nom}-g">{cel}</div>')
        js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, {max(0.05, L(b["t_titre"], -0.1))});')
        js.append(f'    tl.fromTo("#{nom}-g .s2-cel", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(2)", stagger: {round(0.8 / n, 4)} }}, 0.15);')
        for i in b["accents"]:
            js.append(f'    tl.fromTo("#{nom}-c{i}", {{ backgroundColor: "#8FA68A" }}, {{ backgroundColor: "#C2643F", duration: 0.25, ease: "none", immediateRender: false }}, {L(b["t_accents"])});')
            js.append(f'    tl.fromTo("#{nom}-c{i}", {{ scale: 1 }}, {{ scale: 1.25, duration: 0.18, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false }}, {L(b["t_accents"])});')
        if b.get("legende"):
            html.append(f'    <p id="{nom}-leg" class="s2-texte s2-legende titre"><em>{b["legende"][0]}</em></p>')
            js.append(f'    tl.fromTo("#{nom}-leg", {ENTREE}, {L(b["legende"][1], -0.1)});')
        if b.get("grand"):
            html.append(f'    <p id="{nom}-grand" class="s2-texte s2-grand chiffre">{b["grand"][0]}</p>')
            js.append(f'    tl.fromTo("#{nom}-grand", {ENTREE}, {L(b["grand"][1], -0.1)});')
    elif typ == "tracker":
        n = b["n"]
        css += f'''
    #{nom}-g {{
      position: absolute;
      left: calc(50% - 455px);
      top: 640px;
      width: 910px;
      display: grid;
      grid-template-columns: repeat(7, 118px);
      grid-auto-rows: 118px;
      gap: 14px;
    }}
    .s2-cel {{
      position: relative;
      border-radius: 18px;
      border: 4px solid {th["bord"]};
      background: {th["carte"]};
    }}
    .s2-cel svg {{
      position: absolute;
      inset: 14px;
      fill: none;
      stroke: var(--vert-foret);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .s2-q {{
      top: 300px;
      font-size: 64px;
    }}
    .s2-pied {{
      top: 1000px;
      font-size: 60px;
    }}'''
        cel = "".join(f'<span id="{nom}-c{i}" class="s2-cel"><svg viewBox="0 0 24 24"><path id="{nom}-k{i}" d="M5 12.5l4.5 4.5 9.5-10" /></svg></span>' for i in range(n))
        html.append(f'    <p id="{nom}-q" class="s2-texte s2-q titre"><em>{b["questions"][0]}</em></p>')
        html.append(f'    <div id="{nom}-g">{cel}</div>')
        html.append(f'    <p id="{nom}-pied" class="s2-texte s2-pied titre">{b["pied"][0]}</p>')
        js.append(f'    tl.fromTo("#{nom}-g", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, 0.05);')
        coches = [i for i in range(b["vide"])]
        a, z = L(b["t_debut"]), L(b["t_fin"])
        for k, i in enumerate(coches):
            t = round(a + (z - a) * k / max(1, len(coches) - 1), 2)
            js.append(f'    tl.fromTo("#{nom}-k{i}", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, {{ strokeDashoffset: 0, duration: 0.2, ease: "power2.out" }}, {t});')
        js.append(f'    tl.fromTo("#{nom}-c{b["vide"]}", {{ borderColor: "rgba(30, 59, 44, 0.12)" }}, {{ borderColor: "#C2643F", duration: 0.3, ease: "none", immediateRender: false }}, {round(z + 0.3, 2)});')
        for i in range(b["vide"], n):
            js.append(f'    tl.set("#{nom}-k{i}", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, 0);')
        js.append(f'    tl.fromTo("#{nom}-k{b["reprise"]}", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, {{ strokeDashoffset: 0, duration: 0.3, ease: "power2.out", immediateRender: false }}, {L(b["t_reprise"])});')
        js.append(f'    tl.fromTo("#{nom}-q", {ENTREE}, {L(b["questions"][1], -0.1)});')
        js.append(f'    tl.fromTo("#{nom}-pied", {ENTREE}, {L(b["pied"][1], -0.1)});')
    elif typ == "chaine":
        jours = "L M M J V S D".split()
        css += f'''
    #{nom}-r {{
      position: absolute;
      left: calc(50% - 455px);
      top: 700px;
      width: 910px;
      display: grid;
      grid-template-columns: repeat(7, 118px);
      gap: 14px;
    }}
    .s2-j {{
      text-align: center;
      font-family: var(--font-texte);
      font-weight: 700;
      font-size: 36px;
      color: {th["texte"]};
      opacity: 0.8;
    }}
    .s2-cel {{
      position: relative;
      height: 118px;
      border-radius: 18px;
      border: 4px solid {th["bord"]};
      background: {th["carte"]};
    }}
    .s2-cel svg {{
      position: absolute;
      inset: 14px;
      fill: none;
      stroke: var(--sauge);
      stroke-width: 3.4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .s2-cel b {{
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-titre);
      font-size: 64px;
      color: var(--terracotta);
    }}'''
        tete = "".join(f'<span class="s2-j">{j}</span>' for j in jours)
        cel = "".join(f'<span id="{nom}-c{i}" class="s2-cel"><svg viewBox="0 0 24 24"><path id="{nom}-k{i}" d="M5 12.5l4.5 4.5 9.5-10" /></svg>{"<b id=" + chr(34) + nom + "-q" + chr(34) + ">?</b>" if i == 2 else ""}</span>' for i in range(7))
        html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre_regle"]}</p>')
        html.append(f'    <div id="{nom}-r">{tete}{cel}</div>')
        js.append(f'    tl.fromTo("#{nom}-r", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, 0.05);')
        js.append(f'    tl.fromTo("#{nom}-k0", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, {{ strokeDashoffset: 0, duration: 0.25 }}, 0.4);')
        js.append(f'    tl.set("#{nom}-k1", {{ opacity: 0 }}, 0);  // le jour de l\'écart n\'est pas coché')
        js.append(f'    tl.fromTo("#{nom}-c1", {{ borderColor: "rgba(251, 248, 242, 0.22)", backgroundColor: "rgba(251, 248, 242, 0.08)" }}, {{ borderColor: "#C2643F", backgroundColor: "rgba(194, 100, 63, 0.35)", duration: 0.3 }}, 0.6);')
        js.append(f'    tl.fromTo("#{nom}-q", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {L(b["piege"], -0.1)});')
        js.append(f'    tl.fromTo("#{nom}-c2", {{ borderColor: "rgba(251, 248, 242, 0.22)" }}, {{ borderColor: "#C2643F", duration: 0.2, yoyo: true, repeat: 3, immediateRender: false }}, {L(b["piege"])});')
        js.append(f'    tl.to("#{nom}-q", {{ opacity: 0, duration: 0.2 }}, {L(b["regle"], -0.1)});')
        for k, i in enumerate(range(2, 7)):
            js.append(f'    tl.fromTo("#{nom}-k{i}", {{ strokeDasharray: 30, strokeDashoffset: 30 }}, {{ strokeDashoffset: 0, duration: 0.25 }}, {L(b["regle"], 0.1 + k * 0.25):.2f});')
        js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, {L(b["regle"], -0.1)});')
    elif typ == "pages":
        # Feuilletage de vraies pages : chacune arrive par la droite et s'empile ; son titre remplace le précédent
        css += CSS_FEUILLE + """
    .s2-pages-titre {
      top: 230px;
      font-size: 76px;
      line-height: 1.12;
    }"""
        items = b["items"]
        rots = [-3, 2.5, -1.5, 3, -2.5, 1.5]
        for i, (src, alt, titre, m) in enumerate(items):
            t = max(0.05, L(m, -0.15))
            html.append(f'    <p id="{nom}-t{i}" class="s2-texte s2-pages-titre titre">{titre}</p>')
            html.append("    " + html_feuille(f"{nom}-f{i}", src, alt, "left: calc(50% - 255px); top: 460px; width: 510px"))
            js.append(f'    tl.fromTo("#{nom}-f{i}", {{ opacity: 0, x: 620, rotation: 12 }}, {{ opacity: 1, x: 0, rotation: {rots[i % 6]}, duration: 0.5, ease: "power3.out" }}, {t:.2f});')
            js.append(f'    tl.fromTo("#{nom}-t{i}", {ENTREE}, {t + 0.05:.2f});')
            if i < len(items) - 1:
                js.append(f'    tl.to("#{nom}-t{i}", {{ opacity: 0, y: -20, duration: 0.2, ease: "power2.in" }}, {max(t + 0.5, L(items[i + 1][3], -0.35)):.2f});')
        html.insert(0, '    <div data-layout-allow-overlap>')
        html.append('    </div>')
    elif typ == "pastilles":
        css += f'''
    #{nom}-ligne {{
      position: absolute;
      left: 150px;
      right: 150px;
      top: 798px;
      height: 4px;
      background: {th["bord"]};
      transform-origin: left center;
    }}
    .s2-past {{
      position: absolute;
      top: 740px;
      width: 240px;
      height: 120px;
      margin-left: -120px;
      border-radius: 999px;
      background: {th["pastille"]};
      color: {th["pastille_texte"]};
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-texte);
      font-weight: 700;
      font-size: 46px;
    }}
    .s2-pied {{
      top: 950px;
      font-size: 64px;
    }}'''
        html.append(f'    <p id="{nom}-titre" class="s2-titre titre">{b["titre"]}</p>')
        html.append(f'    <span id="{nom}-ligne"></span>')
        k = len(b["items"])
        for i, (texte, m) in enumerate(b["items"]):
            x = 150 + 120 + i * (780 - 240) / max(1, k - 1)
            html.append(f'    <span id="{nom}-p{i}" class="s2-past" style="left: {x:.0f}px">{texte}</span>')
            js.append(f'    tl.fromTo("#{nom}-p{i}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {max(0.1, L(m, -0.1))});')
        js.append(f'    tl.fromTo("#{nom}-titre", {ENTREE}, 0.05);')
        js.append(f'    tl.fromTo("#{nom}-ligne", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, 0.2);')
        if b.get("pied"):
            html.append(f'    <p id="{nom}-pied" class="s2-texte s2-pied titre"><em>{b["pied"][0]}</em></p>')
            js.append(f'    tl.fromTo("#{nom}-pied", {ENTREE}, {L(b["pied"][1], -0.1)});')
    else:
        raise SystemExit(f"bloc inconnu : {typ}")
    return css, "\n".join(html), "\n".join(js)


def rendu_fin(nom, v, f, th, t0, T, duree):
    L = lambda m, d=0.0: round(T(m) - t0 + d, 2)
    css = css_commun(th) + CSS_FEUILLE + '''
    .s2-fin-texte {
      top: 260px;
      font-size: 84px;
    }
    .s2-cta {
      top: 230px;
    }
    .s2-cta-titre {
      margin: 0;
      font-size: 84px;
      line-height: 1.15;
    }
    .s2-mot-cle {
      position: relative;
      display: inline-block;
      margin-top: 22px;
      padding: 12px 46px 18px;
      border-radius: 60px;
      background: ''' + th["pastille"] + ''';
      color: ''' + th["pastille_texte"] + ''';
      font-family: var(--font-texte);
      font-weight: 800;
      font-size: 78px;
      letter-spacing: 0.02em;
    }
    .s2-mot-cle::after {
      content: "";
      position: absolute;
      left: 54px;
      bottom: -22px;
      border-left: 0 solid transparent;
      border-right: 30px solid transparent;
      border-top: 24px solid ''' + th["pastille"] + ''';
    }
    .s2-cta-sous {
      margin: 34px 0 0;
      font-family: var(--font-texte);
      font-weight: 500;
      font-size: 42px;
      color: ''' + th["em"] + ''';
    }
    .s2-accroche {
      top: 560px;
      font-size: 92px;
    }
    #''' + nom + '''-boucle {
      position: absolute;
      inset: 0;
    }'''
    html, js = ['    <div data-layout-allow-overlap>'], []
    textes = f["textes"] + [(None, f["lien"])]
    for i, (texte, m) in enumerate(textes):
        if texte is None:  # appel à l'action : le mot-clé à commenter, comme une bulle de commentaire
            html.append(f'      <div id="{nom}-t{i}" class="s2-texte s2-cta"><p class="s2-cta-titre titre">Commente</p>'
                        f'<span class="s2-mot-cle">90 JOURS</span>'
                        f'<p class="s2-cta-sous">et reçois le lien en message privé</p></div>')
        else:
            html.append(f'      <p id="{nom}-t{i}" class="s2-texte s2-fin-texte titre">{texte}</p>')
        t = max(0.05, L(m, -0.1))
        js.append(f'    tl.fromTo("#{nom}-t{i}", {ENTREE}, {t});')
        if i < len(textes) - 1:
            js.append(f'    tl.to("#{nom}-t{i}", {{ opacity: 0, y: -24, duration: 0.25, ease: "power2.in" }}, {max(t + 0.5, L(textes[i + 1][1], -0.35))});')
    # Pages sous le bloc « Commente 90 JOURS » (qui descend jusqu'à ~560 px), au-dessus des sous-titres
    places = (["left: calc(50% - 200px); top: 610px; width: 400px"] if len(f["pages"]) == 1
              else ["left: 150px; top: 600px; width: 380px", "left: 530px; top: 660px; width: 380px"])
    rots = [-2] if len(f["pages"]) == 1 else [-3, 3]
    for i, ((src, alt, m), place, r) in enumerate(zip(f["pages"], places, rots)):
        html.append("      " + html_feuille(f"{nom}-f{i}", src, alt, place))
        depart = "{ opacity: 0, y: 200, rotation: 0 }" if i == 0 else "{ opacity: 0, x: 200, rotation: 0 }"
        arrivee = f"{{ opacity: 1, {'y' if i == 0 else 'x'}: 0, rotation: {r}, duration: 0.45, ease: \"power3.out\" }}"
        js.append(f'    tl.fromTo("#{nom}-f{i}", {depart}, {arrivee}, {max(0.1, L(m, -0.1))});')
    html.append('    </div>')
    # Boucle : la dernière demi-seconde reprend exactement l'image 0
    html.append(f'    <div id="{nom}-boucle" aria-hidden="true" data-layout-allow-overlap>')
    html.append(f'      <p class="s2-texte s2-accroche titre">{v["accroche"]}</p>')
    html.append('    </div>')
    fin_local = round(duree - t0, 2)
    tous = ", ".join(f'"#{nom}-t{len(textes) - 1}"' for _ in [0]) + "".join(f', "#{nom}-f{i}"' for i in range(len(f["pages"])))
    js.append(f'    tl.to([{tous}], {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {fin_local - 0.75:.2f});')
    js.append(f'    tl.fromTo("#{nom}-boucle", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, {fin_local - 0.55:.2f});')
    return css, "\n".join(html), "\n".join(js)


def hote(id_, src, debut, duree, i, kind="graphics"):
    return f'''      <div
        id="{id_}"
        data-composition-id="{id_}"
        data-composition-src="{src}"
        data-start="{round(debut, 2)}"
        data-duration="{round(duree, 2)}"
        data-track-index="{i}"
        data-track-kind="{kind}"
        data-width="1080"
        data-height="1920"
        style="z-index: {i + 1}"
      ></div>'''


def genere(num):
    base = num if num.startswith("s") else f"s2-{num}"
    serie = base[1]
    num = base[3:]
    mots = json.loads(pathlib.Path(f"assets/voice/{base}.words.json").read_text())
    v = resout(VIDEOS[base], mots)
    th = THEMES[v["fond"]]
    T = lambda m: mots[m]["start"] + DECALAGE
    # Durée : dernier mot + 1,6 s (l'écran de fin se lit, puis la boucle) ; ancre du CTA : « commente »
    duree = math.ceil(mots[-1]["end"] + DECALAGE + 1.6)
    v["fin"]["lien"] = max(i for i, m in enumerate(mots) if m["text"].lower() == "commente")
    musique = pathlib.Path(f"assets/music/{base}.wav")
    if not musique.exists() or abs(sf.info(musique).duration - duree) > 0.05:
        subprocess.run([sys.executable, "-I", "scripts/music-pad.py", str(duree), str(musique)]
                       + (["--piano"] if v["musique"] == "piano" else []), check=True, capture_output=True)
    # Découpage : chaque bloc commence 0,25 s avant son premier mot et finit au début du suivant
    debuts = [max(0.0, T(b["m"]) - 0.25) for b in v["blocs"]] + [max(0.0, T(v["fin"]["m"]) - 0.25)]
    scenes, sons = [], []
    # accroche
    css, html, js = rendu_accroche(f"{base}-acc", v, th, debuts[0])
    pathlib.Path(f"compositions/{base}-acc.html").write_text(scene(f"{base}-acc", f"Série {serie} · vidéo {num} « {v['titre']} » · accroche (image 0)", css, html, js))
    scenes.append((f"{base}-acc", 0.0, debuts[0]))
    for k, b in enumerate(v["blocs"]):
        nom = f"{base}-b{k + 1}"
        t0, t1 = debuts[k], debuts[k + 1]
        css, html, js = rendu_bloc(nom, b, th, t0, T)
        pathlib.Path(f"compositions/{nom}.html").write_text(scene(nom, f"Série {serie} · vidéo {num} · bloc {k + 1} ({b['type']}) · {t0:.2f}–{t1:.2f} s", css, html, js))
        scenes.append((nom, t0, t1 - t0))
        sons.append((f"sfx-b{k + 1}", "assets/sfx/whoosh-short.mp3", round(t0 + 0.2, 2), 0.3))
    nom = f"{base}-fin"
    t0 = debuts[-1]
    css, html, js = rendu_fin(nom, v, v["fin"], th, t0, T, duree)
    pathlib.Path(f"compositions/{nom}.html").write_text(scene(nom, f"Série {serie} · vidéo {num} · fin + boucle · {t0:.2f}–{duree} s", css, html, js))
    scenes.append((nom, t0, duree - t0))
    sons.append(("sfx-lien", "assets/sfx/chime.mp3", round(T(v["fin"]["lien"]), 2), 0.3))

    hotes = [hote(th["fond_id"], th["fond"], 0, duree, 0)]
    for i, (n, d, du) in enumerate(scenes):
        hotes.append(hote(n, f"compositions/{n}.html", d, du, i + 1))
    i = len(scenes) + 1
    if v["mention"]:
        hotes.append(hote("mention-sante", "compositions/mention-sante.html", 0, duree, i))
        i += 1
    hotes.append(hote(f"sous-titres-{base}", f"compositions/{base}-sous-titres.html", 0, duree, i, "captions"))
    i += 1
    audio = [("voix", f"assets/voice/{base}.final.wav", DECALAGE, 1), ("musique", f"assets/music/{base}.wav", 0, 1),
             ("sfx-accroche", "assets/sfx/whoosh.mp3", 0.05, 0.35)] + sons
    for j, (id_, src, st, vol) in enumerate(audio):
        hotes.append(f'      <audio id="{id_}" class="clip" src="{src}" data-start="{st}" data-track-index="{i + j}" data-volume="{vol}"></audio>')
    tete = pathlib.Path("videos/video-01.html").read_text()
    tete = tete[:tete.index("<body>")].replace("background: var(--vert-foret);", f"background: var(--{'vert-foret' if v['fond'] == 'vert' else 'creme'});")
    racine = tete + f'''<body>
    <!-- Série {serie} · vidéo {num} — « {v["titre"]} » · {duree} s (SCRIPTS-SERIE-{serie}.md ; généré par scripts/serie2.py) -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duree}" data-width="1080" data-height="1920">
{chr(10).join(hotes)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
'''
    pathlib.Path(f"videos/{base}.html").write_text(racine)
    print(f"videos/{base}.html · {len(scenes)} scènes · {duree} s")


if __name__ == "__main__":
    for num in (sys.argv[1:] or sorted(VIDEOS)):
        genere(num)
