import os
import time
from datetime import datetime, timedelta

from RPA.Browser.Selenium import ChromeOptions, webdriver
from selenium.common.exceptions import StaleElementReferenceException
from os import listdir
from loguru import logger

from settings.config import DOWNLOADS_PATH, config
from sources.pdf import get_investment_info_from_pdf


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DriverKeeper(metaclass=Singleton):
    def __init__(self):
        self.__driver = None

    def open_browser(self):
        self.__driver = webdriver.webdriver.Chrome(options=_get_chrome_options())
        return self.__driver

    def get_driver(self):
        if self.__driver is None:
            raise Exception('You need to open browser before getting browser')
        return self.__driver


def _get_chrome_options():
    options = ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--disable-gpu")
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('prefs', {'download.default_directory': DOWNLOADS_PATH})
    return options


def __wait_while_file_downloaded(files_before_downloading):
    seconds_for_download = 30
    finish_time = datetime.now() + timedelta(seconds=seconds_for_download)
    while True:
        files = listdir(DOWNLOADS_PATH)
        new_files = [file for file in files if file not in files_before_downloading]
        if new_files and not any([file.split('.')[-1] in ['tmp', 'crdownload'] for file in new_files]):
            return new_files[0]
        if finish_time < datetime.now():
            raise Exception(f"Can't download the file for {seconds_for_download} seconds")


def __download_pdf_file(link):
    driver = DriverKeeper().get_driver()
    main_tab = driver.current_window_handle
    driver.execute_script('window.open(arguments[0]);', link)

    new_tab = [window for window in driver.window_handles if window != main_tab][0]
    driver.switch_to.window(new_tab)

    driver.implicitly_wait(15)
    download_link_elem = driver.find_element_by_xpath("//*[@id='business-case-pdf']/a")
    files_before_downloading = listdir(DOWNLOADS_PATH)
    download_link_elem.click()
    file_name = __wait_while_file_downloaded(files_before_downloading)
    # Close new tab
    driver.close()

    driver.switch_to.window(main_tab)
    return file_name


def open_the_website(url):
    logger.info('Start creating webdriver')
    try:
        driver = DriverKeeper().open_browser()
    except Exception as exc:
        logger.error(f"Catch exception during creating webdriver: {str(exc)}")
        raise exc
    logger.info(f'Open url: "{url}"')
    driver.get(url)


def close_driver():
    try:
        driver = DriverKeeper().get_driver()
        driver.close()
        driver.quit()
    except Exception:
        pass


def scrap_data():
    """
    Get a list of agencies and the amount of spending from the main page
    """
    driver = DriverKeeper().get_driver()

    driver.implicitly_wait(15)
    # Click "DIVE IN" on the homepage to reveal the spend amounts for each agency
    dive_in_button = driver.find_element_by_xpath("//*[@id='node-23']//a[@aria-controls='home-dive-in']")
    is_dive_in_clicked = dive_in_button.get_attribute('aria-expanded')
    if is_dive_in_clicked == 'false':
        dive_in_button.click()

    agencies_block = driver.find_element_by_xpath("//*[@id='agency-tiles-widget']")

    agencies_cols = agencies_block.find_elements_by_class_name("col-sm-4")

    agencies_data = []
    for agency_col in agencies_cols:
        agency_spans = agency_col.find_elements_by_tag_name('span')
        if len(agency_spans) > 1:
            agencies_data.append({'name': agency_spans[0].text, 'amount': agency_spans[1].text})
    logger.info(f'Successfully collected data on {len(agencies_data)} agencies')
    return agencies_data


def __click_agency_link(agency_name: str):
    agency_name = agency_name.lower().strip()

    agencies_link_elements = DriverKeeper().get_driver().find_elements_by_xpath("//*[@id='agency-tiles-widget']//a")

    for link_elem in agencies_link_elements:
        link_text_strings = str(link_elem.text).split('\n')
        if any([agency_name == string.lower().strip() for string in link_text_strings]):
            link_elem.click()
            break
    else:
        raise Exception(f"Can't found agency with name '{agency_name}'")


def scrape_agency_table_page(header_values):
    """
    Read table rows. If the "UII" column contains a link, open it and download PDF with Business Case,
    extract data from PDF and compare the value "Name of this Investment" with the column "Investment Title",
    and the value "Unique Investment Identifier (UII)" with the column "UII"
    """
    uii_col_inx = [val.strip().lower() for val in header_values].index(config['web']['uii_col'])
    investment_title_col_inx = [val.strip().lower() for val in header_values].index(config['web']['title_col'])

    investments_table_rows = DriverKeeper().get_driver().find_elements_by_xpath(
        xpath="//*[@id='investments-table-object']/tbody/tr")

    table_page_data = []
    for row in investments_table_rows:
        row_elements = row.find_elements_by_xpath('.//td')
        if len(row_elements) <= uii_col_inx:
            continue

        # If the "UII" column contains a link, open it and download PDF with Business Case
        a_elements = row_elements[uii_col_inx].find_elements_by_xpath('.//a')
        if a_elements:
            link = a_elements[0].get_attribute('href')
            table_investment_title = row_elements[investment_title_col_inx].text

            logger.info(f'Download Business Case PDF of "{table_investment_title}" Investment')
            file_name = __download_pdf_file(link)

            # Extract data from PDF and compare them with table values
            logger.info(f'Check Business Case PDF file of "{table_investment_title}" Investment')
            pdf_investment_name, pdf_uii = get_investment_info_from_pdf(os.path.join(DOWNLOADS_PATH, file_name))

            table_uii = row_elements[uii_col_inx].text

            uii_match = str(table_uii).strip().lower() == str(pdf_uii).strip().lower()
            investment_match = str(table_investment_title).strip().lower() == str(
                pdf_investment_name).strip().lower()
            if uii_match and investment_match:
                logger.info(f"Values in the file match the values in the table")
            else:
                if not uii_match:
                    logger.warning(
                        f"UII value of '{table_investment_title}' in table does not match the value in PDF file")
                if not investment_match:
                    logger.warning(
                        f"Investment Title '{table_investment_title}' in table does not match the value in PDF file")

        row_values = [str(elem.text) for elem in row_elements]
        table_page_data.append(row_values)
    return table_page_data


def scrape_agency_table(agency_name: str):
    """
    Select one of the agencies - {agency_name} and
    going to the agency page scrape a table with all "Individual Investments"
    """
    driver = DriverKeeper().get_driver()
    __click_agency_link(agency_name)

    investment_table_data = []

    driver.implicitly_wait(30)
    # Get table header
    table_header = driver.find_element_by_xpath("//*[contains(@class, 'datasource-table')]//tr[@role='row']")
    header_elements = table_header.find_elements_by_xpath('.//th')
    header_values = [str(elem.text) for elem in header_elements]
    investment_table_data.append(header_values)

    while True:
        row_values = scrape_agency_table_page(header_values)
        investment_table_data.extend(row_values)

        # Click next paginate button if required
        current_paginate_btn_xpath = "//*[@id='investments-table-object_paginate']//a[@class='paginate_button current']"
        current_paginate_btn = driver.find_element_by_xpath(current_paginate_btn_xpath).text

        next_button = driver.find_element_by_xpath("//*[@id='investments-table-object_next']")
        next_button_class = next_button.get_attribute('class')
        if 'disabled' not in str(next_button_class).split(' '):
            next_button.click()
            for attempt in range(1, 20):
                try:
                    new_current_paginate_btn = driver.find_element_by_xpath(current_paginate_btn_xpath).text
                    if new_current_paginate_btn != current_paginate_btn:
                        current_paginate_btn = new_current_paginate_btn
                        break
                except StaleElementReferenceException:
                    pass
                time.sleep(1)
            else:
                raise Exception('Next page of investments table not load for a long time')
        else:
            return investment_table_data
