import streamlit as st
import sqlite3
import hashlib
import os
import time
import datetime

# ============================================
# INCUBATEUR IA TCHAD - v11\n# Coaching guidé activité par activité : le coach IA\n# explique COMMENT faire chaque activité clé, puis analyse\n# le résultat de l'entrepreneur
# Parcours réorganisé selon 9 étapes de coaching
# professionnel (sans nom d'organisation) :
# chaque étape = objectif + livrables + coach IA
# qui analyse chaque réponse. Fin d'incubation =
# projet bancable complet + budget + attestation.
# ============================================

st.set_page_config(page_title="Incubateur IA Tchad", page_icon="🇹🇩",
                   layout="centered", initial_sidebar_state="expanded")

# ==================== DESIGN ====================
st.markdown("""
<style>
    /* Fond général */
    .stApp {
        background: linear-gradient(180deg, #f7f9fc 0%, #eef2f7 100%);
    }
    /* Titres */
    h1, h2, h3 {
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
        color: #002664;
    }
    /* Bannière héro */
    .hero {
        background: linear-gradient(135deg, #002664 0%, #1a5276 60%, #2e86c1 100%);
        color: white;
        padding: 2.2rem 1.8rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 38, 100, 0.25);
    }
    .hero h1 { color: white !important; margin: 0; font-size: 1.9rem; }
    .hero p { color: #dbe9f5; font-size: 1.05rem; margin-top: 0.6rem; }
    .badge {
        display: inline-block;
        background: #FECB00;
        color: #002664;
        font-weight: bold;
        padding: 0.25rem 0.9rem;
        border-radius: 999px;
        font-size: 0.8rem;
        margin-bottom: 0.8rem;
    }
    /* Cartes */
    .carte {
        background: white;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(0, 38, 100, 0.08);
        border-left: 5px solid #1a5276;
    }
    .carte-or   { border-left-color: #FECB00; }
    .carte-rouge{ border-left-color: #C60C30; }
    .carte-vert { border-left-color: #1e8449; }
    .carte h4 { color: #002664; margin: 0 0 0.4rem 0; }
    .carte p  { margin: 0; color: #444; }
    /* Boutons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    /* Barre latérale */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #002664 0%, #1a3a6b 100%);
    }
    [data-testid="stSidebar"] * { color: #eaf2fa !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1px solid #5a7ba6 !important;
        color: #eaf2fa !important;
    }
    /* Pied de page */
    .pied {
        text-align: center;
        color: #7f8c9b;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #d5dee8;
    }
</style>
""", unsafe_allow_html=True)

NOM_DB = "incubateur.db"

# ---- IA GÉNÉRATIVE (Google Gemini) ----
try:
    import google.generativeai as genai
    GENAI_OK = True
except ImportError:
    GENAI_OK = False

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
        if cle.startswith(("etape_", "diag_", "synthese_", "form_")):
            c.execute("INSERT OR REPLACE INTO data VALUES (?, ?, ?)",
                      (username, cle, str(valeur)))
    conn.commit()
    conn.close()

def charger(username):
    conn = sqlite3.connect(NOM_DB)
    c = conn.cursor()
    c.execute("SELECT cle, valeur FROM data WHERE username = ?", (username,))
    for cle, valeur in c.fetchall():
        if cle.startswith(("chat_", "budget_")):
            continue   # ces clés ne se restaurent pas (listes/widgets)
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
                    ("stade", None), ("diag_domaine", None),
                    ("projet_final", "")]:
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
                         "le commerce transfrontalier offre de bonnes marges."),
        "conseil": "Identifie un produit à forte rotation et sécurise ta chaîne d'approvisionnement avant d'investir lourd."
    },
    "Transformation agroalimentaire": {
        "opportunites": ("Transformation locale = valeur ajoutée et moins de pertes "
                         "(sésame, arachide, mangue...) ; la demande dépasse l'offre."),
        "conseil": "Commence par un produit unique maîtrisé, valide la qualité auprès de 10 clients réguliers."
    },
    "Services / Numérique": {
        "opportunites": ("Croissance rapide du mobile et du mobile money ; besoins "
                         "énormes en services digitaux pour PME."),
        "conseil": "Vends d'abord une prestation simple avant de créer un produit complexe."
    },
    "Artisanat / Mode": {
        "opportunites": ("Fierté du made in Tchad ; touristes et diaspora achètent "
                         "le local."),
        "conseil": "Travaille ton identité visuelle et documente tes créations avec de bonnes photos."
    },
    "Transport / Logistique": {
        "opportunites": ("Déplacements permanents entre N'Djamena, Moundou, Sarh ; "
                         "manque de solutions fiables de livraison."),
        "conseil": "Commence sur une seule ligne bien connue, avec un carnet de clients fidèles."
    },
    "Éducation / Formation": {
        "opportunites": ("Jeunesse majoritaire et soif d'apprentissage ; formations "
                         "professionnelles très demandées."),
        "conseil": "Teste ta méthode avec un petit groupe payant avant de louer des locaux."
    },
    "Santé / Bien-être": {
        "opportunites": ("Besoins en pharmacies de proximité, nutrition, suivi médical."),
        "conseil": "Respecte impérativement la réglementation sanitaire — la confiance est ton premier capital."
    },
    "Autre domaine": {
        "opportunites": "Chaque secteur a ses opportunités : l'étude terrain de l'Étape 1 les révèlera.",
        "conseil": "Décris précisément ton activité dans tes réponses pour un accompagnement sur mesure."
    }
}

# ---------- DIAGNOSTIC IA PAR STADE ----------
DIAGNOSTICS = {
    "idee": {
        "label": "J'ai juste une idée",
        "duree": 6,
        "analyse": ("Ton projet est au stade de l'idée brute. Le plus grand risque à ce "
                    "stade n'est pas le manque d'idées, mais l'absence de preuves de "
                    "marché. Le parcours va d'abord t'aider à comprendre précisément ton "
                    "client et son problème, avant toute dépense."),
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
        "analyse": ("Tu as déjà transformé ton idée en quelque chose de concret. "
                    "L'accompagnement va maintenant mesurer ce qui fonctionne avec de "
                    "vrais clients, corriger ce qui coince, et structurer l'offre "
                    "avant de passer au modèle économique."),
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
        "analyse": ("Ton activité existe déjà : tu as des clients et des ventes. "
                    "L'accompagnement va professionnaliser ta gestion, sécuriser tes "
                    "opérations et préparer le dossier pour accéder au financement "
                    "bancaire."),
        "forces": ["Activité réelle avec des clients",
                   "Données concrètes à analyser",
                   "Crédibilité auprès des financeurs"],
        "risques": ["Gestion informelle des finances",
                    "Formalisation juridique incomplète",
                    "Croissance limitée par le manque de fonds"],
        "questions": [
            "Quel est ton chiffre d'affaires actuel (même approximatif) ?",
            "Quelle est ta plus grande difficulté aujourd'hui ?",
            "Où veux-tu être dans 12 mois ? (objectif concret)"
        ]
    }
}

# ---------- LES 9 ÉTAPES DU PARCOURS ----------
# (inspiré d'un référentiel professionnel de coaching entrepreneurial)
ETAPES = [
    {
        "titre": "Étape 1 - Comprendre le client et le problème",
        "objectif": "Identifier qui paie, quel est son problème prioritaire et comment "
                    "il le vit au quotidien. Rien ne se construit sans cette preuve.",
        "activites": ["Définir le segment client principal (qui paie)",
                      "Réaliser des interviews terrain (besoin, fréquence, budget)",
                      "Cartographier la concurrence locale",
                      "Synthétiser les apprentissages clés"],
        "livrables": ["Fiche client : segment + douleur prioritaire",
                      "Synthèse des interviews (15-30)",
                      "3-5 hypothèses à tester"],
        "questions": [
            "Qui paie réellement : l'utilisateur, le décideur ou un tiers ?",
            "Quelle est la douleur n°1 de ton client et comment se manifeste-t-elle au quotidien ?",
            "Quelles alternatives tes clients utilisent-ils aujourd'hui et pourquoi ?"
        ]
    },
    {
        "titre": "Étape 2 - Proposition de valeur et différenciation",
        "objectif": "Exprimer clairement, en une phrase, pourquoi le client te choisit "
                    "plutôt qu'une alternative.",
        "activites": ["Formuler la proposition de valeur (pour qui / problème / solution / bénéfice)",
                      "Tester 3 messages commerciaux et recueillir les retours",
                      "Clarifier la différenciation (prix, qualité, proximité, confiance)"],
        "livrables": ["Proposition de valeur validée",
                      "3 messages testés + retours clients"],
        "questions": [
            "Si tu avais 10 secondes, que dirais-tu pour convaincre un client ?",
            "Pourquoi un client devrait-il te faire confiance ?",
            "Quel élément de ton offre est impossible à copier facilement ?"
        ]
    },
    {
        "titre": "Étape 3 - MVP / Prototype minimum viable",
        "objectif": "Passer de l'idée à une solution testable. Le MVP n'est pas parfait : "
                    "il sert à apprendre vite.",
        "activites": ["Définir le minimum de fonctions qui délivre la valeur",
                      "Organiser un test utilisateur avec critères de succès",
                      "Mesurer les retours et itérer (au moins 2 améliorations)"],
        "livrables": ["MVP démontrable",
                      "1 test utilisateur documenté",
                      "2 itérations basées sur les retours"],
        "questions": [
            "Que peux-tu tester en 48h avec les moyens actuels ?",
            "Quel est le minimum indispensable pour délivrer la valeur ?",
            "Quel critère concret rendra ton test « réussi » ?"
        ]
    },
    {
        "titre": "Étape 4 - Modèle économique et pricing",
        "objectif": "Montrer comment l'entreprise crée, délivre et capture la valeur : "
                    "revenus, coûts et marge.",
        "activites": ["Compléter le business model (clients, valeur, canaux, revenus, coûts)",
                      "Calculer le coût de revient simplifié",
                      "Fixer un prix cohérent (marché + marge + capacité à payer)"],
        "livrables": ["Business model complet à 1 page",
                      "Fiche pricing : prix, coûts, marge brute"],
        "questions": [
            "Qui paie ? Quand ? Pour quoi exactement ?",
            "Quels coûts augmentent quand tu vends plus ?",
            "Quelle marge minimale dois-tu absolument protéger ?"
        ]
    },
    {
        "titre": "Étape 5 - Go-to-market : premières ventes",
        "objectif": "Obtenir une traction commerciale. Un projet devient entreprise "
                    "quand il vend, même petit.",
        "activites": ["Choisir UN canal principal (terrain, revendeur, WhatsApp...)",
                      "Construire un pipeline : leads → rendez-vous → offre → vente",
                      "Mettre en place une routine de relance (J+2, J+7)"],
        "livrables": ["Plan commercial 30 jours",
                      "Pipeline actif avec preuves d'action",
                      "1 vente, précommande ou pilote"],
        "questions": [
            "Quel est ton canal n°1 et pourquoi celui-là ?",
            "Quelle est ta prochaine vente concrète (client, date) ?",
            "Quelle objection revient le plus souvent chez tes prospects ?"
        ]
    },
    {
        "titre": "Étape 6 - Finance : cashflow et besoin de financement",
        "objectif": "Sécuriser la trésorerie et préparer un besoin de financement crédible.",
        "activites": ["Construire un cashflow prévisionnel 12 mois",
                      "Identifier le besoin réel (montant + calendrier)",
                      "Définir l'usage des fonds et le retour attendu"],
        "livrables": ["Cashflow 12 mois validé",
                      "Besoin chiffré + usage des fonds",
                      "3 options de financement comparées"],
        "questions": [
            "Combien de cash te reste-t-il et pour combien de semaines ?",
            "Quel est le besoin minimal pour atteindre la prochaine preuve ?",
            "Que se passe-t-il si tu n'obtiens pas le financement ?"
        ]
    },
    {
        "titre": "Étape 7 - Opérations et qualité",
        "objectif": "Stabiliser la production/livraison, réduire pertes et retards, "
                    "standardiser la qualité.",
        "activites": ["Définir les procédures clés (production, vente, service)",
                      "Mettre en place un contrôle qualité basique",
                      "Suivre stocks et indicateurs opérationnels"],
        "livrables": ["Procédure simple des processus critiques",
                      "Checklist qualité + suivi des retours"],
        "questions": [
            "Où perds-tu du temps ou de l'argent dans ton processus ?",
            "Quelle étape crée le plus d'erreurs ?",
            "Que faut-il standardiser en premier ?"
        ]
    },
    {
        "titre": "Étape 8 - Administration, RH et juridique",
        "objectif": "Sécuriser les relations commerciales, réduire les litiges et "
                    "préparer la formalisation progressive.",
        "activites": ["Constituer le kit de documents essentiels",
                      "Mettre en place des modèles de contrats simples",
                      "Identifier les 10 risques majeurs et les traiter"],
        "livrables": ["Kit administratif minimal",
                      "3 modèles de contrats adaptés",
                      "Registre des risques + plan de formalisation"],
        "questions": [
            "Quel risque pourrait tuer ton activité en 30 jours ?",
            "Que dois-tu formaliser maintenant vs plus tard ?",
            "Qui signe quoi, et à quel moment ?"
        ]
    },
    {
        "titre": "Étape 9 - Pitch final et readiness financement",
        "objectif": "Être capable de convaincre des financeurs avec des preuves et "
                    "des chiffres.",
        "activites": ["Construire un pitch de 10 points, 5 minutes maximum",
                      "Préparer la session questions/réponses (objections, risques)",
                      "Assembler le dossier de financement complet"],
        "livrables": ["Pitch final",
                      "Dossier de financement complet",
                      "Liste de 10 financeurs/partenaires cibles"],
        "questions": [
            "Quelle est ta preuve la plus forte, montrable en 15 secondes ?",
            "Pourquoi toi et pas un concurrent ?",
            "Quelle est la prochaine étape mesurable après le financement ?"
        ]
    },
]


# ---------- FORMULAIRES DE TRAVAIL (1 par étape) ----------
TEMPLATES = [
    ("fiche_client_probleme.txt", """==============================================
FICHE CLIENT / PROBLÈME — Etape 1
==============================================
Porteur de projet : ..................................
Date : ..................................

1. SEGMENT CLIENT PRINCIPAL (qui paie vraiment ?)
   ..................................................

2. SEGMENT SECONDAIRE (qui influence ?)
   ..................................................

3. DOULEUR PRIORITAIRE (le probleme n°1 du client)
   ..................................................

4. CONTEXTE D'ACHAT (ou / quand / comment il achète)
   ..................................................

5. ALTERNATIVES ACTUELLES (ce qu'il fait aujourd'hui)
   ..................................................

6. BUDGET / CAPACITE A PAYER
   ..................................................

7. PREUVE RECHERCHEE (precommande / RDV / pilote ?)
   ..................................................
"""),
    ("proposition_valeur.txt", """==============================================
PROPOSITION DE VALEUR — Etape 2
==============================================
1. POUR QUI ? (segment precis)
   ..................................................

2. QUEL PROBLEME ? (en une phrase)
   ..................................................

3. QUELLE SOLUTION ?
   ..................................................

4. QUEL BENEFICE CONCRET ? (resultat mesurable)
   ..................................................

5. MESSAGE 1 A TESTER : ..................................
   Retour client : ..................................

6. MESSAGE 2 A TESTER : ..................................
   Retour client : ..................................

7. MESSAGE 3 A TESTER : ..................................
   Retour client : ..................................

8. TA DIFFERENCIATION (prix / qualite / proximite / confiance)
   ..................................................
"""),
    ("checklist_mvp.txt", """==============================================
CHECKLIST MVP + PLAN DE TEST — Etape 3
==============================================
1. FONCTIONNALITE MINIMUM DU MVP
   ..................................................

2. TEST A REALISER (quoi, exactement ?)
   ..................................................

3. AVEC QUI ? (segment teste)
   ..................................................

4. CRITERE DE SUCCES (mesurable)
   ..................................................

5. DATE / LIEU DU TEST
   ..................................................

6. RETOURS CLES RECUEILLIS
   ..................................................

7. ITERATION n°1 (amélioration appliquée)
   ..................................................

8. ITERATION n°2
   ..................................................
"""),
    ("business_model_pricing.txt", """==============================================
BUSINESS MODEL + PRICING — Etape 4
==============================================
SEGMENTS CLIENTS : ..................................
PROPOSITION DE VALEUR : ..................................
CANAUX DE VENTE : ..................................
SOURCE DE REVENUS : ..................................

COUTS DIRECTS (par unité vendue) :
  Matiere / achat : .......... FCFA
  Transport : .......... FCFA
  Main d'oeuvre : .......... FCFA
  Autres : .......... FCFA
  TOTAL DIRECTS : .......... FCFA

PRIX DE VENTE : .......... FCFA
MARGE BRUTE : .......... FCFA (prix - coûts)

COMMENTAIRE (prix du marché / capacité à payer) :
   ..................................................
"""),
    ("pipeline_ventes.txt", """==============================================
PIPELINE VENTES — Etape 5
==============================================
Canal principal choisi : ..................................
Objectif 30 jours : .......... leads

LEAD/CLIENT | CANAL | STATUT(Lead/RDV/Offre/Vente) | PROCHAINE ACTION | DATE
............|.......|...............................|..................|.....
............|.......|...............................|..................|.....
............|.......|...............................|..................|.....
............|.......|...............................|..................|.....

VENTE / PRECOMMANDE / PILOTE OBTENU ?
   ..................................................

OBJECTION LA PLUS FREQUENTE + TA REPONSE :
   ..................................................
"""),
    ("cashflow_12mois.txt", """==============================================
CASHFLOW 12 MOIS + BESOIN — Etape 6
==============================================
MOIS | ENTREES | SORTIES | SOLDE | COMMENTAIRES
M1   | ..........|..........|.......|..............
M2   | ..........|..........|.......|..............
M3   | ..........|..........|.......|..............
(suite jusqu'à M12)

CASH DISPONIBLE ACTUEL : .......... FCFA
AUTONOMIE (semaines) : ..........

BESOIN DE FINANCEMENT : .......... FCFA
USAGE DES FONDS (poste par poste) :
  ..................................................
OPTION 1 (subvention/concours) : ..................................
OPTION 2 (prêt microfinance/banque) : ..................................
OPTION 3 (partenariat/précommande) : ..................................
"""),
    ("operations_qualite.txt", """==============================================
OPERATIONS & QUALITE — Etape 7
==============================================
PROCESSUS CRITIQUE n°1 : ..................................
  Étape 1 : .......... Responsable : .......... Délai : ....
  Étape 2 : .......... Responsable : .......... Délai : ....
  Contrôle qualité : ..................................

PROCESSUS CRITIQUE n°2 : ..................................
  ..................................................

CHECKLIST QUALITE (5 points minimum) :
  [ ] ..................................
  [ ] ..................................
  [ ] ..................................

INDICATEURS SUIVIS (délais, retours, pertes) :
   ..................................................

OÙ PERDS-TU DU TEMPS / ARGENT ?
   ..................................................
"""),
    ("kit_admin_juridique.txt", """==============================================
KIT ADMIN / JURIDIQUE / RISQUES — Etape 8
==============================================
DOCUMENTS DISPONIBLES (ventes, dépenses, inventaire...) :
   ..................................................

CONTRAT DE VENTE (éléments prévus) :
   ..................................................

CONTRAT DE PRESTATION : ..................................
CONTRAT DE PARTENARIAT : ..................................

RISQUES MAJEURS (Top 10) :
  1. ......................... Parade : .........................
  2. ......................... Parade : .........................
  3. ......................... Parade : .........................

FORMALISATION : que faire MAINTENANT ? plus tard ?
   Maintenant : ..................................
   Plus tard : ..................................
"""),
    ("pitch_financement.txt", """==============================================
PITCH & DOSSIER DE FINANCEMENT — Etape 9
==============================================
1. PROBLÈME (avec preuve terrain) :
   ..................................................
2. CLIENT CIBLE :
   ..................................................
3. SOLUTION (MVP) :
   ..................................................
4. PROPOSITION DE VALEUR :
   ..................................................
5. MARCHÉ & CONCURRENCE :
   ..................................................
6. MODÈLE ÉCONOMIQUE (revenus + coûts) :
   ..................................................
7. TRACTION (ventes / pilotes / pipeline) :
   ..................................................
8. STRATÉGIE COMMERCIALE (canaux) :
   ..................................................
9. ÉQUIPE (rôles) :
   ..................................................
10. BESOIN DE FINANCEMENT + usage des fonds :
   ..................................................

10 FINANCEURS / PARTENAIRES CIBLÉS :
   1. ................. 2. ................. 3. .................
"""),
]

# ---------- COACH IA GÉNÉRATIVE (Gemini) ----------
PROMPT_COACH = """
Tu es "Coach IA", le mentor principal d'un incubateur d'entreprises numérique
au Tchad, reconnu comme LA référence des entrepreneurs tchadiens. Tu appliques
une méthode de coaching professionnelle : questionnement socratique (tu ne donnes
pas la solution toute cuite, tu fais réfléchir), écoute active, posture de miroir
critique bienveillant, et exigence sur les preuves terrain.

POUR CHAQUE RÉPONSE DE L'ENTREPRENEUR, STRUCTURE OBLIGATOIRE :
🔎 **Analyse logique** : ce qui est solide dans sa réponse + ce qui manque ou
   reste vague (sois précis, cite ses propres mots).
🧭 **Coaching** : un conseil concret et adapté au contexte tchadien (marchés,
   mobile money, saisonnalité, réalités locales).
✅ **Action de la semaine** : une seule action concrète, faisable, mesurable.
❓ **Question de suivi** : une question ouverte qui le fait progresser.

RÈGLES : français simple, encourageant mais exigeant ; 150-250 mots maximum ;
jamais condescendant ; tu connais son stade, son domaine et son étape en cours
et tu t'y adaptes ; si la question sort du cadre, réponds brièvement et recadre.
"""

def reponse_ia_genai(message, contexte):
    if not GENAI_OK:
        return None
    try:
        cle = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None
    try:
        genai.configure(api_key=cle)
        model = genai.GenerativeModel("gemini-1.5-flash",
                                      system_instruction=PROMPT_COACH)
        question_complete = (f"CONTEXTE DE L'ENTREPRENEUR :\n{contexte}\n\n"
                             f"SON MESSAGE :\n{message}")
        reponse = model.generate_content(question_complete)
        return reponse.text
    except Exception:
        return None

# ---------- MOTEUR DE SECOURS (par mots-clés) ----------
REGLES_IA = [
    (["argent", "finance", "fonds", "capital", "prêt", "pret", "budget",
      "fcfa", "coût", "cout", "cash", "trésorerie", "tresorerie"],
     "💰 **Analyse :** ta préoccupation financière est légitime — c'est le nerf de "
     "la guerre.\n🧭 **Coaching :** commence avec le minimum viable. Liste tes 3 "
     "dépenses indispensables, coupe le reste. Options au Tchad : tontine, "
     "microfinance, concours d'entrepreneuriat, puis banques quand le dossier est prêt.\n"
     "✅ **Action :** note aujourd'hui ton besoin minimal en FCFA et son usage précis.\n"
     "❓ **Question :** quelle dépense peut attendre 3 mois ?"),

    (["client", "vente", "vendre", "marché", "marche", "acheter", "demande", "pipeline"],
     "🎯 **Analyse :** sans ventes, pas d'entreprise — ta priorité est juste.\n"
     "🧭 **Coaching :** choisis UN canal prioritaire et maîtrise-le avant d'en ajouter. "
     "La prévente valide ton marché sans investir.\n"
     "✅ **Action :** contacte 5 clients potentiels cette semaine, note leurs réponses.\n"
     "❓ **Question :** quelle objection revient le plus souvent ?"),

    (["peur", "stress", "échouer", "echouer", "risque", "oser", "confiance",
      "doute", "incapable", "imposteur"],
     "💛 **Analyse :** ce doute est partagé par tous les entrepreneurs — il est un "
     "signe de sérieux, pas de faiblesse.\n🧭 **Coaching :** réduis le risque : "
     "teste petit, apprends vite, répète.\n"
     "✅ **Action :** célèbre aujourd'hui UNE petite victoire déjà accomplie.\n"
     "❓ **Question :** quelle est la pire chose réaliste qui puisse arriver, et "
     "comment t'y prépares-tu ?"),

    (["temps", "occupé", "emploi", "horaire", "disponible"],
     "⏰ **Analyse :** le temps est une ressource, pas une excuse.\n"
     "🧭 **Coaching :** 1h concentrée par jour sur UNE action suffit à faire "
     "décoller un projet.\n"
     "✅ **Action :** bloque un créneau quotidien fixe (ex: 19h-20h) dans ton agenda.\n"
     "❓ **Question :** quelle activité de ta journée peux-tu réduire de 30 min ?"),

    (["famille", "entourage", "conjoint", "mari", "parents", "amis"],
     "👨‍👩‍👧 **Analyse :** le soutien de l'entourage conditionne souvent la "
     "persévérance.\n🧭 **Coaching :** convaincs par les résultats visibles, "
     "pas par les mots. Implique un proche dans une tâche concrète.\n"
     "✅ **Action :** partage avec ta famille UNE victoire récente du projet.\n"
     "❓ **Question :** qui dans ton entourage pourrait devenir ton premier allié ?"),

    (["papier", "formalité", "formalités", "rccm", "impôt", "impot",
      "administration", "statut", "legal", "légal", "contrat"],
     "📄 **Analyse :** formaliser tôt protège l'activité et ouvre l'accès aux "
     "financements.\n🧭 **Coaching :** au Tchad : RCCM + NIF = compte bancaire, "
     "factures, crédibilité. Avance par étapes selon tes moyens.\n"
     "✅ **Action :** liste les 3 documents à préparer pour ton immatriculation.\n"
     "❓ **Question :** quelle formalisation peux-tu faire dès ce mois-ci ?"),

    (["concurrence", "concurrent", "déjà", "deja", "copier", "copie"],
     "⚔️ **Analyse :** la concurrence prouve que le marché existe.\n"
     "🧭 **Coaching :** analyse 2-3 concurrents : leurs forces, leurs négligences — "
     "c'est là que tu gagneras.\n"
     "✅ **Action :** compare aujourd'hui ton prix à celui de 2 concurrents.\n"
     "❓ **Question :** qu'offres-tu qu'ils ne peuvent pas copier facilement ?"),
]

REPONSE_DEFAUT = (
    "🤔 **Analyse :** ta réponse mérite qu'on creuse ensemble.\n"
    "🧭 **Coaching :** détaille un peu plus : parle d'argent, de clients, de "
    "temps, d'équipe ou de formalités — je pourrai te guider précisément.\n"
    "✅ **Action :** reformule ta préoccupation en une question précise.\n"
    "❓ **Question :** qu'est-ce qui te bloque le plus en ce moment ?")

def reponse_ia(message, titre_etape):
    texte = message.lower()
    for mots_clefs, reponse in REGLES_IA:
        if any(mot in texte for mot in mots_clefs):
            return reponse + f"\n\n📌 *(Étape : {titre_etape})*"
    return REPONSE_DEFAUT + f"\n\n📌 *(Étape : {titre_etape})*"

def construire_contexte(titre_etape):
    stade = st.session_state.get("stade")
    label_stade = DIAGNOSTICS.get(stade, {}).get("label", "non précisé")
    domaine = st.session_state.get("diag_domaine") or "non précisé"
    duree = st.session_state.get("duree", 0)
    r1 = st.session_state.get("diag_0", "—")
    r2 = st.session_state.get("diag_1", "—")
    return (f"Prénom : {st.session_state.get('prenom', 'entrepreneur')}\n"
            f"Stade du projet : {label_stade} (parcours de {duree} mois)\n"
            f"Domaine d'activité : {domaine}\n"
            f"Étape en cours : {titre_etape}\n"
            f"Diagnostic : problème = {r1} | clients visés = {r2}")

def envoyer_message(i, j, titre_etape):
    """Envoie le message : IA générative d'abord, moteur de secours ensuite.
    Conserve aussi les réponses de l'entrepreneur pour le projet final."""
    cle_champ = f"q_{i}_{j}"
    cle_chat = f"chat_{i}_{j}"
    message = st.session_state.get(cle_champ, "").strip()
    if message:
        contexte = construire_contexte(titre_etape)
        formulaire = st.session_state.get(f"form_{i}", "")
        if formulaire:
            contexte += "\nFormulaire rempli de l'étape :\n" + formulaire[:800]
        reponse = reponse_ia_genai(message, contexte)
        if reponse is None:
            reponse = reponse_ia(message, titre_etape)
            reponse += "\n\n_⚙️ (Mode hors-ligne : branche la clé Gemini pour le coach complet)_"
        st.session_state.setdefault(cle_chat, []).append((message, reponse))
        # accumulation des réponses de l'entrepreneur pour le projet final
        ancien = st.session_state.get(f"synthese_{i}", "")
        st.session_state[f"synthese_{i}"] = (ancien + "\n- " + message).strip()
        st.session_state[cle_champ] = ""


def analyser_formulaire(i):
    """Le coach IA analyse le formulaire rempli et oriente l'entrepreneur."""
    contenu = st.session_state.get(f"form_{i}", "")
    if not contenu:
        return
    titre = ETAPES[i]["titre"]
    prompt = (
        "Tu es le coach d'un incubateur d'entreprises au Tchad. L'entrepreneur "
        f"({st.session_state.get('prenom', '')}, domaine : "
        f"{st.session_state.get('diag_domaine', '')}) a rempli le formulaire de "
        f"l'étape « {titre} ». Voici son formulaire :\n\n"
        f"{contenu}\n\n"
        "Fais une analyse structurée et bienveillante (200-300 mots max) :\n"
        "✅ Points solides du formulaire (cite ses propres mots)\n"
        "⚠️ Lacunes ou zones vagues à combler\n"
        "🧭 Orientation prioritaire : sur quoi se concentrer maintenant\n"
        "❓ 2-3 questions à creuser en séance de coaching\n"
        "Adapte-toi au contexte tchadien, sois exigeant mais encourageant.")
    resultat = None
    if GENAI_OK:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            resultat = model.generate_content(prompt).text
        except Exception:
            resultat = None
    if resultat is None:
        resultat = ("⚠️ _Analyse IA indisponible (mode hors-ligne). En attendant, "
                    "vérifie : chaque champ est-il rempli ? Chaque chiffre est-il "
                    "justifié ? Un collègue pourrait-il comprendre ton formulaire "
                    "sans t'expliquer ? Relance l'analyse quand l'IA est branchée._")
    st.session_state[f"analyse_{i}"] = resultat
    # L'analyse enrichit aussi le contexte des prochains échanges coaching
    st.session_state[f"synthese_{i}"] = (
        st.session_state.get(f"synthese_{i}", "") +
        f"\n[Formulaire rempli]\n{contenu[:500]}").strip()


def generer_guide(i, j, activite):
    """Le coach IA génère un mini-guide 'comment faire' pour l'activité."""
    stade = st.session_state.get("stade")
    label_stade = DIAGNOSTICS.get(stade, {}).get("label", "non précisé")
    prompt = (
        "Tu es le coach d'un incubateur d'entreprises au Tchad. Un entrepreneur "
        f"({st.session_state.get('prenom', '')}, stade : {label_stade}, domaine : "
        f"{st.session_state.get('diag_domaine', '')}) doit réaliser cette activité "
        f"du parcours : « {activite} ».\n"
        "Rédige un MINI-GUIDE pratique (120 mots max, en français simple) :\n"
        "1️⃣ La méthode en 4-5 étapes concrètes\n"
        "2️⃣ Un exemple concret adapté au contexte tchadien\n"
        "3️⃣ Le piège principal à éviter\n"
        "Va droit au but, ton entrepreneur veut AGIR.")
    resultat = None
    if GENAI_OK:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-flash")
            resultat = model.generate_content(prompt).text
        except Exception:
            resultat = None
    if resultat is None:
        resultat = ("💡 _Guide indisponible (mode hors-ligne). Méthode générale : "
                    "découpe l'activité en petites actions, fais la première "
                    "aujourd'hui, note ce que tu observes, puis partage tes "
                    "résultats au coach pour un retour personnalisé._")
    st.session_state[f"guide_{i}_{j}"] = resultat

# ---------- FORMULES ----------
FORMULES = {
    "1 mois - 5 000 F": "5 000 F",
    "3 mois - 12 500 F": "12 500 F",
    "6 mois - 22 500 F": "22 500 F",
    "1 an - 42 500 F": "42 500 F",
}

PAGES = ["🏠 Accueil", "🎯 Diagnostic", "💰 Abonnement",
         "🗺️ Mon parcours", "📜 Projet final & Attestation"]

POSTES_BUDGET = ["Équipement / Matériel", "Stock / Matière première",
                 "Marketing / Communication", "Formalisation juridique",
                 "Formation", "Trésorerie de sécurité"]

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
    st.markdown("""
    <div class="hero">
        <span class="badge">🇹🇩 100% en ligne — Accessible partout au Tchad</span>
        <h1>🚀 Incubateur IA Tchad</h1>
        <p>De l'idée à l'entreprise bancable : un coach IA professionnel,
        un parcours structuré en 9 étapes, et une attestation à la clé.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="carte carte-or"><h4>🤖 Coach IA</h4>
        <p>Un mentor qui analyse chacune de tes réponses et te pousse
        vers l'action.</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="carte carte-vert"><h4>🗺️ 9 étapes</h4>
        <p>Un parcours professionnel : du client à financer, jusqu'au
        dossier bancable.</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="carte carte-rouge"><h4>📜 Attestation</h4>
        <p>À la fin : ton projet budgétisé + une attestation nominative
        téléchargeable.</p></div>""", unsafe_allow_html=True)

    st.divider()
    langue = st.selectbox("🌐 Langue / اللغة", ["fr", "ar"])
    st.session_state.langue = langue

    st.markdown(f"### {T['bienvenue'][langue]}")
    st.write(T["objectif"][langue])

    prenom = st.text_input("✍️ Ton prénom", value=st.session_state.prenom)
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

**➡️ Prochaine étape recommandée :** l'Étape 1 de ton parcours —
« Comprendre le client et le problème ».
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
        st.caption("💡 Pour chaque étape : lis l'objectif, discute avec le coach IA "
                   "(obligatoire), puis valide l'étape. À la fin : ton projet "
                   "bancable complet + attestation.")

        validees = sum(1 for i in range(len(ETAPES))
                       if st.session_state.get(f"etape_{i}", False))
        st.progress(validees / len(ETAPES))
        st.caption(f"Progression : {validees} / {len(ETAPES)} étapes validées")

        for i, etape in enumerate(ETAPES):
            nb_echanges = sum(len(st.session_state.get(f"chat_{i}_{j}", []))
                              for j in range(len(etape["activites"])))
            a_discute = nb_echanges >= 1
            titre = etape["titre"] + (" ✅" if st.session_state.get(f"etape_{i}") else "")
            with st.expander(f"**{titre}**"):
                st.markdown(f"**🎯 Objectif :** {etape['objectif']}")
                st.markdown("**🛠️ Activités clés :**")
                for a in etape["activites"]:
                    st.markdown(f"- {a}")
                st.markdown("**📦 Livrables attendus :**")
                for l in etape["livrables"]:
                    st.markdown(f"- {l}")

                st.divider()
                st.markdown("**🤖 Atelier guidé : réalise chaque activité avec ton coach**")
                st.caption("Pour chaque activité : 1) lis le guide du coach — "
                           "2) exécute sur le terrain — 3) partage ton résultat — "
                           "4) applique ses conseils.")

                for j, activite in enumerate(etape["activites"]):
                    st.markdown(f"**🛠️ Activité {j + 1} : {activite}**")
                    if st.button("💡 Comment faire ?", key=f"gd_{i}_{j}",
                                 on_click=generer_guide, args=(i, j, activite)):
                        pass
                    if st.session_state.get(f"guide_{i}_{j}"):
                        st.info(st.session_state[f"guide_{i}_{j}"])
                    st.text_input("Ton résultat ou ta question :",
                                  key=f"q_{i}_{j}",
                                  placeholder="Écris ce que tu as fait ou trouvé...")
                    st.button("📩 Envoyer au coach",
                              key=f"btn_{i}_{j}",
                              on_click=envoyer_message,
                              args=(i, j, activite))
                    for question_posee, reponse in st.session_state.get(
                            f"chat_{i}_{j}", []):
                        st.markdown(f"> **Toi :** {question_posee}")
                        st.markdown(reponse)

                st.divider()
                st.markdown("**📄 Formulaire de travail à remplir**")
                st.caption("1. Télécharge le formulaire — 2. Remplis-le — "
                           "3. Re-dépose-le ici — 4. Demande l'analyse du coach")
                nom_fichier, contenu_template = TEMPLATES[i]
                st.download_button("⬇️ Télécharger le formulaire",
                                   data=contenu_template,
                                   file_name=nom_fichier,
                                   mime="text/plain",
                                   key=f"dl_{i}")
                fichier = st.file_uploader("Dépose ton formulaire rempli "
                                           "(.txt ou .md)", type=["txt", "md"],
                                           key=f"up_{i}")
                if fichier is not None:
                    try:
                        texte = fichier.getvalue().decode("utf-8", errors="ignore")
                        st.session_state[f"form_{i}"] = texte
                        st.success(f"✅ « {fichier.name} » reçu !")
                        with st.expander("Aperçu du formulaire reçu"):
                            st.text(texte[:600])
                        if st.button("🤖 Analyser mon formulaire",
                                     key=f"ana_{i}",
                                     on_click=analyser_formulaire,
                                     args=(i,)):
                            pass
                    except Exception:
                        st.error("Format illisible. Enregistre ton formulaire "
                                 "en .txt et re-dépose-le.")

                if st.session_state.get(f"analyse_{i}"):
                    st.markdown("**🧑‍🏫 Analyse de ton coach :**")
                    st.markdown(st.session_state[f"analyse_{i}"])

                st.divider()
                if a_discute:
                    cochee = st.checkbox("✅ Je valide cette étape (après coaching)",
                                         key=f"etape_{i}")
                else:
                    st.info("🔒 Discute d'abord avec le coach IA (envoie au moins "
                            "un message) pour pouvoir valider cette étape.")

    boutons_navigation(index_page)

elif page == "📜 Projet final & Attestation":
    st.title("📜 Projet final, budget et attestation")
    st.write("Cette page se débloque à la **fin de ton incubation**, quand les "
             "9 étapes du parcours sont validées.")

    manquantes = [ETAPES[i]["titre"] for i in range(len(ETAPES))
                  if not st.session_state.get(f"etape_{i}", False)]

    if manquantes:
        st.warning(f"⏳ Il te reste **{len(manquantes)} étape(s)** à valider :")
        for m in manquantes:
            st.markdown(f"- {m}")
    else:
        st.success("🎉 Incubation terminée ! Génère ton projet bancable complet.")

        # ---- 1. PROJET BANCABLE GÉNÉRÉ PAR L'IA ----
        st.subheader("1️⃣ Ton projet bancable complet")
        if st.button("🤖 Générer mon dossier avec l'IA", type="primary"):
            contexte = (f"Porteur : {st.session_state.prenom} | Domaine : "
                        f"{st.session_state.diag_domaine} | Stade : "
                        f"{DIAGNOSTICS.get(st.session_state.stade, {}).get('label', '')}\n")
            for i, etape in enumerate(ETAPES):
                contexte += (f"\n### {etape['titre']}\n"
                             f"{st.session_state.get(f'synthese_{i}', '—')}\n")
            prompt_final = (
                "Tu es un expert en dossiers bancaires pour entrepreneurs au Tchad. "
                "À partir des éléments de l'entrepreneur ci-dessous, rédige son "
                "DOSSIER BANCABLE COMPLET, structuré ainsi :\n"
                "1. Résumé du projet (1 paragraphe percutant)\n"
                "2. Le problème et les clients (preuves terrain)\n"
                "3. Proposition de valeur et différenciation\n"
                "4. Modèle économique (revenus, coûts, marge)\n"
                "5. Stratégie commerciale et traction\n"
                "6. Besoin de financement + usage des fonds\n"
                "7. Plan de remboursement et risques\n"
                "8. Les 3 prochaines étapes mesurables\n"
                "Sois concret, chiffré quand possible, adapté au contexte tchadien. "
                "Maximum 600 mots.\n\nÉLÉMENTS DE L'ENTREPRENEUR :\n" + contexte)
            doc = None
            if GENAI_OK:
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    doc = model.generate_content(prompt_final).text
                except Exception:
                    doc = None
            if doc is None:
                doc = ("⚠️ IA non disponible. Voici ton dossier à compléter avec "
                       "les réponses que tu as données dans chaque étape :\n\n"
                       + contexte.replace("###", "**").replace("\n- ", "\n- "))
            st.session_state.projet_final = doc

        if st.session_state.projet_final:
            st.markdown(st.session_state.projet_final)

        st.divider()

        # ---- 2. BUDGET PRÉVISIONNEL ----
        st.subheader("2️⃣ Budget prévisionnel de lancement")
        st.caption("Estime chaque poste en FCFA — sois prudent, c'est ce que "
                   "les financeurs liront.")
        total_budget = 0
        cols = st.columns(2)
        for k, poste in enumerate(POSTES_BUDGET):
            with cols[k % 2]:
                montant = st.number_input(poste, min_value=0, step=5000,
                                          key=f"budget_{k}")
                total_budget += montant
        st.metric("💰 TOTAL du budget de lancement", f"{total_budget:,} FCFA".replace(",", " "))

        st.divider()

        # ---- 3. ATTESTATION ----
        st.subheader("3️⃣ Ton attestation")
        date_jour = datetime.date.today().strftime("%d/%m/%Y")
        st.markdown(f"""
---
<div style="border:3px solid #1a5276; border-radius:12px; padding:25px; text-align:center; background-color:#fdfbf7;">

# 📜 ATTESTATION DE FIN D'INCUBATION

## Incubateur IA — Tchad 🇹🇩

<br>

Nous attestons que

# {st.session_state.prenom}

a suivi avec succès le **parcours complet d'incubation entrepreneurial** de
**{st.session_state.duree} mois** (9 étapes, coaching IA inclus), et a produit un
**projet structuré, budgétisé ({total_budget:,} FCFA) et bancable**.

Domaine d'activité : {st.session_state.diag_domaine}

Fait le {date_jour}

🤖 _Coach IA — Incubateur IA Tchad_

</div>
""".replace(",", " "), unsafe_allow_html=True)

        texte_attestation = (
            f"ATTESTATION DE FIN D'INCUBATION\n"
            f"Incubateur IA - Tchad\n\n"
            f"Nous attestons que {st.session_state.prenom} a suivi avec succès le "
            f"parcours complet d'incubation entrepreneurial de {st.session_state.duree} "
            f"mois (9 étapes, coaching IA inclus), et a produit un projet structuré, "
            f"budgétisé ({total_budget} FCFA) et bancable.\n"
            f"Domaine d'activité : {st.session_state.diag_domaine}\n"
            f"Fait le {date_jour}.\nCoach IA - Incubateur IA Tchad")
        st.download_button("⬇️ Télécharger mon attestation",
                           data=texte_attestation,
                           file_name="attestation_incubation.txt",
                           mime="text/plain")

st.markdown("---")
st.markdown('<div class="pied">🚀 Incubateur IA Tchad — © 2026 — '
            'Fait avec ❤️ pour les entrepreneurs tchadiens<br>'
            '📱 Moov +235 98 28 25 52 · Airtel +235 62 11 62 78</div>',
            unsafe_allow_html=True)

sauvegarder(st.session_state.user)
