#!/usr/bin/python
# -*- coding=UTF-8 -*-

#说明： 该脚本用来处理淘宝优惠券过期将商品及时下架，主要有两个线程，线程一从数据库查询待处理的上架商品
#       放入公共队列给分布于客户端的worker程序查询是否过期。线程二对返回的数据进行处理
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
import MySQLdb
import threading
from datetime import datetime
__author__='Hoover'

LOG_INFO={
	'log_level':logging.INFO,
	#'log_format':'%(asctime)-15s %(levelname)s %(funcName)s %(lineno)s %(message)s ',
	'log_format':'%(asctime)-15s %(levelname)s %(lineno)s %(message)s ',
	'log_file':'/tmp/publisher/publisher.log',
	'log_max_size':1000000000,
	'log_backup':15,
	}
DB_INFO={
	'db_name':'gddb',
	'db_user':'publisher',
	'db_password':'publisher@mth',
	'db_host':'10.45.23.148',
	'db_port':3306,
	}
QUEUE_INFO={
	'queue_ip':'10.117.74.247',
	'queue_port':50000,
	'queue_auth':'AbAbC'
	}
PID_FILE='/tmp/publisher/publisher.pid'
QUERY_TIME=60
DEBUG=False

def init_logger():
    global DEBUG,LOG_INFO
    logging.basicConfig(level=logging.DEBUG,filename='/dev/null')
    LOGGER=logging.getLogger('Publisher')
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
    logger=logging.getLogger('Publisher')
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
	setproctitle.setproctitle('Publisher')
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
	    print 'Start Publisher Success'
	    self.daemonize()
	publisher=Publisher()
	self.publisher=publisher
	publisher.init_publisher()
	publisher.main()
	

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
	print 'Stop Publisher Success'
	cmd=r''' netstat -ntlp|grep Publisher|awk '{print $NF}'|awk -F'/' '{print $1}' > /tmp/.queue.pid'''
	os.system(cmd)
	with open('/tmp/.queue.pid','r') as f:
	    os.system('kill -9 %s ' %(f.readline()))

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







class DBConnection(object):
    def __init__(self,kw):
	self.db_name=kw.get('db_name',None)
	self.db_host=kw.get('db_host','127.0.0.1')
	self.db_port=kw.get('db_port',3306)
	self.db_user=kw.get('db_user',None)
	self.db_password=kw.get('db_password',None)
	self.logger=logging.getLogger('Publisher')
	self.conn=None

    def connect(self):
	try:
	    self.conn=MySQLdb.connect(user=self.db_user,passwd=self.db_password,host=self.db_host,db=self.db_name,charset='utf8',port=self.db_port)
	except Exception,e:
	    self.logger.error(str(e))
	    self.conn=None

    def cursor(self):
	if self.conn:
	    return self.conn.cursor()
	return None

    def is_connect(self):
	return self.conn is None

    def commit(self):
	if self.conn:
	    self.conn.commit()

    def close(self):
	if self.conn:
	    conn=self.conn
	    self.conn=None
	    try:
		conn.close()
	    except Exception,e:
		self.logger.error(str(e))
   


class Publisher(object):
    def __init__(self):
        self._buffer_dict=dict()
        self._diff_dict=dict()
        self._data_queue=Queue()
        self._ret_queue=Queue()
	self.db=DBConnection(DB_INFO)
	self.manager=None
	self.total=0
	self.left=0
        self.logger=logging.getLogger('Publisher')


    def init_publisher(self):
	BaseManager.register('get_query_queue',lambda:self._data_queue)
	BaseManager.register('get_ret_queue',lambda:self._ret_queue)
	ip=QUEUE_INFO.get('queue_ip','0.0.0.0')
	port=QUEUE_INFO.get('queue_port',5000)
	auth=QUEUE_INFO.get('queue_auth',None)
	if auth:
	    self.manager=BaseManager(address=(ip,port),authkey=auth)
	else:
	    self.manager=BaseManager(address=(ip,port))
	try:
	    self.manager.start()
	    self.logger.info(str(os.getpid()))
	    self.logger.info('Start Queue Listen')
	except Exception ,e:
	    self.logger.error(str(e))
	    sys.exit(1)

    def close_manager(self):
	if self.manager:
	    self.manager.shutdown()

    def is_manual_off_shelf(self,goods_id):
	if self.db.is_connect():
	    self.db.connect()
	if not goods_id:
	    return True
	sql='select status from ps_goods where goods_id="%s" and status="off_shelf"' %(goods_id)
	cursor=self.db.cursor()
	if cursor:
	    try:
		result=cursor.execute(sql)
		if result == 1:
		    return True
	    except Exception,e:
		self.logger.error(str(e))
		self.logger.error('connect failed on is_manual_off_shelf')
	    self.db.close()
        return False



    def fill_buffer_dict(self):
	self._diff_dict=dict()
	if self.db.is_connect():
	    self.db.connect()
	cursor=self.db.cursor()
	sql='select goods_id,goods_code,voucher_link from ps_goods where voucher_link != "" and status="on_shelf" ;'
	#sql='select goods_id,goods_code,voucher_link from ps_goods where voucher_link != "";'
	if cursor:
	    try:
		cursor.execute(sql)
		self._diff_dict={}
		for data in cursor.fetchall():
		    if data[0] not in self._buffer_dict:
			self._buffer_dict[data[0]]=[data[0],data[1],data[2]]
			self._diff_dict[data[0]]=[data[0],data[1],data[2]]
		diff=len(self._diff_dict)
		self.total=self.total+diff
		self.logger.info('Fill Counts: %d, Total Counts : %d ' %(diff,self.total))
	    except Exception,e:
		self.logger.error(str(e))
	    self.db.close()
	else:
	    self.logger.error('can not connect database ! query data fill in buffer failed')

    def sync_data(self):
	data_queue=self.manager.get_query_queue()
	ret_queue=self.manager.get_ret_queue()
	for k,v in self._diff_dict.iteritems():
	    data_queue.put(v)
	    

    def publish(self):
	self.logger.info('start Publish Thread')
	while True:
	    self.fill_buffer_dict()
	    self.sync_data()
	    time.sleep(QUERY_TIME)
    

    def change_status(self,goods_id,goods_code):
	if self.db.is_connect():
	    self.db.connect()
	cursor=self.db.cursor()
	if not cursor:
	    self.logger.error('can not connect to database , update failed')
	    return
	modify_date=datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
	offline_date=datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
	sql='''update ps_goods set status='off_shelf',offline_date='%s',modified_date='%s' where goods_id='%s' and goods_code='%s';''' %(modify_date,offline_date,goods_id,goods_code)
	try:
	    self.logger.info('UPDATE SQL: '+sql)
	    result=cursor.execute(sql)
	    self.db.commit()
	    self.logger.info('Update Success.   goods_id:  %s   goods_code:  %s   Update Result: %d' %(goods_id,goods_code,result))
	except Exception,e:
	    self.logger.error(str(e))
	    self.logger.info('Update Failed. goods_id: %s  goods_code: %s ' %(goods_id,goods_code))
	try:
	    cursor.close()
	except Exception,e:
	    self.logger.error(str(e))



    def update(self):
	ret_queue=self.manager.get_ret_queue()
	query_queue=self.manager.get_query_queue()
	self.logger.info('start Update Thread')
	while True:
	    num=0
	    try:
		recv_num=0
		while True:
		    return_data=ret_queue.get(timeout=3)
		    recv_num=recv_num+1
		    #self.logger.info(str(return_data))
		    if len(return_data)<4:
			self.logger.info('Invalied Return Data In Queue,Skip It')
			continue
		    goods_id=return_data[0]
		    goods_code=return_data[1]
		    status=return_data[3]
		    if self.is_manual_off_shelf(goods_id):
			self.logger.info('goods_id: %s  is manual off shelf . skip it')
			num=num+1
			continue
		    if status == 'off':
			self.change_status(goods_id,goods_code)
			num=num+1
		    else:
			remove_value=return_data[3]
			return_data.remove(remove_value)
			#query_queue=self.manager.get_query_queue()
			query_queue.put(return_data)
	    except Exception,e:
		self.total=self.total-num
		self.logger.info(str(e))
		self.logger.info('Total %d Line Updated, Left Line:  %d' %(num,self.total))
		self.logger.info('Receive %d Line.in Return Queue.  Sleep 10 sec' %(recv_num))
	    time.sleep(10) 
     

    def main(self):
	self.init_publisher()
	func_list=[self.publish,self.update]
	thread_list=[threading.Thread(target=x) for x in func_list]
	for t in thread_list:
	    t.setDaemon(True)
	    t.start()
	for t in thread_list:
	    t.join()



if __name__=='__main__':
    if len(sys.argv) <2:
	print 'usage: {} start|stop|restart'.format(sys.argv[0])
	sys.exit(1)
    init_logger()
    daemon=Daemonize()
    daemon.parse(sys.argv[1])
    

	
