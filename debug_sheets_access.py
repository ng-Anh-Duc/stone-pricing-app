import os
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

print("=== Google Sheets Access Debugger ===\n")

# 1. Check environment variables
spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
print(f"1. Spreadsheet ID from .env: {spreadsheet_id}")

# 2. Check credentials file
creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
if os.path.exists(creds_path):
    print(f"2. Credentials file found: {creds_path}")
    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
        service_account_email = creds_data.get('client_email')
        print(f"   Service account email: {service_account_email}")
        print(f"   ⚠️  Make sure this email has access to the spreadsheet!")
else:
    print(f"2. ❌ Credentials file not found: {creds_path}")
    exit(1)

# 3. Test different access methods
print("\n3. Testing access methods...")

# Method A: Direct URL test (if publicly accessible)
print("\n   A. Testing public access...")
public_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
try:
    response = requests.get(public_url, timeout=5)
    if response.status_code == 200:
        print("      ✅ Sheet is publicly accessible")
    else:
        print(f"      ❌ Not publicly accessible (status: {response.status_code})")
except Exception as e:
    print(f"      ❌ Error: {e}")

# Method B: API access with service account
print("\n   B. Testing API access with service account...")
try:
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly']
    )
    
    # Try Sheets API
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # Test 1: Get spreadsheet metadata
    print("      Testing spreadsheet metadata access...")
    try:
        result = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields='properties.title,sheets.properties.title'
        ).execute()
        print(f"      ✅ Can access spreadsheet: {result['properties']['title']}")
        sheets = [s['properties']['title'] for s in result.get('sheets', [])]
        print(f"      Available sheets: {sheets}")
    except HttpError as e:
        print(f"      ❌ Cannot access spreadsheet metadata: {e}")
        print(f"         Error details: {e.error_details}")
    
    # Test 2: Try to read a single cell
    print("\n      Testing cell read access...")
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A1'
        ).execute()
        print(f"      ✅ Can read cells")
    except HttpError as e:
        print(f"      ❌ Cannot read cells: {e}")
    
    # Try Drive API to check file type
    print("\n   C. Testing Drive API access...")
    drive_service = build('drive', 'v3', credentials=creds)
    try:
        file_metadata = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='name,mimeType,capabilities,shared,ownedByMe,permissions'
        ).execute()
        
        print(f"      File name: {file_metadata.get('name')}")
        print(f"      MIME type: {file_metadata.get('mimeType')}")
        print(f"      Owned by me: {file_metadata.get('ownedByMe')}")
        print(f"      Shared: {file_metadata.get('shared')}")
        
        # Check if it's actually a Google Sheets file
        if file_metadata.get('mimeType') != 'application/vnd.google-apps.spreadsheet':
            print(f"      ⚠️  WARNING: This is not a Google Sheets file!")
            print(f"         Actual type: {file_metadata.get('mimeType')}")
    except HttpError as e:
        print(f"      ❌ Cannot access via Drive API: {e}")
        if e.resp.status == 404:
            print("         File not found or no access")
        elif e.resp.status == 403:
            print("         Permission denied")

except Exception as e:
    print(f"   ❌ API setup error: {e}")

# 4. Test with different sheet names
print("\n4. Testing sheet name access...")
sheet_names_to_test = [
    'cPhuong_last_check',
    'c Phuong_check (add usd_m3)',
    'Sheet1'
]

try:
    sheets_service = build('sheets', 'v4', credentials=creds)
    for sheet_name in sheet_names_to_test:
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1"
            ).execute()
            print(f"   ✅ Can access sheet: '{sheet_name}'")
        except HttpError as e:
            if '400' in str(e):
                print(f"   ❌ Sheet not found: '{sheet_name}'")
            else:
                print(f"   ❌ Error accessing '{sheet_name}': {e}")
except:
    pass

# 5. Alternative spreadsheet ID test
print("\n5. Checking if the ID might be from a different document...")
print(f"   Google Sheets URL should look like:")
print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
print(f"   ")
print(f"   Your URL would be:")
print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
print(f"   ")
print(f"   ⚠️  Please verify this URL opens a Google Sheets document in your browser")

print("\n=== Debugging Complete ===")
print("\nPossible solutions:")
print("1. Verify the spreadsheet ID is correct (from a Google Sheets URL)")
print("2. Make sure the service account email has been granted access to the sheet")
print("3. If it's in a shared drive, additional permissions may be needed")
print("4. Check if the document is actually a Google Sheets file (not Docs/Slides)")