# DataMaturity Pro

Plateforme complète de diagnostic de maturité data, écrite intégralement en Python.
Elle transforme la grille de maturité data de Limpida Consulting (2024) en produit
web monétisable : questionnaire guidé, scoring pondéré, analyse automatique,
rapports PDF et Excel, paiement en FCFA / euro / dollar, et console
d'administration pour le pilotage en production.

**Auteur** : Yves Mouaha Handy · Data & AI Professional
**Contact** : yvesmouaha@yahoo.fr · +225 07 48 78 25 17

---

## Sommaire

1. [Ce que fait le produit](#1-ce-que-fait-le-produit)
2. [Démarrage en trois commandes](#2-démarrage-en-trois-commandes)
3. [Architecture du code](#3-architecture-du-code)
4. [Le modèle de scoring](#4-le-modèle-de-scoring)
5. [Tarification multi-devises](#5-tarification-multi-devises)
6. [Paiements : Stripe et CinetPay](#6-paiements--stripe-et-cinetpay)
7. [Console d'administration](#7-console-dadministration)
8. [Déploiement en production](#8-déploiement-en-production)
9. [API pour intégrateurs](#9-api-pour-intégrateurs)
10. [Tests](#10-tests)
11. [Sécurité et conformité](#11-sécurité-et-conformité)
12. [Feuille de route produit](#12-feuille-de-route-produit)

---

## 1. Ce que fait le produit

### Le parcours client

| Étape | Page | Contenu |
|---|---|---|
| 1 | `/` | Présentation, statistiques réelles, offres dans la devise du visiteur |
| 2 | `/diagnostic` | Formulaire d'identité : organisation, secteur, pays, effectif, contact, consentement |
| 3 | `/diagnostic/{id}/1` à `/7` | Questionnaire en 7 sections, 45 critères, navigation avant-arrière, sauvegarde à chaque étape |
| 4 | `/resultats/{id}` | **Couche gratuite** : score sur 768 points, niveau, radar, détail des 7 dimensions, forces et vigilances |
| 5 | `/paiement/{id}/{offre}` | Choix de la devise et du moyen de paiement |
| 6 | `/resultats/{id}/rapport` | **Couche payante** : analyse des 45 critères, recommandations priorisées, feuille de route 12 mois, valeur en jeu |
| 7 | `/resultats/{id}/rapport.pdf` | Rapport PDF de 10 à 14 pages, prêt à présenter en comité |

### La frontière freemium

Ce qui est gratuit sert à qualifier le prospect : il connaît son score, il voit
que la mesure est rigoureuse, il repart avec un chiffre. Ce qui est payant est
le « comment progresser » : le détail critère par critère, la priorisation
économique, le plan trimestriel. Le mur n'est pas décoratif — la couche gratuite
n'expose **aucune** recommandation opérationnelle, et c'est vérifié par un test
automatisé (`tests/test_flow.py::test_parcours_complet_et_mur_freemium`).

### Ce que le produit vous apporte

Chaque diagnostic terminé alimente une base de prospects qualifiés : identité de
l'organisation, contact nominatif, besoin mesuré objectivement, et un
argumentaire commercial pré-rédigé accessible depuis la fiche du prospect dans
la console d'administration.

---

## 2. Démarrage en trois commandes

```bash
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # renseigner SECRET_KEY et ADMIN_PASSWORD
python run.py
```

- Site public : http://localhost:8000
- Console de pilotage : http://localhost:8000/admin
- Documentation de l'API : http://localhost:8000/api/docs

Aucune base de données à installer : SQLite est créé automatiquement dans `data/`.
Aucune clé de paiement n'est nécessaire pour démarrer — le circuit « virement et
facture » est actif par défaut et pleinement fonctionnel.

Pour remplir la console avec des données de démonstration :

```bash
python scripts/seed_demo.py --nombre 40
```

> À n'exécuter que sur un environnement de test : le script crée des
> organisations fictives.

---

## 3. Architecture du code

```
datamaturity-pro/
├── app/
│   ├── main.py                  Application FastAPI, middlewares, gestion des erreurs
│   ├── config.py                Configuration par variables d'environnement (12-factor)
│   ├── database.py              Moteur SQLAlchemy, sessions, initialisation du schéma
│   ├── models.py                Assessment, Order, Setting, AdminUser, AuditLog
│   ├── security.py              PBKDF2, jetons signés, authentification admin
│   ├── templating.py            Environnement Jinja2, filtres de formatage
│   ├── data/
│   │   ├── grid.py              LA GRILLE — 7 dimensions, 45 critères, 768 points (généré)
│   │   ├── levels.py            Niveaux de maturité et seuils
│   │   ├── recommendations.py   45 recommandations, une par critère
│   │   └── reference.py         Secteurs, pays, tailles, canaux
│   ├── services/
│   │   ├── scoring.py           Moteur de scoring pondéré
│   │   ├── analysis.py          Moteur d'analyse déterministe
│   │   ├── pricing.py           Tarification FCFA / EUR / USD
│   │   ├── payments/            Stripe, CinetPay, circuit manuel
│   │   ├── reports.py           PDF (ReportLab) et Excel (openpyxl)
│   │   ├── benchmark.py         Baromètre et positionnement sectoriel
│   │   ├── kpis.py              Indicateurs de la console
│   │   ├── exports.py           Exports CSV et Excel des prospects
│   │   └── charts.py            Radar SVG, sans JavaScript
│   ├── routers/                 public.py · checkout.py · admin.py · api.py
│   ├── templates/               Gabarits Jinja2 (public + admin)
│   └── static/css/app.css       Feuille de style unique, aucune dépendance externe
├── scripts/                     Génération de la grille, jeu de démonstration
├── tests/                       69 tests pytest
├── deploy/                      Nginx, systemd, script de sauvegarde
├── Dockerfile · docker-compose.yml · Procfile
└── requirements.txt · .env.example
```

### Choix techniques et raisons

**Rendu côté serveur, pas de framework JavaScript.** Le questionnaire fonctionne
sur une connexion 3G, sur un téléphone d'entrée de gamme, sans build front. Le
radar est du SVG généré en Python : il s'imprime et s'exporte tel quel.

**Aucune dépendance externe à l'exécution.** Pas de CDN, pas d'appel d'API pour
produire l'analyse. La plateforme fonctionne dans un intranet bancaire coupé
d'internet, à l'exception des paiements en ligne.

**Analyse déterministe.** À réponses identiques, le rapport est strictement
identique. C'est ce qui le rend défendable devant un comité et vérifiable en
audit — un rapport qui change à chaque génération n'est pas un livrable de
conseil.

**La grille est du code généré.** `app/data/grid.py` est produit depuis le
fichier Excel source par `scripts/generate_grid.py`, avec vérification que les
sous-totaux correspondent exactement (126, 135, 126, 90, 84, 72, 135 = 768).
Si Limpida publie une nouvelle version, on régénère au lieu de retoucher à la main.

---

## 4. Le modèle de scoring

```
score du critère = réponse (0 à 3) × poids du critère × poids de la dimension
```

| Dimension | Poids | Critères | Points max |
|---|---:|---:|---:|
| Gouvernance des données | 3 | 6 | 126 |
| Qualité des données | 3 | 7 | 135 |
| Sécurité des données | 3 | 6 | 126 |
| Intégration des données | 2 | 7 | 90 |
| Analyse des données | 2 | 8 | 84 |
| Culture et compétences | 2 | 5 | 72 |
| Infrastructure des données | 3 | 6 | 135 |
| **Total** | | **45** | **768** |

Niveaux : Débutant (0–25 %), Émergent (25–50 %), Avancé (50–75 %), Leader (75–100 %).

### Comment les recommandations sont priorisées

```
priorité = poids de la dimension × poids du critère × écart au niveau maximum
```

Un critère « très important » dans une dimension « très importante » et noté 0
sort à 27 points de priorité ; le même critère noté 2 sort à 9. Le classement
récompense donc le rendement de l'effort, pas la facilité. Les actions sont
ensuite réparties sur quatre trimestres par quartiles de priorité, avec un
décalage d'un trimestre pour les actions à effort élevé et une avance d'un
trimestre pour celles à effort faible.

### L'estimation de valeur en jeu

```
valeur = CA de référence × exposition de la dimension × écart de maturité
```

Le CA de référence est déduit de la bande d'effectif déclarée. Les taux
d'exposition (0,4 % à 1 % du chiffre d'affaires selon la dimension) sont
volontairement prudents et **écrits en clair dans le rapport**, avec la mention
qu'il s'agit d'un outil de priorisation et non d'un engagement de résultat.
C'est ce qui rend le chiffre discutable avec le client au lieu d'être contesté.

---

## 5. Tarification multi-devises

Le FCFA est la devise de référence. L'euro et le dollar sont calculés par
conversion puis arrondis à un prix commercial : multiple de 5 le plus proche
moins un centime pour les montants inférieurs à 1 000, centaine la plus proche
au-delà. Aucune dérive à la hausse, aucun prix qui ressemble au résultat d'une division.

| Offre | FCFA | Euro | Dollar |
|---|---:|---:|---:|
| Diagnostic gratuit | 0 | 0 | 0 |
| Rapport Standard | 49 000 | 74,99 € | $79.99 |
| Premium + Conseil | 149 000 | 224,99 € | $244.99 |
| Licence Entreprise | 2 500 000 / an | 3 800 € | $4 100 |

La devise proposée par défaut découle du pays déclaré (UEMOA → FCFA, Europe →
euro, Nigeria et Ghana → dollar) ; le visiteur peut la changer à tout moment
depuis le sélecteur présent sur chaque page tarifaire.

**Tout est pilotable depuis `/admin/tarification`**, sans redéploiement :
tarifs de référence en FCFA, taux de change, et prix forcés par devise lorsqu'on
veut un montant précis (par exemple 249 € au lieu du prix converti).

---

## 6. Paiements : Stripe et CinetPay

| Devise | Fournisseur | Moyens |
|---|---|---|
| XOF | CinetPay | Orange Money, MTN, Moov, Wave, carte |
| EUR, USD | Stripe Checkout | Visa, Mastercard |
| Toutes | Circuit manuel | Virement, dépôt Mobile Money, facture |

### Configuration

```bash
# .env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
CINETPAY_API_KEY=...
CINETPAY_SITE_ID=...
CINETPAY_SECRET_KEY=...
```

URLs de notification à déclarer chez les fournisseurs :

- Stripe : `https://votre-domaine/paiement/webhook/stripe` — événement `checkout.session.completed`
- CinetPay : `https://votre-domaine/paiement/webhook/cinetpay`

### Garanties implémentées

- **La signature Stripe est vérifiée** avec `STRIPE_WEBHOOK_SECRET`. Sans secret configuré, le webhook est refusé — jamais accepté par défaut.
- **Les notifications CinetPay ne font pas foi.** Chaque notification déclenche un appel `/v2/payment/check` auprès de CinetPay : seule cette réponse serveur valide le paiement.
- **Le montant est contrôlé.** Un webhook annonçant un montant différent de celui de la commande est rejeté et journalisé en `order.amount_mismatch`.
- **Les webhooks sont idempotents.** Un rejeu ne duplique ni le paiement ni l'accès.
- **La page de retour ne débloque rien par elle-même.** Revenir sur `/paiement/{id}/retour` ne suffit pas : l'état affiché reflète l'état réel de la commande.
- **Sans aucune clé configurée, le produit reste vendable** grâce au circuit manuel, que l'administrateur valide depuis la console. C'est le mode de démarrage recommandé pour les premières ventes.

L'accès au rapport passe par un code d'accès (`DM-XXXXXXXX`) et un jeton signé,
ce qui évite d'imposer la création d'un compte utilisateur.

---

## 7. Console d'administration

Accès : `/admin` — identifiants définis par `ADMIN_USERNAME` et `ADMIN_PASSWORD`.

| Page | Contenu |
|---|---|
| Tableau de bord | Diagnostics, taux d'achèvement, CA total et sur 30 jours, taux de conversion, panier moyen, courbes mensuelles, revenus par devise et par offre, secteurs, canaux d'acquisition |
| Prospects | Liste filtrable (recherche, secteur, pays, niveau, étape commerciale, clients payants), export CSV et Excel du résultat filtré |
| Fiche prospect | Coordonnées, scores par dimension, commandes, étape commerciale, notes internes, **argumentaire commercial généré** avec les 8 actions prioritaires et la valeur en jeu |
| Commandes | Toutes les commandes, encaissé et en attente, **validation manuelle en un clic** pour les virements et factures |
| Tarification | Tarifs en FCFA, taux de change, prix forcés par devise, aperçu client en temps réel |
| Baromètre | Agrégats par secteur, pays et taille, y compris les segments non publiables, avec indication de publiabilité |
| Journal | 300 dernières opérations : connexions, paiements, incohérences de montant, modifications tarifaires |
| Mon compte | Changement de mot de passe, configuration effective de l'instance |

Le premier démarrage crée le compte administrateur depuis les variables
d'environnement. **Modifier ensuite le mot de passe depuis `/admin/compte`** :
changer `ADMIN_PASSWORD` dans `.env` après le premier lancement ne réinitialise
pas le compte existant, par sécurité.

### Le baromètre comme actif

Les données agrégées alimentent deux usages : le positionnement sectoriel vendu
dans le rapport, et un contenu publiable de type « Baromètre de la maturité data
en Afrique de l'Ouest ». Aucun segment n'est publié en dessous de
`MIN_BENCHMARK_SAMPLE` organisations (3 par défaut) afin qu'aucune organisation
ne soit identifiable par recoupement.

---

## 8. Déploiement en production

> **Guide pas à pas** : `deploy/DEPLOIEMENT.md` couvre les trois chemins
> (Render, Railway, VPS) avec les commandes exactes, les coûts réels et la
> procédure post-mise en ligne. Les secrets de production sont déjà générés
> dans `.env.production`, fichier ignoré par Git.
>
> Fichiers fournis : `render.yaml` (Blueprint Render), `railway.json`,
> `deploy/installer-vps.sh` (installation VPS en une commande),
> `deploy/verifier-deploiement.sh` (21 contrôles sur l'instance en ligne).

### Option A — Docker Compose (recommandée)

```bash
cp .env.example .env          # renseigner SECRET_KEY, ADMIN_PASSWORD, clés de paiement
docker compose up -d --build
```

Application sur le port 8000, PostgreSQL 16 avec volume persistant, sonde de
santé sur `/healthz`.

### Option B — VPS avec systemd et Nginx

```bash
sudo mkdir -p /opt/datamaturity && cd /opt/datamaturity
# déposer le code, puis :
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env

sudo cp deploy/datamaturity.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now datamaturity

sudo cp deploy/nginx.conf /etc/nginx/sites-available/datamaturity
sudo ln -s /etc/nginx/sites-available/datamaturity /etc/nginx/sites-enabled/
sudo certbot --nginx -d datamaturity.pro -d www.datamaturity.pro
sudo systemctl reload nginx
```

### Option C — Plateformes managées

Le `Procfile` couvre Railway, Render, Fly.io et Heroku. Variables minimales à
définir : `SECRET_KEY`, `ADMIN_PASSWORD`, `BASE_URL`, `DATABASE_URL`.

### Liste de contrôle avant mise en ligne

- [ ] `SECRET_KEY` aléatoire de 64 caractères (`python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] `ADMIN_PASSWORD` fort, puis modifié depuis `/admin/compte`
- [ ] `APP_ENV=production` — active le cookie de session en HTTPS seul
- [ ] `BASE_URL` = domaine réel, sinon les URLs de retour de paiement seront fausses
- [ ] `DATABASE_URL` vers PostgreSQL (SQLite convient jusqu'à quelques milliers d'évaluations)
- [ ] TLS actif et redirection HTTP → HTTPS
- [ ] Webhooks déclarés chez Stripe et CinetPay, testés en mode test
- [ ] Sauvegarde quotidienne planifiée (`deploy/sauvegarde.sh` en cron)
- [ ] Console `/admin` éventuellement restreinte par IP (bloc commenté dans `deploy/nginx.conf`)
- [ ] Un diagnostic complet effectué de bout en bout sur l'environnement réel

### Coût d'exploitation indicatif

VPS 2 vCPU / 4 Go : 5 à 10 USD par mois. Nom de domaine : environ 12 USD par an.
Commissions de paiement : 2 à 3,5 % selon le fournisseur. Aucun coût d'API
d'intelligence artificielle, l'analyse étant calculée localement.

---

## 9. API pour intégrateurs

Documentation interactive sur `/api/docs`.

| Méthode | Route | Usage |
|---|---|---|
| GET | `/api/v1/grid` | Grille complète : dimensions, critères, poids, libellés des 4 niveaux |
| GET | `/api/v1/levels` | Niveaux de maturité et seuils |
| POST | `/api/v1/score` | Calcul de score et d'analyse **sans persistance** |
| GET | `/api/v1/assessments/{id}` | État d'une évaluation |
| GET | `/api/v1/pricing` | Tarifs des offres dans les trois devises |
| GET | `/api/v1/barometer` | Baromètre agrégé anonymisé |

```bash
curl -X POST https://votre-domaine/api/v1/score \
  -H "Content-Type: application/json" \
  -d '{"answers": {"governance.existence_d_une_politique_de_donnees": 2}, "company_size": "200-999"}'
```

Cette API rend possible l'usage en marque blanche : un groupe bancaire peut
faire évaluer ses filiales depuis son propre intranet et consolider les scores
chez lui — c'est le socle technique de l'offre Licence Entreprise.

---

## 10. Tests

```bash
pytest                 # 69 tests
pytest -v tests/test_scoring.py
```

| Fichier | Couvre |
|---|---|
| `test_grid.py` | Conformité à la grille Limpida : 45 critères, 768 points, sous-totaux, une recommandation par critère |
| `test_scoring.py` | Formule pondérée, bornes, réponses manquantes, seuils de niveau |
| `test_analysis.py` | Déterminisme, priorisation décroissante, couverture de la feuille de route, masquage de la couche gratuite |
| `test_pricing.py` | Conversion, arrondi commercial, unités mineures, devise par pays, surcharges admin |
| `test_flow.py` | Parcours complet, consentement obligatoire, mur freemium, paiement et accès par code |
| `test_admin.py` | Contrôle d'accès sur toutes les pages, exports, modification tarifaire |
| `test_payments.py` | Sélection des fournisseurs, refus des webhooks non signés, idempotence, jetons |
| `test_api.py` | Contrats de l'API JSON |
| `test_reports.py` | Génération PDF et Excel, différence Standard / Premium |

Les tests s'exécutent sur une base SQLite temporaire, sans toucher aux données
de développement.

---

## 11. Sécurité et conformité

**Mots de passe** : PBKDF2-HMAC-SHA256, 260 000 itérations, sel unique par mot
de passe, comparaison à temps constant. Aucune dépendance de chiffrement externe.

**Sessions** : cookies signés, `SameSite=Lax`, `Secure` automatique en production,
durée de 12 heures.

**Accès aux rapports** : jeton HMAC-SHA256 avec expiration, ou code d'accès lié
à une commande payée. Un lien de rapport n'est pas devinable.

**Traçabilité** : chaque connexion, paiement, validation manuelle et modification
tarifaire est journalisée avec acteur, cible et détail.

**Données personnelles** : consentement explicite obligatoire avant le
questionnaire, mention de la loi ivoirienne n°2013-450 du 19 juin 2013 et du
RGPD, page `/mentions-legales` complète, droit de suppression annoncé sous
trente jours. Seules des données professionnelles sont collectées.

**Données bancaires** : aucune n'est stockée ni ne transite par l'application.
Stripe et CinetPay hébergent leurs propres pages de paiement.

À ajouter selon votre exposition : limitation de débit sur `/admin/connexion`
(fail2ban ou `limit_req` Nginx), et jetons anti-CSRF si vous ouvrez la console à
plusieurs administrateurs.

---

## 12. Feuille de route produit

**Court terme.** Envoi automatique des résultats par email (SMTP ou service
transactionnel) ; partage du score sur LinkedIn et WhatsApp depuis la page de
résultats, pour l'effet viral ; relance automatique des diagnostics abandonnés.

**Moyen terme.** Réévaluation comparative à 6 et 12 mois avec courbe de
progression — c'est le levier de revenu récurrent le plus naturel du produit.
Espace multi-entités pour la Licence Entreprise, avec classement interne des
filiales. Version anglaise pour le Nigeria et le Ghana.

**Long terme.** Génération du rapport en marque blanche pour les cabinets de
conseil partenaires. Publication annuelle du baromètre régional, qui transforme
la base accumulée en actif de notoriété. Grille personnalisable pour les
organisations disposant de leur propre référentiel.

---

## Licence et attribution

Grille d'évaluation : **Limpida Consulting — Grille de maturité Data 2024**.
Application, moteur d'analyse, recommandations et rapports :
© Yves Mouaha Handy, 2024-2026. Tous droits réservés.
