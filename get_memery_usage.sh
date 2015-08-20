#!/bin/bash
#the script accept two argv. one argv1: mem ,swap.    argv2: total,free,pused

get_memery_total(){
     total=$(free -m|egrep 'Mem'|awk '{print $2}')
     total=$(echo "scale=2;$total/1024"|bc|awk '{printf "%.2f",$1}')
     printf $total
}

get_swap_total(){
     total=$(free -m|egrep 'Swap'|awk '{print $2}')
     total=$(echo "scale=2;$total/1024"|bc|awk '{printf "%.2f",$1}')
     printf $total
}

get_swap_free(){
     free=$(free -m|egrep 'Swap'|awk '{print $4}')
     free=$(echo "scale=2;$free/1024"|bc|awk '{printf "%.2f",$1}')
     printf $free
}

get_memery_free(){
  
     free=$(free -m|egrep 'Mem'|awk '{print $4}')
     
     free=$(echo "scale=2;$free/1024"|bc|awk '{printf "%.2f",$1}')
     printf $free
}

get_memery_percent(){
      
     total=$(free -m|egrep 'Mem'|awk '{print $2}')
     used=$(free -m|egrep 'Mem'|awk '{print $3}')
     percent=$(echo "scale=2;$used/$total*100"|bc|awk '{printf "%.2f",$1}')
     printf $percent
}
main(){
    if [ $1 == "mem" ] 
    then
     case $2 in
         "total")
              get_memery_total $2
              ;;
         "free")
              get_memery_free $2
              ;;
         "pused")
              get_memery_percent $2
              ;;
            esac

    else
        case $2 in
            "total")
                get_swap_total $2
                ;;
            "free")
                get_swap_free $2
                ;;
            esac
    fi
}
main $1 $2

