from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from dotenv import load_dotenv

from log import logger

load_dotenv()


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
):
    driver = get_driver(url)

    try:
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

        driver.find_element(By.XPATH, '//*[@id="search_top_tag"]/input').click()  # 기차표 조회

        available_seats = []

        seats = driver.find_elements(By.XPATH, '//*[@id="result-form"]/fieldset/div[6]/table/tbody/tr')
        logger.debug(f"searched seats: {len(seats)}")
        for seat in seats:
            departure_time = seat.find_element(By.XPATH, 'td[4]').text.replace("\n", ' ')
            seat_button = seat.find_element(By.XPATH, 'td[7]/a').text
            if seat_button != '매진':
                available_seats.append({
                    'seat_type': '일반실',
                    'departure_time': departure_time.strip("\n"),
                })
            seat_button = seat.find_element(By.XPATH, 'td[6]/a').text
            if seat_button != '매진':
                available_seats.append({
                    'seat_type': '특실',
                    'departure_time': departure_time.strip("\n"),
                })

        return available_seats


    except:
        logger.error('Error occurred while fetching train schedules')
        return []

    finally:
        driver.quit()
