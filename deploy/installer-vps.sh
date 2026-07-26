#!/usr/bin/env bash
# =============================================================================
#  DataMaturity Pro — installation complète sur un serveur Ubuntu 22.04 ou 24.04
#
#  Utilisation, depuis le serveur, en root :
#      curl -fsSL https://raw.githubusercontent.com/VOTRE-COMPTE/datamaturity-pro/main/deploy/installer-vps.sh -o installer.sh
#      bash installer.sh https://github.com/VOTRE-COMPTE/datamaturity-pro.git datamaturity.pro votre@email.com
#
#  Ou, si le code est déjà sur le serveur :
#      bash deploy/installer-vps.sh "" datamaturity.pro votre@email.com
#
#  Le script installe Docker, génère les secrets, démarre l'application et la
#  base PostgreSQL, configure Nginx et le certificat TLS, puis planifie la
#  sauvegarde quotidienne. Il est idempotent : le relancer ne casse rien.
# =============================================================================
set -euo pipefail

DEPOT="${1:-}"
DOMAINE="${2:-}"
EMAIL="${3:-}"
CIBLE="/opt/datamaturity"

rouge()  { printf '\033[0;31m%s\033[0m\n' "$*"; }
vert()   { printf '\033[0;32m%s\033[0m\n' "$*"; }
etape()  { printf '\n\033[1;34m▸ %s\033[0m\n' "$*"; }

[[ $EUID -eq 0 ]] || { rouge "Ce script doit être lancé en root (sudo bash ...)."; exit 1; }
[[ -n "$DOMAINE" ]] || { rouge "Usage : bash installer-vps.sh <url-depot-git|\"\"> <domaine> <email>"; exit 1; }

# --------------------------------------------------------------------------
etape "1/7 — Mise à jour du système et outils de base"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl git ufw nginx sqlite3 >/dev/null

# --------------------------------------------------------------------------
etape "2/7 — Installation de Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh >/dev/null
    vert "Docker installé."
else
    vert "Docker déjà présent."
fi

# --------------------------------------------------------------------------
etape "3/7 — Récupération du code"
mkdir -p "$CIBLE"
if [[ -n "$DEPOT" ]]; then
    if [[ -d "$CIBLE/.git" ]]; then
        git -C "$CIBLE" pull --ff-only
    else
        git clone --depth 1 "$DEPOT" "$CIBLE"
    fi
elif [[ ! -f "$CIBLE/docker-compose.yml" ]]; then
    # Code présent dans le répertoire courant : on le copie
    cp -r "$(dirname "$(dirname "$(readlink -f "$0")")")/." "$CIBLE/"
fi
cd "$CIBLE"

# --------------------------------------------------------------------------
etape "4/7 — Génération des secrets et du fichier .env"
if [[ -f .env ]]; then
    vert "Fichier .env existant conservé (les secrets ne sont pas régénérés)."
else
    SECRET=$(openssl rand -hex 32)
    ADMIN_PWD=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)
    PG_PWD=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)

    cat > .env <<ENVFILE
APP_ENV=production
SECRET_KEY=$SECRET
BASE_URL=https://$DOMAINE
DEFAULT_CURRENCY=XOF

ADMIN_USERNAME=admin
ADMIN_PASSWORD=$ADMIN_PWD
ADMIN_EMAIL=$EMAIL

BRAND_NAME=DataMaturity Pro
BRAND_OWNER=Yves Mouaha Handy
CONTACT_EMAIL=$EMAIL
CONTACT_PHONE=+225 07 48 78 25 17
CONTACT_WHATSAPP=2250748782517

FX_EUR_TO_XOF=655.957
FX_USD_TO_XOF=610.0

ENABLE_PUBLIC_BENCHMARK=true
MIN_BENCHMARK_SAMPLE=3

POSTGRES_PASSWORD=$PG_PWD

# Paiements — à renseigner quand les comptes seront ouverts
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
CINETPAY_API_KEY=
CINETPAY_SITE_ID=
CINETPAY_SECRET_KEY=
CINETPAY_MODE=PRODUCTION
ENVFILE
    chmod 600 .env
    printf '%s\n' "$ADMIN_PWD" > /root/mot-de-passe-admin.txt
    chmod 600 /root/mot-de-passe-admin.txt
    vert "Secrets générés. Mot de passe admin écrit dans /root/mot-de-passe-admin.txt"
fi

# --------------------------------------------------------------------------
etape "5/7 — Démarrage de l'application"
docker compose up -d --build
sleep 12
if curl -fsS http://127.0.0.1:8000/healthz >/dev/null; then
    vert "Application démarrée et sonde de santé positive."
else
    rouge "L'application ne répond pas encore. Journaux : docker compose logs --tail 50 web"
fi

# --------------------------------------------------------------------------
etape "6/7 — Nginx, pare-feu et certificat TLS"
sed "s/datamaturity\.pro/$DOMAINE/g" deploy/nginx.conf > /etc/nginx/sites-available/datamaturity
ln -sf /etc/nginx/sites-available/datamaturity /etc/nginx/sites-enabled/datamaturity
rm -f /etc/nginx/sites-enabled/default

# Configuration temporaire en HTTP seul, le temps d'obtenir le certificat
cat > /etc/nginx/sites-available/datamaturity-temp <<NGINXTEMP
server {
    listen 80;
    server_name $DOMAINE www.$DOMAINE;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINXTEMP
ln -sf /etc/nginx/sites-available/datamaturity-temp /etc/nginx/sites-enabled/datamaturity
rm -f /etc/nginx/sites-enabled/datamaturity-temp
nginx -t && systemctl reload nginx

ufw allow 22/tcp >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
vert "Pare-feu actif : ports 22, 80 et 443 ouverts."

apt-get install -y -qq certbot python3-certbot-nginx >/dev/null
if certbot --nginx -d "$DOMAINE" -d "www.$DOMAINE" --non-interactive --agree-tos -m "$EMAIL" --redirect; then
    vert "Certificat TLS installé et renouvellement automatique en place."
else
    rouge "Certbot a échoué. Vérifiez que le DNS de $DOMAINE pointe bien vers ce serveur, puis relancez :"
    rouge "  certbot --nginx -d $DOMAINE -d www.$DOMAINE -m $EMAIL --agree-tos --redirect"
fi

# --------------------------------------------------------------------------
etape "7/7 — Sauvegarde quotidienne"
chmod +x deploy/sauvegarde.sh
CRON="0 2 * * * cd $CIBLE && docker compose exec -T db pg_dump -U datamaturity datamaturity | gzip > /var/backups/datamaturity-\$(date +\\%Y\\%m\\%d).sql.gz && find /var/backups -name 'datamaturity-*.sql.gz' -mtime +30 -delete"
mkdir -p /var/backups
( crontab -l 2>/dev/null | grep -v 'datamaturity' ; echo "$CRON" ) | crontab -
vert "Sauvegarde planifiée chaque nuit à 2 h, conservation 30 jours."

# --------------------------------------------------------------------------
printf '\n'
vert "═══════════════════════════════════════════════════════════"
vert " Déploiement terminé"
vert "═══════════════════════════════════════════════════════════"
echo " Site public   : https://$DOMAINE"
echo " Pilotage      : https://$DOMAINE/admin"
echo " Identifiant   : admin"
echo " Mot de passe  : $(cat /root/mot-de-passe-admin.txt 2>/dev/null || echo 'voir /opt/datamaturity/.env')"
printf '\n'
echo " Étapes suivantes :"
echo "   1. Se connecter à /admin et changer le mot de passe depuis /admin/compte"
echo "   2. Renseigner les clés Stripe et CinetPay dans $CIBLE/.env"
echo "   3. Relancer : cd $CIBLE && docker compose up -d"
echo "   4. Vérifier : bash deploy/verifier-deploiement.sh https://$DOMAINE"
printf '\n'
