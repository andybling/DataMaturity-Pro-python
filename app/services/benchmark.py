"""Baromètre : agrégation anonymisée des évaluations.

Deux usages :
    1. positionnement du client dans son secteur et son pays (offre payante) ;
    2. contenu marketing agrégé publiable (« Baromètre de la maturité data »).

Règle de confidentialité : aucun segment n'est publié en dessous du seuil
`MIN_BENCHMARK_SAMPLE`, afin qu'aucune organisation ne soit identifiable par
recoupement.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.data.grid import DIMENSIONS
from app.data.levels import level_for
from app.models import STATUS_COMPLETED, Assessment


@dataclass
class Segment:
    label: str
    kind: str          # secteur | pays | taille | global
    sample: int
    average: float
    median: float
    best: float
    worst: float
    dimension_averages: Dict[str, float] = field(default_factory=dict)
    level_distribution: Dict[str, int] = field(default_factory=dict)

    @property
    def is_publishable(self) -> bool:
        return self.sample >= settings.min_benchmark_sample

    @property
    def level_name(self) -> str:
        return level_for(self.average).name


def _completed(session: Session) -> List[Assessment]:
    return list(
        session.scalars(
            select(Assessment).where(Assessment.status == STATUS_COMPLETED)
        ).all()
    )


def _build_segment(label: str, kind: str, rows: List[Assessment]) -> Segment:
    pcts = [a.percentage for a in rows] or [0.0]
    dim_avg: Dict[str, float] = {}
    for dim in DIMENSIONS:
        values = []
        for a in rows:
            entry = a.dimension_scores.get(dim.code)
            if entry:
                values.append(float(entry.get("percentage", 0.0)))
        if values:
            dim_avg[dim.code] = round(statistics.fmean(values), 1)
    dist: Dict[str, int] = {}
    for a in rows:
        dist[a.level_code] = dist.get(a.level_code, 0) + 1
    return Segment(
        label=label,
        kind=kind,
        sample=len(rows),
        average=round(statistics.fmean(pcts), 1),
        median=round(statistics.median(pcts), 1),
        best=round(max(pcts), 1),
        worst=round(min(pcts), 1),
        dimension_averages=dim_avg,
        level_distribution=dist,
    )


def global_segment(session: Session) -> Segment:
    return _build_segment("Toutes organisations", "global", _completed(session))


def segments_by(session: Session, field_name: str) -> List[Segment]:
    """Agrège par `sector`, `country` ou `company_size`."""
    rows = _completed(session)
    buckets: Dict[str, List[Assessment]] = {}
    for row in rows:
        key = getattr(row, field_name, "") or "Non renseigné"
        buckets.setdefault(key, []).append(row)
    kind = {"sector": "secteur", "country": "pays", "company_size": "taille"}.get(field_name, field_name)
    out = [_build_segment(label, kind, items) for label, items in buckets.items()]
    return sorted(out, key=lambda s: -s.average)


@dataclass
class Positioning:
    """Position d'une évaluation par rapport à ses pairs."""

    sector: Optional[Segment]
    country: Optional[Segment]
    overall: Optional[Segment]
    percentile_sector: Optional[int]
    percentile_overall: Optional[int]
    delta_sector: Optional[float]
    delta_overall: Optional[float]
    comment: str


def _percentile(value: float, population: List[float]) -> Optional[int]:
    if len(population) < 2:
        return None
    below = sum(1 for p in population if p < value)
    return int(round(below / len(population) * 100))


def positioning_for(session: Session, assessment: Assessment) -> Positioning:
    rows = _completed(session)
    others = [a for a in rows if a.id != assessment.id]

    sector_rows = [a for a in others if a.sector == assessment.sector]
    country_rows = [a for a in others if a.country == assessment.country]

    sector_seg = _build_segment(assessment.sector, "secteur", sector_rows) if sector_rows else None
    country_seg = _build_segment(assessment.country, "pays", country_rows) if country_rows else None
    overall_seg = _build_segment("Toutes organisations", "global", others) if others else None

    pct_sector = _percentile(assessment.percentage, [a.percentage for a in sector_rows])
    pct_overall = _percentile(assessment.percentage, [a.percentage for a in others])

    delta_sector = (
        round(assessment.percentage - sector_seg.average, 1)
        if sector_seg and sector_seg.is_publishable
        else None
    )
    delta_overall = (
        round(assessment.percentage - overall_seg.average, 1)
        if overall_seg and overall_seg.is_publishable
        else None
    )

    if delta_sector is None:
        comment = (
            "L'échantillon sectoriel est encore insuffisant pour publier une comparaison "
            f"statistiquement honnête (moins de {settings.min_benchmark_sample} organisations "
            "évaluées dans ce secteur). Votre score reste interprétable en valeur absolue."
        )
    elif delta_sector >= 10:
        comment = (
            f"Votre organisation se situe {delta_sector:+.0f} points au-dessus de la moyenne "
            f"de son secteur. C'est un argument utilisable en comité comme auprès de vos partenaires."
        )
    elif delta_sector <= -10:
        comment = (
            f"Votre organisation se situe {delta_sector:+.0f} points en dessous de la moyenne "
            f"de son secteur : l'écart est suffisamment large pour constituer un désavantage "
            "opérationnel à moyen terme."
        )
    else:
        comment = (
            f"Votre organisation est dans la moyenne de son secteur ({delta_sector:+.0f} points). "
            "La différenciation se fera sur les dimensions les plus pondérées de la grille."
        )

    return Positioning(
        sector=sector_seg,
        country=country_seg,
        overall=overall_seg,
        percentile_sector=pct_sector,
        percentile_overall=pct_overall,
        delta_sector=delta_sector,
        delta_overall=delta_overall,
        comment=comment,
    )


def public_barometer(session: Session) -> dict:
    """Données agrégées publiables, filtrées par le seuil de confidentialité."""
    overall = global_segment(session)
    sectors = [s for s in segments_by(session, "sector") if s.is_publishable]
    countries = [s for s in segments_by(session, "country") if s.is_publishable]
    dimension_labels = {d.code: d.short_name for d in DIMENSIONS}
    return {
        "overall": overall,
        "sectors": sectors,
        "countries": countries,
        "dimension_labels": dimension_labels,
        "publishable": overall.is_publishable,
        "threshold": settings.min_benchmark_sample,
    }
