import os
import random
import time
import traceback
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from crawler import get_train_schedules, TrainSchedule
from log import logger
from slack import send_slack_webhook

load_dotenv()
timezone_KST = timezone(timedelta(hours=9))
departure_time_options = '000000', '020000', '040000', '060000', '080000', '100000', '120000', '140000', '160000', '180000', '200000', '220000'

class ServerStatusMonitor:
    def __init__(self, dt, status_webhook_url, server_name):
        self.server_time_ticker = dt
        self.status_webhook_url = status_webhook_url
        self.server_name = server_name

    def tick(self):
        logger.debug("Server status monitor tick")
        current_time = self.get_current_time()
        if current_time.hour != self.server_time_ticker.hour:
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            send_slack_webhook(self.status_webhook_url, f'{current_time_str} | {self.server_name} is running')
            self.server_time_ticker = current_time

    def error(self, e: Exception | None = None):
        text = f'{self.get_current_time_str()} | {self.server_name} | Error: {e if e is not None else ""}\n{traceback.format_exc()}'
        send_slack_webhook(self.status_webhook_url, text)

    def get_current_time(self):
        return datetime.now(timezone_KST)

    def get_current_time_str(self):
        return self.get_current_time().strftime('%Y-%m-%d %H:%M:%S')


class MessageContainer:

    def __init__(self, webhook_url, tz = None):
        self.webhook_url = webhook_url
        self.timezone = tz if tz is not None else timezone(timedelta(hours=9))
        self.previous_message: Message = Message(self.timezone)
        self.message: Message = Message(self.timezone)

    def rotate(self):
        self.previous_message = self.message
        self.message = Message(self.timezone)

    def append_text(self, text):
        self.message.text += text

    def send_message(self):
        if self.previous_message.text != self.message.text:
            if self.message.text != '':
                send_slack_webhook(self.webhook_url, '<!channel>\n' + self.message.get_print_text())
            else:
                send_slack_webhook(self.webhook_url, self.message.get_print_text())


class Message:

    def __init__(self, tz = None):
        self.text = ''
        self.timezone = tz if tz is not None else timezone(timedelta(hours=9))

    def get_print_text(self):
        current_time = datetime.now(self.timezone).strftime('%m-%d %H:%M')
        print_text = self.text if self.text != '' else '좌석이 마감되었습니다.'
        return f'{print_text}\n{current_time}'


def get_search_times(start_time: datetime, end_time: datetime) -> list[str]:
    times = []
    start_time_str = start_time.strftime('%H%M') + '00'
    end_time_str = end_time.strftime('%H%M') + '00'
    for departure_time_option in departure_time_options:
        if start_time_str <= departure_time_option <= end_time_str:
            times.append(departure_time_option)
    return times


def main():
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    status_webhook_url = os.getenv('SLACK_STATUS_WEBHOOK_URL')
    server_name = os.getenv('SERVER_NAME')
    message_container = MessageContainer(webhook_url)
    server_monitor = ServerStatusMonitor(datetime.now(), status_webhook_url, server_name)

    while True:
        date = os.getenv('FLIGHT_SCHEDULE_DATE') # 20250401
        start_time_hour = os.getenv('FLIGHT_SCHEDULE_TIME_START_HOUR') # 13
        start_time_minute = os.getenv('FLIGHT_SCHEDULE_TIME_START_MINUTE', '00')
        end_time_hour = os.getenv('FLIGHT_SCHEDULE_TIME_END_HOUR') # 15
        end_time_minute = os.getenv('FLIGHT_SCHEDULE_TIME_END_MINUTE', '00')
        dep = os.getenv('FLIGHT_SCHEDULE_DEP', '대전')
        arr = os.getenv('FLIGHT_SCHEDULE_ARR', '수서')
        cnt_adult = os.getenv('COUNT_ADULT', '1')

        start_time = datetime.strptime(date + ' ' + start_time_hour + ':' + start_time_minute, '%Y%m%d %H:%M')
        end_time = datetime.strptime(date + ' ' + end_time_hour + ':' + end_time_minute, '%Y%m%d %H:%M')
        times = get_search_times(start_time, end_time)

        schedules_set = set()
        try:
            for t in times:
                schedules: list[TrainSchedule] = get_train_schedules(
                    dep=dep,
                    arr=arr,
                    dep_date=date,
                    dep_time=t,
                    cnt_adult=cnt_adult,
                )
                for schedule in schedules:
                    if start_time <= schedule.departure_time <= end_time:
                        schedules_set.add(schedule)

            message_container.append_text("\n".join([
                f"*Dep:* {schedule.departure_location} {schedule.departure_time.strftime('%m-%d %H:%M')} - *Class:* {schedule.seat_type}\n"
                for schedule in schedules_set
            ]))

            message_container.send_message()
            message_container.rotate()

        except Exception as e:
            server_monitor.error(e)

        server_monitor.tick()
        random_number = random.randint(5, 7)
        time.sleep(random_number)


if __name__ == '__main__':
    main()
