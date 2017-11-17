#!/usr/bin/python
import sys
from aliyunsdkcore import client
from aliyunsdkslb.request.v20140515.RemoveBackendServersRequest import 	RemoveBackendServersRequest 
from aliyunsdkslb.request.v20140515.AddBackendServersRequest import AddBackendServersRequest
import optparse
import json




class SlbAction(object):
    lb_info={'mps_internal_id':'lbbp1th9get31w171np0',
	    'mps_external_id':'15293ce9059-cn-hangzhou-dg-a01',
	    'mps_node2':'i-238skj4un',
	    'mps_node1':'i-23z6ackwg',
	    'appapi_internal_id':'lbbp1lh8u8jm0m19iv7q',
	    'appapi_external_id':'lbbp10i6y9245k6vk9t9',
	    'appapi_node1':'i-23632gp7l',
	    'appapi_node2':'i-237l9af0p',
            'openapi_internal_id':'lbbp1ur89f06e34b5583',
	    'openapi_external_id':'lbbp10t3v9ok2544rd42',
	    'openapi_node1':'i-23q31xu4x',
	    'openapi_node2':'i-23xp1j83j'
	    }
    slb_type=['internal','external']
    slb_project=['openapi','appapi','mps']
    
    def __init__(self,key_id,key_secret,region_id):
	self.key_id=key_id
	self.key_secret=key_secret
	self.region_id=region_id
        self.client=client.AcsClient(self.key_id,self.key_secret,self.region_id)

    def remove_backend_server(self,project,slb_type,servers):
	if project not in self.slb_project:
	    print 'illegal slb project name: the vaild choice is : openapi,appapi,mps'
	    sys.exit(1) 
	if slb_type not in self.slb_type:
	    print 'illegal slb type: the vaild choice is : internal , external'
	    sys.exit(1)
	if not isinstance(servers,list):
	    print 'servers must a list '
	    sys.exit(1)
	slb_id=self.lb_info.get(project+'_'+slb_type+'_id',None)
	servers_list=[]
	for v in servers:
	    if v not in self.lb_info.keys():
		print 'Bad servers list'
		sys.exit(1)
	    servers_list.append(self.lb_info[v].replace(' ',''))
	req=RemoveBackendServersRequest()
	req.set_LoadBalancerId(slb_id)
	req.set_BackendServers(servers_list)
	req.set_accept_format('json')
	result=json.loads(self.client.do_action_with_exception(req))
        if 'BackendServers' not in result.keys():
	    print 'Delete Backend Server Failed.........'
	    sys.exit(1)
	else:
	    print 'Delete Backend Server Success..........'
	    sys.exit(0)


    def add_backend_server(self,project,slb_type,servers):
	if project not in self.slb_project:
	    print 'illegal slb project name: the vaild choice is : openapi,appapi,mps'
	    sys.exit(1) 
	if slb_type not in self.slb_type:
	    print 'illegal slb type: the vaild choice is : internal , external'
	    sys.exit(1)
	if not isinstance(servers,list):
	    print 'servers must a list '
	    sys.exit(1)
	slb_id=self.lb_info.get(project+'_'+slb_type+'_id',None)
	servers_list=[]
	for v in servers:
	    if v not in self.lb_info.keys():
		print 'Bad servers list'
		sys.exit(1)
	    servers_list.append({'ServerId':self.lb_info[v].replace(' ',''),'Weigth':'100'})
	req=AddBackendServersRequest()
	req.set_LoadBalancerId(slb_id)
	req.set_BackendServers(servers_list)
	req.set_accept_format('json')
	result=json.loads(self.client.do_action_with_exception(req))
        if 'BackendServers' not in result.keys():
	    print 'Add Backend Server Failed.........'
	    print result
	    sys.exit(1)
	else:
	    print 'Add Backend Server Success..........'
	    sys.exit(0)




if __name__=='__main__':
    slb=SlbAction('your aliyun key_id','your aliyun key_secret_id','region_id')
    parse=optparse.OptionParser(usage='''
	    usage: %s [option]
	    this is python script to add or delete slb backend server by the aliyun sdk
	    ''' %sys.argv[0])
    parse.add_option('-t','--types',action='store',type='string',help='the lb type',dest='slb_type') 
    parse.add_option('-p','--project',action='store',type='string',help='the lb project',dest='project') 
    parse.add_option('-n','--host',action='store',type='string',help='the backend server name',dest='host_name') 
    parse.add_option('-a','--add',action='store_false',help='append server to lb backend',default=True) 
    parse.add_option('-d','--delete',action='store_false',help='delete server from lb backend',default=True) 
    opt,args=parse.parse_args()
    if not opt.add and not opt.delete:
	print 'can not prvide -a and -d at the same time '
	sys.exit(1)
    if opt.add and opt.delete:
	print 'must privide -a or -d choice '
	sys.exit(1)
    if not opt.add:
	slb.add_backend_server(opt.project,opt.slb_type,[opt.host_name])
    if not opt.delete:
	slb.remove_backend_server(opt.project,opt.slb_type,[opt.host_name])


