import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings'

#from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

import requests
import base64
import json
from pytz import utc

#scheduler = BackgroundScheduler(timezone=utc)
scheduler = BlockingScheduler()

# AUTO ASSIGNED SCHEDULER ----------------------------------------
@scheduler.scheduled_job('cron', id='auto_assign_job_id', hour=0)
def auto_assign():
	url = 'http://yourguy.herokuapp.com/api/v2/cron/'
	try:
		result = requests.get(url)
	except Exception e:
		print e
		# REPORT ERROR
# ----------------------------------------------------------------

# REPORTING SCHEDULER --------------------------------------------
@scheduler.scheduled_job('cron', id='daily_report_job_id', hour=17, minute=55)
def daily_report():
	print 'send_daily_report'
	url = 'http://yourguy.herokuapp.com/api/v2/daily_report/'
	try:
		result = requests.get(url)
	except Exception e:
		print e
		print 'send_daily_report : ERROR'
		# REPORT ERROR
# ----------------------------------------------------------------

scheduler.start()

while True:
	pass
