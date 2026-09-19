"""Les moteurs — brancher la voix réelle, ou dire clairement qu'elle manque.

Le service savait décrocher et répondre, mais rien ne branchait les moteurs
mesurés : `transcrire` rendait une chaîne vide. Ce module ferme ce trou, et il
applique deux règles nées des mesures.

**Le nom du moteur et ses paramètres vivent en configuration.** Le catalogue d'un
fournisseur a bougé trois fois en quarante-huit heures pendant les mesures, et le
modèle de remplacement refusait un paramètre que le précédent acceptait
(mesure 17). Un nom en dur dans le code, c'est une panne programmée.

**Un moteur absent se dit, il ne se devine pas.** Un service qui décroche et
n'entend rien est pire qu'un service qui refuse de démarrer : le commerçant
croit être couvert.

Le choix par défaut vient des mesures, pas du goût :
- **transcription distante** (mesure 12 : +1,9 point de dégradation sous bruit
  contre +25 pour un petit modèle local, et les numéros restent lisibles) ;
- **voix `fr_FR-siwis-medium`** (mesure 22 : 6,4 % de WER après le canal contre
  20 % pour l'autre voix licenciée, à latence identique).
"""

from __future__ import annotations

import json
import os
import urllib.request
import uuid as _uuid
from typing import Any, Callable, Iterator, Mapping

VOIX_PAR_DEFAUT = os.path.expanduser("~/piper/fr_FR-siwis-medium.onnx")
MODELE_STT_PAR_DEFAUT = "whisper-large-v3-turbo"
DELAI_STT_S = 10.0


class MoteurAbsent(RuntimeError):
    """Le moteur demandé n'existe pas, ou ne peut pas être chargé ici."""


# --- transcription -----------------------------------------------------------

def _transcription_distante(base: str, cle: str, modele: str, **_) -> Callable[..., str]:
    """Un service compatible OpenAI. Le nom du modèle vient de la configuration."""

    def transcrire(audio: bytes, frequence: int) -> str:
        limite = _uuid.uuid4().hex
        corps = bytearray()

        def champ(nom, valeur):
            corps.extend(f"--{limite}\r\nContent-Disposition: form-data; "
                         f'name="{nom}"\r\n\r\n{valeur}\r\n'.encode())

        corps.extend(f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; "
                     f'filename="appel.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode())
        corps.extend(_en_wav(audio, frequence))
        corps.extend(b"\r\n")
        champ("model", modele)
        champ("language", "fr")
        champ("response_format", "json")
        corps.extend(f"--{limite}--\r\n".encode())

        requete = urllib.request.Request(
            f"{base}/audio/transcriptions", data=bytes(corps),
            headers={"Authorization": f"Bearer {cle}",
                     "Content-Type": f"multipart/form-data; boundary={limite}",
                     "User-Agent": "standard-telephonique/0.1"})
        with urllib.request.urlopen(requete, timeout=DELAI_STT_S) as reponse:
            return json.load(reponse).get("text", "").strip()

    return transcrire


def _en_wav(audio: bytes, frequence: int) -> bytes:
    """Enveloppe PCM en WAV, en mémoire : pas de fichier, pas de processus."""
    import io
    import wave

    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as sortie:
        sortie.setnchannels(1)
        sortie.setsampwidth(2)
        sortie.setframerate(frequence)
        sortie.writeframes(audio)
    return tampon.getvalue()


def _transcription_locale(modele: str, **_) -> Callable[..., str]:
    """sherpa-onnx en flux — mesuré à RTF 0,065, soit une quinzaine de flux par cœur."""
    try:
        import sherpa_onnx  # noqa: F401
    except ImportError as erreur:
        raise MoteurAbsent("sherpa-onnx n'est pas installé sur cette machine") from erreur

    import numpy as np
    import sherpa_onnx

    reconnaisseur = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=f"{modele}/tokens.txt",
        encoder=f"{modele}/encoder-epoch-29-avg-9-with-averaged-model.int8.onnx",
        decoder=f"{modele}/decoder-epoch-29-avg-9-with-averaged-model.int8.onnx",
        joiner=f"{modele}/joiner-epoch-29-avg-9-with-averaged-model.int8.onnx",
        num_threads=2, sample_rate=16000, feature_dim=80,
        enable_endpoint_detection=False, decoding_method="greedy_search")

    def transcrire(audio: bytes, frequence: int) -> str:
        echantillons = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        flux = reconnaisseur.create_stream()
        flux.accept_waveform(frequence, echantillons)
        flux.accept_waveform(frequence, np.zeros(int(0.5 * frequence), dtype=np.float32))
        flux.input_finished()
        while reconnaisseur.is_ready(flux):
            reconnaisseur.decode_stream(flux)
        return reconnaisseur.get_result(flux)

    return transcrire


def _transcription_muette(**_) -> Callable[..., str]:
    """Pour vérifier un déploiement avant d'avoir un moteur. À demander explicitement."""
    return lambda audio, frequence: ""


MOTEURS_STT: dict[str, Callable[..., Callable[..., str]]] = {
    "distant": _transcription_distante,
    "local": _transcription_locale,
    "muet": _transcription_muette,
}


def choisir_transcription(environnement: Mapping[str, str] | None = None,
                          moteurs: dict | None = None) -> Callable[[bytes, int], str]:
    env = dict(environnement if environnement is not None else os.environ)
    moteurs = MOTEURS_STT if moteurs is None else moteurs
    nom = env.get("STANDARD_STT")

    if not nom:
        raise MoteurAbsent("aucun moteur de transcription configuré : poser "
                           "STANDARD_STT (distant, local ou muet)")

    if nom not in moteurs:
        raise MoteurAbsent(f"moteur de transcription inconnu : {nom}")
    return moteurs[nom](base=env.get("STANDARD_STT_BASE", "https://api.groq.com/openai/v1"),
                        cle=env.get("STANDARD_STT_CLE", ""),
                        modele=env.get("STANDARD_STT_MODELE", MODELE_STT_PAR_DEFAUT))


# --- synthèse ----------------------------------------------------------------

def _charger_piper(chemin: str):
    from piper import PiperVoice
    return PiperVoice.load(chemin)


def choisir_synthese(environnement: Mapping[str, str] | None = None,
                     charger_voix: Callable[[str], Any] = _charger_piper
                     ) -> Callable[[str], Iterator[bytes]]:
    env = dict(environnement if environnement is not None else os.environ)
    nom = env.get("STANDARD_TTS", "piper")

    if nom == "muet":
        return lambda texte: iter([b""])

    if nom != "piper":
        raise MoteurAbsent(f"moteur de synthèse inconnu : {nom}")

    chemin = env.get("STANDARD_VOIX", VOIX_PAR_DEFAUT)
    try:
        voix = charger_voix(chemin)
    except ImportError as erreur:
        # Deux causes differentes appellent deux gestes differents : installer
        # une dependance n'est pas corriger un chemin.
        raise MoteurAbsent("la bibliothèque de synthèse n'est pas installée : "
                           "`pip install piper-tts`") from erreur
    except Exception as erreur:
        # Découvrir qu'il manque une voix au premier appelant est inacceptable :
        # on échoue ici, au démarrage, avec le chemin fautif.
        raise MoteurAbsent(f"voix introuvable ou illisible : {chemin}") from erreur

    def synthetiser(texte: str) -> Iterator[bytes]:
        for fragment in voix.synthesize(texte):
            brut = getattr(fragment, "audio_int16_bytes", None)
            if brut is None:
                brut = getattr(fragment, "audio_int16_array", b"")
                brut = brut.tobytes() if hasattr(brut, "tobytes") else bytes(brut)
            yield brut

    return synthetiser


# --- inventaire ---------------------------------------------------------------

def inventaire(environnement: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Ce qui est réellement disponible sur cette machine, sans rien promettre."""
    env = dict(environnement if environnement is not None else os.environ)
    etat: dict[str, Any] = {}

    for role, nom, choisir in (("transcription", env.get("STANDARD_STT", "—"),
                                lambda: choisir_transcription(env)),
                               ("synthese", env.get("STANDARD_TTS", "piper"),
                                lambda: choisir_synthese(env))):
        try:
            choisir()
            etat[role] = {"nom": nom, "disponible": True, "detail": ""}
        except MoteurAbsent as erreur:
            etat[role] = {"nom": nom, "disponible": False, "detail": str(erreur)}
    return etat
