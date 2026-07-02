import streamlit as st
import pandas as pd
import io
import requests

st.set_page_config(layout="wide")

st.title("📊 ZAPPI SERVICES MARKET PERFORMANCE REVIEW - DASHBOARD")
st.markdown("---")

# =========================================================================
# 1. CLOUD FILE CONFIGURATION (Direct Cloud Sync)
# =========================================================================
FILE_ID = "1jGrpT9e0utjvIUHS-CzZ441ml8YUpx1A" 
GOOGLE_DRIVE_URL = f"https://drive.google.com/uc?id={FILE_ID}&export=download"

@st.cache_data(ttl=600)  
def load_excel_from_cloud(url):
    try:
        session = requests.Session()
        response = session.get(url, stream=True)
        
        if response.status_code == 404:
            st.warning("⚠️ The source file 'Zapi_rawdata.xlsx' has been deleted or moved from Google Drive.")
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
        return pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
    except Exception as e:
        st.warning("⚠️ Source data file not found on Google Drive.")
        return pd.DataFrame()

raw_df = load_excel_from_cloud(GOOGLE_DRIVE_URL)

if raw_df.empty:
    st.info("💡 Please upload the raw data file back to the Google Drive folder to resume tracking.")
    st.stop()

# Clean column spaces safely and quickly
raw_df.columns = raw_df.columns.astype(str).str.strip()

# Drop rows that don't have a valid project name to eliminate ghost excel padding rows
raw_df = raw_df.dropna(subset=["Project Name"])

# =========================================================================
# 2. SIDEBAR FRONT-END FILTERS 
# =========================================================================
with st.sidebar:
    st.header("🔍 Filter Parameters")
    st.caption("💡 Click inside any box and type characters to search instantly.")
    
    available_markets = list(raw_df["Survey Country"].unique()) if "Survey Country" in raw_df.columns else ["India"]
    selected_markets = st.multiselect("Market (Country)", available_markets, default=available_markets)

    filtered_by_market = raw_df[raw_df["Survey Country"].isin(selected_markets)]

    available_languages = list(filtered_by_market["Survey Language"].unique()) if "Survey Language" in filtered_by_market.columns else ["English"]
    selected_langs = st.multiselect("Language", available_languages, default=available_languages)

    filtered_by_lang = filtered_by_market[filtered_by_market["Survey Language"].isin(selected_langs)]

    available_projects = list(filtered_by_lang["Project Name"].unique()) if "Project Name" in filtered_by_lang.columns else []
    selected_projects = st.multiselect("Project Name", available_projects, default=available_projects)

project_df = filtered_by_lang[filtered_by_lang["Project Name"].isin(selected_projects)]

available_projects_preview = list(raw_df["Project Name"].unique()) if "Project Name" in raw_df.columns else []
st.markdown(f"📊 **Currently Analyzing Total Volume across: {len(available_projects_preview)} Registered Projects**")

# =========================================================================
# 3. GLOBAL MATRIX COUNTING LOGIC (Clean direct column lookup)
# =========================================================================
st.markdown("### Quota Performance Summary")

def get_counts(row_type, row_val):
    if raw_df.empty:
        return 0, 0
    temp_df = raw_df.copy()
    
    if row_type == "Device":
        temp_df = temp_df[temp_df["Device"].astype(str).str.strip().str.lower() == str(row_val).strip().lower()]
        
    elif row_type == "City_Code":
        if "City_Code" in temp_df.columns:
            temp_df["City_Match_Lower"] = temp_df["City_Code"].fillna("unknown").astype(str).str.strip().str.lower()
            
            if row_val == "Other_Unassigned":
                known_cities = ["delhi", "jaipur", "mumbai", "hyderabad", "lucknow"]
                temp_df = temp_df[~temp_df["City_Match_Lower"].str.contains('|'.join(known_cities), na=False)]
            else:
                target_str = str(row_val).strip().lower()
                temp_df = temp_df[temp_df["City_Match_Lower"].str.contains(target_str, na=False)]
        else:
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
        offline_count = len(temp_df) - online_count
    else:
        online_count = len(temp_df)
        offline_count = 0
        
    return online_count, offline_count

# =========================================================================
# 4. FIXED LAYOUT STRUCTURE MATRIX
# =========================================================================
layout_definition = [
    ["Desktop", "Device", "Desktop", 400, 160, 240],
    ["Mobile", "Device", "Mobile", 400, 160, 240],
    ["Tablet", "Device", "Tablet", 400, 160, 240],
    ["Device Total", "Total_Marker", "", 800, 320, 240],
    
    ["Delhi - 112", "City_Code", "Delhi", 100, 100, 100],
    ["Jaipur - 120", "City_Code", "Jaipur", 100, 100, 100],
    ["Mumbai - 111", "City_Code", "Mumbai", 100, 100, 100],
    ["Hyderabad - 114", "City_Code", "Hyderabad", 100, 100, 100],
    ["Lucknow - 121", "City_Code", "Lucknow", 100, 100, 100],
    ["Unassigned / Blanks", "City_Code", "Other_Unassigned", 0, 0, 0],
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

]
