import datetime
import time
import logging
import logging.handlers
from log4mongo.handlers import MongoHandler
from configs.configs import log_path


def beijing(sec):
    if time.strftime('%z') == "+0800":
        return datetime.datetime.now().timetuple()
    return (datetime.datetime.now() + datetime.timedelta(hours=8)).timetuple()

FORMATTER = logging.Formatter(
        '%(asctime)s - %(process)d-%(threadName)s - %(pathname)s [line:%(lineno)d]\n    %(levelname)s: %(message)s')
FORMATTER .converter = beijing # 设置时区为东八区

def create_logger(logger=None, name='None', mongodb=None, filename=None, level=logging.INFO):
    """
    mongodb: {'host': '127.0.0.1', 'port': 27017, db_name: 'log'}
    """
    if not logger:
        logger = logging.getLogger(name=name)

    logger.setLevel(level)
    
    set_stream_handler(logger, FORMATTER, level)

    if mongodb:
        set_mongo_handler(logger, mongodb, FORMATTER, level)

    if filename:
        set_file_handler(logger, filename, FORMATTER, level)

    return logger

def set_stream_handler(logger=None, formatter=FORMATTER, level=logging.INFO):
    if logger:
        console_handler = logging.StreamHandler()
        if formatter:
            console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

def set_mongo_handler(logger=None, mongodb=None, formatter=FORMATTER, level=logging.INFO):
    if logger:
        mon_handler = MongoHandler(host=mongodb['host'],
                                    port=mongodb['port'],
                                    database_name=mongodb['db_name'])
        if formatter:
            mon_handler.setFormatter(formatter)
        mon_handler.setLevel(level)
        logger.addHandler(mon_handler)

def set_file_handler(logger=None, filename=None, formatter=FORMATTER, level=logging.INFO):
    if logger and filename:
        file_handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=10485760, backupCount=5, encoding="utf-8")
        if formatter:
            file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)


logger = create_logger(filename=log_path, level=logging.DEBUG)


"""
%(asctime)s     时间格式2003-07-08 16:49:45,896
%(process)d     进程ID
%(threadName)s  线程名
%(pathname)s    发出日志记录调用的源文件的完整路径名（如果可用）。
%(lineno)d      发出日志记录调用所在的源行号
%(levelname)s   消息文本记录级别
%(message)s     记入日志的消息
"""
