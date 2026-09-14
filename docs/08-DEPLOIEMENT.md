# Plan de déploiement et d'exploitation

> Fondé sur `docs/recherche2/A4-exploitation-securite.md` (dimensionnement, durcissement, systemd), `A3-sms-france.md`, `A5-conformite-operationnelle.md` et `R3-telephonie-fr.md`.
> Aucune ligne de code avant le lot L0 : ce document décrit **où le produit tournera**, pas comment il est écrit.

---

## 1. Le chiffre qui commande le plan

**1 Go de RAM = un appel simultané.** Pipecat Cloud dimensionne `agent-1x` à 1 Go pour **une** session vocale (« one bot per instance ») ; LiveKit recommande 4 cœurs / 8 Go pour 10–25 jobs, soit ≈ 320 Mo par session. **La RAM est le mur, pas le processeur.**

Conséquence sur les machines existantes :

| Machine | RAM | Ce qu'elle peut porter |
|---|---|---|
| `petites-claques` (151.241.228.72) | 1 Go, déjà chargée (API + DB Marpeap) | **Rien de vocal.** Elle héberge déjà Crenolo |
| `petites-frappes` (151.241.228.116) | 1 Go | **Un appel simultané**, et rien d'autre |
| `marpeap-series` (Tailscale) | poste de travail | Banc de mesure du lot L0, jamais la production |

**Donc une machine dédiée est nécessaire dès le premier client payant.** Ordre de grandeur à viser : **4 Go pour 3 à 4 appels simultanés** avec la marge d'exploitation (Asterisk, PostgreSQL, supervision). Un salon seul n'a pas 4 appels simultanés ; **dix salons, si.** C'est le vrai palier de coût de l'offre, et il doit être chiffré avant d'annoncer un prix.

---

## 2. Topologie

```
   PSTN ──► trunk SIP (Telnyx)
              │  TLS + SRTP, ACL par IP, préfixes FR entrants seulement
         ┌────▼─────────────────────────────────┐
         │  MACHINE VOCALE (dédiée)             │
         │  Asterisk 22 LTS ≥ 22.10.1           │
         │    autoload=no, ARI en loopback      │
         │    AMI désactivé                     │
         │  AudioSocket ──► worker par appel    │
         │  Piper (service HTTP séparé, GPL-3)  │
         │  PostgreSQL (appels, config, quotas) │
         └────┬─────────────────────────────────┘
              │ HTTPS sortant : STT, LLM, TTS, SMS A2P
              │ HTTPS sortant : connecteur Crenolo (/connecteur/v1)
         ┌────▼─────────────────────────────────┐
         │  petites-claques — Crenolo inchangé  │
         └──────────────────────────────────────┘
```

**Trois frontières tenues** : l'inférence sort de la machine · le connecteur parle à Crenolo **par HTTP, jamais par la base** · Piper tourne en **process séparé**, condition du respect de sa licence GPL-3.0.

---

## 3. Durcissement — la liste qui vient des CVE, pas de l'habitude

**Asterisk**
- Version **22 LTS ≥ 22.10.1**. `autoload=no` et chargement explicite : **13 des 20 CVE du 25/06/2026 visent des modules sans raison d'être chargés** (ooh323, unistim, xmpp, ldap, codec2, app_sms…).
- **ARI en loopback uniquement**, `password_format=crypt`, ACL par utilisateur — deux CVE ARI frappent exactement notre architecture.
- **AMI : ne pas l'activer.** `write=originate` suffit à réécrire `/etc/asterisk/`.
- `pjsip` seul, **TLS + SRTP**, ACL du trunk par IP, restriction aux préfixes FR entrants attendus (anti-IRSF).
- **Piège fail2ban** : sans `auth_username` dans `endpoint_identifier_order` **et** sans `res_security_log.so` chargé, **aucun SecurityEvent n'est émis** — fail2ban tourne à vide sans le dire.
- `Transfer()` **jamais avant décroché** (renvoie un 302 → boucle garantie). Anti-boucle maison : compter ses propres occurrences dans `History-Info`, aucune RFC ne le fait pour nous.

**systemd — quatre durcissements à ne PAS copier tels quels**
- `MemoryDenyWriteExecute=` : « incompatible with JIT execution engines » → **tue ONNX**, donc Silero et Smart Turn.
- `RestrictRealtime=yes` : refuse `SCHED_RR` → **gigue audio silencieuse**.
- `CPUQuota=` : fenêtre de 100 ms contre des trames RTP de 20 ms.
- Rate limit par défaut **5 démarrages / 10 s** : bloque le service après une rafale d'OOM — à relever explicitement.
- `MemoryMax` (invoque l'OOM killer) plutôt que `MemoryHigh` (ne l'invoque jamais). Et **systemd-oomd est inopérant sans swap**.

---

## 4. Numéros, SMS, et ce qui est contractuellement interdit

- **Telnyx** pour les numéros (09, API d'achat, KYC ~72 h, portage par API). **Pré-achat par lots** pour sortir le KYC du parcours d'onboarding client.
- ⚠️ **OVHcloud écarté** : son offre de téléphonie de détail **interdit** robots d'appels, automates, partage SIP, plus d'un utilisateur par compte SIP et la revente. Vérifier la même clause chez tout fournisseur retenu — **le droit d'usage prime sur la grille tarifaire**.
- **SMS : fournisseur A2P, jamais la passerelle SIM** (décision Arcep n° 2018-0881 consolidée au 01/01/2026 : interdiction **absolue** pour un 06/07 de servir d'identifiant à un système automatisé) — et sans accusé de remise, le SMS ne prouve rien. Émission depuis un **09 NPUEPT** ou un Sender ID au nom du salon ; le canal de retour reste le numéro vocal de l'agent.
- **Onboarding client** : renvoi **sur non-réponse** (codes MMI pré-remplis par opérateur), moins de 2 minutes. Et la règle héritée de Slang.ai : **la ligne de transfert ne doit pas elle-même avoir un renvoi actif**, sinon boucle — c'est une question d'onboarding, pas de SIP.

---

## 5. Données, sauvegarde, secrets

- **PostgreSQL** : tables partagées, `tenant_id`, RLS `ENABLE` **et** `FORCE`, rôle applicatif non-propriétaire sans `BYPASSRLS`, contexte posé par `set_config(..., true)` **dans la transaction**.
- **Sauvegarde** : `pg_dump` **plus** `pg_dumpall --globals-only` — `pg_dump` seul **perd les rôles et les GRANT**. Plus le dépôt git des `memoire.md`. Chiffrement avant envoi hors site. **Restauration testée**, sinon ce n'est pas une sauvegarde.
- **Migrations** : Alembic **ne détecte ni les contraintes `EXCLUDE` ni les renommages** — la contrainte anti-chevauchement sur `bookings` s'écrit à la main.
- **Secrets** : chiffrement applicatif (clé maître en variable d'environnement systemd, 0600, hors dépôt), pas pgcrypto — la doc PostgreSQL avertit que tout transite en clair jusqu'au serveur.
- **Audio : non conservé par défaut.** La CNIL écrit « ni permanent ni systématique » et érige en bonne pratique la **suppression de l'audio après transcription**.

---

## 6. Observabilité minimale, dès le premier appel

Une ligne par tour de parole en base : `end_of_utterance_delay`, `llm_ttft`, `tts_ttfb`, `total_latency`, tokens entrée/sortie/**cachés**, `speech_id`, `tenant_id`. Index sur `(tenant_id, created_at)`.

Plus quatre règles de détection d'échec, avant tout LLM : raccroché sous 10 s · plus de trois reformulations consécutives · silence de l'agent au-delà du seuil · demande explicite d'un humain.

**Langfuse : non** (ClickHouse dépasse à lui seul le budget mémoire). **Phoenix : à mesurer**, sans engagement. Une vue maison rend 80 % du service pour 0 % de la RAM.

---

## 7. Séquence

| Étape | Contenu | Porte de sortie |
|---|---|---|
| **L0 — mesures** | RTF NeMo-Speech.cpp · **WER français 8 kHz** · RTF/RAM Piper · **TTFT réel des LLM candidats** (aucun fournisseur ne publie de percentiles) · empreinte mémoire d'un appel complet | Les quatre inconnues sont chiffrées. **Le choix du bord téléphonique (D2) se tranche ici** |
| **L1 — un appel** | Machine dédiée, Asterisk durci, un numéro Telnyx, pipeline complet, `memoire.md` écrit à la main | L'agent tient une conversation. **SLO p50 ≤ 700 ms mesuré, pas estimé** |
| **L2 — greffe** | `/connecteur/v1` côté Crenolo, idempotence, read-after-write | **Taux de confirmation orpheline = 0** sur 100 appels |
| **L3 — configuration** | Questionnaire, packs, `memoire.md` généré, git | Un commerçant configure seul en < 15 min |
| **L4 — console** | Revue d'appel, **correction en trois appuis**, KPI | Une correction modifie l'agent sans toucher un prompt |
| **L5 — premier salon** | Corpus de 60–100 appels réels annotés, porte de non-régression | Le corpus passe `pass^5`, les trois conditions de la porte tiennent |

---

## 8. Ce qui doit exister avant le premier client payant

Extrait des **41 livrables** d'A5, les bloquants :

1. **Annonce IA** non désactivable dans le script (AI Act art. 50 §1, applicable depuis le 02/08/2026 — obligation **de l'éditeur**, non transférable par CGV).
2. **Dossier d'exemption du marquage** — contenu désormais défini par les lignes directrices C(2026) 5054 : une **gap analysis écrite** (point 148), la démonstration que le marquage est **techniquement infaisable** sur notre canal, et la preuve que **l'appelant est informé** (point 88, conditions **cumulatives**). ⚠️ **Le sursis au 02/12/2026 ne s'applique pas à nous** : il ne vaut que pour les systèmes déjà sur le marché avant le 02/08/2026. **Un agent lancé maintenant doit être conforme dès le premier appel.**
3. **Contrat de sous-traitance art. 28** avec chaque commerçant, et la liste des **sous-traitants ultérieurs hors UE** (LLM, STT) avec leur base de transfert.
4. **Mentions d'information de l'appelant**, prononcées au bon moment.
5. **Registre**, et l'examen de l'**AIPD** (à trancher avec un avocat — c'est l'un des 8 points listés).
6. **Qualification arrhes/acompte** verrouillée en réglage, répétée mot pour mot par l'agent (L214-1 : le mot prononcé **est** la stipulation contraire).
7. **Politique de conservation** : transcription oui, audio non par défaut.
