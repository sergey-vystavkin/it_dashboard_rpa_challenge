import os

TEMP_PATH = os.path.join(os.getcwd(), 'temp')
DOWNLOADS_PATH = os.path.join(TEMP_PATH, 'downloads')
OUTPUT_PATH = os.path.join(os.getcwd(), 'output')
OUTPUT_EXCEL_NAME = 'Agencies data.xlsx'

config = {
    'agencies_url': 'http://itdashboard.gov/',
    'agency_name': 'National Science Foundation',
    'excel': {
        'agencies_sheet': 'Agencies',
        'agencies_col_names': ['Agency name', 'Amount'],
        'individual_sheet': 'Individual Investments'
    },
    'web': {
        'uii_col': 'uii',
        'title_col': 'investment title'
    }
}
