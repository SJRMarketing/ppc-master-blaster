import streamlit as st
import pandas as pd
import numpy as np
import io

# --- Page Configuration ---
st.set_page_config(page_title="PPC Master Blaster", page_icon="🚀", layout="wide")

# --- Title and Header ---
st.title("🚀 PPC Master Blaster: Forensic Audit Tool")
st.markdown("""
**Upload your Google Ads 'Search Keyword' CSV.** This tool will forensically analyze your data and detect the top profit-killers instantly.
""")

# --- Sidebar for Settings ---
st.sidebar.header("Audit Settings")
cpa_threshold = st.sidebar.number_input("Max Acceptable CPA ($)", value=30.0, step=5.0)
min_impr = st.sidebar.number_input("Min Impressions for Significance", value=50, step=10)

# --- Helper Functions ---
def clean_currency(x):
    if isinstance(x, str): return float(x.replace(',', '').replace('AUD', '').replace('$', '').strip())
    return x

def clean_percent(x):
    if isinstance(x, str): 
        if '--' in x: return 0.0
        return float(x.replace('%', '').strip())
    return x

def clean_number(x):
    if isinstance(x, str):
        if '--' in x: return 0
        return float(x.replace(',', '').strip())
    return x

def clean_qs(x):
    if isinstance(x, str):
        if '--' in x: return np.nan
        return float(str(x).split('/')[0])
    return x

# --- Main App Logic ---
uploaded_file = st.file_uploader("Drop your Google Ads CSV here", type=['csv'])

if uploaded_file is not None:
    try:
        # Load Data (Skip header rows automatically)
        df = pd.read_csv(uploaded_file, skiprows=2)
        
        # --- Data Cleaning ---
        # Only keep rows with actual keywords
        df_clean = df[df['Keyword'].notna()].copy()
        
        # Clean numeric columns
        cols_to_clean = {
            'Cost': clean_currency,
            'Conversions': clean_number,
            'Impr.': clean_number,
            'CTR': clean_percent,
            'Quality Score': clean_qs
        }
        
        for col, func in cols_to_clean.items():
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(func)
            else:
                st.error(f"Missing Column: {col}. Please check your CSV export includes this.")
                st.stop()
                
        # --- Logic Engine ---
        findings = []
        
        for index, row in df_clean.iterrows():
            kw = row['Keyword']
            match_type = str(row['Match type'])
            cost = row['Cost']
            conv = row['Conversions']
            qs = row['Quality Score']
            impr = row['Impr.']
            ctr = row['CTR']
            
            # 1. Cash Incinerator
            if conv == 0 and cost > cpa_threshold:
                findings.append({
                    "Priority": "🔴 HIGH",
                    "Issue": "Cash Incinerator",
                    "Keyword": kw,
                    "Metric": f"${cost:.2f} Spend / 0 Leads",
                    "The Fix": "PAUSE immediately."
                })
            
            # 2. Broad Match Trap
            if "broad" in match_type.lower() and cost > 0:
                findings.append({
                    "Priority": "🔴 HIGH",
                    "Issue": "Broad Match Trap",
                    "Keyword": kw,
                    "Metric": "Broad Match",
                    "The Fix": "Change to Phrase Match."
                })
                
            # 3. Quality Score Anchor
            if qs < 3 and impr > min_impr:
                findings.append({
                    "Priority": "🔴 HIGH",
                    "Issue": "Quality Score Anchor",
                    "Keyword": kw,
                    "Metric": f"QS: {qs}/10",
                    "The Fix": "Pause or New Ad Group."
                })
                
            # 4. Click Repellent
            if ctr < 1.0 and impr > (min_impr * 2):
                findings.append({
                    "Priority": "🟡 MED",
                    "Issue": "Click Repellent",
                    "Keyword": kw,
                    "Metric": f"CTR: {ctr}%",
                    "The Fix": "Rewrite Ad Headlines."
                })

        # --- Display Results ---
        if findings:
            results_df = pd.DataFrame(findings)
            
            # Metrics Summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Spend Analyzed", f"${df_clean['Cost'].sum():.2f}")
            col2.metric("Critical Issues Found", len(results_df))
            col3.metric("Wasted Spend Detected", f"${results_df[results_df['Issue']=='Cash Incinerator']['Metric'].apply(lambda x: float(x.split('$')[1].split(' ')[0])).sum() if not results_df[results_df['Issue']=='Cash Incinerator'].empty else 0:.2f}")

            st.divider()
            
            st.subheader("Your Forensic Audit Report")
            st.dataframe(results_df, use_container_width=True)
            
            # Download Button
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Fix-It Report (CSV)",
                data=csv,
                file_name="Master_Blaster_Audit.csv",
                mime="text/csv",
            )
        else:
            st.success("✅ No critical issues found! This campaign is clean.")
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure you are uploading the 'Search Keywords' report from Google Ads.")