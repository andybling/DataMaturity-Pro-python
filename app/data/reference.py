"""Référentiels de saisie : secteurs, pays, tailles, canaux d'acquisition."""

from __future__ import annotations

SECTORS = [
    "Banque & Assurance",
    "Télécommunications",
    "Industrie & Manufacturing",
    "Distribution & Commerce",
    "Agro-industrie",
    "Énergie & Mines",
    "Transport & Logistique",
    "Santé",
    "Éducation & Formation",
    "Administration publique",
    "ONG & Organisation internationale",
    "Technologie & Services numériques",
    "Conseil & Services professionnels",
    "Immobilier & BTP",
    "Autre",
]

COUNTRIES = [
    "Côte d'Ivoire",
    "Sénégal",
    "Bénin",
    "Burkina Faso",
    "Mali",
    "Togo",
    "Niger",
    "Guinée",
    "Cameroun",
    "Gabon",
    "Congo",
    "RD Congo",
    "Ghana",
    "Nigeria",
    "Maroc",
    "Tunisie",
    "France",
    "Belgique",
    "Canada",
    "Autre",
]

# Bandes de taille + proxy de chiffre d'affaires annuel en FCFA,
# utilisées pour l'estimation de ROI (hypothèse documentée dans le rapport).
COMPANY_SIZES = [
    {"code": "1-9", "label": "1 à 9 collaborateurs", "revenue_proxy_xof": 60_000_000},
    {"code": "10-49", "label": "10 à 49 collaborateurs", "revenue_proxy_xof": 400_000_000},
    {"code": "50-199", "label": "50 à 199 collaborateurs", "revenue_proxy_xof": 2_500_000_000},
    {"code": "200-999", "label": "200 à 999 collaborateurs", "revenue_proxy_xof": 12_000_000_000},
    {"code": "1000+", "label": "1 000 collaborateurs et plus", "revenue_proxy_xof": 45_000_000_000},
]

COMPANY_SIZES_BY_CODE = {s["code"]: s for s in COMPANY_SIZES}

REVENUE_BANDS = [
    "Moins de 100 M FCFA",
    "100 M à 1 Md FCFA",
    "1 Md à 10 Md FCFA",
    "Plus de 10 Md FCFA",
    "Non communiqué",
]

ACQUISITION_CHANNELS = [
    "LinkedIn",
    "Recommandation / bouche-à-oreille",
    "Événement professionnel",
    "Email / prospection directe",
    "Recherche Google",
    "WhatsApp",
    "Client existant",
    "Autre",
]

LEAD_STAGES = [
    "nouveau",
    "contacté",
    "qualifié",
    "proposition",
    "gagné",
    "perdu",
]
