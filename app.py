import streamlit as st
import pandas as pd
import numpy as np
import io
import xlsxwriter

# --- Page Configuration ---
st.set_page_config(page_title="PPC Master Blaster", page_icon="🚀", layout="wide")

# --- Title and Header ---
st.title("🚀 PPC Master Blaster: Pro Audit Tool")
st.markdown("""
**Upload your Google Ads 'Search Keyword' CSV.** This tool generates a forensic **Excel Report** with color-coded alerts.
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

# --- Excel Styling Function ---
def generate_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Write the dataframe to Excel
    df.to_excel(writer, index=False, sheet_name='Audit Report')
    
    # Get the workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Audit Report']
    
    # Define Formats
    header_fmt = workbook.add_format({
        'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#1F497D', 'border': 1
    })
    
    high_priority_fmt = workbook.add_format({
        'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'border': 1
    })
    
    med_priority_fmt = workbook.add_format({
        'bg_color': '#FFEB9C', 'font_color': '#9C6500', 'border': 1
    })
    
    normal_fmt = workbook.add_format({'border': 1})
    
    # Apply Header Format
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)
        
    # Apply Row Formatting based on Priority
    for row_num, row_data in enumerate(df.values):
        priority = row_data[0] # Priority is first column
        
        if "HIGH" in str(priority):
            fmt = high_priority_fmt
        elif "MED" in str(priority):
            fmt = med_priority_fmt
        else:
            fmt = normal_fmt
            
        for col_num, cell_value in enumerate(row_data):
            worksheet.write(row_num + 1, col_num, cell_value, fmt)
            
    # Adjust Column Widths (Updated for new Ad Group column)
    worksheet.set_column('A:A', 15) # Priority
    worksheet.set_column('B:B', 25) # Issue
    worksheet.set_column('C:C', 30) # Ad Group (NEW)
    worksheet.set_column('D:D', 35) # Keyword
    worksheet.set_column('E:E', 25) # Metric
    worksheet.set_column('F:F', 40) # The Fix
    
    writer.close()
    return output.getvalue()

# --- Main App Logic ---
uploaded_file = st.file_uploader("Drop your Google Ads CSV here", type=['csv'])

if uploaded_file is not None:
    try:
        # Load Data
        df = pd.read_csv(uploaded_file, skiprows=2)
        
        # Data Cleaning
        df_clean = df[df['Keyword'].notna()].copy()
        
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
                
        # Logic Engine
        findings = []
        
        for index, row in df_clean.iterrows():
            kw = row['Keyword']
            # Capture Ad Group (or Campaign if available)
            ad_group = row['Ad group'] if 'Ad group' in row else "Unknown"
            
            match_type = str(row['Match type'])
            cost = row['Cost']
            conv = row['Conversions']
            qs = row['Quality Score']
            impr = row['Impr.']
            ctr = row['CTR']
            
            # Logic Rules
            if conv == 0 and cost > cpa_threshold:
                findings.append({
                    "Priority": "HIGH", "Issue": "Cash Incinerator", 
                    "Ad Group": ad_group, "Keyword": kw, 
                    "Metric": f"${cost:.2f} Spend / 0 Leads", "The Fix": "PAUSE immediately."
                })
            
            if "broad" in match_type.lower() and cost > 0:
                findings.append({
                    "Priority": "HIGH", "Issue": "Broad Match Trap", 
                    "Ad Group": ad_group, "Keyword": kw, 
                    "Metric": "Broad Match", "The Fix": "Change to Phrase Match."
                })
                
            if qs < 3 and impr > min_impr:
                findings.append({
                    "Priority": "HIGH", "Issue": "Quality Score Anchor", 
                    "Ad Group": ad_group, "Keyword": kw, 
                    "Metric": f"QS: {qs}/10", "The Fix": "Pause or New Ad Group."
                })
                
            if ctr < 1.0 and impr > (min_impr * 2):
                findings.append({
                    "Priority": "MED", "Issue": "Click Repellent", 
                    "Ad Group": ad_group, "Keyword": kw, 
                    "Metric": f"CTR: {ctr}%", "The Fix": "Rewrite Ad Headlines."
                })

        # Display Results
        if findings:
            results_df = pd.DataFrame(findings)
            
            # Reorder Columns to put Ad Group next to Keyword
            cols = ["Priority", "Issue", "Ad Group", "Keyword", "Metric", "The Fix"]
            results_df = results_df[cols]
            
            # Sort by Priority
            priority_map = {"HIGH": 1, "MED": 2, "LOW": 3}
            results_df['SortKey'] = results_df['Priority'].map(priority_map)
            results_df = results_df.sort_values('SortKey').drop('SortKey', axis=1)

            # --- VISUAL DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Spend Analyzed", f"${df_clean['Cost'].sum():.2f}")
            col2.metric("Critical Issues Found", len(results_df))
            
            st.divider()
            
            # Charts
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⚠️ Issues by Category")
                st.bar_chart(results_df['Issue'].value_counts())
                
            with c2:
                st.subheader("🔥 Top Cash Incinerators")
                incinerators = results_df[results_df['Issue'] == 'Cash Incinerator']
                if not incinerators.empty:
                    # Clean metric to float for charting
                    incinerators['Lost Spend'] = incinerators['Metric'].apply(lambda x: float(x.split('$')[1].split(' ')[0]))
                    st.bar_chart(incinerators.set_index('Keyword')['Lost Spend'])
                else:
                    st.info("No Cash Incinerators found! (Good job)")

            st.divider()
            st.subheader("Preview of Findings")
            st.dataframe(results_df.head(10), use_container_width=True)
            
            # GENERATE EXCEL
            excel_data = generate_excel(results_df)
            
            st.download_button(
                label="📥 Download Professional Excel Report (.xlsx)",
                data=excel_data,
                file_name="Master_Blaster_Pro_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.success("✅ No critical issues found! This campaign is clean.")
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
