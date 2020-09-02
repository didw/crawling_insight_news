import os
import time
import requests
import encodings
import datetime
import random
import re
from multiprocessing import Process
from tqdm import tqdm
from bs4 import BeautifulSoup

DEBUG = False
session = requests.session()
session.proxies = {}

session.proxies['http'] = 'socks5h://localhost:9050'
session.proxies['https'] = 'socks5h://localhost:9050'

headers = {'User-Agent':'Mozilla/5.0'}
regex = re.compile(r'\[.+\]\s*[가-힣]{3}\s*기자\s*=\s*.+?\.')

fhandle_error = open("error.txt", "w")

def get_news(num):
    url = f"https://biz.insight.co.kr/news/{num}"
    raw = requests.get(url, headers=headers)
    html = BeautifulSoup(raw.text, 'html.parser')
    extract = ''
    try:
        title = html.select(".news-header")
        if isinstance(title, list):
            title = title[0].text
        text = html.select(".news-article-memo")
        if isinstance(text, list):
            text = text[0].text
        extract = regex.findall(text)
        if DEBUG:
            print(extract)
        if isinstance(extract, list):
            extract = extract[0]
        text_begin = text.find(extract)
        text = text[text_begin + len(extract):]
    except Exception as _e:
        print(url)
        print(title.strip())
        print(text.strip()[:30])
        fhandle_error.write(f"{url}\n")
        fhandle_error.write(f"{title.strip()}\n")
        fhandle_error.write(f"{text.strip()[:50]}\n\n")
        exit(1)
        return title, extract, html.text
    return title, extract, text


def save_news(fname, title, extract, text):
    if not os.path.exists(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))
    with open(fname, 'w', encoding='utf-8') as f:
        f.write("{}\n\n".format(title))
        f.write(text.strip())
        f.write("\n")


def get_news_to_save(news_num, fname):
    try:
        title, extract, text = get_news(news_num)
        save_news(fname, title, extract, text)
    except Exception as e:
        print(e)


def check_current_ip():
    url = "https://icanhazip.com"
    raw = session.get(url, headers=headers)
    html = BeautifulSoup(raw.text, 'html.parser')
    ip = html.text.strip()
    print(f"current ip : {ip}")


def change_ip():
    try:
        os.system("sudo service tor restart")
        time.sleep(5)
        check_current_ip()
    except Exception as e:
        print(e)


def get_all_news():
    ps = []
    for news_num in tqdm(range(60000, 296000)):

        cur_dtime = datetime.datetime.now()
        if datetime.time(8, 0) <= cur_dtime.time() <= datetime.time(18, 30) and cur_dtime.weekday() in [0,1,2,3,4]:
            max_ps = 50
            sleep_time = 0.1
        else:
            max_ps = 500
            sleep_time = 0.001

        if max_ps == 500 and news_num % 1000 == 0:
            time.sleep(5)
            change_ip()
        page_num = int(news_num/1000)
        fname = f"news/{page_num}/{news_num}.txt"
        if os.path.exists(fname):
            continue
        p = Process(target=get_news_to_save, args=(news_num, fname))
        t = random.randint(1, 10)
        time.sleep(sleep_time + t/1000)
        p.start()
        ps.append(p)
        while len(ps) > max_ps:
            ps[0].join()
            del ps[0]
    for p in ps:
        p.join()


def main():
    get_all_news()


def test():
    global DEBUG
    DEBUG = True
    title, extract, text = get_news(60010)
    print(title)
    print(extract)
    print(text)


if __name__ == '__main__':
    main()
