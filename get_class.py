import pymysql, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = 'http://www.worldgymtaiwan.com/zh-tw/schedule'

chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(chrome_options=chrome_options)


def get_store(data: list) -> list:
    driver.get(URL)
    time.sleep(0.1)
    dom = driver.page_source
    soup = BeautifulSoup(dom, 'html5lib')
    uls = soup.find('ul', id='store').find_all('li')
    for ul in uls:
        store = {'city': ul['name'],
                 'id': ul['onclick'].split(',')[1].replace(')', ''),
                 'store_name': ul.text}
        data.append(store)

    return data


def get_class(data: dict):
    url = 'http://www.worldgymtaiwan.com/zh-tw/schedule#class!id='+data['id']
    driver.get(url)
    driver.refresh()
    time_delay = 1
    flag = True
    while flag:
        try:
            print(f"{data['store_name']}，第{time_delay}次嘗試")
            time.sleep(0.1*time_delay)
            dom = driver.page_source
            soup = BeautifulSoup(dom, 'html5lib')
            status = soup.find('section', 'class-block').text
            if status.endswith('尚未更新'):
                print(data['store_name'], status)
            else:
                element = soup.find('div', 'column-b7 block').find_all('ul', 'st-list-1')
                for ele in element:
                    week = ele.find('li').text
                    divs = ele.find_all('li')[1:]
                    for div in divs:
                        classes = {'city': data['city'],
                                   'id': data['id'],
                                   'store_name': data['store_name'],
                                   'week': week,
                                   'type': div['name'].strip(),
                                   'class_name': div.a.text.strip(),
                                   'time': div.find('div', 'time').text.strip().replace('"', ':'),
                                   'teacher_name': div.find('div', 'name').text.strip()}
                        key = ', '.join(classes.keys())
                        value = '"," '.join(classes.values())
                        insert_sql = f'insert into class ({key}) values("{value}")'
                        cursor.execute(insert_sql)
                print("完成")
            flag = False
        except Exception as e:
            flag = True
            time_delay += 1
            if time_delay > 10:
                print(e)
                driver.refresh()
                continue


with open('database.txt', encoding='utf8') as f:
    site = f.readline().strip()
    port = int(f.readline().strip())
    user = f.readline().strip()
    passwd = f.readline().strip()
    db = f.readline().strip()
conn = pymysql.connect(site, port=port, user=user, passwd=passwd, charset='utf8', db=db)

cursor = conn.cursor()
cursor.execute("drop table if exists class")
sql_create_table = '''
CREATE TABLE class(
sid int not null auto_increment primary key,
city char(6),
id char(3),
store_name char(30),
week char(10),
type char(20),
class_name char(40),
time char(20),
teacher_name char(20) 
)
'''
cursor.execute(sql_create_table)

store_data = list()
store_data = get_store(store_data)

for data in store_data:
    if not data['store_name'].endswith('Express'):
        get_class(data)


conn.commit()
cursor.close()
conn.close()
driver.quit()
