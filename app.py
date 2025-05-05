import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO

st.set_page_config(page_title="Détection des Doublons d'Utilisateurs", layout="wide")
st.title("🔍 Détection des Doublons d'Utilisateurs dans DHIS2")

# === Connexion DHIS2 ===
st.sidebar.header("🔑 Connexion DHIS2")
token = st.sidebar.text_input("Token d'accès personnel (PAT)", type="password")
username = st.sidebar.text_input("Nom d'utilisateur", type="default")
password = st.sidebar.text_input("Mot de passe", type="password")

# === Authentification ===
def get_auth_header(token=None, username=None, password=None):
    if token:
        return {"Authorization": f"Bearer {token}"}
    elif username and password:
        auth_str = f"{username}:{password}"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {"Authorization": f"Basic {auth_b64}"}
    else:
        return {}

# === Récupération des unités d'organisation ===
def get_org_units(headers):
    url = "https://togo.dhis2.org/dhis/api/organisationUnits.json"
    params = {"paging": "false", "fields": "id,name"}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json().get("organisationUnits", [])
            return {ou["id"]: ou["name"] for ou in data}
        else:
            st.error(f"Erreur {response.status_code} lors de l'accès aux unités d'organisation.")
            return {}
    except Exception as e:
        st.error(f"Exception lors de la récupération des unités d'organisation : {e}")
        return {}

# === Récupération des utilisateurs ===
def get_users(headers):
    url = "https://togo.dhis2.org/dhis/api/users.json"
    params = {"paging": "false", "fields": "id,username,name,organisationUnits[id]"}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("users", [])
    else:
        st.error("Erreur lors de la récupération des utilisateurs depuis DHIS2.")
        return []

# === Traitement principal ===
if (username or token) and (password or token):
    headers = get_auth_header(token=token, username=username, password=password)
    
    users = get_users(headers)
    org_unit_dict = get_org_units(headers)

    if users:
        df_users = pd.DataFrame(users)
        
        # Extraire les IDs des unités d'organisation
        df_users['orgUnits'] = df_users['organisationUnits'].apply(
            lambda units: [ou['id'] for ou in units] if isinstance(units, list) else []
        )

        # Ajouter les noms des unités d'organisation
        df_users['Nom unités d\'organisation'] = df_users['orgUnits'].apply(
            lambda ids: ', '.join([org_unit_dict.get(ou_id, ou_id) for ou_id in ids])
        )

        # Détection des doublons par nom complet
        df_users['doublon'] = df_users.duplicated(subset='name', keep=False)
        df_users['doublon'] = df_users['doublon'].apply(lambda x: "Oui" if x else "Non")

        # Sélection des colonnes finales
        df_users = df_users[['id', 'username', 'name', 'Nom unités d\'organisation', 'doublon']]

        st.success(f"✅ {len(df_users)} utilisateurs trouvés.")
        st.dataframe(df_users, use_container_width=True)

        # Téléchargement CSV
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
