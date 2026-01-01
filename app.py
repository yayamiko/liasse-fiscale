import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import plotly.express as px

# Configuration
st.set_page_config(page_title="e-Conformité Fournisseurs - Santé Financière", layout="wide")
st.title("🏭 e-Conformité Fournisseurs - Analyse Santé Financière")

# Initialisation des données en session_state
if "liasses" not in st.session_state:
    st.session_state.liasses = pd.DataFrame(columns=[
        "ID", "Raison_Sociale", "SIRET", "Annee",
        "Chiffre_Affaires", "Resultat_Exploitation", "Resultat_Net",
        "Capitaux_Propres", "Dettes_Financieres",
        "Actif_Circulant", "Passif_Circulant", "Stocks"
    ])
    # Ajout de quelques exemples pour démarrer
    exemple = pd.DataFrame([{
        "ID": 1,
        "Raison_Sociale": "VIASSO",
        "SIRET": "82351897200018",
        "Annee": 2024,
        "Chiffre_Affaires": 2200000,
        "Resultat_Exploitation": 180000,
        "Resultat_Net": 120000,
        "Capitaux_Propres": 700000,
        "Dettes_Financieres": 350000,
        "Actif_Circulant": 550000,
        "Passif_Circulant": 280000,
        "Stocks": 160000
    }, {
        "ID": 2,
        "Raison_Sociale": "TELEM",
        "SIRET": "06950243300340",
        "Annee": 2024,
        "Chiffre_Affaires": 1500000,
        "Resultat_Exploitation": 80000,
        "Resultat_Net": 50000,
        "Capitaux_Propres": 400000,
        "Dettes_Financieres": 600000,
        "Actif_Circulant": 450000,
        "Passif_Circulant": 350000,
        "Stocks": 100000
    }])
    st.session_state.liasses = pd.concat([st.session_state.liasses, exemple], ignore_index=True)

df = st.session_state.liasses.copy()

# Fonction pour calculer les ratios et la note
def calculer_sante_financiere(row):
    ca = max(row["Chiffre_Affaires"], 1)
    cp = max(row["Capitaux_Propres"], 1)
    dettes = max(row["Dettes_Financieres"], 1)
    ac = max(row["Actif_Circulant"], 1)
    pc = max(row["Passif_Circulant"], 1)
    stocks = row["Stocks"]

    rentabilite = row["Resultat_Net"] / ca * 100
    autonomie = cp / (cp + dettes) * 100
    liquidite_gen = ac / pc
    liquidite_red = (ac - stocks) / pc
    endettement = dettes / cp

    # Note sur 20 (pondération personnalisable)
    note = 0
    note += min(max(rentabilite, 0) / 10 * 5, 5)        # Rentabilité max 5 pts
    note += min(autonomie / 20, 5)                     # Autonomie max 5 pts
    note += min(liquidite_gen * 3, 6)                  # Liquidité max 6 pts
    note += min(max(3 - endettement, 0) * 2, 4)        # Endettement max 4 pts
    note = round(note, 1)

    return pd.Series({
        "Rentabilite_%": round(rentabilite, 2),
        "Autonomie_%": round(autonomie, 2),
        "Liquidite_Generale": round(liquidite_gen, 2),
        "Endettement": round(endettement, 2),
        "Note_Sante": note
    })

# Calcul pour toutes les liasses
if not df.empty:
    ratios = df.apply(calculer_sante_financiere, axis=1)
    df = pd.concat([df, ratios], axis=1)

    # Niveaux de risque
    df["Sanctions"] = df["Liquidite_Generale"].apply(lambda x: "Faible" if x >= 1.5 else ("Modéré" if x >= 1 else "Élevé"))
    df["Documents"] = df["Autonomie_%"].apply(lambda x: "Faible" if x >= 50 else ("Modéré" if x >= 30 else "Élevé"))
    df["Finances"] = df["Endettement"].apply(lambda x: "Faible" if x <= 1 else ("Modéré" if x <= 2 else "Élevé"))
    df["Reglementaire"] = df["Rentabilite_%"].apply(lambda x: "Faible" if x >= 8 else ("Modéré" if x >= 3 else "Élevé"))
    df["RSE"] = df["Note_Sante"].apply(lambda x: "Faible" if x >= 15 else ("Modéré" if x >= 10 else "Élevé"))


#générer PDF
def generer_pdf_entreprise(df_entreprise):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleRed', fontSize=18, textColor=colors.red, alignment=1))
    elements = []

    # Titre
    elements.append(Paragraph(f"Fiche Conformité Fournisseur<br/>{df_entreprise['Raison_Sociale'].iloc[0]}", styles['TitleRed']))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"SIRET : {df_entreprise['SIRET'].iloc[0]}", styles['Title']))
    elements.append(Spacer(1, 1*cm))

    # Tableau des exercices
    data = [["Année", "CA (€)", "Résultat Net (€)", "Note Santé /20", "Sanctions", "Finances", "RSE"]]
    for _, row in df_entreprise.iterrows():
        data.append([
            str(row["Annee"]),
            f"{row['Chiffre_Affaires']:,.0f}",
            f"{row['Resultat_Net']:,.0f}",
            f"{row['Note_Sante']}",
            row["Sanctions"],
            row["Finances"],
            row["RSE"],
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # Graphiques (on sauvegarde en image temporairement)
    categories = ["Sanctions", "Documents", "Finances", "Reglementaire", "RSE"]
    for cat in categories:
        fig = px.pie(df_entreprise, names=cat, title=f"{cat}", color=cat,
                     color_discrete_map={"Faible": "#28a745", "Modéré": "#ffc107", "Élevé": "#dc3545"},
                     hole=0.5)
        img_bytes = fig.to_image(format="png", width=400, height=300)
        img_buffer = BytesIO(img_bytes)
        elements.append(Paragraph(cat, styles['Heading2']))
        elements.append(RLImage(img_buffer, width=8*cm, height=6*cm))
        elements.append(Spacer(1, 0.5*cm))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# Sidebar : Gestion des liasses
with st.sidebar:
    st.header("🛠 Gestion des Liasses Fiscales")
    action = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"])

    if action == "Ajouter":
        st.subheader("Nouvelle Liasse")
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            raison = col1.text_input("Raison Sociale")
            siret = col2.text_input("SIRET")
            annee = col1.number_input("Année", min_value=2000, max_value=2030, value=2025)
            ca = col2.number_input("Chiffre d'Affaires (€)", min_value=0, value=1000000)
            
            col3, col4 = st.columns(2)
            res_exp = col3.number_input("Résultat Exploitation (€)", value=100000)
            res_net = col4.number_input("Résultat Net (€)", value=80000)
            cp = col3.number_input("Capitaux Propres (€)", value=500000)
            dettes = col4.number_input("Dettes Financières (€)", value=300000)
            
            col5, col6 = st.columns(2)
            actif_circ = col5.number_input("Actif Circulant (€)", value=400000)
            passif_circ = col6.number_input("Passif Circulant (€)", value=250000)
            stocks = col5.number_input("Stocks (€)", value=100000)

            submitted = st.form_submit_button("Ajouter la liasse")
            if submitted:
                if raison and siret:
                    new_id = df["ID"].max() + 1 if not df.empty else 1
                    new_row = pd.DataFrame([{
                        "ID": new_id, "Raison_Sociale": raison, "SIRET": siret, "Annee": int(annee),
                        "Chiffre_Affaires": ca, "Resultat_Exploitation": res_exp, "Resultat_Net": res_net,
                        "Capitaux_Propres": cp, "Dettes_Financieres": dettes,
                        "Actif_Circulant": actif_circ, "Passif_Circulant": passif_circ, "Stocks": stocks
                    }])
                    st.session_state.liasses = pd.concat([st.session_state.liasses, new_row], ignore_index=True)
                    st.success("Liasse ajoutée avec succès !")
                    st.rerun()
                else:
                    st.error("Raison sociale et SIRET obligatoires")

    elif action == "Modifier" and not df.empty:
        liasse_id = st.selectbox("Sélectionner la liasse à modifier", df["ID"])
        row = df[df["ID"] == liasse_id].iloc[0]
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            raison = col1.text_input("Raison Sociale", value=row["Raison_Sociale"])
            siret = col2.text_input("SIRET", value=row["SIRET"])
            annee = col1.number_input("Année", value=int(row["Annee"]))
            ca = col2.number_input("CA", value=int(row["Chiffre_Affaires"]))
            # ... (autres champs identiques à l'ajout)
            # Pour simplifier, on peut réutiliser le même formulaire
            st.info("Remplissez tous les champs pour modifier")
            # Tu peux copier le formulaire d'ajout ici avec les values=row[...]
            submitted = st.form_submit_button("Enregistrer modifications")
            if submitted:
                # Mise à jour
                st.session_state.liasses.loc[st.session_state.liasses["ID"] == liasse_id] = [raison, siret, annee, ca, ...]  # à compléter
                st.success("Modifié !")
                st.rerun()

    elif action == "Supprimer" and not df.empty:
        liasse_id = st.selectbox("Sélectionner la liasse à supprimer", df["ID"])
        if st.button("Supprimer définitivement", type="primary"):
            st.session_state.liasses = st.session_state.liasses[st.session_state.liasses["ID"] != liasse_id]
            st.success("Liasse supprimée")
            st.rerun()

# === Dashboard Principal ===
st.header("📊 Accueil")

if df.empty:
    st.info("Aucune liasse fiscale pour l'instant. Ajoutez-en via le menu latéral !")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fournisseurs uniques", df["Raison_Sociale"].nunique())
    col2.metric("Liasses totales", len(df))
    col3.metric("Années couvertes", df["Annee"].nunique())
    col4.metric("Note moyenne /20", f"{df['Note_Sante'].mean():.1f}")

    # Graphiques en anneau
    categories = ["Sanctions", "Documents", "Finances", "Reglementaire", "RSE"]
    cols = st.columns(5)
    colors = {"Faible": "#28a745", "Modéré": "#ffc107", "Élevé": "#dc3545"}

    for i, cat in enumerate(categories):
        with cols[i]:
            counts = df[cat].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=counts.index, values=counts.values, hole=0.6,
                marker_colors=[colors.get(l, "#666") for l in counts.index],
                textinfo='percent+label'
            )])
            fig.update_layout(title=cat, height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # Tableau portefeuille
    st.subheader("📋 Portefeuille Fournisseurs")
    
    # Filtres
    entreprises = st.multiselect("Filtrer par fournisseur", options=sorted(df["Raison_Sociale"].unique()))
    annees = st.multiselect("Filtrer par année", options=sorted(df["Annee"].unique()))

    df_display = df.copy()
    if entreprises:
        df_display = df_display[df_display["Raison_Sociale"].isin(entreprises)]
    if annees:
        df_display = df_display[df_display["Annee"].isin(annees)]

    display_cols = ["Raison_Sociale", "SIRET", "Annee", "Sanctions", "Documents", "Finances", "Reglementaire", "RSE", "Note_Sante"]
    df_show = df_display[display_cols]

    def color_cell(val):
        color_map = {"Faible": "#d4edda", "Modéré": "#fff3cd", "Élevé": "#f8d7da"}
        return f"background-color: {color_map.get(val, '')}; padding: 8px; text-align: center"

    styled = df_show.style.applymap(color_cell, subset=["Sanctions","Documents","Finances","Reglementaire","RSE"])
    st.dataframe(styled, use_container_width=True)

st.caption("Application de gestion de conformité fournisseurs – Données stockées en session (rafraîchissement du navigateur les conserve)")
