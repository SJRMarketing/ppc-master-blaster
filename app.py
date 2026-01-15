import streamlit as st
import pandas as pd
import numpy as np
import io
import xlsxwriter

# --- Page Configuration ---
st.set_page_config(page_title="PPC Master Blaster", page_icon="🚀", layout="wide")

# --- Title and Header ---
st.title("🚀 PPC Master Blaster: Intelligence Edition")
st.markdown("""
**Upload your Google Ads 'Search Keyword' CSV.** This tool runs a forensic audit including **Brand Defense** and **Competitor Analysis**.
""")

# --- Sidebar for Settings ---
st.sidebar.header("Audit Settings")
cpa_threshold = st.sidebar.number_input("Max Acceptable CPA ($)", value=30.0, step=5.0)
min_impr = st.sidebar.number_input("Min Impressions for Significance", value=50, step=10)

st.sidebar.divider()
st.sidebar.header("🕵️‍♂️ Intelligence Inputs")
st.sidebar.info("Optional: Enter names to enable advanced tracking.")
brand_name = st.sidebar.text_input("Your Brand Name (e.g. Diamond Tuck)", value="")
competitor_names = st.sidebar.text_area("Competitor Names (comma separated)", value="")

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

# --- Excel Styling Function ---
def generate_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    df.to_excel(writer, index=False, sheet_name='Audit Report')
    workbook = writer.book
    worksheet = writer.sheets['Audit Report']
    
    # Formats
    header_fmt = workbook.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1F497D', 'border': 1})
    high_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'border': 1})
    med_fmt = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500', 'border': 1})
    normal_fmt = workbook.add_format({'border': 1})
    
    # Apply Header
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)
        
    # Apply Rows
    for row_num, row_data in enumerate(df.values):
        priority = row_data[0]
        if "HIGH" in str(priority): fmt = high_fmt
        elif "MED" in str(priority): fmt = med_fmt
        else: fmt = normal_fmt
        
        for col_num, cell_value in enumerate(row_data):
            worksheet.write(row_num + 1, col_num, cell_value, fmt)
            
    # Widths
    worksheet.set_column('A:A', 15) # Priority
    worksheet.set_column('B:B', 25) # Issue
    worksheet.set_column('C:C', 30) # Ad Group
    worksheet.set_column('D:D', 35) # Keyword
    worksheet.set_column('E:E', 25) # Metric
    worksheet.set_column('F:F', 40) # Fix
    
    writer.close()
    return output.getvalue()

# --- Main App Logic ---
uploaded_file = st.file_uploader("Drop your Google Ads CSV here", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, skiprows=2)
        df_clean = df[df['Keyword'].notna()].copy()
        
        # Cleaning
        cols_map = {
            'Cost': clean_currency, 'Conversions': clean_number,
            'Impr.': clean_number, 'CTR': clean_percent, 'Quality Score': clean_qs
        }
        for col, func in cols_map.items():
            if col in df_clean.columns: df_clean[col] = df_clean[col].apply(func)
                
        # Logic Engine
        findings = []
        competitors = [c.strip().lower() for c in competitor_names.split(',') if c.strip()]
        
        for index, row in df_clean.iterrows():
            kw = str(row['Keyword']).lower()
            ad_group = row['Ad group'] if 'Ad group' in row else "Unknown"
            match_type = str(row['Match type'])
            cost = row['Cost']
            conv = row['Conversions']
            qs = row['Quality Score']
            impr = row['Impr.']
            ctr = row['CTR']
            
            # 1. CASH INCINERATOR
            if conv == 0 and cost > cpa_threshold:
                findings.append({
                    "Priority": "HIGH", "Issue": "Cash Incinerator", "Ad Group": ad_group,
                    "Keyword": row['Keyword'], "Metric": f"${cost:.2f} Spend / 0 Leads", 
                    "The Fix": "PAUSE immediately."
                })
            
            # 2. BRAND DEFENSE (New)
            if brand_name and brand_name.lower() in kw:
                # Brand keywords should have QS 8-10 and High CTR. If not, something is wrong.
                if (qs < 8 and impr > 20) or (ctr < 5.0 and impr > 20):
                    findings.append({
                        "Priority": "HIGH", "Issue": "Brand Defense Leak", "Ad Group": ad_group,
                        "Keyword": row['Keyword'], "Metric": f"QS: {qs} | CTR: {ctr}%", 
                        "The Fix": "Competitors may be stealing traffic. Improve Ad Copy."
                    })

            # 3. COMPETITOR WASTE (New)
            is_competitor = any(comp in kw for comp in competitors)
            if is_competitor:
                if conv == 0 and cost > (cpa_threshold * 0.5): # Stricter threshold for competitors
                    findings.append({
                        "Priority": "MED", "Issue": "Competitor Ego Waste", "Ad Group": ad_group,
                        "Keyword": row['Keyword'], "Metric": f"${cost:.2f} Spend / 0 Leads", 
                        "The Fix": "Stop bidding on competitors. It's too expensive."
                    })

            # 4. BROAD MATCH TRAP
            if "broad" in match_type.lower() and cost > 0:
                findings.append({
                    "Priority": "HIGH", "Issue": "Broad Match Trap", "Ad Group": ad_group,
                    "Keyword": row['Keyword'], "Metric": "Broad Match", 
                    "The Fix": "Change to Phrase Match."
                })
                
            # 5. QUALITY SCORE ANCHOR
            if qs < 3 and impr > min_impr:
                findings.append({
                    "Priority": "HIGH", "Issue": "Quality Score Anchor", "Ad Group": ad_group,
                    "Keyword": row['Keyword'], "Metric": f"QS: {qs}/10", 
                    "The Fix": "Pause or New Ad Group."
                })

        # Display Results
        if findings:
            results_df = pd.DataFrame(findings)
            
            # Reorder
            cols = ["Priority", "Issue", "Ad Group", "Keyword", "Metric", "The Fix"]
            results_df = results_df[cols]
            
            # Sort
            priority_map = {"HIGH": 1, "MED": 2, "LOW": 3}
            results_df['SortKey'] = results_df['Priority'].map(priority_map)
            results_df = results_df.sort_values('SortKey').drop('SortKey', axis=1)

            # --- VISUAL DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Spend Analyzed", f"${df_clean['Cost'].sum():.2f}")
            col2.metric("Critical Issues Found", len(results_df))
            
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚠️ Issues by Category")
                st.bar_chart(results_df['Issue'].value_counts())
                
            with c2:
                st.subheader("🔥 Top Cash Incinerators")
                incinerators = results_df[results_df['Issue'] == 'Cash Incinerator']
                if not incinerators.empty:
                    incinerators['Lost Spend'] = incinerators['Metric'].apply(lambda x: float(x.split('$')[1].split(' ')[0]))
                    st.bar_chart(incinerators.set_index('Keyword')['Lost Spend'])
                else:
                    st.info("No Cash Incinerators found! (Good job)")

            st.divider()
            st.subheader("Preview of Findings")
            st.dataframe(results_df.head(10), use_container_width=True)
            
            # EXCEL EXPORT
            excel_data = generate_excel(results_df)
            st.download_button(
                label="📥 Download Intelligence Report (.xlsx)",
                data=excel_data,
                file_name="Master_Blaster_Intel_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.success("✅ No critical issues found! This campaign is clean.")
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
