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

# === Fonction d'authentification ===
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

# === Récupération des unités d’organisation ===
def get_org_units(headers):
    url = "https://togo.dhis2.org/dhis/api/organisationUnits.json"
    params = {"paging": "false", "fields": "id,name"}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        data = r.json().get("organisationUnits", [])
        return {ou["id"]: ou["name"] for ou in data}
    else:
        st.error("❌ Erreur lors de la récupération des unités d'organisation.")
        return {}

# === Récupération des utilisateurs ===
def get_users(headers, org_unit_dict):
    url = "https://togo.dhis2.org/dhis/api/users.json"
    params = {"paging": "false", "fields": "id,username,name,organisationUnits[id]"}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        st.error("❌ Erreur lors de la récupération des utilisateurs depuis DHIS2.")
        return []

    users_raw = response.json().get("users", [])
    users = []
    for user in users_raw:
        ou_ids = [ou["id"] for ou in user.get("organisationUnits", [])]
        ou_labels = [f'{ou_id} - {org_unit_dict.get(ou_id, "Nom inconnu")}' for ou_id in ou_ids]
        users.append({
            "ID": user["id"],
            "Nom d'utilisateur": user["username"],
            "Nom complet": user["name"],
            "Unités d'organisation (ID - Nom)": "; ".join(ou_labels)
        })
    return users

# === Traitement principal ===
if (username or token) and (password or token):
    headers = get_auth_header(token=token, username=username, password=password)
    org_unit_dict = get_org_units(headers)
    users = get_users(headers, org_unit_dict)

    if users:
        df_users = pd.DataFrame(users)

        # Détecter les doublons par nom complet
        df_users['Doublon'] = df_users.duplicated(subset='Nom complet', keep=False).map({True: "Oui", False: "Non"})

        st.success(f"✅ {len(df_users)} utilisateurs trouvés.")
        st.dataframe(df_users, use_container_width=True)

        # Export CSV
        csv = df_users.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les utilisateurs (avec doublons) CSV",
            data=csv,
            file_name="utilisateurs_dhis2.csv",
            mime="text/csv"
        )
    else:
        st.warning("Aucun utilisateur trouvé.")
else:
    st.info("Veuillez entrer vos identifiants ou votre token d'accès pour vous connecter.")
