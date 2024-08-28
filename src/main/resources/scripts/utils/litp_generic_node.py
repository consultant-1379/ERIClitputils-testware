"""
LITP Generic Node
"""

import paramiko
import time
import socket
import StringIO
from litp_generic_utils import GenericUtils
import logging
import threading


class GenericNode(object):
    """Abstraction of a node which we try to connect to.

    .. note::
       This will be instantiated from :class:`GenericCluster`
    """

    def __init__(self):
        """Initialization of properties only.
        """
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        self.ipv4 = None
        self.username = None
        self.password = None
        self.ipv6 = None
        self.hostname = None
        self.host = None
        self.ssh = None
        self.nodetype = None
        self.filename = None
        self.rootpw = None
        self.vips = dict()
        self.port = 22
        self.rhelver = None
        # Timeout for establishing ssh connection
        self.timeout = 10
        self.retry = 0
        ##The amount of times execution has been retried
        self.execute_retry = 0
        # stdout and stderr buffer size, modify if necessary
        self.out_bufsize = 4096
        self.err_bufsize = 4096
        # 60 seconds timeout for I/O channel operations
        self.session_timeout = 60
        # Timeout to wait for output after execution of a cmd
        self.execute_timeout = 0.25
        ##Keeps track if active connection is root
        self.root_connected = True
        self.refresh_epoch_time = self.__get_current_epoch()
        self.last_connect_time = self.__get_current_epoch()
        self.g_util = GenericUtils()
        self.kill_connection_time = 600

    @staticmethod
    def __get_current_epoch():
        """
        Returns the current epoch time.

        Returns:
            int. The current epoch time.

        """
        return time.time()

    def is_initialised(self):
        """Checks whether required parameters have been set for this node.
        Required parameters are: ipv4 or ipv6, username, password and nodetype.
        These values should be present in the connection files.

        Returns:
            bool. False if any of the required parameters are
                None, or True otherwise.

        """
        # Either ipv4 or ipv6 must be set
        if not self.ipv4:
            if not self.ipv6:
                self.g_util.log('error', 'IP address not set on node')
                return False

        if not self.username:
            self.g_util.log('error', 'Username not set on node')
            return False

        if not self.password:
            self.g_util.log('error', 'Password not set on node')
            return False

        if not self.nodetype:
            self.g_util.log('error', 'Node type not set on node')
            return False

        if not self.hostname:
            self.g_util.log('error', 'Hostname not set on node')
            return False

        return True

    def __connect(self, username=None, password=None, ipv4=True):
        """Connect to a node using paramiko.SSHCLient

        Args:
            username (str): username to override.

            password (str): password to override.

            ipv4 (bool): Switch between ipv4 and ipv6.

        Raises:
            BadHostKeyException, AuthenticationException,
                SSHException, Exception
        """
        self.retry += 1

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if ipv4:
            self.host = self.ipv4
        else:
            self.host = self.ipv6
        if not username:
            username = self.username
        if not password:
            password = self.password
        try:
            ssh.connect(self.host,
                        port=self.port,
                        username=username,
                        password=password,
                        timeout=self.timeout)
            self.ssh = ssh
            self.retry = 0

            if username == "root":
                self.root_connected = True
            else:
                self.root_connected = False

            return True
        except paramiko.BadHostKeyException, except_err:
            self.__disconnect()
            self.g_util.log('error', 'Host key could not be ' +
                                  'verified: %s' % str(except_err))
            raise
        except paramiko.AuthenticationException, except_err:
            self.__disconnect()
            self.g_util.log('error', 'Unable to authenticate: %s' %
                                  str(except_err))
            raise
        except (paramiko.SSHException, socket.error), except_err:
            if self.retry < 2:
                time.sleep(5)
                self.__disconnect()
                return self.__connect(username, password, ipv4)
            else:
                self.__disconnect()
                self.g_util.log('error', 'Too many times to connect: %s'
                                      % str(except_err))
                raise
        except Exception as except_err:
            print "Error connecting to node on {0}: {1}".\
                format(self.host, str(except_err))

            raise

    def disconnect(self):
        """
        Globally visible disconnect method.
        """
        self.__disconnect()

    def __disconnect(self):
        """Close the paramiko SSHClient.
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

    @staticmethod
    def __process_results(result, username):
        """Process the execute command, removes sudo string and
        splits string into list.

        Args:
            result (str): stdout or stderr from execute.

            username (str): username which was used to execute the command.

        Returns:
            list. The results with newline/tab characters removed.
        """
        processed = []
        result = result.replace("[sudo] password for {0}:".format(username),
                                "")

        result = result.replace(" \r", "")
        result = result.replace(" \t", "")

        # If line is not blank, add to list to return
        for item in result.split('\n'):
            if item.strip():
                processed.append(item.strip())

        return processed

    @staticmethod
    def __clean_expects_prompts(data, expects_list):
        """
        Strips prompts and responses from expects list.

        Args:
            data (list): The processed data to strip out lines from.

            expects_list (list): The expects prompt/response dict.

        Returns:
            list. The data as a list.
        """
        for line in list(data):

            for item in expects_list:
                # We cleanup output by removing all prompts & response keys
                if item['prompt'] in line or item['response'] in line:
                    if line in data:
                        data.remove(line)

        return data

    def __get_su_root_expects(self, cmd):
        """Private method to create a list of expects commands which
        generates a dictionary for logging into the current node as su.

        Args:
            cmd (str): The command to run under su rights.

        Returns:
            list. Expects dictionary items.
         """
        su_expects = list()

        su_expects.append(self.g_util.get_expects_dict("Password:",
                                                             self.rootpw))
        su_expects.append(
            self.g_util.get_expects_dict("root@{0}".format(self.hostname),
                                               cmd))

        return su_expects

    def __get_root_exit_expects(self):
        """Returns an expects dictionary which
        performs an exit when logged in as root.

        Returns:
            dict. An expects dictionary pair.
        """
        return self.g_util.\
            get_expects_dict("root@{0}".format(self.hostname),
                             "exit")

    def execute_su_root(self, cmd, timeout):
        """Private method which executes a command
        under su using the expects dictionary.

        Args:
            cmd (str): The command to run under su.

            timeout (int): Timeout in seconds.

        Returns:
            list, list, rc. stdout, stderr, returncode
                of all the expect commands run.
        """
        su_expects = self.__get_su_root_expects(cmd)
        su_expects.append(self.__get_root_exit_expects())

        return self.execute_expects("su", su_expects, timeout_param=timeout)

    @staticmethod
    def __cmd_gens_large_stdout(cmd):
        """
        Check if the cmd being run has potential to generate
        large stdout stream. In these cases, cmd should be run with
        execute_expects method due to bugs in paramiko which can lock
        the channel when run normally.

        Args:
            cmd (str): The command to check.

        Returns:
            bool. True if command passed contains a cmd which is known to
                generate large stdout streams.
      """
        cmds_gen_stdout = ['xmllint']

        for cmd_value in cmds_gen_stdout:
            if cmd_value in cmd:
                return True

        return False

    def __setup_connection(self, username, password, ipv4):
        """
        Configures the SSH connection if not yet set up.

        Args:
            username (str): username used to execute the command.

            password (str): password used to execute the command.

            ipv4 (bool): Use ipv4.

        Returns:
            str, str. Username and password used in connection.
        """
        ##Kill connection if it was last used over 10 minutes ago, SSH has
        #likly died
        timeout_secs = 600
        now_time = self.__get_current_epoch()
        before_time = now_time - timeout_secs

        if before_time > self.last_connect_time:
            print "DISCONNECT NOW"
            #self.__disconnect()

        self.last_connect_time = self.__get_current_epoch()

        if not username:
            username = self.username
        if not password:
            password = self.password

        details_match = True

        if self.root_connected and\
                'root' not in username:
            details_match = False

        if username != self.username \
                or password != self.password:

            if self.root_connected \
                    and 'root' in username:
                details_match = True
            else:
                details_match = False

        ##in rare case not ipv4 just reconnect new each time
        if not self.ssh or not ipv4:
            self.__connect(username, password, ipv4)
        ##if we are already connect but not with the details being passed in
        elif not details_match:
            self.__disconnect()
            self.__connect(username, password, ipv4)

        return username, password

    def __receive_expects_data(self, channel, contents, items_to_send,
                               expects_list, expects_index, username):
        """
        Receives data from the channel and if a matching prompt is found, sends
        the matched response back down the channel.

        Args:
            channel (channel): The data channel in question.

            contents (StringIO): The IO stream to append data to.

            items_to_send (bool): False if there is no more data to send down
                the channel or True otherwise.

            expects_list (list): A list of prompt-response dictionary pairs.

            expects_index (int): The current position in the expects_list.

            username (str): Current username.

        Returns:
            bool, int, StringIO. Flag set to True if data has been sent down
                the channel, the current index in the expects list and
                    the contents of data received from the channel.
        """
          #5. If stdout reports data ready
        data = None
        #contents = StringIO.StringIO()
        send_data = False

        if channel.recv_ready():
                        #5a. Receive data from channel
            data = channel.recv(self.out_bufsize)

            contents.write(data)

            processed_output = \
                self.__process_results(contents.getvalue(),
                                       username)

            if items_to_send:
                            #5b. Convert stdout to list
                processed_output = \
                    self.__process_results(contents.getvalue(),
                                                       username)
                            #5c. Loop through stdout in reverse order
                            # This means we consider response to most recently
                            # returned output first
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
                            response = "*" * len(expects_item['response'])
                        else:
                            response = expects_item['response']

                        if not "exit" in response:
                            print "{0} {1}".format(output_line,
                                                   response)

                        send_data = True
                        expects_index += 1
                        break

        return send_data, expects_index, contents

    def __receive_expects_stderr(self, channel, errors, items_to_send,
                                 expects_list, expects_index, username):
        """
        Receives data from the stderr channel and if a matching prompt is
        found, sends the matched response back down the channel.

        Args:
            channel (channel): The data channel in question.

            errors (StringIO): The string IO stream to append to.

            items_to_send (bool): False if there is no more data to send down
                the channel or True otherwise.

            expects_list (list): A list of prompt-response dictionary pairs.

            expects_index (int): The current position in the expects_list.

            username (str): Current username.

        Returns:
            bool, int, StringIO. Flag set to True if data has been sent down
                the channel, the current index in the expects list and the
                    contents of data received from the stderr channel.
        """
        error = None
        #errors = StringIO.StringIO()
        send_data = False

          #6. If stderr has received data
        if channel.recv_stderr_ready():

                        #6a. Receive data from channel
            error = channel.recv_stderr(self.err_bufsize)
            errors.write(error)
                        #errors.write("\n")

            if items_to_send:
                            #6b. Convert stdout to list
                processed_output = \
                    self.__process_results(errors.getvalue(),
                                           username)

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

        return send_data, expects_index, errors

    def __is_timeout_reached(self, timeout_loop, send_data, timeout_param):
        """
        If no data has been sent down the channel and the timeout is reached,
        return True, otherwise return False.

        Args:
            timeout_loop (int): How many times have we
                looped through to get data.

            send_data (bool): Have we sent data to the
                channel on the most recent loop.

            timeout_param (int): Time to wait for command in seconds.

        Return:
            bool. True if timeout reached or False otherwise.
        """

        if not send_data:
            # We break only when expects timeout is reached
            current_wait_time = timeout_loop * \
                self.execute_timeout

            if current_wait_time > timeout_param:
                return True

        return False

    @staticmethod
    def __get_exit_status(channel):
        """
        Returns the exit status for the channel or -1 if the channel
        exit status is not ready.

        Args:
            channel (channel): The data channel.

        Return:
            int. The channel exit status.
        """
        # If the exit status is not ready the channel may hang forever
        # so we need to check before calling recv_exit_status
        if channel.exit_status_ready():
            return channel.recv_exit_status()
        else:
            return -1

    def __receive_data(self, channel, contents):
        """
        Polls the channel for data and returns contents
        when data is found.

        Args:
            channel (channel): The channel to poll data from.

            contents (StringIO): The IO stream to append data to.

        Return:
            bool, StringIO. Boolean which is True if data was found or
            False otherwise, and the data in a StringIO buffer.
        """
        has_data = False
        data = None

        if channel.recv_ready():
            data = channel.recv(self.out_bufsize)

            while data:
                contents.write(data)
                data = channel.recv(self.out_bufsize)

        if data:
            has_data = True

        return has_data, contents

    def __receive_stderr(self, channel, errors):
        """
        Polls the channel for error data and returns contents
        when errors are found.

        Args:
            channel (channel): The channel to poll data from.

            errors (StringIO): The IO stream to append data to.

        Return:
            bool, StringIO. Boolean which is True if error was found or
            False otherwise, and the errors in a StringIO buffer.
        """
        has_error = False
        error = None

        if channel.recv_stderr_ready():
            error = channel.recv_stderr(self.err_bufsize)
            while error:
                errors.write(error)
                error = channel.recv_stderr(self.err_bufsize)

        if error:
            has_error = True

        return has_error, errors

    def __track_connection(self):
        """Kills the connection if a hung condition is detected.

        Some paramiko operations are liable to hang forever during
        the execute method if there is a connection loss.

        This method will automatically disconnect the channel if a timestamp
        environment variable is not updated after a timeout period.
        This timeout period should be updated at the start and end of
        each execute method so if it has not been updated, it indicates the
        connection has hung.
        """
        ##Gets the current epoch time
        time_started = self.__get_current_epoch()
        #Time to sleep between polling.
        #This should be kept relativly low or you could have threads hanging
        #left around.
        sleep_time = self.execute_timeout
        time_passed = 0
        ##Currently set at 10 minutes
        while True:
            ##Keep track of current time passed
            time.sleep(sleep_time)
            time_passed += sleep_time

            #The instance variable is updated at the end of the execute method
            ##with the current time.
            ##If the current time is greater than the time this thread was
            ##started we know execute method has finished.
            ##Also if SSH connection has been closed due to end of test
            #disconnect we exit
            if self.refresh_epoch_time > time_started or not self.ssh:
                ##Leaving the loop will cause the Thread to exit
                break

            ##If time passed is greater than session tiemout
            ##it indicates the execute method has taken more than the session
            #timeout to complete.
            ##In this case it is assumed to have locked so a reconnection will
            ##be performed.
            if time_passed > self.kill_connection_time:
                self.g_util.log('error',
                                "Connection interruption detected.")
                ##Calling disconnect clears the main thread if it has hung
                self.__disconnect()
                self.__connect()
                break

    def __start_connection_check_thread(self):
        """
        Starts a thread which will perform a
        disconnect if the execute method hangs.
        """
        #As channel may not have fully closed since last command
        #we may potenially have up to 3 threads already
        #(main + 2 paramiko channels)
        #Therefore allow up to 4 threads
        allowed_threads = 4

        #If we are retrying a connection add an extra thread
        if self.execute_retry > 1:
            allowed_threads += 1

        if threading.active_count() < allowed_threads:

            thread_test = \
                threading.Thread(target=self.__track_connection,
                                 args=())
            thread_test.start()

    def execute(self, cmd, username=None, password=None, ipv4=True, sudo=False,
                su_root=False, su_timeout=60, execute_timeout_secs=0.25,
                connection_timeout_secs=600, return_immediate=False):
        """Executes one command in channel to get
        larger outputs and returns processed results.

        Args:
            cmd (str): Command to execute.

        Kwargs:
            username (str): username used to execute the command.

            password (str): password used to execute the command.

            ipv4 (bool): Set to True to use ipv4.

            sudo (bool): Running privileged command.

            su_root (bool): Run commands as root (from litp-admin).

            su_timeout (int): Default timeout values to
                wait for su commands to return.

            execute_timeout_secs (float): If set, changes the execute timeout
                from the default. That is, the time the channel waits in
                    seconds after executing a command before polling for
                        data. Default is 0.25 seconds.

            connection_timeout_secs (int): Time to wait for command to finish
                before exiting with an error. Default is 600 seconds (10 mins).


            return_immediate (bool): Returns immediately after executing
                                     the command without waiting for command
                                     to return. Only works when su_root is
                                     not set.

        Returns:
            list, list, int. std_out, std_err, and return code of the command.
        """
        channel = None

        ##Create a thread to check connection
        self.kill_connection_time = connection_timeout_secs
        now_time = self.__get_current_epoch()
        before_time = now_time - 600

        if before_time > self.refresh_epoch_time:
            self.__disconnect()

        self.refresh_epoch_time = self.__get_current_epoch()
        self.__start_connection_check_thread()

        self.execute_timeout = execute_timeout_secs
        username, password = self.__setup_connection(username,
                                                     password,
                                                     ipv4)

        if self.ssh:
            if su_root:
                return self.execute_su_root(cmd, su_timeout)
            ##If cmd is known to generate large stdout run with expects
            elif self.__cmd_gens_large_stdout(cmd):
                ##Due to large stdout we double timeout allowed.
                timeout = su_timeout * 2
                return self.execute_expects(cmd, [],
                                            timeout_param=timeout)
            else:
                try:
                    channel = self.ssh.get_transport().open_session()
                    channel.settimeout(self.session_timeout)

                    if sudo:
                        channel.get_pty()
                        cmd = '/bin/echo %s | /usr/bin/sudo -S %s' % \
                          (password, cmd)

                    data = False
                    error = False

                    channel.exec_command(cmd)

                    #if requested to return stright after running command
                    if return_immediate:
                        return self.__return_immediate_processing(channel)

                    contents = StringIO.StringIO()
                    errors = StringIO.StringIO()

                    timed_out = False

                    # There are rare cases when recv_exit_status returns while
                    returnc = channel.recv_exit_status()
                    #self.__wait_for_channel(channel)

                    #returnc = channel.recv_exit_status()
                    # recv_ready is not yet ready.
                    # The below structure is designed so
                    # that if recv_ready does not return the loop
                    # will wait a defined execution timeout period
                    # before doing a final check and then leaving the loop.

                    while True:

                        data, contents = self.__receive_data(channel, contents)

                        error, errors = self.__receive_stderr(channel, errors)

                        # After timeout we do one more loop to check
                        # if output buffers are ready and then we exit
                        if data or error or timed_out:
                            break

                        if not timed_out:
                            time.sleep(self.execute_timeout)
                            timed_out = True

                except Exception, except_err:
                    self.g_util.log('error', 'Connection error: {0}'
                                    .format(except_err))

                    ##Retry the execution if we get a failure
                    if self.execute_retry < 1:
                        self.g_util.log('info', 'Retrying command')
                        self.__disconnect()
                        self.execute_retry += 1
                        return self.execute(cmd, username, password,
                                            ipv4, sudo, su_root,
                                            su_timeout, execute_timeout_secs)
                    raise

                finally:
                    #Gets return code of command
                    #returnc = self.__get_exit_status(channel)
                    ##Refresh the current epoch time
                    self.refresh_epoch_time = self.__get_current_epoch()
                    ##Reset execute_retry to 0
                    self.execute_retry = 0

                    if channel:
                        channel.close()

                out = self.__process_results(contents.getvalue(), username)
                err = self.__process_results(errors.getvalue(), username)

            return out, err, returnc

    def __return_immediate_processing(self, channel):
        """
        Processing related to returning immedietly after a command has been
        sent without waiting for it to return success. Used for robustness
        testing.

        Args (channel): The currently active channel where the command has been
        sent.

        Returns.
        [], [], -1.
        """
        count = 0
        while True:
            #We know command has fully be sent if we received
            #back from stdout. If after two loops nothing
            #received return anyway.
            if channel.recv_ready() \
                    or count > 2:
                self.refresh_epoch_time = self.__get_current_epoch()
                channel.close()

                return [], [], -1

            time.sleep(self.execute_timeout)
            count = count + 1

    def execute_expects(self, cmd, expects_list, username=None, password=None,
                        ipv4=True, su_root=False, timeout_param=60):
        """
        Runs a command and responds to responses received back using the
        expects_list of prompts and responses.

        Args:
            cmd (str): Command to execute.

            expects_list (list): A list of expect dicts created using the\
                get_expects_dict command.

        Kwargs:
            username (str): username used to execute the command.

            password (str): password used to execute the command.

            ipv4 (bool): Set to True to use ipv4.

            su_root (bool): Set to True to run command as root.

            timeout_param (int): Timeout to wait for command to return.


        Returns:
            list, list, int. std_out, std_err, and return code of the command.

            NB: The stderr channel will always be empty using this method due
            to use of a pty terminal which sendsall output back on the
            stdout channel.
        """
        self.g_util.log('info', 'Beginning expects execution')
        #1. Establish connection with node
        username, password = self.__setup_connection(username,
                                                     password,
                                                     ipv4)

        #if su_root command we add the su commands to the start
        # of the expects list
        if su_root:
            #original command is added to su expects dict
            su_root_expects = self.__get_su_root_expects(cmd)
            su_root_expects.extend(expects_list)
            expects_list = su_root_expects
            #we need to exit from su state when commands finished
            expects_list.append(self.__get_root_exit_expects())
            #override command as we wish to su first
            cmd = "su"

        if self.ssh:
            #2. Get transport channel
            channel = self.ssh.get_transport().open_session()
            channel.settimeout(self.session_timeout)
            channel.get_pty()

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

                while True:
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
                    send_data_stdout = False
                    send_data_stderr = False

                    send_data_stdout, expects_index, contents = \
                        self.__receive_expects_data(channel,
                                                    contents,
                                                    items_to_send,
                                                    expects_list,
                                                    expects_index,
                                                    username)

                    if self.__is_timeout_reached(timeout_loop,
                                                 send_data_stdout,
                                                 timeout_param):
                        break

                    send_data_stderr, expects_index, errors = \
                        self.__receive_expects_stderr(channel,
                                                      errors,
                                                      items_to_send,
                                                      expects_list,
                                                      expects_index,
                                                      username)

                    #6e. If no data has been sent break as we expect no more
                    #responses from channel
                    if self.__is_timeout_reached(timeout_loop,
                                                 send_data_stderr,
                                                 timeout_param):
                        break

                    #If channel exit status is ready and nothing
                    #in the streams is waiting to be written
                    if channel.exit_status_ready() \
                            and not channel.recv_ready() \
                            and not channel.recv_stderr_ready() \
                            and not send_data_stdout \
                            and not send_data_stderr:
                        break

                # Logs if prompt is missing
                if items_to_send:
                    self.g_util.log("error",
                                    "Missing expected prompt: {0}".format(
                                        expects_list[expects_index]['prompt']))

                # channel.recv_exit_status() can hang forever
                # Check is rdy first or return -1 if not
                returnc = self.__get_exit_status(channel)

            except Exception, except_err:
                self.g_util.log('error', 'Connection error: {0}'
                                      .format(except_err))
                raise
            finally:
                self.refresh_epoch_time = self.__get_current_epoch()
                if channel:
                    channel.close()

            #7. Process return streams
            raw_out = self.__process_results(contents.getvalue(), username)
            raw_err = self.__process_results(errors.getvalue(), username)

            ##Remove prompt and response keys from data
            out = self.__clean_expects_prompts(raw_out, expects_list)
            err = self.__clean_expects_prompts(raw_err, expects_list)

            #self.__disconnect()

        self.g_util.log('info', 'Ending expects execution')

        return out, err, returnc

    def copy_file(self, local_filepath, remote_filepath, root_copy,
                  file_permissions=0777):
        """
        Copy a file to the node using paramiko.SFTP
        Will provide a remote file name equal to the local filename if
        a filename is not provided in the remote path.

        Args:
            local_filepath (str): Path of the local file to copy.

            remote_filepath (str): Path of the remote file to paste to.

            root_copy (str): If set to True, copies as root user.

        Kwargs:
            file_permissions (int): Permissions to set for copied file using
                chmod notation. Defaults to 0777.

        Raises:
            IOError if filepaths are invalid.
        """
        #Permissions to give to files by default
        default_file_permissions = file_permissions

        if root_copy:
            self.__setup_connection("root", self.rootpw, True)
        else:
            self.__setup_connection(None, None, True)

        ###If we already have connection
        if self.ssh:
            ##if current connection is not root and we require root connection
            ##disconnect and reconnect as root
            if root_copy and not self.root_connected:
                self.__disconnect()
                self.__connect("root", self.rootpw)
        ##If we don't have a connection
        else:
            if root_copy:
                self.__connect("root", self.rootpw)
            else:
                self.__connect()

        if self.ssh:

            try:
                sftp_session = self.ssh.open_sftp()

                sftp_session.put(local_filepath, remote_filepath)
                sftp_session.chmod(remote_filepath, default_file_permissions)

            except IOError, except_err:
                self.g_util.log('error', 'File copy error: %s' %
                                      str(except_err))
                raise

    def create_dir(self, filepath):
        """Creates a directory at the given filepath.

        Args:
            filepath (str): The full path of the directory to be created.

        Returns:
            bool. True if directory creation is successful or False otherwise.
        """
        mkdir_cmd = "mkdir %s" % filepath
        _, err, returnc = self.execute(mkdir_cmd)
        if returnc == 0:
            return True

        self.g_util.log("error", "Error creating directory: %s" % err)

        return False

    def download_file(self, local_path, remote_path, root_copy):
        """
        Copy a file from a node to gateway using paramiko.SFTP.

        Args:
            local_path (str): Path to download file to.

            remote_path (str): Path of the remote file to download.

            root_copy (bool): If set to True, copies as root user.

        Raises:
            IOError if filepaths are invalid.
        """
        if root_copy:
            self.__setup_connection("root", self.rootpw, True)
        else:
            self.__setup_connection(None, None, True)

        ###If we already have connection
        if self.ssh:
            ##if current connection is not root and we require root connection
            ##disconnect and reconnect as root
            if root_copy and not self.root_connected:
                self.__disconnect()
                self.__connect("root", self.rootpw)
        ##If we don't have a connection
        else:
            if root_copy:
                self.__connect("root", self.rootpw)
            else:
                self.__connect()

        try:
            sftp_session = self.ssh.open_sftp()
            sftp_session.get(remote_path, local_path, callback=None)

        except IOError, except_err:
            self.g_util.log('error', 'File copy error: %s' %
                                      str(except_err))
            raise
