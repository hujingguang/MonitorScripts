#!/bin/bash
DATE=`date +"%H%M%S"`
TMP_FILE='/tmp/.info'
LOG_PATH=/data/jstack_log/`date +"%Y%m%d"`
INFO_FILE=$LOG_PATH/$DATE
PID=$1
if [ "$PID" == "" ]
then
   PID=`ps aux|grep crm_api|grep -v grep|awk '{print $2}'`
   if [ "$PID" == "" ]
   then
      echo '无法获取指定PID ,Exit'
      exit 1
   fi
fi
ps aux |grep $PID|egrep -v 'grep|bash' &>/dev/null || exit 0
[ -e $LOG_PATH ] || mkdir -p $LOG_PATH  
echo -e '\n进程信息总览\n' >$INFO_FILE
#ps aux|egrep "USER|$PID"|egrep -v "grep|bash"|awk '{print $1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "$10" "$11" "$12}' >>$INFO_FILE
ps aux|egrep "USER|$PID"|egrep -v "grep|bash" >>$INFO_FILE
echo -e '\nTop命令信息总览\n' >> $INFO_FILE
top -n1 -b -Hp $PID >> $INFO_FILE
echo -e "\n\n线程信息总览\n" >> $INFO_FILE
echo "%CPU %MEM   PID   LWP COMMAND             TIME     ELAPSED   RSS START" >> $INFO_FILE 
ps -eLo 'pcpu pmem pid lwp comm time etime rssize start_time'|egrep "$PID"|sort -k1 -n -r > /tmp/.p.log && cat /tmp/.p.log >> $INFO_FILE
ruser=`ps -p $PID -o ruser --no-headers`
su - $ruser -c "jstack -l $PID >/tmp/.j.log"
cat /tmp/.j.log |egrep '\[0x|nid=0x'|awk -F'"' '{print $3}'>/tmp/.j.next.log
PYTHON_CODE='import os\n_STR=""\n_PID=[]\n_PID_MAP={}\nwith open("/tmp/.j.next.log","r") as f:\n\tfor line in f.readlines():\n\t\tfor w in line.split(" "):\n\t\t\tif w.startswith("nid="):\n\t\t\t\t_PID.append(str(int(w.split("=")[1],16)))\n\t\t\t\t_STR=_STR+w+" "+w.split("=")[1]+" "+str(int(w.split("=")[1],16))+"\\n"\nwith open("/tmp/.ret.log","w") as f:\n\tf.write(_STR)\nfor L in _STR.split("\\n"):\n\tif L:\n\t\tL=L.split(" ")\n\t\tcmd="sed -i \"s/{0}/{1}/g\" /tmp/.j.log".format(L[1],L[2])\n\t\tos.system(cmd)\nwith open("/tmp/.p.log","r") as f:\n\tfor L in f.readlines():\n\t\tfor pid in _PID:\n\t\t\tif L.find(pid) != -1:\n\t\t\t\t_PID_MAP[pid]=L\nfor k,v in _PID_MAP.iteritems():\n\tv=v.replace("\\n","")\n\tcmd="sed -i \"/{0}/a\\\\--ThreadInfo--%CPU %MEM   PID   LWP COMMAND TIME  ELAPSED RSS START\\\\n--------------{1}\\\\n\" /tmp/.j.log".format("nid="+k,v)\n\tos.system(cmd)'
echo -e $PYTHON_CODE |python
echo -e "\n\nJSTACK 信息总览\n" >> $INFO_FILE
cat /tmp/.j.log >> $INFO_FILE
rm -f /tmp/.p.py /tmp/.p.log /tmp/.j.next.log /tmp/.j.log /tmp/.ret.log
echo '日志文件---->'$INFO_FILE
