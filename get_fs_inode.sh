#!/bin/bash
#this is script about get inode counts from filesystem
#the script get tow args  arg1 is filesystem partion. etc: /data ,/; arg2 is action. etc:free,total,pused .

getInodeTotal(){
   total=$(/bin/df -i|egrep "$1$"|tr '%' ' '|tr -s ' '|cut -d' ' -f2)
   printf  "$total"; 
}
getInodeFree(){
   free=$(/bin/df -i|egrep "$1$"|tr '%' ' '|tr -s ' ' |cut -d' ' -f4)
   printf "$free";
}
getInodePercent(){
   percent=$(/bin/df -i|egrep "$1$"|tr '%' ' '|tr -s ' ' |cut -d' ' -f5)
   printf "$percent";
}

main(){
   case $2 in
    "total")
           getInodeTotal $1
           ;;
    "free")
           getInodeFree $1
           ;;
    "pused")
           getInodePercent $1
           ;;
    esac
}

main $1 $2
