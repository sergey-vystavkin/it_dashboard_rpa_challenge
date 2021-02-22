import os

from RPA.Excel.Files import Files
from settings.config import config


def __get_workbook(workbook_path):
    lib = Files()
    if os.path.exists(workbook_path):
        return lib.open_workbook(workbook_path)
    else:
        return lib.create_workbook(workbook_path)


def write_amounts_to_excel(agencies_data, workbook_path):
    """
    Write the amounts to an excel file and call the sheet "Agencies"
    """
    workbook = __get_workbook(workbook_path)

    sheet_name = workbook.sheetnames[0]
    workbook.rename_worksheet(config['excel']['agencies_sheet'], sheet_name)

    cell_values_for_writing = [config['excel']['agencies_col_names']]
    cell_values_for_writing.extend([[agency_data['name'], agency_data['amount']] for agency_data in agencies_data])

    for row_idx, row_values in enumerate(cell_values_for_writing):
        for col_idx, value in enumerate(row_values):
            workbook.set_cell_value(row_idx + 1, col_idx + 1, value)
    workbook.save()


def write_individual_investments_to_excel(cell_values_for_writing, workbook_path):
    """
    Write scraped data from table with all "Individual Investments" to a new sheet in excel
    """
    workbook = __get_workbook(workbook_path)

    sheet_name = config['excel']['individual_sheet']
    workbook.create_worksheet(sheet_name)

    for row_idx, row_values in enumerate(cell_values_for_writing):
        for col_idx, value in enumerate(row_values):
            workbook.set_cell_value(row_idx + 1, col_idx + 1, value, sheet_name)
    workbook.save()
