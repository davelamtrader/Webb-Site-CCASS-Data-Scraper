import requests
from bs4 import BeautifulSoup
import csv
import json
import time
from datetime import date, datetime, timedelta
import pandas as pd
import os
import random


def get_proxies_list(country):
    
    proxy_list = []
    for i in range(1,3):
        url = f'https://www.freeproxy.world/?type=http&anonymity=&country={country}&speed=&port=&page={i}'
        page = requests.get(url)
        time.sleep(2)
        soup = BeautifulSoup(page.text, "html.parser")
        
        table = soup.find('table', {'class':'layui-table'})
        all_rows = table.find_all('tr')[1:]
        rows = [row for row in all_rows if row.text not in ['\n\n\n\n\n\n\n\n', '\n']]
        for row in rows:
            ip = row.find('td', {'class':'show-ip-div'}).text.replace('\n', '')
            port = row.find_all('td')[1].text.replace('\n', '')
            row_value = [ip, port]
            proxy_list.append(row_value)
            
    print('There are in total', len(proxy_list), f'proxies for country {country}.')
    
    with open(f'{country}_proxies_list.csv', 'w', newline='') as file:
        for row in proxy_list:
            writer = csv.writer(file)
            writer.writerow(row)
        file.close()
    
    proxies = [{'http': f'http://{proxy[0]}:{proxy[1]}'} for proxy in proxy_list]
    with open(f'{country}_proxies_list.json', 'w') as json_file:
        json.dump(proxies, json_file)
    
    return proxies


def read_user_agents():
    fn = 'ua.json'
    
    with open(fn, 'r') as file:
        raw_ua_list = json.load(file)
    
    ua_list = [value for item in raw_ua_list for value in item.values() if '/' in str(value)]
    
    return ua_list
    
        
        
if __name__ == "__main__":
    
    # proxies = get_proxies_list('HK')
    ua_list = read_user_agents()
        
    headers = {
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'User-Agent': random.choice(ua_list)
    }
        
    for i in range(10):
        print(random.uniform(4, 8))
    