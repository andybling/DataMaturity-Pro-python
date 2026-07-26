"""Moteur d'analyse déterministe.

Aucune dépendance externe, aucun appel réseau : à scores identiques, l'analyse
produite est strictement identique. C'est ce qui rend le rapport défendable
devant un comité de direction et reproductible en audit.

Production :
    - une synthèse macro (couche gratuite)
    - un diagnostic par dimension et par critère (couche payante)
    - des recommandations priorisées
    - une feuille de route 12 mois en 4 trimestres
    - une estimation de valeur en jeu par dimension
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.data.levels import TARGET_LEVEL, level_for
from app.data.recommendations import (
    DIMENSION_VALUE_AT_STAKE,
    narrative_for,
    recommendation_for,
)
from app.data.reference import COMPANY_SIZES_BY_CODE
from app.services.scoring import CriterionResult, DimensionResult, ScoreResult

EFFORT_ORDER = {"faible": 0, "moyen": 1, "élevé": 2}
ROI_DRIVER_LABELS = {
    "risque": "Réduction du risque",
    "coûts évités": "Coûts évités",
    "productivité": "Gain de productivité",
    "revenus": "Croissance des revenus",
}


# ---------------------------------------------------------------------------
#  Structures de sortie
# ---------------------------------------------------------------------------


@dataclass
class Recommendation:
    criterion_code: str
    criterion_name: str
    dimension_code: str
    dimension_name: str
    action: str
    why: str
    steps: List[str]
    kpi: str
    effort: str
    roi_driver: str
    current_answer: int
    current_label: str
    target_label: str
    priority_score: int
    priority_rank: int = 0
    quarter: int = 1
    points_gain: int = 0

    @property
    def priority_label(self) -> str:
        if self.priority_score >= 18:
            return "Critique"
        if self.priority_score >= 12:
            return "Élevée"
        if self.priority_score >= 6:
            return "Moyenne"
        return "Optimisation"

    @property
    def roi_driver_label(self) -> str:
        return ROI_DRIVER_LABELS.get(self.roi_driver, self.roi_driver.capitalize())


@dataclass
class DimensionAnalysis:
    result: DimensionResult
    narrative: str
    strong_points: List[CriterionResult]
    weak_points: List[CriterionResult]
    value_at_stake_xof: int
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def code(self) -> str:
        return self.result.code

    @property
    def gap_points(self) -> int:
        return self.result.max_score - self.result.score


@dataclass
class RoadmapQuarter:
    index: int
    label: str
    theme: str
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def points_gain(self) -> int:
        return sum(r.points_gain for r in self.recommendations)


@dataclass
class Analysis:
    score: ScoreResult
    headline: str
    executive_summary: List[str]
    strengths: List[DimensionResult]
    watchpoints: List[DimensionResult]
    dimensions: List[DimensionAnalysis]
    recommendations: List[Recommendation]
    roadmap: List[RoadmapQuarter]
    quick_wins: List[Recommendation]
    total_value_at_stake_xof: int
    revenue_proxy_xof: int
    projected_percentage: float
    assumptions: List[str]

    def dimension(self, code: str) -> Optional[DimensionAnalysis]:
        return next((d for d in self.dimensions if d.code == code), None)


# ---------------------------------------------------------------------------
#  Construction de l'analyse
# ---------------------------------------------------------------------------


def _priority_score(crit: CriterionResult, dim: DimensionResult) -> int:
    """Priorité = poids stratégique x poids du critère x écart au niveau maximum.

    Un critère très important dans une dimension très importante et très mal noté
    ressort donc systématiquement en tête.
    """
    return dim.weight * crit.weight * crit.gap


def _quarter_for(rank: int, effort: str, total: int) -> int:
    """Répartit les actions sur 12 mois : priorité d'abord, effort ensuite.

    La charge est équilibrée entre les quatre trimestres (quartiles de priorité),
    puis décalée d'un trimestre pour les actions à effort élevé et avancée d'un
    trimestre pour les actions à effort faible (les « quick wins »).
    """
    per_quarter = max(1, math.ceil(total / 4))
    base = min(4, rank // per_quarter + 1)
    if effort == "élevé":
        base = min(4, base + 1)
    elif effort == "faible":
        base = max(1, base - 1)
    return base


QUARTER_THEMES = {
    1: "Sécuriser et cadrer",
    2: "Structurer et outiller",
    3: "Industrialiser",
    4: "Valoriser et pérenniser",
}


def build_analysis(
    score: ScoreResult,
    *,
    company_size_code: str = "50-199",
    company_name: str = "Votre organisation",
    sector: str = "",
) -> Analysis:
    """Produit l'analyse complète à partir d'un résultat de scoring."""
    size = COMPANY_SIZES_BY_CODE.get(company_size_code, COMPANY_SIZES_BY_CODE["50-199"])
    revenue_proxy = int(size["revenue_proxy_xof"])

    dimension_analyses: List[DimensionAnalysis] = []
    all_recos: List[Recommendation] = []

    for dim in score.dimensions:
        weak = [c for c in dim.criteria if c.answer < TARGET_LEVEL]
        strong = [c for c in dim.criteria if c.answer >= 3]
        gap_ratio = 1 - (dim.score / dim.max_score if dim.max_score else 0)
        value = int(revenue_proxy * DIMENSION_VALUE_AT_STAKE.get(dim.code, 0.005) * gap_ratio)

        recos: List[Recommendation] = []
        for crit in dim.criteria:
            if crit.answer >= 3:
                continue  # critère déjà au niveau maximum
            meta = recommendation_for(crit.code)
            if not meta:
                continue
            from app.data.grid import CRITERIA_BY_CODE

            grid_crit = CRITERIA_BY_CODE[crit.code]
            target = min(3, max(TARGET_LEVEL, crit.answer + 1))
            recos.append(
                Recommendation(
                    criterion_code=crit.code,
                    criterion_name=crit.name,
                    dimension_code=dim.code,
                    dimension_name=dim.name,
                    action=meta["action"],
                    why=meta["why"],
                    steps=list(meta["steps"]),
                    kpi=meta["kpi"],
                    effort=meta["effort"],
                    roi_driver=meta["roi_driver"],
                    current_answer=crit.answer,
                    current_label=crit.level_label,
                    target_label=grid_crit.levels[target],
                    priority_score=_priority_score(crit, dim),
                    points_gain=(target - crit.answer) * crit.weight * dim.weight,
                )
            )

        dimension_analyses.append(
            DimensionAnalysis(
                result=dim,
                narrative=narrative_for(dim.code, dim.percentage),
                strong_points=strong,
                weak_points=sorted(weak, key=lambda c: (c.answer, -c.weight)),
                value_at_stake_xof=value,
                recommendations=sorted(recos, key=lambda r: -r.priority_score),
            )
        )
        all_recos.extend(recos)

    # Priorisation globale : priorité décroissante, puis effort croissant.
    all_recos.sort(key=lambda r: (-r.priority_score, EFFORT_ORDER.get(r.effort, 1)))
    for rank, reco in enumerate(all_recos):
        reco.priority_rank = rank + 1
        reco.quarter = _quarter_for(rank, reco.effort, len(all_recos))

    roadmap = [
        RoadmapQuarter(index=q, label=f"Trimestre {q}", theme=QUARTER_THEMES[q],
                       recommendations=[r for r in all_recos if r.quarter == q])
        for q in (1, 2, 3, 4)
    ]

    quick_wins = sorted(
        [r for r in all_recos if r.effort == "faible"],
        key=lambda r: -r.priority_score,
    )[:5]

    total_value = sum(d.value_at_stake_xof for d in dimension_analyses)
    projected_points = score.total_score + sum(r.points_gain for r in all_recos)
    projected_pct = round(min(100.0, projected_points / score.max_score * 100), 1)

    return Analysis(
        score=score,
        headline=_headline(score, company_name),
        executive_summary=_executive_summary(score, dimension_analyses, sector, projected_pct),
        strengths=score.strengths,
        watchpoints=score.watchpoints,
        dimensions=dimension_analyses,
        recommendations=all_recos,
        roadmap=roadmap,
        quick_wins=quick_wins,
        total_value_at_stake_xof=total_value,
        revenue_proxy_xof=revenue_proxy,
        projected_percentage=projected_pct,
        assumptions=_assumptions(size, revenue_proxy),
    )


# ---------------------------------------------------------------------------
#  Rédaction des synthèses
# ---------------------------------------------------------------------------


def _headline(score: ScoreResult, company_name: str) -> str:
    lvl = score.level
    return (
        f"{company_name} obtient {score.total_score} points sur {score.max_score} "
        f"({score.percentage:.1f} %), soit un niveau de maturité data « {lvl.name} »."
    )


def _executive_summary(
    score: ScoreResult,
    dimensions: List[DimensionAnalysis],
    sector: str,
    projected_pct: float,
) -> List[str]:
    lvl = score.level
    best = score.strengths[0]
    worst = score.watchpoints[0]
    critical = [d for d in dimensions if d.result.weight == 3 and d.result.percentage < 50]
    spread = round(best.percentage - worst.percentage, 1)

    paragraphs = [lvl.summary, lvl.stake]

    paragraphs.append(
        f"La dimension la plus solide est « {best.name} » à {best.percentage:.0f} %, "
        f"tandis que « {worst.name} » constitue le point le plus fragile à {worst.percentage:.0f} %. "
        f"L'écart de {spread:.0f} points entre les deux mesure le déséquilibre interne du dispositif : "
        + (
            "il est suffisamment marqué pour que les investissements réalisés sur les dimensions avancées "
            "soient partiellement neutralisés par les plus faibles."
            if spread >= 25
            else "il reste contenu, ce qui indique une progression relativement homogène."
        )
    )

    if critical:
        noms = ", ".join(f"« {d.result.name} » ({d.result.percentage:.0f} %)" for d in critical)
        if len(critical) == 1:
            phrase = (
                f"Point de vigilance majeur : une dimension à poids stratégique maximal reste "
                f"sous le seuil de 50 % — {noms}. Dans la grille Limpida, cette dimension compte "
                "triple dans le score final : c'est là que se situe le meilleur rendement d'effort."
            )
        else:
            phrase = (
                f"Point de vigilance majeur : {len(critical)} dimensions à poids stratégique maximal "
                f"restent sous le seuil de 50 % — {noms}. Dans la grille Limpida, ces dimensions comptent "
                "triple dans le score final : c'est là que se situe le meilleur rendement d'effort."
            )
        paragraphs.append(phrase)
    else:
        paragraphs.append(
            "Aucune dimension à poids stratégique maximal ne se situe sous le seuil de 50 %, "
            "ce qui indique un socle équilibré sur les sujets les plus structurants."
        )

    secteur_txt = f" dans le secteur {sector.lower()}" if sector else ""
    paragraphs.append(
        f"À périmètre constant, la mise en oeuvre des actions prioritaires identifiées permettrait "
        f"d'atteindre environ {projected_pct:.0f} % sur douze mois{secteur_txt}, "
        f"soit un passage au niveau « {level_for(projected_pct).name} »."
    )
    return paragraphs


def _assumptions(size: dict, revenue_proxy: int) -> List[str]:
    return [
        f"Effectif déclaré : {size['label']}.",
        f"Chiffre d'affaires de référence retenu pour l'estimation : {revenue_proxy:,.0f} FCFA".replace(",", " ")
        + " (valeur médiane de la bande d'effectif, à remplacer par le chiffre réel pour affiner).",
        "La valeur en jeu est calculée comme : CA de référence x exposition de la dimension x écart de maturité.",
        "Les taux d'exposition par dimension sont volontairement prudents et documentés dans le module de calcul.",
        "Cette estimation sert à ordonner les priorités, non à constituer un engagement de résultat.",
    ]


def public_summary(analysis: Analysis) -> Dict[str, object]:
    """Version limitée de l'analyse, exposée gratuitement (couche lead generation).

    Volontairement dépourvue de recommandations opérationnelles : les scores et
    le constat sont visibles, le « comment » reste dans l'offre payante.
    """
    return {
        "headline": analysis.headline,
        "level": analysis.score.level,
        "summary": analysis.executive_summary[:3],
        "strengths": [
            {"name": d.name, "percentage": d.percentage, "color": d.color}
            for d in analysis.strengths
        ],
        "watchpoints": [
            {"name": d.name, "percentage": d.percentage, "color": d.color}
            for d in analysis.watchpoints
        ],
        "locked_recommendations": len(analysis.recommendations),
        "locked_quick_wins": len(analysis.quick_wins),
    }
