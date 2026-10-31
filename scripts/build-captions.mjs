// Sous-titres karaoké « 90 jours » à partir des timings mot à mot de la voix.
//
//   node scripts/build-captions.mjs assets/voice/<nom>.words.json [out.html] [--depuis N] [--bas PX]
//   --depuis N : commence au mot wN (ex. quand l'accroche affiche déjà la phrase en grand)
//   --bas PX   : bas des sous-titres en px depuis le haut du cadre (défaut 1500)
//   --decalage S : décale tous les horaires de S secondes (voix posée à S s dans la vidéo)
//   --fond 1   : pastille vert forêt derrière le texte, pour les plans sur pages claires
//
// Écrit une scène statique : chaque groupe est un .clip avec ses horaires, chaque mot un
// <span> avec data-debut / data-fin, donc le texte reste modifiable dans le HTML.
// Style (DESIGN.md) : Inter 700, 68 px, blanc, ombre douce, 2 lignes max, mot prononcé
// en terracotta.
import { readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";

const args = process.argv.slice(2);
const option = (nom, defaut) => {
  const i = args.indexOf(nom);
  if (i < 0) return defaut;
  const v = Number(args[i + 1]);
  args.splice(i, 2);
  return v;
};
const depuis = option("--depuis", 0);
const bas = option("--bas", 1500);
const decalage = option("--decalage", 0);
const fond = option("--fond", 0) === 1;
const [src, dstArg] = args;
if (!src) {
  console.error("usage: node scripts/build-captions.mjs <words.json> [out.html]");
  process.exit(1);
}
const nom = basename(src).replace(/\.words\.json$/, "");
const dst = dstArg ?? `compositions/sous-titres-${nom}.html`;
const id = `sous-titres-${nom}`;
const r = (x) => Math.round(x * 1000) / 1000;
const mots = JSON.parse(readFileSync(src, "utf8"))
  .slice(depuis)
  .map((m) => ({ ...m, start: m.start + decalage, end: m.end + decalage }));

// Groupes calmes : 5 mots max, ~38 caractères (2 lignes à 68 px sur 920 px),
// coupure à la ponctuation ou après une pause de 150 ms
const MAX_MOTS = 5;
const MAX_CARS = 38;
const PAUSE = 0.15;
// Un groupe ne finit pas sur un petit mot outil (« reprendre le » / « contrôle… »)
const OUTILS = new Set("le la les l' de du des d' un une son sa ses ton ta tes pour par à au aux en et ou sur avec sans dans ne pas ma mon ta que qui ce cet cette ces est tu je".split(" "));
const groupes = [];
let courant = [];
mots.forEach((m, i) => {
  const suivant = mots[i + 1];
  const cars = [...courant, m].map((x) => x.text).join(" ").length;
  // Un mot de plus permis s'il termine la phrase et tient sur la ligne (pas de « faim. » orphelin)
  const finit = /[.!?…]$/.test(m.text) && courant.length === MAX_MOTS && cars <= MAX_CARS;
  if (courant.length && !finit && (courant.length >= MAX_MOTS || cars > MAX_CARS)) {
    const report = [];
    while (courant.length > 1 && OUTILS.has(courant.at(-1).text.toLowerCase())) report.unshift(courant.pop());
    groupes.push(courant);
    courant = report;
  }
  courant.push(m);
  const finDePhrase = /[.!?…,;:]$/.test(m.text);
  const pause = suivant ? suivant.start - m.end >= PAUSE : true;
  if (finDePhrase || pause || !suivant) {
    groupes.push(courant);
    courant = [];
  }
});
if (courant.length) groupes.push(courant);

const fin = r(mots.at(-1).end + 0.5);
const html = groupes
  .map((g, gi) => {
    const debut = r(Math.max(0.1, g[0].start - 0.08, gi ? groupes[gi - 1].at(-1).end : 0));
    const finG = gi < groupes.length - 1 ? r(groupes[gi + 1][0].start - 0.08) : fin;
    const spans = g
      .map(
        (m) =>
          `<span id="st-${m.id}" class="st-mot" data-debut="${r(m.start)}" data-fin="${r(m.end)}">${m.text}</span>`,
      )
      .join(" ");
    return `    <div id="st-g${gi}" class="clip st-groupe" data-start="${debut}" data-duration="${r(Math.max(0.2, finG - debut))}" data-track-index="${gi % 2}">
      <p class="st-ligne">${spans}</p>
    </div>`;
  })
  .join("\n");

writeFileSync(
  dst,
  `<!-- Généré par scripts/build-captions.mjs depuis ${src}. Corriger le texte ici ; les horaires viennent de la voix. -->
<template>
  <link rel="stylesheet" href="assets/design/tokens.css" />
  <style>
    #root {
      position: absolute;
      inset: 0;
    }
    .st-groupe {
      position: absolute;
      left: var(--safe-x);
      right: var(--safe-x);
      bottom: ${1920 - bas}px;
      text-align: center;
      overflow: visible;
    }
    .st-ligne {
      margin: 0 auto;
      max-width: 920px;${fond ? `
      width: fit-content;
      padding: 10px 30px 14px;
      border-radius: 28px;
      background: rgba(30, 59, 44, 0.94);` : ""}
      font-family: var(--font-texte);
      font-weight: 700;
      font-size: 68px;
      line-height: 1.18;
      color: #ffffff;
      text-shadow: 0 0 2px rgba(0, 0, 0, 0.55), 0 4px 18px rgba(0, 0, 0, 0.45);
    }
    .st-mot {
      display: inline-block;
    }
  </style>
  <div id="root" data-composition-id="${id}" data-width="1080" data-height="1920">
${html}
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    document.querySelectorAll(".st-groupe").forEach((g) => {
      const debut = parseFloat(g.dataset.start);
      tl.fromTo(g.querySelector(".st-ligne"), { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.2, ease: "power3.out" }, debut);
      const motsG = [...g.querySelectorAll(".st-mot")];
      motsG.forEach((m, i) => {
        // Le mot reste surligné jusqu'au mot suivant (pas de clignotement entre deux mots)
        const t0 = parseFloat(m.dataset.debut);
        const t1 = i < motsG.length - 1 ? parseFloat(motsG[i + 1].dataset.debut) : parseFloat(m.dataset.fin);
        tl.fromTo(m, { color: "#ffffff" }, { color: "#C2643F", duration: 0.06, ease: "none", immediateRender: false }, t0);
        tl.to(m, { color: "#ffffff", duration: 0.08, ease: "none" }, t1);
      });
    });
    window.__timelines["${id}"] = tl;
  </script>
</template>
`,
);
console.log(`${dst}: ${groupes.length} groupes, ${mots.length} mots, fin ${fin}s`);
