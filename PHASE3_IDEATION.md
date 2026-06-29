# Phase 3 — Idéation : concepts de réemploi du FACOM SCANDIAG®

Concours National Informatique Ynov × FACOM (Stanley Black & Decker).

Briques réutilisables (Phases 1-2) : laser vert à ligne (classe 3R, modulable), caméra OmniVision
OV9712 (1280×800, 30 fps), liaison Bluetooth, batterie Li-Ion rechargeable par USB, bouton + LED RGB,
aimant de fixation, microcontrôleur reprogrammable.

Notation : valeur perçue et difficulté de 1 à 10 ; taux de réemploi en pourcentage du produit réutilisé.

---

## Concept 1 — ScanWear : profilomètre / scanner 3D de surface

**Description.** Le laser projette une ligne sur une pièce, la caméra observe sa déformation, et le
microcontrôleur reconstruit le profil par triangulation. On transforme l'analyseur de freins en
instrument de mesure 3D universel.

**Enjeux RSE / métiers.** La métrologie 3D optique coûte des milliers d'euros : un profilomètre issu
du réemploi la rend accessible et permet de numériser des pièces cassées pour les réimprimer (réparer
plutôt que jeter).

**Fonctions et ajouts.** Utilise laser, caméra, microcontrôleur, Bluetooth, batterie, bouton/LED.
À ajouter : recalibration laser-caméra, traitement d'image (triangulation), idéalement un axe motorisé.

**Valeur : 9/10 — Difficulté : 9/10 — Réemploi : 95 %**

---

## Concept 2 — QualiScan : station d'inspection qualité

**Description.** Appareil fixé en bout de poste : chaque pièce est contrôlée (planéité au laser,
défauts à la caméra). Verdict conforme / non conforme via LED et Bluetooth.

**Enjeux RSE / métiers.** Donne un contrôle qualité automatisé aux PME et ateliers sans budget vision
industrielle ; détecter les défauts tôt réduit le rebut et le gaspillage de matière.

**Fonctions et ajouts.** Utilise caméra, laser, LED, bouton, Bluetooth. À ajouter : support de
fixation, traitement d'image (comparaison à une référence), logique de décision.

**Valeur : 8/10 — Difficulté : 8/10 — Réemploi : 90 %**

---

## Concept 3 — TacoScan : tachymètre / stroboscope laser de maintenance

**Description.** Réutilise le mécanisme d'origine (laser + détection de rotation) pour mesurer le
régime (tr/min) d'une machine tournante. Lecture sur LED ou par Bluetooth.

**Enjeux RSE / métiers.** Maintenance prédictive : repérer balourd, survitesse ou usure avant la
panne prolonge la vie des équipements. L'outil reste dans son habitat naturel, l'atelier.

**Fonctions et ajouts.** Utilise laser, caméra ou capteur Hall, microcontrôleur, Bluetooth, LED,
aimant (fixation). À ajouter : firmware de comptage et mode stroboscope, appli mobile d'affichage.

**Valeur : 7/10 — Difficulté : 5/10 — Réemploi : 80 %**

---

## Concept 4 — ReuseTag : scanner d'inventaire pour le réemploi

**Description.** La caméra lit les codes QR / DataMatrix / codes-barres (laser comme viseur), le
microcontrôleur décode et envoie l'identifiant par Bluetooth au système d'inventaire.

**Enjeux RSE / métiers.** Au cœur du sujet : équiper ressourceries et entrepôts d'occasion d'un
scanner gratuit pour tracer les pièces réemployées. L'outil recyclé sert directement l'économie
circulaire.

**Fonctions et ajouts.** Utilise caméra, laser (viseur), Bluetooth, batterie, bouton, LED. À ajouter :
bibliothèque de décodage de codes (ZXing / ZBar), application d'inventaire.

**Valeur : 8/10 — Difficulté : 5/10 — Réemploi : 85 %**

---

## Concept 5 — MicroView : microscope numérique nomade

**Description.** Caméra + aimant (fixation main-libre) = microscope numérique sans fil. Image diffusée
par Bluetooth ou USB vers tablette pour inspecter soudures, composants, textiles, végétaux.

**Enjeux RSE / métiers.** Outil pédagogique (écoles, fablabs) et aide à la réparation électronique à
très bas coût, issu d'un produit sauvé du rebut.

**Fonctions et ajouts.** Utilise caméra, Bluetooth/USB, batterie, LED (éclairage), aimant, bouton.
À ajouter : optique macro et flux vidéo continu. Le laser n'est pas utilisé.

**Valeur : 7/10 — Difficulté : 4/10 — Réemploi : 70 %**

---

## Concept 6 — LevelLine : niveau / télémètre laser connecté

**Description.** La ligne laser sert de référence de niveau ; la caméra mesure sa position pour
estimer planéité ou distance. Mesures envoyées par Bluetooth au smartphone.

**Enjeux RSE / métiers.** Outil de mesure et de mise à niveau pour artisans et bricoleurs, recyclé
plutôt qu'acheté neuf.

**Fonctions et ajouts.** Utilise laser, caméra, Bluetooth, batterie, bouton/LED. À ajouter :
calibration optique, application mobile, éventuellement une centrale inertielle pour l'inclinaison.

**Valeur : 6/10 — Difficulté : 6/10 — Réemploi : 75 %**

---

## Concept 7 — CountSense : capteur de comptage par vision

**Description.** À poste fixe, la caméra compte les passages ou objets (magasin, file, parking) et
remonte les compteurs par Bluetooth. Nœud IoT autonome sur batterie.

**Enjeux RSE / métiers.** Le comptage d'occupation permet d'optimiser éclairage et chauffage, donc de
réduire la consommation énergétique des petits commerces.

**Fonctions et ajouts.** Utilise caméra, Bluetooth, batterie, microcontrôleur, LED. À ajouter :
algorithme de détection/comptage, passerelle Wi-Fi. Le laser n'est pas utilisé.

**Valeur : 6/10 — Difficulté : 6/10 — Réemploi : 65 %**

---

## Concept 8 — ReadAid : lecteur OCR portable / aide visuelle

**Description.** Stylo-caméra qui scanne une ligne de texte (laser = ligne-guide) ; le smartphone fait
la reconnaissance de caractères pour numériser un document ou lire à voix haute.

**Enjeux RSE / métiers.** Accessibilité et numérisation : un fort impact social qui donne au réemploi
une dimension solidaire.

**Fonctions et ajouts.** Utilise caméra, laser (guide), Bluetooth, batterie, bouton. À ajouter :
chaîne OCR (Tesseract sur mobile) et synthèse vocale.

**Valeur : 7/10 — Difficulté : 7/10 — Réemploi : 70 %**

---

## Concept 9 — ClickPoint : pointeur / télécommande de présentation

**Description.** Réemploi minimal et immédiat : laser + bouton + Bluetooth = télécommande de
présentation servant de pointeur et de commande pour les diapositives.

**Enjeux RSE / métiers.** Valorisation immédiate de pièces simples, sans déchet ; utile en formation
et enseignement.

**Fonctions et ajouts.** Utilise laser, bouton, Bluetooth, batterie, LED. À ajouter : profil Bluetooth
HID. La caméra n'est pas utilisée.

**Valeur : 4/10 — Difficulté : 2/10 — Réemploi : 55 %**
