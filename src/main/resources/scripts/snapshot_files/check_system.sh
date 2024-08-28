#!/bin/bash

IFS=$'\n'; set -f;
hostn=( $(cat /etc/hosts | grep -v HEADER | awk '{print $1;}' ) )
for line in ${hostn[@]}
do
    ping -c3 $line | grep "0% packet loss"
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then
        echo "HOST: $line could not be reached"
        exit 1
    fi
done
echo "LITP kgb_restore has completed sucessfully"
unset IFS
