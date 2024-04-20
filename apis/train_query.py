from flask import views, render_template, request, jsonify
from apis import app


# from logics.zhongtie_login import *
from logics.spider12306 import Query12306, Spider12306


query12306 = Query12306()

# 主页面
# http://127.0.0.1:5000/trainquery
@app.route("/trainquery", endpoint="trainquery")
def trainquery():
    return render_template('trainquery.html')

# 提示词
@app.route("/trainquery/suggest", methods=["GET"], endpoint="trainquery_suggest")
def trainquery_suggest():
    suggest = request.args.get('q')
    results = []
    if suggest:
        results = [city for city in query12306.stations_name if suggest in city]

    print(results)
    return jsonify(results)

# 搜索车票
@app.route("/trainquery/search", methods=["GET"], endpoint="trainquery_search")
def trainquery_search():
    from_station = request.args.get('from_station')
    to_station = request.args.get('to_station')
    date = request.args.get('date')
    results = []
    if (from_station in query12306.stations_name) and (to_station in query12306.stations_name) and date:
        res = query12306.train_query(date, from_station, to_station)
        if res:
            results = query12306.get_show_data(res)

    return jsonify(results)

# 抢票
@app.route("/trainquery/buyticket", methods=["POST"], endpoint="trainquery_buyticket")
def trainquery_buyticket():
    ticket_info = {
        'train_date': request.form['train_date'],
        'from_station': request.form['from_station_name'],
        'from_station_code': request.form['from_station_telecode'],
        'to_station': request.form['to_station_name'],
        'to_station_code': request.form['to_station_telecode'],
        'user': request.form['username'],
        'password': request.form['password'],
        'passengers': [
                {
                    'name': request.form['passengers'],
                    'seat_type': 'O',
                    'ticket_type': '1'
                },
        ],
        'choose_seats': request.form['choose_seats'],
        'secretStr': request.form['secretStr'],
    }
    s1 = Spider12306(ticket_info)
    s1.start()

    return '收到'
