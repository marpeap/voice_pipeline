# Voice-Pipeline — où en est le chantier (15/09/2026, 9 h)

## En une phrase

**Un assistant téléphonique configurable, vendu comme service à part entière** — Crenolo n'en est qu'un adaptateur parmi d'autres.

**21 documents de conception · 16 rapports de recherche sourcés · 18 mesures · toujours zéro ligne de code produit** (les bancs, eux, tournent). Dépôt : `marpeap/voice_pipeline`, branche **`refonte`**.

**La nuit du 14 au 15 a produit douze mesures**, toutes faites depuis le poste, le banc étant hors ligne depuis neuf heures.

---

## Les quatre choses à retenir si tu ne lis rien d'autre

**1. Un agent « prompt seul » ment une fois sur deux.** Sur douze tours ordinaires, six fautes : un créneau inventé (« neuf heures moins le quart » devient 9 h 15), un fait inventé (« le premier du mois prochain est un dimanche », alors qu'il n'a aucune date), et **deux confirmations orphelines** dont « votre rendez-vous de demain matin est annulé » — rien n'est écrit nulle part, le client s'organise là-dessus. **Aucune faute n'est signalée : un modèle ne dit jamais qu'il n'a pas compris, il comble.**

**2. Avec les garde-fous, le mensonge disparaît — et l'utilité aussi.** Zéro confirmation orpheline, zéro date inventée. Mais zéro réservation : sept tours sur dix finissent en « pouvez-vous répéter ? », parce que le STT local est trop abîmé. **La rigueur ne remplace pas la qualité d'écoute, elle la révèle.** Un client raccroche dans les deux cas.

**3. Ce qui coûte la latence n'était pas la distance.** Une connexion rouverte à chaque appel : 2 040 ms. Gardée ouverte : **378 ms**, et 85 ms au mieux — vers un fournisseur américain. Ce sont le DNS et les poignées de main. **Le premier levier de latence est gratuit.**

**4. Le mur n'est pas là où on croyait.** Le STT tient 25 à 30 appels simultanés et coûte 11 Mo par appel. **C'est le TTS qui limite** — et en latence, pas en débit : le délai avant le premier son passe de 162 ms à un appel à 614 ms à six, pendant que la charge processeur reste basse. **Une machine soutient une dizaine d'appels en cours.**

---

## Les mesures, en un tableau

| # | Ce qui a été mesuré | Résultat |
|---|---|---|
| 1 | TTS Piper | RTF 0,096 — **et le TTFB de 372 ms venait du binaire, pas du modèle** (voir 13) |
| 3 | WER français 16 contre 8 kHz | Nemotron 7,8 % · Vosk 10,6 % · sherpa 23,4 % |
| 4 | Latence LLM | **2 040 ms connexion neuve contre 378 ms gardée** ; DNS froid 1,6 à 4,7 s |
| 5 | Tatouage audio | survit au canal téléphonique |
| 6 | Conversion 8 kHz | 11 ms de travail, **45 ms rien que pour lancer `ffmpeg`** |
| 7 | Bande téléphonique | **×1,03** sur un gros modèle — et **4 numéros sur 10 perdus, identiquement dans les deux bandes** |
| 8-9 | Trois moteurs, même corpus | **le WER classe les moteurs à l'envers** ; un moteur streaming perd **un premier mot sur quatre** |
| 10 | Courbe de bruit | **le classement s'inverse dès 15 dB** ; le WER réel à attendre est 20-27 %, pas 9-11 % |
| 11 | Charge STT | 8 flux, RTF 0,27, **11 Mo par flux** → 25 à 30 appels |
| 12 | Bruit, moteur distant | **+1,9 point seulement**, et **les numéros ne bougent pas** |
| 13 | Charge TTS | **162 ms à un flux, 614 ms à six** ; +150 Mo par synthèse |
| 14 | Tour complet | **624 ms p50**, 1 498 ms p90 — toute la variance vient du LLM |
| 15-18 | Rigueur d'exécution | garde-fous, boucle de clarification (**2,2 tours**), escalade graduée |

---

## Trois décisions que ces mesures ont changées

1. **Le STT reste en API, durablement.** L'auto-héberger économise 6,50 $/salon/mois et coûte deux choses : toute la grammaire française des nombres (les moteurs locaux rendent des mots, le distant rend des chiffres) **et** l'effondrement sous bruit. L'ordre de rapatriement « LLM → STT → TTS » devient **« STT en dernier »**.
2. **Le bruit est du côté de l'appelant, jamais du salon.** L'agent entend la rue, la voiture, le haut-parleur. Ce qui nous décrit, c'est la ligne 10-15 dB.
3. **Le modèle est une pièce d'usure.** Trois mouvements de catalogue en 48 h, dont un modèle disparu en pleine nuit et un remplaçant qui refuse un paramètre que l'autre acceptait. **Le nom du modèle et ses paramètres vivent en configuration.**

---

## Ce qui attend une décision de toi

1. **L'extraction de `reservation.py`** côté Crenolo — le pair a 14 tests de caractérisation et attend ton feu vert. Argument décisif : **le verrou y est déjà dupliqué**, donc l'extraction en supprime un au lieu d'en ajouter un.
2. **Un salon volontaire.** `docs/18-SALON-PILOTE.md` contient tout : feuille de comptage à imprimer, accord de sous-traitance, argumentaire. **L'étape A ne demande aucune technique** — juste une feuille près du téléphone pendant une semaine.

## Ce qui attend de l'argent

**Une clé d'API payante**, pour la seule mesure encore impossible : le gain réel du cache de prompt. Le palier gratuit plafonne à 8 000 jetons par minute, soit un refus dès la deuxième requête avec un prompt réaliste.

## Ce qui attend une machine

**`marpeap-series` est hors ligne depuis neuf heures.** Plus rien n'en dépend : les mesures qui l'attendaient ont été refaites ici.

---

## La suite

**Lot L1** (`docs/17`) : une machine, Asterisk durci, un numéro, le pipeline complet, un premier appel qui tient une conversation. **Il n'attend personne.**
**Lot L2** (`docs/20`) : l'inscription, le questionnaire, le branchement du numéro — ce qui fait exister le service autonome.
