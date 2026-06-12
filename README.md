# GLITCH — Descent Into the Undercity

An immersive, scroll-driven web experience: a forbidden journey into a secret
underground rave hidden beneath Aarhus.

Not a website. A descent.

## The journey

1. Hidden alley in Aarhus at night — the only message: **ENTER GLITCH**
2. Secret industrial entrance behind caution tape
3. A long 3D service tunnel: flickering fluorescents, concrete, pipes, steam,
   sparks, graffiti, warning signs, wet reflective floors
4. Bass vibrations grow — lights pulse with the kick drum
5. Reality breaks apart into digital glitch particles
6. **The reveal:** a gigantic underground cavern — lasers, floating lights,
   techno monoliths, a suspended DJ booth, dancing silhouettes
7. Explore the zones: Techno District, Open Decks, Hardstyle Arena,
   Psy Forest Chamber
8. The Ticket Portal

## Tech

- Single self-contained `index.html` — zero dependencies, zero external assets
- Scroll-driven CSS 3D tunnel with per-segment fog, culling and procedural decoration
- Canvas FX layer: sparks, steam, digital disintegration particles, floating cavern lights
- Fully synthesized techno engine via the Web Audio API (kick, sub bass, hats,
  claps, acid stabs) — gets louder and brighter the deeper you descend
- Respects `prefers-reduced-motion`

## Run

Open `index.html` in any modern browser, or serve it:

```sh
python3 -m http.server 8000
# → http://localhost:8000
```

Click **ENTER GLITCH** (enables sound) and scroll to descend.

Tell no one. GLITCH does not exist.
