import streamlit as st
import pandas as pd
import io
import requests

st.set_page_config(layout="wide")

st.title("📊 ZAPPI SERVICES MARKET PERFORMANCE REVIEW - DASHBOARD")
st.markdown("---")

# =========================================================================
# 1. CLOUD FILE CONFIGURATION (Bypassing Corporate Workspace Walls)
# =========================================================================
FILE_ID = "1jGrpT9e0utjvIUHS-CzZ441ml8YUpx1A" 
GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?id={FILE_ID}&export=download"

@st.cache_data(ttl=600)  # Automatically refreshes data every 10 minutes from Google Drive
def load_excel_from_cloud(url):
    try:
        session = requests.Session()
        response = session.get(url, stream=True)
        
        if response.status_code == 404:
            st.warning("⚠️ The source file 'Zapi_rawdata.xlsx' has been deleted or moved from Google Drive. Displaying empty dashboard.")
            return pd.DataFrame()
            
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
                
        if token:
            url = url + f"&confirm={token}"
            response = session.get(url, stream=True)
            
        response.raise_for_status()
        
        if b"html" in response.content[:100].lower():
            st.error("❌ The file on Google Drive has been deleted or its sharing permissions have been revoked.")
            return pd.DataFrame()
            
        return pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    except Exception as e:
        st.warning("⚠️ Source data file not found on Google Drive. It may have been deleted.")
        return pd.DataFrame()

raw_df = load_excel_from_cloud(GOOGLE_DRIVE_URL)

if raw_df.empty:
    st.info("💡 Please upload the raw data file back to the Google Drive folder to resume tracking.")
    st.stop()

# Clean column spaces safely
raw_df.columns = raw_df.columns.str.strip()

# Clean column spaces safely
raw_df.columns = raw_df.columns.str.strip()

# ⭐ FIX: Drop all ghost/empty rows from the bottom of the Excel sheet instantly
raw_df = raw_df.dropna(subset=["Project Name"])

# =========================================================================
# 2. SIDEBAR FRONT-END FILTERS (Zero Scrolling & Built-In Search)
# =========================================================================
with st.sidebar:
    st.header("🔍 Filter Parameters")
    st.caption("💡 Click inside any box and type characters to search instantly.")
    
    available_markets = list(raw_df["Survey Country"].unique()) if "Survey Country" in raw_df.columns else ["India"]
    selected_markets = st.multiselect("Market (Country)", available_markets, default=[available_markets[0]])

    filtered_by_market = raw_df[raw_df["Survey Country"].isin(selected_markets)]

    available_languages = list(filtered_by_market["Survey Language"].unique()) if "Survey Language" in filtered_by_market.columns else ["English"]
    selected_langs = st.multiselect("Language", available_languages, default=[available_languages[0]])

    filtered_by_lang = filtered_by_market[filtered_by_market["Survey Language"].isin(selected_langs)]

    available_projects = list(filtered_by_lang["Project Name"].unique()) if "Project Name" in filtered_by_lang.columns else []
    default_projects = [available_projects[0]] if available_projects else []
    selected_projects = st.multiselect("Project Name", available_projects, default=default_projects)

project_df = filtered_by_lang[filtered_by_lang["Project Name"].isin(selected_projects)]

available_projects_preview = list(raw_df["Project Name"].unique()) if "Project Name" in raw_df.columns else []
st.markdown(f"📊 **Currently Analyzing: {len(selected_projects)} of {len(available_projects_preview)} Total Projects**")

# =========================================================================
# 3. ADVANCED COUNTING LOGIC 
# =========================================================================
st.markdown("### Quota Performance Summary")

def get_counts(row_type, row_val):
    if project_df.empty:
        return 0, 0
    temp_df = project_df.copy()
    
    if row_type == "Device":
        temp_df = temp_df[temp_df["Device"].astype(str).str.strip() == row_val]
        
    elif row_type == "City_Code":
        city_col = [c for c in temp_df.columns if "4121" in c or "City Question" in c]
        if city_col:
            actual_col = city_col[0]
            # Clean up the data column by removing trailing spaces and making it lowercase
            temp_df["City_Cleaned_Str"] = temp_df[actual_col].astype(str).str.strip().str.lower()
            # Clean up the target lookup value the exact same way
            target_val = str(row_val).strip().str.lower() if hasattr(row_val, 'lower') else str(row_val).strip().lower()
            
            temp_df = temp_df[temp_df["City_Cleaned_Str"] == target_val]
        else:
            return 0, 0
            return 0, 0
        
    elif row_type == "Age-Gender":
        gender, age_range = row_val.split(":")  
        low_age, high_age = map(int, age_range.split("-"))
        temp_df = temp_df[temp_df["Gender"].astype(str).str.strip().str.upper() == gender.upper()]
        temp_df["Age_Clean"] = pd.to_numeric(temp_df["Age"], errors='coerce')
        temp_df = temp_df[(temp_df["Age_Clean"] >= low_age) & (temp_df["Age_Clean"] <= high_age)]
        
    elif row_type == "ISEC":
        low_isec, high_isec = map(int, row_val.split("-"))
        isec_col = "ISEC - Segmentation Parent Edition"
        if isec_col in temp_df.columns:
            temp_df[isec_col] = temp_df[isec_col].astype(str).str.strip()
            temp_df["ISEC_Clean"] = temp_df[isec_col].str.extract(r'(\d+)').apply(pd.to_numeric, errors='coerce')
            numeric_filter = temp_df[(temp_df["ISEC_Clean"] >= low_isec) & (temp_df["ISEC_Clean"] <= high_isec)]
            if not numeric_filter.empty:
                temp_df = numeric_filter
            else:
                allowed_strings = [str(num) for num in range(low_isec, high_isec + 1)]
                temp_df = temp_df[temp_df[isec_col].str.contains('|'.join(allowed_strings), na=False)]
        else:
            return 0, 0

    if "Supplier Group" in temp_df.columns:
        online_count = len(temp_df[temp_df["Supplier Group"].astype(str).str.strip() == "Group MP"])
        offline_count = len(temp_df[(temp_df["Supplier Group"].astype(str).str.strip() == "None") | (temp_df["Supplier Group"].isna())])
    else:
        online_count, offline_count = 0, 0
    return online_count, offline_count

# =========================================================================
# 4. FIXED LAYOUT STRUCTURE MATRIX
# =========================================================================
layout_definition = [
    ["Desktop", "Device", "Desktop", 400, 160, 240],
    ["Mobile", "Device", "Mobile", 400, 160, 240],
    ["Tablet", "Device", "Tablet", 400, 160, 240],
    ["Device Total", "Total_Marker", "", 800, 320, 240],
    
    ["Delhi - 112", "City_Code", "112", 100, 100, 100],
    ["Jaipur - 120", "City_Code", "120", 100, 100, 100],
    ["Mumbai - 111", "City_Code", "111", 100, 100, 100],
    ["Hyderabad - 114", "City_Code", "114", 100, 100, 100],
    ["Lucknow - 121", "City_Code", "121", 100, 100, 100],
    ["City Total", "Total_Marker", "", 500, 500, 500],
    
    ["Male - 16-24", "Age-Gender", "Male:16-24", 50, 20, 30],
    ["Female - 16-24", "Age-Gender", "Female:16-24", 50, 20, 30],
    ["Male 25-44", "Age-Gender", "Male:25-44", 90, 36, 54],
    ["Female 25-44", "Age-Gender", "Female:25-44", 90, 36, 54],
    ["Male 45-75", "Age-Gender", "Male:45-75", 60, 24, 36],
    ["Female 45-75", "Age-Gender", "Female:45-75", 60, 24, 36],
    ["Gender-Age Total", "Total_Marker", "", 400, 160, 240],
    
    ["ISEC 1-3", "ISEC", "1-3", 80, 80, 0],
    ["ISEC 4-5", "ISEC", "4-5", 80, 80, 0],
    ["ISEC 6-7", "ISEC", "6-7", 120, 0, 120],
    ["ISEC 8-12", "ISEC", "8-12", 120, 0, 120],
    ["ISEC Total", "Total_Marker", "", 400, 160, 240]
]

final_rows = []
row_labels = []

for row in layout_definition:
    label, r_type, r_val, t_tgt, on_tgt, off_tgt = row
    row_labels.append(label)
    if r_type == "Total_Marker":
        final_rows.append([t_tgt, "100%", 0, on_tgt, 0, 0, off_tgt, 0, 0])
    else:
        on_col, off_col = get_counts(r_type, r_val)
        tot_col = on_col + off_col
        on_pend = on_tgt - on_col
        off_pend = off_tgt - off_col
        pct_text = f"{(t_tgt / 400)*100:,.0f}%" if t_tgt <= 400 else "100%"
        final_rows.append([t_tgt, pct_text, tot_col, on_tgt, on_col, on_pend, off_tgt, off_col, off_pend])

columns = pd.MultiIndex.from_tuples([
    ('TOTAL', 'Target'), ('TOTAL', 'Target %'), ('TOTAL', 'Collected'),
    ('GROUP MP (ONLINE)', 'Target'), ('GROUP MP (ONLINE)', 'Collected'), ('GROUP MP (ONLINE)', 'Pending'),
    ('MARKETEXCEL (OFFLINE)', 'Target'), ('MARKETEXCEL (OFFLINE)', 'Collected'), ('MARKETEXCEL (OFFLINE)', 'Pending')
])

report_df = pd.DataFrame(final_rows, index=row_labels, columns=columns)

# =========================================================================
# 5. RE-CALCULATE SECTION TOTALS (Synchronized with City layout keys)
# =========================================================================
device_rows = [row[0] for row in layout_definition if row[1] == "Device"]
city_rows = [row[0] for row in layout_definition if row[1] == "City_Code"] 
age_rows = [row[0] for row in layout_definition if row[1] == "Age-Gender"]
isec_rows = [row[0] for row in layout_definition if row[1] == "ISEC"]

dynamic_sections = [
    ("Device Total", device_rows),
    ("City Total", city_rows), 
    ("Gender-Age Total", age_rows),
    ("ISEC Total", isec_rows)
]

for section_tot, tracking_rows in dynamic_sections:
    if tracking_rows:
        report_df.loc[section_tot, ('TOTAL', 'Collected')] = report_df.loc[tracking_rows, ('TOTAL', 'Collected')].sum()
        report_df.loc[section_tot, ('GROUP MP (ONLINE)', 'Collected')] = report_df.loc[tracking_rows, ('GROUP MP (ONLINE)', 'Collected')].sum()
        report_df.loc[section_tot, ('MARKETEXCEL (OFFLINE)', 'Collected')] = report_df.loc[tracking_rows, ('MARKETEXCEL (OFFLINE)', 'Collected')].sum()
        report_df.loc[section_tot, ('GROUP MP (ONLINE)', 'Pending')] = report_df.loc[section_tot, ('GROUP MP (ONLINE)', 'Target')] - report_df.loc[section_tot, ('GROUP MP (ONLINE)', 'Collected')]
        report_df.loc[section_tot, ('MARKETEXCEL (OFFLINE)', 'Pending')] = report_df.loc[section_tot, ('MARKETEXCEL (OFFLINE)', 'Target')] - report_df.loc[section_tot, ('MARKETEXCEL (OFFLINE)', 'Collected')]

# Rendering styled display
def highlight_cols(val):
    return 'background-color: #FFFF99; color: black;'

styled_report = report_df.style.map(highlight_cols, subset=[('GROUP MP (ONLINE)', 'Collected'), ('MARKETEXCEL (OFFLINE)', 'Collected')])
st.dataframe(styled_report, use_container_width=True, height=750)
