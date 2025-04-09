import streamlit as st
import pandas as pd
import json
import tempfile
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
import searchconsole
from io import StringIO

st.set_page_config(page_title="SEO GSC + GA4 Analyzer", layout="wide")
st.title("🔍 SEO Analyzer: Search Console + GA4")

# --- Credenziali da st.secrets ---
try:
    creds_str = st.secrets["GCP_SERVICE_ACCOUNT"]
    creds_dict = json.loads(creds_str)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    st.success("Credenziali caricate correttamente!")

    # Salva il JSON in un file temporaneo per Search Console
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as temp_file:
        temp_file.write(creds_str)
        temp_file.flush()
        temp_json_path = temp_file.name

except Exception as e:
    st.error(f"Errore nel caricamento delle credenziali: {e}")
    st.stop()

# --- Input utente ---
st.sidebar.header("Parametri")
property_url = st.sidebar.text_input("Dominio GSC", "https://re-pack.it/")
ga4_property_id = st.sidebar.text_input("GA4 Property ID", "347608976")
start_date = st.sidebar.date_input("Data inizio")
end_date = st.sidebar.date_input("Data fine")

if start_date and end_date and property_url and ga4_property_id:

    # --- Search Console ---
    st.subheader("🔎 Google Search Console")
    try:
        account = searchconsole.authenticate(client_config=temp_json_path)
        webproperty = account[property_url]
        report = webproperty.query.range(str(start_date), str(end_date)) \
            .dimension('page') \
            .metric('clicks', 'impressions', 'ctr', 'position') \
            .execute()
        gsc_df = report.to_dataframe()
        gsc_df['page_normalized'] = gsc_df['page'].str.replace(property_url, '')
        st.dataframe(gsc_df)
    except Exception as e:
        st.error(f"Errore GSC: {e}")

    # --- GA4 ---
    st.subheader("📈 Google Analytics 4")
    try:
        client = BetaAnalyticsDataClient(credentials=credentials)
        request = RunReportRequest(
            property=f"properties/{ga4_property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="sessions"), Metric(name="engagedSessions")],
            date_ranges=[DateRange(start_date=str(start_date), end_date=str(end_date))]
        )
        response = client.run_report(request)
        ga4_df = pd.DataFrame([
            {
                "pagePath": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "engagedSessions": int(row.metric_values[1].value)
            }
            for row in response.rows
        ])
        ga4_df['page_normalized'] = ga4_df['pagePath']
        st.dataframe(ga4_df)
    except Exception as e:
        st.error(f"Errore GA4: {e}")

    # --- Merge GSC + GA4 ---
    st.subheader("🔗 Dati combinati GSC + GA4")
    try:
        merged = pd.merge(gsc_df, ga4_df, on="page_normalized", how="outer")
        st.dataframe(merged)
        csv = merged.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Scarica dati combinati", csv, "seo_merged.csv", "text/csv")
    except Exception as e:
        st.error(f"Errore nel merge: {e}")
