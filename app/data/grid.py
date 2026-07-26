"""Grille de maturité Data — Limpida Consulting 2024.

Module généré automatiquement depuis "Grille de maturité Data_Limpida_2024.xlsx".
NE PAS ÉDITER À LA MAIN : régénérer via scripts/generate_grid.py.

Structure : 7 dimensions, 45 critères, score maximum 768 points.
Formule de score : réponse (0-3) x poids_critère x poids_dimension.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Criterion:
    """Un critère d'évaluation, noté de 0 à 3."""

    code: str
    name: str
    weight: int  # 1 = Pas important, 2 = Important, 3 = Très important
    levels: List[str]  # 4 libellés (niveaux 0 à 3)
    dimension_code: str = ""
    dimension_weight: int = 1

    @property
    def max_score(self) -> int:
        return 3 * self.weight * self.dimension_weight

    def score(self, answer: int) -> int:
        return int(answer) * self.weight * self.dimension_weight


@dataclass(frozen=True)
class Dimension:
    """Un thème de la grille regroupant plusieurs critères."""

    code: str
    name: str
    short_name: str
    weight: int
    color: str
    criteria: List[Criterion] = field(default_factory=list)

    @property
    def max_score(self) -> int:
        return sum(c.max_score for c in self.criteria)


def _d(code, name, short, weight, color, criteria):
    crits = [
        Criterion(
            code=f"{code}.{c[0]}",
            name=c[1],
            weight=c[2],
            levels=list(c[3]),
            dimension_code=code,
            dimension_weight=weight,
        )
        for c in criteria
    ]
    return Dimension(code=code, name=name, short_name=short, weight=weight, color=color, criteria=crits)


DIMENSIONS: List[Dimension] = [
    _d(
        'governance',
        'Gouvernance des données',
        'Gouvernance',
        3,
        '#4F46E5',
        [
            (
                'existence_d_une_politique_de_donnees',
                "Existence d'une politique de données",
                3,
                (
                    'Non existante',
                    'Politique documentée mais non officielle ou non approuvée',
                    'Officiellement approuvée et communiquée',
                    'Politique révisée régulièrement, alignée avec les objectifs stratégiques et activement utilisée pour la prise de décision',
                ),
            ),
            (
                'roles_et_responsabilites_definis',
                'Rôles et responsabilités définis',
                2,
                (
                    'Absents',
                    'Rôles identifiés mais pas clairement définis ni communiqués',
                    'Établis et communiqués',
                    'Assignés, respectés et intégrés dans les processus métier',
                ),
            ),
            (
                'cadre_de_gouvernance',
                'Cadre de gouvernance',
                2,
                (
                    'Inexistant',
                    'Informel',
                    'Fonctionnel avec des réunions régulières',
                    "Intégré dans la stratégie d'entreprise",
                ),
            ),
            (
                'formation_et_sensibilisation_a_la_gouver',
                'Formation et sensibilisation à la gouvernance',
                3,
                (
                    'Inexistante',
                    'Ad hoc, souvent réactive',
                    'Programme de formation régulier et proactif',
                    'Continue et sensibilisation à tous les niveaux avec une personnalisation selon les rôles',
                ),
            ),
            (
                'audit_et_conformite_des_donnees',
                'Audit et conformité des données',
                2,
                (
                    'Aucun',
                    'Ad hoc',
                    'Planifié avec des rapports et des suivis',
                    'Intégré avec actions correctives systématiques',
                ),
            ),
            (
                'technologie',
                'Technologie',
                2,
                (
                    'Aucune',
                    'Outils basiques pour la documentation et le suivi (Data Catalogue, dictionnaire de données...)',
                    'Plateforme de gouvernance des données avec des fonctionnalités standards (gestion des politiques de données...) et maintenance externalisée',
                    "Solutions automatisées avec des workflow de validation et maintenance de l'outil internalisée",
                ),
            ),
        ],
    ),
    _d(
        'quality',
        'Qualité des données',
        'Qualité',
        3,
        '#0891B2',
        [
            (
                'politique_de_qualite_des_donnees',
                'Politique de qualité des données',
                3,
                (
                    'Non définie',
                    'Existante mais non appliquée ou sans soutien exécutif',
                    'Formellement établie et communiquée',
                    'Appliquée, révisée régulièrement et alignée avec les objectifs stratégiques',
                ),
            ),
            (
                'mecanismes_de_controle_de_qualite',
                'Mécanismes de contrôle de qualité',
                3,
                (
                    'Inexistants',
                    'Ad hoc et réactifs',
                    'Standardisés avec documentation',
                    'Automatisés et proactifs, intégrés dans les opérations quotidiennes',
                ),
            ),
            (
                'correction_des_donnees',
                'Correction des données',
                2,
                (
                    'Manuelle et sporadique',
                    'Sur demande',
                    'Planifiée et basée sur les résultats des contrôles',
                    'Continue, automatique et basée sur les alertes proactives',
                ),
            ),
            (
                'profilage_des_donnees',
                'Profilage des données',
                1,
                (
                    'Aucun',
                    'Occasionnel',
                    'Régulier avec des outils dédiés',
                    'Intégré dans les processus de gestion des données et analyses continues',
                ),
            ),
            (
                'mesure_de_la_qualite',
                'Mesure de la qualité',
                2,
                (
                    'Aucune',
                    'Mesures de base réalisées sans cohérence',
                    'KPIs de qualité définis et suivis',
                    'Suivi en temps réel de la qualité avec des tableaux de bord dynamiques',
                ),
            ),
            (
                'gestion_des_metadonnees',
                'Gestion des métadonnées',
                2,
                (
                    'Non gérée ou non documentée',
                    'Gestion basique sans standardisation',
                    'Standardisée, documentée et gérée',
                    "Intégrée pleinement dans l'utilisation et la gestion des données",
                ),
            ),
            (
                'technologie',
                'Technologie',
                2,
                (
                    'Aucune',
                    'Outils manuels ou semi-automatisés pour le nettoyage et le contrôle de la qualité',
                    "Plateforme de qualité des données et maintenance de l'outil externalisée",
                    "Plateforme ou système automatisé pour le nettoyage et l'enrichissement des données et maintenance internalisée",
                ),
            ),
        ],
    ),
    _d(
        'security',
        'Sécurité des données',
        'Sécurité',
        3,
        '#DC2626',
        [
            (
                'politiques_de_securite_des_donnees',
                'Politiques de sécurité des données',
                3,
                (
                    'Absentes',
                    'Basiques couvrants quelques aspects essentiels',
                    'Avancées, détaillées et largement communiquées',
                    'Complètes, régulièrement mises à jour et auditables avec une approche "safe by design"',
                ),
            ),
            (
                'gestion_des_acces_et_des_identites',
                'Gestion des accès et des identités',
                3,
                (
                    'Non réglementé, sans contrôles formels',
                    "Gestion manuelle, processus initiaux de contrôle d'accès",
                    'Systématisée avec vérification périodique et documentation avec les rôles et responsabilités définis et communiqués',
                    'Basée sur les rôles, automatisée et intégrée',
                ),
            ),
            (
                'protection_des_donnees',
                'Protection des données',
                3,
                (
                    'Absente',
                    'Essentielle uniquement (antivirus, firewall...)',
                    'Étendue incluant des solutions plus avancées avec documentation',
                    'Complète et cryptage avancé',
                ),
            ),
            (
                'formation_a_la_securite',
                'Formation à la sécurité',
                2,
                (
                    'Aucune',
                    'Sur demande ou ad hoc',
                    'Programme de formation régulier et structuré',
                    "Programme continu de sensibilisation et formation intégrée à la culture de l'entreprise",
                ),
            ),
            (
                'reponse_aux_incidents',
                'Réponse aux incidents',
                2,
                (
                    'Inexistante',
                    'Informelle, sans procédure standard',
                    'Plan formel avec des rôles définis',
                    "Plan de réponse complet avec simulations régulières, revues post-incident et plan d'assurance qualité clairement défini",
                ),
            ),
            (
                'tests_de_penetration',
                'Tests de pénétration',
                1,
                (
                    'Non réalisés',
                    'Ad hoc, sans planification régulière',
                    'Périodiques',
                    'Planifiés et périodiques',
                ),
            ),
        ],
    ),
    _d(
        'integration',
        'Intégration des données',
        'Intégration',
        2,
        '#EA580C',
        [
            (
                'capacite_d_integration_des_systemes',
                "Capacité d'intégration des systèmes",
                2,
                (
                    'Systèmes isolés, sans intégration',
                    'Connexions manuelles',
                    'Semi-automatique',
                    'Intégration fluide et automatisée',
                ),
            ),
            (
                'fiabilite_et_utilite_des_donnees_integre',
                'Fiabilité et utilité des données intégrées',
                3,
                (
                    'Faible, données souvent incohérentes',
                    'Moyenne, données parfois utiles',
                    'Haute, données fiables et utiles',
                    'Excellente',
                ),
            ),
            (
                'normalisation_des_donnees',
                'Normalisation des données',
                2,
                (
                    'Non effectuée, données hétérogènes',
                    'Partielle, certaines données clés normalisées',
                    'Complète pour les données clés, effort de normalisation étendu',
                    'Systématique et exhaustive',
                ),
            ),
            (
                'gestion_des_donnees_non_structurees',
                'Gestion des données non structurées',
                2,
                (
                    'Ignorée',
                    'Basique, gestion élémentaire sans extraction de valeur',
                    'Avancée, extraction de valeur mais pas systématique',
                    'Complète, intégration et valorisation systèmatiques',
                ),
            ),
            (
                'gestion_des_echanges_de_donnees_avec_des',
                'Gestion des échanges de données avec des tiers',
                2,
                (
                    'Non gérée, échanges non sécurisés',
                    'Gérée mais non sécurisée, vulnérabilités présentes',
                    'Sécurisée mais non optimisée',
                    'Sécurisée, optimisée et conforme aux réglementations',
                ),
            ),
            (
                'automatisation_de_l_integration',
                "Automatisation de l'intégration",
                2,
                (
                    'Aucune, intégration entièrement manuelle',
                    'Partielle, certains processus automatisés',
                    'Sur les processus clés',
                    'Automatisation et orchestration complètes',
                ),
            ),
            (
                'technologie',
                'Technologie',
                2,
                (
                    'Aucune',
                    'Outils ETL (Talend, Pentaho...)',
                    'Différents outils ETL/ELT sans gouvernance unifiée',
                    "Plateformes d'intégration des données avec support ETL/ELT (Data Build Tool...)",
                ),
            ),
        ],
    ),
    _d(
        'analytics',
        'Analyse des données',
        'Analyse',
        2,
        '#16A34A',
        [
            (
                'outils_d_analyse',
                "Outils d'analyse",
                2,
                (
                    'Aucun outil disponible',
                    'Basiques et isolés',
                    'Intégrés avec des fonctionnalités avancées',
                    "Plateforme d'analyse unifiée avec IA et ML",
                ),
            ),
            (
                'capacite_d_analyse_en_temps_reel',
                "Capacité d'analyse en temps réel",
                1,
                (
                    'Non disponible',
                    'Disponible pour des cas limités',
                    'Disponible et utilisée largement',
                    'Intégrée dans tous les processus critiques',
                ),
            ),
            (
                'competences_analytiques',
                'Compétences analytiques',
                2,
                (
                    'Absentes',
                    'Basiques',
                    'Avancées en interne',
                    'Reconnues et sollicitées',
                ),
            ),
            (
                'democratisation_des_donnees',
                'Démocratisation des données',
                2,
                (
                    'Données centralisées et inaccessibles',
                    'Accès limité aux données',
                    'Accès démocratisé et facilité aux données',
                    'Culture de self-service analytique établie',
                ),
            ),
            (
                'integration_des_analyses_dans_les_workfl',
                'Intégration des analyses dans les workflows',
                2,
                (
                    'Non intégrée',
                    'Partielle et manuelle',
                    'Automatisée pour certains processus',
                    'Complètement automatisée et optimisée',
                ),
            ),
            (
                'data_storytelling',
                'Data storytelling',
                2,
                (
                    'Absence de narration',
                    'Narration ad hoc',
                    'Intégré dans les analyses',
                    'Avancé pour tous les rapports',
                ),
            ),
            (
                'analyse_predictive_et_prescriptive',
                'Analyse prédictive et prescriptive',
                1,
                (
                    'Non existante',
                    'Expérimentations ponctuelles',
                    'Utilisation régulière pour des décisions stratégiques',
                    'Intégration systématique dans les processus opérationnels',
                ),
            ),
            (
                'technologie',
                'Technologie',
                2,
                (
                    'Aucune',
                    'Tableaux de bord basiques (Excel)',
                    'Plateforme BI avancées (Tableau, Power BI, Qlik...)',
                    "Solution d'analyse avancée avec IA (Knime, Google BigQuery ML...)",
                ),
            ),
        ],
    ),
    _d(
        'culture',
        'Culture et compétences',
        'Culture',
        2,
        '#9333EA',
        [
            (
                'formation_et_sensibilisation_aux_donnees',
                'Formation et sensibilisation aux données',
                3,
                (
                    'Inexistante',
                    'Occasionnelle, sans suivi',
                    'Programme de formation continue avec suvi des progrès',
                    'Apprentissage intégré dans les trajectoires professionnelles avec des parcours personnalisés',
                ),
            ),
            (
                'prise_de_decision_basee_sur_les_donnees',
                'Prise de décision basée sur les données',
                2,
                (
                    'Non utilisée',
                    'Partielle, principalement réactive',
                    'Courante dans de nombreux département',
                    "Systématique et proactive dans toute l'organisation",
                ),
            ),
            (
                'valorisation_des_donnees',
                'Valorisation des données',
                2,
                (
                    'Vue comme un coût',
                    'Vue comme un actif mais sous-utilisées',
                    'Considérée comme un avantage concurrentiel',
                    "Intégrée comme un élément central de la stratégie d'entreprise",
                ),
            ),
            (
                'strategie_de_recrutement_data',
                'Stratégie de recrutement data',
                3,
                (
                    'Pas de recrutement ciblé',
                    'Recrutement ponctuel de profils data',
                    'Équipe data dédiée',
                    'Talent data intégré dans chaque département, recrutement interne et externe continu',
                ),
            ),
            (
                'collaboration_inter_departementale',
                'Collaboration inter-départementale',
                2,
                (
                    'Non existante',
                    'Occasionnelle, souvent silotée',
                    'Structurée avec des processus définis',
                    'Stratégiquement pilotée et optimisée, avec des objectifs communs',
                ),
            ),
        ],
    ),
    _d(
        'infrastructure',
        'Infrastructure des données',
        'Infrastructure',
        3,
        '#0F766E',
        [
            (
                'stockage_des_donnees',
                'Stockage des données',
                2,
                (
                    'Infrastructure non adaptée, dépassée',
                    'Infrastructure avec capacité limitée, problèmes de scalabilité',
                    'Infrastructure évolutive et sécurisée, adaptée à la demande',
                    'Infrastructure agile et scalable, haute disponibilité',
                ),
            ),
            (
                'traitement_des_donnees',
                'Traitement des données',
                3,
                (
                    'Manuel et inefficace',
                    'Automatisation partielle, processus semi-manuels',
                    'Automatisation avancée et intégration des flux de données',
                    'Plateforme intégrée de gestion des flux de données',
                ),
            ),
            (
                'architecture_des_donnees',
                'Architecture des données',
                3,
                (
                    'Non structurée',
                    'Basique avec des silos de données',
                    'Modulaire et flexible',
                    'Orientée services et événementielle',
                ),
            ),
            (
                'securite_de_l_infrastructure',
                "Sécurité de l'infrastructure",
                3,
                (
                    'Négligée, vulnérable aux attaques',
                    'Basique avec quelques contrôles',
                    'Renforcée avec surveillance continue',
                    "Proactive et réactive, utilisation de l'IA pour la détection de menaces",
                ),
            ),
            (
                'interoperabilite_des_plateformes',
                'Interopérabilité des plateformes',
                2,
                (
                    'Isolation des plateformes',
                    'Connexions manuelles entre plateformes',
                    'Connexions automatisées et API',
                    'Écosystème de données intégré et interopérable',
                ),
            ),
            (
                'support_de_gros_volumes_de_donnees',
                'Support de gros volumes de données',
                2,
                (
                    'Incapable',
                    'Limité',
                    'Capable',
                    'Optimisé et facilement scalable',
                ),
            ),
        ],
    ),
]

DIMENSIONS_BY_CODE: Dict[str, Dimension] = {d.code: d for d in DIMENSIONS}

ALL_CRITERIA: List[Criterion] = [c for d in DIMENSIONS for c in d.criteria]

CRITERIA_BY_CODE: Dict[str, Criterion] = {c.code: c for c in ALL_CRITERIA}

MAX_TOTAL_SCORE: int = sum(d.max_score for d in DIMENSIONS)

CRITERIA_COUNT: int = len(ALL_CRITERIA)

WEIGHT_LABELS: Dict[int, str] = {
    1: "Pas important",
    2: "Important",
    3: "Très important",
}

GRID_SOURCE = "Grille de maturité Data — Limpida Consulting 2024"

