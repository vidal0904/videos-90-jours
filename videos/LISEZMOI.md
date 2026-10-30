# Racines des vidéos de la série

HyperFrames n'accepte qu'une racine par projet : `index.html`.
Chaque vidéo garde ici sa racine ; pour la retravailler ou la re-rendre :

    cp videos/video-01.html index.html
    npx hyperframes render -q delivery -o renders/video-01-final.mp4

Toutes les scènes (`compositions/v1-*`, `v2-*`…) et composants partagés restent en place.
