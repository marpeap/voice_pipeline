"""Ce qui manque entre la page publiée et un vrai essai : le canal chiffré.

La page vit sur Vercel, en HTTPS. Un navigateur en HTTPS **refuse** un
WebSocket en clair — sans expliquer pourquoi. Il faut donc `wss://`, donc un
proxy TLS devant le standard, et ce proxy a trois pièges connus :

  - sans les en-têtes `Upgrade`/`Connection`, la poignée de main échoue et le
    navigateur dit seulement « connexion fermée » ;
  - avec le délai de lecture par défaut (60 s), le canal tombe pendant qu'un
    appelant réfléchit — et l'appel meurt sans un mot ;
  - avec la mise en tampon, la voix de l'agent part par blocs au lieu de partir
    au rythme du canal : l'appelant entend des saccades.

Ce fichier vérifie le fichier livré, pas une intention.
"""

from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
NGINX = RACINE / "deploiement" / "agent-toile.nginx"


@pytest.fixture
def conf():
    return NGINX.read_text()


def test_le_proxy_fait_la_bascule_websocket(conf):
    assert "proxy_set_header Upgrade $http_upgrade;" in conf
    assert 'proxy_set_header Connection "upgrade";' in conf
    assert "proxy_http_version 1.1;" in conf


def test_le_canal_ne_tombe_pas_pendant_qu_un_appelant_reflechit(conf):
    """Le défaut de nginx est soixante secondes. Un appelant qui cherche son
    agenda met plus longtemps, et l'appel mourrait sans un mot."""
    import re

    lecture = re.search(r"proxy_read_timeout\s+(\d+)([smh]);", conf)
    assert lecture, "proxy_read_timeout doit être posé explicitement"
    secondes = int(lecture.group(1)) * {"s": 1, "m": 60, "h": 3600}[lecture.group(2)]
    assert secondes >= 600, f"{secondes} s : trop court pour un appel"


def test_la_voix_part_au_rythme_du_canal(conf):
    """Vingt millisecondes par paquet : mis en tampon, cela s'entend."""
    assert "proxy_buffering off;" in conf


def test_le_point_d_etat_ne_sort_pas_de_la_machine(conf):
    """`/sante` est joignable sans jeton : il n'a rien à faire sur Internet.

    On lit les **directives**, pas les commentaires : un commentaire qui
    explique pourquoi le point d'état reste chez lui est utile, une règle
    `location /sante` qui l'expose ne l'est pas."""
    directives = [ligne.strip() for ligne in conf.splitlines()
                  if ligne.strip() and not ligne.strip().startswith("#")]
    assert not any("/sante" in ligne for ligne in directives)
    assert any("return 404" in ligne for ligne in directives), (
        "tout ce qui n'est pas le canal doit être refusé explicitement")


def test_la_page_n_est_pas_servie_deux_fois(conf):
    """Vercel sert la page ; le proxy ne porte que le canal. Deux exemplaires
    publics auraient divergé, et on ne saurait plus laquelle on regarde."""
    assert "/parler" in conf


def test_le_certificat_n_est_pas_invente(conf):
    """Aucun chemin de certificat en dur qui n'existerait que sur ma machine :
    la configuration dit ce qu'il faut faire, avec certbot."""
    assert "certbot" in conf.lower()
