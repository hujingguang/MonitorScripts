#!/usr/bin/python
# -*- coding=UTF-8 -*-

#说明： 该脚本为公共队列监听管理器
from Queue import Queue
import random
import logging
import os
import time
from multiprocessing.managers import BaseManager
from logging.handlers import RotatingFileHandler
from signal import SIGTERM
import setproctitle
import sys
import threading
from datetime import datetime
from multiprocessing import Process,Value
from imp import reload

__author__='Hoover'


LOG_INFO={
	'log_level':logging.INFO,
	#'log_format':'%(asctime)-15s %(levelname)s %(funcName)s %(lineno)s %(message)s ',
	'log_format':'%(asctime)-15s %(levelname)s %(lineno)s %(message)s ',
	'log_file':'/tmp/publisher/manager.log',
	'log_max_size':1000000000,
	'log_backup':15,
	}
QUEUE_INFO={
	'queue_ip':'0.0.0.0',
	'queue_port':4502,
	'queue_auth':'AbAbC'
	}
PID_FILE='/tmp/publisher/manager.pid'
QUERY_TIME=60
DEBUG=False
Result_Queue=Queue()
BaseManager.register('get_result_queue',callable=lambda:Result_Queue)

def init_logger():
    global DEBUG,LOG_INFO
    logging.basicConfig(level=logging.DEBUG,filename='/dev/null')
    LOGGER=logging.getLogger('Queue')
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
    logger=logging.getLogger('Queue')
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
	#import atexit
	#atexit.register(self.del_pid)
	setproctitle.setproctitle('queue')
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
	    #print 'Start Publisher Success'
	    self.daemonize()
	publisher=Publisher()
	publisher.init_publisher()
	publisher.loop()
	

    def stop(self):
	if not os.path.exists(self.pid_file):
	    self.logger.warning('Stop failed. the pid_file do not exist !')
	    sys.exit(1)
	with open(self.pid_file,'r') as f:
	    pid=int(f.readline())
	    ppid=pid+1
	#try:
	#    while True:
	#	os.kill(pid,SIGTERM)
	#	time.sleep(0.1)
        #except Exception,e:
	#    e=str(e) 
	#    if e.find('No such process'):
	#	self.logger.info('Stop publisher process Success')
	#    else:
	#	self.logger.error(e)
	##os.remove(self.pid_file)
	#cmd=r''' netstat -ntlp|grep queue|awk '{print $NF}'|awk -F'/' '{print $1}' > /tmp/.queue.pid'''
	#os.system(cmd)
	[os.system('kill -9 {0}'.format(p)) for p in [str(pid),str(ppid)]]
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

class Publisher(object):
    def __init__(self):
        self.logger=logging.getLogger('Queue')

    def init_publisher(self):
	setproctitle.setproctitle('queue')
	ip=QUEUE_INFO.get('queue_ip','0.0.0.0')
	port=QUEUE_INFO.get('queue_port',5000)
	auth=QUEUE_INFO.get('queue_auth',None)
	if auth:
	    self.manager=BaseManager(address=(ip,port),authkey=auth)
	else:
	    self.manager=BaseManager(address=(ip,port))
	try:
	    self.manager.start()
	    print dir(self.manager)
	    self.logger.info('Start Queue Listen')
	except Exception ,e:
	    self.logger.error(str(e))
	    sys.exit(1)
    def loop(self):
	while True:
	    time.sleep(30)

  






if __name__=='__main__':
    if len(sys.argv) <2:
	print 'usage: {} start|stop|restart'.format(sys.argv[0])
	sys.exit(1)
    init_logger()
    daemon=Daemonize()
    daemon.parse(sys.argv[1])
    

	
