import streamlit as st
import sqlite3
import hashlib
import os
import time

# ============================================
# INCUBATEUR IA TCHAD - v6
# - Phase Admission SUPPRIMÉE (on commence par
#   "Analyse et validation de l'idée")
# - Quand l'entrepreneur coche une étape, l'IA
#   DISCUTE avec lui : question + réponses aux
#   préoccupations (mini-chat intégré)
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
                    ("stade", None), ("diag_domaine", None)]:
    if cle not in st.session_state:
        st.session_state[cle] = valeur

# ---------- TRADUCTIONS ----------
T = {
    "bienvenue": {"fr": "Bienvenue dans l'incubateur de projets !",
                  "ar": "مرحباً بك في حاضنة المشاريع !"},
    "objectif": {"fr": "Transformons ton idée en projet finançable.",
                 "ar": "سنحوّل فكرتك إلى مشروع قابل للتمويل."}
}

# ---------- DOMAINES D'ACTIVITÉ ----------
DOMAINES = {
    "Agriculture / Élevage": {
        "opportunites": ("Forte demande locale en produits vivriers ; possibilités "
                         "d'export vers la CEMAC ; saison sèche = niche pour "
                         "l'irrigation et l'agrobusiness."),
        "conseil": "Commence petit avec un cycle court (légumes, volaille) pour générer des revenus rapidement."
    },
    "Commerce / Distribution": {
        "opportunites": ("Déficit d'approvisionnement structuré dans plusieurs régions ; "
                         "le commerce transfrontalier (Cameroun, Nigéria, Soudan) "
                         "offre de bonnes marges."),
        "conseil": "Identifie un produit à forte rotation et sécurise ta chaîne d'approvisionnement avant d'investir lourd."
    },
    "Transformation agroalimentaire": {
        "opportunites": ("Transformation locale = valeur ajoutée et moins de pertes "
                         "(sésame, arachide, mangue...) ; la demande en produits "
                         "transformés locaux dépasse l'offre."),
        "conseil": "Commence par un produit unique maîtrisé, valide la qualité auprès de 10 clients réguliers."
    },
    "Services / Numérique": {
        "opportunites": ("Croissance rapide du mobile et du mobile money ; besoins "
                         "énormes en services digitaux pour PME (comptabilité, "
                         "visibilité, formation)."),
        "conseil": "Vends d'abord une prestation simple (ex: gestion de page Facebook pour commerçants) avant de créer un produit complexe."
    },
    "Artisanat / Mode": {
        "opportunites": ("Fierté du made in Tchad ; touristes et diaspora achètent "
                         "le local ; les tenues traditionnelles ont un marché "
                         "constant."),
        "conseil": "Travaille ton identité visuelle et documente tes créations avec de bonnes photos — c'est ta vitrine."
    },
    "Transport / Logistique": {
        "opportunites": ("Déplacements permanents entre N'Djamena, Moundou, Sarh "
                         "et l'extérieur ; manque de solutions fiables de "
                         "livraison pour le e-commerce naissant."),
        "conseil": "Commence sur une seule ligne bien connue, avec un carnet de clients fidèles avant d'étendre."
    },
    "Éducation / Formation": {
        "opportunites": ("Jeunesse majoritaire et soif d'apprentissage ; parents "
                         "prêts à payer pour la réussite scolaire ; formations "
                         "professionnelles très demandées."),
        "conseil": "Teste ta méthode avec un petit groupe payant avant de louer des locaux."
    },
    "Santé / Bien-être": {
        "opportunites": ("Besoins en pharmacies de proximité, nutrition, suivi "
                         "médical ; la santé préventive est un marché émergent "
                         "en milieu urbain."),
        "conseil": "Respecte impérativement la réglementation sanitaire — la confiance est ton premier capital."
    },
    "Autre domaine": {
        "opportunites": "Chaque secteur a ses opportunités : l'étude de marché de la Phase 1 les révèlera.",
        "conseil": "Décris précisément ton activité dans tes réponses pour un accompagnement sur mesure."
    }
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
        "risques": ["Idée pas encore validée par le marché",
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

# ---------- LE PARCOURS (Admission supprimée) ----------
# Chaque étape a maintenant sa QUESTION d'IA qui se
# déclenche quand l'entrepreneur coche la case.
PHASES = [
    ("Phase 1 - Analyse et validation de l'idée", [
        ("Étude de marché : clients cibles, concurrence, tendances",
         "Quels sont les 3 types de clients que tu vises en priorité ?"),
        ("Affiner l'idée avec l'aide de l'IA",
         "Qu'est-ce qui rend ton idée différente de ce qui existe déjà ?"),
        ("Décider : poursuivre, adapter ou abandonner",
         "Quelles informations as-tu collectées pour prendre ta décision ?"),
    ]),
    ("Phase 2 - Business plan", [
        ("Construire le modèle économique (revenus, coûts, prix, valeur)",
         "Comment vas-tu gagner de l'argent concrètement ?"),
        ("Rédiger le business plan complet (prévisionnel, stratégie, organisation)",
         "Quelle section du business plan te semble la plus difficile ?"),
        ("Préparer le pitch pour convaincre partenaires et investisseurs",
         "En une phrase, peux-tu présenter ton projet ?"),
    ]),
    ("Phase 3 - Accompagnement et formation", [
        ("Formations : gestion, finance, marketing, droit, numérique",
         "Quelle compétence te manque le plus aujourd'hui ?"),
        ("Mentorat : échanges avec des entrepreneurs expérimentés",
         "Quel type de mentor t'aiderait le plus ? (métier, expérience...)"),
        ("Constituer son réseau (fournisseurs, clients, investisseurs)",
         "Qui sont les 3 premières personnes utiles de ton réseau actuel ?"),
    ]),
    ("Phase 4 - Mise en place opérationnelle", [
        ("Formalisation juridique : choix du statut, RCCM, NIF",
         "Quelle forme juridique envisages-tu pour ton entreprise ?"),
        ("Identité visuelle, site web, outils de communication",
         "Comment veux-tu que les clients te reconnaissent et te retrouvent ?"),
        ("Ressources : local, matériel, premiers financements",
         "Quelle est ta première dépense vraiment indispensable ?"),
    ]),
    ("Phase 5 - Lancement et après-incubation", [
        ("Lancement avec tests pilotes sur le marché",
         "Quel petit test peux-tu lancer rapidement avec peu de moyens ?"),
        ("Poursuite : pépinière, accélérateur ou coworking",
         "De quel accompagnement après-incubation as-tu le plus besoin ?"),
    ]),
]

# ---------- MOTEUR DE RÉPONSE DE L'IA (par mots-clés) ----------
REGLES_IA = [
    (["argent", "finance", "fonds", "capital", "prêt", "pret", "budget",
      "fcfa", "coût", "cout", "cher", "moyens"],
     "💰 **La finance d'abord :** commence avec le minimum viable. Liste tes 3 premières "
     "dépenses indispensables, coupe le reste. Au Tchad, plusieurs options existent : "
     "tontine ou épagner solidaire, microfinance locale, concours d'entrepreneuriat, "
     "et bientôt les banques quand ton dossier sera bancable. Un projet qui démarre "
     "petit mais génère des revenus attire les financeurs."),

    (["client", "vente", "vendre", "marché", "marche", "acheter", "demande"],
     "🎯 **Trouver ses clients :** commence par les clients qui ont le problème le "
     "plus urgent. Va à leur rencontre directement (marchés, quartiers, WhatsApp). "
     "Pose une seule question : « Qu'est-ce qui t'empêche de... ? ». Vends avant "
     "d'avoir tout construit — la prévente valide ton marché sans investir."),

    (["peur", "stress", "échouer", "echouer", "risque", "oser", "confiance",
      "doute", "incapable"],
     "💛 **La peur est normale :** tous les entrepreneurs connus ont douté au début. "
     "L'échec n'est pas la fin : c'est une donnée qui te dit quoi ajuster. Réduis "
     "le risque : teste petit, apprends vite, répète. Chaque étape que tu coches ici "
     "est une victoire réelle."),

    (["temps", "occupé", "emploi", "horaire", "disponible"],
     "⏰ **Gérer son temps :** tu n'as pas besoin de 8h par jour. 1h concentrée "
     "chaque jour sur UNE action concrète fait avancer un projet énormément. "
     "Bloque un créneau fixe (ex: 19h-20h) et protège-le comme un rendez-vous "
     "important."),

    (["famille", "entourage", "conjoint", "mari", "parents", "amis"],
     "👨‍👩‍👧 **L'entourage :** la meilleure stratégie, c'est les résultats visibles. "
     "Ne cherche pas à convaincre par les mots : montre les petites victoires "
     "(premier client, premier chiffre). Implique un membre de la famille dans "
     "une tâche concrète — on soutient mieux ce qu'on a aidé à construire."),

    (["papier", "formalité", "formalités", "rccm", "impôt", "impot",
      "administration", "statut", "legal", "légal"],
     "📄 **Les formalités :** ne les reporte pas trop — une entreprise formalisée "
     "peut ouvrir un compte bancaire, facturer, et accéder aux financements. Au "
     "Tchad : choisis ta forme juridique, immatricule-toi au RCCM et obtiens ton "
     "NIF auprès des impôts. La Phase 4 de ton parcours te guidera pas à pas."),

    (["expérience", "experience", "compétence", "competence", "savoir",
      "formation", "diplôme"],
     "📚 **Compétences :** tu n'as pas besoin de tout savoir — il faut savoir "
     "apprendre. Identifie LA compétence qui bloque le plus (souvent : vente ou "
     "gestion), et travaille uniquement celle-là ce mois-ci. Le mentorat de la "
     "Phase 3 te connectera à des expériences complémentaires."),

    (["concurrence", "concurrent", "déjà", "deja", "copier", "copie"],
     "⚔️ **La concurrence est une bonne nouvelle :** elle prouve qu'il y a un "
     "marché ! Ta différence peut être le prix, la qualité, la proximité, le "
     "service ou la spécialisation. Analyse 2-3 concurrents : que font-ils bien ? "
     "Que négligent-ils ? C'est là que tu gagneras."),

    (["équipe", "equipe", "associé", "associer", "partenaire", "seul"],
     "🤝 **On est plus fort à plusieurs :** repère quelqu'un qui a les compétences "
     "que tu n'as pas (souvent technique + commercial). Testez une collaboration "
     "sur un petit projet avant de vous engager. Si tu es seul pour l'instant : "
     "c'est OK, beaucoup d'entreprises ont démarré avec une seule personne."),

    (["internet", "connexion", "réseau social", "whatsapp", "publicité",
      "marketing", "communication"],
     "📱 **La visibilité :** au Tchad, WhatsApp et Facebook sont des canaux "
     "puissants et économiques. Une page propre, des photos réelles de ton produit, "
     "des témoignages clients — c'est suffisant pour démarrer. Publie régulièrement, "
     "même une fois par semaine."),
]

REPONSE_DEFAUT = (
    "🤔 **Merci pour ta question !** Voici comment avancer : découpe ta préoccupation "
    "en une petite action concrète à faire cette semaine. Si c'est un blocage "
    "financier, parle-en en utilisant des mots comme « argent » ou « budget » ; "
    "si c'est la peur d'échouer, dis « peur » — je suis là pour ça. Qu'est-ce qui "
    "te préoccupe le plus en ce moment ?")

def reponse_ia(message, titre_etape):
    """Cherche le mot-clé de la préoccupation et renvoie la réponse adaptée."""
    texte = message.lower()
    for mots_clefs, reponse in REGLES_IA:
        if any(mot in texte for mot in mots_clefs):
            return reponse + f"\n\n📌 *(Étape concernée : {titre_etape})*"
    return REPONSE_DEFAUT + f"\n\n📌 *(Étape concernée : {titre_etape})*"

def envoyer_message(i, j, titre_etape):
    """Callback du bouton Envoyer : lit la question, génère la réponse, vide le champ."""
    cle_champ = f"q_{i}_{j}"
    cle_chat = f"chat_{i}_{j}"
    message = st.session_state.get(cle_champ, "").strip()
    if message:
        st.session_state.setdefault(cle_chat, []).append(
            (message, reponse_ia(message, titre_etape)))
        st.session_state[cle_champ] = ""

# ---------- FORMULES ----------
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

    with st.spinner("🤖 L'IA analyse ton projet..."):
        time.sleep(1)

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

    st.subheader("🏭 Dans quel domaine veux-tu entreprendre ?")
    st.selectbox("Choisis ton domaine d'activité", list(DOMAINES.keys()),
                 key="diag_domaine")

    domaine = st.session_state.diag_domaine
    if domaine in DOMAINES:
        infos_domaine = DOMAINES[domaine]
        st.info(f"**Opportunités du secteur « {domaine} » au Tchad :** "
                + infos_domaine["opportunites"])

    st.divider()

    st.subheader("🤖 Pour affiner ton diagnostic, l'IA a besoin de toi")

    for i, question in enumerate(infos["questions"]):
        st.text_input(f"**{i + 1}.** {question}", key=f"diag_{i}")

    reponses = [st.session_state.get(f"diag_{i}", "").strip()
                for i in range(len(infos["questions"]))]
    toutes_repondues = all(reponses) and domaine is not None

    if toutes_repondues:
        with st.spinner("🤖 L'IA structure ton diagnostic..."):
            time.sleep(1.5)

        st.divider()
        st.subheader("📋 Ton diagnostic structuré par l'IA")
        st.markdown(f"""
**👤 Porteur de projet :** {st.session_state.prenom}
**🏭 Domaine :** {domaine}
**📍 Stade :** {infos["label"]} → parcours de **{infos["duree"]} mois**

**🔍 Problème identifié :** {reponses[0]}

**🎯 Clients visés :** {reponses[1]}

**💪 Atout du porteur :** {reponses[2]}

**🌟 Opportunités du secteur :** {infos_domaine["opportunites"]}

**🧭 Premier conseil de l'IA :** {infos_domaine["conseil"]}

**➡️ Prochaine étape recommandée :** l'étude de marché de la Phase 1
de ton parcours (« Analyse et validation de l'idée »).
        """)
        st.success("✅ Diagnostic complet et sauvegardé ! Clique sur « Suivant ».")
    else:
        st.info("Réponds aux questions de l'IA (ou clique Passer pour plus tard).")

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
        st.caption("💡 Coche une étape : ton mentor IA te pose une question et "
                   "répond à tes préoccupations juste en dessous.")

        for i, (titre_phase, etapes) in enumerate(PHASES):
            validees_phase = sum(
                1 for j in range(len(etapes))
                if st.session_state.get(f"etape_{i}_{j}", False))
            with st.expander(
                    f"**{titre_phase}** — {validees_phase}/{len(etapes)} étapes"):
                for j, (etape, question_ia) in enumerate(etapes):
                    cochee = st.checkbox(etape, key=f"etape_{i}_{j}")

                    if cochee:
                        # ---- LE MENTOR IA PREND LE RELAIS ----
                        st.markdown(
                            f"🤖 **Ton mentor IA :** _{question_ia}_")
                        st.text_input("Ta réponse ou ta préoccupation :",
                                      key=f"q_{i}_{j}",
                                      placeholder="Ex: j'ai peur de manquer "
                                                  "d'argent pour démarrer...")
                        st.button("📩 Envoyer à l'IA",
                                  key=f"btn_{i}_{j}",
                                  on_click=envoyer_message,
                                  args=(i, j, etape))

                        # Affichage de la conversation
                        for question, reponse in st.session_state.get(
                                f"chat_{i}_{j}", []):
                            st.markdown(
                                f"> **Toi :** {question}")
                            st.markdown(reponse)

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
