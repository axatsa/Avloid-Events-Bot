import gspread
from google.oauth2.service_account import Credentials
import os

# Scopes required for Google Sheets and Google Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

MASTER_SPREADSHEET_NAME = "Avlod Adventures - Event Registrations"

def get_gc():
    if not os.path.exists("service_account.json"):
        return None
    creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    return gspread.authorize(creds)

def add_to_sheet(event_name, user_data):
    """
    event_name: Name of the event (will be the worksheet title)
    user_data: dict with {'full_name': ..., 'phone': ...}
    """
    gc = get_gc()
    if not gc:
        print("Google Sheets credentials not found.")
        return False

    try:
        # Try to open existing master spreadsheet
        try:
            sh = gc.open(MASTER_SPREADSHEET_NAME)
        except gspread.SpreadsheetNotFound:
            # Create new master spreadsheet if not found
            sh = gc.create(MASTER_SPREADSHEET_NAME)
            # Share with anyone with the link (optional)
            # sh.share(None, perm_type='anyone', role='reader')
        
        # Try to find worksheet for this event
        try:
            worksheet = sh.worksheet(event_name)
        except gspread.WorksheetNotFound:
            # Create new worksheet for this event
            worksheet = sh.add_worksheet(title=event_name, rows=100, cols=5)
            # Add headers
            worksheet.append_row(["ФИО", "Номер телефона"])
        
        # Add user data
        worksheet.append_row([user_data['full_name'], user_data['phone']])
        return True
    except Exception as e:
        print(f"Error adding to Google Sheets: {e}")
        return False
