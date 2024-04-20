from node_vm2 import VM

import re
import json
import urllib.parse
import requests
import time
import os
from datetime import date

from logics.selenium_base import *


class Query12306:
    """12306车票查询"""
    def __init__(self) -> None:
        self.query_info = dict()
        self.session = requests.session()
        self.stations_code = self.pares_station()
        
        # 车站中文列表
        if self.stations_code:
            self.stations_name = [i for i in self.stations_code.values()]
        else:
            self.stations_name = []

        self.query_result = None


    def train_query(self, train_date, from_station, to_station):
        """班次查询请求
        train_date: 班次日期 yyyy-mm-dd
        from_station: 出发站名
        to_station: 终点站名
        """
        
        self.query_info['train_date'] = train_date
        self.query_info['from_station'] = from_station
        self.query_info['to_station'] = to_station
        self.query_info['from_station_code'] = self.get_station_code(from_station)
        self.query_info['to_station_code'] = self.get_station_code(to_station)

        if not (self.query_info['from_station_code'] and self.query_info['to_station_code']):
            print('车站不存在')
            return None

        self.set_cookies()
        self.set_headers()
        self.set_params()

        resp = self.session.get('https://kyfw.12306.cn/otn/leftTicket/query')

        if resp.status_code != 200:
            print(f'车票搜索失败 function: train_query, status_code: {resp.status_code}')
            return None
        
        with open('text.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        self.query_result = self.pares_train_query(json.loads(resp.text))
        
        return self.query_result
    
    def get_result(self):
        """获取搜索结果"""
        return self.query_result
    
    def get_ticket_info(self, index):
        return {
            'train_date': self.query_info['train_date'],
            'from_station': self.query_info['from_station'],
            'from_station_code': self.query_info['from_station_code'],
            'to_station': self.query_info['to_station'],
            'to_station_code': self.query_info['to_station_code'],
            'secretStr': self.get_result()[index]['secretStr'],
        }
    
    def pares_station(self):
        """解析站名数据
        https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9261"""

        filename = os.path.join(static_dir, 'station_names.txt')
        # 站名文件不存在则去下载
        if not os.path.exists(filename):
            self.download_station_name()
        with open(filename, 'r', encoding='utf-8') as f:
            station_names = f.read()

        if not station_names:
            return None

        # @bjb|北京北|VAP|beijingbei|bjb|0|0357|北京||
        stations = {}
        for station in station_names.split('@')[1:]:
            index = station.split('|')
            # {车站代号: 车站名}
            stations[index[2]] = index[1]

        return stations
    
    def download_station_name(self):
        '''
        下载站名文件
        '''
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }

        response = requests.get('https://kyfw.12306.cn/otn/static/js/framework/station_name.js', headers=headers)
        
        if response.status_code == 200:
            # js代码中提取变量值
            pattern = "var station_names ='(.*)';"
            matches = re.findall(pattern, response.text)
            if len(matches) <= 0:
                return None
            filename = os.path.join(static_dir, 'station_names.txt')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(matches[0])
    
    def get_station_code(self, name):
        """站名中文转站名代码"""
        for k, v in self.stations_code.items():
            if v == name:
                return k
        return ''
    
    @staticmethod
    def pares_train_query(data):
        """班次查询ajax返回数据解析 
        解析train_query返回的数据"""

        cZ = data["data"]['result']
        c1 = data["data"]['map']
        cY = []
        for cX in range(len(cZ)):
            c2 = {}
            cW = cZ[cX].split("|")
            c2['secretStr'] = cW[0]
            # 如果可以买票，就显示该信息在按钮上
            c2['buttonTextInfo'] = cW[1]
            c0 = {}
            # 班次号
            c0['train_no'] = cW[2]
            # 列车号
            c0['station_train_code'] = cW[3]
            # 总出发站代号
            c0['start_station_telecode'] = cW[4]
            # 总终点站代号
            c0['end_station_telecode'] = cW[5]
            # 出发站代号
            c0['from_station_telecode'] = cW[6]
            # 终点站代号
            c0['to_station_telecode'] = cW[7]
            # 出发时间
            c0['start_time'] = cW[8]
            # 到达时间
            c0['arrive_time'] = cW[9]
            # 历时
            c0['lishi'] = cW[10]
            # 能否买票
            c0['canWebBuy'] = cW[11]
            # 余票？？？
            c0['yp_info'] = cW[12]
            # 出发日期
            c0['start_train_date'] = cW[13]
            # 用作参数传入到myStopStation.opne()函数
            c0['train_seat_feature'] = cW[14]
            # 没用到
            c0['location_code'] = cW[15]
            # 出发站代号
            c0['from_station_no'] = cW[16]
            # 终点站代号
            c0['to_station_no'] = cW[17]
            # 没用到
            c0['is_support_card'] = cW[18]
            # 没用到
            c0['controlled_train_flag'] = cW[19]
            # 没用到
            c0['gg_num'] = cW[20] if cW[20] else "--"
            # 高级软卧
            c0['gr_num'] = cW[21] if cW[21] else "--"
            # 其他
            c0['qt_num'] = cW[22] if cW[22] else "--"
            # 软卧、一等卧
            c0['rw_num'] = cW[23] if cW[23] else "--"
            # 软座
            c0['rz_num'] = cW[24] if cW[24] else "--"
            # 特等座
            c0['tz_num'] = cW[25] if cW[25] else "--"
            # 无座
            c0['wz_num'] = cW[26] if cW[26] else "--"
            # 没用到
            c0['yb_num'] = cW[27] if cW[27] else "--"
            # 硬卧、二等卧
            c0['yw_num'] = cW[28] if cW[28] else "--"
            # 硬座
            c0['yz_num'] = cW[29] if cW[29] else "--"
            # 二等座、二等包座
            c0['ze_num'] = cW[30] if cW[30] else "--"
            # 一等座
            c0['zy_num'] = cW[31] if cW[31] else "--"
            # 商务座
            c0['swz_num'] = cW[32] if cW[32] else "--"
            # 动卧
            c0['srrb_num'] = cW[33] if cW[33] else "--"
            c0['yp_ex'] = cW[34]
            c0['seat_types'] = cW[35]
            c0['exchange_train_flag'] = cW[36]
            c0['houbu_train_flag'] = cW[37]
            # 候补座位限制
            c0['houbu_seat_limit'] = cW[38]
            c0['yp_info_new'] = cW[39]
            if len(cW) > 46:
                c0['dw_flag'] = cW[46]
            if len(cW) > 48:
                # 停止出票时间？？
                c0['stopcheckTime'] = cW[48]
            if len(cW) > 49:
                c0['country_flag'] = cW[49]
                c0['local_arrive_time'] = cW[50]
                c0['local_start_time'] = cW[51]
            c0['from_station_name'] = c1[cW[6]]
            c0['to_station_name'] = c1[cW[7]]
            c2['queryLeftNewDTO'] = c0
            cY.append(c2)
        return cY
    
    @staticmethod
    def to_unicode_with_percent(s: str) -> str:
        """中文转unicode，以%u前缀返回"""
        u = s.encode('unicode-escape').decode()
        return u.replace('\\', '%')
    
    def set_cookies(self):
        """更新cookies"""
        cookie = {}
        cookie['_jc_save_fromStation'] = f"{self.to_unicode_with_percent(self.query_info['from_station'])},{self.query_info['from_station_code']}"
        cookie['_jc_save_toStation'] = f"{self.to_unicode_with_percent(self.query_info['to_station'])},{self.query_info['to_station_code']}"
        cookie['_jc_save_toDate'] = self.query_info['train_date']
        cookie['_jc_save_fromDate'] = str(date.today())

        self.session.cookies.update(cookie)

    def set_headers(self):
        """更新请求头"""

        referer_url = 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={},{}&ts={},{}&date={}&flag=N,Y,Y'.format(
            urllib.parse.quote(self.query_info['from_station']),
            self.query_info['from_station_code'],
            urllib.parse.quote(self.query_info['to_station']),
            self.query_info['to_station_code'],
            self.query_info['train_date']
        )

        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'If-Modified-Since': '0',
            'Pragma': 'no-cache',
            'Referer': referer_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        self.session.headers.update(headers)

    def set_params(self):
        """更新请求参数"""

        params = {
            'leftTicketDTO.train_date': self.query_info['train_date'],
            'leftTicketDTO.from_station': self.query_info['from_station_code'],
            'leftTicketDTO.to_station': self.query_info['to_station_code'],
            'purpose_codes': 'ADULT',
        }

        self.session.params = params

    @staticmethod
    def get_show_data(trains):
        """搜索结果转成网页显示格式"""

        seat_num = {
        "swz_num": "SWZ_",
        "tz_num": "TZ_",
        "gr_num": "GR_",
        "qt_num": "QT_",
        "rw_num": "RW_",
        "rz_num": "RZ_",
        "wz_num": "WZ_",
        "yw_num": "YW_",
        "yz_num": "YZ_",
        "ze_num": "ZE_",
        "zy_num": "ZY_",
        "srrb_num": "SRRB_", }

        def check_ticket(seat_info, seat_str1, data):
            """查询车票状态"""

            res = seat_info
            # 当是无票，非无座，非其他，该班次出发时间没到，把无转换成候补
            houbu = True
            if '1' != data['houbu_train_flag']:
                houbu = False
            if "无" == seat_info and "WZ_" != seat_str1 and "QT_" != seat_str1 and houbu:
                res = "候补"
                flag = transition_seat_info(seat_info)
                if flag != "" and data['houbu_seat_limit'] and data['houbu_seat_limit'] and str.find(flag) > -1:
                    res = "暂时不能候补"

            return res
        
        def transition_seat_info(seat_info):
            if seat_info == "SWZ_":
                return "9"
            if seat_info == "TZ_":
                return "P"
            if seat_info == "ZY_":
                return "M"
            if seat_info == "ZE_":
                return "O"
            if seat_info == "GR_":
                return "6"
            if seat_info == "RW_":
                return "4"
            if seat_info == "SRRB_":
                return "F"
            if seat_info == "YW_":
                return "3"
            if seat_info == "RZ_":
                return "2"
            if seat_info == "YZ_":
                return "1"
            if seat_info == "WZ_":
                return ""
            return ""
        
        res = []
        for train in trains:
            i = train['queryLeftNewDTO']
            info = {}
            print(i)
            info['station_train_code'] = i['station_train_code']
            info['from_to_station'] = i['from_station_name'] + \
                " 到 " + i['to_station_name']
            info['start_arrive_time'] = i['start_time'] + ' -> ' + i['arrive_time']
            info['lishi'] = i['lishi']

            info['swz_tz_num'] = "--"
            if i['swz_num'] and i['swz_num'] != '--' and i['swz_num'] != 0 and i['swz_num'] != '无':
                info['swz_tz_num'] = check_ticket(
                    i['swz_num'], seat_num['swz_num'], i)
            else:
                if i['tz_num'] and i['tz_num'] != '--' and i['tz_num'] != 0 and i['tz_num'] != '无':
                    info['swz_tz_num'] = check_ticket(
                        i['tz_num'], seat_num['tz_num'], i)
                else:
                    if i['swz_num'] and i['swz_num'] != '无':
                        info['swz_tz_num'] = check_ticket(
                            i['swz_num'], seat_num['swz_num'], i)
                    else:
                        info['swz_tz_num'] = check_ticket(
                            i['tz_num'], seat_num['tz_num'], i)

            info['zy_num'] = check_ticket(i['zy_num'], seat_num['zy_num'], i)
            info['ze_num'] = check_ticket(i['ze_num'], seat_num['ze_num'], i)
            info['gr_num'] = check_ticket(i['gr_num'], seat_num['gr_num'], i)
            info['rw_num'] = check_ticket(i['rw_num'], seat_num['rw_num'], i)
            info['srrb_num'] = check_ticket(i['srrb_num'], seat_num['srrb_num'], i)
            info['yw_num'] = check_ticket(i['yw_num'], seat_num['yw_num'], i)
            info['rz_num'] = check_ticket(i['rz_num'], seat_num['rz_num'], i)
            info['yz_num'] = check_ticket(i['yz_num'], seat_num['yz_num'], i)
            info['wz_num'] = check_ticket(i['wz_num'], seat_num['wz_num'], i)
            info['qt_num'] = check_ticket(i['qt_num'], seat_num['qt_num'], i)
            info['secretStr'] = train['secretStr']
            info['from_station_telecode'] = i['from_station_telecode']
            info['to_station_telecode'] = i['to_station_telecode']
            info['from_station_name'] = i['from_station_name']
            info['to_station_name'] = i['to_station_name']
            info['to_station_name'] = i['to_station_name']
            info['start_train_date'] = i['start_train_date']
            res.append(info)

        return res


class Spider12306:
    """12306抢票"""

    def __init__(self, ticket_info) -> None:
        """
        ticket_info = {
            'train_date': '2023-06-14',
            'from_station':'吴川',
            'from_station_code': '',
            'to_station': '广州南',
            'to_station_code': '',
            'user': '',
            'password': '',
            'passengers': [
                {
                    'name': '陈宇明',
                    'seat_type': 'O', # 选座
                    'ticket_type': '1'
                },
            ],
            'choose_seats': '1A',
            'secretStr': "AFASGSDFSDFASQWEAFAS",
        }
        """
        # 抢票所需的信息
        self.ticket_info = ticket_info
        # 用户登录cookie文件
        self.login_cookies_file = f'cookie.{self.ticket_info["user"]}.json'
        self.is_login = False

    def start(self):
        """开始抢票"""

        self.verify_login()

        if not self.is_login:
            self.login()

        func_list = [self.requests_2, self.requests_3, self.requests_4, 
                     self.requests_5, self.requests_6, self.requests_7]
        
        for func in func_list:
            res = func()
            if not res:
                print(f'{func.__name__} 失败')
                return

        

    def get_verify_headers(self):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://kyfw.12306.cn',
            'Pragma': 'no-cache',
            'Referer': 'https://kyfw.12306.cn/otn/view/passengers.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        return headers
    
    def get_headers(self):
        """更新请求头"""

        referer_url = 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={},{}&ts={},{}&date={}&flag=N,Y,Y'.format(
            urllib.parse.quote(self.ticket_info['from_station']),
            self.ticket_info['from_station_code'],
            urllib.parse.quote(self.ticket_info['to_station']),
            self.ticket_info['to_station_code'],
            self.ticket_info['train_date']
        )

        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'If-Modified-Since': '0',
            'Pragma': 'no-cache',
            'Referer': referer_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        return headers

    def add_login_cookies(self, cookies):
        """给cookie添加登录信息"""
        login_cookie = self.load_cookies(self.login_cookies_file)
        if login_cookie:
            for cookie in login_cookie:
                cookies[cookie['name']] = cookie['value']

    def set_cookies(self, cookies):
        """更新cookies"""
        cookies['_jc_save_fromStation'] = '{}%2C{}'.format(self.to_unicode_with_percent(self.ticket_info['from_station']), self.ticket_info['from_station_code'])
        cookies['_jc_save_toStation'] = '{}%2C{}'.format(self.to_unicode_with_percent(self.ticket_info['to_station']), self.ticket_info['to_station_code'])
        cookies['_jc_save_toDate'] = self.ticket_info['train_date']
        cookies['_jc_save_fromDate'] = str(date.today())

    @staticmethod
    def to_unicode_with_percent(s: str) -> str:
        """中文转unicode, 以%u前缀返回"""
        u = s.encode('unicode-escape').decode()
        return u.replace('\\', '%')

    def verify_login(self):
        """验证12306cookie"""
        headers = self.get_verify_headers()
        cookies = {}
        self.add_login_cookies(cookies)
        if not cookies:
            return

        response = requests.post('https://kyfw.12306.cn/otn/login/conf', cookies=cookies, headers=headers)
        if response.status_code != 200:
            print(f'verify_login 验证登录失败 {response.status_code}')
            return
        
        res = json.loads(response.text)
        print('verify_login', res)
        
        self.is_login = True if res['data']['is_login'] == "Y" else False
        return

    def login(self):
        """selenium登录获取cookie"""
        
        brower = get_brower(headless=False)
        cookies = []

        self.login_process(brower, self.ticket_info["user"], self.ticket_info["password"])

        time.sleep(3)
        cookies = brower.get_cookies()
        brower.close()

        self.save_cookies(cookies, self.login_cookies_file)
        
    @staticmethod
    def login_process(brower, username, password):
        """selenium登录12306模拟过程"""

        url = 'https://kyfw.12306.cn/otn/resources/login.html'
        try:
            brower.get(url=url)
            username_element = brower.find_element(By.CSS_SELECTOR, '#J-userName')
            username_element.send_keys(username)

            password_element = brower.find_element(By.CSS_SELECTOR, '#J-password')
            password_element.send_keys(password)

            time.sleep(1)

            submit = brower.find_element(By.CSS_SELECTOR, '#J-login')
            submit.click()

            # 判断验证码是否出来
            block_css = '#nc_1_n1z'
            for _ in range(5):
                try:
                    wait_element_css(brower, block_css, 5)
                    block = brower.find_element(By.CSS_SELECTOR, block_css)
                    break
                except:
                    pass
                # 验证码不出来再点击登录
                submit.click()
                time.sleep(3)

            block_width = block.value_of_css_property('width')
            block_width = int(block_width[:-2])

            slide = brower.find_element(By.CSS_SELECTOR, '#nc_1__scale_text')
            slide_width = slide.value_of_css_property("width")
            slide_width = int(slide_width[:-2])

            offset = slide_width - block_width
            action = webdriver.ActionChains(brower)
            action.click_and_hold(slide).move_by_offset(offset, 0)
            time.sleep(0.5)
            action.release().perform()

        except Exception as e:
            print(f'login_process: 登录失败 {e}')
            return False

        return True
    
    @staticmethod
    def save_cookies(cookies, file):
        """保存cookies"""
        if cookies and file:
            with open(os.path.join(info_dir, file), 'w', encoding='utf-8') as f:
                json.dump(cookies, f)
            return True
        return False
    
    @staticmethod
    def load_cookies(file):
        """读取cookies"""
        cookies = None
        if os.path.exists(os.path.join(info_dir, file)):
            with open(os.path.join(info_dir, file), 'r', encoding='utf-8') as f:
                cookies = json.load(f)
        return cookies
    
############## 车票点击预订的请求 开始 ################

    def requests_1(self):
        """点击车票预订后，第一个请求"""

        # 先加载登录cookies，再修给cookes
        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)
        
        headers = self.get_headers()
        headers['If-Modified-Since'] = '0'

        data = {
            '_json_att': '',
        }

        response = requests.post('https://kyfw.12306.cn/otn/login/checkUser', cookies=cookies, headers=headers, data=data)

        if response.status_code != 200:
            print(f'requests_1 status_code {response.status_code}')
            return False

        # '{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"flag":true},"messages":[],"validateMessages":{}}'
        # flag为true即可
        print("requests_1", response.text)
        res = json.loads(response.text)
        return res['data']['flag']
    
    def requests_2(self):
        """点击车票预订后，第二个请求"""

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Origin'] = 'https://kyfw.12306.cn'

        # TODO这行很怪，明明是错的，改了就不行
        data = f'secretStr={self.ticket_info["secretStr"]}&train_date={self.ticket_info["train_date"]}&back_train_date={str(date.today())}&tour_flag=dc&purpose_codes=ADULT&query_from_station_name={self.ticket_info["from_station"]}&query_to_station_name={self.ticket_info["to_station"]}&undefined'.encode()

        response = requests.post('https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest', cookies=cookies, headers=headers, data=data)

        if response.status_code != 200:
            print(f'requests_2 status_code {response.status_code}')
            return False
        
        res = json.loads(response.text)
        print("requests_2", res)
        # {'validateMessagesShowId': '_validatorMessage', 'status': True, 'httpstatus': 200, 'data': '0', 'messages': [], 'validateMessages': {}}
        return res['status']
    
    def requests_3(self):
        """点击车票预订后，第三个请求, 获取initDC.html中的token"""

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Origin'] = 'https://kyfw.12306.cn'
        headers['Sec-Fetch-Dest'] = 'document'
        headers['Sec-Fetch-Mode'] = 'navigaten'
        headers['Sec-Fetch-User'] = '?1'
        headers['Upgrade-Insecure-Requests'] = '1'

        data = {
            '_json_att': '',
        }

        response = requests.post('https://kyfw.12306.cn/otn/confirmPassenger/initDc', cookies=cookies, headers=headers, data=data)
        if response.status_code != 200:
            print(f'requests_3 sta tus_code {response.status_code}')
            return False
        
        html = response.text.encode('utf-8').decode('unicode_escape')
        pattern = re.compile("var globalRepeatSubmitToken = '(.*)';")
        self.globalRepeatSubmitToken = pattern.findall(html)

        # 把js的对象转成python对象
        pattern = re.compile("var ticketInfoForPassengerForm=(.*);")
        t = pattern.findall(html)[0]

        pattern = re.compile("var orderRequestDTO=(.*);")
        o = pattern.findall(html)[0]

        with VM() as vm:
            vm.run(f"""
                var ticketInfoForPassengerForm = {t};
                var orderRequestDTO = {o};
            """)
            self.ticketInfoForPassengerForm = vm.run("ticketInfoForPassengerForm")
            self.orderRequestDTO = vm.run("orderRequestDTO")
        
        if not (self.ticketInfoForPassengerForm and self.orderRequestDTO):
            return False
        
        print('requests_3 OK')
        return True

    def requests_4(self):
        """点击车票预订后，第四个请求, 获取乘车人列表信息"""

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Origine'] = 'https://kyfw.12306.cn'
        headers['Referer'] = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'

        data = {
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.globalRepeatSubmitToken,
        }

        response = requests.post(
            'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs',
            cookies=cookies,
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            print(f'requests_4 status_code {response.status_code}')
            return False
        
        print('requests_4 OK')
        self.save_passenger_info(json.loads(response.text))
        
        return True
    

    @staticmethod
    def save_passenger_info(info):
        """保存乘车人json信息"""
        with open(os.path.join(info_dir, '乘车人信息.json'), 'w') as f:
                json.dump(info, f)
    
    @staticmethod
    def load_passengers(passengers_info):
        """
        passengers_info: [
            {
                'name': '陈宇明',
                'seat_type': 'O',
                'ticket_type': '1'
            },
        ]
        """

        with open(os.path.join(info_dir, '乘车人信息.json'), 'r') as f:
                info = json.load(f)
        limit_tickets = []
        
        for p in passengers_info:
            for i in info['data']['normal_passengers']:
                if i['passenger_name'] == p['name']:
                    limit_ticket = Spider12306.get_limit_ticket(p['seat_type'], p['ticket_type'], p['name'], i['passenger_id_type_code'], i['passenger_id_no'],
                                                                i['mobile_no'], i['allEncStr'], i['passenger_type'])
                    limit_tickets.append(limit_ticket)
                    break
        
        return limit_tickets

    
############## 车票点击预订的请求 结束 ################

############## 选择乘车人的请求 开始 ################

    def requests_5(self):
        '''选择乘车人后，第一个请求'''

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Origin'] = 'https://kyfw.12306.cn'
        headers['Referer'] = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'

        # 构建乘车人的信息，在这之前需要获取候选人JSON
        self.limit_tickets = self.load_passengers(self.ticket_info['passengers'])

        # data = f'cancel_flag=2&\
        # bed_level_order_num=000000000000000000000000000000&\
        # passengerTicketStr={self.get_passengerTicketStr(self.limit_tickets)}&\
        # oldPassengerStr={self.get_oldPassengerStr(self.limit_tickets)}&\
        # tour_flag={self.ticketInfoForPassengerForm.tour_flag}&\
        # randCode=&\
        # whatsSelect=1&\
        # sessionId=&\
        # sig=&\
        # scene=nc_login&\
        # _json_att=&\
        # REPEAT_SUBMIT_TOKEN={self.globalRepeatSubmitToken}'
        data = {
            'bed_level_order_num': '000000000000000000000000000000',
            'passengerTicketStr': self.get_passengerTicketStr(self.limit_tickets),
            'oldPassengerStr': self.get_oldPassengerStr(self.limit_tickets),
            'tour_flag': self.ticketInfoForPassengerForm['tour_flag'],
            'randCode': '',
            'whatsSelect': '1',
            'sessionId': '',
            'sig': '',
            'scene': 'nc_login',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.globalRepeatSubmitToken
        }

        response = requests.post('https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo', cookies=cookies, headers=headers, data=data)
        if response.status_code != 200:
            print(f'requests_5 请求失败 {response.status_code}')
            return False

        self.checkOrderInfo_result = json.loads(response.text)
        print('requests_5', self.checkOrderInfo_result)
        return True

    @staticmethod
    def get_passengerTicketStr(limit_tickets):
        s = ''
        for limit_ticket in limit_tickets:
            stemp = limit_ticket['seat_type'] + ",0," + limit_ticket['ticket_type'] + "," + limit_ticket['name'] + "," + \
            limit_ticket['id_type'] + "," + limit_ticket['id_no'] + "," + limit_ticket['phone_no'] + "," + \
                limit_ticket['save_status'] + "," + limit_ticket['allEncStr']
            s += stemp + '_'
        if len(s) > 0:
            s = s[0:-1]
        return s
    
    @staticmethod
    def get_limit_ticket(seat_type, ticket_type, name, id_type_code, id_no, phone_no, allEncStr, passenger_type):
        limit_ticket = {}
        # O 二等座 M 一等座
        limit_ticket['seat_type'] = seat_type
        # ticket_submit_order.ticket_type 成人，儿童，学生，残疾
        limit_ticket['ticket_type'] = ticket_type
        # passenger_name 乘车人名字
        limit_ticket['name'] = name
        # passenger_id_type_code 乘车人证件代号
        limit_ticket['id_type'] = id_type_code
        # passenger_id_no 乘车人证件号码
        limit_ticket['id_no'] = id_no
        # mobile_no 乘车人手机号码
        limit_ticket['phone_no'] = phone_no
        limit_ticket['save_status'] = 'N'
        # allEncStr 乘车人标识字符串
        limit_ticket['allEncStr'] = allEncStr
        # passenger_type 
        limit_ticket['passenger_type'] = passenger_type

        return limit_ticket
    
    @staticmethod
    def get_oldPassengerStr(limit_tickets):
        s = ''
        for limit_ticket in limit_tickets:
            s += limit_ticket['name'] + ',' + limit_ticket['id_type'] + ',' + \
                limit_ticket['id_no'] + ',' + limit_ticket['passenger_type'] + '_'
        return s
    

    def requests_6(self):
        '''选择乘车人后，第二个请求'''

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['Cache-Control'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Origin'] = 'https://kyfw.12306.cn'
        headers['Referer'] = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'

        
        # data = 'train_date=Wed+Jun+07+2023+00%3A00%3A00+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&\
        #     train_no=6k000C693401&\
        #     stationTrainCode=C6934&\
        #     seatType=O&\
        #     fromStationTelecode=WAQ&\
        #     toStationTelecode=IZQ&\
        #     leftTicket=E5mMSkKSMvzM%252FZgXY34XaWT8xT8IZf3u7ClcnJmGWeq18hqi&\
        #     purpose_codes=00&\
        #     train_location=Q9&\
        #     _json_att=&\
        #     REPEAT_SUBMIT_TOKEN=93c3059ecec2f9f1d8a0f877ec758e5a'

        # 获取js的Date() 的GMT时间格式
        with VM() as vm:
            vm.run(f"""
                d = new Date({self.orderRequestDTO['train_date']['time']}).toString()
            """)
            d = vm.run("d")

        data = {
            'train_date': d,
            'train_no': self.orderRequestDTO['train_no'],
            'stationTrainCode': self.orderRequestDTO['station_train_code'],
            'seatType': self.limit_tickets[0]['seat_type'],
            'fromStationTelecode': self.orderRequestDTO['from_station_telecode'],
            'toStationTelecode': self.orderRequestDTO['to_station_telecode'],
            'leftTicket': self.ticketInfoForPassengerForm['queryLeftTicketRequestDTO']['ypInfoDetail'],
            'purpose_codes': self.ticketInfoForPassengerForm['purpose_codes'],
            'train_location': self.ticketInfoForPassengerForm['train_location'],
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.globalRepeatSubmitToken,
            # 'isCheckOrderInfo': self.checkOrderInfo_result['data']['isCheckOrderInfo']
        }

        response = requests.post('https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount', cookies=cookies, headers=headers, data=data)
        if response.status_code != 200:
            print(f'requests_6 请求失败 {response.status_code}')
            return False
        
        
        print('requests_6', response.text)
        # {"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"count":"7","ticket":"303,228","op_2":"false","countT":"0","op_1":"true"},"messages":[],"validateMessages":{}}
        return True

############## 选择乘车人的请求 结束 ################


############## 选择座位的请求 开始 ################

    def requests_7(self):
        '''选择座位后，第一个请求'''

        cookies = {}
        self.add_login_cookies(cookies)
        self.set_cookies(cookies)

        headers = self.get_headers()
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['Cache-Control'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Origin'] = 'https://kyfw.12306.cn'
        headers['Referer'] = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
        
        data = {
            'passengerTicketStr': self.get_passengerTicketStr(self.limit_tickets),
            'oldPassengerStr': self.get_oldPassengerStr(self.limit_tickets),
            'randCode': '',
            'purpose_codes': self.ticketInfoForPassengerForm['purpose_codes'],
            'key_check_isChange': self.ticketInfoForPassengerForm['key_check_isChange'],
            'leftTicketStr': self.ticketInfoForPassengerForm['leftTicketStr'],
            'train_location': self.ticketInfoForPassengerForm['train_location'],
            'choose_seats': self.ticket_info['choose_seats'],
            'seatDetailType': '000', # 上中下铺
            'encryptedData':'',
            'whatsSelect': '1',
            'roomType': '00',
            'dwAll': 'N',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self.globalRepeatSubmitToken
        }

        response = requests.post(
            'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue',
            cookies=cookies,
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            print(f'requests_7 请求失败 {response.status_code}')
            return False
        
        print('requests_7', response.text)
        return True
    



############## 选择座位的请求 结束 ################