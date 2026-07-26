"""Console d'administration : contrôle d'accès et fonctions de pilotage."""

PROTECTED = [
    "/admin",
    "/admin/prospects",
    "/admin/commandes",
    "/admin/tarification",
    "/admin/barometre",
    "/admin/journal",
    "/admin/compte",
]


def test_acces_refuse_sans_session(client):
    for path in PROTECTED:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303, path
        assert response.headers["location"] == "/admin/connexion"


def test_mauvais_identifiants(client):
    response = client.post("/admin/connexion", data={"username": "admin", "password": "faux"})
    assert response.status_code == 401


def test_pages_admin_accessibles(admin_client):
    for path in PROTECTED:
        assert admin_client.get(path).status_code == 200, path


def test_exports(admin_client):
    csv_response = admin_client.get("/admin/prospects/export.csv")
    assert csv_response.status_code == 200
    assert csv_response.content.startswith(b"\xef\xbb\xbf")  # BOM pour Excel
    assert b"organisation" in csv_response.content

    xlsx_response = admin_client.get("/admin/prospects/export.xlsx")
    assert xlsx_response.status_code == 200
    assert xlsx_response.content[:2] == b"PK"  # archive xlsx


def test_filtres_prospects(admin_client):
    response = admin_client.get("/admin/prospects?secteur=Banque+%26+Assurance&payes=1")
    assert response.status_code == 200


def test_mise_a_jour_tarification(admin_client):
    response = admin_client.post(
        "/admin/tarification",
        data={"price_standard": "59000", "price_premium": "169000", "fx_USD": "615"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    from app.database import session_scope
    from app.services.pricing import get_fx_rates, get_plan_prices_xof

    with session_scope() as session:
        assert get_plan_prices_xof(session)["standard"] == 59000
        assert get_fx_rates(session)["USD"] == 615.0

    public = admin_client.get("/tarifs")
    assert "59 000 FCFA" in public.text

    # remise en état pour les autres tests
    admin_client.post(
        "/admin/tarification",
        data={"price_standard": "49000", "price_premium": "149000", "fx_USD": "610"},
        follow_redirects=False,
    )


def test_changement_de_mot_de_passe_refuse_si_faible(admin_client):
    response = admin_client.post(
        "/admin/compte/mot-de-passe",
        data={"current_password": "motdepasse-de-test", "new_password": "court",
              "confirm_password": "court"},
    )
    assert response.status_code == 400


def test_journal_alimente(admin_client):
    response = admin_client.get("/admin/journal")
    assert "admin.login" in response.text
