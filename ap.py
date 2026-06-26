Python
# =========================================================================
# 1. FILE CONFIGURATION (Google Drive Cloud Setup)
# =========================================================================
import io
import requests

# The Folder ID provided: 1fFcmQFcKUYGtr5_IpMQ7V6cal0k15vzd
# To make this seamless, you need the File ID of 'Zapi_rawdata.xlsx' inside that folder.
# Ensure the file is set to "Anyone with the link can view" or shared within your organization.

# 💡 Replace 'YOUR_FILE_ID_HERE' with the actual ID of the Zapi_rawdata.xlsx file
FILE_ID = "1VKas4go8yq32otZ7acyUlEdZnpOAbovy" 
GOOGLE_DRIVE_URL = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data(ttl=600)  # Caches data for 10 minutes, then auto-checks Google Drive for updates
def load_excel_data_from_drive(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Read the file directly into memory from the cloud response
        return pd.read_excel(io.BytesIO(response.content))
    except Exception as e:
        st.error(f"❌ Failed to fetch data from Google Drive: {e}")
        return pd.DataFrame()

raw_df = load_excel_data_from_drive(GOOGLE_DRIVE_URL)

if raw_df.empty:
    st.stop()

# Clean column spaces just in case
raw_df.columns = raw_df.columns.str.strip()