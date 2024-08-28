#!/bin/bash

args=( $@ )

wkdir=( $(dirname "${BASH_SOURCE[0]}" ) )

#cd $wkdir
echo "MY CURRENT DIRECTORY IS: $pwd"
echo -e "Running Test Case: ${args[0]} from test case file ${args[1]}\n"

export PYTHONPATH="$PYTHONPATH:${args[2]}"
export LITP_CONN_DATA_FILE="${args[3]}"

cp ${args[4]} ${args[5]}

IFS=$'\n'; set -f;
runnose=( $(nosetests -s --testmatch=${args[0]} ${args[1]} 2>&1) )
for line in "${runnose[@]}"
do
    echo $line
done
unset IFS
if [[ "${runnose[${#runnose[@]} - 1]}" == "OK" ]]
then
    echo "RPM UPGRADE IS SUCCESSFUL"
    exit 0
else
    echo "RPM UPGRADE HAS FAILED"
    exit 1
fi
