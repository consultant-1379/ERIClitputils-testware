"""
Test
"""

import paramiko
import time
import socket
import StringIO
#import os
#import test_constants
#import string
import subprocess
import pexpect
import os

class NodeConnect():
    """
    Test
    """

    def __init__(self, ipaddr="", username="", password="",
                 ssh_key=True, hostname="", rootpw=""):
        """
        Init the object
        Args:
           username  (str): username to override
           password  (str): password to override
           ipv4     (bool): switch between ipv4 and ipv6

        Kwargs:
          ssh_key (bool): Set to False to disable ssh key checking.
                          This should be disabled when connecting to
                          an ILO due to compatibility issues between
                          some firmware versions and paramiko SSH.
        """
        self.ipv4 = ipaddr
        self.username = username
        self.password = password
        self.rootpw = rootpw
        self.ipv6 = None
        self.hostname = hostname
        self.host = None
        self.port = 22
        self.ssh = None
        # timeout for establishing ssh connection
        self.timeout = 20
        self.retry = 0
        # stdout and stderr buffer size, modify if necessary
        self.out_bufsize = 4096
        self.err_bufsize = 4096
        # 60 seconds timeout for I/O channel operations
        self.session_timeout = 60
        # Timeout to wait for output after execution of a cmd
        self.execute_timeout = 0.25
        self.ssh_key = ssh_key

    def __connect(self, username=None, password=None):
        """Connect to a node using paramiko.SSHCLient

        Args:
           username  (str): username to override
           password  (str): password to override
           ipv4     (bool): switch between ipv4 and ipv6

        Returns:
           bool

        Raises:
           BadHostKeyException, AuthenticationException, SSHException,
           socket.error
        """
        self.retry += 1

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = self.ipv4
        username = self.username
        password = self.password
        try:
            if self.ssh_key:
                ssh.connect(self.host,
                            port=self.port,
                            username=username,
                            password=password,
                            timeout=self.timeout)
            else:
                ssh.connect(self.host,
                            port=self.port,
                            username=username,
                            password=password,
                            timeout=self.timeout,
                            allow_agent=False,
                            look_for_keys=False)
            self.ssh = ssh
            self.retry = 0
            return True
        except paramiko.BadHostKeyException, except_err:
            self.__disconnect()
            raise
        except paramiko.AuthenticationException, except_err:
            self.__disconnect()
            raise
        except paramiko.SSHException or socket.error, except_err:
            if (self.retry < 11):
                print "DEBUG: Connection failed, retrying connection {0} of 10".format(self.retry)
                time.sleep(5)
                self.__disconnect()
                return self.__connect(username, password)
            else:
                self.__disconnect()
                raise
        except Exception as except_err:
            print "Error connecting to node on {0}: {1}".\
                format(self.host, str(except_err))
            if (self.retry < 11):
                print "DEBUG: Retrying connection {0} of 10".format(self.retry)
                time.sleep(5)
                self.__disconnect()
                return self.__connect(username, password)
            else:
                self.__disconnect()
                raise


    def __disconnect(self):
        """Close the paramiko.SSHClient
        """
        if self.ssh:
            try:
                self.ssh.close()
                self.ssh = None
            except Exception as except_err:
                print "Error disconnecting: {1}".\
                    format(str(except_err))
                self.ssh = None
        else:
            self.ssh = None

    def run_command(self, cmd, username=None, password=None, logs=True):
        """Run command on node
           stdout, stderr, rc (list, list, integer)
        """

        if logs:
            print "[{0}@{1}]# {2}".format(self.username,
                                              self.ipv4, cmd)

        stdout, stderr, exit_code = self.execute(
            cmd, username, password, logs=logs)

        return stdout, stderr, exit_code

                    
    def execute(self, cmd, username=None, password=None, logs=True):
        """
        Test
        """
        username = self.username
        password = self.password
        if not self.ssh:
            self.__connect(username, password)
        if self.ssh:
            
            #print "#####DEBUG#### BEFORE OPENSESSION"
            channel = self.ssh.get_transport().open_session()
            #print "#####DEBUG#### BEFORE SETTIMEOUT"
            channel.settimeout(self.session_timeout)
            try:
                #print "#####DEBUG#### BEFORE RUNNING COMMAND: ", cmd
                channel.exec_command(cmd)
                #print "#####DEBUG#### COMMAND EXECUTED"
                contents = StringIO.StringIO()
                #print "#####DEBUG#### contents: ", contents.getvalue()
                errors = StringIO.StringIO()
                #print "#####DEBUG#### errors: ", errors.getvalue()

                timed_out = False
                returnc = channel.recv_exit_status()

                while (True):

                    if channel.recv_ready():
                        #print "#####DEBUG#### ENTERED STOUT LOOP"
                        data = channel.recv(self.out_bufsize)
                        while data:
                            #print "#####DEBUG#### before data received is: ", data
                            contents.write(data)
                            data = channel.recv(self.out_bufsize)
                            #print "#####DEBUG#### data received is: ", data

                        #print "#####DEBUG#### LEFT WHILE LOOP"
                        break
                    if channel.recv_stderr_ready():
                        error = channel.recv_stderr(self.err_bufsize)
                        while error:
                            #print "#####DEBUG#### before error received is: ", error
                            errors.write(error)
                            error = channel.recv_stderr(self.err_bufsize)
                            #print "#####DEBUG#### error received is: ", error

                        break

                    # After timeout we do one more loop to check
                    # if output buffers are ready and then we exit
                    if timed_out:
                        break

                    if not timed_out:
                        time.sleep(self.execute_timeout)
                        timed_out = True
                #print "#####DEBUG#### FINISHED OVERALL WHILE LOOP"

            except socket.timeout, except_err:
                print 'Socket timeout error: {0}'.format(except_err)
                raise
            finally:
                if channel:
                    channel.close()

            if logs:
                print contents.getvalue()
                print errors.getvalue()
                print returnc

            out = self.__process_results(contents.getvalue())
            err = self.__process_results(errors.getvalue())

            self.__disconnect()

        return out, err, returnc

    def __process_results(self, result):
        """
        Test
        """
        processed = []
        for item in result.split('\n'):
            if item.strip():
                processed.append(item.strip())

        return processed

    def run_command_local(self, cmd, logs=True):
        """
        """
        if logs:
            print "[local]# {0}".format(cmd)

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)

        result = child.communicate()

        if logs:
            print result[0]
            print result[1]
            print child.returncode

        exit_code = child.returncode
        stdout = result[0].splitlines()
        stderr = result[1].splitlines()

        return stdout, stderr, exit_code

    def copy_file(self, local_filepath, remote_filepath):
        """
        Copy a file to the node using paramiko.SFTP
        """

        #stdout, _, _ = self.run_command_local("hostname -i", logs=False)
        #if stdout[0] == "10.44.86.30":
        #    self.run_command_local("expect %s/copy_file.exp %s %s %s %s %s" \
        #        % (os.path.dirname(os.path.realpath(__file__)), self.ipv4, \
        #        self.username, self.password, local_filepath, remote_filepath))
        #else:
        if not self.ssh:
            self.__connect()

        if self.ssh:

            try:
                sftp_session = self.ssh.open_sftp()
                sftp_session.put(local_filepath, remote_filepath)
            except IOError, except_err:
                raise
            finally:
                self.__disconnect()

    def copy_file_from(self, remote_filepath, local_filepath):
        """
        Copy a file to the node using paramiko.SFTP
        """
        if not self.ssh:
            self.__connect()

        if self.ssh:

            try:
                sftp_session = self.ssh.open_sftp()
                sftp_session.get(remote_filepath, local_filepath)
            except IOError, except_err:
                raise
            finally:
                self.__disconnect()

    def check_service(self, service_name):
        """
        Run a check on a service against a node
        """

        cmd = "/sbin/service %s status" % service_name
        stdout, stderr, retc = self.run_command(cmd)
        if retc != 0:
            print ">> ERROR: SERVICE '%s' IS NOT RUNNING" % service_name
            return False
        return True

    def run_interactive_cmds(self, cmd, expect_outp, list_interaction, timeout=2, logs=False):
        """
        Pass a cmd and list of expected interactive cmds and results
        """

        try:
            if logs:
                print "-> Running: %s" % cmd
            child = pexpect.spawn(cmd)
            time.sleep(timeout)
            child.expect(expect_outp)
            if logs:
                print child.before
                print child.after
            for line in list_interaction:
                if logs:
                    print "-> Sending: %s" % line[0]
                child.sendline(line[0])
                if len(line) == 3:
                   child.expect(line[1], timeout=int(line[2]))
                else:
                    child.expect(line[1], timeout=120)
                if logs:
                    print child.before.splitlines()[1:-1]
                    print child.after.splitlines()[1:-1]
                time.sleep(1)

            if child.isalive():
            # Try to ask ftp child to exit
                child.sendline('Closing connection') 
                child.close()
            if child.isalive():
                # Try to ask ftp child to exit.
                child.sendline('Closing connection')
                print "Did not close the first time"
                child.close()
            if child.isalive():
                print "Did not close the second time"
            return True

        except Exception, e:
            print "ERROR FROM EXPECT"
            return False

    def handle_run_command(self, cmd, expected_stdout="empty", expected_stderr="empty", 
            expected_retc=0, username=None, password=None, logs=True):
        """
        Assert/return if command does not behave as expected
        """

        success = False
        stdout, stderr, retc = self.run_command(cmd, username, password, logs)
        if expected_stdout == "empty":
            if stdout == []:
                success = True
        else:
            if stdout != []:
                success = True

        if expected_stderr == "empty":
            if stderr != []:
                success = False
        else:
            if stderr == []:
                success = False
            
        if expected_retc == 0:
            if retc != 0:
                success = False
        else:
            if retc == 0:
                success = False

        return success

    def is_node_pingable(self):
        """
        Performs a ping from the local machine to the ms
        and returns true if it can be pinged or False otherwise.
        """
        ping_cmd = "/bin/ping {0} -c1".format(self.ipv4)

        _, _, exit_code = self.run_command_local(ping_cmd)

        if exit_code == 0:
            return True

        return False

    def waitfor_litp_plan(self, try_attempts, sleepfor, initial_sleep=1, print_error=True):
        """
        Wait for a litp plan to stop running and return true if successful
        """

        # NOW MONITOR THE PLAN

        time.sleep(initial_sleep)

        start_try = 0
        failed_ping_count = 0

        while start_try < try_attempts:
            if not self.is_node_pingable:
                time.sleep(sleepfor)
                failed_ping_count += 1
                if failed_ping_count == 5:
                    print ">> ERROR: NODE IS UNREACHABLE"
                    return False
                continue

            start_try += 1
            cmd = "/usr/bin/litp show_plan | /usr/bin/tail -3"
            stdout, stderr, retc = self.run_command(cmd)
            if stdout == [] or stderr != [] or retc != 0:
                print ">> ERROR: PLAN COMMAND ON HOST"
                return False
            if "Plan Status: Failed" in stdout[-1]:
                #print ">> WARNING: PLAN FAILED - IGNORING UNTIL TIMEOUT IS REACHED"
                if print_error:
                    print ">> ERROR: PLAN FAILED"
                else:
                    print ">> WARNING: PLAN FAILED"
                break
            if "Plan Status: Successful" in stdout[-1]:
                break
            time.sleep(sleepfor)

        # NOW CHECK PLAN IS COMPLETE AND ALL TASKS ARE COMPLETE WITH SUCCESS

        cmd = "/usr/bin/litp show_plan | /usr/bin/tail -3"
        stdout, stderr, retc = self.run_command(cmd)
        if stdout == [] or stderr != [] or retc != 0:
            print ">> ERROR: PLAN COMMAND FAILED ON HOST"
            return False
        if "Plan Status: Running" in stdout[-1]:
            cmd = "/usr/bin/litp show_plan"
            self.run_command(cmd)
            print ">> ERROR: Plan is running over the given timeout period"
            return False
        if "Plan Status: Successful" not in stdout[-1]:
            cmd = "/usr/bin/litp show_plan"
            self.run_command(cmd)
            if print_error:
                print ">> ERROR: PLAN FAILED"
            else:
                print ">> WARNING: PLAN FAILED"
            return False

        # SHOW PLAN FOR INFORMATION

        cmd = "/usr/bin/litp show_plan"
        if not self.handle_run_command(cmd, expected_stdout=""):
            print ">> ERROR: PLAN COMMAND FAILED ON HOST"
            return False

        return True

    def run_expects_commands(self, node, cmd, expects_list, timeout_secs=15):
        """
        Run interactive commands
        """

        stdout, stderr, returnc = node.execute_expects(cmd, expects_list, timeout_param=timeout_secs)

        print '\n'.join(stdout)
        print '\n'.join(stderr)
        print returnc

        if stdout == []:
            return False
        if stderr != []:
            return False
        if returnc != 0:
            return False

        #return stdout, stderr, returnc
        return True


    def execute_expects(self, cmd, expects_list, timeout_param=15, logs=True):
        """
        Run interactive commands
        """
        username = self.username
        password = self.password
        if not self.ssh:
            self.__connect(username, password)

        if self.ssh:
            #2. Get transport channel
            channel = self.ssh.get_transport().open_session()
            channel.settimeout(self.session_timeout)
            channel.get_pty()

            data = None
            error = None

            try:
                #3. Execute command on channel
                channel.exec_command(cmd)
                print "[{0}@{1}]# {2}".format(username,
                                              self.ipv4, cmd)

                contents = StringIO.StringIO()
                errors = StringIO.StringIO()

                #We loop through the expects dict list in order
                expects_index = 0
                items_to_send = True
                timeout_loop = 0

                while(True):
                    #To avoid exiting to early sleep to allow time to receive
                    #data into channel
                    time.sleep(self.execute_timeout)

                    #If we have been through all items in the expects list
                    #  don't send any more items
                    if expects_index >= len(expects_list):
                        items_to_send = False

                    timeout_loop += 1

                    #4. Reset send_data flag to false
                    #If it is still False at the end of the loop we know no
                    #data has been sent so will leave the loop.
                    #(if no data is sent we should not wait for a response)
                    send_data = False

                    #5. If stdout reports data ready
                    if channel.recv_ready():
                        #5a. Receive data from channel
                        data = channel.recv(self.out_bufsize)

                        contents.write(data)
                        #contents.write("\n")

                        processed_output = \
                            self.__process_results(contents.getvalue())

                        if items_to_send:
                            #5b. Convert stdout to list
                            processed_output = \
                                self.__process_results(contents.getvalue())
                            #5c. Loop through stdout in reverse order
                            # This means we consider response to most recently
                            # returned output first
                            time.sleep(1)
                            for output_line in reversed(processed_output):
                                #5d. If an output line is found matching the
                                #next prompt key in our expect list send the
                                #response key
                                expects_item = expects_list[expects_index]
                                if expects_item['prompt'] \
                                        in output_line:
                                    channel.send(expects_item['response']
                                                     + "\n")

                                    if "assword" in output_line:
                                        response = "*" * len(\
                                            expects_item['response'])
                                    else:
                                        response = expects_item['response']

                                    if not "exit" in response:
                                        print "{0} {1}".format(output_line,
                                                               response)

                                    send_data = True
                                    expects_index += 1
                                    break

                        #5e. If no data has been sent break as we expect
                        # not more responses from channel
                    if not send_data:
                        #We break only when expects timeout is reached
                        current_wait_time = timeout_loop * \
                            self.execute_timeout
                        if current_wait_time > timeout_param:
                            break

                    #6. If stderr has received data
                    if channel.recv_stderr_ready():

                        #6a. Receive data from channel
                        error = channel.recv_stderr(self.err_bufsize)
                        errors.write(error)
                        #errors.write("\n")

                        if items_to_send:
                            #6b. Convert stdout to list
                            processed_output = \
                                self.__process_results(errors.getvalue())

                            #6c. Loop through stdout in reverse order
                            # This means we consider response to most recently
                            # returned output first
                            for output_line in reversed(processed_output):
                                #6d. If an output line is found matching the
                                #next prompt key in our expect list send the
                                #response key
                                expects_item = expects_list[expects_index]
                                if expects_item['prompt'] \
                                        in output_line:
                                    channel.send(expects_item['response']
                                                     + "\n")

                                    if "assword" in output_line:
                                        response = "*" * len(\
                                            expects_item['response'])
                                    else:
                                        response = expects_item['response']

                                    if not "exit" in response:
                                        print "{0} {1}".format(output_line,
                                                               response)

                                    send_data = True
                                    expects_index += 1
                                    break

                    #6e. If no data has been sent break as we expect no more
                    #responses from channel
                    if not send_data:
                        #We break only when expects timeout is reached
                        current_wait_time = timeout_loop * \
                            self.execute_timeout

                        if current_wait_time > timeout_param:
                            break

                    #If channel exit status is ready and nothing
                    #in the streams is waiting to be written
                    if channel.exit_status_ready() \
                            and not channel.recv_ready() \
                            and not channel.recv_stderr_ready():
                        if not send_data:
                            break

                # Logs if prompt is missing
                if items_to_send:
                    print processed_output
                    print "Missing expected prompt: {0}".format(expects_list[expects_index]['prompt'])

                # channel.recv_exit_status() can hang forever
                # Check is rdy first or return -1 if not
                if channel.exit_status_ready():
                    returnc = channel.recv_exit_status()
                else:
                    returnc = "-1"

            except socket.timeout, except_err:
                print 'Socket timeout error: {0}'.format(except_err)
                raise
            finally:
                if channel:
                    channel.close()

            #7. Process return streams
            rawout = contents.getvalue()
            rawerr = errors.getvalue()

            rawout = rawout.replace(" \r", "")
            rawout = rawout.replace(" \t", "")
            rawerr = rawerr.replace(" \r", "")
            rawerr = rawerr.replace(" \t", "")

            # If line is not blank, add to list to return
            out = []
            for item in rawout.split('\n'):
                if item.strip():
                    out.append(item.strip())
            err = []
            for item in rawerr.split('\n'):
                if item.strip():
                    err.append(item.strip())

            for line in list(out):

                for item in expects_list:
                    # We cleanup output by removing all prompts & response keys
                    if item['prompt'] in line or item['response'] in line:
                        if line in out:
                            out.remove(line)

            for line in list(err):

                for item in expects_list:
                # We cleanup output by removing all prompts and response keys
                    if item['prompt'] in line or item['response'] in line:
                        if line in err:
                            err.remove(line)

            self.__disconnect()

        if logs:
            print "\n".join(out)
            print "\n".join(err)
            print returnc

        return out, err, returnc

    def get_expects_dict(self, prompt, response):
        """
        Get dict together
        """

        expects_dict = dict()
        expects_dict['prompt'] = prompt
        expects_dict['response'] = response

        return expects_dict

    def __get_su_root_expects(self, cmd):
        """Private method to create a list of expects commands
        which generates a dictionary for logging into the current node as su

        Args:
            cmd (str): The command to run under su rights

        Returns:
            A list of expects dictionary items
         """
        su_expects = list()

        su_expects.append(self.get_expects_dict("Password:",
                                                self.rootpw))
        su_expects.append(
            self.get_expects_dict("root@{0}".format(self.hostname),
                                  cmd))

        return su_expects

    def __get_root_exit_expects(self):
        """Returns a expects dictionary which performs an exit
        when logged in as root

        Returns:
           dict. An expects dictionary pair
        """
        return self.get_expects_dict("root@{0}".format(self.hostname),
                                     "exit")

    def run_su_root_cmd(self, cmd, timeout_secs=60):
        """
        Runs a command as root using the su command. Most useful
        for running root commands on the nodes.

        Returns:
            stdout, stderr, returnc
        """
        su_expects = self.__get_su_root_expects(cmd)
        su_expects.append(self.__get_root_exit_expects())

        return self.execute_expects("su", su_expects, timeout_secs)
