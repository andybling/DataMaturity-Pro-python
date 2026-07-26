"""API JSON : intégration dans un intranet, un CRM ou un tableau de bord tiers."""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.data.grid import CRITERIA_COUNT, DIMENSIONS, MAX_TOTAL_SCORE
from app.data.levels import LEVELS
from app.database import get_session
from app.services import assessments as svc
from app.services.analysis import build_analysis
from app.services.benchmark import public_barometer
from app.services.pricing import SUPPORTED_CURRENCIES, plan_views
from app.services.scoring import compute_score

router = APIRouter(prefix="/api/v1", tags=["api"])


# ---------------------------------------------------------------------------
#  Schémas
# ---------------------------------------------------------------------------


class CriterionOut(BaseModel):
    code: str
    name: str
    weight: int
    max_score: int
    levels: List[str]


class DimensionOut(BaseModel):
    code: str
    name: str
    short_name: str
    weight: int
    max_score: int
    criteria: List[CriterionOut]


class GridOut(BaseModel):
    source: str
    criteria_count: int
    max_score: int
    dimensions: List[DimensionOut]


class ScoreRequest(BaseModel):
    answers: Dict[str, int] = Field(..., description="Code de critère -> réponse de 0 à 3")
    company_size: str = Field("50-199", description="Code de bande d'effectif")
    company_name: str = "Votre organisation"
    sector: str = ""


class DimensionScoreOut(BaseModel):
    code: str
    name: str
    weight: int
    score: int
    max_score: int
    percentage: float
    level: str


class ScoreOut(BaseModel):
    total_score: int
    max_score: int
    percentage: float
    level: str
    level_name: str
    complete: bool
    missing: List[str]
    dimensions: List[DimensionScoreOut]
    headline: Optional[str] = None
    recommendations_count: int = 0


class AssessmentOut(BaseModel):
    public_id: str
    company_name: str
    sector: str
    country: str
    status: str
    total_score: int
    max_score: int
    percentage: float
    level: str
    unlocked: bool


# ---------------------------------------------------------------------------
#  Endpoints
# ---------------------------------------------------------------------------


@router.get("/grid", response_model=GridOut, summary="Grille de maturité complète")
async def get_grid() -> GridOut:
    return GridOut(
        source="Grille de maturité Data — Limpida Consulting 2024",
        criteria_count=CRITERIA_COUNT,
        max_score=MAX_TOTAL_SCORE,
        dimensions=[
            DimensionOut(
                code=d.code,
                name=d.name,
                short_name=d.short_name,
                weight=d.weight,
                max_score=d.max_score,
                criteria=[
                    CriterionOut(
                        code=c.code, name=c.name, weight=c.weight,
                        max_score=c.max_score, levels=c.levels,
                    )
                    for c in d.criteria
                ],
            )
            for d in DIMENSIONS
        ],
    )


@router.get("/levels", summary="Niveaux de maturité et seuils")
async def get_levels() -> List[dict]:
    return [
        {"code": l.code, "name": l.name, "min": l.min_pct, "max": l.max_pct, "color": l.color}
        for l in LEVELS
    ]


@router.post("/score", response_model=ScoreOut, summary="Calcul de score sans persistance")
async def post_score(payload: ScoreRequest) -> ScoreOut:
    score = compute_score(payload.answers)
    analysis = build_analysis(
        score,
        company_size_code=payload.company_size,
        company_name=payload.company_name,
        sector=payload.sector,
    )
    return ScoreOut(
        total_score=score.total_score,
        max_score=score.max_score,
        percentage=score.percentage,
        level=score.level.code,
        level_name=score.level.name,
        complete=score.is_complete,
        missing=score.missing,
        dimensions=[
            DimensionScoreOut(
                code=d.code, name=d.name, weight=d.weight, score=d.score,
                max_score=d.max_score, percentage=d.percentage, level=d.level.code,
            )
            for d in score.dimensions
        ],
        headline=analysis.headline,
        recommendations_count=len(analysis.recommendations),
    )


@router.get("/assessments/{public_id}", response_model=AssessmentOut,
            summary="État d'une évaluation")
async def get_assessment(public_id: str, session: Session = Depends(get_session)) -> AssessmentOut:
    assessment = svc.get_assessment(session, public_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    return AssessmentOut(
        public_id=assessment.public_id,
        company_name=assessment.company_name,
        sector=assessment.sector,
        country=assessment.country,
        status=assessment.status,
        total_score=assessment.total_score,
        max_score=assessment.max_score,
        percentage=assessment.percentage,
        level=assessment.level_code,
        unlocked=assessment.is_unlocked,
    )


@router.get("/pricing", summary="Tarifs par offre et par devise")
async def get_pricing(session: Session = Depends(get_session)) -> dict:
    out: dict = {"currencies": SUPPORTED_CURRENCIES, "plans": []}
    for view in plan_views("XOF", session=session):
        out["plans"].append(
            {
                "code": view.code,
                "name": view.plan.name,
                "quote_only": view.plan.quote_only,
                "recurring": view.plan.recurring,
                "prices": {
                    code: {"amount": float(price.amount), "formatted": price.formatted,
                           "minor_units": price.minor_units}
                    for code, price in view.all_prices.items()
                },
            }
        )
    return out


@router.get("/barometer", summary="Baromètre agrégé anonymisé")
async def get_barometer(session: Session = Depends(get_session)) -> dict:
    data = public_barometer(session)
    return {
        "threshold": data["threshold"],
        "publishable": data["publishable"],
        "overall": {
            "sample": data["overall"].sample,
            "average": data["overall"].average,
            "median": data["overall"].median,
            "dimension_averages": data["overall"].dimension_averages,
            "level_distribution": data["overall"].level_distribution,
        },
        "sectors": [
            {"label": s.label, "sample": s.sample, "average": s.average, "median": s.median}
            for s in data["sectors"]
        ],
        "countries": [
            {"label": s.label, "sample": s.sample, "average": s.average, "median": s.median}
            for s in data["countries"]
        ],
    }
