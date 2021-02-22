from os import path
from RPA.PDF import PDF


def get_investment_info_from_pdf(path_to_file):
    _, extension = path.splitext(path_to_file)
    if extension.lower() != '.pdf':
        raise Exception(f"File '{path.basename(path_to_file)}' has wrong extension, it should be .pdf for reading data")

    pdf_pages_text = PDF().get_text_from_pdf(path_to_file)
    all_text = '\n'.join(pdf_pages_text.values())

    try:
        section_start = all_text.lower().index('section a:')
        section_end = all_text.lower().index('section b:')
        section_text = all_text[section_start:section_end]
    except ValueError:
        raise Exception(f"Can't found Section A in file '{path.basename(path_to_file)}'")

    investment_name_key = '1. Name of this Investment:'
    uii_key = '2. Unique Investment Identifier (UII):'

    try:
        investment_name_idx = section_text.lower().index(investment_name_key.lower())
        uii_idx = section_text.lower().index(uii_key.lower())
    except ValueError:
        raise Exception(f"Can't found required key strings in Section A in file '{path.basename(path_to_file)}'")

    investment_name = section_text[investment_name_idx + len(investment_name_key):uii_idx].strip()
    uii = section_text[uii_idx + len(uii_key):].strip()

    return investment_name, uii
