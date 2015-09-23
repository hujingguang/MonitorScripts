#!/usr/bin/python
import.netmands
import time
import os
import sys
WEB_BACKENDS={'www.kldjy.net':['192.168.168.121:8080','192.168.168.123:80'],
        'iphone.kldjy.net':['192.168.168.121:80','192.168.168.123:80'],
        'user.xixixi.net':['192.168.168.119:80/checkstatus.php','192.168.168.124:80/checkstatus.php'],
        'sv.xixixi.net':['192.168.168.103:80','192.168.168.104:80'],
        'umsa.xixixi.net':['192.168.168.105:80'],
        'ums.xixixi.net':['192.168.168.117:88/release/checkstatus.ums','192.168.168.118:88/release/checkstatus.ums','192.168.168.128:88/release/checkstatus.ums'],
        'kz.xixixi.net.net':['192.168.169.31:80/checkstatus.php','192.168.169.33/checkstatus.php'],
        'qcode.xixixi.net':['192.168.168.103:80/checkstatus.php','192.168.168.104:80/checkstatus.php'],
        'open.xixixi.net':['192.168.168.103:80/checkstatus.php','192.168.168.104:80/checkstatus.php'],
        'map.xixixi.net':['192.168.168.103:80/checkstatus.php','192.168.168.104:80/checkstatus.php'],
        'weixin.xixixi.net':['192.168.168.103:80/checkstatus.php','192.168.168.104:80/checkstatus.php'],
        'boss.xixixi.net':['192.168.168.101:80/checkstatus.php'],
        'channel.xixixi.net':['192.168.168.102:80/checkstatus.php','192.168.168.106:80/checkstatus.php'],
        'shop.xixixi.net':['192.168.168.102:80/checkstatus.php','192.168.168.106:80/checkstatus.php'],
        'img1.kldjy.net':['192.168.168.137:80','192.168.168.114:80'],
        'www.xixixi.net':['192.168.168.102:80','192.168.168.106:80'],
        'www.navione.net':['192.168.168.102:80','192.168.168.106:80'],
        'lbs.xixixi.net':['192.168.168.120:80/ds/'],
        'hy.xixixi.net':['192.168.168.103:80','192.168.168.104:80'],
        'hnradio.kldlk.net':['192.168.168.120:80'],
        'navi.xixixi.net':['192.168.169.21:80/cgi/cgi_test.ums?test=cgitest','192.168.169.22:80/cgi/cgi_test.ums?test=cgitest','192.168.169.23:80/cgi/cgi_test.ums?test=cgitest','192.168.169.36:80/cgi/cgi_test.ums?test=cgitest','192.168.169.37:80/cgi/cgi_test.ums?test=cgitest','192.168.169.38:80/cgi/cgi_test.ums?test=cgitest','192.168.169.39:80/cgi/cgi_test.ums?test=cgitest','192.168.169.40:80/cgi/cgi_test.ums?test=cgitest','192.168.169.41:80/cgi/cgi_test.ums?test=cgitest'],
        'st.xixixi.net':['192.168.168.109/tc/controlpanel/login.php','192.168.168.113/tc/controlpanel/login.php','192.168.168.112/tc/controlpanel/login.php','192.168.168.107/tc/controlpanel/login.php'],
        'hyapi.xixixi.net':['192.168.168.102:80/checkstatus.php','192.168.168.106:80/checkstatus.php']
        }


def check_backend(domain,url):
    cmd='curl --head -H "Host:%s" %s |grep "200 OK" &>/dev/null' %(domain,url)
    res.netmands.getstatusoutput(cmd)
    if res[0] !=0:
        return True

Old_Hosts={}
New_Hosts={}

def main(domain,Hosts):
    if domain in WEB_BACKENDS:
        hosts=[]
        flag=False
        for backend in WEB_BACKENDS[domain]:
            if check_backend(domain,backend):
                #print 'the domain: %s   backend: %s  not available' %(domain,backend)
                hosts.append(backend.split('/')[0])
                Hosts[domain]=hosts
                if not flag:
                    flag=True
            else:
                pass
                #print 'the domain: %s   backend: %s  is ok' %(domain,backend)
        if flag:
           .netments=domain+"-Backends-"
            for h in hosts:
               .netments.netments+h+"-Failed"
            f_name='/tmp/%s' %domain
            f=open(f_name,'w')
            f.write.netments)
            f.close()
        else:
            pass            
            #if os.path.exists('')





if __name__== '__main__':
    list=[]
    for i in WEB_BACKENDS.iterkeys():
        main(i,Old_Hosts)
    time.sleep(180)
    for i in WEB_BACKENDS.iterkeys():
        main(i,New_Hosts)
    if New_Hosts:
        for domain in New_Hosts.iterkeys():
           if domain in Old_Hosts:
                  for h in Old_Hosts[domain]:
                      print h.split('/')[0]
                      f='/tmp/.domain_%s_%s' %(domain,h.split('/')[0])
                      if not os.path.exists(f):
                         os.system('touch %s' %f)
                         messages="PROBLEM_:%s_%s__has_failed" %(domain,h.split('/')[0])
                         os.system('bash /soft/zabbix/share/zabbix/alertscripts/web_backend.sh "%s"' %messages)
                         print 'send warning sms'
    
    res=os.system('ls /tmp/.domain_* &>/dev/null')
    if res == 0:
        res,out.netmands.getstatusoutput(r'ls /tmp/.domain_*')
        recovery={}
        for var in out.split('\n'):
           List=var.strip().split('_')
           if not List[1] in recovery:
                  recovery[List[1]]=[List[2]]
           else:
                  tmp_list=recovery[List[1]]
                  tmp_list.append(List[2])
                  recovery[List[1]]=tmp_list
        for fail_domain in recovery.iterkeys():
           if not fail_domain in New_Hosts:
                  print 'this domain: %s begain to recovery' %fail_domain
                  f=r'/tmp/.domain_%s_*' %(fail_domain)
                  os.system('rm -rf %s' %f)
                  messages="OK_:%s__all_backend_hosts_has_UP" %fail_domain
                  os.system('bash /soft/zabbix/share/zabbix/alertscripts/web_backend.sh "%s"' %messages)
                  print 'send recovery sms'
           else:
                  fail_hosts=recovery[fail_domain]
                  for fail_host in fail_hosts:
                           for h in New_Hosts[fail_domain]:
                                if fail_host != h.split('/')[0]:
                                   print 'host_ip: %s recovery ' %fail_host
                                   f='/tmp/.domain_%s_%s' %(fail_domain,fail_host)
                                   os.system('rm -f %s' %f)                                  
                                   messages="OK_:%s__%s__has_Recover" %(fail_domain,fail_host)
                                   os.system('bash /soft/zabbix/share/zabbix/alertscripts/web_backend.sh "%s"' %messages)
                                   print 'send recovery sms'
          
                           
