# `poc/` — Preuves de concept (Phase 4)

Ce dossier contient les démonstrateurs réalisés à partir des concepts de réemploi de la Phase 3.
Chaque POC est autonome dans son sous-dossier.

## `ocr-webcam/` — ReadAid : lecture de texte par laser + OCR local

Démonstrateur du **concept 8 (ReadAid)** : un lecteur OCR portable où un faisceau laser matérialise
la ligne de lecture et où la reconnaissance de texte se fait sur une image capturée par la caméra.
Le POC reproduit cette chaîne **dans le navigateur**, en remplaçant temporairement la caméra OV9712
de l'outil par la webcam du PC, le temps de valider le principe.

### Ce que ça fait

1. La page ouvre la **webcam** (`getUserMedia`) et l'affiche en direct.
2. Une **ligne laser verte déplaçable** délimite la zone à lire (le texte situé **au-dessus** du
   trait). C'est l'équivalent logiciel du laser-guide du SCANDIAG.
3. À la demande (« Lire la zone ») ou en continu, la portion d'image au-dessus du laser est
   **capturée sur un `<canvas>`** et encodée en base64.
4. L'image est envoyée à un **modèle OCR exécuté en local via Ollama** (`glm-ocr`), qui renvoie le
   texte transcrit.
5. Le texte est affiché à côté de la vidéo.

### Architecture

```
   Webcam ──getUserMedia──► <video> ──crop au-dessus du laser──► <canvas> ──base64──┐
                                                                                     │ HTTP POST
                                                                                     ▼
                                                          Ollama (local :11434) — modèle glm-ocr
                                                                                     │
                                                                  texte transcrit ◄──┘
                                                                                     ▼
                                                                            affichage résultat
```

Tout tourne **en local** : la page est servie en HTTP (obligatoire car `getUserMedia` exige un
contexte sécurisé), et l'OCR est fait par Ollama sur la machine — aucune donnée n'est envoyée vers
le cloud.

### Correspondance avec le produit réel

| Élément du POC | Équivalent sur le SCANDIAG |
|---|---|
| Webcam du PC | Caméra OV9712 de l'outil |
| Ligne laser verte à l'écran | Diode laser verte 3R (ligne-guide) |
| Canvas + envoi HTTP | Liaison Bluetooth/série vers le PC |
| Ollama / glm-ocr sur le PC | Traitement OCR déporté sur le smartphone/PC |

Le POC valide donc la **partie traitement** (cadrage par laser → OCR → texte). L'étape suivante,
sur le matériel réel, consiste à remplacer la webcam par le flux de la caméra de l'outil une fois
celui-ci récupéré (voir `../tools/`).

### Lancer le POC

Pré-requis : Python 3, [Ollama](https://ollama.com) avec un modèle OCR.
```bash
ollama serve                 # démarre Ollama (port 11434)
ollama pull glm-ocr          # récupère le modèle OCR (si absent)
./ocr-webcam/start.sh        # sert la page et ouvre http://localhost:8000
```
Si le navigateur affiche « Connexion à Ollama impossible », relance Ollama en autorisant l'origine
du navigateur : `OLLAMA_ORIGINS='*' ollama serve`.

### Fichiers

- `ocr-webcam/index.html` — toute l'application (UI, capture caméra, laser déplaçable, appel OCR).
- `ocr-webcam/start.sh` — sert la page en local et vérifie qu'Ollama répond.

### Limites connues

- L'OCR dépend de la **netteté** de l'image : sur le matériel réel, l'optique de l'OV9712 est figée
  pour la mesure rapprochée des disques de frein et devra être adaptée pour lire du texte.
- Le laser de l'outil est de **classe 3R** : un usage « aide visuelle » impose des précautions
  oculaires (cf. dossier de rétro-ingénierie).
