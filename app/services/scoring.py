"""Moteur de scoring : applique la pondération à deux niveaux de la grille Limpida.

Formule : score_critère = réponse (0-3) x poids_critère x poids_dimension
Le score maximum de référence est de 768 points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

from app.data.grid import ALL_CRITERIA, CRITERIA_BY_CODE, DIMENSIONS, MAX_TOTAL_SCORE
from app.data.levels import MaturityLevel, level_for


@dataclass
class CriterionResult:
    code: str
    name: str
    answer: int
    weight: int
    score: int
    max_score: int
    level_label: str

    @property
    def percentage(self) -> float:
        return round(self.score / self.max_score * 100, 1) if self.max_score else 0.0

    @property
    def gap(self) -> int:
        """Écart en points de réponse jusqu'au niveau 3."""
        return 3 - self.answer


@dataclass
class DimensionResult:
    code: str
    name: str
    short_name: str
    weight: int
    color: str
    score: int
    max_score: int
    criteria: List[CriterionResult] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return round(self.score / self.max_score * 100, 1) if self.max_score else 0.0

    @property
    def level(self) -> MaturityLevel:
        return level_for(self.percentage)

    @property
    def weakest_criteria(self) -> List[CriterionResult]:
        return sorted(self.criteria, key=lambda c: (c.answer, -c.weight))


@dataclass
class ScoreResult:
    total_score: int
    max_score: int
    dimensions: List[DimensionResult]
    answered_count: int
    missing: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return round(self.total_score / self.max_score * 100, 1) if self.max_score else 0.0

    @property
    def level(self) -> MaturityLevel:
        return level_for(self.percentage)

    @property
    def is_complete(self) -> bool:
        return not self.missing

    def dimension(self, code: str) -> Optional[DimensionResult]:
        return next((d for d in self.dimensions if d.code == code), None)

    @property
    def strengths(self) -> List[DimensionResult]:
        """Trois dimensions les mieux notées (par pourcentage décroissant)."""
        return sorted(self.dimensions, key=lambda d: -d.percentage)[:3]

    @property
    def watchpoints(self) -> List[DimensionResult]:
        """Trois dimensions les plus fragiles, à poids stratégique égal les plus lourdes d'abord."""
        return sorted(self.dimensions, key=lambda d: (d.percentage, -d.weight))[:3]

    def to_dict(self) -> Dict[str, dict]:
        """Représentation sérialisable, stockée avec l'évaluation."""
        return {
            d.code: {
                "name": d.name,
                "short_name": d.short_name,
                "weight": d.weight,
                "color": d.color,
                "score": d.score,
                "max_score": d.max_score,
                "percentage": d.percentage,
                "level": d.level.code,
                "criteria": [
                    {
                        "code": c.code,
                        "name": c.name,
                        "answer": c.answer,
                        "weight": c.weight,
                        "score": c.score,
                        "max_score": c.max_score,
                    }
                    for c in d.criteria
                ],
            }
            for d in self.dimensions
        }


def normalise_answers(raw: Mapping[str, object]) -> Dict[str, int]:
    """Ne conserve que les codes de critères connus et borne les réponses entre 0 et 3."""
    clean: Dict[str, int] = {}
    for code, value in raw.items():
        if code not in CRITERIA_BY_CODE:
            continue
        try:
            answer = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        clean[code] = max(0, min(3, answer))
    return clean


def compute_score(answers: Mapping[str, object]) -> ScoreResult:
    """Calcule le score global, par dimension et par critère.

    Les critères non renseignés sont comptés comme 0 mais listés dans `missing`,
    ce qui permet de bloquer la finalisation d'une évaluation incomplète.
    """
    clean = normalise_answers(answers)
    dimension_results: List[DimensionResult] = []
    total = 0

    for dim in DIMENSIONS:
        crit_results: List[CriterionResult] = []
        dim_score = 0
        for crit in dim.criteria:
            answer = clean.get(crit.code, 0)
            score = crit.score(answer)
            dim_score += score
            crit_results.append(
                CriterionResult(
                    code=crit.code,
                    name=crit.name,
                    answer=answer,
                    weight=crit.weight,
                    score=score,
                    max_score=crit.max_score,
                    level_label=crit.levels[answer] if 0 <= answer < len(crit.levels) else "",
                )
            )
        total += dim_score
        dimension_results.append(
            DimensionResult(
                code=dim.code,
                name=dim.name,
                short_name=dim.short_name,
                weight=dim.weight,
                color=dim.color,
                score=dim_score,
                max_score=dim.max_score,
                criteria=crit_results,
            )
        )

    missing = [c.code for c in ALL_CRITERIA if c.code not in clean]
    return ScoreResult(
        total_score=total,
        max_score=MAX_TOTAL_SCORE,
        dimensions=dimension_results,
        answered_count=len(clean),
        missing=missing,
    )
