import os
import sqlite3
# import predict_route as route
from predict_route import *
from get_route_info import *   # import Dana's main python program


# from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g

# https://inloop.github.io/sqlite-viewer/


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

DB_FILE = "route.db"

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///DB_FILE")

DBG_LOG = True
dbg('scott ....................')

db = sqlite3.connect(DB_FILE)

db.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sta_src TEXT NOT NULL,
        sta_dst TEXT NOT NULL,
        departure_time DATETIME,
        arrival_time DATETIME,
        travel_time TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

db.close()

# DROP TABLE IF EXISTS history

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/route", methods=["GET", "POST"])
def route():
    if request.method == "POST":

        # TODO: Add the user's entry into the database
        s2s_route = request.form.get("s2s_route")        
        start_date = request.form.get("departure_date_from_dormitory")
        start_time = request.form.get("departure_time_from_dormitory")
        walking_time = request.form.get("walking_time")
        transfer_time = request.form.get("transfer_time")

        if not (start_date or start_time or walking_time or transfer_time):
            print('missing route information, pleaes input')
            return redirect("/")

        # Insert data into database

        print(f'*** start_date = {start_date}, start_time = {start_time}, walking_time = {walking_time}, transfer_time = {transfer_time} ***')

        dt_start = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')

        is_use_scott_mtthod = False

        if (is_use_scott_mtthod == True):
            walking_time_list = []
            walking_time_list.append(int(walking_time))
            walking_time_list.append(int(transfer_time))

            print(walking_time_list)

            route = get_route_plan(s2s_route, dt_start, walking_time_list)

            print(route)
        else:
            route = get_route_info(s2s_route, dt_start, int(walking_time), int(transfer_time))
            print('run Dana get_route_info')
            
        sta_src = route[0]
        sta_dst = route[1]
        departure_time = route[2]
        arrival_time = route[3]
        travel_time = str(arrival_time - departure_time)

        db = getattr(g, '_database', None)

        if db is None:
            print('[Route][POST] open SQL connection')
            db = g._database = sqlite3.connect(DB_FILE)

        cur = db.cursor()

        cur.execute("INSERT INTO history (sta_src, sta_dst, departure_time, arrival_time, travel_time) VALUES(?, ?, ?, ?, ?)", (sta_src, sta_dst, departure_time, arrival_time, travel_time))

        db.commit()

        return redirect("/")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        return redirect("/")

    else:

        # TODO: Display the entries in the database on index.html

        db = getattr(g, '_database', None)

        if db is None:
            print('[GET] open SQL connection')
            db = g._database = sqlite3.connect(DB_FILE)

        db.row_factory = sqlite3.Row

        db = db.cursor()

        # Query for all 
        history_db = db.execute("SELECT * FROM history")

        rows = history_db.fetchall()

        # Render page

        print('[SC] Render page')

        return render_template("index.html", history=rows)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        print('[SC] Close SQL connection')
        db.close()

# CREATE DATABASE IF NOT EXISTS sqlite_database 


# 路徑規劃
# ----------------------------------------------------------------------------
def get_route_plan(query_route, dt_start = None, walking_time_list = None):
# ----------------------------------------------------------------------------
    # 取得行程開始時間
    if (dt_start == None):
        dt_start = get_start_time()

    if (walking_time_list == None):
        assert (walking_time_list == None)

    if query_route == 'G07_G10':
        sta_s = '公館'
        sta_d = '中正紀念堂'
        t0 = walking_time_list[0]
    elif query_route == 'R08_R10':
        sta_s = '中正紀念堂'
        sta_d = '台北車站'
        t0 = walking_time_list[0]
    elif query_route == 'G07_R10':
        sta_s = '公館'
        sta_d = '台北車站'
        t0 = walking_time_list[0] # walking time from NTU to MRT G07
        t1 = walking_time_list[1] # walking time from MRT G07 to G10

    # 計算步行時間 & 預估步行到達時間 (宿舍到公館捷運)
    w_time = get_estimated_walking_time(t0)
    predict_time = dt_start + timedelta(minutes=w_time)

    # 預估捷運行駛時間 (公館捷運到中正紀念堂捷運)
    s_time, e_time = MRT_travel_time(predict_time, '公館', '中正紀念堂')
    # dbg(s_time)
    # dbg(e_time)

    # 計算步行時間 & 預估步行到達時間 (中正紀念堂捷運, 綠線轉紅線)
    w_time = get_estimated_walking_time(t1)
    predict_time = e_time + timedelta(minutes=w_time)

    # 預估捷運行駛時間 (中正紀念堂捷運到台北車站捷運)
    s_time, e_time = MRT_travel_time(predict_time, '中正紀念堂', '台北車站')

    dt_end = e_time

    log.append(f'[99] 出發時間 {dt_start} 到達時間 {dt_end} 行駛時間 {dt_end - dt_start}')

    # return format { sta0, sta1, departure_time, arrival_time }
    return [sta_s, sta_d, dt_start, dt_end]

if __name__ == '__main__':
   app.run()
