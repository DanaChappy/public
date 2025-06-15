from datetime import datetime, timedelta
import requests
import json
# import json
# GOAL: turn all the filter into code

app_id = 'herginc-18228f71-f44e-4186'
app_key = '190e9a28-cea9-483f-b974-70c9fa58e956'

# 基礎會員金鑰存取頻率為每分鐘5次，請留意您的API呼叫頻率是否超過此限制導致。
# tdx_token = None
tdx_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJER2lKNFE5bFg4WldFajlNNEE2amFVNm9JOGJVQ3RYWGV6OFdZVzh3ZkhrIn0.eyJleHAiOjE3MzU1NzY4ODcsImlhdCI6MTczNTQ5MDQ4NywianRpIjoiZjJmYjM0NWItM2NhMi00MWJiLTg4ZjktZTc3NWMwMGI1YWEzIiwiaXNzIjoiaHR0cHM6Ly90ZHgudHJhbnNwb3J0ZGF0YS50dy9hdXRoL3JlYWxtcy9URFhDb25uZWN0Iiwic3ViIjoiMmUwMDUxMjItYmM2Ny00NmFhLWFlZWYtMmE2OThiNTA3ZTU4IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiaGVyZ2luYy0xODIyOGY3MS1mNDRlLTQxODYiLCJhY3IiOiIxIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInN0YXRpc3RpYyIsInByZW1pdW0iLCJwYXJraW5nRmVlIiwibWFhcyIsImFkdmFuY2VkIiwiZ2VvaW5mbyIsInZhbGlkYXRvciIsInRvdXJpc20iLCJoaXN0b3JpY2FsIiwiY3dhIiwiYmFzaWMiXX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInVzZXIiOiJiODY5YjA3MyJ9.itgzsqmT6lkgdrL5X4UyFohfqs3fnRv3Wg4UwHKUwc-STDq3y1rMJt8hR5hL0ZMTgkjVH9_Kk4T7-aveTFGu0iDx5hwNNMJJWM-hEfiJuDOQ7QLlgt1dzwcTn6fnTYgjz8qT6ZaEff62EM0D6sudxvLkC-UJoL3_-zVnAo55Q8nI_kvsD_20kCjS538S-MnJN_8T53gL2vf0EaLbJPxYSQuJbUKyyvMBFtfoXvVCqXYVNtzQVZnwFEf_EGaKaD9wWp7zk4lemlKWZsd2Sou23PT53YJKGAeICaC27dJpYytFoazqta17iTbtcD8XyCl6_2uem1no5lFn5lVBd8Xp6w'

# start_dt = None
start_dt_str = None
isHoliday = None
time_time = 0

def apply_for_token():
    URL = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'

    tdx_header = { 'content-type': 'application/x-www-form-urlencoded' }
    tdx_data = {
        'grant_type': 'client_credentials',
        'client_id': app_id,
        'client_secret': app_key
    }

    global tdx_token


    if not tdx_token is None:
        return True

    resp = requests.post(URL, headers = tdx_header, data = tdx_data)

    if resp.status_code == 200:
        
        print('OK')
        # print(resp.text)
        j = resp.json()
        tdx_token = j['access_token']
        print(j['access_token'])
        # tdx_token = resp['access_token']
    else:
        print(resp.status_code)
        # print(resp.text)

def get_start_datetime_information(start_dt):
    global start_dt_str, isHoliday

    # start_dt = datetime.now()
    # start_dt = datetime(2025, 1, 10)
    start_dt_str = start_dt.strftime("%Y-%m-%d")
    if (start_dt.weekday()==5 or start_dt.weekday()==6):
        isHoliday = True
    else:
        isHoliday = False

    print(f'start_dt = {start_dt}, weekday = {start_dt.weekday()}, isHoliday = {isHoliday}')

    # time_str = input("Enter a time (HH:MM): ")
    # start_str = f'{start_dt_str} {time_str}'
    # new_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M") 

    # return new_dt



def train_departure(new_time, sta_s):
    global tdx_token

    uuurl = 'https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/StationTimeTable/TRTC'

    dana_header = { 'authorization': f'Bearer {tdx_token}' }

    if isHoliday == True:
        service_workday = '假日'
    else:
        service_workday = '平日'

    print(f'new_time = {new_time}, sta_s = {sta_s}')

    if (sta_s == '公館'):
        line_id = 'G'
        sta_id = 'G07'
        
    elif (sta_s == '中正紀念堂'):
        line_id = 'R'
        sta_id = 'R08'

    print(f'line_id = {line_id}, sta_id = {sta_id}')


    filter = f"LineID eq '{line_id}' AND StationID eq '{sta_id}' AND ServiceDay/ServiceTag eq '{service_workday}' AND Direction eq 0"
    url = f'{uuurl}?$filter={filter}&$format=JSON'

    asking = requests.get(url, headers = dana_header)
    
    a = asking.json()
    json_str = json.dumps(a, indent=8, ensure_ascii=False)
    # print(asking.text)
    # print(json_str)
    with open("ooo.json", "w", encoding='utf-8') as outfile:
        outfile.write(json_str)
        outfile.close()


    
    # new_time accounted for walking to MRT station time, 10 minutes

    if asking.status_code == 200:
        
        print('OHHHH')
        # print(resp.text)
        b_list = asking.json()
        # found = False
        print('----------------------------------------')

        for b in b_list:
            if (b['StationName']['Zh_tw'] == sta_s):
                print('********************************')
                for t in b['Timetables']:
                    # print(t['ArrivalTime'])
                    # train_time = datetime.strptime(t['ArrivalTime'], "%H:%M")
                    # train_time = datetime.strptime(t['ArrivalTime'], "%H:%M")
                    start_str = f'{start_dt_str} {t['DepartureTime']}'
                    # print('===============================')
                    # print(f'start_str = {start_str}')
                    # print('===============================')

                    train_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                    difference = train_time - new_time
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    # print(train_time)
                    # print(new_time)
                    # print(difference)
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    if(difference > timedelta(minutes=0) ):
                        print("You can take train on")
                        print(t['DepartureTime'])
                        start_str = f'{start_dt_str} {t['DepartureTime']}'
                        departure_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                        # print(f'[0] departure_datetime = {departure_datetime}, start_dt_str = {start_dt_str}')
                        return departure_datetime
                        break
                        # the difference shows train arrive later
                break
                print("Sorry, out of service")
                                           

                # found = True
                # break
            # NEED to calculate which trains are after my arrival. PROB: the time we received is string not datatime mode
            # start = datetime.strptime("4:25:40", "%H:%M:%S") 
            # end = datetime.strptime("11:40:10", "%H:%M:%S") 
            # difference = end - start 
        print('----------------------------------------')
        # print(asking.text)
    else:
        print(asking.status_code)
        # print(asking.text)

    assert (False)

def train_departure_dana(sta_s):
    global tdx_token

    uuurl = 'https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/StationTimeTable/TRTC'

    dana_header = { 'authorization': f'Bearer {tdx_token}' }

    if isHoliday == True:
        service_workday = '假日'
    else:
        service_workday = '平日'

    # print(dana_header)

    if (sta_s == '公館'):
        line_id = 'G'
        sta_id = 'G07'
        
    elif (sta_s == '中正紀念堂'):
        line_id = 'R'
        sta_id = 'R08'

    filter = f"LineID eq '{line_id}' AND StationID eq '{sta_id}' AND ServiceDay/ServiceTag eq '{service_workday}' AND Direction eq 0"
    url = f'{uuurl}?$filter={filter}&$format=JSON'

    asking = requests.get(url, headers = dana_header)
    
    a = asking.json()
    json_str = json.dumps(a, indent=8, ensure_ascii=False)
    # print(asking.text)
    # print(json_str)
    with open("sample0.json", "w", encoding='utf-8') as outfile:
        outfile.write(json_str)
        outfile.close()


    time_str = input("Enter a time (HH:MM): ")
    # Convert string to datetime object
    # get user input of the time
    start_str = f'{start_dt_str} {time_str}'
    time_obj = datetime.strptime(start_str, "%Y-%m-%d %H:%M") 
    time_change = timedelta(minutes=10) 
    new_time = time_obj + time_change 
    # new_time accounted for walking to MRT station time, 10 minutes

    if asking.status_code == 200:
        
        print('OHHHH')
        # print(resp.text)
        b_list = asking.json()
        # found = False
        print('----------------------------------------')

        for b in b_list:
            if (b['StationName']['Zh_tw'] == '公館'):
                print('********************************')
                for t in b['Timetables']:
                    # print(t['ArrivalTime'])
                    # train_time = datetime.strptime(t['ArrivalTime'], "%H:%M")
                    # train_time = datetime.strptime(t['ArrivalTime'], "%H:%M")
                    start_str = f'{start_dt_str} {t['DepartureTime']}'
                    train_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M") 
                    difference = train_time - new_time
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    # print(train_time)
                    # print(new_time)
                    # print(difference)
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    if(difference > timedelta(minutes=0) ):
                        print("You can take train on")
                        print(t['DepartureTime'])
                        start_str = f'{start_dt_str} {t['DepartureTime']}'
                        departure_datetime = datetime.strptime(start_str, "%Y-%m-%d %H:%M") 
                        return departure_datetime
                        break
                        # the difference shows train arrive later
                break
                print("Sorry, out of service")
                                           

                # found = True
                # break
            # NEED to calculate which trains are after my arrival. PROB: the time we received is string not datatime mode
            # start = datetime.strptime("4:25:40", "%H:%M:%S") 
            # end = datetime.strptime("11:40:10", "%H:%M:%S") 
            # difference = end - start 
        print('----------------------------------------')
        # print(asking.text)
    else:
        print(asking.status_code)
        # print(asking.text)


def train_move_time(sta_s, sta_e):
    global time_time

    time_time = 0

    if (sta_s == '公館' and sta_e == '中正紀念堂'):
        line_id = 'G'
        route_id = 'G-1'
        sta_id = 'G07'
        dd_FromStationName = '中正紀念堂'
        dd_ToStationName = '公館'
    elif (sta_s == '中正紀念堂' and sta_e == '台北車站'):
        line_id = 'R'
        route_id = 'R-2'
        sta_id = 'R08'
        dd_FromStationName = '台北車站'
        dd_ToStationName = '中正紀念堂'

    # LineID eq 'G' AND StationID eq 'G07'

    uurl = 'https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/S2STravelTime/TRTC'

    filter = f"RouteID eq '{route_id}'"
    
    url = f'{uurl}?$filter={filter}&$format=JSON'
    print(f'url = {url}')

    scott_header = { 'authorization': f'Bearer {tdx_token}' }

    # print(scott_header)    

    asking = requests.get(url, headers=scott_header)
    if asking.status_code == 200:
        
        print('OK')

        # print(resp.text)
        s2_travel_time_list = asking.json()
        json_str = json.dumps(s2_travel_time_list, indent=4, ensure_ascii=False)

        with open("xxx.json", "w", encoding='utf-8') as outfile:
            outfile.write(json_str)
            outfile.close()


        # print(asking.text)
        # print(json_str)
        # Say from is NTU, then go to 中正
        is_cks = False
        for travel_time in s2_travel_time_list:
            print(f'RouteID = {travel_time['RouteID']}')
            for tt in (travel_time['TravelTimes']):
                print(tt['FromStationName']['Zh_tw'])

                if(tt['FromStationName']['Zh_tw'] == dd_FromStationName):
                    is_cks = True

                if(is_cks == True):
                    timesum = tt['RunTime'] + tt['StopTime']
                    print(timesum)
                    time_time = time_time + timesum

                if(tt['ToStationName']['Zh_tw'] == dd_ToStationName):
                    break


        return timedelta(seconds=time_time)
        
    else:
        print(asking.status_code)
        print(asking.text)
        return None
    
    



def get_route_info(route_id, dt_start, t0, t1):

    print('-----------------------------------------------------')
    print(f'route_id = {route_id}, dt_start = {dt_start}, t0 = {t0}, t1 = {t1}')
    print('-----------------------------------------------------')

    if (route_id == 'G07_R10'):
        G07 = '公館'
        G10 = R08 = '中正紀念堂'
        R10 = '台北車站'
        sta_s = G07
        sta_d = R10
    elif (route_id == 'G07_G10'):
        G07 = '公館'
        G10 = R08 = '中正紀念堂'
        R10 = '台北車站'
    elif (route_id == 'R08_R10'):
        G07 = '公館'
        G10 = R08 = '中正紀念堂'
        R10 = '台北車站'
    else:
        return 'error'

    if (t0 == None):
        t0 = 10

    if (t1 == None):
        t0 = 1

    apply_for_token()

    get_start_datetime_information(dt_start)

    start_dt = dt_start

    print(f'start_dt = {start_dt}')
 
    G07_arrival_time = start_dt + timedelta(minutes=t0)

    print(f'G07_arrival_time = {G07_arrival_time}')

    departure_datetime = train_departure(G07_arrival_time, G07)

    print(f'departure_datetime = {departure_datetime}, type = {type(departure_datetime)}')

    travel_time = train_move_time(G07, G10)

    print(f'travel_time = {travel_time}, type = {type(travel_time)}')

    R08_arrival_time = departure_datetime + travel_time

    print(f'departure_datetime = {departure_datetime}  travel_time = {travel_time} R08_arrival_time = {R08_arrival_time}')

    R08_arrival_time = R08_arrival_time + timedelta(minutes=t1)

    print(f'new R08_arrival_time = {R08_arrival_time}')

    departure_datetime = train_departure(R08_arrival_time, R08)

    travel_time = train_move_time(R08, R10)

    R10_arrival_time = departure_datetime + travel_time

    print(f'departure_datetime = {departure_datetime}  travel_time = {travel_time} R10_arrival_time = {R10_arrival_time}')

    dt_end = R10_arrival_time

    # return format { sta0, sta1, departure_time, arrival_time }
    return [sta_s, sta_d, dt_start, dt_end]


if __name__ == '__main__':
    get_route_info()
