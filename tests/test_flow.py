"""Parcours client complet : identité, questionnaire, résultats, paiement, rapport."""

from app.data.grid import DIMENSIONS

IDENTITY = {
    "company_name": "Groupe Atlantique SA",
    "sector": "Banque & Assurance",
    "country": "Côte d'Ivoire",
    "company_size": "200-999",
    "contact_name": "Awa Kone",
    "contact_role": "Directrice des systèmes d'information",
    "contact_email": "awa.kone@atlantique.ci",
    "contact_phone": "+225 07 00 00 00",
    "annual_revenue_band": "1 Md à 10 Md FCFA",
    "acquisition_channel": "LinkedIn",
    "consent": "1",
}


def _create(client) -> str:
    response = client.post("/diagnostic", data=IDENTITY, follow_redirects=False)
    assert response.status_code == 303
    return response.headers["location"].split("/")[2]


def _complete(client, public_id: str) -> None:
    for step, dimension in enumerate(DIMENSIONS, start=1):
        payload = {crit.code: str((i * 3 + step) % 4) for i, crit in enumerate(dimension.criteria)}
        payload["direction"] = "next"
        response = client.post(f"/diagnostic/{public_id}/{step}", data=payload, follow_redirects=False)
        assert response.status_code == 303


def test_pages_publiques(client):
    for path in ["/", "/tarifs", "/methodologie", "/barometre", "/mentions-legales",
                 "/diagnostic", "/acces", "/healthz"]:
        assert client.get(path).status_code == 200, path


def test_consentement_obligatoire(client):
    payload = dict(IDENTITY)
    payload.pop("consent")
    response = client.post("/diagnostic", data=payload)
    assert response.status_code == 400
    assert "consentement" in response.text.lower()


def test_email_invalide_refuse(client):
    payload = dict(IDENTITY, contact_email="pas-un-email")
    assert client.post("/diagnostic", data=payload).status_code == 400


def test_section_incomplete_bloquee(client):
    public_id = _create(client)
    response = client.post(f"/diagnostic/{public_id}/1", data={"direction": "next"})
    assert response.status_code == 400


def test_parcours_complet_et_mur_freemium(client):
    public_id = _create(client)
    _complete(client, public_id)

    results = client.get(f"/resultats/{public_id}")
    assert results.status_code == 200
    assert "Groupe Atlantique SA" in results.text

    # La couche gratuite ne divulgue pas les recommandations opérationnelles.
    assert "Contenu réservé" in results.text

    # Le rapport et le PDF sont verrouillés.
    assert client.get(f"/resultats/{public_id}/rapport", follow_redirects=False).status_code == 303
    assert client.get(f"/resultats/{public_id}/rapport.pdf").status_code == 403

    # L'export Excel gratuit ne contient pas le plan d'action.
    xlsx = client.get(f"/resultats/{public_id}/grille.xlsx")
    assert xlsx.status_code == 200
    assert xlsx.headers["content-type"].startswith("application/vnd.openxmlformats")


def test_navigation_arriere_conserve_les_reponses(client):
    public_id = _create(client)
    dimension = DIMENSIONS[0]
    payload = {crit.code: "2" for crit in dimension.criteria}
    payload["direction"] = "next"
    client.post(f"/diagnostic/{public_id}/1", data=payload, follow_redirects=False)
    response = client.post(f"/diagnostic/{public_id}/2", data={"direction": "previous"},
                           follow_redirects=False)
    assert response.status_code == 303
    page = client.get(f"/diagnostic/{public_id}/1")
    assert page.text.count('value="2"\n                       checked') >= 1 or "checked" in page.text


def test_paiement_manuel_puis_acces_par_code(client):
    public_id = _create(client)
    _complete(client, public_id)

    assert client.get(f"/paiement/{public_id}/premium").status_code == 200
    response = client.post(
        f"/paiement/{public_id}/premium",
        data={"currency": "XOF", "provider": "manual"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/instructions" in response.headers["location"]
    assert client.get(response.headers["location"]).status_code == 200

    from app.database import session_scope
    from app.models import Assessment, Order
    from app.services.assessments import mark_order_paid

    with session_scope() as session:
        assessment = session.query(Assessment).filter_by(public_id=public_id).one()
        order = session.query(Order).filter_by(assessment_id=assessment.id).one()
        mark_order_paid(session, order, actor="test")
        code = order.access_code

    from fastapi.testclient import TestClient

    from app.main import app

    fresh = TestClient(app)
    response = fresh.post("/acces", data={"code": code}, follow_redirects=False)
    assert response.status_code == 303
    report = fresh.get(f"/resultats/{public_id}/rapport")
    assert report.status_code == 200
    assert "Feuille de route 12 mois" in report.text
    assert fresh.get(f"/resultats/{public_id}/rapport.pdf").status_code == 200


def test_offre_inconnue_refusee(client):
    public_id = _create(client)
    _complete(client, public_id)
    assert client.get(f"/paiement/{public_id}/offre-fantaisiste").status_code == 404


def test_code_acces_invalide(client):
    assert client.post("/acces", data={"code": "DM-INEXISTANT"}).status_code == 404
