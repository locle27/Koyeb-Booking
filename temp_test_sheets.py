
import os
os.environ["DEFAULT_SHEET_ID"] = "13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w"
os.environ["GCP_CREDS_FILE_PATH"] = "credentials.json"
os.environ["GOOGLE_API_KEY"] = "AIzaSyA-0V4VgrJbnzQWueDVI9pSOoH_V2EMUg4"

try:
    from logic import import_from_gsheet
    df = import_from_gsheet(
        "13kQETOUGCVUwUqZrxeLy-WAj3b17SugI4L8Oq09SX2w",
        "credentials.json"
    )
    print(f"SUCCESS: Google Sheets loaded {len(df)} records")
except Exception as e:
    print(f"ERROR: {str(e)}")
