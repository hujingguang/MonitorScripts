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
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr,formataddr
import smtplib
try:
    import simplejson
    json=simplejson
except ImportError,e:
    import json

_LOG_INFO={
"log_level":logging.INFO,
"log_format":'%(asctime)-15s %(levelname)s %(lineno)s %(message)s',
"log_file":'/var/log/master.log',
"log_max_size":100000000,
"log_backup":7,
}
_PID_FILE='/var/run/master.pid'
_DEBUG=False
_DEAD_LINE=90
QUEUE_INFO={
	'queue_ip':'4.10.3.204',
	'queue_port':4502,
	'queue_auth':'Ab'
	}
REGION_CONF={'hb1':u'青岛',
	'hb2':u'北京',
	'hb3':u'张家口',
	'hb5':u'呼和浩特',
	'hd1':u'杭州',
	'hd2':u'上海',
	'hn1':u'深圳',
	'hk':u'香港',
	}
EMAIL_LIST=['xx@xx.com']


'''
函数返回数据格式 {"hostname":"ld-hn1-1","type":"ping","result":1,"datetime":"2018-08-20 19:00:01","target":"120.19.11.23","info":"",'region':'',"standby":''}

状态记录字典
Status={
      'ping':
      {
      'hostname':
       {
      'target':{
      'send_problem_email':0,
      'send_recovery_email':0,
      'result':0,
       }
       }
       }
      }
'''
STATUS={'api':{},'ping':{}}
CHECK_INTERNAL=10




def main(queue,logger):
    global STATUS,_DEADLINE
    all_buff=dict()
    n=0
    begin_sec=int(time.time())
    while True:
	current_sec=int(time.time())
	if current_sec - begin_sec > _DEAD_LINE:
	    logger.info('超过最大处理时间,停止获取数据,开始处理监控数据')
	    break
	try:
	    recv=queue.get(timeout=6)
	    logger.info(recv)
	    if recv:
		try:
		    recv=json.loads(recv)
		    _type=recv['type'].lower()
		    if _type not in all_buff:
			all_buff[_type]=[]
		    if _type in STATUS:
			all_buff[_type].append(recv)
		    else:
			back=json.dumps(recv)
			queue.put(back)
		except Exception as e:
		    logger.error(str(e))
	except Exception as e:
	    logger.info('No data')
	    break
    dowith_all(all_buff,logger)
    #dowith_ping(ping_buff,logger)
    #dowith_api(api_buff,logger)
    #threads=[]
    #threads.append(threading.Thread(target=dowith_ping,args=(ping_buff,)))
    #threads.append(threading.Thread(target=dowith_api,args=(api_buff,)))
    #for t in threads:
    #    t.start()
    #for t in threads:
    #    t.join()

def dowith_all(data_dict,logger):
    global STATUS
    status=STATUS
    if not data_dict:
	return
    for t,data in data_dict.iteritems():
	for d in data:
	    hostname=d['hostname']
	    target=d['target']
	    if hostname not in status[t]:
		status[t][hostname]={}
	    if target not in status[t][hostname]:
		status[t][hostname][target]={'send_problem_email':0,'send_recovery_email':1,'result':0,'send_info':''}
	    result=d['result']
	    if result == 1:
		status[t][hostname][target]['result']=result
		info='Visit Area: %s (%s) Target:%s  Time: %s Info: %s' %(d['hostname'],d['region'],d['target'],d['datetime'],d['info'])
		status[t][hostname][target]['send_info']=info
	    elif result == 0:
		status[t][hostname][target]['result']=result
		info='Visit Area: %s (%s) Target:%s  Time: %s Info: Check  Ok ....' %(d['hostname'],d['region'],d['target'],d['datetime'])
		status[t][hostname][target]['send_info']=info
	alert_mess='PROBLEM: \n %s Check\n' %(t.upper())
	ok_mess='RECOVERY: \n %s Check\n'   %(t.upper())
	send_ok_flag,send_alert_flag =0,0
	for h,d in status[t].iteritems():
	    alert_info=''
	    ok_info=''
	    for t,r in d.iteritems():
		if r['result'] == 1 and r['send_problem_email'] == 0:
		    alert_info=alert_info+'\n\n'+r['send_info']
		    r['send_problem_email']=1
		    r['send_recovery_email']=0
		    send_alert_flag=1
		elif r['result'] == 0 and r['send_recovery_email'] == 0:
		    ok_info=ok_info+'\n\n'+r['send_info']
		    r['send_recovery_email']=1
		    r['send_problem_email']=0
		    send_ok_flag=1
	    alert_mess=alert_mess+alert_info
	    ok_mess=ok_mess+ok_info
	if send_ok_flag != 0:
	    send_result=0
	    while True:
		if send_result == 1:
		    break
		try:
	            logger.info(ok_mess)
	            send_email(ok_mess,"RECOVERY")
		    send_result=1
		except Exception as e:
		    logger.info(str(e))
		    logger.info('发送邮件失败,3s后重试')
		    time.sleep(3)
	if send_alert_flag != 0:
	    send_result=0
	    while True:
		if send_result == 1:
		    break
		try:
	            logger.info(alert_mess)
	            send_email(alert_mess,"PROBLEM")
		    send_result=1
		except Exception as e:
		    logger.info(str(e))
		    logger.info('发送邮件失败,3s后重试')
		    time.sleep(3)





def dowith_ping(data,logger):
    global STATUS
    status=STATUS
    if not data:
	return
    for d in data:
	hostname=d['hostname']
	target=d['target']
	if hostname not in status['ping']:
	    status['ping'][hostname]={}
	if target not in status['ping'][hostname]:
	    status['ping'][hostname][target]={'send_problem_email':0,'send_recovery_email':1,'result':0,'send_info':''}
	result=d['result']
	if result == 1:
	    status['ping'][hostname][target]['result']=result
	    info='Visit Area: %s (%s) Target:%s  Time: %s Info: %s' %(d['hostname'],d['region'],d['target'],d['datetime'],d['info'])
	    status['ping'][hostname][target]['send_info']=info
	elif result == 0:
	    status['ping'][hostname][target]['result']=result
	    info='Visit Area: %s (%s) Target:%s  Time: %s Info: Ping Ok ....' %(d['hostname'],d['region'],d['target'],d['datetime'])
	    status['ping'][hostname][target]['send_info']=info
    alert_mess='Problem Content: \nPing Check\n'
    ok_mess='Recovery Content: \nPing Check\n'
    send_ok_flag,send_alert_flag,have_alert_new,have_ok_new=0,0,0,0
    for h,d in status['ping'].iteritems():
	alert_info=''
	ok_info=''
	for t,r in d.iteritems():
	    if r['result'] == 1 and r['send_problem_email'] == 0:
		alert_info=alert_info+'\n\n'+r['send_info']
		r['send_problem_email']=1
		r['send_recovery_email']=0
		send_alert_flag=1
	    elif r['result'] == 0 and r['send_recovery_email'] == 0:
		ok_info=ok_info+'\n\n'+r['send_info']
		r['send_recovery_email']=1
		r['send_problem_email']=0
		send_ok_flag=1
	alert_mess=alert_mess+alert_info
	ok_mess=ok_mess+ok_info
    if send_ok_flag != 0:
	logger.info(ok_mess)
	send_email(ok_mess)
    if send_alert_flag != 0:
	logger.info(alert_mess)
	send_email(alert_mess)


def dowith_api(data,logger):
    global STATUS
    status=STATUS
    if not data:
	return
    for d in data:
	hostname=d['hostname']
	target=d['target']
	if hostname not in status['api']:
	    status['api'][hostname]={}
	if target not in status['api'][hostname]:
	    status['api'][hostname][target]={'send_problem_email':0,'send_recovery_email':1,'result':0,'send_info':''}
	result=d['result']
	if result == 1:
	    status['api'][hostname][target]['result']=result
	    info='Visit Area: %s (%s) Target:%s  Time: %s Info: %s' %(d['hostname'],d['region'],d['target'],d['datetime'],d['info'])
	    status['api'][hostname][target]['send_info']=info
	elif result == 0:
	    status['api'][hostname][target]['result']=result
	    info='Visit Area: %s (%s) Target:%s  Time: %s Info: Check API  Ok ....' %(d['hostname'],d['region'],d['target'],d['datetime'])
	    status['api'][hostname][target]['send_info']=info
    alert_mess='Problem Content: \nAPI Check\n'
    ok_mess='Recovery Content: \nAPI Check\n'
    send_ok_flag,send_alert_flag,have_alert_new,have_ok_new=0,0,0,0
    for h,d in status['api'].iteritems():
	alert_info=''
	ok_info=''
	for t,r in d.iteritems():
	    if r['result'] == 1 and r['send_problem_email'] == 0:
		alert_info=alert_info+'\n\n'+r['send_info']
		r['send_problem_email']=1
		r['send_recovery_email']=0
		send_alert_flag=1
	    elif r['result'] == 0 and r['send_recovery_email'] == 0:
		ok_info=ok_info+'\n\n'+r['send_info']
		r['send_recovery_email']=1
		r['send_problem_email']=0
		send_ok_flag=1
	alert_mess=alert_mess+alert_info
	ok_mess=ok_mess+ok_info
    if send_ok_flag != 0:
	logger.info(ok_mess)
	send_email(ok_mess,'恢复')
    if send_alert_flag != 0:
	logger.info(alert_mess)
	send_email(alert_mess,'告警')




def send_email(mess,subject):
    from_addr='xx@xx.com'
    password='xxxx'
    to_addrs=','.join(EMAIL_LIST)
    smtp_server='smtp.exmail.qq.com'
    msg=MIMEText(mess,'plain','utf-8')
    msg['From']=formataddr((Header('API和Ping接口检测'+subject,'utf-8').encode(),from_addr))
    msg['To']=formataddr((Header(u'System Admin','utf-8').encode(),to_addrs))
    msg['Subject']=Header('Agent Report','utf-8').encode()
    server=smtplib.SMTP_SSL(smtp_server,465)
    server.set_debuglevel(0)
    server.login(from_addr,password)
    server.sendmail(from_addr,EMAIL_LIST,msg.as_string())
    server.quit()


CALL_BACKS=[main]


class Daemon(object):
    '''
    守护进程类,初始化日志和启动,关闭
    '''
    def __init__(self):
	self._pid_file=_PID_FILE
	self._std_in_file='/dev/null'
	self._std_out_file='/dev/null'
	self._std_err_file=_LOG_INFO.get('log_file','/var/log/master.log')
	self.logger_ok=False
	self.logger=None

    def set_logger(self):
	global _LOG_INFO,_DEBUG
	logging.basicConfig(level=logging.DEBUG,filename='/dev/null')
	Logger=logging.getLogger('Master')
	log_level=_LOG_INFO.get('log_level',logging.INFO)
	log_format=logging.Formatter(_LOG_INFO.get('log_format',''))
	log_file=_LOG_INFO.get('log_file','/tmp/master.log')
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
	    self.logger=logging.getLogger('Master')

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
	setproctitle.setproctitle('master')
	pid=str(os.getpid())
	self.logger.info(str(pid))
	if not os.path.exists(os.path.dirname(self._pid_file)):
	    os.makedirs(os.path.dirname(self._pid_file))
	with open(self._pid_file,'w') as f:
	    f.write(pid)

    def start(self):
	if not _DEBUG:
	    if os.path.exists(self._pid_file):
		self.logger.info('master is running ?')
		sys.exit(1)
	    self.daemonize()
	    self.logger.info('start master success')
	else:
	    self.logger.info('start master in debug mode')
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
	    self.logger.info('Stop master process Success')
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
	    self.logger.error('bad params ,exsample: ./master.py  start|stop|restart')
	    sys.exit(1)


class Worker(object):
    def __init__(self,callbacks=None,internal=CHECK_INTERNAL):
	self._callbacks=callbacks
	self.logger=logging.getLogger('Master')
	self._internal=internal
	self.manager=None
	self.status=STATUS

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
		self.logger.info('can not connect Manager , try again after 3 sec')
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
	    self.logger.info('Sleep 10s')
	    time.sleep(self._internal)




if __name__ == '__main__':
    if len(sys.argv) == 2:
	daemon=Daemon()
	daemon.init_logger()
	daemon.parse_input(sys.argv[1])
    else:
	print 'bad params'















