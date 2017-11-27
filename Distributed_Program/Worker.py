#!/usr/bin/python
# -*- coding=UTF-8 -*-

#说明：  该脚本分布于客户端，用来查询淘宝优惠券是否失效，并返回数据给Publisher进程处理.

from Queue import Queue
import random
import logging
import os
import time
#from multiprocessing.managers import BaseManager
import multiprocessing.managers 
from logging.handlers import RotatingFileHandler
from signal import SIGTERM
import sys
import requests
import socket
import json
from imp import reload
__author__='Hoover'


LOG_INFO={
	'log_level':logging.INFO,
	#'log_format':'%(asctime)-15s %(levelname)s %(funcName)s %(lineno)s %(message)s ',
	'log_format':'%(asctime)-15s %(levelname)s %(lineno)s %(message)s ',
	'log_file':'/tmp/worker/worker.log',
	'log_max_size':1000000000,
	'log_backup':15,
	}

QUEUE_INFO={
	'queue_ip':'10.117.74.247',
	'queue_port':50000,
	'queue_auth':'AbAbC'
	}

PID_FILE='/tmp/worker/worker.pid'
DEBUG=False
LINE_PER_SEC=1

def init_logger():
    global DEBUG,LOG_INFO
    logging.basicConfig(level=logging.DEBUG,filename='/dev/null')
    LOGGER=logging.getLogger('Worker')
    log_format=logging.Formatter(LOG_INFO.get('log_format',''))
    log_file=LOG_INFO.get('log_file')
    log_level=LOG_INFO.get('log_level')
    if DEBUG:
	stream_handler=logging.StreamHandler()
	stream_handler.setLevel(log_level)
	stream_handler.setFormatter(log_format)
	LOGGER.addHandler(stream_handler)
    else:
	log_folder=os.path.dirname(LOG_INFO.get('log_file'))
	if not os.path.exists(log_folder):
	    os.makedirs(log_folder)
	log_max_size=LOG_INFO.get('log_max_size')
	log_backup=LOG_INFO.get('log_backup')
	rotate_handler=RotatingFileHandler(log_file,'a',log_max_size,log_backup)
	rotate_handler.setFormatter(log_format)
	rotate_handler.setLevel(log_level)
	LOGGER.addHandler(rotate_handler)


class Daemonize(object):
    std_in_file='/dev/null'
    std_out_file='/dev/null'
    std_err_file=LOG_INFO.get('log_file')
    logger=logging.getLogger('Worker')
    pid_file=PID_FILE
    def daemonize(self):
	try:
	    pid=os.fork()
	    if pid > 0:
		sys.exit(0)
	except OSError,e:
	    logger.error(str(e))
	os.setsid()
	os.umask(0)
	try:
	    pid=os.fork()
	    if pid > 0:
		sys.exit(0)
	except OSError, e:
	    logger.error(str(e))
	for f in sys.stdout,sys.stderr:f.flush()
	si=file(self.std_in_file,'r')
	so=file(self.std_out_file,'a+')
	se=file(self.std_err_file,'a+',0)
        os.dup2(si.fileno(),sys.stdin.fileno())
        os.dup2(so.fileno(),sys.stdout.fileno())
        os.dup2(se.fileno(),sys.stderr.fileno())
	os.umask(022)
	import atexit
	atexit.register(self.del_pid)
	pid=str(os.getpid())
	if not os.path.exists(os.path.dirname(self.pid_file)):
	    os.makedirs(os.path.dirname(self.pid_file))
	with open(self.pid_file,'w') as f:
	    f.write(pid)

    def start(self):
	if not DEBUG:
	    if os.path.exists(self.pid_file):
	        self.logger.error('the pid file exists. is running ?')
		sys.exit(1)
	    self.daemonize()
	self.logger.info('Start Worker Success')
	worker=Worker()
	worker.return_data()

    def stop(self):
	if not os.path.exists(self.pid_file):
	    self.logger.warning('Stop failed. the pid_file do not exist !')
	    sys.exit(1)
	with open(self.pid_file,'r') as f:
	    pid=int(f.readline())
	try:
	    while True:
		os.kill(pid,SIGTERM)
		time.sleep(0.1)
        except Exception,e:
	    e=str(e) 
	    if e.find('No such process'):
		self.logger.info('Stop publisher process Success')
	    else:
		self.logger.error(e)
	os.remove(self.pid_file)

    def restart(self):
	self.stop()
	time.sleep(1)
	self.start()

    def parse(self,opt):
	if opt == 'start':
	   self.start()
        elif opt == 'stop':
	   self.stop()
        elif opt == 'restart':
	   self.restart()
        else:
	   self.logger.error('invalid param, exsample:  start|stop|restart')
	   sys.exit(1)

    def del_pid(self):
	os.remove(self.pid_file)



class Worker(object):
    def __init__(self):
	self.manager=None
	self.logger=logging.getLogger('Worker')

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
	multiprocessing.managers.BaseManager.register('get_query_queue')
	multiprocessing.managers.BaseManager.register('get_ret_queue')
	if auth:
	    self.manager=multiprocessing.managers.BaseManager(address=(self.ip,self.port),authkey=auth)
	else:
	    self.manager=multiprocessing.managers.BaseManager(address=(self.ip,self.port))
	try:
	    self.manager.connect()
	    return True
	except Exception,e:
	    self.logger.error(str(e))
	    return False


    def query_from_api(self,data):
	goods_code=data[1]
	voucher_link=data[2]
	activity_id=None
	url=None
	for s in voucher_link.split('&'):
	    if s.startswith('activity_id'):
		activity_id=s.split('=')[1]
		break
	    if s.startswith('activityId'):
		activity_id=s.split('=')[1]
		break
	if activity_id and voucher_link:
	    url='http://uland.taobao.com/cp/coupon?activityId=%s&pid=mm_0_0_0&src=tkzs_1&itemId=%s' %(activity_id,goods_code)
	else:
	    url=None
	try:
	    response=json.loads(requests.get(url).text)
	    startTime=response['result']['effectiveStartTime'] 
	    endTime=response['result']['effectiveEndTime'] 
	    if not startTime and not endTime:
		data.append('off')
	    else:
		data.append('on')
	    self.logger.info(str(data))
	except Exception,e:
	    self.logger.error(str(e))
	    self.logger.warning('Query Goods Failed : '+str(data))
	    self.logger.warning('URL:  '+url)
	    return None
	return data



    def get_data(self):
	data_list=list()
	if self.manager:
	    query_queue=self.manager.get_query_queue()
	    try:
		for i in range(LINE_PER_SEC):
		    ret_list=query_queue.get(timeout=5)
		    ret_list=self.query_from_api(ret_list)
		    data_list.append(ret_list)
	    except Exception,e:
		self.logger.info('No Data in Queue ')
	return data_list



    def return_data(self):
	while True:
	    while True:
		if self._init_worker(QUEUE_INFO):
		    break
		self.logger.info('can not connect Publisher , try again after 3 sec')
		time.sleep(3)
	    try:
		ret_queue=self.manager.get_ret_queue()
		while True:
		    ret_data_list=self.get_data()
		    for data in ret_data_list:
			ret_queue.put(data)
		    time.sleep(4)
	    except Exception,e:
		self.logger.error(str(e))
	    self.manager=None
	    time.sleep(5)



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



if __name__=='__main__':
    init_logger()
    if len(sys.argv) <2:
	print 'usage: %s start|stop|restart' %(sys.argv[0])
	sys.exit(1)
    daemon=Daemonize()
    daemon.parse(sys.argv[1])
