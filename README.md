# Réemploi du FACOM SCANDIAG® — Concours Ynov × FACOM

Donner une seconde vie au **FACOM SCANDIAG® `DX.TSCANPB`** (analyseur de freins/pneus à laser + caméra)
par rétro-ingénierie et réemploi de ses composants.

## Contenu

- **`tools/`** — scripts pour dialoguer avec l'outil et extraire ses données (voir `tools/README.md`).
- **`poc/`** — preuves de concept, Phase 4 (voir `poc/README.md`).
- **`FACOM_SCANDIAG/`** — contenu d'origine du CD FACOM (manuels, drivers). Les gros `.exe` sont ignorés par git.
- **`DOSSIER_RETRO-INGENIERIE.md`** — Phases 1 & 2 : composants, schéma fonctionnel, ce qui est réutilisable.
- **`PHASE3_IDEATION.md`** — Phase 3 : les 9 concepts de réemploi, avec notes.

## En bref

L'outil = une plateforme embarquée réutilisable : MCU, caméra OV9712, laser vert 3R, Bluetooth,
batterie Li-Ion, bouton/LED, aimant. Il se connecte au PC via un port série (FTDI USB `0403:6001`
ou Bluetooth SPP `LSG1MT6LT000889`).