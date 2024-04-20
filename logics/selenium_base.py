import os
import time
import shlex
import subprocess
import psutil
# from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

from configs.configs import *

before = 'before.png'
after = 'after.png'


def wait_element(brower, element_id, wait_time=10):
    try:

        WebDriverWait(brower, wait_time, 1).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
    except Exception as e:
        raise Exception(e)


def wait_element_css(brower, css, wait_time=10):
    try:
        WebDriverWait(brower, wait_time, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
    except Exception as e:
        raise Exception(e)


def wait_element_xpath(brower, xpath, wait_time=10):
    try:
        WebDriverWait(brower, wait_time, 1).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except Exception as e:
        raise Exception(e)


def get_brower_header(brower):
    all_header_info = []
    for request in brower.requests:
        req_url = request.url
        req_headers = dict(request.headers)
        resp_headers = dict(request.response.headers)
        data = {
            'req_url': req_url,
            'req_headers': req_headers,
            'resp_headers': resp_headers
        }
        all_header_info.append(data)
    return all_header_info


def add_header(headers):
    options = Options()
    for k, v in headers.items():
        options.add_argument(f'{k}={v}')
    return options


def disable_img_css(options):
    # 禁止图片
    prefs = {"profile.managed_default_content_settings.images": 2,
             }
    options.add_experimental_option("prefs", prefs)


def disable_css(options):
    # 禁止css加载
    prefs = {'permissions.default.stylesheet': 2}
    options.add_experimental_option("prefs", prefs)


def brower_headless(options):
    # 无头浏览器
    options.add_argument('headless')


def start_chrome(port, browser_user_data):
    """
    命令行开启Chrome
    """
    shell = f'''
   "{chrome_exe_path}" --remote-debugging-port={port} --user-data-dir="{browser_user_data}"
   '''
    print(shell)
    subprocess.Popen(shlex.split(shell), shell=False)

def get_process_id(port):
    processes = [proc for proc in psutil.process_iter()]
    for p in processes:
        for c in p.connections():
            if c.status == 'LISTEN' and c.laddr.port == port:
                return p
    return None

def get_process_name(port):
    p = get_process_id(int(port))
    if p:
        return p.name()
    else:
        return None


def kill_process(port):
    p = get_process_id(int(port))
    if not p:
        return None
    else:
        p.kill()

def stop_chrome(port):
    process_name = get_process_name(port)
    if process_name == 'chrome.exe':
        # 关停进程
        kill_process(port)


def get_brower_debugger(port):
    # stop_chrome(port)
    # start_chrome(port, browser_user_data)
    options = webdriver.ChromeOptions()
    options.add_argument('disable-popup-blocking')

    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    # driver = webdriver.Chrome(executable_path=chrome_driver_exe_path, options=options)
    driver = webdriver.Chrome(options=options)
    return driver

def get_brower(headers=None, stealth=True, disable_img=False, disable_css=False, headless=False):
    if not headers:
        headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    options = add_header(headers)
    if headless:
        brower_headless(options)

    options.add_argument('user-data-dir={}'.format(user_data_dir))

    # brower = webdriver.Chrome(executable_path=chrome_driver_exe_path, chrome_options=options)
    brower = webdriver.Chrome(options=options)

    if stealth:
        js_path = os.path.join(js_dir, 'stealth.min.js')
        with open(js_path) as f:
            js = f.read()

        # 在打印具体的网页前，执行隐藏浏览器特征的JavaScript
        brower.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
    return brower

if __name__ == "__main__":
    get_brower()