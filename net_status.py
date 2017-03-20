#!/usr/bin/python
import psutil
import optparse
import sys



def get_net_status_counts(lport,status,dst_port=None):
    conns=psutil.net_connections()
    STATUS=['TIME_WAIT','ESTABLISHED','CLOSED','LISTEN','SYN_SENT','SYN_RCVD','CLOSE_WAIT','FIN_WAIT1','FIN_WAIT2','CLOSING','LAST_ACK']
    counts=0
    pid=get_pid_from_port(conns,lport)
    if status not in STATUS:
	raise 'Bad net connnections status' 
    if dst_port:
	for conn in conns:
	    if conn.status == status and conn.raddr[1] == dst_port and conn.pid==pid:
		counts=counts+1
    else:
	for conn in conns:
	    if conn.status == status and conn.laddr[1]==lport:
		counts=counts+1
    return counts

def get_pid_from_port(conns,port):
    if not conns:
	raise 'Not connection object'
    for conn in conns:
	if conn.status=='LISTEN' and conn.laddr[1] == port:
	    return conn.pid

    


def parse_option():
    parse=optparse.OptionParser(usage='''
	    get net connections status 
	    ''')
    parse.add_option('-p','--port',action='store',type='int',help='connect port',dest='port')
    parse.add_option('-s','--status',action='store',type='string',help='net connections status',dest='status')
    parse.add_option('-d','--dstport',action='store',type='int',help='dst port ',dest='dst_port')
    opts,args=parse.parse_args()
    if not opts.status or not opts.port:
	parse.print_help()
	sys.exit(1)
    return opts.status,opts.port,opts.dst_port



if __name__=='__main__':
    status,port,dst_port=parse_option()
    print dst_port
    print get_net_status_counts(port,status,dst_port=dst_port)


	



