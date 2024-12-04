from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from my_package.crawler import *

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    def scheduled_job():
        header, total_data = extract_date(crawler_source_code())
        evaluate_water_quality(total_data)
        handle_date(total_data)
        data_list = handle_missing_data(total_data)
        save_to_mysql(data_list)

    scheduler.add_job(scheduled_job, "interval", hours=1)

    scheduler.start()



