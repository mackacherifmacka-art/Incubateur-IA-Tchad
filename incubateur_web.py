import streamlit as st
import sqlite3
import hashlib
import os
import time

# ============================================
# INCUBATEUR IA TCHAD - v4
# Nouveauté : le DIAGNOSTIC IA se lance
# automatiquement après le choix du stade :
# analyse + forces + risques + questions IA
# ============================================

st.set_page_config(page_title="Incubateur IA Tchad", page_icon="🇹🇩")

NOM_DB = "incubateur.db"

# ---------- BASE DE DONNÉES ----------
def init_db():
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    sel TEXT,
                    mot_de_passe_hash TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS data (
                    username TEXT,
                    cle TEXT,
                    valeur TEXT,
                    PRIMARY KEY (username, cle))""")
    conn.commit()
    conn.close()

def hacher(mot_de_passe, sel):
    return hashlib.sha256((sel + mot_de_passe).encode()).hexdigest()

def creer_compte(username, mot_de_passe):
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone() is not None:
        conn.close()
        return False
    sel = os.urandom(16).hex()
    c.execute("INSERT INTO users VALUES (?, ?, ?)",
              (username, sel, hacher(mot_de_passe, sel)))
    conn.commit()
    conn.close()
    return True

def se_connecter(username, mot_de_passe):
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    c.execute("SELECT sel, mot_de_passe_hash FROM users WHERE username = ?",
              (username,))
    ligne = c.fetchone()
    conn.close()
    if ligne is None:
        return False
    sel, vrai_hash = ligne
    return hacher(mot_de_passe, sel) == vrai_hash

def sauvegarder(username):
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    for cle in ["prenom", "langue", "duree", "abonnement", "stade"]:
        c.execute("INSERT OR REPLACE INTO data VALUES (?, ?, ?)",
                  (username, cle, str(st.session_state.get(cle))))
    for cle, valeur in st.session_state.items():
        if cle.startswith("etape_") or cle.startswith("diag_"):
            c.execute("INSERT OR REPLACE INTO data VALUES (?, ?, ?)",
                      (username, cle, str(valeur)))
    conn.commit()
    conn.close()

def charger(username):
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    c.execute("SELECT cle, valeur FROM data WHERE username = ?", (username,))
    for cle, valeur in c.fetchall():
        if valeur == "True":
            st.session_state[cle] = True
        elif valeur == "False":
            st.session_state[cle] = False
        elif valeur == "None":
            st.session_state[cle] = None
        elif cle == "duree":
            st.session_state[cle] = int(valeur)
        else:
            st.session_state[cle] = valeur
    conn.close()

init_db()

# ---------- VALEURS PAR DÉFAUT ----------
for cle, valeur in [("langue", None), ("prenom", ""), ("duree", 0),
                    ("abonnement", None), ("page", "🏠 Accueil"),
                    ("stade", None)]:
    if cle not in st.session_state:
        st.session_state[cle] = valeur

# ---------- TRADUCTIONS ----------
T = {
    "bienvenue": {"fr": "Bienvenue dans l'incubateur de projets !",
                  "ar": "مرحباً بك في حاضنة المشاريع !"},
    "objectif": {"fr": "Transformons ton idée en projet finançable.",
                 "ar": "سنحوّل فكرتك إلى مشروع قابل للتمويل."}
}

# ---------- DIAGNOSTIC IA PAR STADE ----------
DIAGNOSTICS = {
    "idee": {
        "label": "J'ai juste une idée",
        "duree": 6,
        "analyse": ("Ton projet est au stade de l'idée brute. C'est le moment le plus "
                    "excitant... et le plus fragile : beaucoup d'idées meurent faute de "
                    "structure. L'IA va d'abord t'aider à clarifier le problème que tu "
                    "résolves et à vérifier que des clients en ont réellement besoin, "
                    "avant tout investissement."),
        "forces": ["Fraîcheur et créativité de l'idée",
                   "Aucun coût engagé pour l'instant",
                   "Possibilité de pivoter facilement"],
        "risques": ["Idee pas encore validée par le marché",
                    "Manque de données concrètes",
                    "Risque de rester bloqué dans la réflexion"],
        "questions": [
            "Dans une phrase simple : quel problème concret ton idée résout-elle ?",
            "Qui sont les 2-3 premiers clients que tu imagines ? (décris-les)",
            "Pourquoi toi peux-tu réussir ce projet ? (tes forces, ton expérience)"
        ]
    },
    "prototype": {
        "label": "J'ai un prototype ou un plan",
        "duree": 5,
        "analyse": ("Tu as déjà transformé ton idée en quelque chose de concret : plan, "
                    "maquette, prototype ou premiers tests. L'IA va maintenant t'aider à "
                    "mesurer ce qui fonctionne, corriger ce qui coince, et structurer "
                    "l'offre avant de passer à l'étude de marché approfondie."),
        "forces": ["Idée déjà concrétisée",
                   "Premiers retours possibles",
                   "Vision claire du produit ou service"],
        "risques": ["Prototype jamais testé auprès de vrais clients",
                    "Coûts cachés sous-estimés",
                    "Plan perfectible côté finances"],
        "questions": [
            "Qu'as-tu déjà construit ou préparé concrètement ? (plan, maquette, test...)",
            "As-tu déjà montré ton projet à de vrais clients ? Qu'ont-ils dit ?",
            "Qu'est-ce qui te bloque le plus en ce moment ?"
        ]
    },
    "lance": {
        "label": "Mon activité est déjà lancée",
        "duree": 3,
        "analyse": ("Ton activité existe déjà : tu as des clients, des ventes, une "
                    "réalité sur le terrain. L'IA va t'aider à structurer ce qui est "
                    "déjà en place, professionnaliser ta gestion et préparer le dossier "
                    "pour accéder au financement bancaire."),
        "forces": ["Activité réelle avec des clients",
                   "Données concrètes à analyser",
                   "Crédibilité auprès des financeurs"],
        "risques": ["Gestion informelle des finances",
                    "Pas de structure juridique formalisée",
                    "Croissance limitée par le manque de fonds"],
        "questions": [
            "Quel est ton chiffre d'affaires actuel (même approximatif) ?",
            "Quelle est ta plus grande difficulté aujourd'hui ?",
            "Où veux-tu être dans 12 mois ? (objectif concret)"
        ]
    }
}

# ---------- LES 6 PHASES ----------
PHASES = [
    ("Phase 1 - Admission en incubateur", [
        "Déposer le dossier de candidature (idée + profil + besoins)",
        "Évaluation par le comité de sélection (faisabilité, originalité, motivation)",
        "Signature de la convention d'incubation (durée : 6 à 24 mois)"]),
    ("Phase 2 - Analyse et validation de l'idée", [
        "Étude de marché : clients cibles, concurrence, tendances",
        "Affiner l'idée avec l'aide de l'IA",
        "Décider : poursuivre, adapter ou abandonner"]),
    ("Phase 3 - Business plan", [
        "Construire le modèle économique (revenus, coûts, prix, valeur)",
        "Rédiger le business plan complet (prévisionnel, stratégie, organisation)",
        "Préparer le pitch pour convaincre partenaires et investisseurs"]),
    ("Phase 4 - Accompagnement et formation", [
        "Formations : gestion, finance, marketing, droit, numérique",
        "Mentorat : échanges avec des entrepreneurs expérimentés",
        "Constituer son réseau (fournisseurs, clients, investisseurs)"]),
    ("Phase 5 - Mise en place opérationnelle", [
        "Formalisation juridique : choix du statut, RCCM, NIF",
        "Identité visuelle, site web, outils de communication",
        "Ressources : local, matériel, premiers financements"]),
    ("Phase 6 - Lancement et après-incubation", [
        "Lancement avec tests pilotes sur le marché",
        "Poursuite : pépinière, accélérateur ou coworking"]),
]

FORMULES = {
    "1 mois - 5 000 F": "5 000 F",
    "3 mois - 12 500 F": "12 500 F",
    "6 mois - 22 500 F": "22 500 F",
    "1 an - 42 500 F": "42 500 F",
}

PAGES = ["🏠 Accueil", "🎯 Diagnostic", "💰 Abonnement",
         "🗺️ Mon parcours", "📊 Mon score"]

def aller_a(nouvelle_page):
    st.session_state.page = nouvelle_page
    st.rerun()

def boutons_navigation(index_page, passer_actif=True, action_passer=None):
    col_passer, col_suivant = st.columns(2)
    with col_passer:
        if passer_actif and index_page < len(PAGES) - 1:
            if st.button("⏭ Passer", use_container_width=True):
                if action_passer is not None:
                    action_passer()
                aller_a(PAGES[index_page + 1])
    with col_suivant:
        if index_page < len(PAGES) - 1:
            if st.button("Suivant ➡️", use_container_width=True, type="primary"):
                aller_a(PAGES[index_page + 1])
        else:
            if st.button("🎉 Terminer", use_container_width=True, type="primary"):
                st.balloons()
                st.success("Bravo ! Ton parcours d'incubation est terminé. 🎓")

# ============================================
# BARRE LATÉRALE : AUTHENTIFICATION
# ============================================
st.sidebar.title("🇹🇩 Incubateur IA")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.sidebar.subheader("🔐 Ton compte")
    mode = st.sidebar.radio("", ["Se connecter", "Créer un compte"])
    username = st.sidebar.text_input("Nom d'utilisateur")
    mot_de_passe = st.sidebar.text_input("Mot de passe", type="password")

    if mode == "Créer un compte":
        if st.sidebar.button("✨ Créer mon compte"):
            if not username or not mot_de_passe:
                st.sidebar.error("Remplis les deux champs.")
            elif creer_compte(username, mot_de_passe):
                st.sidebar.success("Compte créé ! Connecte-toi maintenant.")
            else:
                st.sidebar.error("Ce nom d'utilisateur existe déjà.")
    else:
        if st.sidebar.button("🔓 Se connecter"):
            if se_connecter(username, mot_de_passe):
                st.session_state.user = username
                charger(username)
                st.rerun()
            else:
                st.sidebar.error("Identifiants incorrects.")

    st.title("🇹🇩 Incubateur IA Tchad")
    st.info("👈 **Crée un compte ou connecte-toi** dans le menu à gauche pour commencer ton parcours.")
    st.stop()

st.sidebar.success(f"👋 {st.session_state.user}")
st.sidebar.progress(PAGES.index(st.session_state.page) / (len(PAGES) - 1))
st.sidebar.caption(f"Étape {PAGES.index(st.session_state.page) + 1} / {len(PAGES)}")
if st.sidebar.button("🚪 Se déconnecter"):
    for cle in list(st.session_state.keys()):
        del st.session_state[cle]
    st.rerun()

page = st.sidebar.radio("Navigation", PAGES,
                        index=PAGES.index(st.session_state.page))
st.session_state.page = page
index_page = PAGES.index(page)

# ============================================
# PAGES
# ============================================
if page == "🏠 Accueil":
    langue = st.selectbox("Langue / اللغة", ["fr", "ar"])
    st.session_state.langue = langue

    st.title(T["bienvenue"][langue])
    st.write(T["objectif"][langue])

    prenom = st.text_input("Ton prénom", value=st.session_state.prenom)
    st.session_state.prenom = prenom

    if st.session_state.prenom:
        st.success(f"👋 Enchanté {st.session_state.prenom} !")

    boutons_navigation(index_page)

elif page == "🎯 Diagnostic":
    st.title("🎯 Diagnostic du projet")

    stade = st.radio("Quel est le stade de ton projet ?", list(DIAGNOSTICS.keys()),
                     format_func=lambda k: DIAGNOSTICS[k]["label"],
                     index=list(DIAGNOSTICS.keys()).index(st.session_state.stade)
                     if st.session_state.stade in DIAGNOSTICS else 0)

    # ---- LE TRAVAIL DE L'IA COMMENCE ----
    with st.spinner("🤖 L'IA analyse ton projet..."):
        time.sleep(1.5)   # petite pause pour l'effet "analyse en cours"

    infos = DIAGNOSTICS[stade]
    st.session_state.stade = stade
    st.session_state.duree = infos["duree"]

    st.success(f"🎯 Parcours recommandé : **{infos['duree']} mois** d'accompagnement")

    st.subheader("🧠 Analyse de l'IA")
    st.write(infos["analyse"])

    col_f, col_r = st.columns(2)
    with col_f:
        st.markdown("**💪 Tes forces**")
        for f in infos["forces"]:
            st.markdown(f"- {f}")
    with col_r:
        st.markdown("**⚠️ Points de vigilance**")
        for r in infos["risques"]:
            st.markdown(f"- {r}")

    st.divider()
    st.subheader("🤖 Pour affiner ton diagnostic, l'IA a besoin de toi")

    toutes_repondues = True
    for i, question in enumerate(infos["questions"]):
        cle = f"diag_{i}"
        reponse = st.text_input(f"**{i + 1}.** {question}", key=cle,
                                value=st.session_state.get(cle, ""))
        st.session_state[cle] = reponse
        if not reponse.strip():
            toutes_repondues = False

    if toutes_repondues:
        st.success("✅ Diagnostic complet ! L'IA a tout ce qu'il faut pour te guider.")
    else:
        st.info("Réponds aux questions de l'IA (ou laisse vide et clique Passer).")

    boutons_navigation(index_page)

elif page == "💰 Abonnement":
    st.title("💰 Formules d'abonnement")
    st.write("2 semaines gratuites, puis choisis ta formule :")

    formule = st.selectbox("Choisis ta formule", list(FORMULES.keys()))
    prix = FORMULES[formule]
    st.write(f"**Montant à payer : {prix}**")
    st.write("📱 Moov Money : **+235 98 28 25 52**")
    st.write("📱 Airtel Money : **+235 62 11 62 78**")

    if st.button("✅ J'ai envoyé le paiement"):
        st.session_state.abonnement = "paye"
        st.success("Paiement enregistré ! Envoie ta capture d'écran pour activation.")

    if st.button("🎁 Continuer avec l'essai gratuit (14 jours)"):
        st.session_state.abonnement = "essai"
        st.info("Essai gratuit activé. Profite bien !")

    def passer_abonnement():
        if st.session_state.abonnement is None:
            st.session_state.abonnement = "essai"

    boutons_navigation(index_page, action_passer=passer_abonnement)

elif page == "🗺️ Mon parcours":
    if st.session_state.abonnement is None:
        st.warning("⚠️ Va d'abord à la page **Abonnement** pour activer ton accès.")
    else:
        st.title(f"🗺️ Mon parcours ({st.session_state.duree} mois)")
        for i, (titre, etapes) in enumerate(PHASES):
            with st.expander(f"**{titre}**"):
                for j, etape in enumerate(etapes):
                    st.checkbox(etape, key=f"etape_{i}_{j}")

    boutons_navigation(index_page)

elif page == "📊 Mon score":
    st.title("📊 Score de bancabilité")

    total = sum(len(e) for _, e in PHASES)
    validees = sum(
        1 for i in range(len(PHASES))
        for j in range(len(PHASES[i][1]))
        if st.session_state.get(f"etape_{i}_{j}", False)
    )
    score = round(validees / total * 100)

    st.metric("Étapes validées", f"{validees} / {total}")
    st.progress(score / 100)
    st.metric("Score de bancabilité", f"{score} %")

    if score >= 80:
        st.success("🎉 Projet très bancable ! Prêt pour les banques et investisseurs.")
    elif score >= 50:
        st.info("💪 Bonne avancée ! Encore quelques étapes pour un dossier solide.")
    else:
        st.warning("🌱 C'est un début ! Continue étape par étape.")

    boutons_navigation(index_page)

sauvegarder(st.session_state.user)
