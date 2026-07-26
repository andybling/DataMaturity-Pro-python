"""Le moteur d'analyse doit être déterministe et cohérent."""

from app.data.grid import ALL_CRITERIA
from app.services.analysis import build_analysis
from app.services.scoring import compute_score


def _analysis(value: int):
    return build_analysis(
        compute_score({c.code: value for c in ALL_CRITERIA}),
        company_size_code="200-999",
        company_name="Test SA",
        sector="Banque & Assurance",
    )


def test_determinisme(full_answers):
    first = build_analysis(compute_score(full_answers))
    second = build_analysis(compute_score(full_answers))
    assert first.headline == second.headline
    assert first.executive_summary == second.executive_summary
    assert [r.criterion_code for r in first.recommendations] == [
        r.criterion_code for r in second.recommendations
    ]


def test_aucune_recommandation_au_niveau_maximum():
    analysis = _analysis(3)
    assert analysis.recommendations == []
    assert analysis.total_value_at_stake_xof == 0


def test_toutes_les_recommandations_au_niveau_zero():
    analysis = _analysis(0)
    assert len(analysis.recommendations) == 45
    assert analysis.total_value_at_stake_xof > 0


def test_priorisation_decroissante(full_answers):
    analysis = build_analysis(compute_score(full_answers))
    scores = [r.priority_score for r in analysis.recommendations]
    assert scores == sorted(scores, reverse=True)
    assert [r.priority_rank for r in analysis.recommendations] == list(
        range(1, len(analysis.recommendations) + 1)
    )


def test_feuille_de_route_couvre_toutes_les_actions(full_answers):
    analysis = build_analysis(compute_score(full_answers))
    planned = sum(len(quarter.recommendations) for quarter in analysis.roadmap)
    assert planned == len(analysis.recommendations)
    assert all(1 <= reco.quarter <= 4 for reco in analysis.recommendations)


def test_projection_superieure_au_score_actuel(full_answers):
    analysis = build_analysis(compute_score(full_answers))
    assert analysis.projected_percentage >= analysis.score.percentage
    assert analysis.projected_percentage <= 100.0


def test_resume_public_masque_les_recommandations(full_answers):
    from app.services.analysis import public_summary

    analysis = build_analysis(compute_score(full_answers))
    summary = public_summary(analysis)
    assert summary["locked_recommendations"] == len(analysis.recommendations)
    assert "recommendations" not in summary
    assert len(summary["strengths"]) == 3
    assert len(summary["watchpoints"]) == 3
