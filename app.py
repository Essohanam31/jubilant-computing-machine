# -*- coding: utf-8 -*-
# Streamlit – Liste complète des utilisateurs DHIS2 avec identification des doublons

import streamlit as st
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Liste des utilisateurs DHIS2", layout="wide")

# URL DHIS2 préconfigurée
DHIS2_URL = "https://ton_instance.dhis2.org/dhis"  # À modifier avec l'URL de ton instance

st.sidebar.header("🔐 Connexion à DHIS2")

auth_method = st.sidebar.radio("Méthode d’authentification", ["Nom d'utilisateur / Mot de passe", "Token personnel (PAT)"])

if auth_method == "Nom d'utilisateur / Mot de passe":
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    token = None
else:
    token = st.sidebar.text_input("Token personnel (PAT)", type="password")
    username = None
    password = None

@st.cache_data(show_spinner=False)
def get_auth_header(username=None, password=None, token=None):
    if token:
        return {"Authorization": f"ApiToken {token}"}
    else:
        auth = f"{username}:{password}"
        encoded = base64.b64encode(auth.encode()).decode("utf-8")
        return {"Authorization": f"Basic {encoded}"}

@st.cache_data(show_spinner=False)
def get_users(headers):
    url = f"{DHIS2_URL}/api/users.json"
    params = {
        "paging": "false",
        "fields": "id,username,name,organisationUnits[id,name],userCredentials[userRoles[name]]"
    }
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json().get("users", [])
    else:
        st.error("❌ Erreur lors de la récupération des utilisateurs.")
        return []

if (username and password) or token:
    headers = get_auth_header(username, password, token)

    if st.sidebar.button("📥 Charger tous les utilisateurs"):
        users = get_users(headers)
        if users:
            rows = []
            for user in users:
                name = user.get("name")
                username = user.get("username")
                orgs = [ou["name"] for ou in user.get("organisationUnits", [])]
                roles = [r["name"] for r in user.get("userCredentials", {}).get("userRoles", [])]
                rows.append({
                    "name": name,
                    "username": username,
                    "organisation": ", ".join(orgs),
                    "roles": ", ".join(roles)
                })

            df = pd.DataFrame(rows)

            # Détection des doublons (par nom)
            df["doublon"] = df.duplicated(subset="name", keep=False).apply(lambda x: "Oui" if x else "Non")

            st.success(f"✅ {len(df)} utilisateurs trouvés (dont {df['doublon'].value_counts().get('Oui', 0)} doublons).")
            st.dataframe(df, use_container_width=True)

            # Bouton de téléchargement
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📄 Télécharger la liste complète (CSV)",
                data=csv,
                file_name="utilisateurs_dhis2_avec_doublons.csv",
                mime="text/csv"
            )
        else:
            st.warning("Aucun utilisateur récupéré.")
else:
    st.warning("Veuillez fournir vos identifiants ou un token personnel.")
