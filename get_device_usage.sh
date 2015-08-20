#!/bin/bash
#this is scripts about get file system usage 
#the script get two  params  ARGS1 is  filesytem name etc:/ , /data ,/soft  ;ARGS2 is usage  etc: free,total,pused,  


getPartionTotal(){
   total=$(/bin/df -h |egrep "$1$" |tr 'G' ' '|tr 'M' ' ' |tr -s ' '|cut -d' ' -f2)
   printf $total
}
getPartionFree(){
    free=$(/bin/df -h |egrep "$1$"|tr 'G' ' '|tr 'M' ' '|tr -s ' '|cut -d' ' -f4)
    printf $free 
}
getPartusedPercent(){
    percent=$(/bin/df -h |egrep "$1$"|tr 'G' ' '|tr 'M' ' '|tr '%' ' '|tr -s ' '|cut -d' ' -f5)
    printf $percent
}

main(){
   case "$2" in 
    "free")
          getPartionFree $1
          ;;
    "total")
          getPartionTotal $1
          ;;
    "pused")
          getPartusedPercent $1
         ;;
      esac
}

main $1 $2
