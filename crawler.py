from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from dotenv import load_dotenv
from selenium.webdriver.support.wait import WebDriverWait

from log import logger

load_dotenv()


class TrainSchedule:
    def __init__(self, seat_type, departure_location, departure_time):
        self.seat_type: str = seat_type
        self.departure_location: str = departure_location
        self.departure_time: datetime = departure_time

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __str__(self):
        return self.departure_location + " " + self.departure_time.strftime("%Y%m%d %H:%M") + " " + self.seat_type


def get_driver(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222") 
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("user-data-dir=/tmp/chrome_profile")


    driver = webdriver.Chrome(service=Service(), options=options)
    driver.execute_script("return navigator.webdriver")
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(url)

    return driver


def get_train_schedules(
        url = 'https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000',
        dep = '대전',
        arr = '수서',
        dep_date = '20250401',
        dep_time = '140000',
        cnt_adult = '2',
) -> list[TrainSchedule]:
    driver = get_driver(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="search_top_tag"]/input'))
        )

        driver.find_element(By.ID, 'dptRsStnCdNm').clear()
        driver.find_element(By.ID, 'dptRsStnCdNm').send_keys(dep)  # 출발역 입력

        driver.find_element(By.ID, 'arvRsStnCdNm').clear()
        driver.find_element(By.ID, 'arvRsStnCdNm').send_keys(arr)  # 도착역 입력

        dt_options: List[WebElement] = driver.find_elements(By.XPATH, '//*[@id="dptDt"]/option')
        for option in dt_options:
            if option.get_attribute('value') == dep_date:
                option.click()
                break
        else:
            raise ValueError('출발 날짜를 찾을 수 없습니다.')

        dt_options: List[WebElement] = driver.find_elements(By.XPATH, '//*[@id="dptTm"]/option')
        for option in dt_options:
            if option.get_attribute('value') == dep_time:
                option.click()
                break
        else:
            raise ValueError('출발 시간을 찾을 수 없습니다.')

        dt_options: List[WebElement] = driver.find_elements(By.XPATH, '//*[@id="psgInfoPerPrnb1"]/option')
        for option in dt_options:
            if option.get_attribute('value') == cnt_adult:
                option.click()
                break
        else:
            raise ValueError('성인 인원 선택창을 찾을 수 없습니다.')

        driver.find_element(By.XPATH, '//*[@id="search_top_tag"]/input').click()  # 기차표 조회

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="result-form"]/fieldset/div[6]/table/tbody/tr'))
        )

        available_seats = []
        seats = driver.find_elements(By.XPATH, '//*[@id="result-form"]/fieldset/div[6]/table/tbody/tr')
        logger.debug(f"searched seats: {len(seats)}")
        for seat in seats:
            dep_location, _dep_time = seat.find_element(By.XPATH, 'td[4]').text.strip("\n").split('\n')
            dep_time = datetime.strptime(dep_date + ' ' + _dep_time, "%Y%m%d %H:%M")
            seat_button = seat.find_element(By.XPATH, 'td[7]/a').text
            if seat_button != '매진':
                available_seats.append(
                    TrainSchedule(
                        seat_type = '일반실',
                        departure_location = dep_location,
                        departure_time = dep_time,
                    )
                )
            seat_button = seat.find_element(By.XPATH, 'td[6]/a').text
            if seat_button != '매진':
                available_seats.append(
                    TrainSchedule(
                        seat_type = '특실',
                        departure_location = dep_location,
                        departure_time = dep_time,
                    )
                )

        return available_seats


    except Exception as e:
        logger.error('Error occurred while fetching train schedules', e)
        return []

    finally:
        driver.quit()
