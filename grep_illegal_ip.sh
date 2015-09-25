#!/bin/sh
#BlackList=$(grep 'Failed' /var/log/secure|cut -d' ' -f11 |egrep '^[0-9].*[0-9]$' |sort|uniq -c|awk -F' ' '{print $1" "$2}')


grep 'Failed' /var/log/secure|tr -s ' '|cut -d' ' -f11|egrep '^[0-9].*' |sort |uniq -c|awk -F' ' '{print $1" "$2 }' | while read line
                do 
                    echo "1">/tmp/txt  #设置标记为1
                    num=$(echo "$line"|cut -d' ' -f1)
                    IP=$(echo "$line"|cut -d' ' -f2)
                   if (($num >= 5))
                        then
                       grep 'sshd:' /etc/hosts.deny |cut -d":" -f2 |while read EIP
                          do
                             if [ "$IP" == "$EIP" ]
                             then
                                 echo "$IP---------$EIP"
                                 echo '不用添加'
                                 echo '0'>/tmp/txt  #设置标记为0
                                 break 1
                             fi
                        done 
                        flag=$(cat /tmp/txt)       #获取标记 
                      if  (($flag == 1))
                        then
                        echo "sshd:$IP">>/etc/hosts.deny
                      fi
                   fi
                done

