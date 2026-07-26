"""API JSON destinée aux intégrations."""


def test_grille_exposee(client):
    payload = client.get("/api/v1/grid").json()
    assert payload["criteria_count"] == 45
    assert payload["max_score"] == 768
    assert len(payload["dimensions"]) == 7
    assert sum(len(d["criteria"]) for d in payload["dimensions"]) == 45


def test_niveaux(client):
    levels = client.get("/api/v1/levels").json()
    assert [l["code"] for l in levels] == ["debutant", "emergent", "avance", "leader"]


def test_calcul_de_score(client, full_answers):
    response = client.post("/api/v1/score", json={"answers": full_answers, "company_size": "50-199"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["complete"] is True
    assert payload["max_score"] == 768
    assert 0 < payload["total_score"] <= 768
    assert payload["recommendations_count"] > 0


def test_tarifs_en_trois_devises(client):
    payload = client.get("/api/v1/pricing").json()
    assert payload["currencies"] == ["XOF", "EUR", "USD"]
    premium = next(p for p in payload["plans"] if p["code"] == "premium")
    assert set(premium["prices"]) == {"XOF", "EUR", "USD"}
    assert premium["prices"]["XOF"]["minor_units"] > 0


def test_barometre(client):
    payload = client.get("/api/v1/barometer").json()
    assert "overall" in payload
    assert "threshold" in payload


def test_evaluation_inconnue(client):
    assert client.get("/api/v1/assessments/inexistant").status_code == 404


def test_documentation_disponible(client):
    assert client.get("/api/openapi.json").status_code == 200
