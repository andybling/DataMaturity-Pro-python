#!/usr/bin/env bash
# =============================================================================
#  Vérification d'un déploiement en ligne.
#  Usage : bash deploy/verifier-deploiement.sh https://datamaturity.pro
#
#  Contrôle les pages publiques, l'API, la protection de la console
#  d'administration, la présence du HTTPS et l'état des paiements.
# =============================================================================
set -uo pipefail

BASE="${1:-http://localhost:8000}"
BASE="${BASE%/}"
OK=0; KO=0

vert()  { printf '\033[0;32m  OK   \033[0m %s\n' "$*"; }
rouge() { printf '\033[0;31m ÉCHEC \033[0m %s\n' "$*"; }
titre() { printf '\n\033[1;34m▸ %s\033[0m\n' "$*"; }

verifier() {
    local chemin="$1" attendu="$2" libelle="$3"
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASE$chemin")
    if [[ "$code" == "$attendu" ]]; then vert "$libelle ($code)"; OK=$((OK+1))
    else rouge "$libelle — attendu $attendu, obtenu $code"; KO=$((KO+1)); fi
}

contient() {
    local chemin="$1" motif="$2" libelle="$3"
    if curl -s --max-time 20 "$BASE$chemin" | grep -q "$motif"; then
        vert "$libelle"; OK=$((OK+1))
    else rouge "$libelle — motif « $motif » absent"; KO=$((KO+1)); fi
}

echo "Vérification de $BASE"

titre "Disponibilité"
verifier "/healthz" 200 "Sonde de santé"
verifier "/" 200 "Page d'accueil"
verifier "/diagnostic" 200 "Formulaire de diagnostic"
verifier "/tarifs" 200 "Page des tarifs"
verifier "/methodologie" 200 "Méthodologie"
verifier "/barometre" 200 "Baromètre public"
verifier "/mentions-legales" 200 "Mentions légales"
verifier "/acces" 200 "Récupération d'accès"
verifier "/page-qui-nexiste-pas" 404 "Page d'erreur 404"

titre "API"
verifier "/api/v1/grid" 200 "Grille exposée"
verifier "/api/v1/pricing" 200 "Tarifs exposés"
verifier "/api/docs" 200 "Documentation interactive"
contient "/api/v1/grid" '"max_score":768' "Score maximum de 768 points"
contient "/api/v1/grid" '"criteria_count":45' "45 critères chargés"

titre "Sécurité"
verifier "/admin" 303 "Console protégée (redirection vers la connexion)"
verifier "/admin/connexion" 200 "Page de connexion accessible"
verifier "/admin/prospects" 303 "Liste des prospects protégée"
verifier "/admin/commandes" 303 "Commandes protégées"

if [[ "$BASE" == https://* ]]; then
    if curl -s -o /dev/null -w '%{http_code}' --max-time 20 "${BASE/https:/http:}" | grep -qE '30[128]'; then
        vert "HTTP redirigé vers HTTPS"; OK=$((OK+1))
    else
        rouge "HTTP n'est pas redirigé vers HTTPS"; KO=$((KO+1))
    fi
else
    printf '\033[0;33m ALERTE \033[0m URL en HTTP : ne pas exploiter en production sans TLS\n'
fi

titre "Tarification affichée"
contient "/tarifs" "FCFA" "Prix en francs CFA"
contient "/tarifs?devise=EUR" "€" "Prix en euros"
contient "/tarifs?devise=USD" '\$' "Prix en dollars"

titre "Résultat"
printf '  %d contrôle(s) réussi(s), %d en échec\n\n' "$OK" "$KO"
if [[ $KO -eq 0 ]]; then
    printf '\033[0;32m  Déploiement conforme. Étapes restantes : changer le mot de passe admin\n'
    printf '  depuis /admin/compte, puis déclarer les webhooks de paiement.\033[0m\n\n'
    exit 0
else
    printf '\033[0;31m  Des contrôles ont échoué. Journaux : docker compose logs --tail 80 web\033[0m\n\n'
    exit 1
fi
