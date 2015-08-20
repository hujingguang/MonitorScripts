#!/bin/bash
#get two args . $1 is domian etc: bbs.wikiki.cn  $2 is status . etc: active , read,write,wait


get_active_con(){
     num=$(curl $1/status 2>/dev/null|awk -F':' '/Active/ {print $2}')
     printf $num
}
get_read_request(){

     num=$(curl $1/status 2>/dev/null|awk '/Reading/ {print $2}')
     printf $num
 }
get_write_respond(){
    
     num=$(curl $1/status 2>/dev/null|awk '/Reading/ {print $4}')
     printf $num
}
get_wait_conn(){

     num=$(curl $1/status 2>/dev/null|awk '/Reading/ {print $6}')
     printf $num

}

main(){

  case $2 in
      active)
             get_active_con $1
             ;;
      read)
             get_read_request $1
             ;;
      write)
             get_write_respond $1
             ;;
      wait)
             get_wait_conn $1
    esac
}
main $1 $2
