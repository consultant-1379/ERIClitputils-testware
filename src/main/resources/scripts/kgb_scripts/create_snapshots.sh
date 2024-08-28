#!/bin/bash

IFS=$'\n'; set -f;


origvols=( $(/usr/sbin/vxdg list | grep -vE 'NAME|STATE'))
for line in ${origvols[@]}
do
    echo "--------> $line"
    volgr=( $(echo "$line" | awk '{ print $1 }') )
    volnode=( $(echo "$line" | awk '{ print $3 }') )
    volsize=( $(vxprint -g $volgr -um | grep "v" | grep "fsgen" | head -1 | awk '{ print $5 }' ) )
    #volnm=( $(vxprint -g $volgr -um | grep "v" | grep "fsgen" | head -1 | awk '{ print $2 }' ) )
    volnm=( $(vxprint -g $volgr -um | grep "fsgen" | grep -v "v  L_" | awk '{ print $2 }' ) )
    volpresnapsize=( $(echo $volsize | sed s/m//g) )
    volsnapsize=( $(echo "scale=2;$volpresnapsize/10" | bc -l) )
    echo "VOLGRP IS: $volgr , SIZE IS $volsize , NODE IS ${volnode##*.} , VOLNAME IS: $volnm , VOL SNAP SIZE IS: $volsnapsize"
    echo "/opt/VRTS/bin/vxassist -g $volgr make litp_kgb_""$volnm""_cv $volsnapsize init=active"
    /opt/VRTS/bin/vxassist -g $volgr make 'litp_kgb_'$volnm'_cv' $volsize init=active
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then 
        echo "SNAPSHOT FAILED TO CREATE"
        exit 1
    fi
    echo "/opt/VRTS/bin/vxmake -g $volgr cache litp_kgb_""$volnm""_co cachevolname=litp_kgb_""$volnm""_cv'"
    /opt/VRTS/bin/vxmake -g $volgr cache litp_kgb_$volnm'_co' cachevolname=litp_kgb_$volnm'_cv'
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then 
        echo "SNAPSHOT FAILED TO CREATE"
        exit 1
    fi
    echo "/opt/VRTS/bin/vxcache -g $volgr start litp_kgb_""$volnm""_co"
    /opt/VRTS/bin/vxcache -g $volgr start litp_kgb_$volnm'_co'
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then 
        echo "SNAPSHOT FAILED TO CREATE"
        exit 1
    fi
    echo "/opt/VRTS/bin/vxsnap -g $volgr  make source=$volnm/newvol=litp_""$volnm""_kgb_snapshot/cache=litp_kgb_""$volnm""_co"
    /opt/VRTS/bin/vxsnap -g $volgr  make source=$volnm/newvol='litp_'$volnm'_kgb_snapshot'/cache=litp_kgb_$volnm'_co'
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then 
        echo "SNAPSHOT FAILED TO CREATE"
        exit 1
    fi
done



origvols=( $(/sbin/lvscan | grep Original))
for line in ${origvols[@]}
do
    volgr=( $(echo "$line" | awk '{print $3;}' | sed s/\'//g) )
    volsize=( $(echo "$line" | awk '{print $4;}' | cut -d '[' -f 2) )
    snapsize=( $(echo "scale=2;$volsize/10" | bc -l))
    if [[ ${snapsize:0:1} == "." ]]
    then
        snapsize=($(echo "0$snapsize"))
    fi
    snapname=( $(echo ${volgr##*:}))
    echo "VOLGRP: $volgr SIZE: $volsize SNAPSHOT NAME: $snapname SNAPSHOT SIZE: $snapsize"
    /sbin/lvcreate -s -L $snapsize'G' -n $snapname'_kgb_snapshot' $volgr
    retval=( $(echo $?) )
    if [[ $retval -ne 0 ]]
    then 
        echo "SNAPSHOT FAILED TO CREATE"
        exit 1
    fi
done

echo "Copy of /boot/grub2/grub.cfg to /boot/grub2/grub.cfg.kgb.backup"
cp -p /boot/grub2/grub.cfg /boot/grub2/grub.cfg.kgb.backup

echo "All litp_kgb snapshots have been created successfully"
unset IFS
