"""Tarification multi-devises : conversion, formatage et unités mineures."""

from decimal import Decimal

import pytest

from app.services.pricing import (
    SUPPORTED_CURRENCIES,
    convert,
    currency_for_country,
    format_amount,
    normalise_currency,
    price_for,
)


def test_devises_supportees():
    assert SUPPORTED_CURRENCIES == ["XOF", "EUR", "USD"]


def test_formatage_par_devise():
    assert format_amount(49000, "XOF") == "49 000 FCFA"
    assert format_amount(Decimal("74.99"), "EUR") == "74,99 €"
    assert format_amount(Decimal("79.99"), "USD") == "$79.99"
    assert format_amount(2500000, "XOF") == "2 500 000 FCFA"


def test_offre_gratuite_reste_gratuite():
    for code in SUPPORTED_CURRENCIES:
        price = price_for("free", code)
        assert price.is_free
        assert price.minor_units == 0


def test_conversion_et_arrondi_commercial():
    # 49 000 FCFA / 655,957 = 74,70 EUR -> arrondi au multiple de 5 moins un centime
    assert convert(49000, "EUR", {"EUR": 655.957}) == Decimal("74.99")
    assert convert(49000, "XOF") == Decimal(49000)


def test_unites_mineures_pour_les_api_de_paiement():
    euro = price_for("standard", "EUR")
    assert euro.minor_units == int(euro.amount * 100)
    franc = price_for("standard", "XOF")
    assert franc.minor_units == int(franc.amount)  # le XOF n'a pas de sous-unité


def test_devise_par_defaut_selon_le_pays():
    assert currency_for_country("Côte d'Ivoire") == "XOF"
    assert currency_for_country("Sénégal") == "XOF"
    assert currency_for_country("France") == "EUR"
    assert currency_for_country("Nigeria") == "USD"
    assert currency_for_country("Pays inconnu") == "XOF"


@pytest.mark.parametrize("value,expected", [("eur", "EUR"), ("xof", "XOF"), ("gbp", "XOF"), (None, "XOF")])
def test_normalisation_des_codes(value, expected):
    assert normalise_currency(value) == expected


def test_surcharge_des_tarifs_en_base():
    from app.database import session_scope
    from app.services.pricing import PRICE_OVERRIDE_KEY, get_plan_prices_xof
    from app.services.settings_store import set_setting

    with session_scope() as session:
        set_setting(session, PRICE_OVERRIDE_KEY, {"standard": {"EUR": 89.0}})
        assert price_for("standard", "EUR", session=session).amount == Decimal("89.0")
        assert get_plan_prices_xof(session)["standard"] > 0
        set_setting(session, PRICE_OVERRIDE_KEY, {})
