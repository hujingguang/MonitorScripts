#!/bin/bash
#the scripts to used count R/s and W/s on device.and accept two Args
#arg1 is device name .etc: sda1 sda; arg2 is Read or Write , etc:R/s ,W/s

getRead(){
   r_rate=$(/usr/bin/iostat -x -m -d $1|egrep "$1" |awk '{print $6}')
   printf $r_rate
}
getWrite(){
    w_rate=$(/usr/bin/iostat -x -m -d $1|egrep "$1"|awk '{print $7}')
    printf $w_rate
}

main(){
   case $2 in
       "r/s")
          getRead $1
          ;;
       "w/s")
          getWrite $1
          ;;
      esac
}
main $1 $2




