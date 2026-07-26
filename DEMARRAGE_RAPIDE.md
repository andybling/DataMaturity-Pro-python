# Démarrage rapide — 5 minutes

## 1. Installer

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurer

```bash
cp .env.example .env
```

Deux valeurs suffisent pour démarrer en local :

```ini
SECRET_KEY=collez-ici-une-chaine-aleatoire-longue
ADMIN_PASSWORD=votre-mot-de-passe-admin
```

Générer une clé : `python -c "import secrets; print(secrets.token_hex(32))"`

## 3. Lancer

```bash
python run.py
```

| Adresse | Contenu |
|---|---|
| http://localhost:8000 | Site public |
| http://localhost:8000/diagnostic | Questionnaire |
| http://localhost:8000/admin | Console de pilotage |
| http://localhost:8000/api/docs | Documentation de l'API |

## 4. Voir la console remplie

```bash
python scripts/seed_demo.py --nombre 40
```

Crée 40 organisations fictives dont environ 9 clientes payantes, pour voir les
indicateurs, les courbes et le baromètre en situation.
Ne jamais exécuter sur une base contenant de vrais prospects.

## 5. Tester un achat de bout en bout

1. Réaliser un diagnostic complet, jusqu'à la page de résultats.
2. Cliquer « Débloquer le rapport détaillé », choisir Premium.
3. Laisser la devise sur FCFA et le moyen « Virement bancaire ».
4. Noter la référence de commande affichée.
5. Dans `/admin/commandes`, cliquer **Valider** sur cette commande.
6. Revenir sur `/acces` et saisir le code d'accès : le rapport complet s'ouvre.

Ce circuit fonctionne sans aucune clé de paiement et convient pour les
premières ventes réelles.

## 6. Activer les paiements en ligne

Renseigner dans `.env` :

```ini
STRIPE_SECRET_KEY=sk_live_...          # carte bancaire, EUR et USD
STRIPE_WEBHOOK_SECRET=whsec_...
CINETPAY_API_KEY=...                   # Mobile Money, FCFA
CINETPAY_SITE_ID=...
CINETPAY_SECRET_KEY=...
BASE_URL=https://votre-domaine
```

Puis déclarer les URLs de notification :

- Stripe → `https://votre-domaine/paiement/webhook/stripe`
- CinetPay → `https://votre-domaine/paiement/webhook/cinetpay`

## 7. Vérifier avant mise en ligne

```bash
pytest
```

69 tests doivent passer. Consulter ensuite la liste de contrôle de mise en
production dans `README.md`, section 8.
