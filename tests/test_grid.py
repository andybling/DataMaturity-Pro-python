"""La grille chargée doit être conforme au fichier Limpida 2024."""

from app.data.grid import ALL_CRITERIA, DIMENSIONS, MAX_TOTAL_SCORE

EXPECTED_SUBTOTALS = {
    "governance": 126,
    "quality": 135,
    "security": 126,
    "integration": 90,
    "analytics": 84,
    "culture": 72,
    "infrastructure": 135,
}


def test_structure_globale():
    assert len(DIMENSIONS) == 7
    assert len(ALL_CRITERIA) == 45
    assert MAX_TOTAL_SCORE == 768


def test_sous_totaux_par_dimension():
    for dimension in DIMENSIONS:
        assert dimension.max_score == EXPECTED_SUBTOTALS[dimension.code], dimension.name
    assert sum(EXPECTED_SUBTOTALS.values()) == 768


def test_ponderations_et_niveaux():
    for criterion in ALL_CRITERIA:
        assert criterion.weight in {1, 2, 3}
        assert len(criterion.levels) == 4
        assert all(label.strip() for label in criterion.levels)
        assert criterion.max_score == 3 * criterion.weight * criterion.dimension_weight


def test_codes_uniques():
    codes = [criterion.code for criterion in ALL_CRITERIA]
    assert len(codes) == len(set(codes))


def test_chaque_critere_a_une_recommandation():
    from app.data.recommendations import R

    for criterion in ALL_CRITERIA:
        assert criterion.code in R, criterion.code
        entry = R[criterion.code]
        assert entry["action"] and entry["why"] and entry["kpi"]
        assert len(entry["steps"]) == 3
        assert entry["effort"] in {"faible", "moyen", "élevé"}


def test_normalisation_des_urls_de_base_de_donnees():
    """Les hébergeurs managés exposent postgres:// : SQLAlchemy 2 exige le pilote explicite."""
    from app.database import normalise_database_url

    assert normalise_database_url("postgres://u:p@h:5432/d") == "postgresql+psycopg://u:p@h:5432/d"
    assert normalise_database_url("postgresql://u:p@h:5432/d") == "postgresql+psycopg://u:p@h:5432/d"
    assert normalise_database_url("postgresql+psycopg://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert normalise_database_url("sqlite:///./data/x.db") == "sqlite:///./data/x.db"
