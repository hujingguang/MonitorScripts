#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import setproctitle
from logging.handlers import RotatingFileHandler
from signal import SIGTERM
import time
import multiprocessing.managers
import socket
import threading
import commands
import copy
from datetime import datetime
import requests
try:
    import simplejson
    json=simplejson
except ImportError,e:
    import json

_LOG_INFO={
"log_level":logging.INFO,
"log_format":'%(asctime)-15s %(levelname)s %(lineno)s %(message)s',
"log_file":'/var/log/agent.log',
"log_max_size":100000000,
"log_backup":7,
}
_PID_FILE='/var/run/agent.pid'
_DEBUG=False
QUEUE_INFO={
	'queue_ip':'4.17.6.24',
	'queue_port':4502,
	'queue_auth':'Ab'
	}
r,HOSTNAME=commands.getstatusoutput('hostname')
REGION_CONF={'hb1':'青岛',
	'hb2':'北京',
	'hb3':'张家口',
	'hb5':'呼和浩特',
	'hd1':'杭州',
	'hd2':'上海',
	'hn1':'深圳',
	'hk':'香港',
	}
REGION=''
for region in REGION_CONF:
    if HOSTNAME.find(region) != -1:
	REGION=REGION_CONF[region]

'''
此处添加需要检查的API地址
'''
API_TARGET={
	"crm_monitor_http_key":"https://crm.imlaidian.com/crm-api/crmMonitor",
	"crm_ad_monitor_http_key":"https://cnt.imlaidian.com/adcrm/adMonitor",
	"crm_api-http":"https://crm.imlaidian.com/crm-api/crmMonitor",
	"device_is_available_check":"https://mobile-api.imlaidian.com/cdt/deviceArgs?terminal=000020001650",
	"wx.imlaidian.com-local":"https://wx.imlaidian.com/share/js/switch.js",
	"wx.imlaidian.com-wx":"https://wx.imlaidian.com/weixin/css/weixin.css",
	"www.imlaidian.com":"https://www.imlaidian.com/css/all.min.css",
	"online_ad_monitor":"https://ad.imlaidian.com/ad-job-api/monitor",
	"bg_web":"https://bg.imlaidian.com",
	"ali_web":"https://ali.imlaidian.com/share",
	}

'''
此处添加需要检查的Ping地址
'''
PING_TARGET={'lb-002':['106.75.48.173','lb-002.laidiantech.com','lb-002.imlaidian.com'],
	'lb-001':['106.75.114.82','lb-001.laidiantech.com','lb-001.imlaidian.com'],
	'wx-010':['wx-cdt-bj-010.imlaidian.com',],
	'wx-007':['wx-cdt-bj-007.imlaidian.com',],
	'mobile-api':['mobile-api.imlaidian.com'],
	'www.imlaidian.com':['www.imlaidian.com'],
	'wx.imlaidian.com':['wx.imlaidian.com'],
	'crm-api':['crm.imlaidian.com'],
	'terminal-api2':['terminal-api2.imlaidian.com'],
	}



'''
函数返回数据格式 {"hostname":"ld-hn1-1",
                   "type":"ping",
		   "result":1,
		   "datetime":"2018-08-20 19:00:01",
		   "target":"120.19.11.23",
		   "info":"",
		   'region':'',
		   "standby":''
		 }
'''

DEFAULT_DATA={
	"hostname":HOSTNAME,
	"type":'',
	"result":0,
	"datetime":"",
	"target":"",
	"region":REGION,
	"info":"",
	"standby":"",
	}

def check_ping(queue,logger):
    global PING_TARGET
    target=PING_TARGET
    def analyse_result(data):
	lines=data.split('\n')
	loss,avg_time,run_time,result=0,0,'',0
	for line in lines:
	    if line.find('loss') != -1:
		loss=int(line.split(',')[2].replace(' ','').split('%')[0])
		run_time=line.split(',')[3].split(' ')[-1]
	    if line.find('rtt') != -1:
		avg_time=float(line.split(' ')[3].split('/')[1])
        if loss>=25 or avg_time >= 1000:
	    result=1
	info='packet loss : {0}%, total run time: {1} , avg time: {2} ms'.format(str(loss),run_time,str(avg_time))
	return [result,avg_time,run_time,loss,info]

    for k,v in target.iteritems():
	for ip in v:
            send_data=copy.deepcopy(DEFAULT_DATA)
            send_data['type']='Ping'
            cmd='ping -c 4 -s 500 -w 5 -W 3 '+ip
	    code,result=commands.getstatusoutput(cmd)
	    send_data["datetime"]=datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
	    result=analyse_result(result)
	    send_data['result'],send_data['info'],send_data['target']=result[0],result[-1],ip
	    try:
		send_data=json.dumps(send_data)
	    except Exception as e:
		logger.error(str(e))
		send_data=None
		continue
	    try:
		queue.put(send_data)
	    except Exception as e:
		logger.error(str(e))
		return
	    send_data=None


def check_api(queue,logger):
    global API_TARGET
    target=API_TARGET
    for k,v in target.iteritems():
        send_data=copy.deepcopy(DEFAULT_DATA)
        send_data['type']='Api'
        send_data['target']=v
	send_data["datetime"]=datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
	info=''
	try:
	    check_status=0 #0 is sucessed ,1 is failed
	    b_time=time.time()
	    result=requests.get(v,timeout=12)
	    e_time=time.time()
	    u_time=str(e_time-b_time)
	    if result.status_code != 200:
		info="Status_code: %s Content_Length: %s , Response Time: %s s" %(str(result.status_code),result.headers.get("Content-Length","Null"),u_time)
		check_status=1
	    else:
		try:
		    d=result.json()
		    status=d.get('result',None)
		    if status == 1:
		        info="Status_code: %s Content_Length: %s , Response Time: %s s" %(str(result.status_code),result.headers.get("Content-Length","Null"),u_time)
		    elif not status:
		        info="Status_code: %s Content_Length: %s , Response Time: %s s" %(str(result.status_code),result.headers.get("Content-Length","Null"),u_time)
		    else:
			info="json data result key value is not 1"
			check_status=1
		except Exception as e:
		    logger.info(str(e))
		    info="Status_code: %s Content_Length: %s , Response Time: %s s" %(str(result.status_code),result.headers.get("Content-Length","Null"),u_time)
	except Exception as e:
	    check_status=1
	    logger.info(str(e))
	    info='响应时间超过12s'
	send_data['info']=info
	send_data['result']=check_status
	try:
	    send_data=json.dumps(send_data)
	except Exception as e:
	    logger.error(str(e))
	    send_data=None
	    continue
	try:
	    queue.put(send_data)
	except Exception as e:
	    logger.error(str(e))
	    return
	send_data=None

#callbacks 填入编写的监控插件函数名,按照规定的数据格式返回数据
CALL_BACKS=[check_ping,check_api]
#检测时间间隔
CHECK_INTERNAL=50

class Daemon(object):
    def __init__(self):
	self._pid_file=_PID_FILE
	self._std_in_file='/dev/null'
	self._std_out_file='/dev/null'
	self._std_err_file=_LOG_INFO.get('log_file','/var/log/agent.log')
	self.logger_ok=False
	self.logger=None

    def set_logger(self):
	global _LOG_INFO,_DEBUG
	logging.basicConfig(level=logging.DEBUG,filename='/dev/null')
	Logger=logging.getLogger('Agent')
	log_level=_LOG_INFO.get('log_level',logging.INFO)
	log_format=logging.Formatter(_LOG_INFO.get('log_format',''))
	log_file=_LOG_INFO.get('log_file','/tmp/agent.log')
	if _DEBUG:
	    handler=logging.StreamHandler()
	else:
	    log_max_size=_LOG_INFO.get('log_max_size',100000)
	    log_backup=_LOG_INFO.get('log_backup',7)
	    log_folder=os.path.dirname(_LOG_INFO.get('log_file'))
	    if os.path.exists(log_folder):
		os.system('mkdir -p {0}'.format(log_folder))
	    handler=RotatingFileHandler(log_file,'a',log_max_size,log_backup)
	handler.setLevel(log_level)
	handler.setFormatter(log_format)
	Logger.addHandler(handler)
	if not self.logger:
	    self.logger=logging.getLogger('Agent')

    def init_logger(self):
	if not self.logger_ok:
	    self.logger_ok=True
	    self.set_logger()


    def daemonize(self):
	try:
	    pid=os.fork()
	    if pid > 0:
		sys.exit(0)
	except OSError,e:
	    self.logger.error(str(e))
	os.setsid()
	os.umask(0)
	try:
	    pid=os.fork()
	    if pid > 0:
		sys.exit(0)
	except OSError,e:
	    self.logger.error(str(e))
	for f in sys.stdout,sys.stderr:f.flush()
	si=file(self._std_in_file,'r')
	so=file(self._std_out_file,'a+')
	se=file(self._std_err_file,'a+',0)
	os.dup2(si.fileno(),sys.stdin.fileno())
	os.dup2(so.fileno(),sys.stdout.fileno())
	os.dup2(se.fileno(),sys.stderr.fileno())
	import atexit
	atexit.register(self.del_pidfile)
	setproctitle.setproctitle('agent')
	pid=str(os.getpid())
	self.logger.info(str(pid))
	if not os.path.exists(os.path.dirname(self._pid_file)):
	    os.makedirs(os.path.dirname(self._pid_file))
	with open(self._pid_file,'w') as f:
	    f.write(pid)

    def start(self):
	if not _DEBUG:
	    if os.path.exists(self._pid_file):
		self.logger.info('agent is running ?')
		sys.exit(1)
	    self.daemonize()
	    self.logger.info('start agent success')
	else:
	    self.logger.info('start agent in debug mode')
	worker=Worker(CALL_BACKS)
	worker._init_worker(QUEUE_INFO)
	worker.start_loop()
    def stop(self):
	if not os.path.exists(self._pid_file):
	    self.logger.error('the pid file is not exists! stop fail')
	    sys.exit(1)
	pid=None
	with open(self._pid_file) as f:
	    pid=int(f.readline())
	if pid:
	    os.system('kill -9 {0}'.format(str(pid)))
	    self.logger.info('Stop publisher process Success')
	try:
	    os.remove(self._pid_file)
	except Exception as e:
	    pass
    def del_pidfile(self):
	os.remove(self._pid_file)

    def restart(self):
	self.stop()
	time.sleep(1)
	self.start()
    def parse_input(self,opt):
	if opt == 'start':
	    self.start()
	elif opt == 'stop':
	    self.stop()
	elif opt == 'restart':
	    self.restart()
	else:
	    self.logger.error('bad params ,exsample: ./agent.py  start|stop|restart')
	    sys.exit(1)


class Worker(object):
    def __init__(self,callbacks=None,internal=CHECK_INTERNAL):
	self._callbacks=callbacks
	self.logger=logging.getLogger('Agent')
	self._internal=internal
	self.manager=None

    def _init_worker(self,kw):
	self.ip=kw.get('queue_ip',None)
	self.port=kw.get('queue_port',None)
	auth=kw.get('queue_auth',None)
	if not self.ip or not self.port:
	    self.logger.error('IP or Port is None !')
	    sys.exit(1)
	if not self.try_connect():
	    return False
	reload(multiprocessing.managers)
	multiprocessing.managers.BaseManager.register('get_result_queue')
	if auth:
	    self.manager=multiprocessing.managers.BaseManager(address=(self.ip,self.port),authkey=auth)
	else:
	    self.manager=multiprocessing.managers.BaseManager(address=(self.ip,self.port))
	try:
	    self.manager.connect()
	    return True
	except Exception,e:
	    self.logger.error(str(e))
	    self.manager=None
	    return False

    def try_connect(self):
	sk=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
 	sk.settimeout(5)
	try:
	    sk.connect((self.ip,self.port))
	    sk.close()
	    return True
   	except Exception ,e:
	    self.logger.error(str(e))
	    return False
    def start_loop(self):
	while True:
	    while True:
		if self._init_worker(QUEUE_INFO):
		    break
		self.logger.info('can not connect Publisher , try again after 3 sec')
		time.sleep(3)
	    callbacks=self._callbacks
	    threads=[]
	    queue=self.manager.get_result_queue()
	    if callbacks:
		for callback in  callbacks:
		    threads.append(threading.Thread(target=callback,args=(queue,self.logger)))
		for t in threads:
		    try:
		        t.start()
		    except Exception as e:
			self.logger(str(e))
			threads.remove(t)
		for t in threads:
		    t.join(timeout=600)
	    self.logger.info('Sleep %d s' %(self._internal))
            time.sleep(self._internal)
	    self.logger.info('Start run callbacks')
		    


if __name__ == '__main__':
    if len(sys.argv) == 2:
	daemon=Daemon()
	daemon.init_logger()
	daemon.parse_input(sys.argv[1])
    else:
	print 'bad params'















