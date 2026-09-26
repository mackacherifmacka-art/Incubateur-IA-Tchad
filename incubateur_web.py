import streamlit as st

# ============================================
# INCUBATEUR IA TCHAD - Version Web (Streamlit)
# ============================================

st.set_page_config(page_title="Incubateur IA Tchad", page_icon="🇹🇩")

# ---------- TRADUCTIONS ----------
T = {
    "bienvenue": {
        "fr": "Bienvenue dans l'incubateur de projets !",
        "ar": "مرحباً بك في حاضنة المشاريع !"
    },
    "objectif": {
        "fr": "Transformons ton idée en projet finançable.",
        "ar": "سنحوّل فكرتك إلى مشروع قابل للتمويل."
    }
}

# ---------- LES 6 PHASES (contenu du parcours) ----------
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

# ---------- MÉMOIRE DE L'APPLICATION (session_state) ----------
if "langue" not in st.session_state:
    st.session_state.langue = None
if "prenom" not in st.session_state:
    st.session_state.prenom = ""
if "duree" not in st.session_state:
    st.session_state.duree = 0
if "abonnement" not in st.session_state:
    st.session_state.abonnement = None   # None, "essai" ou "paye"

# ---------- BARRE LATÉRALE : NAVIGATION ----------
st.sidebar.title("🇹🇩 Incubateur IA")
page = st.sidebar.radio("Navigation", [
    "🏠 Accueil", "🎯 Diagnostic", "💰 Abonnement",
    "🗺️ Mon parcours", "📊 Mon score"
])

# ---------- PAGE : ACCUEIL ----------
if page == "🏠 Accueil":
    langue = st.selectbox("Langue / اللغة", ["fr", "ar"])
    st.session_state.langue = langue

    st.title(T["bienvenue"][langue])
    st.write(T["objectif"][langue])

    prenom = st.text_input("Ton prénom", value=st.session_state.prenom)
    st.session_state.prenom = prenom

    if st.session_state.prenom:
        st.success(f"👋 Enchanté {st.session_state.prenom} ! Va au **Diagnostic** dans le menu à gauche.")

# ---------- PAGE : DIAGNOSTIC ----------
elif page == "🎯 Diagnostic":
    st.title("🎯 Diagnostic du projet")
    st.write(f"Entrepreneur : **{st.session_state.prenom}**")

    stade = st.radio("Quel est le stade de ton projet ?", [
        "J'ai juste une idée",
        "J'ai un prototype ou un plan",
        "Mon activité est déjà lancée"
    ])

    if stade == "J'ai juste une idée":
        st.session_state.duree = 6
    elif stade == "J'ai un prototype ou un plan":
        st.session_state.duree = 5
    else:
        st.session_state.duree = 3

    st.info(f"🎯 Ton parcours d'accompagnement durera **{st.session_state.duree} mois**.")

# ---------- PAGE : ABONNEMENT ----------
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

# ---------- PAGE : PARCOURS ----------
elif page == "🗺️ Mon parcours":
    if st.session_state.abonnement is None:
        st.warning("⚠️ Va d'abord à la page **Abonnement** pour activer ton accès.")
    else:
        st.title(f"🗺️ Mon parcours ({st.session_state.duree} mois)")
        for i, (titre, etapes) in enumerate(PHASES):
            with st.expander(f"**{titre}**"):
                for j, etape in enumerate(etapes):
                    st.checkbox(etape, key=f"etape_{i}_{j}")

# ---------- PAGE : SCORE ----------
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
