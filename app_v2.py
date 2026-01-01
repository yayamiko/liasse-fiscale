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
st.set_page_config(page_title="e-Conformité Fournisseurs", layout="wide")
st.title("🏭 e-Conformité Fournisseurs - Analyse Santé Financière")

# Initialisation données
if "liasses" not in st.session_state:
    st.session_state.liasses = pd.DataFrame(columns=[
        "ID", "Raison_Sociale", "SIRET", "Annee",
        "Chiffre_Affaires", "Resultat_Exploitation", "Resultat_Net",
        "Capitaux_Propres", "Dettes_Financieres",
        "Actif_Circulant", "Passif_Circulant", "Stocks"
    ])
    # Exemples
    exemple = pd.DataFrame([
        {"ID": 1, "Raison_Sociale": "VIASSO", "SIRET": "82351897200018", "Annee": 2024,
         "Chiffre_Affaires": 2200000, "Resultat_Exploitation": 180000, "Resultat_Net": 120000,
         "Capitaux_Propres": 700000, "Dettes_Financieres": 350000, "Actif_Circulant": 550000,
         "Passif_Circulant": 280000, "Stocks": 160000},
        {"ID": 2, "Raison_Sociale": "VIASSO", "SIRET": "82351897200018", "Annee": 2023,
         "Chiffre_Affaires": 2000000, "Resultat_Exploitation": 150000, "Resultat_Net": 100000,
         "Capitaux_Propres": 600000, "Dettes_Financieres": 400000, "Actif_Circulant": 500000,
         "Passif_Circulant": 300000, "Stocks": 150000},
        {"ID": 3, "Raison_Sociale": "TELEM", "SIRET": "06950243300340", "Annee": 2024,
         "Chiffre_Affaires": 1500000, "Resultat_Exploitation": 80000, "Resultat_Net": 50000,
         "Capitaux_Propres": 400000, "Dettes_Financieres": 600000, "Actif_Circulant": 450000,
         "Passif_Circulant": 350000, "Stocks": 100000},
    ])
    st.session_state.liasses = pd.concat([st.session_state.liasses, exemple], ignore_index=True)

df = st.session_state.liasses.copy()

# Calcul ratios et risques
def calculer_sante_financiere(row):
    ca = max(row["Chiffre_Affaires"], 1)
    cp = max(row["Capitaux_Propres"], 1)
    dettes = max(row["Dettes_Financieres"], 1)
    ac = max(row["Actif_Circulant"], 1)
    pc = max(row["Passif_Circulant"], 1)

    rentabilite = row["Resultat_Net"] / ca * 100
    autonomie = cp / (cp + dettes) * 100
    liquidite_gen = ac / pc
    endettement = dettes / cp

    note = 0
    note += min(max(rentabilite, 0) / 10 * 5, 5)
    note += min(autonomie / 20, 5)
    note += min(liquidite_gen * 3, 6)
    note += min(max(3 - endettement, 0) * 2, 4)
    note = round(note, 1)

    return pd.Series({
        "Rentabilite_%": round(rentabilite, 2),
        "Autonomie_%": round(autonomie, 2),
        "Liquidite_Generale": round(liquidite_gen, 2),
        "Endettement": round(endettement, 2),
        "Note_Sante": note
    })

if not df.empty:
    ratios = df.apply(calculer_sante_financiere, axis=1)
    df = pd.concat([df, ratios], axis=1)
    df["Sanctions"] = df["Liquidite_Generale"].apply(lambda x: "Faible" if x >= 1.5 else ("Modéré" if x >= 1 else "Élevé"))
    df["Documents"] = df["Autonomie_%"].apply(lambda x: "Faible" if x >= 50 else ("Modéré" if x >= 30 else "Élevé"))
    df["Finances"] = df["Endettement"].apply(lambda x: "Faible" if x <= 1 else ("Modéré" if x <= 2 else "Élevé"))
    df["Reglementaire"] = df["Rentabilite_%"].apply(lambda x: "Faible" if x >= 8 else ("Modéré" if x >= 3 else "Élevé"))
    df["RSE"] = df["Note_Sante"].apply(lambda x: "Faible" if x >= 15 else ("Modéré" if x >= 10 else "Élevé"))

# === Fonction génération PDF ===
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

# === Sidebar : Gestion ===
with st.sidebar:
    st.header("🛠 Gestion des Liasses")
    # (Le code d'ajout/modif/suppression reste le même que précédemment)
    # Je l'ai omis ici pour raccourcir, mais garde-le de la version précédente !

# === Dashboard ===
st.header("📊 Accueil")

if df.empty:
    st.info("Aucune donnée. Ajoutez des liasses via le menu.")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fournisseurs", df["Raison_Sociale"].nunique())
    col2.metric("Liasses", len(df))
    col3.metric("Années", df["Annee"].nunique())
    col4.metric("Note moyenne", f"{df['Note_Sante'].mean():.1f}/20")

    # Donuts globaux
    categories = ["Sanctions", "Documents", "Finances", "Reglementaire", "RSE"]
    cols = st.columns(5)
    for i, cat in enumerate(categories):
        with cols[i]:
            counts = df[cat].value_counts()
            fig = go.Figure(go.Pie(labels=counts.index, values=counts.values, hole=0.6,
                                   marker_colors=["#28a745", "#ffc107", "#dc3545"]))
            fig.update_layout(title=cat, height=300, margin=dict(t=40))
            st.plotly_chart(fig, use_container_width=True)

    # Tableau cliquable
    st.subheader("📋 Portefeuille Fournisseurs")

    # Agrégation par entreprise (moyenne des notes, etc.)
    df_group = df.groupby("Raison_Sociale").agg({
        "SIRET": "first",
        "Note_Sante": "mean",
        "Sanctions": lambda x: x.mode()[0] if not x.empty else "N/A",
        "Documents": lambda x: x.mode()[0] if not x.empty else "N/A",
        "Finances": lambda x: x.mode()[0] if not x.empty else "N/A",
        "Reglementaire": lambda x: x.mode()[0] if not x.empty else "N/A",
        "RSE": lambda x: x.mode()[0] if not x.empty else "N/A",
    }).round(1).reset_index()

    # Colonne cliquable
    df_group["Détail →"] = "👆 Cliquez pour voir la fiche détaillée"
    st.dataframe(df_group.style.applymap(lambda x: f"background-color: {'#d4edda' if x=='Faible' else '#fff3cd' if x=='Modéré' else '#f8d7da'}",
                                         subset=["Sanctions","Documents","Finances","Reglementaire","RSE"]),
                 use_container_width=True, on_select="rerun", selection_mode="single-row")

    # Si une ligne est sélectionnée
    if st.session_state.get("dataframe_selection"):
        selection = st.session_state.dataframe_selection["rows"]
        if selection:
            selected_row = df_group.iloc[selection[0]]
            raison = selected_row["Raison_Sociale"]
            df_entreprise = df[df["Raison_Sociale"] == raison].sort_values("Annee", ascending=False)

            st.subheader(f"📄 Fiche détaillée : {raison}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Note moyenne /20", f"{selected_row['Note_Sante']:.1f}")
            col2.metric("Nombre d'exercices", len(df_entreprise))
            col3.metric("Dernière année", df_entreprise["Annee"].max())

            st.dataframe(df_entreprise[["Annee", "Chiffre_Affaires", "Resultat_Net", "Note_Sante",
                                        "Sanctions", "Documents", "Finances", "Reglementaire", "RSE"]])

            # Bouton PDF
            pdf_buffer = generer_pdf_entreprise(df_entreprise)
            st.download_button(
                label="📄 Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name=f"Fiche_Conformite_{raison.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

st.caption("Application avec export PDF individuel par fournisseur – Créée par Grok ❤️")
