#!/usr/bin/python
import psutil
import optparse
import sys



def get_net_status_counts(lport,status):
    conns=psutil.net_connections()
    STATUS=['TIME_WAIT','ESTABLISHED','CLOSED','LISTEN','SYN_SENT','SYN_RCVD','CLOSE_WAIT','FIN_WAIT1','FIN_WAIT2','CLOSING','LAST_ACK']
    counts=0
    if status not in STATUS:
	raise 'Bad net connnections status' 
    for conn in conns:
	if conn.status == status and conn.laddr[1]==lport:
	    counts=counts+1
    return counts

def parse_option():
    parse=optparse.OptionParser(usage='''
	    get net connections status 
	    ''')
    parse.add_option('-p','--port',action='store',type='int',help='connect port',dest='port')
    parse.add_option('-s','--status',action='store',type='string',help='net connections status',dest='status')
    opts,args=parse.parse_args()
    if not opts.status or not opts.port:
	parse.print_help()
	sys.exit(1)
    return opts.status,opts.port



if __name__=='__main__':
    status,port=parse_option()
    print get_net_status_counts(port,status)


	



