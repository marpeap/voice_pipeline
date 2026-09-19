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
from dataclasses import dataclass, field
from typing import Any

from standard.echecs import libelle as libelle_d_echec
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
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; }} }}
"""


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
    acteur: str = "console"
    _message: str | None = None

    # --- routage ------------------------------------------------------------

    def repondre(self, methode: str, chemin: str, corps: dict | None = None):
        if methode == "GET" and chemin == "/":
            return 200, {"Content-Type": "text/html; charset=utf-8"}, self._fil()
        if methode == "GET" and chemin.startswith("/appel/"):
            return self._detail(chemin.removeprefix("/appel/"))
        if methode == "POST" and chemin == "/correction":
            return self._poser_correction(corps or {})
        return 404, {"Content-Type": "text/html; charset=utf-8"}, _page(
            "Introuvable", "<h1>Cette page n'existe pas</h1>"
            "<p class=legende><a href='/'>Revenir au fil des appels</a></p>")

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
            return _page("Vos appels", entete + bloc_messages + corps)

        lignes = "".join(
            f"<li><a class=appel href='/appel/{html.escape(a['uuid'])}'>"
            f"<span class=heure>{html.escape(a['debut'][11:16])}</span>"
            f"<span class=issue>{_texte(a.get('issue', '—'))}</span>"
            f"<span class=heure>{int(a.get('duree_s', 0))} s</span></a></li>"
            for a in appels[:50])
        return _page("Vos appels",
                     entete + bloc_incidents + bloc_messages
                     + f"<h2>Fil des appels</h2><ul class=fil>{lignes}</ul>")

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
