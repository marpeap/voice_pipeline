"""La console du commerçant — voir ses appels, corriger en trois gestes.

Règle qui domine `docs/06` : **le commerçant ne voit jamais un prompt, sous
aucune forme « avancée »**. Une correction n'est donc pas un champ de texte :
c'est une faute choisie dans une liste fermée, ancrée sur un passage de la
transcription.

**Conception — règles Barthez.**
- **Action primaire** : corriger un appel raté. Une seule par écran.
- **Pic** : le moment où la faute se choisit en un geste, sans clavier.
- **Fin** : « la correction est active, et elle sera rejouée à chaque
  changement » — une fin qui promet quelque chose, pas un cul-de-sac.
- Les sept fautes sont réparties en **deux groupes titrés** (B4 : jamais plus de
  cinq éléments dans un groupe non scannable), les cibles font 44 px (B3),
  l'accent bleu ne marque que l'action primaire (B6), et l'état vide dit quoi
  faire plutôt que « aucune donnée » (B9).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Any

from standard.decision import enoncer_date, enoncer_heure
from standard.echecs import libelle as libelle_d_echec
from standard.locataire import paliers_manquants
from standard.regles import JOURS
from standard.grammaire import ecrire_numero
from standard.correction import FAUTES, Correction, RegistreDeCorrections

PAPIER = "#F2F0EB"
ENCRE = "#0A0A0C"
ELECTRIQUE = "#0A0AEA"
ENCRE_ATTENUEE = "#6A6765"
FILET = "#A19E99"

# B4 : deux groupes titrés plutôt qu'une liste de sept.
GROUPES_DE_FAUTES = {
    "Il a mal compris": ("prestation", "duree", "mauvaise_information"),
    "Il n'aurait pas dû": ("creneau_inexistant", "promesse_interdite", "escalade", "autre"),
}

STYLE = f"""
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:{PAPIER}; color:{ENCRE};
  font:16px/1.5 ui-sans-serif, system-ui, -apple-system, sans-serif; }}
main {{ max-width:60rem; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:2rem; letter-spacing:-.02em; margin:0 0 4px; }}
h2 {{ font-size:1.1rem; margin:32px 0 8px; }}
p.legende {{ color:{ENCRE_ATTENUEE}; margin:0 0 24px; }}
/* B5, regle du 1:2 : l'ecart dans un groupe est deux fois moindre qu'entre groupes. */
ul.fil {{ list-style:none; margin:0; padding:0; display:grid; gap:8px; }}
ul.fil + h2 {{ margin-top:32px; }}
a.appel {{ display:flex; gap:16px; align-items:baseline; min-height:44px;
  padding:12px; border:1px solid {FILET}; text-decoration:none; color:{ENCRE}; }}
a.appel:hover, a.appel:focus-visible {{ border-color:{ENCRE}; outline:none; }}
.heure {{ font-variant-numeric:tabular-nums; color:{ENCRE_ATTENUEE}; }}
.issue {{ font-weight:600; }}
.incident {{ border-left:4px solid {ELECTRIQUE}; padding-left:12px; }}
.vide {{ border:1px dashed {FILET}; padding:24px; color:{ENCRE_ATTENUEE}; }}
/* Un message a rappeler : le nom et le numero d'abord, le texte ensuite.
   B5, 1:2 — 8 px dans le bloc, 16 px entre deux blocs. */
li.message {{ border:1px solid {FILET}; padding:12px; display:grid; gap:4px; }}
li.message p {{ margin:4px 0 0; color:{ENCRE_ATTENUEE}; }}
a.numero {{ display:inline-flex; align-items:center; min-height:44px;
  font-variant-numeric:tabular-nums; color:{ENCRE}; text-decoration:none;
  border-bottom:2px solid {ELECTRIQUE}; }}
a.numero:focus-visible {{ outline:3px solid {ENCRE}; outline-offset:2px; }}
blockquote {{ margin:0 0 8px; padding:12px; border-left:2px solid {FILET}; }}
form {{ display:grid; gap:24px; margin-top:24px; }}
fieldset {{ border:0; padding:0; margin:0; display:grid; gap:8px; }}
legend {{ font-weight:600; padding:0 0 8px; }}
label.faute {{ display:flex; gap:12px; align-items:center; min-height:44px;
  padding:8px 12px; border:1px solid {FILET}; cursor:pointer; }}
label.faute:has(input:checked) {{ border-color:{ELECTRIQUE}; border-width:2px; }}
button {{ min-height:44px; padding:12px 24px; border:0; background:{ELECTRIQUE};
  color:{PAPIER}; font-size:1rem; font-weight:600; cursor:pointer; }}
button:focus-visible {{ outline:3px solid {ENCRE}; outline-offset:2px; }}
.succes {{ border:1px solid {ELECTRIQUE}; padding:12px; margin-bottom:24px; }}
/* L'annulation est destructive : 24 px la séparent du reste de la ligne (B3),
   et elle reste un bouton fantôme — une seule emphase forte par vue (B6). */
form.annuler {{ margin:24px 0 0; }}
form.annuler button {{ background:transparent; color:{ENCRE};
  border:1px solid {FILET}; font-weight:400; }}
form.annuler button:hover {{ border-color:{ENCRE}; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; }} }}
"""


def _lire_des_tarifs(texte: str) -> dict:
    """« coupe 28 », « coloration 65,50 € » — une ligne par prestation.

    Une ligne illisible n'emporte pas les autres : le gerant en ecrit plusieurs
    et ne les relit pas. Un montant sans prestation, ou l'inverse, est ignore —
    on ne devine pas un tarif.
    """
    tarifs: dict = {}
    for ligne in (texte or "").splitlines():
        trouve = re.match(r"^\s*(.+?)\s+(\d+(?:[.,]\d{1,2})?)\s*€?\s*$", ligne)
        if not trouve:
            continue
        montant = float(trouve.group(2).replace(",", "."))
        tarifs[trouve.group(1).strip().lower()] = (
            int(montant) if montant == int(montant) else montant)
    return tarifs


def _texte(valeur: str) -> str:
    """Echappe pour du CONTENU, pas pour un attribut.

    Une apostrophe n'a pas besoin d'etre echappee dans du texte, et la voir
    ressortir en `&#x27;` dans une phrase francaise donne un air de formulaire
    casse — dans une langue ou l'apostrophe est partout, ce n'est pas un detail.
    """
    return html.escape(valeur, quote=False)


def _page(titre: str, contenu: str) -> str:
    return (f"<!doctype html><html lang=fr><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{_texte(titre)}</title><style>{STYLE}</style>"
            f"<main>{contenu}</main></html>")


@dataclass
class Console:
    """Rend des pages. Aucun socket ici : c'est ce qui la rend testable."""

    journal: Any
    tenant: str
    registre: RegistreDeCorrections = field(default_factory=RegistreDeCorrections)
    audit: Any = None
    depot: Any = None               # pour lire les messages pris pendant un appel
    pack: Any = None                # le questionnaire : sans lui, pas de réglages
    creneaux: tuple = ()            # pour l'essai : ce que le salon propose
    aujourd_hui: Any = None         # injectable, pour que les tests aient une date
    _essai: Any = None              # la conversation d'essai en cours
    acteur: str = "console"
    _message: str | None = None

    # --- routage ------------------------------------------------------------

    def repondre(self, methode: str, chemin: str, corps: dict | None = None):
        if methode == "GET" and chemin == "/":
            return 200, {"Content-Type": "text/html; charset=utf-8"}, self._fil()
        if methode == "GET" and chemin.startswith("/appel/"):
            return self._detail(chemin.removeprefix("/appel/"))
        if methode == "GET" and chemin.rstrip("/") == "/agenda":
            return self._agenda()
        if methode == "POST" and chemin.rstrip("/") == "/agenda/annuler":
            return self._annuler_un_rendez_vous(corps or {})
        if methode == "GET" and chemin.rstrip("/") == "/essayer":
            return self._ecran_d_essai()
        if methode == "POST" and chemin.split("?")[0].rstrip("/") == "/essayer":
            corps = dict(corps or {})
            if "nouveau=1" in chemin:
                corps["nouveau"] = "1"
            return self._essayer(corps)
        if methode == "GET" and chemin.rstrip("/") == "/reglages":
            return self._reglages()
        if methode == "POST" and chemin.rstrip("/") == "/reglages":
            return self._enregistrer_reglages(corps or {})
        if methode == "POST" and chemin == "/correction":
            return self._poser_correction(corps or {})
        return 404, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Introuvable", "<h1>Cette page n'existe pas</h1>"
            "<p class=legende><a href='/'>Revenir au fil des appels</a> · "
            "<a href='/essayer'>Essayer votre agent</a></p>")

    # --- le fil -------------------------------------------------------------

    def _fil(self) -> str:
        appels = self.journal.lister(self.tenant)
        resume = self.journal.resume(self.tenant)
        incidents = self.journal.incidents(self.tenant)

        # Miller (4±1) : quatre chiffres au plus dans cette ligne, et le
        # quatrieme n'apparait que s'il y a quelque chose a dire.
        chiffres = [f"{resume['appels']} appels",
                    f"{resume['rendez_vous']} rendez-vous",
                    f"{resume['transferts']} transferts"]
        filtres = resume.get("demarchages", 0)
        if filtres:
            chiffres.append(f"{filtres} démarchage{'s' if filtres > 1 else ''} "
                            f"filtré{'s' if filtres > 1 else ''}, non facturé"
                            f"{'s' if filtres > 1 else ''}")
        entete = ("<h1>Vos appels</h1>"
                  f"<p class=legende>{' · '.join(chiffres)}</p>")
        if self._message:
            entete += f"<p class=succes>{_texte(self._message)}</p>"
            self._message = None

        bloc_messages = self._bloc_messages()

        # B7 : ce qui compte est en position 1. Un incident passe devant le fil.
        bloc_incidents = ""
        if incidents:
            lignes = "".join(
                f"<li class=incident><a class=appel href='/appel/{html.escape(i['uuid'])}'>"
                f"<span class=issue>{_texte(i['motif'])}</span>"
                f"<span class=heure>{html.escape(i['debut'][11:16])}</span></a></li>"
                for i in incidents[:5])
            bloc_incidents = f"<h2>À regarder — incident</h2><ul class=fil>{lignes}</ul>"

        if not appels:
            # B9 : un état vide dit quoi faire, il ne dit pas « aucune donnée ».
            corps = ("<div class=vide><strong>Aucun appel pour le moment.</strong><br>"
                     "Dès que votre numéro sera branché, les appels apparaîtront ici, "
                     "avec ce que l'agent a compris et ce qu'il a répondu.</div>")
            corps = self._bandeau_de_reglages() + corps
            return _page("Vos appels",
                         entete + bloc_messages + corps + self._pied_de_page())

        lignes = "".join(
            f"<li><a class=appel href='/appel/{html.escape(a['uuid'])}'>"
            f"<span class=heure>{html.escape(a['debut'][11:16])}</span>"
            f"<span class=issue>{_texte(a.get('issue', '—'))}</span>"
            f"<span class=heure>{int(a.get('duree_s', 0))} s</span></a></li>"
            for a in appels[:50])
        return _page("Vos appels",
                     entete + self._bandeau_de_reglages() + bloc_incidents + bloc_messages
                     + f"<h2>Fil des appels</h2><ul class=fil>{lignes}</ul>"
                     + self._pied_de_page())

    def _bloc_messages(self) -> str:
        """Les messages pris quand le salon a choisi « rappeler » (question D4).

        Un message pris et jamais montre vaut moins que pas de message du tout :
        le commercant croit alors que l'agent a transfere. Il passe donc avant le
        fil (B7), et porte le numero ecrit pour l'oeil plutot que pour l'oreille.
        """
        if self.depot is None:
            return ""
        messages = self.depot.messages(self.tenant)
        if not messages:
            return ""
        # Un rendez-vous que l'agenda n'a pas confirme n'est pas un message de
        # rappel : c'est une action a faire AVANT que le client ne se deplace.
        # Il passe donc en tete, et porte son propre titre (B6 : une seule
        # emphase, mais deux natures qu'on ne melange pas).
        a_rattraper = [m for m in messages if m.get("type") == "rendez_vous_a_rattraper"]
        rappels = [m for m in messages if m.get("type") != "rendez_vous_a_rattraper"]
        return (self._liste_de_messages("À confirmer — l'agenda n'a pas répondu",
                                        a_rattraper)
                + self._liste_de_messages("À rappeler — messages", rappels))

    def _liste_de_messages(self, titre: str, messages: list) -> str:
        if not messages:
            return ""
        lignes = []
        for message in messages[:5]:
            qui = _texte(message.get("nom") or "Appelant")
            numero = message.get("telephone")
            rappel = (f"<a class=numero href='tel:{html.escape(numero)}'>"
                      f"{_texte(ecrire_numero(numero))}</a>") if numero else \
                     "<span class=legende>pas de numéro</span>"
            lignes.append(f"<li class=message><strong>{qui}</strong> {rappel}"
                          f"<p>{_texte(message.get('texte', ''))}</p></li>")
        return f"<h2>{_texte(titre)}</h2><ul class=fil>{''.join(lignes)}</ul>"

    # --- le détail ----------------------------------------------------------

    def _detail(self, uuid: str):
        appel = next((a for a in self.journal.lister(self.tenant) if a["uuid"] == uuid), None)
        if appel is None:
            return self.repondre("GET", "/introuvable")

        tours = "".join(
            f"<blockquote><strong>Lui :</strong> {_texte(t.get('transcription', '—'))}"
            f"<br><strong>L'agent :</strong> {_texte(t.get('phrase', '—'))}</blockquote>"
            for t in appel.get("tours", []))

        empan = next((t.get("transcription", "") for t in appel.get("tours", [])), "")
        groupes = ""
        for titre, fautes in GROUPES_DE_FAUTES.items():
            choix = "".join(
                f"<label class=faute><input type=radio name=faute value='{f}'>"
                f"{_texte(FAUTES[f]['libelle'])}</label>" for f in fautes)
            groupes += f"<fieldset><legend>{_texte(titre)}</legend>{choix}</fieldset>"

        # Chaque faute a besoin d'une valeur differente. Sans ces champs, la
        # console ne transmettait qu'une note libre — et la correction ne
        # s'appliquait a rien. Ils restent optionnels : ce qui manque met la
        # correction de cote, sans jamais faire tomber les autres.
        precisions = (
            "<fieldset><legend>Précisions</legend>"
            "<label for=prestation>Prestation concernée</label>"
            "<input id=prestation name=prestation type=text>"
            "<label for=duree>Durée réelle, en minutes</label>"
            "<input id=duree name=duree_minutes type=number min=5 max=480 step=5>"
            "<label for=interdit>Ce qu'il ne doit jamais promettre</label>"
            "<input id=interdit name=interdit type=text>"
            # Sans ce champ, « ce créneau n'existe pas » ne disait pas LEQUEL :
            # la règle serveur se posait sur du vide et ne fermait rien.
            "<label for=heure>Le créneau qui n'existe pas</label>"
            "<input id=heure name=heure type=time step=300>"
            "<label for=jour>Ce jour-là seulement (facultatif)</label>"
            "<input id=jour name=jour type=text placeholder='samedi'>"
            "</fieldset>")

        formulaire = (
            f"<h2>Corriger cet appel</h2>"
            f"<p class=legende>Choisissez ce qui n'allait pas. Aucune phrase à écrire : "
            f"la correction s'applique tout de suite, et elle sera rejouée à chaque "
            f"changement pour qu'elle ne se reperde pas.</p>"
            f"<form method=post action='/correction'>"
            f"<input type=hidden name=appel value='{html.escape(uuid)}'>"
            f"<input type=hidden name=empan value='{html.escape(empan)}'>"
            f"{groupes}{precisions}"
            f"<label for=note>Précision, si vous voulez (facultatif)</label>"
            f"<textarea id=note name=note rows=2></textarea>"
            f"<button type=submit>Poser la correction</button></form>")

        rsb = appel.get("rsb_db")
        contexte = (f"<p class=legende>{html.escape(appel['debut'][:16].replace('T', ' à '))} · "
                    f"{int(appel.get('duree_s', 0))} s · "
                    f"{'ligne bruitée' if appel.get('bruite') else 'ligne correcte'}"
                    f"{f' ({rsb} dB)' if rsb is not None else ''}</p>")
        # Le motif d'echec est ce qu'on cherche en ouvrant un appel : sans lui,
        # il faut relire toute la transcription pour deviner. En gris, jamais en
        # rouge — un gerant qui a peur d'ouvrir sa console ne la corrige pas.
        motif = libelle_d_echec(appel.get("echec"))
        bandeau = f"<p class=legende><strong>Ce qui a manqué :</strong> {_texte(motif)}.</p>" \
            if motif else ""
        return 200, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Appel", f"<h1>Appel de {html.escape(appel['debut'][11:16])}</h1>"
                     f"{contexte}{bandeau}{tours}{formulaire}")

    def _bandeau_de_reglages(self) -> str:
        """Tant qu'une question critique est vide, l'agent ne décroche pas.

        C'est la seule chose qui compte sur ce fil-là (B7, B6 : une emphase, et
        elle n'est pas décorative). Une fois le questionnaire complet, le lien
        reste discret en bas de page — le fil des appels reprend la vedette.
        """
        if self.pack is None or self.depot is None:
            return ""
        manquantes = paliers_manquants(self.pack, self._reponses())
        if not manquantes:
            return ""
        return ("<div class=vide><strong>Votre agent ne peut pas encore "
                f"décrocher.</strong><br>Il manque {len(manquantes)} réponse"
                f"{'s' if len(manquantes) > 1 else ''} au questionnaire — "
                "<a class=numero href='/reglages'>y répondre</a>.</div>")

    def _pied_de_page(self, sauf: str = "") -> str:
        """La suite utile, sur chaque écran : B10, aucune fin en cul-de-sac.

        Jamais un lien vers la page qu'on regarde : un lien mort fait douter le
        gérant d'avoir cliqué.
        """
        if self.pack is None:
            return ""
        liens = [("/agenda", "Vos rendez-vous"),
                 ("/reglages", "Les réponses de votre agent"),
                 ("/essayer", "L'essayer")]
        rendus = [f"<a href='{chemin}'>{libelle}</a>"
                  for chemin, libelle in liens if chemin != sauf]
        return f"<p class=legende>{' · '.join(rendus)}</p>"

    # --- les réglages (docs/05) ---------------------------------------------

    def _reponses(self) -> dict:
        return self.depot.reponses(self.tenant) if self.depot is not None else {}

    def _champ(self, question: dict, valeur) -> str:
        """Le bon contrôle pour le bon type — jamais une zone de texte libre là
        où le pack propose une liste (B8 : le produit absorbe la complexité)."""
        identifiant = html.escape(question["id"])
        type_de_question = question.get("type", "texte")

        if type_de_question in ("choix_unique", "choix_multiple"):
            options = []
            for option in question.get("options", []):
                coche = ""
                if type_de_question == "choix_multiple":
                    coche = " checked" if option["valeur"] in (valeur or []) else ""
                elif valeur == option["valeur"] or (valeur is None and option.get("defaut")):
                    coche = " checked"
                genre = "checkbox" if type_de_question == "choix_multiple" else "radio"
                recommande = " <span class=legende>(recommandé)</span>" \
                    if option.get("defaut") else ""
                options.append(
                    f"<label class=faute><input type={genre} name={identifiant} "
                    f"value='{html.escape(str(option['valeur']))}'{coche}>"
                    f"{_texte(option['libelle'])}{recommande}</label>")
            return "".join(options)

        if type_de_question == "tarifs":
            # Une ligne par prestation, dans l'ordre de ce que le salon a coché :
            # le gérant lit sa propre liste, pas un formulaire vide (B8).
            lignes = []
            deja = valeur if isinstance(valeur, dict) else {}
            for prestation in (self._reponses().get("C1") or []):
                montant = deja.get(prestation, "")
                lignes.append(f"{prestation} {montant}".strip())
            for prestation, montant in deja.items():
                if prestation not in (self._reponses().get("C1") or []):
                    lignes.append(f"{prestation} {montant}")
            return (f"<textarea id={identifiant} name={identifiant} rows=4 "
                    f"placeholder='coupe 28'>{_texte(chr(10).join(lignes))}</textarea>")

        if type_de_question == "texte_long":
            return (f"<textarea id={identifiant} name={identifiant} rows=4>"
                    f"{_texte(str(valeur or ''))}</textarea>")

        if type_de_question == "horaires_semaine":
            # Une grille d'horaires ne se tape pas à la main dans un texte : on
            # montre ce que le pack propose par défaut, et on laisse corriger
            # jour par jour, en toutes lettres — « 09:00-19:00 ».
            defaut = valeur if isinstance(valeur, dict) else (question.get("defaut") or {})
            lignes = []
            for jour in JOURS:
                plages = defaut.get(jour) or []
                lignes.append(
                    f"<label for={identifiant}_{jour}>{jour.capitalize()}</label>"
                    f"<input id={identifiant}_{jour} name={identifiant}.{jour} "
                    f"type=text placeholder='fermé' "
                    f"value='{html.escape(', '.join(plages))}'>")
            return "".join(lignes)

        return (f"<input id={identifiant} name={identifiant} type=text "
                f"value='{html.escape(str(valeur or ''))}'>")

    def _reglages(self):
        if self.pack is None:
            return 404, {"Content-Type": "text/html; charset=utf-8"}, _page(
                "Réglages", "<h1>Aucun questionnaire</h1>"
                "<p class=legende>Ce déploiement n'a pas de pack.</p>")

        reponses = self._reponses()
        manquantes = paliers_manquants(self.pack, reponses)

        # B7 : ce qui décide de tout est en position 1. Tant qu'une question
        # critique est vide, l'agent NE DÉCROCHE PAS — le dire d'abord.
        if manquantes:
            pluriel = len(manquantes) > 1
            etat = ("<div class=vide><strong>Votre agent ne peut pas encore "
                    f"décrocher.</strong><br>Il manque {len(manquantes)} réponse"
                    f"{'s' if pluriel else ''} : sans "
                    f"{'elles' if pluriel else 'elle'}, il dirait au client "
                    "quelque chose de faux.</div>")
        else:
            etat = ("<div class=vide><strong>Votre agent peut décrocher.</strong>"
                    "<br>Vous pouvez encore affiner ce qui suit, il répondra "
                    "pendant ce temps.</div>")

        blocs = ""
        for bloc in self.pack.get("blocs", []):
            champs = ""
            for question in bloc.get("questions", []):
                valeur = reponses.get(question["id"])
                critique = " <span class=legende>(indispensable)</span>" \
                    if question.get("critique") else ""
                aide = f"<p class=legende>{_texte(question.get('aide', ''))}</p>" \
                    if question.get("aide") else ""
                champs += (f"<fieldset><legend>{_texte(question['libelle'])}{critique}"
                           f"</legend>{aide}{self._champ(question, valeur)}</fieldset>")
            blocs += f"<h2>{_texte(bloc.get('titre', bloc['id']))}</h2>{champs}"

        return 200, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Réglages",
            "<h1>Votre agent</h1>"
            "<p class=legende>Répondez dans vos mots. Il n'y a rien d'autre à "
            "écrire : ces réponses deviennent ce que l'agent sait.</p>"
            f"{etat}<form method=post action='/reglages'>{blocs}"
            "<button type=submit>Enregistrer</button></form>"
            "<p class=legende><a href='/'>Revenir au fil des appels</a> · "
            "<a href='/essayer'>Essayer votre agent</a></p>")

    def _enregistrer_reglages(self, corps: dict):
        """N'écrit que ce que le pack déclare : le formulaire vient du navigateur."""
        connues = {q["id"]: q for bloc in (self.pack or {}).get("blocs", [])
                   for q in bloc.get("questions", [])}
        reponses: dict = {}
        for cle, valeur in corps.items():
            racine, _, jour = cle.partition(".")
            if racine not in connues:
                continue
            question = connues[racine]
            if question.get("type") == "tarifs":
                tarifs = _lire_des_tarifs(str(valeur))
                if tarifs:
                    reponses[racine] = tarifs
            elif question.get("type") == "horaires_semaine" and jour:
                # « 09:00-19:00, 14:00-18:00 » : on garde ce qui est écrit, on
                # ne devine pas un horaire à la place du commerçant.
                plages = [p.strip() for p in str(valeur).split(",") if p.strip()]
                if plages:
                    reponses.setdefault(racine, {})[jour] = plages
            elif valeur:
                reponses[racine] = valeur

        if reponses and self.depot is not None:
            self.depot.pour(self.tenant).enregistrer_reponses(reponses)
            if self.audit is not None:
                self.audit.noter(self.tenant, acteur=self.acteur,
                                 action="reglages.modifies", cible="questionnaire",
                                 detail={"questions": sorted(reponses)})
        # B10 : la fin promet la suite. On revient au fil, jamais sur un écran mort.
        self._message = ("C'est enregistré. Votre agent en tient compte au "
                         "prochain appel.")
        return 303, {"Location": "/"}, ""

    # --- l'agenda du commerçant ---------------------------------------------

    JOURS_D_AGENDA = 7
    """Une semaine : au-dela, un gerant regarde son planning, pas sa console."""

    def _aujourd_hui(self):
        from datetime import date

        return self.aujourd_hui() if callable(self.aujourd_hui) else date.today()

    def _agenda(self):
        if self.depot is None:
            return 404, {"Content-Type": "text/html; charset=utf-8"}, _page(
                "Agenda", "<h1>Aucun agenda</h1>")

        from datetime import timedelta

        aujourd_hui = self._aujourd_hui()
        limite = (aujourd_hui + timedelta(days=self.JOURS_D_AGENDA)).isoformat()
        par_jour: dict = {}
        for ligne in self.depot.lister(self.tenant):
            jour = ligne.get("date") or ""
            # Le passe ne pollue pas la journee : un gerant ouvre sa console
            # entre deux clients, il regarde devant.
            if not (aujourd_hui.isoformat() <= jour <= limite):
                continue
            par_jour.setdefault(jour, []).append(ligne)

        if not par_jour:
            # B9 : un etat vide dit quoi faire.
            corps = ("<div class=vide><strong>Aucun rendez-vous pour le moment."
                     "</strong><br>Dès que votre agent en prendra un, il "
                     "apparaîtra ici, avec le nom et le numéro du client.</div>")
            return 200, {"Content-Type": "text/html; charset=utf-8"}, _page(
                "Agenda", f"<h1>Vos rendez-vous</h1>{corps}"
                          f"{self._pied_de_page(sauf='/agenda')}")

        sections = ""
        for jour in sorted(par_jour):
            lignes = ""
            for rendez_vous in sorted(par_jour[jour], key=lambda r: r.get("heure", "")):
                lignes += self._ligne_d_agenda(rendez_vous)
            sections += (f"<h2>{_texte(self._titre_du_jour(jour, aujourd_hui))}</h2>"
                         f"<ul class=fil>{lignes}</ul>")

        return 200, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Agenda", f"<h1>Vos rendez-vous</h1>{sections}"
                      f"{self._pied_de_page(sauf='/agenda')}")

    def _titre_du_jour(self, jour: str, aujourd_hui) -> str:
        """« Aujourd'hui », « Demain », puis la date. Tous les agendas du monde
        font ainsi, et un gerant ne compte pas les jours (B1)."""
        from datetime import timedelta

        if jour == aujourd_hui.isoformat():
            return "Aujourd'hui"
        if jour == (aujourd_hui + timedelta(days=1)).isoformat():
            return "Demain"
        return enoncer_date(jour).capitalize()

    def _ligne_d_agenda(self, rendez_vous: dict) -> str:
        heure = enoncer_heure(rendez_vous.get("heure", "")) \
            if rendez_vous.get("heure") else "—"
        qui = _texte(rendez_vous.get("nom") or "Sans nom")
        quoi = _texte(rendez_vous.get("prestation") or "")
        duree = rendez_vous.get("duree_minutes")
        detail = " · ".join(morceau for morceau in
                            (quoi, f"{duree} min" if duree else "") if morceau)
        numero = rendez_vous.get("telephone")
        rappel = (f"<a class=numero href='tel:{html.escape(numero)}'>"
                  f"{_texte(ecrire_numero(numero))}</a>") if numero else ""
        reference = html.escape(str(rendez_vous.get("reference", "")))
        # L'annulation est une action destructive : elle est a l'ecart du reste
        # (B3, 24 px de la voisine) et elle dit ce qu'elle fait, pas « OK ».
        annuler = (f"<form method=post action='/agenda/annuler' class=annuler>"
                   f"<input type=hidden name=reference value='{reference}'>"
                   f"<button type=submit>Annuler</button></form>")
        precision = f"<p>{detail}</p>" if detail else ""
        return (f"<li class=message><strong>{heure}</strong> {qui} {rappel}"
                f"{precision}{annuler}</li>")

    def _annuler_un_rendez_vous(self, corps: dict):
        reference = corps.get("reference", "")
        annule = False
        if reference and self.depot is not None:
            annule = self.depot.pour(self.tenant).annuler(reference)
        if annule and self.audit is not None:
            # Qui a annule quoi : un rendez-vous disparu sans trace est une
            # dispute entre le salon et son client.
            self.audit.noter(self.tenant, acteur=self.acteur, action="agenda.annule",
                             cible=reference, detail={})
        self._message = ("Le rendez-vous est annulé. Le créneau est de nouveau "
                         "proposable." if annule else
                         "Ce rendez-vous n'existe plus.")
        return 303, {"Location": "/agenda"}, ""

    # --- essayer son agent (confrontation du 20/09) -------------------------

    PHRASES_D_ESSAI = (
        "Bonjour, je voudrais un rendez-vous jeudi à quinze heures trente.",
        "Vous êtes ouverts samedi ?",
        "Je voudrais parler à quelqu'un du salon.",
        "Je vous appelle pour vous proposer notre solution de référencement.",
    )

    def _agent_d_essai(self):
        """Un agent monté sur la configuration du commerçant, et sur une base
        jetable : l'essai n'écrit jamais dans l'agenda réel, c'est ce qui permet
        de tout tenter."""
        from datetime import date

        from standard.depot import Depot as DepotJetable
        from standard.hors_ligne import ModeleHorsLigne
        from standard.service import Configuration, Service

        aujourd_hui = date.today()
        config = Configuration(tenant=self.tenant, pack=self.pack,
                               reponses=self._reponses(), aujourd_hui=aujourd_hui,
                               creneaux=tuple(self.creneaux))
        service = Service(config, client_modele=ModeleHorsLigne(aujourd_hui=aujourd_hui),
                          base=DepotJetable(":memory:").pour(self.tenant))
        service.demarrer()
        return service.nouvel_appel("essai")

    def _ecran_d_essai(self):
        if self.pack is None or self.depot is None:
            return 404, {"Content-Type": "text/html; charset=utf-8"}, _page(
                "Essai", "<h1>Rien à essayer</h1>")

        echanges = (self._essai or {}).get("echanges", [])
        # La toute première phrase est celle que le client entendra en
        # décrochant : c'est ce que le gérant veut entendre en premier, et elle
        # porte l'annonce obligatoire.
        ouverture = ""
        if echanges:
            ouverture = (f"<blockquote><strong>L'agent décroche :</strong> "
                         f"{_texte((self._essai or {}).get('salutation', ''))}"
                         f"</blockquote>")
        conversation = ouverture + "".join(
            f"<blockquote><strong>Vous :</strong> {_texte(dit)}"
            f"<br><strong>L'agent :</strong> {_texte(repondu)}</blockquote>"
            for dit, repondu in echanges)
        if not echanges:
            # B9 : un état vide dit quoi faire.
            conversation = ("<div class=vide><strong>Dites-lui quelque chose.</strong>"
                            "<br>Rien de ce qui se passe ici n'atteint votre "
                            "agenda : vous pouvez tout essayer.</div>")

        # Ces quatre phrases sont des DEBUTS d'appel : les envoyer au milieu
        # d'une conversation aboutie montrerait l'agent sous un faux jour — le
        # demarchage, par exemple, n'est filtre que dans les premiers tours.
        suggestions = "".join(
            f"<button type=submit name=dire value='{html.escape(phrase)}' "
            f"formaction='/essayer?nouveau=1'>{_texte(phrase)}</button>"
            for phrase in self.PHRASES_D_ESSAI)

        return 200, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Essayer",
            "<h1>Essayer votre agent</h1>"
            "<p class=legende>Ce qu'il répondra à vos clients, avec vos réponses "
            "à vous. Rien n'est écrit dans votre agenda.</p>"
            f"{conversation}"
            "<form method=post action='/essayer'>"
            "<label for=dire>Ce que dirait le client</label>"
            "<input id=dire name=dire type=text>"
            "<button type=submit>Envoyer</button>"
            f"<fieldset><legend>Ou essayez ceci</legend>{suggestions}</fieldset>"
            "</form>"
            "<form method=post action='/essayer'>"
            "<input type=hidden name=recommencer value='1'>"
            "<button type=submit>Recommencer</button></form>"
            "<p class=legende><a href='/'>Revenir au fil des appels</a> · "
            "<a href='/reglages'>Changer une réponse</a></p>")

    def _essayer(self, corps: dict):
        if corps.get("recommencer"):
            self._essai = None
            return 303, {"Location": "/essayer"}, ""

        dit = (corps.get("dire") or "").strip()
        if not dit:
            return 303, {"Location": "/essayer"}, ""
        if corps.get("nouveau"):
            self._essai = None

        if self._essai is None:
            agent = self._agent_d_essai()
            self._essai = {"agent": agent, "echanges": [],
                           "salutation": agent.salutation()}
        try:
            reponse = self._essai["agent"].tour(dit)
            phrase = reponse.phrase
        except Exception as erreur:
            # Un essai qui tombe ne doit pas ressembler à une panne du produit :
            # on montre ce qui s'est passé plutôt qu'une page blanche.
            phrase = f"[l'essai n'a pas abouti : {erreur}]"
        self._essai["echanges"].append((dit, phrase))
        return 303, {"Location": "/essayer"}, ""

    # --- la correction ------------------------------------------------------

    def _poser_correction(self, corps: dict):
        faute = corps.get("faute", "")
        if faute not in FAUTES:
            # B9 : l'erreur vient de la réalité, et elle dit quoi faire.
            return 400, {"Content-Type": "text/html; charset=utf-8"}, _page(
                "Correction impossible",
                "<h1>Choisissez une faute dans la liste</h1>"
                "<p class=legende>Aucune faute n'a été sélectionnée — "
                "<a href='/'>revenir au fil</a>.</p>")

        valeur = {cle: valeur for cle, valeur in corps.items()
                  if cle not in ("faute", "appel", "empan") and valeur}
        if "duree_minutes" in valeur:
            try:
                valeur["duree_minutes"] = int(valeur["duree_minutes"])
            except (TypeError, ValueError):
                # Un champ libre arrive de l'exterieur : une duree illisible ne
                # doit pas faire tomber la console du commercant.
                valeur.pop("duree_minutes")

        correction = self.registre.ajouter(Correction(
            faute=faute, appel=corps.get("appel", ""),
            empan=corps.get("empan", ""), valeur=valeur))

        if self.audit is not None:
            # Qui a change quoi, et sur quel appel. Sans cette ligne, un reglage
            # pose un mardi devient un « bug » cherche le jeudi.
            self.audit.noter(self.tenant, acteur=self.acteur, action="correction.posee",
                             cible=correction.identifiant,
                             detail={"faute": faute, "etat": correction.etat},
                             correlation=corps.get("appel", ""))
        # B10 : la fin promet la suite au lieu de se refermer.
        self._message = ("Correction enregistrée. Elle s'applique dès maintenant, "
                         "et elle sera rejouée à chaque changement — cinq fois de suite — "
                         "pour qu'elle ne se reperde pas.")
        return 303, {"Location": "/"}, ""
