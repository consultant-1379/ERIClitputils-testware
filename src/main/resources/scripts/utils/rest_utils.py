"""
Rest Utils

Note: :sysnopsis: for this file is located in source_code_docs.rst
"""

from litp_generic_utils import GenericUtils
import json
import test_constants
import time


class RestUtils(object):

    """REST API related utilities.
    """

    HEADER_JSON = "Content-Type:application/json"

    def __init__(self, server, port="9999", rest_version="v1",
                 username=None, password=None,
                 rest_loc="/litp/rest/"):
        """Initialise REST variables.

        Args:
            server (str): REST server IP address.

        Kwargs:
            port (str): REST server port.

            rest_version (str): Version of the REST interface to use.

            username (str): Username to use in authenticating to REST.

            password (str): Password to use in authenticating to REST.

            rest_loc (str): Location of REST.
        """
        # GENERIC UTILS
        self.g_utils = GenericUtils()

        # REST SERVER IP ADDRESS / HOST NAME
        self.server = server
        # REST SERVER PORT
        self.port = port
        # USER NAME FOR AUTHENTICATION ON THE REST SERVER

        if not username or not password:
            tmp_usr_name, tmp_usr_pw = self.g_utils.load_ms_usr_creds()

            if not username:
                username = tmp_usr_name

            if not password:
                password = tmp_usr_pw

        self.user = username
        # PASSWORD FOR AUTHENTICATION ON THE REST SERVER
        self.password = password
        # REST PATH
        self.restpath = "{0}{1}".format(rest_loc, rest_version)
        # CURL COMMAND WITH ABSOLUTE PATH
        self.curl_cmd = "/usr/bin/curl"
        # ITEM TYPE PATH
        self.item_type_path = "/item-types"
        # PROPERTY TYPE PATH
        self.property_type_path = "/property-types"

        ##We have two lists as we must remove the children (inherited) paths
        ##before the actual rest paths
        self.paths_to_clean = list()
        self.inherited_paths_to_clean = list()

        # Set this to true if a plan has been run during the test
        self.plan_has_run = False

    @staticmethod
    def _stringify_dict(props_dict):
        """Turns all dictionary elements to a string.

        Takes:    {'a':1, 'b':2, 'c':3} <type dict>
        Returns:  "{'a':'1', 'b':'2', 'c':'3'}" <type str>

        Args:
            props_dict (dict): The dictionary you want to convert to strings.

        Returns:
            str. The dictionary converted to a string.
        """
        return ",".join([
            """ "{0}": "{1}" """.format(key, str(val))
            for key, val in props_dict.iteritems()
        ])

    def inherit_cmd_rest(self, path, source_path, props=None):
        """Execute a REST POST to inherit a model item from source path.

        Args:
            path (str): The path you intend to create.

            source_path (str): The source_path you are inheriting from.

        Kwargs:
            props (dict): Properties you wish to add in as a dict.

        Returns:
            str, str, int. stdout, stderr and status for
                running the inherit command.
        """
        split_path, path_id = path.rsplit("/", 1)

        if props is None:
            props = {}

        # build REST create JSON
        if props:
            msg_data = """{{
                "id": "{0}",
                "inherit": "{1}",
                "properties": {{ {2} }}
            }}""".format(path_id, source_path, self._stringify_dict(props))
        else:
            msg_data = """{{
                "id": "{0}",
                "inherit": "{1}"
            }}""".format(path_id, source_path)

        stdout, stderr, status = self.post(
            split_path, self.HEADER_JSON, msg_data
        )

        return stdout, stderr, status

    def create_plan_rest(self):
        """
        This function creates a plan using the REST interface.

        Returns:
            str, str, int. stdout, stderr and HTML status
                from running the command.
        """
        message_data = "{\"id\": \"plan\"," "\"type\": \"plan\"}"
        stdout, stderr, status = self.post(
            "/plans", self.HEADER_JSON, message_data)

        return stdout, stderr, status

    def run_plan_rest(self):
        """
        This function runs a plan using the REST interface.

        Returns:
            str, str, int. stdout, stderr and HTML status
                from running the command.
        """
        message_data = "{\"properties\":{\"state\": \"running\"}}"
        stdout, stderr, status = self.put(
            "/plans/plan/", self.HEADER_JSON, message_data)
        return stdout, stderr, status

    def stop_plan_rest(self):
        """
        This function stops a plan using the REST interface.

        Returns:
            str, str, int. stdout, stderr and HTML status
                from running the command.
        """
        message_data = "{\"properties\":{\"state\": \"stopped\"}}"
        stdout, stderr, status = self.put(
            "/plans/plan/", self.HEADER_JSON, message_data)

        return stdout, stderr, status

    def show_plan_rest(self):
        """
        This function shows a plan using the REST interface.

        Returns:
            str, str, int. stdout, stderr and HTML status
                from running the command.
        """
        stdout, stderr, status = self.get("/plans/plan")

        return stdout, stderr, status

    def remove_plan_rest(self):
        """
        This function removes a plan using the REST interface.

        Returns:
            str, str, int. Return stdout, stderr and HTML status
                from running the command.
        """
        stdout, stderr, status = self.delete("/plans/plan/")

        return stdout, stderr, status

    def clean_paths(self):
        """
        Performs REST level cleanup to remove any
        paths created in the LITP tree.

        This works by running remove on a list of paths which
        is appended to after each post command.
        """
        self.g_utils.log("info", "ENTERING REST CLEAN_PATHS")
        # If a plan has been, run stop it and wait for it to stop
        if self.plan_has_run:
            self.stop_plan_if_running_rest()

        # Remove inherit items
        for path in list(self.inherited_paths_to_clean):
            stdout, _, status = self.delete(path)
            if not self.is_status_success(status):
                self.g_utils.log("error", "Cleanup of url failed: {0}"
                                 .format(stdout))

        # Run plan to apply removes for inherit
        if self.plan_has_run:
            self.create_plan_rest()
            self.run_plan_rest()
            self.wait_for_plan_state_rest(test_constants.PLAN_COMPLETE)
            self.remove_plan_rest()

        # Remove all other items
        for path in list(self.paths_to_clean):
            stdout, _, status = self.delete(path)
            if not self.is_status_success(status):
                self.g_utils.log("error", "Cleanup of url failed: {0}"
                                 .format(stdout))

        # If a plan has been run, we need to run a plan again to apply changes
        if self.plan_has_run:
            self.create_plan_rest()
            self.run_plan_rest()
            self.wait_for_plan_state_rest(test_constants.PLAN_COMPLETE)
            self.remove_plan_rest()

        self.g_utils.log("info", "EXITING REST CLEAN_PATHS")

    def stop_plan_if_running_rest(self):
        """
        Checks if a plan is running and, if so, attempts to stop it.
        Will wait the default timeout period for the plan to stop.

        Returns:
            bool. True if the plan was stopped/was not in
                progress or False if the Plan could not be stopped.
        """
        # Check if a plan is currently running
        if self.get_current_plan_state_rest() \
                    == test_constants.PLAN_IN_PROGRESS:
            ##If plan was running, call stop
            _, stderr, status = self.stop_plan_rest()

            if stderr != "" or not self.is_status_success(status):
                self.g_utils.log("error", "Unable to stop plan")
                return False

            # Return the result of waiting for the stopped phase.
            return self.wait_for_plan_state_rest(test_constants.PLAN_STOPPED)

        # If plan is already stopping, wait for it to reach phase of stopped
        if self.get_current_plan_state_rest() == test_constants.PLAN_STOPPING:
            return self.wait_for_plan_state_rest(test_constants.PLAN_STOPPED)

        return True

    def wait_for_plan_state_rest(self, state_value, timeout_mins=10):
        """Waits until the plan reports the
        specified status or has completed its run.

         Args:
            state_value (int): The state value to wait for as
                recorded in test_constants.

            timeout_mins (int): When to timeout from the method if
                the plan is still running. Default is 10 minutes.

        Returns:
            bool. True if the specified state is reached or False if the plan
                is no longer running but is not in specified state.

        Returns when the task reaches the stated state or when the state can
        no longer be reached (i.e. plan is in error case or has completed).
        """
        self.g_utils.log("info", "Entering wait_for_plan_state method")

        seconds_increment = 3
        seconds_count = seconds_increment

        plan_state = self.get_current_plan_state_rest()

        # Loop until break
        while True:

            time.sleep(seconds_increment)
            seconds_count += seconds_increment
            minutes_passed = seconds_count / 60

            if minutes_passed > timeout_mins:
                self.get_current_plan_state_rest()
                self.g_utils.log("info",
                             "Exiting wait_for_plan_state method after " + \
                                 "{0} seconds (TIMEOUT)"\
                                 .format(seconds_count))
                return False

            plan_state = self.get_current_plan_state_rest()

            # This covers case where you are waiting for plan to start
            if plan_state == state_value:
                self.get_current_plan_state_rest()
                self.g_utils.log("info",
                             "Exiting wait_for_plan_state method after " + \
                                 "{0} seconds (SUCCESS)"\
                                 .format(seconds_count))
                return True

            # If plan is not in progress, need to exit or you will loop forever
            if plan_state != test_constants.PLAN_IN_PROGRESS:
                if plan_state == state_value:
                    self.g_utils.log("info",
                                 "Exiting wait_for_plan_state method after"\
                                     + " {0} seconds (SUCCESS)"\
                                     .format(seconds_count))
                    return True
                # If we are waiting for stopped state and current state is
                # stopping, wait.
                elif state_value == test_constants.PLAN_STOPPED and \
                        plan_state == test_constants.PLAN_STOPPING:
                    continue
                else:
                    self.g_utils.log("info",
                                 "Exiting wait_for_plan_state method after"\
                                     + " {0} seconds (UNEXPECTED STATE)" \
                                     .format(seconds_count))
                    return False

    def get_current_plan_state_rest(self):
        """Returns the status of the currently running plan.

        Returns:
            int. An integer of corresponding to the status of
                the plan as defined in test_constants.
        """
        # Get the plan path
        stdout, stderr, status = self.get("/plans/plan")

        # If we have an error retrieving the plan state return error
        if stderr != "" or not self.is_status_success(status):
            return test_constants.CMD_ERROR

        data, errors = self.get_json_response(stdout)

        if errors:
            return test_constants.CMD_ERROR

        # Get the state value from returned JSON object
        plan_status = data["properties"]["state"]

        if "initial" in plan_status:
            return test_constants.PLAN_NOT_RUNNING
        elif "running" in plan_status:
            return test_constants.PLAN_IN_PROGRESS
        elif "stopping" in plan_status:
            return test_constants.PLAN_STOPPING
        elif "stopped" in plan_status:
            return test_constants.PLAN_STOPPED
        elif "successful" in plan_status:
            return test_constants.PLAN_COMPLETE
        elif "failed" in plan_status:
            return test_constants.PLAN_FAILED
        elif "invalid" in plan_status:
            return test_constants.PLAN_INVALID

        return test_constants.CMD_ERROR

    def request(self, url, header="", request="GET", data="", options=""):
        """Send a request to REST server.

        Args:
            url (str): URL points to the resource.

        Kwargs:
            header (str): Header of the REST request, separated by
                space if there are more.

            request (str): Request type, one of: GET, POST, PUT, DELETE.

            data (str): Input data for REST request.

            options (str): Further options.

        Returns:
            str, str, int. Standard output and error strings corresponding
                to the REST request output, and HTTP response status.
        """
        header_option = ""
        if header != "":
            header_list = header.split(" ")
            for header_element in header_list:
                header_option += " -H '{0}' ".format(header_element.strip("'"))

        request_option = "-X {0}".format(request)

        data_option = ""
        if data != "":
            data_option = "-d '{0}'".format(data)

        options += " -w '\\n%{http_code}\\n'"

        cmd = "{0} {1} {2} {3} -s -S -u {4}:{5} -k {6} {7}".\
            format(self.curl_cmd, header_option, request_option, data_option,
                   self.user, self.password, options, url)

        outlist, stderr, _ = \
            self.g_utils.run_command_local(cmd)

        status = -1
        if len(outlist) > 0:
            if outlist[-1].isdigit():
                status = int(outlist[-1])
                outlist = outlist[:-1]
            else:
                status = -255

        stdout = "\n".join(outlist)
        sderr = "\n".join(stderr)

        # If someone has performed a successful update on plan item, assume a
        # plan has been run in the test and will require a plan run at cleanup
        if self.is_status_success(status) \
                and "plans/plan" in url and request == "PUT":
            self.plan_has_run = True

        return stdout, sderr, status

    def get(self, path, options=""):
        """GET request (read) for REST server.

        Args:
            path (str): Path to LITP resource.

        Kwargs:
            options (str): Further options.

        Returns:
            str, str, int. Standard output and error strings corresponding
                to the REST request output, and HTTP response status.
        """
        url = "https://{0}:{1}{2}{3}".format(self.server, self.port,
                                             self.restpath, path)

        return self.request(url=url, request="GET", options=options)

    def post(self, path, header="", data="", options=""):
        """POST request (create) for REST server.

        Args:
            path (str): Path to LITP resource.

        Kwargs:
            header (str): Header of the REST request, separated by
                space if there are more.

            data (str): JSON input for request.

            options (str): Further options.

        Returns:
            str, str, int. Standard output and error strings corresponding
                to the REST request output, and HTTP response status.
        """
        url = "https://{0}:{1}{2}{3}".format(self.server, self.port,
                                             self.restpath, path)

        stdout, sderr, status = self.request(url=url, header=header,
                                             request="POST", data=data,
                                             options=options)

        # If URL successfully created, add to list of URLs we
        # need to delete in cleanup
        if self.is_status_success(status):
            json_data, _ = self.get_json_response(data)
            if "id" in json_data:
                # If the id key is present, use it to do cleanup, otherwise we
                # can't clean up
                if "inherit" in data:
                    self.inherited_paths_to_clean.append(
                        self.g_utils.join_paths(path, json_data['id']))
                else:
                    self.paths_to_clean.append(
                        self.g_utils.join_paths(path, json_data['id']))

        return stdout, sderr, status

    def put(self, path, header="", data="", options=""):
        """PUT request (update) for REST server.

        Args:
            path (str): Path to LITP resource.

        Kwargs:
            header (str): Header of the REST request, separated by
                space if there are more.

            data (str): JSON input for request.

            options (str): Further options.

        Returns:
            str, str, int. Standard output and error strings corresponding
                to the REST request output, and HTTP response status.
        """
        url = "https://{0}:{1}{2}{3}".format(self.server, self.port,
                                             self.restpath, path)

        return self.request(url=url, header=header, request="PUT",
                            data=data, options=options)

    def delete(self, path, options=""):
        """DELETE request (remove) for REST server.

        Args:
            path (str): Path to LITP resource.

        Kwargs:
            options (str): Further options.

        Returns:
            str, str, int. Standard output and error strings corresponding
                to the REST request output, and HTTP response status.
        """
        url = "https://{0}:{1}{2}{3}".format(self.server, self.port,
                                             self.restpath, path)

        stdout, sderr, status = self.request(url=url, request="DELETE",
                                             options=options)

        ##If success, remove URL deleted from list of cleanup urls
        if self.is_status_success(status):
            if path in self.paths_to_clean:
                self.paths_to_clean.remove(path)

        return stdout, sderr, status

    @staticmethod
    def is_status_success(status):
        """
        Checks the passed status from running a REST command for
        a valid success HTTP response code.

        Expected success codes:
        200	OK	Successful HTTP request.
        201	Created	item created successfully.

        All other codes correspond to an error case.

        Args:
            status (int): The HTTP response code.

        Returns:
            bool. True if HTTP code indicates success or False otherwise.
        """
        return status == 200 or status == 201

    @staticmethod
    def get_json_response(json_string):
        """Transform JSON sting to JSON data structure,
        and do further checks on JSON.

        Args:
            json_string (str): JSON sting.

        Returns:
            dict, list. JSON data structure, list of errors.
        """
        errors = []
        json_data = None
        try:
            json_data = json.loads(json_string)

            if json_data is None:
                errors.append("json content was empty")
            else:
                if "status" in json_data.keys():
                    errors.append("status field is not accepted.")
        except ValueError:
            errors.append("Can not convert string to JSON")

        return json_data, errors

    def get_rest_uri(self):
        """Get REST URI.

        Returns:
            str. The REST URI.
        """
        return "https://{0}:{1}{2}".format(self.server, self.port,
                                           self.restpath)
