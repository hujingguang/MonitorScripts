#!/usr/bin/python
from aliyunsdkecs.request.v20140526.DescribeImagesRequest import DescribeImagesRequest
from aliyunsdkecs.request.v20140526.CreateImageRequest import CreateImageRequest
from aliyunsdkecs.request.v20140526.DeleteImageRequest import DeleteImageRequest
from aliyunsdkcore.client import AcsClient
import optparse
import ConfigParser
import sys
import json
import logging

'''
create or delete an aliyun host image script
'''

__author__='hoover'
__CONFIG_FILE_PATH='/root/deploy/region.conf'
__SK='your_aliyun_Secret Key'
__KEY='your Key'
IMAGE_RETURN_ATTR=['ImageId','CreationTime','Progress','Usage','Status','Description','ImageName','Platform','ImageOwnerAlias']
__LOG_FILE_PATH='/tmp/aliyun_img.log'
DEBUG=True
__level=None
if DEBUG:
    __level=logging.DEBUG
    __LOG_FILE_PATH=None
else:
    __level=logging.INFO
logging.basicConfig(filename=__LOG_FILE_PATH,format='%(asctime)s %(levelname)s:  %(message)s',level=__level)

def config_parser(configure_file_path):
    conf=ConfigParser.ConfigParser()
    conf.read(configure_file_path)
    __section_list=conf.sections()
    __region_ids={}
    for region in __section_list:
	tmp_dict=dict()
	host_list=conf.options(region)
	if host_list:
	    for host in host_list:
		tmp_dict[host]=conf.get(region,host)
        __region_ids[region]=tmp_dict 
    return __region_ids

def get_region_from_host(host):
    region_ids=config_parser(__CONFIG_FILE_PATH)
    region_name=None
    host_id=None
    for region,values in region_ids.iteritems():
	if host in values.keys():
            region_name=region
	    host_id=values[host]
	    flag=False
	    break
	else:
	    flag=True
    if flag:
	logging.error("the host: %s  don't exist ! " %host)
	sys.exit(1)
    else:
	return region_name,host_id


def get_img_from_region(region,status='Available'):
    client=AcsClient(__SK,__KEY,region)
    request=DescribeImagesRequest()
    request.set_accept_format('json')
    request.set_Status(status)
    result=json.loads(client.do_action_with_exception(request))
    images=dict()
    for k,v in result.iteritems():
	if k == 'Images':
	    for i in v['Image']:
		if i['ImageOwnerAlias'] == 'self':
		    tmp=dict()
		    for key in IMAGE_RETURN_ATTR:
			tmp[key]=i[key]
	            images[i['ImageName']]=tmp
		    continue
    return images
    
def change_image(host,img_name_suffix='copy',option='add'):
    '''
    @host: list , host name to be cloned
    @img_name_suffix  default is Copy . if host name is Server1  the ImageName is Server1_copy 
    '''
    if not isinstance(host,list) or host == [] :
	raise 'host not list type or host is empty list . function: create_image'
	sys.exit(1)
    host_info=dict()
    for h in host:
	region_name,host_id=get_region_from_host(h)
	host_info[h]=[region_name,host_id]
    for h,region_and_id in host_info.iteritems():
	images=get_img_from_region(region_and_id[0])
	conbine_img_name=h+'_'+img_name_suffix
	if option == 'add':
	    if conbine_img_name in get_img_from_region(region_and_id[0],status='Creating'):
		logging.warn('the image: %s is be creating . please wait' %conbine_img_name)
	    elif conbine_img_name in get_img_from_region(region_and_id[0]):
		logging.info('the image is exists,begin to delete %s images' %conbine_img_name)
		img_id=images[conbine_img_name]['ImageId']
		__delete_image(img_id,region_and_id[0])
	    __create_image(region_and_id[1],conbine_img_name,region_and_id[0])
	elif option == 'del':
	    if conbine_img_name in get_img_from_region(region_and_id[0],status='Creating'):
		logging.warn('the image: %s is be creating . can not delete by API' %conbine_img_name)
	    else:
		logging.info('begin to remove the image : %s' %conbine_img_name)
		img_id=images[conbine_img_name]['ImageId']
		__delete_image(img_id,region_and_id[0])
	    
	else:
	    raise 'Bad Option Args !'



def __delete_image(img_id,region):
    client=AcsClient(__SK,__KEY,region)
    d_request=DeleteImageRequest()
    d_request.set_accept_format('json')
    d_request.set_ImageId(img_id)
    result=json.loads(client.do_action_with_exception(d_request))
    if 'Code' in result:
	logging.warn('remove image failed')
	logging.error('remove failed . message: ' %result['Message'])
	return False
    else:
        logging.info('Ok,image has been removed')
	return True


def __create_image(host_id,img_name,region):
    client=AcsClient(__SK+'O',__KEY+'3',region)
    c_request=CreateImageRequest()
    c_request.set_accept_format('json')
    c_request.set_ImageName(img_name)
    c_request.set_InstanceId(host_id)
    result=json.loads(client.do_action_with_exception(c_request))
    if 'Code' in result:
	logging.warn('the image: %s  can not  be creating now ! please wait' %img_name)
    else:
	logging.info('Ok , the image: %s  begin to copy now' %img_name)
    

def parser_opt():
    parser=optparse.OptionParser(usage='''
	    usage: %s [option]
	    this script be used to add or delete aliyun image 
	    ''' %sys.argv[0])
    parser.add_option('-H','--hosts',action='store',type='string',help='host list configure file path: ./region.conf ',dest='hosts') 
    parser.add_option('-o','--option',action='store',type='string',help='add or delete image . value: del|add',dest='option')
    opt,args=parser.parse_args()
    if not opt.hosts  or not opt.option:
	parser.print_help()
    else:
	hosts=[i for i in opt.hosts.replace(' ',':').split(':') if i!='']	
        change_image(hosts,option=opt.option)


if __name__=='__main__':
    parser_opt()

