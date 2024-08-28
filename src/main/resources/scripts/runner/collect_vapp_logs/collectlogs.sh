#!/bin/sh

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

cd ptyprocess-0.5.2; python setup.py install
cd ..; rm -rf ptyprocess-0.5.2

cd pexpect-4.5.0; python setup.py install
cd ..; rm -rf pexpect-4.5.0

python collect_all_logs.py
