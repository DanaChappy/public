from datetime import datetime, timedelta
import requests
import json
import csv
import os

# https://zhung.com.tw/mrt-live/

# start_time = None
log = []

app_id = 'herginc-18228f71-f44e-4186'
app_key = '190e9a28-cea9-483f-b974-70c9fa58e956'

client_id = app_id  # '<your_client_id>'
client_secret = app_key  # '<your_client_secret>'

access_token = ""

PATH_CACHE = './cache'

FILE_UPDATE_TIMESTAMP = 'update_timestamp.json'
FILE_TDX_TOKEN = 'tdx_token.json'

DBG_LOG = False


# ----------------------------------------------------------------------------
def setup_environment():
# ----------------------------------------------------------------------------
    mkdir_cache()


# ----------------------------------------------------------------------------
def mkdir_cache():
# ----------------------------------------------------------------------------
    if not os.path.exists(PATH_CACHE):
        os.mkdir(PATH_CACHE)


# ----------------------------------------------------------------------------
def is_file_exist(fname):
# ----------------------------------------------------------------------------
    return os.path.exists(fname)


# ----------------------------------------------------------------------------
def create_file(fname):
# ----------------------------------------------------------------------------
    full_filename = os.path.join(path, fname)
    outfile = open(full_filename, "w", encoding='utf-8')    
    outfile.write(fname)
    outfile.close()


# return True if cache/file 不存在 or update時間 超過1天
# ----------------------------------------------------------------------------
def is_update_expired(filename):
# ----------------------------------------------------------------------------

    retval, expire_timestamp, jason_data = read_expire_timestamp_and_data(filename)

    if retval == False:
        return True

    now = datetime.now()

    if (retval == False):
        return False

    if (now > expire_timestamp):
        return True
    else:
        return False


# ----------------------------------------------------------------------------
def read_expire_timestamp_and_data(filename):
# ----------------------------------------------------------------------------
    fname = os.path.join(PATH_CACHE, FILE_UPDATE_TIMESTAMP)

    isFound = False
    list = []
    data = {}

    if is_file_exist(fname):
        infile = open(fname, "r+", encoding='utf-8')

        try:
            list = json.load(infile)
        except json.JSONDecodeError as e:
            print(f'json.JSONDecodeError: {e}')

        infile.close()

        for data in list:
            if data['filename'] == filename:
                isFound = True
                break
    else:
        dbg(f'file {fname} is not exist')
        return False, None, None
        
    if not isFound:
        return False, None, None
    else:
        return True, datetime.strptime(data['expire_timestamp'], '%Y-%m-%d %H:%M:%S'), data['json_data']


# ----------------------------------------------------------------------------
def write_update_timestamp(filename, json_data, expire_timedelta: timedelta):
# ----------------------------------------------------------------------------

    fname = os.path.join(PATH_CACHE, FILE_UPDATE_TIMESTAMP)

    isFound = False
    list = []
    data = {}

    if is_file_exist(fname):
        infile = open(fname, "r+", encoding='utf-8')
        try:
            list = json.load(infile)
        except json.JSONDecodeError as e:
            print(f'json.JSONDecodeError: {e}')

        infile.close()

        for data in list:
            if data['filename'] == filename:
                isFound = True
                expire_time = datetime.now() + expire_timedelta
                data['json_data'] = json_data
                data['update_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data['expire_timestamp'] = expire_time.strftime('%Y-%m-%d %H:%M:%S')
                data['update_times'] = data['update_times'] + 1
                break

    if not isFound:
        data = {}
        expire_time = datetime.now() + expire_timedelta
        data['filename'] = filename
        data['json_data'] = json_data
        data['update_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['expire_timestamp'] = expire_time.strftime('%Y-%m-%d %H:%M:%S')
        data['update_times'] = 1
        list.append(data)

    # dbg('-----------------------------------')
    # dbg(data)
    # dbg('-----------------------------------')

    outfile = open(fname, "w", encoding='utf-8')    
    json.dump(list, outfile, ensure_ascii=False, indent=4)
    outfile.close()


# ----------------------------------------------------------------------------
class TDX():
# ----------------------------------------------------------------------------
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_token(self):        

        now = datetime.now()
        retval, expire_timestamp, json_data = read_expire_timestamp_and_data(FILE_TDX_TOKEN)

        if (retval == True) and (now <= expire_timestamp):
            return json_data['access_token']
        else:
            json_data = None
            dbg('[07] Do not find a valid token')

        # get access_token from TDX server
        token_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(token_url, headers=headers, data=data)

        if (response.status_code != 200):
            dbg(response.status_code)
            dbg(response.text)

        assert(response.status_code == 200)

        json_data = response.json()

        # record update timestamp
        write_update_timestamp(FILE_TDX_TOKEN, json_data, timedelta(seconds=json_data['expires_in']))

        dbg(json_data['access_token'])

        return json_data['access_token']


    def get_response(self, url):
        if access_token is '':
            token = self.get_token()
        else:
            token = access_token

        headers = {'authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response
        else:
            dbg(response.status_code)
            dbg(response.text)
            assert(response.status_code == 200)
            return 'error'


# ----------------------------------------------------------------------------
def get_url_for_station_time_table(base_url, RailSystem, filter):
# ----------------------------------------------------------------------------
    format = 'JSON'
    url = f'{base_url}{RailSystem}?$filter={filter}&$format={format}'
    dbg(url)
    return url


# ----------------------------------------------------------------------------
def get_tdx_api_url(api_path, filter):
# ----------------------------------------------------------------------------

    base_url = 'https://tdx.transportdata.tw/api/basic/'

    RailSystem = 'TRTC'

    format = 'JSON'

    url = f'{base_url}{api_path}{RailSystem}?$filter={filter}&$format={format}'

    return url


# ----------------------------------------------------------------------------
def get_tdx_odata_from_server(url, filename):
# ----------------------------------------------------------------------------
    
    tdx = TDX(app_id, app_key)

    response = tdx.get_response(url)
    json_resp = response.json()

    # write tdx json data to cache file
    fname = os.path.join(PATH_CACHE, filename)
    dbg(f'[04] fname = {fname}  url = {url}')
    outfile = open(fname, "w", encoding='utf-8')     
    json.dump(json_resp, outfile, ensure_ascii=False, indent=4)    
    outfile.close()

    write_update_timestamp(filename, '', timedelta(days=3))

    return json_resp


# ----------------------------------------------------------------------------
def get_tdx_odata_from_file(filename):
# ----------------------------------------------------------------------------

    fname = os.path.join(PATH_CACHE, filename)

    infile = open(fname, "r", encoding='utf-8') 
    json_resp = json.load(infile)
    infile.close()

    return json_resp


# ----------------------------------------------------------------------------
def get_S2S_travel_time(s_station, d_station, dt = None):
# ----------------------------------------------------------------------------

    api_path = '/v2/Rail/Metro/StationTimeTable/'

    if (dt is None):
        dt = datetime.now()

    ServiceDay = '假日' if is_taiwan_holiday(dt) is True else '平日'

    if s_station == '公館' and d_station == '中正紀念堂':
        sta_id = 'G07'
        dir = 0
    elif s_station == '中正紀念堂' and d_station == '台北車站':
        sta_id = 'R08'
        dir = 0    

    filename = f'StationTime_Table_{sta_id}_Dir{dir}_{ServiceDay}.json'

    is_expired = is_update_expired(filename)

    if is_expired is True:
        filter = f"StationID eq '{sta_id}' and Direction eq {dir} and ServiceDay/ServiceTag eq '{ServiceDay}'"
        url = get_tdx_api_url(api_path, filter)
        time_table_list = get_tdx_odata_from_server(url, filename)
    else:
        time_table_list = get_tdx_odata_from_file(filename)

    # dbg(time_table)

    # trvel_time_list = []
    
    Latest_DepartureTime = '23:59'

    for time_table in time_table_list:
        table = time_table['Timetables']
        idx = timetable_binary_search(table, dt)
        if (table[idx]['DepartureTime'] < Latest_DepartureTime):
            Latest_DepartureTime = table[idx]['DepartureTime']
            route_id = time_table['RouteID']

    dbg(f'[06] Latest_DepartureTime = {Latest_DepartureTime}, RouteID = {route_id}')

    total_travel_time = 0

    travel_time_table = get_S2S_travel_time_table(route_id)

    n = len(travel_time_table)

    # dbg(f'len(travel_time_table) = {n}')

    # travel_time_list = travel_time_table[0]

    for travel_time_list in travel_time_table:
        
        TravelTimes = travel_time_list['TravelTimes']

        n = len(TravelTimes)

        sta0 = s_station
        sta1 = d_station
        total_travel_time = 0
        from_station_found = False

        for tt in TravelTimes:
            if (sta0 == tt['FromStationName']['Zh_tw']) or (sta1 == tt['FromStationName']['Zh_tw']):                
                from_station_found = True
                if (sta0 == tt['FromStationName']['Zh_tw']):
                    sta0 = ''
                else:
                    sta1 = ''

            if from_station_found == True:
                total_travel_time = total_travel_time + (tt['RunTime']+tt['StopTime'])
                dbg(f"{tt['RunTime']+tt['StopTime']}\t{tt['FromStationName']['Zh_tw']} - {tt['ToStationName']['Zh_tw']}")

                if (sta0 == tt['ToStationName']['Zh_tw']) or (sta1 == tt['ToStationName']['Zh_tw']):
                    break

                if (sta0 == '' and sta1 == ''):
                    break

        dbg(f'[05] total_travel_time = {total_travel_time} seconds')

    # next_ArrivalTime = Latest_DepartureTime + total_travel_time

    s_time = datetime.strptime(f'{dt.strftime("%Y-%m-%d")} {Latest_DepartureTime}', '%Y-%m-%d %H:%M')
    e_time = s_time + timedelta(seconds=total_travel_time)    

    return s_time, e_time


# ----------------------------------------------------------------------------
def get_S2S_travel_time_table(route_id):
# ----------------------------------------------------------------------------

    api_path = '/v2/Rail/Metro/S2STravelTime/'

    filter = f"RouteID eq '{route_id}'"

    url = get_tdx_api_url(api_path, filter)

    filename = f'S2STravelTime_{route_id}.json'

    is_expired = is_update_expired(filename)

    if is_expired is True:
        travel_time_table = get_tdx_odata_from_server(url, filename)
    else:
        travel_time_table = get_tdx_odata_from_file(filename)

    return travel_time_table


# Public Holidays in Taiwan (or Taiwan Public Holidays)
# https://www.abstractapi.com/api/holidays-api
# https://holidayapi.com/countries/tw/2025
# ----------------------------------------------------------------------------
def is_taiwan_holiday(date = None):
# ----------------------------------------------------------------------------
    if date is None:
        x = datetime.today()
    else:
        x = date

    dbg(x)
    qrydate = x.strftime('%Y%m%d')
    # dbg(qrydate)
    weekday = x.strftime('%a') # Mon, Tue, Wed, Tur, Fri, Sat, Sun
    # dbg(weekday)

    # return True if weekday in ('Sat' or 'Sun'), others return False
    # [scott] for 台北捷運, 好像不需要此判斷 (not sure)
    if qrydate in ('20240217', '20250208'):
        dbg(f'{qrydate} is make-up day')
        return False

    isHoliday = False

    # return True if weekday in ('Sat' or 'Sun'), others return False
    isWeekend = weekday in ('Sat', 'Sun')

    # dbg(isWeekend)

    if isWeekend is True:
        return True

    fname = 'TaiwanHolidayCalendar.csv'

    try:
        with open(fname, newline='') as csvfile:

            # 讀取 CSV 檔內容，將每一列轉成一個 dictionary
            Calendar = csv.DictReader(csvfile)

            # dbg(Calendar.fieldnames)

            n = 0

            # 以迴圈輸出指定欄位
            for calendar in Calendar:
                # dbg(f"{calendar['Date']}\t{calendar['isHoliday']}")
                n = n + 1
                if calendar['Date'] == qrydate:
                    if calendar['isHoliday'] == 'Y':
                        dbg(f"[02] (n={n}) {calendar['Date']} is Holiday!!")
                        isHoliday = True
                        return True
                    else:
                        dbg(f"[02] (n={n}) {calendar['Date']} is Holiday, BUT also is make-up day !!")
                        isHoliday = False
                        return False
                elif calendar['Date'] > qrydate:
                    isHoliday = False
                    break

    except FileNotFoundError:
        print(f"The file {fname} was not found")

    except IOError:
        print(f"An error occurred while reading the file {fname}")


    dbg(f"[02] (n={n}) {qrydate} is NOT a Holiday (return {isHoliday})")

    return False


# https://www.freecodecamp.org/news/how-to-search-large-datasets-in-python/
# ----------------------------------------------------------------------------
def timetable_binary_search(table, dt: datetime): 
# ----------------------------------------------------------------------------
    n = len(table)
    low = 0
    high = n - 1

    x = dt.strftime('%H:%M')
    # dbg(x)

    while low <= high:  
        mid = (low + high) // 2
        if table[mid]['ArrivalTime'] == x:
            return mid
        elif table[mid]['ArrivalTime'] < x:
            low = mid + 1
        else:
            high = mid - 1

    return low


# 預估行程開始時間
# ----------------------------------------------------------------------------
def get_start_time() -> datetime:
# ----------------------------------------------------------------------------
    dt = datetime(2025, 1, 13, 14, 16)
    t = datetime.now()
    log.append(f"({t.strftime('%H:%M:%S')}) start time: {dt}")
    return dt


# 預估步行時間 (宿舍到捷運)
# 預估步行時間 (捷運G線換捷運R線)
# ----------------------------------------------------------------------------
def get_estimated_walking_time(m):
# ----------------------------------------------------------------------------
    t = datetime.now()
    log.append(f"({t.strftime('%H:%M:%S')}) estimated_walking_time minutes {m}")
    return m


# 預估捷運行車時間
# ----------------------------------------------------------------------------
def MRT_travel_time(start_time: datetime, station0, station1):
# ----------------------------------------------------------------------------

    s_time, e_time = get_S2S_travel_time(station0, station1, start_time)

    dbg(f"[20] s_time = {s_time}, e_time = {e_time}")

    t = datetime.now()
    log.append(f"({t.strftime('%H:%M:%S')}) MRT {station0} to {station1}: {s_time} - {e_time}")
    return s_time, e_time

# 預估捷運行車時間
# ----------------------------------------------------------------------------
def THSR_travel_time(start_time: datetime, station0, station1):
# ----------------------------------------------------------------------------

    s_time, e_time = get_THSR_travel_time(station0, station1, start_time)

# /v2/Rail/THSR/DailyTimetable/TrainDate/{TrainDate}



# 路徑規劃
# ----------------------------------------------------------------------------
def predict_route():
# ----------------------------------------------------------------------------
    # 取得行程開始時間
    start_time = get_start_time()

    # 計算步行時間 & 預估步行到達時間 (宿舍到公館捷運)
    w_time = get_estimated_walking_time(10)
    predict_time = start_time + timedelta(minutes=w_time)

    # 預估捷運行駛時間 (公館捷運到中正紀念堂捷運)
    s_time, e_time = MRT_travel_time(predict_time, '公館', '中正紀念堂')
    # dbg(s_time)
    # dbg(e_time)

    # 計算步行時間 & 預估步行到達時間 (中正紀念堂捷運, 綠線轉紅線)
    w_time = get_estimated_walking_time(1)
    predict_time = e_time + timedelta(minutes=w_time)

    # 預估捷運行駛時間 (中正紀念堂捷運到台北車站捷運)
    s_time, e_time = MRT_travel_time(predict_time, '中正紀念堂', '台北車站')

    # 預估高鐵行駛時間
    # TBD

    log.append(f'[99] 出發時間 {start_time} 到達時間 {e_time} 行駛時間 {e_time - start_time}')


# 詳細路徑規劃紀錄
# ----------------------------------------------------------------------------
def dump_log():
# ----------------------------------------------------------------------------
    print('------------------------------------------------------------------------------')
    for s in log:
        print(s)
    print('------------------------------------------------------------------------------')


# ----------------------------------------------------------------------------
def dbg(str):
# ----------------------------------------------------------------------------
    if (DBG_LOG == True):
        print(str)


# ----------------------------------------------------------------------------
if __name__ == '__main__':
# ----------------------------------------------------------------------------
    setup_environment()
    predict_route()
    dump_log()
