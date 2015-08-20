#/bin/bash
#the script accept two  arg. arg1: eth1,eth0. arg2: in/s , out/s. 


getInterfaceIn(){
    Rx_old=$(ifconfig $1|egrep "RX"|tail -n1|tr ':' ' '|awk '{print $3}')
    sleep 2 
    wait 
    Rx_new=$(ifconfig $1|egrep "RX"|tail -n1|tr ':' ' '|awk '{print $3}')
    R_rate=$(echo "scale=3;($Rx_new-$Rx_old)/(2*1024*1024)"|bc|awk '{printf "%.3f",$1}')
    printf $R_rate
}
getInterfaceOut(){
     
    Tx_old=$(ifconfig $1|egrep "RX"|tail -n1|tr ':' ' '|awk '{print $8}')
    #echo $Tx_old
    sleep 2    
    wait
    Tx_new=$(ifconfig $1|egrep "RX"|tail -n1|tr ':' ' '|awk '{print $8}')
    
    #echo $Tx_new
    T_rate=$(echo "scale=3;($Tx_new-$Tx_old)/(2*1024*1024)"|bc|awk '{printf "%.3f",$1}')
    printf $T_rate
}

main(){
  case $2 in
      "in/s")
          getInterfaceIn $1
          ;;
      "out/s")
          getInterfaceOut $1
          ;;
      esac
}

main $1 $2
