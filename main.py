import os
import traceback
from shutil import rmtree, move

from os import listdir
from loguru import logger

from settings.config import config, TEMP_PATH, DOWNLOADS_PATH, OUTPUT_PATH, OUTPUT_EXCEL_NAME
from sources.excel import write_amounts_to_excel, write_individual_investments_to_excel
from sources import web


def create_temp_folder():
    if os.path.exists(TEMP_PATH):
        rmtree(TEMP_PATH)
    os.mkdir(TEMP_PATH)
    os.mkdir(DOWNLOADS_PATH)


def move_files_to_output():
    if os.path.exists(OUTPUT_PATH):
        rmtree(OUTPUT_PATH)
    os.mkdir(OUTPUT_PATH)
    move(os.path.join(TEMP_PATH, OUTPUT_EXCEL_NAME), os.path.join(OUTPUT_PATH, OUTPUT_EXCEL_NAME))
    for file_name in listdir(DOWNLOADS_PATH):
        move(os.path.join(DOWNLOADS_PATH, file_name), os.path.join(OUTPUT_PATH, file_name))


def main():
    logger.info('Start bot execution')
    logger.info(OUTPUT_PATH)
    create_temp_folder()
    try:
        web.open_the_website(config['agencies_url'])

        logger.info('Start scrap data about agencies')
        agencies_data = web.scrap_data()
        logger.info(f'Successfully collected data of {len(agencies_data)} agencies')

        logger.info(f'Write data about agencies to workbook "{OUTPUT_EXCEL_NAME}"')
        write_amounts_to_excel(agencies_data, workbook_path=os.path.join(TEMP_PATH, OUTPUT_EXCEL_NAME))

        logger.info(f'Start scrap data about {config["agency_name"]} agency')
        scraped_data_for_excel = web.scrape_agency_table(config["agency_name"])
        logger.info(f'Successfully collected data of {len(scraped_data_for_excel)} Individual Investments')

        logger.info(f'Write data about Individual Investments to workbook "{OUTPUT_EXCEL_NAME}"')
        write_individual_investments_to_excel(scraped_data_for_excel,
                                              workbook_path=os.path.join(TEMP_PATH, OUTPUT_EXCEL_NAME))
        logger.info(f'Move files to output')
        move_files_to_output()
    except Exception as exception:
        traceback.print_exc()
        logger.error(str(exception))
    finally:
        web.close_driver()

    logger.info('Finish bot execution')


if __name__ == '__main__':
    main()
