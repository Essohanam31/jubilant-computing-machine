import streamlit as st
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Liste des utilisateurs et détection des doublons", layout="wide")
st.title("👥 Liste des utilisateurs DHIS2 et détection des doublons")

# === Paramètres fixes ===
DHIS2_URL = "https://togo.dhis2.org/dhis"

# === Authentification via PAT ou identifiants ===
st.sidebar.header("🔐 Authentification")
use_pat = st.sidebar.checkbox("Se connecter avec un token personnel (PAT)", value=True)

if use_pat:
    pat = st.sidebar.text_input("Token personnel (PAT)", type="password")
    headers = {"Authorization": f"ApiToken {pat}"} if pat else None
else:
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")
    if username and password:
        auth_str = f"{username}:{password}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        headers = {"Authorization": f"Basic {auth_b64}"}
    else:
        headers = None

if headers:
    try:
        with st.spinner("🔄 Chargement des utilisateurs..."):
            url = f"{DHIS2_URL}/api/users.json"
            params = {
                "paging": "false",
                "fields": "id,username,name,email,organisationUnits[id,name],userCredentials[userRoles[name]]"
            }
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            users = response.json().get("users", [])

            if not users:
                st.warning("Aucun utilisateur trouvé.")
            else:
                df_users = pd.json_normalize(users)

                # Créer une colonne 'Doublon' basée sur les noms
                df_users["doublon_nom"] = df_users.duplicated("name", keep=False).map({True: "Oui", False: "Non"})

                # Affichage du tableau
                st.success(f"✅ {len(df_users)} utilisateur(s) trouvé(s).")
                st.dataframe(df_users[["id", "username", "name", "email", "doublon_nom"]], use_container_width=True)

                # Filtrer les doublons uniquement
                df_doublons = df_users[df_users["doublon_nom"] == "Oui"]
                if not df_doublons.empty:
                    st.subheader("⚠️ Doublons détectés par nom")
                    st.dataframe(df_doublons[["id", "username", "name", "email"]])

                    # Télécharger les doublons
                    st.download_button(
                        label="📥 Télécharger les doublons (CSV)",
                        data=df_doublons.to_csv(index=False).encode(),
                        file_name="doublons_utilisateurs.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("✅ Aucun doublon détecté.")

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à DHIS2 : {e}")
else:
    st.info("Veuillez entrer vos identifiants ou votre token personnel pour continuer.")

