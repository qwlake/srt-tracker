import urllib.parse

import requests


# https://sky.interpark.com/_next/data/gxa3F_U8gLqybk9NDhEDO/ko/schedules/domestic/GMP-CJU-20250501.json?adt=2&chd=0&inf=0&seat=ALL&pickAirLine=&pickMainFltNo=&pickSDate=&tripInfo=GMP-CJU-20250501
base_search_api_url = "https://sky.interpark.com/api/v1/schedule/domestic"
airline_codes = ["RS", "BX", "OZ", "LJ", "TW", "ZE", "7C", "KE"]

def get_flight_schedules(dep, arr, depDate):

    # 요청 파라미터
    params = {
        "dep": dep,
        "arr": arr,
        "depDate": depDate,
        "dep2": "",
        "arr2": "",
        "depDate2": "",
        "adt": "2",
        "chd": "0",
        "inf": "0",
        "display": "",
        "format": "json",
        "siteCode": "WEBSTD",
        "tripDivi": "0"
    }

    # 결과 저장 리스트
    results = []

    for airline in airline_codes:
        params["airlineCode"] = airline  # 항공사 코드 추가
        url = f"{base_search_api_url}?{urllib.parse.urlencode(params)}"  # URL 생성

        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            data = response.json()

            # 데이터 파싱
            fare_data = data.get("data", {}).get("replyAvailFare") or {}
            avail_fare_set = fare_data.get("availFareSet") or []

            for fare_set in avail_fare_set:
                seg_fare = fare_set.get("segFare") or {}

                airline_name = seg_fare.get("carDesc")
                departure_time = seg_fare.get("depTime")
                arrival_time = seg_fare.get("arrTime")
                fuel_charge = seg_fare.get("fuelChg")
                air_tax = seg_fare.get("airTax")
                tasf = seg_fare.get("tasf")
                class_detail = seg_fare.get("classDetail") or []

                for class_info in class_detail:
                    results.append({
                        "airline_name": airline_name,
                        "departure_time": departure_time[:2] + ':' + departure_time[2:],
                        "arrival_time": arrival_time[:2] + ':' + arrival_time[2:],
                        "fee": format(int(class_info.get("fare")) + int(fuel_charge) + int(air_tax) + int(tasf), ',') + '원',
                        "seats": class_info.get("noOfAvailSeat")
                    })

        except Exception as e:
            print(f"Error fetching data for {airline}: {e}")
            raise e

    return results

