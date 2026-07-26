"""Bibliothèque de recommandations, une entrée par critère de la grille.

Chaque entrée est indépendante du niveau constaté : le moteur d'analyse
(app/services/analysis.py) module la priorité, l'horizon et la formulation
en fonction de l'écart entre le niveau déclaré et le niveau cible.

Champs :
    action      — action à mener, formulée à l'impératif
    why         — raison d'être de l'action pour un comité de direction
    steps       — 3 étapes concrètes de mise en oeuvre
    kpi         — indicateur de suivi mesurable
    effort      — faible | moyen | élevé (charge interne estimée)
    roi_driver  — risque | coûts évités | productivité | revenus
"""

from __future__ import annotations

from typing import Dict

R: Dict[str, dict] = {
    # ------------------------------------------------------------------ Gouvernance
    "governance.existence_d_une_politique_de_donnees": {
        "action": "Formaliser et faire approuver une politique de données",
        "why": "Sans texte de référence approuvé par la direction, aucune règle data n'est opposable en interne.",
        "steps": [
            "Rédiger un document de 8 à 12 pages couvrant propriété, classification, cycle de vie et usages autorisés",
            "Le faire valider en comité de direction et le diffuser à l'ensemble des managers",
            "Programmer une revue annuelle inscrite au calendrier de gouvernance",
        ],
        "kpi": "Politique approuvée et taux de managers l'ayant formellement acquittée",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "governance.roles_et_responsabilites_definis": {
        "action": "Nommer des data owners et data stewards par domaine",
        "why": "Une donnée sans propriétaire désigné n'est corrigée par personne et bloque toute démarche qualité.",
        "steps": [
            "Cartographier 5 à 8 domaines de données (client, produit, financier, RH, risque...)",
            "Nommer un data owner métier et un data steward opérationnel par domaine",
            "Inscrire ces responsabilités dans les fiches de poste et les objectifs annuels",
        ],
        "kpi": "Part des domaines de données dotés d'un owner nommé",
        "effort": "faible",
        "roi_driver": "productivité",
    },
    "governance.cadre_de_gouvernance": {
        "action": "Installer un comité data avec un rythme de réunion tenu",
        "why": "La gouvernance ne produit d'effet que par des arbitrages réguliers et tracés.",
        "steps": [
            "Constituer un comité data trimestriel présidé par un membre du comité exécutif",
            "Définir un ordre du jour standard : incidents qualité, arbitrages d'accès, avancement de la feuille de route",
            "Publier un compte rendu et un relevé de décisions après chaque séance",
        ],
        "kpi": "Nombre de comités tenus et de décisions closes par trimestre",
        "effort": "faible",
        "roi_driver": "productivité",
    },
    "governance.formation_et_sensibilisation_a_la_gouver": {
        "action": "Déployer un programme de formation à la gouvernance par population",
        "why": "Les règles ne sont respectées que lorsqu'elles sont comprises dans le contexte de chaque métier.",
        "steps": [
            "Construire trois parcours différenciés : direction, managers, utilisateurs opérationnels",
            "Rendre obligatoire un module d'accueil data pour toute nouvelle recrue",
            "Mesurer la compréhension par un quiz court et un suivi de complétion",
        ],
        "kpi": "Taux de complétion du parcours et score moyen au quiz",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "governance.audit_et_conformite_des_donnees": {
        "action": "Planifier des audits data avec plan d'actions correctives",
        "why": "L'audit transforme les principes en obligations vérifiables et prépare les contrôles externes.",
        "steps": [
            "Établir un plan d'audit annuel couvrant les domaines les plus sensibles",
            "Produire un rapport par audit avec constats hiérarchisés et responsables désignés",
            "Suivre la clôture des actions correctives en comité data",
        ],
        "kpi": "Taux de constats d'audit clos dans les délais",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "governance.technologie": {
        "action": "Outiller la gouvernance par un catalogue de données",
        "why": "Un catalogue rend la donnée trouvable et documente les règles là où les équipes travaillent.",
        "steps": [
            "Choisir une solution adaptée à la taille de l'organisation (open source ou éditeur)",
            "Alimenter le catalogue sur les domaines prioritaires avec propriétaires et définitions",
            "Automatiser les workflows de validation et de demande d'accès",
        ],
        "kpi": "Part des jeux de données critiques catalogués et documentés",
        "effort": "élevé",
        "roi_driver": "productivité",
    },
    # ------------------------------------------------------------------ Qualité
    "quality.politique_de_qualite_des_donnees": {
        "action": "Établir une politique de qualité soutenue par la direction",
        "why": "Sans arbitrage exécutif, la qualité reste un sujet technique sans moyens ni priorité.",
        "steps": [
            "Définir les dimensions de qualité retenues : exactitude, complétude, fraîcheur, unicité, conformité",
            "Fixer des seuils d'acceptation par domaine de données critique",
            "Faire porter la politique par un sponsor du comité exécutif",
        ],
        "kpi": "Nombre de domaines dotés de seuils de qualité formalisés",
        "effort": "faible",
        "roi_driver": "coûts évités",
    },
    "quality.mecanismes_de_controle_de_qualite": {
        "action": "Industrialiser des contrôles qualité automatisés",
        "why": "Un défaut détecté à la source coûte une fraction de ce qu'il coûte détecté par un client.",
        "steps": [
            "Écrire des règles de contrôle sur les 10 tables les plus utilisées",
            "Exécuter ces contrôles à chaque chargement et bloquer les flux non conformes",
            "Router les alertes vers le data steward du domaine concerné",
        ],
        "kpi": "Part des flux critiques couverts par des contrôles automatisés",
        "effort": "moyen",
        "roi_driver": "coûts évités",
    },
    "quality.correction_des_donnees": {
        "action": "Passer d'une correction à la demande à une correction planifiée",
        "why": "La correction réactive consomme du temps expert sans réduire le taux de défauts.",
        "steps": [
            "Prioriser les anomalies par volume et impact métier",
            "Planifier des campagnes de remédiation avec objectifs chiffrés",
            "Traiter la cause racine dans l'application source, pas seulement dans l'entrepôt",
        ],
        "kpi": "Délai moyen de correction et taux de récurrence des anomalies",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "quality.profilage_des_donnees": {
        "action": "Profiler régulièrement les jeux de données clés",
        "why": "Le profilage révèle les dérives silencieuses avant qu'elles n'atteignent les tableaux de bord.",
        "steps": [
            "Outiller un profilage automatique (distributions, taux de nuls, cardinalités)",
            "Comparer les profils dans le temps pour détecter les ruptures",
            "Documenter les anomalies structurelles dans le catalogue",
        ],
        "kpi": "Fréquence de profilage et nombre de dérives détectées en amont",
        "effort": "faible",
        "roi_driver": "coûts évités",
    },
    "quality.mesure_de_la_qualite": {
        "action": "Publier des indicateurs de qualité suivis dans le temps",
        "why": "Ce qui n'est pas mesuré ne progresse pas et ne peut être arbitré en comité.",
        "steps": [
            "Définir 5 à 8 KPI de qualité par domaine critique",
            "Construire un tableau de bord qualité rafraîchi automatiquement",
            "Présenter la trajectoire à chaque comité data",
        ],
        "kpi": "Score de qualité global et sa tendance trimestrielle",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "quality.gestion_des_metadonnees": {
        "action": "Standardiser la gestion des métadonnées",
        "why": "Sans définitions partagées, deux directions produisent deux chiffres différents pour le même indicateur.",
        "steps": [
            "Créer un glossaire métier des 50 indicateurs les plus utilisés",
            "Rattacher chaque indicateur à sa source, sa règle de calcul et son propriétaire",
            "Rendre le glossaire accessible depuis les outils de reporting",
        ],
        "kpi": "Part des indicateurs de pilotage dotés d'une définition unique validée",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "quality.technologie": {
        "action": "Se doter d'une plateforme de qualité des données",
        "why": "L'outillage manuel plafonne dès que le nombre de flux dépasse la capacité des équipes.",
        "steps": [
            "Évaluer les solutions de data quality compatibles avec l'architecture existante",
            "Automatiser nettoyage, dédoublonnage et enrichissement sur les référentiels clés",
            "Internaliser progressivement la maintenance de l'outil",
        ],
        "kpi": "Part des traitements qualité automatisés",
        "effort": "élevé",
        "roi_driver": "coûts évités",
    },
    # ------------------------------------------------------------------ Sécurité
    "security.politiques_de_securite_des_donnees": {
        "action": "Compléter et rendre auditables les politiques de sécurité",
        "why": "Une politique incomplète expose l'organisation en cas de contrôle ou d'incident.",
        "steps": [
            "Couvrir classification, chiffrement, conservation, sous-traitance et transferts",
            "Aligner les textes sur la réglementation applicable (loi ivoirienne n°2013-450, RGPD si UE)",
            "Instaurer une revue annuelle avec traçabilité des versions",
        ],
        "kpi": "Couverture des domaines de sécurité par une politique à jour",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "security.gestion_des_acces_et_des_identites": {
        "action": "Mettre en place une gestion des accès basée sur les rôles",
        "why": "Les accès accumulés au fil des mobilités constituent le premier facteur de fuite de données.",
        "steps": [
            "Définir une matrice rôles/droits par domaine de données",
            "Automatiser l'attribution et la révocation à l'arrivée et au départ",
            "Réaliser une revue des habilitations au moins semestrielle",
        ],
        "kpi": "Taux de comptes revus dans les délais et nombre d'accès orphelins",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "security.protection_des_donnees": {
        "action": "Étendre la protection au chiffrement et à la prévention des fuites",
        "why": "Antivirus et pare-feu ne protègent pas la donnée elle-même une fois extraite du système.",
        "steps": [
            "Chiffrer les données sensibles au repos et en transit",
            "Restreindre et journaliser les extractions massives",
            "Anonymiser ou pseudonymiser les environnements hors production",
        ],
        "kpi": "Part des données sensibles chiffrées et volume d'extractions non justifiées",
        "effort": "élevé",
        "roi_driver": "risque",
    },
    "security.formation_a_la_securite": {
        "action": "Structurer une sensibilisation sécurité continue",
        "why": "La majorité des incidents commence par une action humaine évitable.",
        "steps": [
            "Programmer une session annuelle obligatoire et des rappels trimestriels",
            "Réaliser des campagnes de simulation d'hameçonnage",
            "Communiquer les résultats agrégés pour installer une culture du signalement",
        ],
        "kpi": "Taux de clic aux simulations d'hameçonnage et taux de complétion",
        "effort": "faible",
        "roi_driver": "risque",
    },
    "security.reponse_aux_incidents": {
        "action": "Formaliser et tester un plan de réponse aux incidents",
        "why": "En situation réelle, l'improvisation multiplie la durée d'indisponibilité et l'exposition.",
        "steps": [
            "Documenter procédure, rôles, seuils d'escalade et modèles de communication",
            "Réaliser au moins un exercice de simulation par an",
            "Systématiser une revue post-incident avec actions correctives",
        ],
        "kpi": "Délai moyen de détection et de résolution des incidents",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "security.tests_de_penetration": {
        "action": "Planifier des tests d'intrusion périodiques",
        "why": "Un test annuel identifie des vulnérabilités que les contrôles internes ne voient pas.",
        "steps": [
            "Définir un périmètre annuel priorisé sur les applications exposées",
            "Mandater un prestataire indépendant",
            "Suivre la remédiation des vulnérabilités critiques sous 30 jours",
        ],
        "kpi": "Nombre de vulnérabilités critiques ouvertes au-delà du délai cible",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    # ------------------------------------------------------------------ Intégration
    "integration.capacite_d_integration_des_systemes": {
        "action": "Remplacer les connexions manuelles par des flux automatisés",
        "why": "Chaque transfert manuel est un point de rupture et une source d'écart non traçable.",
        "steps": [
            "Recenser les échanges manuels récurrents entre applications",
            "Automatiser en priorité les flux quotidiens à fort volume",
            "Instrumenter chaque flux avec supervision et alerte en cas d'échec",
        ],
        "kpi": "Part des flux inter-applicatifs automatisés",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "integration.fiabilite_et_utilite_des_donnees_integre": {
        "action": "Fiabiliser les données intégrées par des règles de rapprochement",
        "why": "Des données intégrées mais incohérentes détruisent la confiance dans tout le dispositif décisionnel.",
        "steps": [
            "Mettre en place des rapprochements automatiques source contre destination",
            "Définir un référentiel maître pour les entités partagées (client, produit, tiers)",
            "Publier un indicateur de fiabilité par flux",
        ],
        "kpi": "Taux d'écarts de rapprochement par flux",
        "effort": "moyen",
        "roi_driver": "coûts évités",
    },
    "integration.normalisation_des_donnees": {
        "action": "Normaliser les formats et référentiels des données clés",
        "why": "L'hétérogénéité des formats est la première cause d'échec des projets d'intégration.",
        "steps": [
            "Définir des standards de format (dates, codes pays, identifiants, unités)",
            "Appliquer ces standards dans les couches d'ingestion",
            "Vérifier la conformité par des contrôles automatiques",
        ],
        "kpi": "Part des champs clés conformes aux standards définis",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "integration.gestion_des_donnees_non_structurees": {
        "action": "Exploiter systématiquement les données non structurées",
        "why": "Contrats, courriels et documents concentrent une valeur inexploitée et un risque de conformité.",
        "steps": [
            "Inventorier les gisements documentaires et leur criticité",
            "Industrialiser l'extraction d'information sur les documents à fort volume",
            "Rattacher les documents aux entités métier du référentiel",
        ],
        "kpi": "Volume de documents indexés et taux d'extraction automatique réussie",
        "effort": "élevé",
        "roi_driver": "productivité",
    },
    "integration.gestion_des_echanges_de_donnees_avec_des": {
        "action": "Sécuriser et contractualiser les échanges avec les tiers",
        "why": "Les échanges avec les partenaires sont le maillon le moins contrôlé de la chaîne de données.",
        "steps": [
            "Recenser tous les flux sortants et entrants avec des tiers",
            "Imposer des canaux chiffrés et des accords de traitement de données",
            "Auditer annuellement la conformité des partenaires critiques",
        ],
        "kpi": "Part des flux tiers sous contrat et chiffrés",
        "effort": "moyen",
        "roi_driver": "risque",
    },
    "integration.automatisation_de_l_integration": {
        "action": "Orchestrer les traitements de bout en bout",
        "why": "L'orchestration supprime les reprises manuelles et rend les délais de mise à disposition prévisibles.",
        "steps": [
            "Déployer un ordonnanceur unique pour les chaînes de données",
            "Modéliser les dépendances et les reprises sur incident",
            "Publier un indicateur de ponctualité des livraisons de données",
        ],
        "kpi": "Taux de chaînes livrées à l'heure sans intervention humaine",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "integration.technologie": {
        "action": "Consolider l'outillage d'intégration sous une gouvernance unique",
        "why": "La multiplication d'outils ETL sans règles commune crée une dette d'intégration coûteuse.",
        "steps": [
            "Rationaliser le parc d'outils d'intégration",
            "Standardiser les patterns de développement et la gestion des versions",
            "Documenter chaque pipeline dans le catalogue de données",
        ],
        "kpi": "Nombre d'outils d'intégration en production et part des pipelines documentés",
        "effort": "élevé",
        "roi_driver": "coûts évités",
    },
    # ------------------------------------------------------------------ Analyse
    "analytics.outils_d_analyse": {
        "action": "Unifier les outils d'analyse sur une plateforme partagée",
        "why": "Des outils isolés produisent des chiffres divergents et empêchent la mutualisation des efforts.",
        "steps": [
            "Choisir une plateforme BI de référence pour l'organisation",
            "Migrer les tableaux de bord critiques vers une couche sémantique commune",
            "Décommissionner les reportings redondants",
        ],
        "kpi": "Part des indicateurs de direction produits depuis la plateforme de référence",
        "effort": "élevé",
        "roi_driver": "productivité",
    },
    "analytics.capacite_d_analyse_en_temps_reel": {
        "action": "Ouvrir l'analyse en temps réel sur les processus critiques",
        "why": "Certaines décisions perdent toute valeur si l'information arrive avec un jour de retard.",
        "steps": [
            "Identifier 2 ou 3 processus où la latence a un coût mesurable",
            "Mettre en place une ingestion en continu sur ces périmètres",
            "Associer des alertes opérationnelles aux seuils métier",
        ],
        "kpi": "Latence moyenne entre l'événement et sa disponibilité analytique",
        "effort": "élevé",
        "roi_driver": "revenus",
    },
    "analytics.competences_analytiques": {
        "action": "Élever les compétences analytiques internes",
        "why": "La dépendance à des prestataires externes plafonne la vitesse et le transfert de connaissance.",
        "steps": [
            "Évaluer les compétences existantes et cibler les écarts prioritaires",
            "Former une communauté d'analystes avec des parcours certifiants",
            "Instaurer un mentorat interne et des revues de code analytiques",
        ],
        "kpi": "Nombre d'analystes certifiés et part des analyses réalisées en interne",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "analytics.democratisation_des_donnees": {
        "action": "Ouvrir un accès self-service encadré aux données",
        "why": "Centraliser toutes les demandes sur une équipe crée un goulot d'étranglement structurel.",
        "steps": [
            "Publier des jeux de données certifiés et documentés par domaine",
            "Former les métiers à l'exploration autonome",
            "Encadrer les usages par une gouvernance des accès claire",
        ],
        "kpi": "Nombre d'utilisateurs actifs autonomes et délai moyen des demandes ad hoc",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "analytics.integration_des_analyses_dans_les_workfl": {
        "action": "Intégrer les analyses directement dans les processus métier",
        "why": "Une analyse qui n'est pas branchée sur une action ne produit aucune valeur économique.",
        "steps": [
            "Choisir 3 processus où une recommandation peut déclencher une action",
            "Exposer les résultats dans les outils utilisés par les opérationnels",
            "Mesurer le taux d'adoption et l'effet sur l'indicateur métier",
        ],
        "kpi": "Part des analyses reliées à une action opérationnelle traçable",
        "effort": "moyen",
        "roi_driver": "revenus",
    },
    "analytics.data_storytelling": {
        "action": "Professionnaliser la restitution et la narration des données",
        "why": "Une analyse juste mais mal restituée ne déclenche pas de décision.",
        "steps": [
            "Définir une charte de visualisation et des modèles réutilisables",
            "Former les producteurs de rapports à la narration analytique",
            "Systématiser un message clé et une recommandation par rapport",
        ],
        "kpi": "Part des rapports comportant une recommandation explicite",
        "effort": "faible",
        "roi_driver": "productivité",
    },
    "analytics.analyse_predictive_et_prescriptive": {
        "action": "Passer des expérimentations à un usage régulier du prédictif",
        "why": "Les modèles restés au stade d'expérimentation immobilisent des ressources sans retour.",
        "steps": [
            "Sélectionner 2 cas d'usage à valeur chiffrée (churn, risque, demande, fraude)",
            "Industrialiser le cycle de vie des modèles avec supervision de la dérive",
            "Documenter le gain constaté après six mois d'exploitation",
        ],
        "kpi": "Nombre de modèles en production et gain économique mesuré",
        "effort": "élevé",
        "roi_driver": "revenus",
    },
    "analytics.technologie": {
        "action": "Faire évoluer la plateforme analytique vers les capacités avancées",
        "why": "Un socle limité aux tableurs interdit toute analyse à l'échelle et toute automatisation.",
        "steps": [
            "Établir la cible technologique (entrepôt cloud, couche sémantique, capacités ML)",
            "Migrer par vagues en commençant par un domaine pilote",
            "Suivre le coût par requête et par utilisateur pour maîtriser la facture",
        ],
        "kpi": "Part des usages analytiques servis par la plateforme cible",
        "effort": "élevé",
        "roi_driver": "productivité",
    },
    # ------------------------------------------------------------------ Culture
    "culture.formation_et_sensibilisation_aux_donnees": {
        "action": "Installer un programme de data literacy avec suivi des progrès",
        "why": "Le retour sur investissement des outils data dépend directement du niveau des utilisateurs.",
        "steps": [
            "Définir un socle commun de littératie des données pour tous les managers",
            "Créer des parcours par métier avec évaluation initiale et finale",
            "Inscrire la progression dans les trajectoires professionnelles",
        ],
        "kpi": "Taux de couverture du programme et progression des scores d'évaluation",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "culture.prise_de_decision_basee_sur_les_donnees": {
        "action": "Ancrer la décision fondée sur les données dans les instances",
        "why": "Une décision prise sans donnée dans une instance dirigeante légitime la pratique dans toute l'organisation.",
        "steps": [
            "Imposer un jeu d'indicateurs sourcés dans tout dossier de comité",
            "Documenter les hypothèses et les scénarios chiffrés",
            "Réaliser une revue post-décision comparant prévisions et réalisé",
        ],
        "kpi": "Part des décisions de comité appuyées sur des indicateurs sourcés",
        "effort": "faible",
        "roi_driver": "productivité",
    },
    "culture.valorisation_des_donnees": {
        "action": "Faire reconnaître la donnée comme un actif du bilan opérationnel",
        "why": "Tant que la donnée est vue comme un coût informatique, les budgets restent défensifs.",
        "steps": [
            "Chiffrer la valeur des cas d'usage data existants (gains, risques évités)",
            "Communiquer ces résultats en interne comme des résultats d'entreprise",
            "Rattacher la feuille de route data aux objectifs stratégiques annuels",
        ],
        "kpi": "Valeur cumulée documentée des cas d'usage data",
        "effort": "faible",
        "roi_driver": "revenus",
    },
    "culture.strategie_de_recrutement_data": {
        "action": "Structurer une stratégie de recrutement et de rétention data",
        "why": "Les compétences data sont rares sur le marché régional et se perdent vite sans trajectoire.",
        "steps": [
            "Définir les profils cibles et le modèle d'organisation (centralisé, hybride, embarqué)",
            "Construire un vivier via les écoles et les communautés techniques locales",
            "Mettre en place des parcours d'évolution et une politique de rétention",
        ],
        "kpi": "Délai moyen de recrutement d'un profil data et taux de rotation",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "culture.collaboration_inter_departementale": {
        "action": "Organiser la collaboration data entre directions",
        "why": "Les silos organisationnels se traduisent mécaniquement en silos de données.",
        "steps": [
            "Créer des objectifs partagés entre directions sur les domaines communs",
            "Animer une communauté data transverse à rythme mensuel",
            "Rendre visibles les dépendances de données entre directions",
        ],
        "kpi": "Nombre d'initiatives data portées conjointement par plusieurs directions",
        "effort": "faible",
        "roi_driver": "productivité",
    },
    # ------------------------------------------------------------------ Infrastructure
    "infrastructure.stockage_des_donnees": {
        "action": "Faire évoluer le stockage vers une capacité élastique et sécurisée",
        "why": "Une infrastructure saturée transforme chaque nouveau besoin métier en projet lourd.",
        "steps": [
            "Mesurer la trajectoire de volume et les points de saturation",
            "Choisir une cible évolutive (cloud, hybride) avec politique de conservation",
            "Mettre en place sauvegarde testée et plan de reprise documenté",
        ],
        "kpi": "Marge de capacité disponible et succès des tests de restauration",
        "effort": "élevé",
        "roi_driver": "coûts évités",
    },
    "infrastructure.traitement_des_donnees": {
        "action": "Automatiser les traitements de données de bout en bout",
        "why": "Les traitements manuels sont lents, non reproductibles et dépendants de personnes clés.",
        "steps": [
            "Identifier les traitements manuels récurrents et leur coût en temps",
            "Les convertir en pipelines versionnés et testés",
            "Superviser les exécutions avec alerte et reprise automatique",
        ],
        "kpi": "Part des traitements automatisés et temps humain libéré par mois",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "infrastructure.architecture_des_donnees": {
        "action": "Définir une architecture de données cible modulaire",
        "why": "Sans architecture cible, chaque projet ajoute un silo supplémentaire.",
        "steps": [
            "Formaliser une architecture en couches (ingestion, socle, exposition)",
            "Instaurer une revue d'architecture obligatoire pour tout nouveau projet data",
            "Publier des patterns réutilisables et des standards d'API",
        ],
        "kpi": "Part des nouveaux projets conformes à l'architecture cible",
        "effort": "élevé",
        "roi_driver": "coûts évités",
    },
    "infrastructure.securite_de_l_infrastructure": {
        "action": "Renforcer la sécurité de l'infrastructure et sa supervision",
        "why": "L'infrastructure est la surface d'attaque la plus large et la plus automatisable à protéger.",
        "steps": [
            "Durcir les configurations et appliquer un cycle de correctifs discipliné",
            "Centraliser les journaux et mettre en place une détection continue",
            "Segmenter les réseaux et isoler les environnements sensibles",
        ],
        "kpi": "Délai moyen d'application des correctifs critiques",
        "effort": "élevé",
        "roi_driver": "risque",
    },
    "infrastructure.interoperabilite_des_plateformes": {
        "action": "Généraliser les API et l'interopérabilité entre plateformes",
        "why": "Sans interfaces standardisées, chaque intégration doit être redéveloppée de zéro.",
        "steps": [
            "Exposer les domaines de données via des API documentées et versionnées",
            "Instaurer un catalogue d'API avec règles d'authentification communes",
            "Supprimer progressivement les échanges par fichiers plats",
        ],
        "kpi": "Part des échanges réalisés via API documentées",
        "effort": "moyen",
        "roi_driver": "productivité",
    },
    "infrastructure.support_de_gros_volumes_de_donnees": {
        "action": "Rendre la plateforme capable d'absorber la croissance des volumes",
        "why": "Un socle non scalable transforme la croissance de l'activité en incident technique.",
        "steps": [
            "Réaliser des tests de charge sur les traitements critiques",
            "Optimiser modèles et partitionnement avant d'ajouter de la puissance",
            "Mettre en place un suivi du coût unitaire de traitement",
        ],
        "kpi": "Temps de traitement à volume doublé et coût unitaire par téraoctet",
        "effort": "élevé",
        "roi_driver": "coûts évités",
    },
}

# Part du chiffre d'affaires annuel considérée comme "en jeu" sur chaque dimension.
# Hypothèses prudentes servant uniquement à ordonner les priorités économiques ;
# elles sont explicitées dans le rapport pour rester discutables avec le client.
DIMENSION_VALUE_AT_STAKE: Dict[str, float] = {
    "governance": 0.004,
    "quality": 0.010,
    "security": 0.008,
    "integration": 0.006,
    "analytics": 0.009,
    "culture": 0.004,
    "infrastructure": 0.005,
}

# Lecture qualitative par dimension et par palier de score.
DIMENSION_NARRATIVES: Dict[str, Dict[str, str]] = {
    "governance": {
        "low": "La gouvernance repose sur des initiatives individuelles. Les décisions relatives aux données ne sont ni arbitrées ni tracées, ce qui rend toute démarche qualité ou conformité difficilement défendable devant un auditeur.",
        "mid": "Un cadre de gouvernance existe mais son application est inégale. Les rôles sont connus sans être toujours exercés, et les arbitrages dépendent encore de la disponibilité de quelques personnes.",
        "high": "La gouvernance est installée et produit des arbitrages réguliers. L'enjeu se déplace vers l'automatisation des contrôles et l'alignement continu avec la stratégie.",
    },
    "quality": {
        "low": "La qualité est traitée en réaction aux incidents. Le coût réel se paie en temps de reprise et en perte de confiance dans les chiffres produits.",
        "mid": "Des contrôles existent sur une partie du périmètre. La qualité est mesurée ponctuellement, sans seuils opposables ni suivi systématique de la cause racine.",
        "high": "La qualité est mesurée et pilotée. Les efforts doivent désormais porter sur la détection préventive et la responsabilisation des métiers producteurs.",
    },
    "security": {
        "low": "Le dispositif de sécurité des données est insuffisant au regard des obligations légales et du risque réputationnel. C'est le point qui expose le plus directement la direction générale.",
        "mid": "Les fondamentaux de sécurité sont en place mais la couverture reste partielle, notamment sur la revue des accès et la préparation aux incidents.",
        "high": "La sécurité est structurée et documentée. La priorité devient la vérification indépendante et la réduction du délai de détection.",
    },
    "integration": {
        "low": "Les systèmes fonctionnent en silos, avec des transferts manuels non traçables. Chaque nouveau besoin métier se traduit par un développement spécifique.",
        "mid": "L'intégration progresse sur les flux principaux mais la normalisation et l'orchestration restent incomplètes, ce qui limite la fiabilité des données consolidées.",
        "high": "Les flux sont largement automatisés et fiables. Le gain suivant se situe dans l'exposition par API et la valorisation des données non structurées.",
    },
    "analytics": {
        "low": "Les capacités d'analyse sont limitées à du reporting descriptif produit manuellement. Les décisions restent majoritairement fondées sur l'expérience.",
        "mid": "L'organisation produit des analyses utiles mais leur accès reste concentré et leur intégration aux processus opérationnels partielle.",
        "high": "L'analyse est diffusée et outillée. L'étape suivante consiste à passer du descriptif au prédictif sur des cas d'usage à valeur chiffrée.",
    },
    "culture": {
        "low": "La donnée n'est pas encore un réflexe managérial. Les investissements techniques risquent de ne pas être exploités faute d'appropriation.",
        "mid": "Une culture data émerge dans certaines directions. L'hétérogénéité entre équipes freine encore les démarches transverses.",
        "high": "La culture data est installée dans les pratiques de management. Le maintien passe par la formation continue et la reconnaissance des contributions.",
    },
    "infrastructure": {
        "low": "L'infrastructure limite les usages plutôt qu'elle ne les soutient. Les problèmes de capacité et d'architecture vont se transformer en incidents à mesure que les volumes croissent.",
        "mid": "L'infrastructure répond aux besoins courants mais son évolutivité et son interopérabilité doivent être renforcées pour absorber la croissance.",
        "high": "L'infrastructure est évolutive et supervisée. La vigilance porte sur la maîtrise des coûts et la sécurité proactive.",
    },
}


def narrative_for(dimension_code: str, percentage: float) -> str:
    band = "low" if percentage < 34 else ("mid" if percentage < 67 else "high")
    return DIMENSION_NARRATIVES.get(dimension_code, {}).get(band, "")


def recommendation_for(criterion_code: str) -> dict:
    return R.get(criterion_code, {})
