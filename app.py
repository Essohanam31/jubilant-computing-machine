# NOTE: Ce script nécessite que le module 'streamlit' soit installé dans votre environnement Python.
# Installez-le avec : pip install streamlit

try:
    import streamlit as st
    import pandas as pd
    import requests
    import base64
except ModuleNotFoundError as e:
    missing_module = str(e).split("No module named ")[-1].strip("'")
    print(f"Le module {missing_module} est requis mais non installé. Veuillez l'installer avec : pip install {missing_module}")
    exit(1)

st.set_page_config(page_title="Détection des doublons DHIS2", layout="wide")

# Onglet Connexion
st.sidebar.header("🔐 Connexion à DHIS2")
dhis2_url = st.sidebar.text_input("URL DHIS2", value="https://ton_instance.dhis2.org/dhis")
username = st.sidebar.text_input("Nom d'utilisateur", type="default")
password = st.sidebar.text_input("Mot de passe", type="password")

# Authentification de base
@st.cache_data(show_spinner=False)
def get_auth_header(username, password):
    token = f"{username}:{password}"
    encoded = base64.b64encode(token.encode()).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}

# Obtenir les unités d'organisation
@st.cache_data(show_spinner=False)
def get_organisation_units(base_url, headers):
    url = f"{base_url}/api/organisationUnits.json"
    params = {"paging": "false", "fields": "id,name"}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json().get("organisationUnits", [])
    return []

# Obtenir les utilisateurs
def get_users(base_url, headers, org_unit_id):
    url = f"{base_url}/api/users.json"
    params = {
        "paging": "false",
        "fields": "id,username,name,organisationUnits[id]"
    }
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        st.error("Erreur lors de la récupération des utilisateurs.")
        return []
    users = r.json().get("users", [])
    # Filtrer par unité d'organisation
    filtered = []
    for user in users:
        user_ous = [ou['id'] for ou in user.get('organisationUnits', [])]
        if org_unit_id in user_ous:
            filtered.append(user)
    return filtered

if username and password and dhis2_url:
    headers = get_auth_header(username, password)

    # Récupérer les unités d'organisation
    st.sidebar.subheader("🏥 Sélection de l'unité d'organisation")
    units = get_organisation_units(dhis2_url, headers)
    unit_options = {unit['name']: unit['id'] for unit in units}

    if unit_options:
        selected_name = st.sidebar.selectbox("Choisir une unité", list(unit_options.keys()))
        selected_id = unit_options[selected_name]

        # Bouton pour charger les utilisateurs
        if st.sidebar.button("📥 Charger les utilisateurs"):
            st.info(f"Chargement des utilisateurs pour l'unité : {selected_name}")
            users = get_users(dhis2_url, headers, selected_id)

            if users:
                df_users = pd.DataFrame(users)
                df_users = df_users[['id', 'username', 'name']]

                # Marquer les doublons
                df_users['doublon'] = df_users.duplicated(subset='name', keep=False)
                df_users['doublon'] = df_users['doublon'].apply(lambda x: "Oui" if x else "Non")

                st.success(f"✅ {len(df_users)} utilisateurs trouvés.")
                st.dataframe(df_users, use_container_width=True)

                # Télécharger le CSV
                csv = df_users.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Télécharger la liste CSV",
                    data=csv,
                    file_name="utilisateurs_dhis2.csv",
                    mime='text/csv'
                )
            else:
                st.warning("Aucun utilisateur trouvé pour cette unité.")
else:
    st.warning("Veuillez renseigner vos identifiants DHIS2 pour commencer.")
