"""Le moteur de scoring doit reproduire exactement la formule de la grille."""

import pytest

from app.data.grid import ALL_CRITERIA, MAX_TOTAL_SCORE
from app.services.scoring import compute_score


def test_score_maximum():
    result = compute_score({c.code: 3 for c in ALL_CRITERIA})
    assert result.total_score == MAX_TOTAL_SCORE
    assert result.percentage == 100.0
    assert result.level.code == "leader"
    assert result.is_complete


def test_score_minimum():
    result = compute_score({c.code: 0 for c in ALL_CRITERIA})
    assert result.total_score == 0
    assert result.percentage == 0.0
    assert result.level.code == "debutant"


def test_reponses_manquantes_signalees():
    result = compute_score({})
    assert not result.is_complete
    assert len(result.missing) == 45


def test_bornage_des_reponses():
    result = compute_score({c.code: 99 for c in ALL_CRITERIA})
    assert result.total_score == MAX_TOTAL_SCORE
    result = compute_score({c.code: -5 for c in ALL_CRITERIA})
    assert result.total_score == 0


def test_codes_inconnus_ignores():
    result = compute_score({"dimension.inexistante": 3})
    assert result.answered_count == 0


@pytest.mark.parametrize(
    "answer,expected",
    [(0, 0), (1, 9), (2, 18), (3, 27)],
)
def test_formule_ponderee(answer, expected):
    """Politique de données : poids critère 3, poids dimension 3 -> 3x3x3 = 27 points."""
    code = "governance.existence_d_une_politique_de_donnees"
    result = compute_score({code: answer})
    criterion = next(c for c in result.dimension("governance").criteria if c.code == code)
    assert criterion.score == expected


def test_seuils_de_niveau():
    from app.data.levels import level_for

    assert level_for(0).code == "debutant"
    assert level_for(24.9).code == "debutant"
    assert level_for(25).code == "emergent"
    assert level_for(49.9).code == "emergent"
    assert level_for(50).code == "avance"
    assert level_for(74.9).code == "avance"
    assert level_for(75).code == "leader"
    assert level_for(100).code == "leader"
