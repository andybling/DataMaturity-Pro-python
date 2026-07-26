#!/usr/bin/env python3
"""Jeu de données de démonstration : peuple la base pour tester le pilotage.

Usage :
    python scripts/seed_demo.py --nombre 40

Les organisations générées sont fictives. À ne jamais exécuter sur une base
de production contenant de vrais prospects.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.grid import ALL_CRITERIA  # noqa: E402
from app.data.reference import (  # noqa: E402
    ACQUISITION_CHANNELS,
    COMPANY_SIZES,
    COUNTRIES,
    SECTORS,
)
from app.database import init_db, session_scope  # noqa: E402
from app.services import assessments as svc  # noqa: E402
from app.services.pricing import currency_for_country  # noqa: E402

PREFIXES = ["Groupe", "Société", "Compagnie", "Entreprise", "Holding", "Agence"]
NAMES = ["Atlantique", "Ivoire", "Sahel", "Lagune", "Baobab", "Ébène", "Kola", "Wouri",
         "Bandama", "Comoé", "Niger", "Sénégal", "Zenith", "Horizon", "Concorde", "Étoile"]
SUFFIXES = ["SA", "SARL", "Holding", "Services", "International", "& Cie"]
FIRST = ["Awa", "Kouadio", "Fatou", "Ibrahim", "Aminata", "Yao", "Mariam", "Sekou",
         "Adjoua", "Moussa", "Nadia", "Cheikh"]
LAST = ["Koné", "Traoré", "Diallo", "N'Guessan", "Bamba", "Ouattara", "Sow", "Cissé"]
ROLES = ["Directeur des systèmes d'information", "Chief Data Officer", "Directeur général",
         "Responsable transformation digitale", "Directeur financier", "Responsable BI"]


def random_answers(bias: float) -> dict:
    """Réponses corrélées à un niveau de maturité cible (bias entre 0 et 1)."""
    out = {}
    for criterion in ALL_CRITERIA:
        base = bias * 3
        value = round(random.gauss(base, 0.75))
        out[criterion.code] = max(0, min(3, value))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère des évaluations de démonstration.")
    parser.add_argument("--nombre", type=int, default=30, help="Nombre d'évaluations à créer")
    parser.add_argument("--taux-conversion", type=float, default=0.22,
                        help="Part des évaluations converties en commande payée")
    args = parser.parse_args()

    init_db()
    random.seed(42)
    created = paid = 0

    with session_scope() as session:
        for index in range(args.nombre):
            country = random.choice(COUNTRIES[:12])
            size = random.choice(COMPANY_SIZES)
            company = f"{random.choice(PREFIXES)} {random.choice(NAMES)} {random.choice(SUFFIXES)}"
            contact = f"{random.choice(FIRST)} {random.choice(LAST)}"
            assessment = svc.create_assessment(
                session,
                {
                    "company_name": company,
                    "sector": random.choice(SECTORS),
                    "country": country,
                    "company_size": size["code"],
                    "contact_name": contact,
                    "contact_role": random.choice(ROLES),
                    "contact_email": f"contact{index}@exemple-demo.ci",
                    "contact_phone": "+225 07 00 00 00",
                    "acquisition_channel": random.choice(ACQUISITION_CHANNELS),
                    "consent": True,
                    "currency": currency_for_country(country),
                },
            )
            # Antidatage pour alimenter les courbes mensuelles
            assessment.created_at = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 165)
            )
            svc.save_answers(session, assessment, random_answers(random.uniform(0.15, 0.9)))
            svc.finalise(session, assessment)
            assessment.completed_at = assessment.created_at + timedelta(minutes=12)
            created += 1

            if random.random() < args.taux_conversion:
                plan = random.choices(["standard", "premium"], weights=[0.4, 0.6])[0]
                order = svc.create_order(
                    session, assessment, plan, assessment.currency, "manual"
                )
                order.created_at = assessment.completed_at
                svc.mark_order_paid(session, order, actor="seed")
                order.paid_at = assessment.completed_at + timedelta(hours=random.randint(1, 72))
                paid += 1

    print(f"{created} évaluations créées, dont {paid} converties en commande payée.")
    print("Console de pilotage : /admin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
