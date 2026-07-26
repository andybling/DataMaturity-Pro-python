"""Tarification multi-devises : FCFA (XOF), euro (EUR) et dollar américain (USD).

Principe retenu
---------------
Le FCFA est la devise de référence : tous les tarifs sont définis en XOF et
convertis à l'affichage. Les montants convertis sont arrondis à un prix
« commercial » (terminaison en 9) pour éviter d'afficher des montants issus
d'une division.

Les taux de change et les tarifs sont surchargeables à chaud depuis la console
d'administration (table `settings`), sans redéploiement.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings

# ---------------------------------------------------------------------------
#  Devises
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Currency:
    code: str
    name: str
    symbol: str
    decimals: int
    symbol_before: bool
    thousands_sep: str
    decimal_sep: str
    minor_units: int  # nombre d'unités mineures pour 1 unité (100 pour EUR, 1 pour XOF)


CURRENCIES: Dict[str, Currency] = {
    "XOF": Currency("XOF", "Franc CFA (UEMOA)", "FCFA", 0, False, " ", ",", 1),
    "EUR": Currency("EUR", "Euro", "€", 2, False, " ", ",", 100),
    "USD": Currency("USD", "Dollar américain", "$", 2, True, ",", ".", 100),
}

DEFAULT_CURRENCY = "XOF"
SUPPORTED_CURRENCIES: List[str] = ["XOF", "EUR", "USD"]

# Devise proposée par défaut selon le pays déclaré.
COUNTRY_CURRENCY: Dict[str, str] = {
    "Côte d'Ivoire": "XOF",
    "Sénégal": "XOF",
    "Bénin": "XOF",
    "Burkina Faso": "XOF",
    "Mali": "XOF",
    "Togo": "XOF",
    "Niger": "XOF",
    "Guinée": "XOF",
    "Cameroun": "XOF",
    "Gabon": "XOF",
    "Congo": "XOF",
    "RD Congo": "USD",
    "Ghana": "USD",
    "Nigeria": "USD",
    "Maroc": "EUR",
    "Tunisie": "EUR",
    "France": "EUR",
    "Belgique": "EUR",
    "Canada": "USD",
}


def normalise_currency(code: Optional[str]) -> str:
    code = (code or "").upper()
    return code if code in CURRENCIES else DEFAULT_CURRENCY


def currency_for_country(country: Optional[str]) -> str:
    return COUNTRY_CURRENCY.get(country or "", DEFAULT_CURRENCY)


# ---------------------------------------------------------------------------
#  Catalogue des offres (tarifs de référence en FCFA)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    tagline: str
    price_xof: int          # 0 = gratuit ; None impossible, -1 = sur devis
    features: List[str]
    excluded: List[str]
    highlight: bool = False
    cta: str = "Choisir cette offre"
    badge: str = ""
    quote_only: bool = False
    recurring: str = ""     # ex. "par an"


PLANS: List[Plan] = [
    Plan(
        code="free",
        name="Diagnostic gratuit",
        tagline="Mesurez votre position en 10 minutes",
        price_xof=0,
        features=[
            "Questionnaire complet : 45 critères, 7 dimensions",
            "Score global sur 768 points et niveau de maturité",
            "Radar de positionnement par dimension",
            "Score détaillé de chacune des 7 dimensions",
            "Synthèse macro : forces et points de vigilance",
            "Export du récapitulatif de vos réponses",
        ],
        excluded=[
            "Analyse critère par critère",
            "Recommandations priorisées",
            "Feuille de route 12 mois",
            "Estimation de la valeur en jeu",
        ],
        cta="Démarrer le diagnostic",
        badge="Sans engagement",
    ),
    Plan(
        code="standard",
        name="Rapport Standard",
        tagline="Le diagnostic complet, prêt à présenter",
        price_xof=49_000,
        features=[
            "Tout le contenu du diagnostic gratuit",
            "Analyse qualitative des 45 critères, un par un",
            "Diagnostic rédigé pour chacune des 7 dimensions",
            "Recommandations priorisées avec indicateur de suivi",
            "Positionnement comparatif sectoriel (baromètre)",
            "Rapport PDF professionnel téléchargeable",
            "Export Excel de la grille complétée",
        ],
        excluded=[
            "Feuille de route trimestrielle 12 mois",
            "Estimation de la valeur en jeu",
            "Session de conseil",
        ],
        highlight=False,
        cta="Débloquer le rapport",
    ),
    Plan(
        code="premium",
        name="Premium + Conseil",
        tagline="Le plan d'action et l'accompagnement",
        price_xof=149_000,
        features=[
            "Tout le contenu du rapport Standard",
            "Feuille de route 12 mois découpée en 4 trimestres",
            "Estimation de la valeur en jeu par dimension",
            "Sélection des quick wins à effort faible",
            "Étapes de mise en oeuvre détaillées par action",
            "Séance de restitution d'une heure avec un expert",
            "Rapport PDF de présentation pour la direction générale",
        ],
        excluded=[],
        highlight=True,
        cta="Choisir Premium",
        badge="Le plus choisi",
    ),
    Plan(
        code="enterprise",
        name="Licence Entreprise",
        tagline="Piloter la maturité data de plusieurs entités",
        price_xof=2_500_000,
        features=[
            "Évaluations illimitées sur toutes vos entités",
            "Tableau de bord consolidé multi-filiales",
            "Comparaison et classement interne des entités",
            "Grille personnalisable selon votre référentiel",
            "Marque blanche et export aux couleurs du groupe",
            "Accompagnement au déploiement et formation des référents",
        ],
        excluded=[],
        cta="Demander une proposition",
        badge="Sur devis",
        quote_only=True,
        recurring="par an",
    ),
]

PLANS_BY_CODE: Dict[str, Plan] = {p.code: p for p in PLANS}
PAID_PLAN_CODES = ["standard", "premium"]


# ---------------------------------------------------------------------------
#  Taux de change et surcharges administrables
# ---------------------------------------------------------------------------

FX_SETTING_KEY = "fx_rates"
PRICE_SETTING_KEY = "plan_prices_xof"
PRICE_OVERRIDE_KEY = "plan_prices_override"


def default_fx_rates() -> Dict[str, float]:
    """Nombre de FCFA pour une unité de la devise."""
    return {
        "XOF": 1.0,
        "EUR": float(settings.fx_eur_to_xof),
        "USD": float(settings.fx_usd_to_xof),
    }


def get_fx_rates(session: Optional[Session] = None) -> Dict[str, float]:
    rates = default_fx_rates()
    if session is None:
        return rates
    from app.services.settings_store import get_setting

    stored = get_setting(session, FX_SETTING_KEY)
    if isinstance(stored, dict):
        for code, value in stored.items():
            code = code.upper()
            if code in CURRENCIES:
                try:
                    rate = float(value)
                except (TypeError, ValueError):
                    continue
                if rate > 0:
                    rates[code] = rate
    rates["XOF"] = 1.0
    return rates


def get_plan_prices_xof(session: Optional[Session] = None) -> Dict[str, int]:
    prices = {p.code: p.price_xof for p in PLANS}
    if session is None:
        return prices
    from app.services.settings_store import get_setting

    stored = get_setting(session, PRICE_SETTING_KEY)
    if isinstance(stored, dict):
        for code, value in stored.items():
            if code in prices:
                try:
                    prices[code] = int(value)
                except (TypeError, ValueError):
                    continue
    return prices


def get_price_overrides(session: Optional[Session] = None) -> Dict[str, Dict[str, float]]:
    """Tarifs fixés manuellement par devise, ex. {"premium": {"EUR": 229.0}}."""
    if session is None:
        return {}
    from app.services.settings_store import get_setting

    stored = get_setting(session, PRICE_OVERRIDE_KEY)
    return stored if isinstance(stored, dict) else {}


# ---------------------------------------------------------------------------
#  Conversion et formatage
# ---------------------------------------------------------------------------


def _commercial_round(amount: Decimal, currency: Currency) -> Decimal:
    """Arrondit vers un prix d'affichage crédible.

    - montant nul : reste nul (offre gratuite) ;
    - XOF : au millier le plus proche, les prix locaux s'exprimant en milliers ;
    - EUR / USD au-dessus de 1 000 : à la centaine la plus proche ;
    - EUR / USD en dessous de 1 000 : au multiple de 5 le plus proche, moins un
      centime, ce qui donne des terminaisons en « ,99 » sans dérive à la hausse.
    """
    if amount <= 0:
        return Decimal(0)
    if currency.code == "XOF":
        thousands = (amount / Decimal(1000)).to_integral_value(rounding=ROUND_HALF_UP)
        return (max(Decimal(1), thousands) * Decimal(1000)).quantize(Decimal("1"))
    if amount >= Decimal(1000):
        hundreds = (amount / Decimal(100)).to_integral_value(rounding=ROUND_HALF_UP)
        return (hundreds * Decimal(100)).quantize(Decimal("1"))
    fives = (amount / Decimal(5)).to_integral_value(rounding=ROUND_HALF_UP)
    target = max(Decimal(5), fives * Decimal(5))
    return (target - Decimal("0.01")).quantize(Decimal("0.01"))


def format_amount(amount: Decimal | float | int, currency_code: str) -> str:
    """Formate un montant selon les conventions de la devise."""
    cur = CURRENCIES[normalise_currency(currency_code)]
    value = Decimal(str(amount)).quantize(Decimal(1) if cur.decimals == 0 else Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)
    negative = value < 0
    value = abs(value)
    integral, _, frac = f"{value:.{cur.decimals}f}".partition(".")
    grouped = ""
    for index, char in enumerate(reversed(integral)):
        if index and index % 3 == 0:
            grouped = cur.thousands_sep + grouped
        grouped = char + grouped
    text = grouped + (cur.decimal_sep + frac if cur.decimals else "")
    if negative:
        text = "-" + text
    return f"{cur.symbol}{text}" if cur.symbol_before else f"{text} {cur.symbol}"


@dataclass(frozen=True)
class Price:
    """Montant prêt à afficher et prêt à encaisser."""

    currency: str
    amount: Decimal
    amount_xof: int
    formatted: str
    minor_units: int  # montant en plus petite unité, pour les API de paiement

    @property
    def is_free(self) -> bool:
        return self.amount == 0


def convert(amount_xof: int, currency_code: str, rates: Optional[Dict[str, float]] = None) -> Decimal:
    """Convertit un montant en FCFA vers la devise cible, avec arrondi commercial."""
    code = normalise_currency(currency_code)
    cur = CURRENCIES[code]
    if code == "XOF":
        return Decimal(int(amount_xof))
    rates = rates or default_fx_rates()
    rate = Decimal(str(rates.get(code, default_fx_rates()[code])))
    raw = Decimal(int(amount_xof)) / rate
    return _commercial_round(raw, cur)


def price_for(
    plan_code: str,
    currency_code: str,
    *,
    session: Optional[Session] = None,
) -> Price:
    """Tarif d'une offre dans une devise, en tenant compte des surcharges admin."""
    code = normalise_currency(currency_code)
    cur = CURRENCIES[code]
    prices_xof = get_plan_prices_xof(session)
    amount_xof = int(prices_xof.get(plan_code, 0))
    overrides = get_price_overrides(session)

    forced = overrides.get(plan_code, {}).get(code)
    if forced is not None:
        amount = Decimal(str(forced))
    else:
        amount = convert(amount_xof, code, get_fx_rates(session))

    minor = int((amount * Decimal(cur.minor_units)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return Price(
        currency=code,
        amount=amount,
        amount_xof=amount_xof,
        formatted=format_amount(amount, code),
        minor_units=minor,
    )


def all_prices(plan_code: str, *, session: Optional[Session] = None) -> Dict[str, Price]:
    return {code: price_for(plan_code, code, session=session) for code in SUPPORTED_CURRENCIES}


@dataclass
class PlanView:
    """Offre enrichie de son tarif, telle qu'affichée dans les gabarits."""

    plan: Plan
    price: Price
    all_prices: Dict[str, Price]

    @property
    def code(self) -> str:
        return self.plan.code

    @property
    def price_label(self) -> str:
        if self.plan.quote_only:
            return "Sur devis"
        if self.price.is_free:
            return "Gratuit"
        suffix = f" {self.plan.recurring}" if self.plan.recurring else ""
        return f"{self.price.formatted}{suffix}"

    @property
    def secondary_prices(self) -> List[str]:
        """Les deux autres devises, pour affichage sous le prix principal."""
        return [
            p.formatted
            for code, p in self.all_prices.items()
            if code != self.price.currency and not p.is_free
        ]


def plan_views(currency_code: str, *, session: Optional[Session] = None,
               codes: Optional[List[str]] = None) -> List[PlanView]:
    selected = [PLANS_BY_CODE[c] for c in codes] if codes else PLANS
    return [
        PlanView(
            plan=plan,
            price=price_for(plan.code, currency_code, session=session),
            all_prices=all_prices(plan.code, session=session),
        )
        for plan in selected
    ]


def format_xof(amount: int | float) -> str:
    return format_amount(Decimal(str(int(amount))), "XOF")
