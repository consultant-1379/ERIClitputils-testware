Check_sleep.py
-------------------

TORF-195717 showed behaviour where a 1 second sleep was actually taking several minutes due to LITP performance degredation.

The check_sleep.py script compares lines like the below:

Jun  9 06:33:05 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: ._sleep_and_check_plan_state: Waiting for state transition to end. 5 second(s) elapsed out of 15 second(s) on node "node2dot68".
Jun  9 06:33:05 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: [DataManager] get_plan: CURRENT
Jun  9 06:33:06 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: ._sleep_and_check_plan_state: Waiting for state transition to end. 6 second(s) elapsed out of 15 second(s) on node "node2dot68".
Jun  9 06:33:06 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: [DataManager] get_plan: CURRENT

To ensure that only 1 second passes between two get_plan calls. it is called as below:

> python check_sleep.py ##LOGFILE_PATH##

Below is an example failure:

>python check_sleep.py messages 
#######ERROR#########
Time delay between below lines is greater than expected:
Jun  9 06:28:28 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: ._sleep_and_check_plan_state: Waiting for state transition to end. 9 second(s) elapsed out of 15 second(s) on node "node1dot68".

Jun  9 06:28:30 ms1 litp.trace[46474:Celery(run_plan_phase)]{0x7f0b16e46700}: DEBUG: ._sleep_and_check_plan_state: Waiting for state transition to end. 10 second(s) elapsed out of 15 second(s) on node "node1dot68".

>>> Sleep between lines: 2
##########################
Number of log sleep cases: 316
Number of failures: 1




The script will return a 0 exit code if there are no failures or 1 if there are failures.

NB: Debug must be turned on in logs for this script to work.

David Appleton
9/6/2017
