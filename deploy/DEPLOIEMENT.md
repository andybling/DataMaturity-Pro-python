# Mise en ligne de DataMaturity Pro

Trois chemins sont préparés. Le premier ne demande aucune ligne de commande
serveur, le troisième donne le contrôle total. Comptez 20 à 40 minutes.

Les secrets de production sont déjà générés dans `.env.production` à la racine
du projet. Ce fichier est ignoré par Git : il ne partira jamais dans votre dépôt.

---

## Étape commune — publier le code sur GitHub

Depuis le dossier du projet, sur votre machine :

```bash
cd datamaturity-pro
git init
git add .
git commit -m "DataMaturity Pro — version initiale"
git branch -M main
```

Créer un dépôt vide sur GitHub, nommé `datamaturity-pro`, **en privé**, puis :

```bash
git remote add origin https://github.com/VOTRE-COMPTE/datamaturity-pro.git
git push -u origin main
```

Vérifier avant de pousser que `.env` et `.env.production` n'apparaissent pas :

```bash
git status --short          # ne doit lister ni .env ni .env.production
```

Si l'un des deux apparaît, arrêter et corriger : `.gitignore` doit être présent
à la racine avant le premier `git add`.

---

## Chemin A — Render (le plus simple)

Render lit le fichier `render.yaml` du dépôt et crée tout seul la base
PostgreSQL et le service web.

1. Créer un compte sur render.com et connecter votre compte GitHub.
2. **New** → **Blueprint** → sélectionner le dépôt `datamaturity-pro`.
3. Render détecte `render.yaml` et propose la création de deux ressources :
   la base `datamaturity-db` et le service `datamaturity-pro`. Confirmer.
4. Render demande les variables marquées à saisir manuellement :

   | Variable | Valeur |
   |---|---|
   | `ADMIN_PASSWORD` | celle de `.env.production` |
   | `BASE_URL` | `https://datamaturity-pro.onrender.com` pour commencer |
   | Clés Stripe et CinetPay | laisser vides pour l'instant |

   `SECRET_KEY` est générée automatiquement par Render — ne rien saisir.
5. Attendre la fin du déploiement (5 à 8 minutes au premier build).
6. Vérifier :

   ```bash
   bash deploy/verifier-deploiement.sh https://datamaturity-pro.onrender.com
   ```

**Coûts.** Le plan gratuit convient pour tester, avec deux limites à connaître :
le service web s'endort après 15 minutes d'inactivité — le premier visiteur
attend alors une trentaine de secondes — et la base PostgreSQL gratuite est
supprimée à l'expiration de sa période d'essai. Pour un usage commercial, le
service web Starter est à 7 USD par mois et la plus petite base payante à
6 USD par mois, soit environ 13 USD. Vérifiez les montants en vigueur sur la
page de tarification de Render avant de vous engager.

**Note importante sur la base gratuite** : ne l'utilisez pas pour de vrais
prospects. Passez sur une base payante dès la première évaluation réelle,
sinon vos données seront perdues à l'expiration.

---

## Chemin B — Railway

1. Créer un compte sur railway.app et connecter GitHub.
2. **New Project** → **Deploy from GitHub repo** → `datamaturity-pro`.
3. Dans le projet, **New** → **Database** → **Add PostgreSQL**.
   Railway crée la variable `DATABASE_URL` et la relie au service web.
4. Onglet **Variables** du service web : coller le contenu de
   `.env.production`, en retirant les lignes `DATABASE_URL` et
   `POSTGRES_PASSWORD`.
5. Onglet **Settings** → **Networking** → **Generate Domain**. Reporter
   l'adresse obtenue dans la variable `BASE_URL`, puis redéployer.
6. Vérifier :

   ```bash
   bash deploy/verifier-deploiement.sh https://votre-projet.up.railway.app
   ```

**Coûts.** Le plan Hobby est à 5 USD par mois, incluant 5 USD de consommation.
Application plus base PostgreSQL, cela situe la facture réelle entre 6 et
12 USD par mois selon le trafic, la facturation se faisant à l'usage.

---

## Chemin C — VPS avec Docker Compose (contrôle total)

C'est le chemin que je recommande dès que vous avez de vrais clients : coût
fixe, données là où vous décidez, aucune dépendance à la politique tarifaire
d'une plateforme.

### 1. Commander le serveur

Une machine 2 vCPU / 4 Go de RAM / 40 Go de disque suffit largement — le
produit est léger. Hetzner (Allemagne, environ 5 EUR par mois) ou un hébergeur
ivoirien si vous souhaitez que les données restent en Côte d'Ivoire. Choisir
**Ubuntu 24.04**.

### 2. Faire pointer le domaine

Chez votre registrar, créer deux enregistrements DNS :

| Type | Nom | Valeur |
|---|---|---|
| A | `@` | l'adresse IP du serveur |
| A | `www` | l'adresse IP du serveur |

Attendre la propagation, puis vérifier depuis votre machine :

```bash
dig +short datamaturity.pro          # doit retourner l'IP du serveur
```

Ne pas lancer l'installation avant que cette commande réponde : le certificat
TLS échouerait.

### 3. Lancer l'installation

En SSH sur le serveur, en root :

```bash
curl -fsSL https://raw.githubusercontent.com/VOTRE-COMPTE/datamaturity-pro/main/deploy/installer-vps.sh -o installer.sh
bash installer.sh https://github.com/VOTRE-COMPTE/datamaturity-pro.git datamaturity.pro yvesmouaha@yahoo.fr
```

> Dépôt privé : le `curl` et le `git clone` demanderont une authentification.
> Le plus simple est de créer un jeton d'accès personnel GitHub et d'utiliser
> `https://VOTRE-COMPTE:LE_JETON@github.com/VOTRE-COMPTE/datamaturity-pro.git`.
> Ce jeton reste sur le serveur, dans la configuration Git du dépôt cloné.

Le script enchaîne : mise à jour du système, installation de Docker, clonage du
code, génération des secrets, démarrage de l'application et de PostgreSQL,
configuration de Nginx, obtention du certificat TLS, activation du pare-feu et
planification de la sauvegarde quotidienne. Il est idempotent : le relancer ne
casse rien et ne régénère pas les secrets existants.

À la fin, il affiche l'adresse du site et le mot de passe administrateur, également
écrit dans `/root/mot-de-passe-admin.txt`.

### 4. Vérifier

```bash
bash /opt/datamaturity/deploy/verifier-deploiement.sh https://datamaturity.pro
```

### Commandes d'exploitation courantes

```bash
cd /opt/datamaturity

docker compose logs -f web            # suivre les journaux
docker compose restart web            # redémarrer après un changement de .env
docker compose up -d --build          # appliquer une mise à jour du code
git pull && docker compose up -d --build   # déployer une nouvelle version

# Sauvegarde manuelle immédiate
docker compose exec -T db pg_dump -U datamaturity datamaturity | gzip > sauvegarde.sql.gz

# Restauration
gunzip -c sauvegarde.sql.gz | docker compose exec -T db psql -U datamaturity datamaturity
```

**Coûts.** 5 à 10 USD par mois pour le serveur, environ 12 USD par an pour le
domaine. Pas d'autre frais.

---

## Après la mise en ligne, dans cet ordre

### 1. Sécuriser le compte administrateur

Se connecter sur `/admin`, aller dans **Mon compte**, changer le mot de passe.
Modifier `ADMIN_PASSWORD` dans l'environnement ne réinitialise pas un compte
existant : c'est volontaire, pour qu'une variable oubliée dans un historique de
commandes ne donne pas accès à la console.

### 2. Faire un diagnostic réel de bout en bout

Sur le site en ligne, réaliser un diagnostic complet, commander le rapport
Premium en mode virement, valider la commande depuis `/admin/commandes`, puis
ouvrir le rapport et télécharger le PDF. Cela valide toute la chaîne avant le
premier vrai client.

### 3. Ouvrir les comptes de paiement

**CinetPay** (Mobile Money, FCFA) : créer un compte marchand, récupérer
`API_KEY`, `SITE_ID` et `SECRET_KEY`, déclarer l'URL de notification
`https://votre-domaine/paiement/webhook/cinetpay`.

**Stripe** (carte, EUR et USD) : créer un compte, récupérer la clé secrète,
puis créer un endpoint webhook vers
`https://votre-domaine/paiement/webhook/stripe` en s'abonnant à l'événement
`checkout.session.completed`. Stripe fournit alors le `whsec_...` à placer dans
`STRIPE_WEBHOOK_SECRET`.

Renseigner ces valeurs dans l'environnement, redémarrer, et tester d'abord en
mode test côté fournisseur. Tant que ces clés sont vides, le circuit virement et
facture reste actif : vous pouvez vendre sans attendre.

### 4. Ajuster les tarifs et le change

Sur `/admin/tarification`, vérifier le taux dollar du moment et ajuster les prix
si nécessaire. La parité euro/franc CFA est fixe à 655,957 et n'a pas à être
modifiée.

### 5. Vérifier la sauvegarde

Sur VPS, le lendemain de l'installation :

```bash
ls -la /var/backups/          # un fichier datamaturity-AAAAMMJJ.sql.gz doit être présent
```

Sur Render et Railway, activer les sauvegardes automatiques dans les réglages de
la base — ne pas s'en dispenser : la base de prospects est l'actif principal du
produit.

---

## En cas de problème

| Symptôme | Cause probable | Action |
|---|---|---|
| Erreur au démarrage mentionnant `psycopg2` | URL de base non normalisée | L'application corrige `postgres://` automatiquement ; vérifier que `DATABASE_URL` est bien injectée |
| Certbot échoue | DNS non propagé | Vérifier `dig +short votre-domaine`, attendre, relancer certbot |
| Retour de paiement sur une mauvaise adresse | `BASE_URL` incorrecte | Corriger `BASE_URL`, redémarrer |
| Webhook Stripe refusé | `STRIPE_WEBHOOK_SECRET` absent ou erroné | Recopier le `whsec_...` depuis le tableau de bord Stripe |
| Paiement Mobile Money non validé | URL de notification non déclarée | Déclarer l'URL chez CinetPay ; en attendant, valider depuis `/admin/commandes` |
| Page 502 | Application arrêtée | `docker compose logs --tail 80 web` |

Le script `deploy/verifier-deploiement.sh` effectue 21 contrôles et indique
précisément ce qui ne répond pas.
