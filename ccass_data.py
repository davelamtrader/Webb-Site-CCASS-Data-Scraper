import requests
from bs4 import BeautifulSoup
import csv
import json
import time
from datetime import date, datetime, timedelta
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
import random
from get_proxies import get_proxies_list, read_user_agents


pd.options.display.width = None
pd.options.display.max_columns = None
pd.set_option('display.max_rows', 10000)
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_colwidth', 100)



def safe_inspect(soup, selector):
    element = soup.select_one(selector)
    return element


def safe_inspect_selenium(driver, locator, value):
    try:
        return driver.find_element(locator, value)
    except (StaleElementReferenceException, NoSuchElementException):
        return None


def submit_recaptcha(chrome_path, url):

    def move_mouse_to_element(driver, element):
        action = ActionChains(driver)
        offset_x, offset_y = random.randint(-10, 10), random.randint(-10, 10)  # Random offset
        action.move_to_element_with_offset(element, offset_x, offset_y).perform()
        # action.click().perform()

    def random_sleep(min_seconds=1, max_seconds=3):
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)

    def random_scroll(driver, scrolls=3):
        for _ in range(scrolls):
            driver.execute_script("window.scrollBy(0, 200);")
            random_sleep()

    webdriver_service = Service(chrome_path)
    chrome_options = Options()
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(url)
    time.sleep(1)

    random_scroll(driver)
    iframe = driver.find_elements(By.TAG_NAME, 'iframe')[0]
    move_mouse_to_element(driver, iframe)
    random_sleep()
    random_scroll(driver)
    driver.switch_to.frame(iframe)

    tickbox = safe_inspect_selenium(driver, By.ID, 'recaptcha-anchor')
    if tickbox is not None:
        move_mouse_to_element(driver, tickbox)
        tickbox.click()
        time.sleep(1)
        driver.switch_to.default_content()
        submit = safe_inspect_selenium(driver, By.XPATH, '/html/body/div[4]/form/input[1]')
        if submit is not None:
            move_mouse_to_element(driver, submit)
            submit.click()
            print('Re-captcha successfully bypassed!')

    time.sleep(600)


def get_hsi_tickers(chrome_path):
    url = 'http://www.aastocks.com/en/stocks/market/index/hk-index-con.aspx?index=HSI'
    webdriver_service = Service(chrome_path)
    chrome_options = Options()
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(url)
    time.sleep(2)

    body = driver.find_element(By.XPATH, '//*[@id="stock"]')
    for i in range(10):
        if i == 9:
            time.sleep(1)
            table = driver.find_element(By.ID, 'tblTS2')
            rows = table.find_elements(By.TAG_NAME, 'a')
            codes = [row.text[1:-3] for row in rows if row.get_attribute('class') == 'bmpLnk cls']
            print(codes)
            filepath = '#hsi_tickers.csv'
            with open(filepath, 'w', newline='') as file:
                for code in codes:
                    file.write(code + '\n')
                file.close()
            break
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)

    return codes


def get_hti_tickers(chrome_path):
    url = 'http://www.aastocks.com/en/stocks/market/index/hk-index-con.aspx?index=HSTECH'
    webdriver_service = Service(chrome_path)
    chrome_options = Options()
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(url)
    time.sleep(2)

    body = driver.find_element(By.XPATH, '//*[@id="stock"]')
    for i in range(10):
        if i == 9:
            time.sleep(1)
            table = driver.find_element(By.ID, 'tblTS2')
            rows = table.find_elements(By.TAG_NAME, 'a')
            codes = [row.text[1:-3] for row in rows if row.get_attribute('class') == 'bmpLnk cls']
            print(codes)
            filepath = '#hti_tickers.csv'
            with open(filepath, 'w', newline='') as file:
                for code in codes:
                    file.write(code + '\n')
                file.close()
            break
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)

    return codes


def get_ticker_list(filename):
    ticker_list = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in list(reader):
            temp = row[0]
            ticker = temp[:-3]
            ticker_list.append(ticker)

    return ticker_list


def generate_dates(start_date, end_date, public_holidays):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []

    public_holidays = [datetime.strptime(date, "%Y-%m-%d") for date in public_holidays]

    delta = timedelta(days=1)
    while start_date <= end_date:
        if start_date.weekday() not in [5, 6] and start_date not in public_holidays:
            date_list.append(start_date.strftime("%Y-%m-%d"))
        start_date += delta

    return date_list


def get_public_holidays(headers, start_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.today()
    year_list = []

    while start_date <= end_date:
        year_list.append(str(start_date.year))
        start_date += timedelta(days=365)

    holiday_dict = {}
    dates_list = []
    for year in year_list:
        url = f'https://www.timeanddate.com/holidays/hong-kong/{year}?hol=1'
        page = requests.get(url, headers=headers)
        time.sleep(sleep)
        soup = BeautifulSoup(page.text, "html.parser")

        holidate_list = []
        table = soup.find('table', {'id': 'holidays-table'})
        for row in table.find_all('tr', {'class': 'showrow'}):
            raw_date = row.find('th').text
            date = '0' + raw_date if ' ' in raw_date[:2] else raw_date
            wd = row.find_all('td')[0].text
            holidate = f"{year}-{datetime.strptime(date, '%d %b').strftime('%m-%d')}"
            print(holidate)
            holidate_list.append((holidate, wd))
            dates_list.append(holidate)

        holiday_dict[year] = holidate_list

    with open(f'#public_holidays_to_{end_date.year}.json', 'w') as json_file:
        json.dump(holiday_dict, json_file)

    with open(f'#public_holidays_to_{end_date.year}.csv', 'w') as file:
        for date in dates_list:
            file.write(date + '\n')
        file.close()

    return holiday_dict, dates_list


def get_ticker_holdings_snapshots(ua, ticker, dates, root, proxy):
    values_dict = {}
    for date in dates:
        url = f'https://webb-site.com/ccass/choldings.asp?sort=holddn&sc={ticker}&d={date}'
        print(url)
        headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
        page = requests.get(url, headers=headers, proxies=proxy)
        time.sleep(sleep)
        soup = BeautifulSoup(page.text, "html.parser")

        summary_head = ['Type of holder', 'Holding', 'Stake %']
        summary_table = soup.find('table', {'class': 'optable'})
        sum_dict_list = []
        for row in summary_table.find_all('tr')[1:]:
            td_holders = row.find_all('td')
            row_text = [td.text for td in td_holders]
            single_dict = dict(zip(summary_head, row_text))
            sum_dict_list.append(single_dict)

        details_head = ['Rank', 'CCASS ID', 'Name', 'Holding', 'Last Change', 'Stake %', 'Cumulative Stake %']
        details_table = soup.find('table', {'class': 'optable yscroll'})
        det_dict_list = []
        for row in details_table.find_all('tr')[1:]:
            td_holders = row.find_all('td')
            row_text = [td.text for td in td_holders]
            row_text[0] = row_text[0].replace('\r\n\t\t\t\t\t', '').replace('\t', '')
            if row_text[2] in ['Unnamed Investor Participants', 'Total securities in CCASS', 'Securities not in CCASS']:
                row_text[5] = row_text[5].replace('\r\n\t\t\t\t', '').replace('\t', '')
            else:
                row_text[5] = row_text[5].replace('\r\n\t\t\t\t\t\t', '')
            single_dict = dict(zip(details_head, row_text))
            det_dict_list.append(single_dict)

        snapshot_dict = {'summary': sum_dict_list, 'details': det_dict_list}
        values_dict[date] = snapshot_dict
        ticker_dict = {ticker: {date: snapshot_dict}}

        d = datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        sub = os.path.join(root, 'snapshots')
        subdir = os.path.join(sub, ticker)
        os.makedirs(subdir, exist_ok=True)
        filepath = os.path.join(subdir, f'{ticker}_holdings_snapshot_{d}.json')
        with open(filepath, 'w') as json_file:
            json.dump(ticker_dict, json_file)
        print(f'Successfully scrape the required data of {ticker} for date {d}!')

    result_dict = {ticker: values_dict}
    time.sleep(0.5)
    return result_dict


def get_ticker_holdings_change(ua, ticker, dates, root, proxy):
    values_dict = {}
    for date in dates:
        url = f'https://webb-site.com/ccass/chldchg.asp?sort=chngdn&sc={ticker}&d={date}'
        print(url)
        headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
        page = requests.get(url, headers=headers, proxies=proxy)
        time.sleep(sleep)
        soup = BeautifulSoup(page.text, "html.parser")

        table_head = ['Rank', 'CCASS ID', 'Name', 'Holding', 'Change', 'Stake %', 'Stake Change %', 'Last Holding']
        table = soup.find('table', {'class': 'optable yscroll'})
        single_dict_list = []
        for row in table.find_all('tr')[1:]:
            td_holders = row.find_all('td')
            row_text = [td.text for td in td_holders]
            if row_text[2] in ['Unnamed Investor Participants', 'Total securities in CCASS', 'Securities not in CCASS']:
                row_text[6] = row_text[6].replace('\r\n\t\t\t\t', '').replace('\t', '')
            single_dict = dict(zip(table_head, row_text))
            single_dict_list.append(single_dict)

        values_dict[date] = single_dict_list
        ticker_dict = {ticker: {date: single_dict_list}}

        d = datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        sub = os.path.join(root, 'holdings change')
        subdir = os.path.join(sub, ticker)
        os.makedirs(subdir, exist_ok=True)
        filepath = os.path.join(subdir, f'{ticker}_holdings_change_{d}.json')
        with open(filepath, 'w') as json_file:
            json.dump(ticker_dict, json_file)
        print(f'Successfully fetch the holdings change data of {ticker} for date {d}!')

    result_dict = {ticker: values_dict}
    time.sleep(0.5)
    return result_dict


def get_ticker_holdings_big_change(ua, ticker, today, root, proxy):
    url = f'https://webb-site.com/ccass/bigchangesissue.asp?sc={ticker}'
    print(url)
    headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
    page = requests.get(url, headers=headers, proxies=proxy)
    time.sleep(sleep)
    soup = BeautifulSoup(page.text, "html.parser")

    table_head = ['Row', 'Change Date', 'Participant', 'Change %', 'Previous Change Date']
    table = soup.find('table', {'class': 'numtable yscroll'})
    single_dict_list = []
    for row in table.find_all('tr')[1:]:
        td_holders = row.find_all('td')
        row_text = [td.text for td in td_holders]
        row_text[1] = row_text[1].replace('\n', '')
        single_dict = dict(zip(table_head, row_text))
        single_dict_list.append(single_dict)

    ticker_dict = {ticker: single_dict_list}
    
    subdir = os.path.join(root, 'holdings big change')
    filepath = os.path.join(subdir, f'{ticker}_holdings_big_change.json')
    with open(filepath, 'w') as json_file:
        json.dump(ticker_dict, json_file)
    print(f'Successfully fetch the holdings big change of {ticker}!')
    
    time.sleep(0.5)
    return ticker_dict


def get_ticker_concentration_history(ua, ticker, today, root, proxy):
    url = f'https://webb-site.com/ccass/cconchist.asp?sc={ticker}'
    print(url)
    headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
    page = requests.get(url, headers=headers, proxies=proxy)
    time.sleep(sleep)
    soup = BeautifulSoup(page.text, "html.parser")

    table_head = ['Date', 'Top5 %', 'Top10 %', 'Top10+NCIP %', 'Stake in CCASS %']
    table = soup.find('table', {'class': 'numtable yscroll'})
    single_dict_list = []
    for row in table.find_all('tr')[1:]:
        td_holders = row.find_all('td')[1:]
        row_text = [td.text for td in td_holders]
        single_dict = dict(zip(table_head, row_text))
        single_dict_list.append(single_dict)

    ticker_dict = {ticker: single_dict_list}
    
    subdir = os.path.join(root, 'concentration history')
    filepath = os.path.join(subdir, f'{ticker}_concentration_hist.json')
    with open(filepath, 'w') as json_file:
        json.dump(ticker_dict, json_file)
    print(f'Successfully fetch the concentration history of {ticker}!')
    
    time.sleep(0.5)
    return ticker_dict


def get_sh_holdings(ua, dates, root, proxies): 
    dict_list = []    
    for date in dates:
        url = f'https://webb-site.com/ccass/cholder.asp?part=1323&d={date}&z=False&sort=valndn'
        headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
        # page = requests.get(url, headers=headers, proxies=random.choice(proxies))
        page = requests.get(url, headers=headers)
        time.sleep(2)
        soup = BeautifulSoup(page.text, "html.parser")
    
        table_head = ['Row', 'Code', 'Name', 'Holding', 'Value', 'Is Susp/Parallel', 'Stake %', 'Last Chg Date']
        table = soup.find('table', {'class': 'optable yscroll'})
        single_dict_list = []
        row_values_list = []
        for row in table.find_all('tr')[1:]:
            td_holders = row.find_all('td')
            rank = td_holders[0].text
            code = td_holders[1].text
            name = td_holders[2].find('a').text
            holding = td_holders[3].text
            value = td_holders[4].text
            is_susp = True if '*' in td_holders[5].text else False
            stake_pct = td_holders[6].find('a').text
            chg_date = td_holders[7].find('a').text
            row_values = [rank, code, name, holding, value, is_susp, stake_pct, chg_date]
            row_values_list.append(row_values)
            single_dict = dict(zip(table_head, row_values))
            single_dict_list.append(single_dict)
        
        d = datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        subdir = os.path.join(root, 'north holdings')
        os.makedirs(subdir, exist_ok=True)
        
        date_dict = {date: single_dict_list}
        dict_list.append(date_dict)
        
        filepath1 = os.path.join(subdir, f'sh_southbound_holdings_{d}.json') 
        with open(filepath1, 'w') as json_file:
            json.dump(date_dict, json_file)
        
        filepath2 = os.path.join(subdir, f'sh_southbound_holdings_{d}.csv')
        with open(filepath2, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(table_head)
            for rv in row_values_list:
                writer.writerow(rv)
            file.close()

    return dict_list

    

def get_sz_holdings(ua, dates, root, proxies):
    dict_list = []
    for date in dates:
        url = f'https://webb-site.com/ccass/cholder.asp?part=1456&d={date}&z=False&sort=valndn'
        headers = {'Sec-Fetch-Mode': 'navigate','User-Agent': random.choice(ua)}
        # page = requests.get(url, headers=headers, proxies=random.choice(proxies))
        page = requests.get(url, headers=headers)
        time.sleep(2)
        soup = BeautifulSoup(page.text, "html.parser")
    
        table_head = ['Row', 'Code', 'Name', 'Holding', 'Value', 'Is Susp/Parallel', 'Stake %', 'Last Chg Date']
        table = soup.find('table', {'class': 'optable yscroll'})
        single_dict_list = []
        row_values_list = []
        for row in table.find_all('tr')[1:]:
            td_holders = row.find_all('td')
            rank = td_holders[0].text
            code = td_holders[1].text
            name = td_holders[2].find('a').text
            holding = td_holders[3].text
            value = td_holders[4].text
            is_susp = True if '*' in td_holders[5].text else False
            stake_pct = td_holders[6].find('a').text
            chg_date = td_holders[7].find('a').text
            row_values = [rank, code, name, holding, value, is_susp, stake_pct, chg_date]
            row_values_list.append(row_values)
            single_dict = dict(zip(table_head, row_values))
            single_dict_list.append(single_dict)
        
        d = datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        subdir = os.path.join(root, 'north holdings')
        os.makedirs(subdir, exist_ok=True)
        
        date_dict = {date: single_dict_list}
        dict_list.append(date_dict)
        
        filepath1 = os.path.join(subdir, f'sz_southbound_holdings_{d}.json') 
        with open(filepath1, 'w') as json_file:
            json.dump(date_dict, json_file)
        
        filepath2 = os.path.join(subdir, f'sz_southbound_holdings_{d}.csv')
        with open(filepath2, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(table_head)
            for rv in row_values_list:
                writer.writerow(rv)
            file.close()

    return dict_list


def gen_shift_dict(days, start_day='2007-06-26', end_day='2022-12-31'):
    dt_format = '%Y-%m-%d'
    start_dt = datetime.strptime(start_day, dt_format)
    end_dt = datetime.strptime(end_day, dt_format)
    cycles_num = round((end_dt - start_dt).days / days)

    daypairs_list = []
    for i in range(1, cycles_num):
        cycle_start = start_dt
        cycle_end = min(start_dt + timedelta(days=days), end_dt)
        daypair = [cycle_start, cycle_end]
        daypairs_list.append(daypair)
        start_dt = cycle_end + timedelta(days=1)

    dayshift_list = []
    for pair in daypairs_list:
        shift_start = (datetime.today() - pair[0]).days
        shift_end = (datetime.today() - pair[1]).days
        shift_pair = [shift_start, shift_end]
        dayshift_list.append(shift_pair)

    dayshift_list = dayshift_list[::-1]

    shift_dict = {}
    for i in range(len(dayshift_list)):
        shift_dict[i + 1] = dayshift_list[i]

    print(shift_dict)
    return shift_dict


def gen_hist_constituent_data(chrome_path, start_date, end_date, dt_format, ph):
    start_dt = datetime.strptime(start_date, dt_format)
    end_dt = datetime.strptime(end_date, dt_format)
    diff = (end_dt - start_dt).days
    dates = [start_dt + timedelta(days=i) for i in range(1, diff + 1)][::-1]

    read_path1 = 'hist_hsi_constituents.xlsx'
    raw_hsi_df = pd.read_excel(read_path1)
    raw_hsi_codes = raw_hsi_df['Stock Code']
    hsi_codes = [('000' + str(c))[-4:] for c in raw_hsi_codes]
    raw_hsi_df.insert(5, 'Real Code', hsi_codes)

    read_path2 = 'hist_hstech_constituents.xlsx'
    raw_hti_df = pd.read_excel(read_path2)
    raw_hti_codes = raw_hti_df['Stock Code']
    hti_codes = [('000' + str(c))[-4:] for c in raw_hti_codes]
    raw_hti_df.insert(5, 'Read Code', hti_codes)

    hsi_list = get_hsi_tickers(chrome_path) if hsi not in os.listdir(rootdir) else read_tickers_list(hsi)
    today_hsi = hsi_list
    print(today_hsi)
    print(len(today_hsi))

    hti_list = get_hti_tickers(chrome_path) if hti not in os.listdir(rootdir) else read_tickers_list(hti)
    today_hti = hti_list
    print(today_hti)
    print(len(today_hti))

    data_dict = {}
    for date in dates:
        date_str = date.strftime(dt_format)

        print(f'Processing hsi constituent list for {date_str}')
        for index, row in raw_hsi_df.iterrows():
            if date == datetime.strptime(row[0], dt_format) - timedelta(days=1) and 'Delete' in row[2]:
                today_hsi.append(row[5])
            elif date == datetime.strptime(row[0], dt_format) - timedelta(days=1) and 'Add' in row[2]:
                today_hsi.remove(row[5])
            else:
                pass

        if date >= datetime.strptime('2020-07-27', dt_format):
            print(f'Processing hti constituent list for {date_str}')
            for index, row in raw_hti_df.iterrows():
                if date == datetime.strptime(row[0], dt_format) - timedelta(days=1) and 'Delete' in row[2]:
                    today_hti.append(row[5])
                elif date == datetime.strptime(row[0], dt_format) - timedelta(days=1) and 'Add' in row[2]:
                    today_hti.remove(row[5])
                else:
                    pass
        else:
            today_hti = []

        date_tickers = sorted(list(set(today_hsi + today_hti)))
        print(f'There is {len(date_tickers)} hsi and hti symbols at {date_str}')
        data_dict[date_str] = date_tickers

    filepath = 'hsihti_constituents_data.json'
    with open(filepath, 'w') as json_file:
        json.dump(data_dict, json_file)

def read_hist_constituent_data(filepath='hsihti_constituents_data.json'):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data



if __name__ == "__main__":

    # Define variables
    sleep = 2
    chrome_path = r'C:\Users\dave\Downloads\chromedriver-win32\chromedriver.exe'
    rootdir = r'C:\Users\user\Documents\#Coding\CCASS'
    hsi = '#hsi_tickers.csv'
    hti = '#hti_tickers.csv'


    # Don't touch anything below here
    def read_tickers_list(fn):
        tickers = []
        with open(fn, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                tickers.append(row[0])
        return tickers


    today = datetime.today().strftime('%Y%m%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y%m%d')
    ua_list = read_user_agents()

    holidays_list = []
    with open('#public_holidays_to_2023.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            holidays_list.append(row[0])

    # hsi_list = get_hsi_tickers(chrome_path) if hsi not in os.listdir(rootdir) else read_tickers_list(hsi)
    # hti_list = get_hti_tickers(chrome_path) if hti not in os.listdir(rootdir) else read_tickers_list(hti)
    # ticker_list = list(set(hsi_list + hti_list))
    # ticker_list.extend(['2007', '2018'])
    # # print([[i, c] for i, c in zip(range(len(ticker_list)), ticker_list)])
    # print(f'There is in total {len(ticker_list)} symbols.')

    # shift_dict = gen_shift_dict(66)
    # # for key in list(shift_dict.keys()):
    # key = 2
    # shift_start = shift_dict[key][0] if key != 0 else 1
    # shift_end = shift_dict[key][1] if key != 0 else 1 # when shift = 1 it means yesterday, 2 means the day before yesterday
    # start = (datetime.today() - timedelta(days=shift_start)).strftime('%Y-%m-%d')
    # end = (datetime.today() - timedelta(days=shift_end)).strftime('%Y-%m-%d')
    # dates_list = generate_dates(start, end, holidays_list)[::]
    # print(dates_list)
    # print(f'There is {len(dates_list)} days in total.')

    # gen_hist_constituent_data(chrome_path, '2008-06-10', '2023-12-12', '%Y-%m-%d', holidays_list)
    constituents_data = read_hist_constituent_data()
    end_date = '2022-06-01'
    calendar = generate_dates('2008-06-11', end_date, holidays_list)[::-1]
    shift_map = [(datetime.today() - datetime.strptime(date, '%Y-%m-%d')).days for date in calendar]
    key = 21
    dates_list = [(datetime.today() - timedelta(days=shift_map[key])).strftime('%Y-%m-%d')]
    ticker_list = constituents_data[dates_list[0]]
    print(ticker_list)
    print(f'There is in total {len(ticker_list)} symbols.')
    print(dates_list)
    print(f'There is {len(dates_list)} days in total.')

    proxies = get_proxies_list('HK')[::]

    # Main Loop
    # s = 0
    for i, ticker in zip(range(1, len(ticker_list[::]) + 1), ticker_list[::]):
        print(ticker)
        proxy = proxies[i % len(proxies)]
        print(f'Using proxy: {proxy} at index [{i}]:{ticker}')

        tempdir = os.path.join(rootdir, 'temp')
        get_ticker_holdings_snapshots(ua_list, ticker, dates_list, tempdir, proxy)
        # get_ticker_holdings_change(ua_list, ticker, dates_list, tempdir, proxy)

        # if datetime.today().weekday() == 0:
        #     get_ticker_holdings_big_change(ua_list, ticker, today, rootdir, proxy)
        #     get_ticker_concentration_history(ua_list, ticker, today, rootdir, proxy)

        # if i % 5 == 0 and i != 0:
        #     time.sleep(random.uniform(30, 40))
        # else:
        #     time.sleep(random.uniform(1, 4))
        # time.sleep(0.5)

    # sh_list = get_sh_holdings(ua_list, dates_list, rootdir, proxies)
    # sz_list = get_sz_holdings(ua_list, dates_list, rootdir, proxies)

    for i in range(98):
        url = 'https://webb-site.com/ccass/choldings.asp?sort=holddn&sc=00001&d=2023-07-31'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        summary_head = ['Type of holder', 'Holding', 'Stake %']
        summary_table = soup.find('table', {'class': 'optable'})
        for row in summary_table.find_all('tr')[1:2]:
            print(row.text)


