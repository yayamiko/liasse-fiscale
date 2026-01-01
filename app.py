import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration de la page
st.set_page_config(page_title="Mon App Data Viz", layout="wide")

# Titre principal
st.title("📊 Application de Visualisation de Données Interactive")
st.markdown("Chargez un fichier CSV pour explorer vos données !")

# Sidebar pour les uploads et options
with st.sidebar:
    st.header("Options")
    uploaded_file = st.file_uploader("Chargez votre fichier CSV", type=["csv"])
    if uploaded_file is not None:
        sep = st.text_input("Séparateur (par défaut ',')", value=",")
    else:
        sep = ","
    
    st.markdown("---")
    st.info("Exemple : Utilisez le dataset Iris intégré si aucun fichier n'est chargé.")

# Chargement des données
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=sep)
        st.success("Fichier chargé avec succès !")
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        df = None
else:
    # Dataset exemple intégré (Iris)
    st.info("Aucun fichier chargé. Utilisation du dataset Iris comme exemple.")
    from sklearn.datasets import load_iris
    iris = load_iris()
    df = pd.DataFrame(data=np.c_[iris['data'], iris['target']],
                      columns=iris['feature_names'] + ['target'])
    df['target'] = df['target'].map({0: 'setosa', 1: 'versicolor', 2: 'virginica'})

# Si des données sont disponibles
if df is not None:
    st.subheader("Aperçu des données")
    st.dataframe(df.head(10))
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Forme du DataFrame :", df.shape)
    with col2:
        st.write("Colonnes :", list(df.columns))
    
    st.subheader("Statistiques descriptives")
    st.dataframe(df.describe())
    
    st.subheader("Visualisations")
    
    # Sélection des colonnes
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    
    viz_type = st.selectbox("Type de graphique", 
                            ["Histogramme", "Graphique en ligne", "Scatter plot", "Bar chart", "Corrélation (heatmap)"])
    
    if viz_type == "Histogramme" and numeric_cols:
        col = st.selectbox("Colonne numérique", numeric_cols)
        fig, ax = plt.subplots()
        ax.hist(df[col].dropna(), bins=30, edgecolor='black')
        ax.set_title(f"Histogramme de {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Fréquence")
        st.pyplot(fig)
        
    elif viz_type == "Graphique en ligne" and numeric_cols:
        col_x = st.selectbox("Axe X (index ou colonne)", ["Index"] + numeric_cols)
        col_y = st.selectbox("Axe Y", numeric_cols)
        fig, ax = plt.subplots()
        if col_x == "Index":
            ax.plot(df.index, df[col_y])
        else:
            ax.plot(df[col_x], df[col_y])
        ax.set_title(f"Ligne : {col_y} vs {col_x}")
        st.pyplot(fig)
        
    elif viz_type == "Scatter plot" and len(numeric_cols) >= 2:
        col_x = st.selectbox("Axe X", numeric_cols)
        col_y = st.selectbox("Axe Y", numeric_cols)
        hue = st.selectbox("Couleur par catégorie (optionnel)", ["Aucun"] + categorical_cols)
        fig, ax = plt.subplots()
        if hue == "Aucun":
            ax.scatter(df[col_x], df[col_y])
        else:
            sns.scatterplot(data=df, x=col_x, y=col_y, hue=hue, ax=ax)
        ax.set_title(f"Scatter : {col_y} vs {col_x}")
        st.pyplot(fig)
        
    elif viz_type == "Bar chart":
        if categorical_cols:
            cat_col = st.selectbox("Colonne catégorielle (X)", categorical_cols + numeric_cols)
            if numeric_cols:
                num_col = st.selectbox("Valeur à agréger (Y)", numeric_cols)
                agg = st.selectbox("Agrégation", ["count", "mean", "sum"])
                if agg == "count":
                    data = df[cat_col].value_counts()
                    st.bar_chart(data)
                else:
                    data = df.groupby(cat_col)[num_col].agg(agg)
                    st.bar_chart(data)
        
    elif viz_type == "Corrélation (heatmap)" and len(numeric_cols) > 1:
        fig, ax = plt.subplots()
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="coolwarm", ax=ax)
        ax.set_title("Matrice de corrélation")
        st.pyplot(fig)

st.caption("Application créée avec ❤️ par Grok – Prête à déployer sur Streamlit Community Cloud !")
