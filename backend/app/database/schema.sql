-- =====================================================================
-- schema.sql : base PostgreSQL complète de la SAÉ « Recommandation de vols »
-- Groupe « Les Orques tactiques » - BUT3 5.Real.01
--
-- Contenu (dans l'ordre) :
--   0. Extensions, types, fonction de trigger
--   1. Compte et accès            (US1-US4, US24, US25)
--   2. Référentiel                (pays, aéroports : US33)
--   3. Données de vols            (JSON bruts, vols, segments : US33-US35)
--   4. Préférences et profil      (US5, US6, US10, US11, US23)
--   5. Recherches et historique   (US9, US14, US19)
--   6. Interactions               (US16, US17, US21, US22)
--   7. Recommandations et mesures (US12, US18, US26-US31)
--   8. Vues
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. Extensions, types, fonction de trigger
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector

DO $$ BEGIN CREATE TYPE role_utilisateur AS ENUM ('utilisateur', 'evaluateur');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE type_jeton AS ENUM ('activation', 'reinitialisation_mdp');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE type_consentement AS ENUM ('politique', 'personnalisation', 'localisation');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE type_requete AS ENUM ('aller_simple', 'aller_retour', 'aeroports');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE sens_trajet AS ENUM ('aller', 'retour');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE classe_cabine AS ENUM ('economy', 'premium_economy', 'business', 'first');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE type_interaction AS ENUM ('vue', 'favori', 'avis_pertinent', 'avis_non_pertinent', 'reserver');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE approche_reco AS ENUM ('A', 'B', 'MELANGE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE OR REPLACE FUNCTION maj_modifie_le()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modifie_le = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
-- 1. Compte et accès
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utilisateurs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom                   VARCHAR(100) NOT NULL,
    prenom                VARCHAR(100) NOT NULL,
    email                 VARCHAR(255) NOT NULL,
    mot_de_passe_hash     VARCHAR(255) NOT NULL,
    role                  role_utilisateur NOT NULL DEFAULT 'utilisateur',
    actif                 BOOLEAN NOT NULL DEFAULT FALSE,     -- TRUE après activation par email (US2)
    onboarding_termine    BOOLEAN NOT NULL DEFAULT FALSE,     -- page de préférences passée ou remplie (US5)
    simule                BOOLEAN NOT NULL DEFAULT FALSE,     -- utilisateur fictif (US36)
    demo                  BOOLEAN NOT NULL DEFAULT FALSE,     -- compte de démonstration (US32)
    derniere_connexion    TIMESTAMPTZ,
    cree_le               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_utilisateur_email CHECK (position('@' IN email) > 1)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_utilisateurs_email ON utilisateurs (LOWER(email));

DROP TRIGGER IF EXISTS trg_utilisateurs_modifie_le ON utilisateurs;
CREATE TRIGGER trg_utilisateurs_modifie_le
    BEFORE UPDATE ON utilisateurs
    FOR EACH ROW EXECUTE FUNCTION maj_modifie_le();

-- Consentements : « politique » est obligatoire (vérifié par le service),
-- « personnalisation » et « localisation » sont facultatifs.
CREATE TABLE IF NOT EXISTS consentements (
    utilisateur_id   UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    type             type_consentement NOT NULL,
    accorde          BOOLEAN NOT NULL,
    modifie_le       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (utilisateur_id, type)
);

-- Jetons à usage unique : activation (24 h) et mot de passe oublié (1 h).
-- On stocke le hash du jeton, jamais le jeton lui-même.
CREATE TABLE IF NOT EXISTS jetons (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id   UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    type             type_jeton NOT NULL,
    hash_jeton       CHAR(64) NOT NULL UNIQUE,
    expire_le        TIMESTAMPTZ NOT NULL,
    utilise_le       TIMESTAMPTZ,
    cree_le          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_jeton_expiration CHECK (expire_le > cree_le)
);

CREATE INDEX IF NOT EXISTS idx_jetons_utilisateur ON jetons (utilisateur_id, type);

-- ---------------------------------------------------------------------
-- 2. Référentiel : pays et aéroports
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pays (
    code_pays   CHAR(2) PRIMARY KEY,           -- ISO 3166-1 alpha-2
    nom         VARCHAR(150) NOT NULL,
    cree_le     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aeroports (
    code_iata   CHAR(3) PRIMARY KEY,
    nom         VARCHAR(200) NOT NULL,
    ville       VARCHAR(120),
    code_pays   CHAR(2) REFERENCES pays(code_pays),
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    fuseau      VARCHAR(64),
    cree_le     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aeroports_pays  ON aeroports (code_pays);
CREATE INDEX IF NOT EXISTS idx_aeroports_ville ON aeroports (ville);

DROP TRIGGER IF EXISTS trg_aeroports_modifie_le ON aeroports;
CREATE TRIGGER trg_aeroports_modifie_le
    BEFORE UPDATE ON aeroports
    FOR EACH ROW EXECUTE FUNCTION maj_modifie_le();

-- ---------------------------------------------------------------------
-- 3. Données de vols
-- ---------------------------------------------------------------------
-- 3.1 JSON bruts : un enregistrement par appel d'API (rejeu possible, US34)
CREATE TABLE IF NOT EXISTS ingestions_brutes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source           VARCHAR(40) NOT NULL DEFAULT 'ignav',
    type             type_requete NOT NULL,
    origine          CHAR(3),
    destination      CHAR(3),
    date_depart      DATE,
    date_retour      DATE,
    observe_le       TIMESTAMPTZ NOT NULL,             -- champ "observed_at" du JSON
    nb_itineraires   INTEGER NOT NULL DEFAULT 0,
    payload          JSONB NOT NULL,
    traite           BOOLEAN NOT NULL DEFAULT FALSE,   -- TRUE une fois normalisé
    cree_le          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ingestion_dates CHECK (date_retour IS NULL OR date_retour >= date_depart)
);

CREATE INDEX IF NOT EXISTS idx_ingestions_route
    ON ingestions_brutes (origine, destination, date_depart);
CREATE INDEX IF NOT EXISTS idx_ingestions_a_traiter
    ON ingestions_brutes (traite) WHERE traite = FALSE;

-- 3.2 Vols : un itinéraire complet (aller simple ou aller-retour).
-- "signature" = SHA-256 calculé côté Python à partir des segments
-- (code compagnie | numéro de vol | départ UTC, aller puis retour).
CREATE TABLE IF NOT EXISTS vols (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signature           CHAR(64) NOT NULL UNIQUE,
    ignav_id            VARCHAR(64),
    ingestion_id        UUID REFERENCES ingestions_brutes(id) ON DELETE SET NULL,

    origine             CHAR(3) NOT NULL REFERENCES aeroports(code_iata),
    destination         CHAR(3) NOT NULL REFERENCES aeroports(code_iata),
    date_depart         DATE NOT NULL,
    date_retour         DATE,
    aller_retour        BOOLEAN NOT NULL DEFAULT FALSE,

    prix                NUMERIC(10,2) NOT NULL CHECK (prix >= 0),
    devise              CHAR(3) NOT NULL DEFAULT 'USD',
    statut_prix         VARCHAR(30),
    classe              classe_cabine NOT NULL DEFAULT 'economy',
    auto_transfert      BOOLEAN NOT NULL DEFAULT FALSE,

    compagnie_aller     VARCHAR(120) NOT NULL,
    duree_aller_min     INTEGER NOT NULL CHECK (duree_aller_min > 0),
    escales_aller       SMALLINT NOT NULL DEFAULT 0 CHECK (escales_aller >= 0),
    compagnie_retour    VARCHAR(120),
    duree_retour_min    INTEGER CHECK (duree_retour_min > 0),
    escales_retour      SMALLINT CHECK (escales_retour >= 0),

    bagage_inclus       BOOLEAN,                       -- NULL tant que la donnée est inconnue
    simulee             BOOLEAN NOT NULL DEFAULT FALSE,-- vol généré hors catalogue (US35)
    observe_le          TIMESTAMPTZ NOT NULL,          -- date de relevé du prix

    embedding           vector(5),                     -- approche A : prix, durée, escales, compagnie, bagage (0 à 1)

    cree_le             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modifie_le          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_vol_aller_retour CHECK (
        (aller_retour = FALSE AND date_retour IS NULL AND compagnie_retour IS NULL)
        OR (aller_retour = TRUE AND date_retour IS NOT NULL AND compagnie_retour IS NOT NULL)
    ),
    CONSTRAINT ck_vol_dates CHECK (date_retour IS NULL OR date_retour >= date_depart),
    CONSTRAINT ck_vol_route CHECK (origine <> destination)
);

CREATE INDEX IF NOT EXISTS idx_vols_recherche
    ON vols (origine, destination, date_depart, aller_retour);
CREATE INDEX IF NOT EXISTS idx_vols_prix     ON vols (prix);
CREATE INDEX IF NOT EXISTS idx_vols_ignav_id ON vols (ignav_id);
CREATE INDEX IF NOT EXISTS idx_vols_embedding
    ON vols USING hnsw (embedding vector_cosine_ops);

DROP TRIGGER IF EXISTS trg_vols_modifie_le ON vols;
CREATE TRIGGER trg_vols_modifie_le
    BEFORE UPDATE ON vols
    FOR EACH ROW EXECUTE FUNCTION maj_modifie_le();

-- 3.3 Segments : un tronçon. Escales d'un sens = nombre de segments - 1.
CREATE TABLE IF NOT EXISTS segments_vol (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vol_id                UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    sens                  sens_trajet NOT NULL,
    ordre                 SMALLINT NOT NULL CHECK (ordre >= 1),

    code_compagnie        VARCHAR(3) NOT NULL,         -- marketing_carrier_code
    numero_vol            VARCHAR(10) NOT NULL,
    compagnie_operante    VARCHAR(120) NOT NULL,
    avion                 VARCHAR(80),

    aeroport_depart       CHAR(3) NOT NULL REFERENCES aeroports(code_iata),
    depart_local          TIMESTAMP NOT NULL,
    fuseau_depart         VARCHAR(64) NOT NULL,
    depart_utc            TIMESTAMPTZ NOT NULL,

    aeroport_arrivee      CHAR(3) NOT NULL REFERENCES aeroports(code_iata),
    arrivee_locale        TIMESTAMP NOT NULL,
    fuseau_arrivee        VARCHAR(64) NOT NULL,
    arrivee_utc           TIMESTAMPTZ NOT NULL,

    duree_min             INTEGER NOT NULL CHECK (duree_min > 0),

    UNIQUE (vol_id, sens, ordre),
    CONSTRAINT ck_segment_horaires CHECK (arrivee_utc > depart_utc)
);

CREATE INDEX IF NOT EXISTS idx_segments_vol    ON segments_vol (vol_id);
CREATE INDEX IF NOT EXISTS idx_segments_depart ON segments_vol (aeroport_depart, depart_utc);

-- ---------------------------------------------------------------------
-- 4. Préférences et profil
-- ---------------------------------------------------------------------
-- Préférences facultatives (US5, US6) + lieu de départ (US10, US11).
-- US25 : supprimer le lieu de départ = mettre latitude/longitude à NULL.
CREATE TABLE IF NOT EXISTS preferences_utilisateur (
    utilisateur_id        UUID PRIMARY KEY REFERENCES utilisateurs(id) ON DELETE CASCADE,
    aeroport_habituel     CHAR(3) REFERENCES aeroports(code_iata) ON DELETE SET NULL,
    budget_max            NUMERIC(10,2) CHECK (budget_max >= 0),
    escales_max           SMALLINT CHECK (escales_max >= 0),
    compagnies_preferees  VARCHAR(120)[] NOT NULL DEFAULT '{}',
    bagage_requis         BOOLEAN,
    latitude_depart       DOUBLE PRECISION,
    longitude_depart      DOUBLE PRECISION,
    modifie_le            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_preferences_modifie_le ON preferences_utilisateur;
CREATE TRIGGER trg_preferences_modifie_le
    BEFORE UPDATE ON preferences_utilisateur
    FOR EACH ROW EXECUTE FUNCTION maj_modifie_le();

-- Profil de l'approche A : moyenne des embeddings des vols vus, favoris ou
-- réservés (ou préférences pour un nouvel utilisateur). Recalculé à la
-- connexion suivante (US23).
CREATE TABLE IF NOT EXISTS profils_utilisateur (
    utilisateur_id        UUID PRIMARY KEY REFERENCES utilisateurs(id) ON DELETE CASCADE,
    embedding             vector(5),
    nb_interactions       INTEGER NOT NULL DEFAULT 0 CHECK (nb_interactions >= 0),
    mis_a_jour_le         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 5. Recherches et historique
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recherches (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id    UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    origine           CHAR(3) REFERENCES aeroports(code_iata) ON DELETE SET NULL,
    destination       CHAR(3) REFERENCES aeroports(code_iata) ON DELETE SET NULL,
    pays_destination  CHAR(2) REFERENCES pays(code_pays) ON DELETE SET NULL,
    ville_destination VARCHAR(120),
    date_depart       DATE,
    date_retour       DATE,
    aller_retour      BOOLEAN NOT NULL DEFAULT FALSE,
    nb_passagers      SMALLINT NOT NULL DEFAULT 1 CHECK (nb_passagers BETWEEN 1 AND 9),
    budget_max        NUMERIC(10,2) CHECK (budget_max >= 0),
    autres_criteres   JSONB NOT NULL DEFAULT '{}'::jsonb,   -- escales, compagnies, bagage...
    cree_le           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_recherche_dates CHECK (date_retour IS NULL OR date_retour >= date_depart)
);

CREATE INDEX IF NOT EXISTS idx_recherches_utilisateur ON recherches (utilisateur_id, cree_le DESC);

-- ---------------------------------------------------------------------
-- 6. Interactions
-- ---------------------------------------------------------------------
-- Journal des actions (US22). Le poids sert à l'approche B :
-- un clic « Réserver » compte plus qu'une simple vue.
CREATE TABLE IF NOT EXISTS interactions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id   UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    vol_id           UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    recherche_id     UUID REFERENCES recherches(id) ON DELETE SET NULL,
    type             type_interaction NOT NULL,
    poids            SMALLINT GENERATED ALWAYS AS (
                        CASE type
                            WHEN 'vue'                THEN 1
                            WHEN 'favori'             THEN 3
                            WHEN 'avis_pertinent'     THEN 3
                            WHEN 'avis_non_pertinent' THEN -2
                            WHEN 'reserver'           THEN 5
                        END
                     ) STORED,
    cree_le          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interactions_utilisateur ON interactions (utilisateur_id, cree_le DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_vol         ON interactions (vol_id);

-- État courant des favoris (US16) et des avis (US17).
CREATE TABLE IF NOT EXISTS favoris (
    utilisateur_id   UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    vol_id           UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    cree_le          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (utilisateur_id, vol_id)
);

CREATE TABLE IF NOT EXISTS avis_vol (
    utilisateur_id   UUID NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    vol_id           UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    pertinent        BOOLEAN NOT NULL,
    modifie_le       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (utilisateur_id, vol_id)
);

-- ---------------------------------------------------------------------
-- 7. Recommandations et mesures
-- ---------------------------------------------------------------------
-- Une exécution = un calcul de recommandation (temps, ressources : US26, US30).
-- Les mesures sont conservées si l'utilisateur supprime son compte.
CREATE TABLE IF NOT EXISTS executions_recommandation (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id   UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    recherche_id     UUID REFERENCES recherches(id) ON DELETE SET NULL,
    approche         approche_reco NOT NULL,
    alpha            NUMERIC(4,3) CHECK (alpha BETWEEN 0 AND 1),   -- part de B dans le mélange (US28)
    k                SMALLINT,                                      -- voisins utilisés par kNN
    duree_ms         NUMERIC(10,2) NOT NULL CHECK (duree_ms >= 0),
    cpu_ms           NUMERIC(10,2),
    memoire_mo       NUMERIC(10,2),
    nb_resultats     INTEGER NOT NULL DEFAULT 0,
    cree_le          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_executions_approche ON executions_recommandation (approche, cree_le DESC);

-- Résultats classés, avec explication courte (US12, US18) et scores A/B (US29).
CREATE TABLE IF NOT EXISTS resultats_recommandation (
    execution_id   UUID NOT NULL REFERENCES executions_recommandation(id) ON DELETE CASCADE,
    vol_id         UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    rang           INTEGER NOT NULL CHECK (rang >= 1),
    score          DOUBLE PRECISION NOT NULL,
    score_a        DOUBLE PRECISION,
    score_b        DOUBLE PRECISION,
    explication    VARCHAR(255),
    PRIMARY KEY (execution_id, vol_id),
    UNIQUE (execution_id, rang)
);

-- Similarités vol-vol de l'approche B (kNN item-based).
-- Stockées dans les deux sens pour simplifier la requête des voisins.
CREATE TABLE IF NOT EXISTS similarites_vols (
    vol_id      UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    voisin_id   UUID NOT NULL REFERENCES vols(id) ON DELETE CASCADE,
    similarite  REAL NOT NULL CHECK (similarite BETWEEN -1 AND 1),
    calcule_le  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (vol_id, voisin_id),
    CHECK (vol_id <> voisin_id)
);

CREATE INDEX IF NOT EXISTS idx_similarites_classement ON similarites_vols (vol_id, similarite DESC);

-- Qualité de chaque approche sur l'historique (US31).
CREATE TABLE IF NOT EXISTS metriques_qualite (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approche         approche_reco NOT NULL,
    k                SMALLINT NOT NULL CHECK (k >= 1),
    precision_k      DOUBLE PRECISION CHECK (precision_k BETWEEN 0 AND 1),
    ndcg             DOUBLE PRECISION CHECK (ndcg BETWEEN 0 AND 1),
    nb_utilisateurs  INTEGER NOT NULL CHECK (nb_utilisateurs >= 0),
    calcule_le       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metriques_approche ON metriques_qualite (approche, calcule_le DESC);

-- ---------------------------------------------------------------------
-- 8. Vues
-- ---------------------------------------------------------------------
-- Vol + horaires de l'aller, pour l'API de résultats et la fiche d'un vol.
CREATE OR REPLACE VIEW v_vols_resume AS
SELECT
    v.id, v.origine, v.destination, v.date_depart, v.date_retour, v.aller_retour,
    v.prix, v.devise, v.compagnie_aller, v.duree_aller_min, v.escales_aller,
    v.compagnie_retour, v.duree_retour_min, v.escales_retour,
    v.bagage_inclus, v.simulee, v.observe_le, v.ignav_id,
    (SELECT MIN(s.depart_local) FROM segments_vol s
        WHERE s.vol_id = v.id AND s.sens = 'aller')   AS depart_aller_local,
    (SELECT MAX(s.arrivee_locale) FROM segments_vol s
        WHERE s.vol_id = v.id AND s.sens = 'aller')   AS arrivee_aller_locale
FROM vols v;

-- Tableau de bord évaluateur : temps min, max, moyen et ressources (US30).
CREATE OR REPLACE VIEW v_stats_approches AS
SELECT
    approche,
    COUNT(*)                         AS nb_executions,
    ROUND(MIN(duree_ms), 2)          AS duree_min_ms,
    ROUND(MAX(duree_ms), 2)          AS duree_max_ms,
    ROUND(AVG(duree_ms), 2)          AS duree_moyenne_ms,
    ROUND(AVG(cpu_ms), 2)            AS cpu_moyen_ms,
    ROUND(AVG(memoire_mo), 2)        AS memoire_moyenne_mo
FROM executions_recommandation
GROUP BY approche;

-- Interactions pondérées par utilisateur et par vol : matrice de l'approche B.
CREATE OR REPLACE VIEW v_matrice_interactions AS
SELECT utilisateur_id, vol_id, SUM(poids) AS poids_total
FROM interactions
GROUP BY utilisateur_id, vol_id;

-- =====================================================================
-- Rappel pour le script d'ingestion (upsert sans doublon) :
--
-- INSERT INTO vols (signature, ignav_id, ...) VALUES (%s, %s, ...)
-- ON CONFLICT (signature) DO UPDATE
--    SET prix = EXCLUDED.prix,
--        ignav_id = EXCLUDED.ignav_id,
--        observe_le = EXCLUDED.observe_le,
--        statut_prix = EXCLUDED.statut_prix
-- RETURNING id;
--
-- Segments : insérés seulement si le vol vient d'être créé
-- (ou DELETE puis INSERT dans la même transaction).
-- =====================================================================
