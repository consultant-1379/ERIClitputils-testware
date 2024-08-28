"""
LITP Generic Utils

Global logger variables used
"""
import logging.config
from os import path, listdir, environ
import datetime
import subprocess
import traceback
import json
import re
import time
import urllib2
from xml.dom import minidom
import test_constants

# Get absolute path to this file
LOG_FILEPATH = path.dirname(__file__)
# Use configuration file for logger
logging.config.fileConfig(path.join(LOG_FILEPATH, 'litp_logging.conf'))
# Use litp.test logger (logging to stdout "class=StreamHandler"
# can be easily changed to log to file "class=FileHandler")
LITP_LOGGER = logging.getLogger('litp.test')


class GenericUtils(object):

    """Generic Tools which do not require node connection.
    """

    def load_ms_usr_creds(self):
        """
        Loads the default MS username and password as stored
        in the connection data files.

        Returns:
           str, str. The default username and password files for the MS.
        """
        # slave is set up in Jenkins as environment variable to
        # distinguish between environments

        new_format = False
        if "LITP_CONN_DATA_FILE" in environ:
            # TMP hardcoding while TAF is developed
            con_data_path = environ['LITP_CONN_DATA_FILE']
            new_format = True
        elif "LITP_CON_DATA_PATH" in environ:
            con_data_path = environ['LITP_CON_DATA_PATH']
        else:
            con_data_path = '/opt/ericsson/SIT/connection_data_files/'

        if new_format:
            #print "NEW STUFF"
            return self.parse_taf_con_file(con_data_path)
        else:
            return self.parse_orig_format(con_data_path)

    @staticmethod
    def parse_orig_format(con_data_path):
        """Parses the original formatted connection data file.

        Args:
           con_data_path (str): The path to the connection data files.

        Returns:
            str, str. MS username and password.
        """
        slave = environ['LITP_SLAVE']
        fields = 7
        filepath = path.dirname(__file__)

        # relative path to connection data files depending on absolute path
        # to this file
        path_full = path.join(filepath, con_data_path)

        for item in listdir(path.join(path_full, slave)):
            with open(path.join(path_full, slave, item), 'r') as nodefile:
                for line in nodefile:
                    if not line.startswith('#'):
                        line = line.strip().strip('\n').split(',')
                        if line and len(line) == fields:
                            try:
                                if "ms" in item.lower():
                                    ms_username = line[1]
                                    ms_password = line[2]
                                    break

                            except Exception:
                                raise ValueError(
                                    """
                                        Processing: {fname}

                                        Please check your data conn files!
                                    """.format(fname=item))

        return ms_username, ms_password

    @staticmethod
    def parse_taf_con_file(con_data_path):
        """
        Read data from TAF format connection data files.

        Args:
           con_data_path (str): The path to the connection data files.

        Returns:
            str, str. MS username and password.
        """

        variable_list = list()

        # Load all variables into a dictionary list
        with open(con_data_path, 'r') as nodefile:
            for line in nodefile:
                # Ignore hash comments
                if not line.startswith('#'):
                    variable_dict = dict()
                    # Split variable between value and variable name.
                    # N.b. We limit the split as value may contain '=',
                    # e.g. in password
                    variable_parts = line.split("=", 1)
                    # If line contains no name/value parts, skip line
                    if len(variable_parts) < 2:
                        continue
                    variable_name = variable_parts[0]
                    variable_value = variable_parts[1]

                    variable_dict[variable_name] = variable_value
                    variable_list.append(variable_dict)

        hostname = None
        for variable in variable_list:
            for key, value in variable.iteritems():
                if ".type" in key and "MS" in value:
                    hostname = key.split(".")[1]
                    break

        for variable in variable_list:
            for key, value in variable.iteritems():
                if "user." in key and "user.root" not in key and\
                        hostname in key:
                    password = value.strip()
                    username = key.split(".")[3]
                    break

        return username, password

    def run_command_local(self, cmd, log=True):
        """Runs the given command from the machine the
        test is being run from.

        This is used by area classes such as rest,
        it is here rather than generic test.

        Args:
            cmd  (str): The command to be run.

        Kwargs:
            log (bool): Set to False to remove logging of command results.

        Returns:
            (list, list, integer): stdout, stderr, rc
        """

        if log:
            self.log_now()
            print "[local]# {0}".format(cmd)

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)

        result = child.communicate()
        exit_code = child.returncode
        stdout = result[0].splitlines()
        stderr = result[1].splitlines()

        if log:
            print '\n'.join(stdout)
            print '\n'.join(stderr)
            print exit_code

        return stdout, stderr, exit_code

    @staticmethod
    def get_expects_dict(prompt, response):
        """Returns a prompt-response dictionary pair used in the
        run_expects_command method.

        Args:
            prompt (str): A prompt to expect when running a command.

            response (str): Response to send when the prompt is encountered.

        Returns:
            dict. A dictionary with two entries (prompt and response).
        """
        expects_dict = dict()
        expects_dict['prompt'] = prompt
        expects_dict['response'] = response

        return expects_dict

    @staticmethod
    def log(logtype, msg, *args, **kwargs):
        """Simple log wrapper for Python logger functions.

        Args:
           logtype  (str): Type of log message.
                           Supported types:
                           'info', 'warning', 'debug',
                           'error', 'critical'

           msg      (str): Message to log.

        Kwargs:
           args:    Keep compatibility with standard logger.

           kwargs:  Keep compatibility with standard logger.
        """
        case = {'info': LITP_LOGGER.info,
                'warning': LITP_LOGGER.warning,
                'debug': LITP_LOGGER.debug,
                'error': LITP_LOGGER.error,
                'critical': LITP_LOGGER.critical}
        return case[logtype](msg, *args, **kwargs)

    @staticmethod
    def log_now():
        """
        Print actual timestamp to console.
        """
        now = datetime.datetime.now()
        print "Current timestamp: {0}".format(str(now))

    @staticmethod
    def join_paths(path1, path2):
        """Joins two paths together ensuring only one '/'
        is used between them. Uses only str manipulation so
        can be used for filepaths or LITP paths.

        Args:
           path1  (str): The first path.

           path2  (str): The path to append.

        Returns:
            str. The two paths appended.
        """
        # Removes '/' symbol from each string
        if path1[-1] == '/':
            path1 = path1[:-1]
        if path2[0] == '/':
            path2 = path2[1:]

        # Adds '/'
        final_path = path1 + "/" + path2

        return final_path

    @staticmethod
    def cmd_has_error(cmd):
        """Checks rc is 0 and the error stream is an empty list.

        Args:
            cmd (dictionary): The result from running a command.

        Returns:
            bool. False if no error or True otherwise.
        """
        if cmd['rc'] == 0 and cmd['stderr'] == []:
            return False

        return True

    def no_errors(self, result):
        """Checks all return codes from the passed result dictionary
        and returns True if no errors are present or False otherwise.

        Args:
           result (dict): Dictionary of results from running multiple commands.

        Returns:
           bool. True if no errors found or False otherwise.
        """
        if not result:
            raise ValueError("Received empty 'result' dict!")

        for node_index in result.iterkeys():
            for cmd in result[node_index].itervalues():
                if self.cmd_has_error(cmd):
                    return False

        return True

    def get_errors(self, result):
        """Loops through a result dictionary and returns a
        list of commands (ref by number) which reported errors.

        Args:
           result (dict): Result dictionary returned from running
                          multiple commands.

        Returns:
           list. A list of commands which returned errors (ref by number).
        """
        if not result:
            raise ValueError("Received empty 'result' dict!")

        errors = []
        for node_index in result.iterkeys():
            for cmd in result[node_index].itervalues():
                if self.cmd_has_error(cmd):
                    errors.append(cmd)
        return errors

    def get_std_out_by_node(self, result, node):
        """Gets the std out from the result dictionary for
        all commands run on the specified node.

        Args:
           result  (dict): Result dictionary returned from running
                           multiple commands.
           node    (str): The node to filter by.

        Returns:
           std_out (list): A list of the standard:out returned for
                           each command ran.
        """

        std_out = []
        check_stdout = "stdout"

        if not node in result:
            self.log('error', "Node not found in result dictionary")
            return std_out
        else:
            for cmd in result[node]:
                std_out.append(result[node][cmd][check_stdout])

        return std_out

    @staticmethod
    def is_std_out_empty(result):
        """Returns True if all std out is empty for all commands
        in the result dictionary.

        Args:
           result  (dict): Result dictionary returned from running
                           multiple commands.

        Returns:
           bool. True if std_out is empty or False otherwise.
        """

        check_stdout = "stdout"

        for node in result:
            for cmd in result[node]:
                if result[node][cmd][check_stdout]:
                    return False

        return True

    @staticmethod
    def is_std_out_in_all(result):
        """Returns True if each commands returns something to std_out
        or False if at least one command returns nothing to std out.
        Useful when asserting grep commands all found their expected item.

        Args:
           result  (dict): Result dictionary returned from running
                           multiple commands.

        Returns:
           bool. True if all cmds contain std_out.
        """

        check_stdout = "stdout"

        for node in result:
            for cmd in result[node]:
                if not result[node][cmd][check_stdout]:
                    return False

        return True

    @staticmethod
    def is_text_in_list(text, list_item):
        """Checks to see if the text passed exists within
        any item in the list.

        Args:
           text      (str): The string to test for.

           list_item (list): The list to check.

        Returns:
            bool. True if item found or False otherwise.
        """
        if text is None:
            return False

        if text is "":
            raise ValueError(
                'Test string is is type {0} which is invalid: {1}'\
                    .format(type(text), text))

        if not isinstance(list_item, list):
            raise ValueError('Non-list item: {0}'\
                                 .format(list_item))

        for line in list_item:
            if text in line:
                return True

        return False

    @staticmethod
    def is_text_in_list_regex(pattern_obj, list_item):
        """Checks using a Regular Expression or RegexObject to see if the
        pattern exists within any item in the list.

        Args:
           pattern_obj (str)/(RegexObject): The Regular Expression, or compiled
           RegexObject to test for.

           list_item (list): The list to check.

        Returns:
            bool. True if item found or False otherwise.
        """
        if pattern_obj is None:
            return False

        if not isinstance(list_item, list):
            raise ValueError('Non-list item: {0}'.format(list_item))

        if isinstance(pattern_obj, type(re.compile("temp"))):
            for line in list_item:
                if pattern_obj.search(line):
                    return True
        else:
            for line in list_item:
                if re.search(pattern_obj, line):
                    return True

        return False

    @staticmethod
    def count_text_in_list(text, list_item):
        """Returns number of times a string exists in a list.

        Args:
           text      (str): The string to search for.

           list_item (list): The list to check.

        Returns:
            int. Number of times passed string exists in passed list.
        """
        count = 0

        if text is "":
            raise ValueError(
                'Test string is type {0} which is invalid: {1}'\
                    .format(type(text), text))

        if not isinstance(list_item, list):
            raise ValueError('Non-list item: {0}'\
                                 .format(list_item))

        for line in list_item:
            if text in line:
                count += 1

        return count

    @staticmethod
    def compare_lists(list1, list2, rtn_unique=True, get_all_unique=False):
        """Compares two lists and returns a new list depending on the
        flags passed in the parameter.

        Args:
           list1 (list): First list to test.

           list2 (list): Second list to compare against.

        Kwargs:
           rtn_unique (Boolean): If True, the list of unique items are
                                returned, otherwise the list of matching
                                items in the two lists are returned.

          get_all_unique (Boolean): If True, any item that is unique to either
                                list will be returned. Otherwise, only items
                                unique to the first list will be returned.

        Returns:
            If rtn_unique is False, returns all common items in
            the list as a list.

            If rtn_unique is True:
                If get_all_unique is True, returns all unique values
                found in list 1 or list 2.
                If get_all unique is False, returns all values in list 1 which
                are not in list2.
        """
        # Returns items in both list 1 and list 2
        if rtn_unique == False:
            return set(list1).intersection(list2)

        # Returns items that are in list1 but not list 2
        if get_all_unique:
            return set(list1).symmetric_difference(list2)
        # Returns items in either list1 or list2 but not both
        else:
            return set(list1).difference(list2)

    def load_json(self, json_data):
        """Attempts to load the passed string into JSON.

        Args:
            json_data (str): The JSON data to load.

        Returns:
            The data parsed to JSON or None if the JSON.loads fails.
        """
        try:
            return json.loads(json_data)

        except Exception, err:
            traceback.print_exc()
            self.log("error", "JSON is corrupt {0}".format(err))
            return None

    @staticmethod
    def get_filelist_dict(local_filepath, remote_filepath):
        """Returns a dictionary based on the local and remote paths
        passed to it.

        Args:
          local_filepath (str): The local filepath of the file to copy.

          remote_filepath (str): The filepath on the remote machine you
                                    wish to copy to.

        Returns:
            dict. Contains 'local_path' and 'remote_path' keys.
        """
        fileitem = dict()
        fileitem['local_path'] = local_filepath
        fileitem['remote_path'] = remote_filepath

        return fileitem

    @staticmethod
    def remove_unicode_from_dict(dict_item):
        """
        Removes unicode notation 'u' from a dict.
        Common use case is when processing JSON output.

        Args:
            dict_item (dict): The dictionary to process.

        Returns:
            dict. The same dictionary with unicode notation removed.
        """
        dict_item_converted = dict()

        for key, value in dict_item.items():
            dict_item_converted[str(key)] = str(value)

        return dict_item_converted

    @staticmethod
    def diffdates(date1, date2):
        """
        Determines the difference in seconds between the two dates.
        Can be useful when determining the time difference between two
        entries in /var/log/messages for example.

        Args:
            date1         (str): Line containing a date in format:
                                 %b %d %H:%M:%S
                                 E.G. Apr  7 17:25:20

            date2         (str): Line containing a date in format:
                                 %b %d %H:%M:%S
                                 E.G. Apr  7 17:25:20

        Returns:
            float. Time in seconds.
                   NOTE: A negative value means date2 is before date1.
        """
        match1 = re.search(r'\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}', date1)
        match2 = re.search(r'\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}', date2)
        timestamp1 = match1.group()
        timestamp2 = match2.group()

        return (time.mktime(time.strptime(timestamp2, "%b %d %H:%M:%S")) -
                time.mktime(time.strptime(timestamp1, "%b %d %H:%M:%S")))

    @staticmethod
    def __get_latest_version_in_nexus(group_id, artifact_id,
                                      repo='public'):
        """
        Returns the latest version of the requested item in nexus.

        Args:

           group_id (str): The group id of the item.

           artifact_id (str): The artiface id of the item.

        KWargs:

          repo (str): The nexus repo to lookup. Defaults to public.

        Returns:
          str. The latest version of the package in question or None if
          package could not be found.
        """
        #We want to get the latest
        version = 'RELEASE'
        print "Searching Nexus for {0}:{1}:{2} pom" \
            .format(group_id, artifact_id, version)
        url = "{0}/service/local/artifact/maven/redirect?r={1}" \
              "&g={2}&a={3}&p=pom&v={4}".format(test_constants.NEXUS_LINK,
                                                repo, group_id,
                                                artifact_id, version)
        print url

        response = urllib2.urlopen(url)
        html = response.read()

        xmldoc = minidom.parseString(html)

        # see if version is specified in the pom
        project = xmldoc.getElementsByTagName('project')[0]
        for node in project.childNodes:
            if node.nodeType == node.ELEMENT_NODE and \
               node.tagName == 'version':
                return node.firstChild.nodeValue

        # if we get this far the pom could be inheriting from parent
        parent = xmldoc.getElementsByTagName('parent')[0]
        for node in parent.childNodes:
            if node.nodeType == node.ELEMENT_NODE and \
               node.tagName == 'version':
                return node.firstChild.nodeValue

    def get_item_from_nexus(self, group_id, artifact_id,
                            version='RELEASE', filetype='rpm',
                            repo='public'):
        """
        Downloads the requested item from nexus to the local machine.

        Args:

         group_id (str): The group id of the item. (ie 'com.ericsson.nms.litp')

         artifact_id (str): The artiface id of the item.
         (ie 'ERIClitpvmmonitord_CXP9031644')

       KWargs:

          version (str): The version of the item in nexus. Defaults to
                         RELEASE to take the latest version.

          filetype (str): The type of the file you wish to download.
                          Defaults to rpm.

        Returns:
           str. The name of the file downloaded from nexus or None if there was
           a Download error.
        """
        if version == 'RELEASE':
            version = self.__get_latest_version_in_nexus(group_id, artifact_id,
                                                         repo)

        filename = "{0}-{1}.{2}".format(artifact_id, version, filetype)

        web_part1 = test_constants.NEXUS_LINK
        web_part2 = "content/groups/{0}".format(repo)
        web_part3 = "/".join(group_id.split('.'))
        web_part4 = "{0}/{1}/{2}".format(artifact_id,
                                         version,
                                         filename)

        full_link = "{0}/{1}/{2}/{3}".format(web_part1,
                                             web_part2,
                                             web_part3,
                                             web_part4)
        cmd = "/usr/bin/wget --no-check-certificate {0}"\
            .format(full_link)

        _, stderr, returnc = self.run_command_local(cmd)

        if returnc != 0:
            self.log('error', "Failed to download from nexus: {0}"\
                         .format(stderr))
            return None

        return filename

    @staticmethod
    def get_prop_from_file(file_contents, prop_name, space_before_equals=True):
        """
        Function which returns the requested property value
        from the property file contents passed. Designed
        for parsing the litpd.conf file but will work in other
        files which have key/value pairs seperated by '='.

        Args:
           file_contents (str) : The contents of the file. This can be what
                                 is returned from get_file_contents.

           prop_name (str): The name of the property wanted.
           space_before_equals (bool): Whether a space is expected between the
                                       prop_name and equals sign.
                                       Default is True.

        Returns:
          str. The value of the requested property or None if the property
          cannot be found.
        """
        prop_val = None

        if space_before_equals:
            check_str = "{0} =".format(prop_name)
        else:
            check_str = "{0}=".format(prop_name)

        for line in file_contents:
            #Ignore commented out lines
            if line.startswith(';') or line.startswith('#'):
                continue

            if check_str in line:
                prop_val = line.split("=")[1].strip()
                break

        return prop_val

    @staticmethod
    def get_text_in_help(stdout_list, heading):
        """
        Description:
            Returns a string that contains the description of the requested
            help section.

        Args:
            stdout_list (list): List returned from running a detailed litp
            help command. (ie 'litp export --help')

            heading (str): Heading to search for within the stdout_list
                    Example: Usage
        Returns:
            str. The description from the heading within the stdout_list

        Note:
            Cli help message guidlines can be found at:
            http://confluence-nam.lmera.ericsson.se/display/ELITP/
            CLI+Help+Guidelines
        """

        dictionary = {}
        out = ''.join(stdout_list).replace(' ', '')
        usage = 'Usage:'
        option_arguments = 'OptionalArguments:'
        required_arguments = 'RequiredArguments:'
        example = 'Example:' if 'Examples:' not in stdout_list else 'Examples:'

        start_usage = out.index(usage) + len(usage)
        end_usage = out.index(option_arguments)
        dictionary['Usage'] = out[start_usage:end_usage]

        start_option = end_usage + len(option_arguments)
        end_option = out.index(required_arguments)
        dictionary['Optional Arguments'] = out[start_option:end_option]

        start_required = end_option + len(required_arguments)
        end_required = out.index(example)
        dictionary['Required Arguments'] = out[start_required:end_required]

        start_example = end_required + len(example)
        dictionary[example[:-1]] = out[start_example:]

        return dictionary[heading]
