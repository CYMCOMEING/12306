from flask import Flask
import logging
from logger import set_file_handler, FORMATTER

app = Flask(__name__)
# logging默认WARNING级别
if app.debug:
    app.logger.setLevel(logging.DEBUG)
else:
    app.logger.setLevel(logging.INFO)

set_file_handler(app.logger, 'log/flask.log', FORMATTER)


from apis.holle_world import *
from apis.train_query import *