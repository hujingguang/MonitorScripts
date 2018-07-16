#!/bin/bash
DATE=`date +"%H%M%S"`
TMP_FILE='/tmp/.info'
LOG_PATH=/data/backup/js_log/`date +"%Y%m%d"`
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
ps aux|egrep "USER|$PID"|egrep -v "grep|bash"|awk '{print $1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "$10" "$11}' >>$INFO_FILE
echo -e "\n\n线程信息总览\n" >> $INFO_FILE
echo "%CPU   PID   LWP  COMMAND           TIME     ELAPSED" >> $INFO_FILE 
ps -eLo 'pcpu pid lwp comm time etime'|egrep "$PID"|sort -k1 -n -r >> $INFO_FILE
su - ld_dev -c "jstack -l $PID >/tmp/.j.log"
cat /tmp/.j.log |egrep '\[0x|nid=0x'|awk -F'"' '{print $3}'>/tmp/.j.next.log
PYTHON_CODE='import os\n_STR=""\nwith open("/tmp/.j.next.log","r") as f:\n\tfor line in f.readlines():\n\t\tfor w in line.split(" "):\n\t\t\tif w.startswith("nid="):\n\t\t\t\t_STR=_STR+w+" "+w.split("=")[1]+" "+str(int(w.split("=")[1],16))+"\\n"\nwith open("/tmp/.ret.log","w") as f:\n\tf.write(_STR)\nfor L in _STR.split("\\n"):\n\tif L:\n\t\tL=L.split(" ")\n\t\tcmd="sed -i \"s/{0}/{1}/g\" /tmp/.j.log".format(L[1],L[2])\n\t\tos.system(cmd)'
echo -e $PYTHON_CODE >/tmp/.p.py && python /tmp/.p.py
echo -e "\n\nJSTACK 信息总览\n" >> $INFO_FILE
cat /tmp/.j.log >> $INFO_FILE
