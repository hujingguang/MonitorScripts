#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__='hoover'

from aliyunsdkess.request.v20140828.CreateScalingGroupRequest import CreateScalingGroupRequest
from aliyunsdkess.request.v20140828.CreateScalingRuleRequest import CreateScalingRuleRequest
from aliyunsdkess.request.v20140828.ExecuteScalingRuleRequest import ExecuteScalingRuleRequest
from aliyunsdkess.request.v20140828.CreateScalingConfigurationRequest import CreateScalingConfigurationRequest
from aliyunsdkess.request.v20140828.DeleteScalingGroupRequest import DeleteScalingGroupRequest
from aliyunsdkess.request.v20140828.DescribeScalingGroupsRequest import DescribeScalingGroupsRequest
from aliyunsdkess.request.v20140828.DescribeScalingActivitiesRequest import DescribeScalingActivitiesRequest
from aliyunsdkess.request.v20140828.EnableScalingGroupRequest import EnableScalingGroupRequest
from aliyunsdkess.request.v20140828.ModifyScalingGroupRequest import ModifyScalingGroupRequest
from aliyunsdkess.request.v20140828.ExecuteScalingRuleRequest import ExecuteScalingRuleRequest
from aliyunsdkess.request.v20140828.EnableScalingGroupRequest import EnableScalingGroupRequest
from aliyunsdkecs.request.v20140526.DescribeImagesRequest import DescribeImagesRequest
from aliyunsdkslb.request.v20140515.DescribeLoadBalancersRequest import DescribeLoadBalancersRequest
from aliyunsdkcore.client import AcsClient
import logging
import sys
import os
import ConfigParser
import json
import optparse
import time

__DEBUG=True
__CONF_FILE_PATH='/root/deploy/region.conf'
__LOG_FILE_PATH='/tmp/aliyun_ess.log'
__SECURITY_GROUP_ID='you security group id'
__SK='your aliyun Secret key'
__KEY='your key'
INSTANCE_TYPE={
	'ecs.m1.medium':'4core X 16 GB',
	'ecs.s3.large':'4core X 16 GB',
	'ecs.s2.xlarge':'2core X 8 GB',
	'ecs.s2.2xlarge':'2core X 16 GB',
	}
if __DEBUG:
    __LEVEL=logging.DEBUG
    __LOG_FILE_PATH=None
else:
    __LEVEL=logging.INFO

logging.basicConfig(filename=__LOG_FILE_PATH,format='%(asctime)s %(levelname)s : %(message)s ',level=__LEVEL)

'''
this script  be used to dynamic increase or decrease aliyun ECS and add to or delete from aliyun SLB
'''
__Client=None

def __get_client(region):
    global __Client
    if not __Client:
	__Client=AcsClient(__SK,__KEY,region)
    return __Client



def __get_img_id(image_name,region):
    request=DescribeImagesRequest()
    request.set_accept_format('json')
    result=do_action(request,region)
    for k,v in result['Images'].iteritems():
	for i in v:
	    if image_name == i['ImageName']:
		return i['ImageId']
    return None
    
def do_action(request,region):
    client=__get_client(region)
    request.set_accept_format('json')
    try:
	result=json.loads(client.do_action_with_exception(request))
    except Exception as e:
	logging.error('Bad Region Name')
	sys.exit(1)
    if 'Code' in result:
	logging.error('%s' %result['Message'])
	sys.exit(1)
    return result

def __get_scaling_group_id(group_name,region):
    group_id=None
    request=DescribeScalingGroupsRequest()
    request.set_RegionId(region)
    result=do_action(request,region)
    for scaling_group in result['ScalingGroups']['ScalingGroup']:
	if group_name == scaling_group['ScalingGroupName']:
	   group_id=scaling_group['ScalingGroupId']
    return group_id

def __get_slb_id(slb_name,region):
    request=DescribeLoadBalancersRequest()
    request.set_RegionId(region)
    result=do_action(request,region)
    __slb_id=None
    for slb in result['LoadBalancers']['LoadBalancer']:
	if slb_name == slb['LoadBalancerName']:
	    __slb_id=slb['LoadBalancerId']
    return __slb_id


def create_scaling_group(group_name,region,maxsize,slb_id,minsize=0,default_cool_down=300,removal_policy=None):
    if maxsize <=minsize or maxsize >100:
	logging.error('invalid size : %d' %maxsize)
    else:
	request=CreateScalingGroupRequest()
	request.set_MinSize(minsize)
	request.set_MaxSize(maxsize)
	slb_id='["'+slb_id+'"]'
	request.set_LoadBalancerId(slb_id)
	request.set_ScalingGroupName(group_name)
	request.set_DefaultCooldown(default_cool_down)
	do_action(request,region)
	time.sleep(1)
	return True
    return False
 

	

def __enable_scaling_group(group_id,region):
    request=EnableScalingGroupRequest()
    request.set_ScalingGroupId(group_id)
    do_action(request,region)

def create_scaling_configure(group_id,img_id,region,instance_type,security_id,maxband_in=1,maxband_out=1):
    request=CreateScalingConfigurationRequest()
    request.set_ScalingGroupId(group_id)
    request.set_ImageId(img_id)
    request.set_InstanceType(instance_type)
    request.set_SecurityGroupId(security_id)
    request.set_InternetMaxBandwidthIn(maxband_in)
    request.set_InternetMaxBandwidthOut(maxband_out)
    result=do_action(request,region)
    time.sleep(1)
    return result['ScalingConfigurationId']


def __active_scaling_configure(group_id,conf_id,region):
    request=ModifyScalingGroupRequest()
    request.set_ScalingGroupId(group_id)
    request.set_ActiveScalingConfigurationId(conf_id)
    do_action(request,region)

def __enable_scaling_group(group_id,conf_id,region):
    __active_scaling_configure(group_id,conf_id,region)
    request=EnableScalingGroupRequest()
    request.set_ScalingGroupId(group_id)
    do_action(request,region)
    time.sleep(1)

def create_scaling_rule(group_id,region,adjustment_value,adjustment_type='QuantityChangeInCapacity'):
    request=CreateScalingRuleRequest()
    request.set_ScalingGroupId(group_id)
    request.set_AdjustmentType(adjustment_type)
    request.set_AdjustmentValue(adjustment_value)
    result=do_action(request,region)
    time.sleep(1)
    return result['ScalingRuleAri']

def __active_scaling_rule(rule_ari,region):
    request=ExecuteScalingRuleRequest()
    request.set_ScalingRuleAri(rule_ari)
    result=do_action(request,region)
    time.sleep(1)
    return  result['ScalingActivityId']


def __query_scaling_activity_status(group_id,activity_id,region,status):
    request=DescribeScalingActivitiesRequest()
    request.set_ScalingGroupId(group_id)
    request.set_ScalingActivityId1(activity_id)
    request.set_StatusCode(status)
    result=do_action(request,region)
    if 'ScalingActivities' in result:
	return True
    return False

def delete_scaling_group(group_id,region,force_delete=True):
    request=DeleteScalingGroupRequest()
    request.set_ScalingGroupId(group_id)
    if not force_delete:
	pass
    else:
	request.set_ForceDelete('true')
    do_action(request,region)

def parser_opt():
    parser=optparse.OptionParser(usage=u'''
	    此脚本用来对服务器进行自动扩容和删除

	    扩容服务器可选规格如下：
	    ecs.s2.xlarge :  2 核  8 GB
	    ecs.s2.2xlarge :  2 核  16 GB
	    ecs.s3.large :  4 核  8 GB
	    ecs.m1.medium :  4 核  16 GB

	    使用范例:  %s  -i appapi_node4_copy -t ecs.s2.xlarge -g scaling_app -n 10 -s appportal_external -r cn-hangzhou -o add
	    
	    表示 在cn-hangzhou (华东1地区),创建名为 scaling_app 的伸缩组
	    使用镜像名为: appapi_node4_copy
	    服务器规格为 ecs.s2.xlarge (4核8GB)
	    伸缩组数量为10台并加入到负载均衡名为 appportal_external 中。

	    %s -o del -g scaling_app -r cn-hangzhou

	    删除伸缩组名为 scaling_app 的伸缩组

	    ''' %(sys.argv[0],sys.argv[0]))
    parser.add_option('-i','--image-name',action='store',type='string',help='image name',dest='image_name')
    parser.add_option('-t','--type',action='store',type='string',help='ECS instance type',dest='instance_type',)
    parser.add_option('-g','--group-name',action='store',type='string',help='scaling group name',dest='group_name')
    parser.add_option('-n','--number',action='store',type='int',help='adding ECS instance number',dest='num')
    parser.add_option('-s','--slb-name',action='store',type='string',help='SLB name',dest='slb_name')
    parser.add_option('-r','--region-id',action='store',type='string',help='region id',dest='region')
    parser.add_option('-o','--option',action='store',type='string',help='add or del scaling group. available value is : add|del',dest='option')
    opt,args=parser.parse_args()
    if opt.option == 'del':
	if opt.region is None or opt.group_name is None:
	    logging.error('please privide all args !')
	    sys.exit(1)
	group_id=__get_scaling_group_id(opt.group_name,opt.region)
	if not group_id:
	    logging.error('invalid group name !')
	    sys.exit(1)
	elif opt.region is None:
	    logging.error('region must be privided')
	else:
	    stop_scaling(group_id,opt.region)
    elif opt.option == 'add':
	if opt.image_name is None \
		or opt.group_name is None \
		or opt.num is None \
		or opt.slb_name is None \
		or opt.region is None:
		logging.error('please privide all args !')
		sys.exit(1)
	image_id=__get_img_id(opt.image_name,opt.region)
	slb_id=__get_slb_id(opt.slb_name,opt.region)
	if not image_id:
	    logging.error(u'invalid image name ! ')
	elif opt.instance_type not in INSTANCE_TYPE:
	    logging.error(u'invalid ECS instance type!')
	elif not slb_id:
	    logging.error(u'invalid SLB Name !')
	elif not isinstance(opt.num,int) or opt.num < 1 or opt.num >100:
            logging.error('invalid -n option')
	elif opt.region is None:
	    logging.error('-r option is must be privided')
	else:
	    start_scaling(opt.group_name,opt.region,opt.num,slb_id,image_id,opt.instance_type,__SECURITY_GROUP_ID)
    else:
	parser.print_help()

def start_scaling(group_name,region,num,slb_id,image_id,instance_type,security_id):
    if create_scaling_group(group_name,region,num,slb_id):
	group_id=__get_scaling_group_id(group_name,region)
	conf_id=create_scaling_configure(group_id,image_id,region,instance_type,security_id)
	logging.info(u'创建伸缩组成功')
	rule_ari=create_scaling_rule(group_id,region,num)
	__enable_scaling_group(group_id,conf_id,region)
	logging.info(u'开始激活伸缩组')
	active_id=__active_scaling_rule(rule_ari,region)
	flag=True
	while True:
	    status=['Successful','Failed','InProgress','Rejected']
	    if __query_scaling_activity_status(group_id,active_id,region,status[0]):
		logging.info('Ok  Scaling Success ')
		break
	    elif __query_scaling_activity_status(group_id,active_id,region,status[2]):
		if flag:
		    flag=False
		    logging.info(u'正在执行伸缩活动,请稍后....')
		time.sleep(5)
	    elif __query_scaling_activity_status(group_id,active_id,region,status[1]):
		logging.error(u'伸缩活动失败  !')
		break
	    elif __query_scaling_activity_status(group_id,active_id,region,status[3]):
		logging.error(u' 伸缩活动被拒绝!')
		break
	    else:
		time.sleep(5)
    

def stop_scaling(group_id,region):
    logging.info(u'开始删除伸缩组')
    delete_scaling_group(group_id,region)
    logging.info(u'删除成功')

def main():
    parser_opt()

if __name__=='__main__':
    main()
