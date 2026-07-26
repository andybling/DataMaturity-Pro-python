"""Niveaux de maturité et seuils associés."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MaturityLevel:
    code: str
    name: str
    min_pct: float
    max_pct: float
    color: str
    summary: str
    stake: str


LEVELS: List[MaturityLevel] = [
    MaturityLevel(
        code="debutant",
        name="Débutant",
        min_pct=0.0,
        max_pct=25.0,
        color="#DC2626",
        summary=(
            "La donnée est encore traitée comme un sous-produit de l'activité. Les pratiques existent "
            "de manière isolée, portées par des individus plutôt que par des processus."
        ),
        stake=(
            "L'enjeu immédiat n'est pas technologique mais organisationnel : nommer des responsables, "
            "écrire les règles minimales et sécuriser l'existant avant d'investir dans des outils."
        ),
    ),
    MaturityLevel(
        code="emergent",
        name="Émergent",
        min_pct=25.0,
        max_pct=50.0,
        color="#EA580C",
        summary=(
            "Les fondations sont posées sur plusieurs dimensions mais restent inégales. L'organisation "
            "sait produire de la donnée, elle ne sait pas encore la garantir ni la réutiliser à l'échelle."
        ),
        stake=(
            "L'enjeu est la mise en cohérence : industrialiser ce qui fonctionne déjà, combler les écarts "
            "sur les dimensions à fort poids stratégique et rendre les résultats mesurables."
        ),
    ),
    MaturityLevel(
        code="avance",
        name="Avancé",
        min_pct=50.0,
        max_pct=75.0,
        color="#2563EB",
        summary=(
            "L'organisation dispose d'un socle data crédible : gouvernance formalisée, qualité mesurée, "
            "analyses utilisées dans les décisions courantes."
        ),
        stake=(
            "L'enjeu devient l'effet de levier : automatiser, démocratiser l'accès et passer d'une donnée "
            "de reporting à une donnée qui déclenche des actions opérationnelles."
        ),
    ),
    MaturityLevel(
        code="leader",
        name="Leader",
        min_pct=75.0,
        max_pct=100.01,
        color="#16A34A",
        summary=(
            "La donnée est un actif piloté, intégré à la stratégie et aux processus métier. "
            "Les pratiques sont automatisées, auditables et portées par une culture partagée."
        ),
        stake=(
            "L'enjeu est de tenir la position : maintenir la conformité, exploiter l'IA sur des cas "
            "d'usage à forte valeur et faire de la maturité data un argument commercial."
        ),
    ),
]

LEVELS_BY_CODE = {lvl.code: lvl for lvl in LEVELS}


def level_for(percentage: float) -> MaturityLevel:
    """Retourne le niveau de maturité correspondant à un pourcentage global."""
    pct = max(0.0, min(100.0, float(percentage)))
    for lvl in LEVELS:
        if lvl.min_pct <= pct < lvl.max_pct:
            return lvl
    return LEVELS[-1]


def level_by_code(code: str) -> Optional[MaturityLevel]:
    return LEVELS_BY_CODE.get(code)


# Niveau attendu par critère selon la cible de progression retenue :
# on considère qu'un critère est "à traiter" tant qu'il n'atteint pas le niveau 2.
TARGET_LEVEL = 2
