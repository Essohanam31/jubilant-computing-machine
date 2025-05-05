import streamlit as st
import pandas as pd
import requests
import base64
from collections import defaultdict
from io import BytesIO

st.set_page_config(page_title="Détection des Doublons d'Utilisateurs", layout="wide")
st.title("🔍 Détection des Doublons d'Utilisateurs dans DHIS2")

# === Étape 1 : Saisie des identifiants DHIS2 ===
st.sidebar.header("🔑 Connexion DHIS2")
token = st.sidebar.text_input("Token d'accès personnel (PAT)", type="password")
username = st.sidebar.text_input("Nom d'utilisateur", type="default")
password = st.sidebar.text_input("Mot de passe", type="password")

# Fonction pour obtenir les en-têtes d'authentification
def get_auth_header(token=None, username=None, password=None):
    if token:
        # Utilisation du token personnel (PAT) pour l'authentification
        return {"Authorization": f"Bearer {token}"}
    elif username and password:
        # Authentification avec nom d'utilisateur et mot de passe
        auth_str = f"{username}:{password}"
        auth_bytes = auth_str.encode("utf-8")  # Encodage UTF-8
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {"Authorization": f"Basic {auth_b64}"}
    else:
        return {}

# === Étape 2 : Récupérer tous les utilisateurs ===
def get_users(headers):
    url = "https://togo.dhis2.org/dhis/api/users.json"
    params = {"paging": "false", "fields": "id,username,name,organisationUnits[id]"}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("users", [])
    else:
        st.error("Erreur lors de la récupération des utilisateurs depuis DHIS2.")
        return []

# === Étape 3 : Afficher les utilisateurs et détecter les doublons ===
if (username or token) and (password or token):
    headers = get_auth_header(token=token, username=username, password=password)
    users = get_users(headers)

    if users:
        # Créer un DataFrame des utilisateurs
        df_users = pd.DataFrame(users)
        df_users = df_users[['id', 'username', 'name']]  # Colonnes à afficher

        # Détecter les doublons (par nom d'utilisateur)
        df_users['doublon'] = df_users.duplicated(subset='name', keep=False)
        df_users['doublon'] = df_users['doublon'].apply(lambda x: "Oui" if x else "Non")

        st.success(f"✅ {len(df_users)} utilisateurs trouvés.")
        st.dataframe(df_users, use_container_width=True)

        # Télécharger le fichier CSV
        csv = df_users.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les doublons détectés (CSV)",
            data=csv,
            file_name="doublons_utilisateurs.csv",
            mime="text/csv"
        )
    else:
        st.warning("Aucun utilisateur trouvé.")
else:
    st.info("Veuillez entrer vos identifiants ou votre token d'accès pour vous connecter.")
