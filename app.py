import streamlit as st
import pandas as pd

st.set_page_config(page_title="SEO Audit Tool", layout="wide")
st.title("🔍 SEO Audit Tool (Base)")

st.markdown("""
Questo strumento ti permette di caricare un file CSV (esportato da Search Console, Screaming Frog o altri) e analizzare:
- Pagine senza `<title>` o `<h1>`
- Descrizioni duplicate o mancanti
- Pagine con CTR basso o impression alte
""")

# Upload file CSV
uploaded_file = st.file_uploader("Carica un file CSV con le pagine del sito", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File caricato correttamente!")
    st.dataframe(df.head())

    col1, col2 = st.columns(2)

    with col1:
        if "title" in df.columns:
            missing_title = df[df['title'].isnull() | (df['title'].str.strip() == '')]
            st.subheader("🔴 Title mancanti")
            st.dataframe(missing_title)

        if "meta_description" in df.columns:
            missing_desc = df[df['meta_description'].isnull() | (df['meta_description'].str.strip() == '')]
            duplicated_desc = df[df.duplicated('meta_description', keep=False) & df['meta_description'].notnull()]
            st.subheader("🟡 Meta Description duplicate")
            st.dataframe(duplicated_desc)
            st.subheader("🔴 Meta Description mancanti")
            st.dataframe(missing_desc)

    with col2:
        if "h1" in df.columns:
            missing_h1 = df[df['h1'].isnull() | (df['h1'].str.strip() == '')]
            duplicated_h1 = df[df.duplicated('h1', keep=False) & df['h1'].notnull()]
            st.subheader("🔴 H1 mancanti")
            st.dataframe(missing_h1)
            st.subheader("🟡 H1 duplicati")
            st.dataframe(duplicated_h1)

    # Esporta CSV filtrato
    st.subheader("⬇️ Scarica i risultati (filtrati)")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download completo", csv, "seo_audit_completo.csv", "text/csv")