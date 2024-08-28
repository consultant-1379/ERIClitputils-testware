#!/bin/bash


IFS=$'\n'; set -f;
origvols=( $(/usr/sbin/vxdg list | grep -vE 'NAME|STATE'))
for line in ${origvols[@]}
do
    volgr=( $(echo "$line" | awk '{ print $1 }') )
    volnode=( $(echo "$line" | awk '{ print $3 }') )
    #volnm=( $(vxprint -g $volgr -um | grep "v" | grep "fsgen" | head -1 | awk '{ print $2 }' ) )
    volnm=( $(vxprint -g $volgr -um | grep "fsgen" | grep -v "v  L_" | awk '{ print $2 }' ) )
    echo "VOLGRP IS: $volgr , NODE IS ${volnode##*.} , VOLNAME IS: $volnm"
    echo "/opt/VRTS/bin/vxsnap -g $volgr restore $volnm source=litp_""$volnm""_kgb_snapshot"
    /opt/VRTS/bin/vxsnap -g $volgr restore $volnm source=litp_$volnm'_kgb_snapshot'
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOT REMOVAL FAILED"
       exit 1
   fi
   sleep 1
   echo "/opt/VRTS/bin/vxsnap -g $volgr dis litp_$volnm""_kgb_snapshot"
   /opt/VRTS/bin/vxsnap -g $volgr dis litp_$volnm'_kgb_snapshot'
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOT REMOVAL FAILED"
       exit 1
   fi
   sleep 1
   echo "/opt/VRTS/bin/vxedit -g $volgr -rf rm litp_$volnm""_kgb_snapshot"
   /opt/VRTS/bin/vxedit -g $volgr -rf rm litp_$volnm'_kgb_snapshot'
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOT REMOVAL FAILED"
       exit 1
   fi
   sleep 1
   echo "/opt/VRTS/bin/vxcache -g $volgr stop litp_kgb_""$volnm""_co"
    /opt/VRTS/bin/vxcache -g $volgr stop litp_kgb_$volnm'_co'
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOT REMOVAL FAILED"
       exit 1
   fi
   sleep 1
   echo "/opt/VRTS/bin/vxedit -g $volgr -rf rm litp_kgb_""$volnm""_co"
    /opt/VRTS/bin/vxedit -g $volgr -rf 'rm' litp_kgb_$volnm'_co'
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOT REMOVAL FAILED"
       exit 1
   fi
done

origvols=( $(/sbin/lvscan | grep kgb_snapshot))
for line in ${origvols[@]}
do
   volgr=( $(echo "$line" | awk '{print $3;}' | sed s/\'//g) )
   /sbin/lvconvert --merge $volgr
   retval=( $(echo $?) )
   if [[ $retval -ne 0 ]]
   then 
       echo "SNAPSHOTS FAILED TO MERGE"
       exit 1
   fi
done

echo "Move of /boot/grub2/grub.cfg.kgb.backup /boot/grub2/grub.cfg"
mv -f /boot/grub2/grub.cfg.kgb.backup /boot/grub2/grub.cfg

echo "All litp_kgb snapshots have been merged successfully"
unset IFS
