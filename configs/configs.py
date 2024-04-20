import os
import configparser

# 项目根目录
root_path = os.path.abspath(os.getcwd())

static_dir = os.path.join(root_path, 'static')
info_dir = os.path.join(root_path, 'info')
js_dir = os.path.join(root_path, 'js')

# 日志文件
log_path = os.path.join(root_path, 'log', 'main.log')
if not os.path.exists(os.path.dirname(log_path)):
    os.makedirs(os.path.dirname(log_path))

# Chrome位置
chrome_driver_exe_path = os.path.join(static_dir, 'chromedriver.exe')
chrome_exe_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
user_data_dir = os.path.join(static_dir, 'chrome_user_data')