from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

import os
import time
import json
import requests
import urllib.parse
from datetime import date

from configs.configs import info_dir
from logics.selenium_base import *


def login(username, password):
    """登录获取cookie"""
    brower = get_brower(headless=False)
    cookies = []

    login_process(brower, username, password)

    time.sleep(5)
    cookies = brower.get_cookies()
    brower.close()

    return cookies


def login_process(brower, username, password):
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
        print(e)
        return False

    return True


def order_ticket(username, password, train_date, from_station, to_station, train_no, passengers, seats):
    """抢票
    train_date: 班次日期 yyyy-mm-dd
    from_station: 出发站代号
    to_station: 终点站代号
    train_no: 班次号
    """

    brower = get_brower()

    url = 'https://www.12306.cn/index/index.html'

    try:
        brower.get(url)
        time.sleep(1)

        if not wait_elenemt(brower, '#fromStationText'):
            print("打开主页失败")
            return

        # 通过logout检查是否需要登录
        login_ele = brower.find_element(By.CSS_SELECTOR, '#J-btn-login')
        if login_ele:
            # 登录操作
            if not login_process(brower, username, password):
                return False
            time.sleep(1)
            # 登录成功会显示注销
            if not wait_elenemt(brower, '#J-header-logout > a.logout'):
                print('登录失败')
                return
            else:
                # 登录成功后打开主页
                brower.get(url)
                time.sleep(1)

                if not wait_elenemt(brower, '#fromStationText'):
                    print("打开主页失败")
                    return

        # 提交搜索部分
        from_ele = brower.find_element(By.CSS_SELECTOR, '#fromStationText')
        from_ele.clear()
        from_ele.send_keys(from_station)
        from_ele.send_keys(Keys.ENTER)

        to_ele = brower.find_element(By.CSS_SELECTOR, '#toStationText')
        to_ele.clear()
        to_ele.send_keys(to_station)
        to_ele.send_keys(Keys.ENTER)

        date_ele = brower.find_element(By.CSS_SELECTOR, '#train_date')
        date_ele.clear()
        date_ele.send_keys(train_date)
        date_ele.send_keys(Keys.ENTER)

        submit = brower.find_element(By.CSS_SELECTOR, '#search_one')
        submit.click()
        time.sleep(1)

        # 提交搜索后会弹出新的标签
        handles = brower.window_handles
        brower.switch_to.window(handles[1])

        if not wait_elenemt(brower, '#queryLeftTable tr td'):
            print("搜索车次失败")
            return

        # 找出对应车次
        trains = brower.find_elements(
            By.CSS_SELECTOR, "#queryLeftTable tr td div div div a")
        index = -1
        for i, train in enumerate(trains):
            if train.text == train_no:
                index = i
                break

        if index == -1:
            print('没有找到对应班次')
            return

        # 预订，点击进入订单界面
        submits = brower.find_elements(
            By.CSS_SELECTOR, "#queryLeftTable td.no-br > a")
        submit = submits[index]
        submit.click()
        time.sleep(1)

        if not wait_elenemt(brower, '#normal_passenger_id'):
            print("预订车票失败")
            return

        # 获取乘车人
        inputs = brower.find_elements(
            By.CSS_SELECTOR, "#normal_passenger_id > li > input")
        lis = brower.find_elements(
            By.CSS_SELECTOR, "#normal_passenger_id > li")

        l_passengers = [str(l.text) for l in lis]

        # 点击乘车人
        for i, p in enumerate(l_passengers):
            if p in passengers:
                inputs[i].click()
        time.sleep(0.5)

        # 选择票种，席别
        trs = brower.find_elements(By.CSS_SELECTOR, "#ticketInfo_id > tr")
        trs = [trs[i] for i in range(len(trs)) if i % 2 == 0]
        for tr in trs:
            # tds 1 票种 2 席别 3 名字
            tds = tr.find_elements(By.CSS_SELECTOR, 'td')

            # sellect_ele = tds[1].find_element(By.CSS_SELECTOR, "select")
            # select = Select(sellect_ele)
            # # 1 成人票 2 儿童票 3 学生票 4 残军票  #dialog_xsertcj_ok
            # select.select_by_value("2")

            sellect_ele = tds[2].find_element(By.CSS_SELECTOR, "select")
            select = Select(sellect_ele)
            # O 二等座 M 一等座 3 硬卧 1 硬座
            select.select_by_value("M")

        # 提交订单
        submit = brower.find_element(By.CSS_SELECTOR, '#submitOrder_id')
        submit.click()
        time.sleep(1)

        if not wait_elenemt(brower, '#erdeng1'):
            print("提交乘车人失败")
            return

        # 选座
        seat_item = brower.find_elements(
            By.CSS_SELECTOR, '#id-seat-sel > div.seat-sel-bd > div')
        seat_item = [seat_item[i] for i in range(len(seat_item)) if i % 4 == 0]
        for item in seat_item:
            seat_sel = item.find_elements(By.CSS_SELECTOR, 'ul > li > a')
            for seat in seats:
                for sel in seat_sel:
                    if sel.text == seat:
                        sel.click()
                        break
        time.sleep(0.5)

        # 提交订单
        submit = brower.find_element(By.CSS_SELECTOR, '#qr_submit_id')
        submit.click()
        # 判断提交按钮是否存在，不存在表示已经按下去，存在继续按，抢不抢到票听天由命
        for _ in range(5):
            ele = brower.find_element(By.CSS_SELECTOR, '#qr_submit_id')
            if not ele:
                break
            time.sleep(0.5)
            submit.click()

    except:
        pass
    finally:
        brower.close()
        pass

    print('ok')


def wait_elenemt(brower, css, wait_time=0.5, times=10):
    """等待selenium加载元素"""
    for _ in range(times):
        try:
            wait_element_css(brower, css, wait_time=wait_time)
        except:
            pass
        ele = brower.find_element(By.CSS_SELECTOR, css)
        if ele:
            return True
    return False


def verify_login(cookies):
    """验证12306cookie
    12306 cookie有效期一小时不到"""
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Cookie': 'JSESSIONID=AF91A217B9D4EDF80E27A49508245E4F; tk=mh3BLvrEBPYiSPAs2d6WXjHKcBQ9ldtYaOJvuOSCwiQ09q1q0; BIGipServerotn=602407178.64545.0000; BIGipServerpassport=870842634.50215.0000; route=6f50b51faa11b987e576cdb301e545c4; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off; uKey=7a71c8a65fca6b5fca02caad9984a1a76275455a96f9f4f3d73a2544d1779c95; fo=87wpl64e95a8c31cfd_U2UnLj1gj0AH1K7mocNdvTL-Bpsgi4q_V5fCZc7tryIqmKBN1Ed_JUyGg3LwV0AWuR08rVXjdreVOn2wmldqAjJi12i0bjf_Wx2hDE-GX3ouqROCeCi0m_sxzyubhJXR4TBT_EXcd7yo5mVnJYRJO9yDSwkVvi9xJsMxGSsg',
        'Pragma': 'no-cache',
        'Referer': 'https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    url = 'https://kyfw.12306.cn/otn/view/index.html'
    resp = requests.get(url, cookies=cookies, headers=headers)
    if resp.status_code == 200:
        return True
    return False


def save_cookies(cookies, file):
    # 保存cookie
    if cookies and file:
        with open(os.path.join(info_dir, file), 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
        return True
    return False


def load_cookies(file):
    # 读取cookie
    cookies = None
    if os.path.exists(os.path.join(info_dir, file)):
        with open(os.path.join(info_dir, file), 'r', encoding='utf-8') as f:
            cookies = json.load(f)
    return cookies


def train_query(train_date, from_station, to_station):
    """班次查询请求
    train_date: 班次日期 yyyy-mm-dd
    from_station: 出发站代号
    to_station: 终点站代号
    """

    referer_url = 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={},{}&ts={},{}&date={}&flag=N,Y,Y'.format(
        urllib.parse.quote(stations_data[from_station]),
        from_station,
        urllib.parse.quote(stations_data[to_station]),
        to_station,
        train_date
    )

    cookies = {
        # 'tk': 'MK4P8hFDhna2k8gOqbc3PmA3uPpKOt_a7IP2RJ1kvCo09q1q0',
        # 'JSESSIONID': '2075708A40DAFE9129EB7E5DCD7B97E2',
        # 'BIGipServerotn': '602407178.64545.0000',
        # 'BIGipServerpassport': '870842634.50215.0000',
        # 'route': '6f50b51faa11b987e576cdb301e545c4',
        'guidesStatus': 'off',
        'highContrastMode': 'defaltMode',
        'cursorStatus': 'off',
        # 'fo': '940lioawb9e42c2hp9sJU5C2h8VJGXYciNwIVa4xumjpTc-6jWBMA5Gtvwefr0OGBP4rnlKa6719UwgY6yiCGZqwZGXXekY2u12rJ0Sw1IG3XK_UGhzHBTXPyvrLjVXmC6TSWICDzl0_oQNWvS-uODDA1PPcOUysbxJXVFk5SdLGCpF3MXYMx-A_ug8',
        '_jc_save_fromStation': '{}%2C{}'.format(to_unicode_with_percent(from_station), from_station),
        '_jc_save_toStation': '{}%2C{}'.format(to_unicode_with_percent(to_station), to_station),
        '_jc_save_toDate': train_date,
        '_jc_save_wfdc_flag': 'dc',
        # 'current_captcha_type': 'Z',
        '_jc_save_fromDate': str(date.today()),
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Cookie': 'tk=MK4P8hFDhna2k8gOqbc3PmA3uPpKOt_a7IP2RJ1kvCo09q1q0; JSESSIONID=2075708A40DAFE9129EB7E5DCD7B97E2; BIGipServerotn=602407178.64545.0000; BIGipServerpassport=870842634.50215.0000; route=6f50b51faa11b987e576cdb301e545c4; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off; fo=940lioawb9e42c2hp9sJU5C2h8VJGXYciNwIVa4xumjpTc-6jWBMA5Gtvwefr0OGBP4rnlKa6719UwgY6yiCGZqwZGXXekY2u12rJ0Sw1IG3XK_UGhzHBTXPyvrLjVXmC6TSWICDzl0_oQNWvS-uODDA1PPcOUysbxJXVFk5SdLGCpF3MXYMx-A_ug8; _jc_save_fromStation=%u5434%u5DDD%2CWAQ; _jc_save_toStation=%u5E7F%u5DDE%u5357%2CIZQ; _jc_save_toDate=2023-05-11; _jc_save_wfdc_flag=dc; current_captcha_type=Z; _jc_save_fromDate=2023-05-12',
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

    params = {
        'leftTicketDTO.train_date': train_date,
        'leftTicketDTO.from_station': from_station,
        'leftTicketDTO.to_station': to_station,
        'purpose_codes': 'ADULT',
    }

    resp = requests.get('https://kyfw.12306.cn/otn/leftTicket/query',
                        params=params, cookies=cookies, headers=headers)

    if resp.status_code == 200:
        resp.encoding = 'utf-8'
        return resp.text

    return None


def to_unicode_with_percent(s: str) -> str:
    """中文转unicode，以%u前缀返回"""
    u = s.encode('unicode-escape').decode()
    u.replace('\\', '%')
    return u


def pares_train_query(data):
    """班次查询ajax返回数据解析"""

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


def pares_station():
    """解析站名数据
    https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9261"""

    file = os.path.join(static_dir, 'station_names.txt')
    with open(file, 'r', encoding='utf-8') as f:
        station_names = f.read()

    if not station_names:
        return None

    # @bjb|北京北|VAP|beijingbei|bjb|0|0357|北京||
    stations = {}
    for station in station_names.split('@')[1:]:
        index = station.split('|')
        stations[index[2]] = index[1]

    return stations


stations_data = pares_station()


def get_stations_list():
    # 返回站名中文列表
    return list(stations_data.values())


stations_list = get_stations_list()


def get_station_code(name):
    # 站名中文转站名代码
    for k, v in stations_data.items():
        if v == name:
            return k


def parse_price(yp_info_new, zw):
    """从字段yp_info_new解析出价格
    根据zw给的字符串常量，就获取哪个座位的价格
    """
    res = ''
    length = len(yp_info_new) // 10
    for i in range(length):
        substr = yp_info_new[10 * i: 10 * (i + 1)]
        # 前缀
        s1 = substr[0: 1]
        # 价格
        s2 = str(int(substr[1:6]) // 10)
        s3 = substr[6: 10]
        if "SWZ_" == zw:
            if (s1 == "9"):
                res += "商务座票价" + s2 + "元"
                return res
        if "TZ_" == zw:
            if (s1 == "P"):
                res += "特等座票价" + s2 + "元"
                return res
        if "ZY_" == zw:
            if (s1 == "M"):
                res += "一等座票价" + s2 + "元"
                return res
        if "ZE_" == zw:
            if (s1 == "O"):
                res += "二等座票价" + s2 + "元"
                return res
            if (s1 == "S"):
                res += "二等包座票价" + s2 + "元"
                return res
        if "GR_" == zw:
            if (s1 == "6"):
                res += "高级软卧票价" + s2 + "元"
                return res
        if "RW_" == zw:
            if (s1 == "4"):
                res += "软卧票价" + s2 + "元"
                return res
            if (s1 == "I"):
                res += "一等卧票价" + s2 + "元"
                return res
        if "SRRB_" == zw:
            if (s1 == "F"):
                res += "动卧票价" + s2 + "元"
                return res
        if "YW_" == zw:
            if (s1 == "P"):
                res += "硬卧票价" + s2 + "元"
                return res
            if (s1 == "J"):
                res += "二等卧票价" + s2 + "元"
                return res
        if "RZ_" == zw:
            if (s1 == "2"):
                res += "软座票价" + s2 + "元"
                return res
        if "YZ_" == zw:
            if (s1 == "1"):
                res += "硬座票价" + s2 + "元"
                return res
        if "WZ_" == zw:
            if (s3 >= 3000):
                res += "无座票价" + s2 + "元"
                return res
        if "QT_" == zw:
            if (s1 != "9" & s1 != "P" & s1 != "M" & s1 != "O" & s1 != "S" & s1 != "6" & s1 != "4" & s1 != "I" & s1 != "F" & s1 != "3" & s1 != "J" & s1 != "2" & s1 != "1" & s3 < 3000):
                res += "其他席位票价" + s2 + "元"
                return res
    return ''


############## 查询车票状态部分代码################
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


def get_show_data(trains):
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
        res.append(info)

    return res

############## 查询车票状态部分代码结束 ################

def add_login_to_cookies(cookies, file):
    """给cookie添加登录信息"""
    login_cookie = load_cookies(file)
    for cookie in login_cookie:
        cookies[cookie['name']] = cookie['value']


############## 车票点击预订的请求 开始 ################

def get_order_header(train_date, from_station, to_station):
    '''获取点击车票预订后的请求头'''

    referer_url = 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={},{}&ts={},{}&date={}&flag=N,N,Y'.format(
        urllib.parse.quote(stations_data[from_station]),
        from_station,
        urllib.parse.quote(stations_data[to_station]),
        to_station,
        train_date
    )

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'JSESSIONID=B0C3A63FBB066E2E50C93537F97D669A; tk=-GTDDWBD96UhwtYdXAVOHjCx4yhA2yBs_B1_gjOzNDketq1q0; route=495c805987d0f5c8c84b14f60212447d; BIGipServerotn=4057399562.50210.0000; _jc_save_fromStation=%u5434%u5DDD%2CWAQ; _jc_save_toStation=%u5E7F%u5DDE%u5357%2CIZQ; _jc_save_wfdc_flag=dc; guidesStatus=off; highContrastMode=defaltMode; cursorStatus=off; BIGipServerpassport=837288202.50215.0000; current_captcha_type=Z; fo=undefined; _jc_save_showIns=true; _jc_save_fromDate=2023-05-31; uKey=7a71c8a65fca6b5fca02caad9984a1a784051b465dd971438ea75325a1b5d3a9; _jc_save_toDate=2023-05-29',
        'Origin': 'https://kyfw.12306.cn',
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

def get_order_header(train_date, from_station, to_station):
    '''获取点击车票预订后的请求cookies'''

    cookies = {
        # 'uKey': '7a71c8a65fca6b5fca02caad9984a1a7c975bd0fed278f1cc73d92151e4200a0',
        # 'JSESSIONID': '8EFACEA54E335FF08A6803B8D7C52303',
        # 'tk': '-Yk41qjieVaE_PQMfxg9rkXtenZT_rwlma3zTfsvQsDgfsq1q0',
        'route': '495c805987d0f5c8c84b14f60212447d',
        # 'BIGipServerotn': '4057399562.50210.0000',
        '_jc_save_fromStation': '{}%2C{}'.format(to_unicode_with_percent(from_station), from_station),
        '_jc_save_toStation': '{}%2C{}'.format(to_unicode_with_percent(to_station), to_station),
        '_jc_save_wfdc_flag': 'dc',
        'guidesStatus': 'off',
        'highContrastMode': 'defaltMode',
        'cursorStatus': 'off',
        # 'BIGipServerpassport': '837288202.50215.0000',
        'current_captcha_type': 'Z',
        'fo': 'undefined',
        '_jc_save_showIns': 'true',
        '_jc_save_fromDate': train_date,
        '_jc_save_toDate': str(date.today()),
    }

    add_login_to_cookies(cookies, 'zhongtie.cookies.json')

    return cookies

def requests_1(train_date, from_station, to_station):
    """点击车票预订后，第一个请求
    train_date: 班次日期 yyyy-mm-dd
    from_station: 出发站代号
    to_station: 终点站代号
    """
    
    cookies = get_order_header(train_date, from_station, to_station)
    headers = get_order_header(train_date, from_station, to_station)
    headers['If-Modified-Since'] = '0'
    data = {
        '_json_att': '',
    }

    response = requests.post('https://kyfw.12306.cn/otn/login/checkUser', cookies=cookies, headers=headers, data=data)

    # '{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"flag":true},"messages":[],"validateMessages":{}}'
    # flag为true即可
    return response.text

def requests_2(train_date, from_station, to_station, secretStr):
    """点击车票预订后，第二个请求
    train_date: 班次日期 yyyy-mm-dd
    from_station: 出发站代号
    to_station: 终点站代号
    """

    cookies = get_order_header(train_date, from_station, to_station)
    headers = get_order_header(train_date, from_station, to_station)

    data = 'secretStr=ddd2%2FK9B8zJW1X5rzeo%2FhizzP5%2BpkdI8qjgYnEIPFF5cFmlP4vf6M%2Ffd2S8yY3aU7oUxwNtIvtGi%0Ach%2Fv6yfvkIxY1KMdc0wQEJP%2FmugfI0SxiJ93qVRMeL1D0MxYHd8D8yK0j2ERBNrRJ1znPPYPcbSF%0As8R7rIe%2FPC%2FWASOs03vfipUpy6KSyr%2BqFs%2FmCB%2BxeZP08mtlJHnQ3oNG4bbHVqmJ3cw%2F51tnZf87%0A8yhwD98kO%2FxxUHd53SE%2Fm9%2FGiozeU9UhZHdDiLpj%2F1ywvf6cHD1DbwY7YceXmVwrOfUabuu93lLZ%0AFgihGsbIJmAJ2xlZb8vvai28TiU%3D \
    &train_date=2023-05-31 \
    &back_train_date=2023-05-29 \
    &tour_flag=dc \
    &purpose_codes=ADULT \
    &query_from_station_name=吴川 \
    &query_to_station_name=广州南 \
    &undefined'.encode()

    response = requests.post('https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest', cookies=cookies, headers=headers, data=data)


############## 车票点击预订的请求 结束 ################


if __name__ == "__main__":
    pass
