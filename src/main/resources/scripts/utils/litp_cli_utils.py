"""
LITP ClI Utils:

Note: :synopsis: for this file is located in source_code_docs.rst
"""

from litp_generic_utils import GenericUtils
from json_utils import JSONUtils
import re


class CLIUtils(object):
    """
    CLI related utilities.
    """

    def __init__(self):
        """Initialise LITP path variables.
        """
        self.litp_path = "/usr/bin/litp"
        self.cli_cleanup_mappings = {'create ': 'remove',
                                     'create_plan ': 'remove_plan',
                                     'restore_snapshot ': 'remove_plan',
                                     '_snapshot ': 'snapshot',
                                     'inherit ': 'remove'}
        self.gen_utils = GenericUtils()
        self.json_u = JSONUtils()
        self.debug_log_path = "/litp/logging"

    def get_grep_all_state_cmd(self, path='/'):
        """Returns a grep command used to collect the
        state of all items in the LITP tree.

        Kwargs:
            path (str): The LITP path to search under. By default, uses
                the root path.

        Returns:
            str. A show and grep command to get all states in the tree.
        """
        show_cmd = self.get_show_cmd(path, "-r")
        grep_cmd = "| /bin/grep ^'    state:'"

        full_cmd = "{0} {1}".format(show_cmd, grep_cmd)

        return full_cmd

    def get_grep_unexpected_state_cmd(self, path='/', state='Applied'):
        """
        Returns a grep command used to collect all items not in the
        expected state in the tree, including the associated URLs.

        Kwargs:
            path (str): The LITP path to search under. By default, uses
                the root path.

            state (str): Expected state of items in tree. By default, uses
                state Applied.

        Returns:
            str. A show and grep command to get all unexpected states in the\
                 tree and also display the associated URL.
        """
        show_cmd = self.get_show_cmd(path, "-r")
        grep1_cmd = "| /bin/grep -B5 'state:'"
        grep2_cmd = " | /bin/grep -E 'state|^/' | /bin/grep -v ^'        '"
        grep3_cmd = " | /bin/grep -v '{0}'".format(state)
        grep4_cmd = r" | /bin/grep -B1 'state: ' | /bin/grep -v '\--'"

        full_cmd = "{0} {1} {2} {3} {4}".format(show_cmd, grep1_cmd,\
                                            grep2_cmd, grep3_cmd, grep4_cmd)

        return full_cmd

    @staticmethod
    def get_num_phases_in_plan(plan_output):
        """
        Counts the number of phases in a plan.

        Args:
            plan_output (list): Output from running a show_plan.

        Returns:
            int. The number of phases in the plan.
        """
        phase_count = 0

        for line in plan_output:
            if re.match(r'^Phase', line):
                phase_count += 1

        return phase_count

    @staticmethod
    def get_plan_phase(plan_output, phase_num):
        """
        Extracts the part of the show_plan output related
        to the selected phase.

        Args:
            plan_output (list): The output from the show_plan command.

            phase_num (int): The phase you wish to extract.

        Returns:
            list. The show_plan output related to the specified phase.
        """
        phase_list = list()
        phase_started = False

        for line in plan_output:
            # If line matches the phase we are looking for
            if re.match(r'^Phase {0}'.format(str(phase_num)), line):
                phase_started = True
                continue

            # If phase has started
            if phase_started:
                # If we reach the next phase or end of the plan output, break
                if re.match(r'^Phase|^Tasks', line):
                    break
                # Otherwise, append line to current phase list
                phase_list.append(line)

        return phase_list

    def get_num_tasks_in_phase(self, plan_output, phase_num):
        """
        Counts the number of tasks in a phase.

        Args:
            plan_output (list): Output from running a show_plan.

            phase_num (int): The phase in the plan to count the\
                                number of tasks contained in it.

        Returns:
            int. The number of tasks in the specified phase.
        """
        task_count = 0

        phase = self.get_plan_phase(plan_output, phase_num)

        for line in phase:
            if re.match(r'Initial|Running|Success|Failed|Stopped',
                        line):
                task_count += 1

        return task_count

    def get_task_status(self, plan_output, phase_num, task_num):
        """
        Returns the status of the selected task in the selected phase.

        Args:
            plan_output (list): Output from running a show_plan.

            phase_num (int): The phase to examine.

            task_num (int): The task to examine.

        Returns:
            str. The state of the task.
        """
        task_count = 0
        current_phase = self.get_plan_phase(plan_output, phase_num)

        for line in current_phase:
            match_item = \
                re.match(r'Initial|Running|Success|Failed|Stopped',
                         line)

            if match_item:
                task_count += 1

                if task_num == task_count:
                    return match_item.group(0).strip()

        return None

    def get_task_desc(self, plan_output, phase_num, task_num):
        """
        Returns the description of the selected task in the selected phase.

        Args:
            plan_output (list): Output from running a show_plan.

            phase_num (int): The phase to examine.

            task_num (int): The task to examine.

        Returns:
            list. The description of the task.
        """
        task_count = 0
        task_desc = list()
        current_phase = self.get_plan_phase(plan_output, phase_num)

        for line in current_phase:
            match_item = \
                re.match(r'Initial|Running|Success|Failed|Stopped',
                         line)

            if match_item:
                task_count += 1

            if task_num == task_count:
                if match_item:
                    task_desc.append(
                        line.split(match_item.group(0).strip())[1].strip())
                else:
                    task_desc.append(line.strip())

        return task_desc

    def get_task_phase_no(self, plan_output, task_desc):
        """
        Extracts the Phase number of the Phase in which the
        specified task description is found.

        Args:
            plan_output (list): Output from running a show_plan.

            task_desc (str): The task description to search for
                                within the plan.

        Returns:
            int. The phase number in which the task is found.
        """
        num_phases = self.get_num_phases_in_plan(plan_output)
        phase_task_desc = ""
        task_desc = task_desc.replace(" ", "")
        task_statuses = ['Success', 'Initial', 'Running',\
                            'Failed', 'Stopped']

        #Parse the phase output into a list of task descriptions
        phase_index = 1
        while phase_index <= num_phases:
            phase_output = self.get_plan_phase(plan_output,
                                                 phase_index)
            for line in phase_output:
                new_task = False
                line = line.replace(" ", "")

                #If a task status is in the line, indicates a new task
                for status in task_statuses:
                    if status in line:
                        new_task = True
                        break

                if new_task:
                    #Check if the current task str contains the task arg
                    if phase_task_desc:
                        if task_desc in phase_task_desc:
                            return phase_index
                    #Reset the phase_task_desc for creating a new task.
                    phase_task_desc = ""
                #Append the line to the phase task description
                phase_task_desc += line.strip()

            phase_index += 1

        return None

    def parse_plan_output(self, plan_output):
        """Parses the passed show_plan output to a dict.

        Args:
            plan_output (list): Output from running a show_plan.

        Returns:
            dict. Show_plan output.
        """
        plan_output_dict = dict()
        num_of_phases = self.get_num_phases_in_plan(plan_output)

        for phase_num in range(1, num_of_phases + 1):
            num_of_tasks = self.get_num_tasks_in_phase(plan_output, phase_num)
            plan_output_dict[phase_num] = dict()

            for task_num in range(1, num_of_tasks + 1):
                plan_output_dict[phase_num][task_num] = dict()

                plan_output_dict[phase_num][task_num]["STATUS"] = \
                    self.get_task_status(plan_output,
                                         phase_num,
                                         task_num)

                plan_output_dict[phase_num][task_num]["DESC"] = \
                    self.get_task_desc(plan_output,
                                       phase_num,
                                       task_num)

        return plan_output_dict

    def get_litp_version_cmd(self, args=''):
        """
        Returns the LITP version command.

        Kwargs:
            args (str): Arguments for the command (e.g. '--json', '-a').

        Returns:
            str. The LITP version command.
        """

        cmd = "{0} version {1}".format(self.litp_path, args)
        return cmd

    def get_restore_snapshot_cmd(self, args=''):
        """Generate a LITP restore snapshot command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI restore_snapshot command.
        """

        cmd = "{0} restore_snapshot {1}"\
            .format(self.litp_path, args)
        return cmd

    @staticmethod
    def get_mco_cmd(cmd):
        """Attaches the mco prefix to a command.

        Args:
            cmd (str): The mco command to run.

        Returns:
            str. The mco command.
        """

        return "/usr/bin/mco {0}".format(cmd)

    def get_restoremodel_cmd(self):
        """
        Returns the LITP restore model command.

        Returns:
            str. The LITP restore model command.
        """
        return "{0} restore_model".format(self.litp_path)

    def get_create_cmd(self, url, class_type, properties='', args=''):
        """
        Generate a LITP create command string based on the parameters passed.

        Args:
            url (str): Path to create in the LITP model manager.

            class_type (str): The type of the LITP object being created.

        Kwargs:
            properties (str): The LITP object properties.

            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI create command.
        """

        if properties:
            create_command = "{0} create -p {1} -t {2} -o {3} {4}"\
                .format(self.litp_path, url, class_type, properties, args)
        else:
            create_command = "{0} create -p {1} -t {2} {3}"\
                .format(self.litp_path, url, class_type, args)

        return create_command

    def get_inherit_cmd(self, path, source_path, properties='', args=''):
        """Generate a LITP inherit command string based on parameters passed.

        Args:
            path (str): The path where you wish to create the inherit link.

            source_path (str): The source path you want the inherit link to\
                              point to.

        Kwargs:
            properties (str): LITP object properties you wish to overwrite.

            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI inherit command.
        """
        if properties:
            inherit_command = "{0} inherit -p {1} -s {2} -o {3} {4}"\
                .format(self.litp_path, path, source_path, properties, args)
        else:
            inherit_command = "{0} inherit -p {1} -s {2} {3}"\
                .format(self.litp_path, path, source_path, args)

        return inherit_command

    def is_inherit_cmd(self, cmd):
        """
        Returns True if the cmd passed to it is an inherit command.

        This is used by the automatic cleanup in Generic Test.

        Args:
            cmd (str): A LITP CLI command.

        Returns:
            bool. True if the passed command is an inherit command.
        """
        if "{0} inherit".format(self.litp_path) in cmd:
            return True

        return False

    def is_create_link_cmd(self, cmd):
        """Returns True if the cmd passed to it is a create, link
        or a create_plan command.

        This is used by the automatic cleanup in Generic Test.

        Args:
            cmd (str): A LITP CLI command.

        Returns:
            bool. True if the passed command is a create,
                link or create_plan command.
        """
        if "{0} create".format(self.litp_path) in cmd \
                or "{0} link".format(self.litp_path) in cmd:
            return True

        return False

    def get_remove_cmd(self, url, args=''):
        """Generate a LITP remove command string based on parameters passed.

        Args:
            url (str): URL location of the LITP model manager.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI remove command.
        """

        remove_command = "{0} remove -p {1} {2}"\
            .format(self.litp_path, url, args)

        return remove_command

    def is_remove_cmd(self, cmd):
        """Returns True if the passed command is a LITP remove command
        or False otherwise.

        Args:
            cmd (str): A LITP CLI command.

        Returns:
            bool. True if the passed command is a LITP remove command.
        """
        if "{0} remove -p".format(self.litp_path) in cmd:
            return True

        return False

    def get_show_cmd(self, url, args=''):
        """Generate a LITP show command string based on parameters passed.

        Args:
            url (str): URL location of the LITP model manager.

        Kwargs:
            args (str): Optional arguments to use in the show command.

        Returns:
            str. Correctly formatted CLI show command.
        """
        show_command = "{0} show -p {1} {2}"\
            .format(self.litp_path, url, args)

        return show_command

    def get_path_state_cmd(self, url):
        """A show command with greps included to strip out
        the state of the passed path.

        Args:
            url (str): The LITP path you wish to get the state of.

        Returns:
            str. The show command with added greps to get the state of the path
        """
        show_cmd = self.get_show_cmd(url)

        trim_output = "| /bin/grep {0} -A 3 ".format(url)
        trim_whitespace = "| /bin/sed 's/^[ \t]*//;s/[ \t]*$//'"
        trim_to_value = " | /bin/grep ^'{0}:' | /bin/sed 's/{0}://'" \
            .format("state")

        return "{0} {1} {2} {3}".format(show_cmd,
                                        trim_output,
                                        trim_whitespace,
                                        trim_to_value)

    def get_show_data_value_cmd(self, url, filter_value):
        """Returns a show command with added sed/grep pipes to extract a
        specific data value from the passed URL when passed to run command.

        Args:
            url (str): Path to run the show command on.

            filter_value (str): The data value you wish to filter by
                (e.g. state).

        Returns:
            str. A show command with added greps and seds to extract a
                specific value from running this command.
        """
        trim_whitespace = "| sed 's/^[ \t]*//;s/[ \t]*$//'"
        trim_to_value = " | grep ^'{0}:' | sed 's/{0}://'" \
            .format(filter_value)

        show_cmd = self.get_show_cmd(url)

        return show_cmd + trim_whitespace + trim_to_value

    @staticmethod
    def get_path_name(path):
        """Returns the last item in a LITP URL path which
        corresponds to the path ID.

        Args:
            path (str): The LITP URL path (e.g. '/deployments/cluster').

        Returns:
            str. A string corresponding to the path ID\
                ('cluster' in the above example).

        Raises:
            ValueError if an invalid path is passed.
        """
        split_path = path.split("/")

        if len(split_path) < 1:
            raise ValueError("Invalid path parameter: {0}".format(path))

        return split_path[len(split_path) - 1]

    def get_upgrade_cmd(self, url, args=''):
        """
        Generate a LITP upgrade command.

        Args:
            url (str): Location in the LITP model.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI upgrade command.
        """
        cmd = "{0} upgrade -p {1} {2}".format(self.litp_path, url, args)

        return cmd

    def get_update_cmd(self, url, properties, args='', action_delete=False):
        """Generate a LITP update command str based on the parameters passed.

        Args:
            url (str): URL location of the LITP model manager.

            properties (str): The LITP object properties to update.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

            action_delete (bool): If set to True, properties will be deleted,
                otherwise properties will be updated.

        Returns:
            str. Correctly formatted CLI update command.
        """

        if action_delete:
            prop_arg = "-d"
        else:
            prop_arg = "-o"

        update_command = "{0} update -p {1} {2} {3} {4}"\
            .format(self.litp_path, url, prop_arg, properties, args)

        return update_command

    def get_create_plan_cmd(self, args=''):
        """Generate a LITP create_plan command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI create_plan command.
        """

        cmd = "{0} create_plan {1}"\
            .format(self.litp_path, args)
        return cmd

    def get_prepare_restore_cmd(self, args=''):
        """Generate a LITP prepare for restore command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI prepare for restore command.
        """

        cmd = "{0} prepare_restore {1}"\
            .format(self.litp_path, args)

        return cmd

    def get_create_snapshot_cmd(self, args=''):
        """Generate a LITP create_snapshot command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI create_snapshot command.
        """

        cmd = "{0} create_snapshot {1}"\
            .format(self.litp_path, args)
        return cmd

    def get_remove_snapshot_cmd(self, args=''):
        """Generate a LITP remove_snapshot command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI remove_snapshot command.
        """

        cmd = "{0} remove_snapshot {1}"\
            .format(self.litp_path, args)

        return cmd

    def is_snapshot_cmd(self, cmd_to_test):
        """
        Tests if the passed command is a snapshot command.
        Does not consider snapshot commands issued with --help option
        as snapshot commands.

        Args:
            cmd_to_test (str): The command you wish to test.

        Returns:
            bool. True if command passed is snapshot command, False otherwise.
       """
        snap_commands = list()
        snap_commands.append("{0} remove_snapshot".format(self.litp_path))
        snap_commands.append("{0} create_snapshot".format(self.litp_path))
        snap_commands.append("{0} restore_snapshot".format(self.litp_path))

        for cmd in snap_commands:
            if cmd in cmd_to_test and '--help' not in cmd_to_test \
                                  and '-h' not in cmd_to_test:
                return True

        return False

    def is_tagged_snapshot_cmd(self, cmd_to_test):
        """
        Tests if the passed command is a tagged snapshot command.

        Args:
            cmd_to_test (str): The command you wish to test.

        Returns:
            bool. True if tagged snapshot command or False otherwise.
        """
        if self.is_snapshot_cmd(cmd_to_test) and '-n' in cmd_to_test:
            return True

        return False

    @staticmethod
    def get_tagged_snapshot_name(cmd):
        """
        Gets the name of the tagged snapshot from the command.

        Args:
            cmd (str): The command you wish to test.

        Returns:
            str. Name of the tagged snapshot.
        """
        if '--name' in cmd:
            name = cmd.split("--name")[-1].split()[0]
        else:
            name = cmd.split("-n")[-1].split()[0]

        return name

    def get_stop_plan_cmd(self, args=''):
        """Generate a LITP stop plan command.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI stop_plan command.
        """

        cmd = "{0} stop_plan {1}"\
            .format(self.litp_path, args)

        return cmd

    def get_run_plan_cmd(self, args=''):
        """Generate a LITP run plan command.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI run_plan command.
        """

        cmd = "{0} run_plan {1}"\
            .format(self.litp_path, args)

        return cmd

    def is_run_plan_cmd(self, cmd):
        """Returns True if command passed is a run_plan command.

        Args:
            cmd (str): The command to test.

        Returns:
            bool. True if command is a run_plan command.
        """
        if "{0} run_plan".format(self.litp_path) in cmd:
            return True

        return False

    def get_remove_plan_cmd(self, args=''):
        """Generate a LITP remove_plan command.

        Kwargs:
            args (str): Optional arguments for the command (e.g. '--json').

        Returns:
            str. Correctly formatted CLI remove_plan command.
        """
        return "{0} remove_plan {1}".format(self.litp_path, args)

    def get_show_plan_cmd(self, args=''):
        """Generate a LITP show_plan command.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI show_plan command.
        """
        return "{0} show_plan {1}".format(self.litp_path, args)

    def get_show_plan_status_cmd(self):
        """Returns a show command which uses tail to show only the
        last line which contains overall status figures.
        """
        return self.get_show_plan_cmd() + " | tail -n 3"

    @staticmethod
    def load_plan_state_to_dict(cmd_status):
        """Takes as input the std_out returned from successfully
        running the cmd returned from get_show_plan_status_cmd
        and returns the plan status as a dictionary.

        Args:
            cmd_status (list): The std_out from running the cmd returned\
                from the get_show_plan_status_cmd.

        Returns
            dict. Containing the following keys: Total:, Initial:, Running:,\
                Success:, Failed: and Stopped:.
        """
        if isinstance(cmd_status, list) and len(cmd_status) > 1:
            for line in cmd_status:
                # Find the line with the task lists in
                if "|" in line:
                    cmd_status = line
                    break
        else:
            GenericUtils.log("error", "Unexpected plan status")
            return None

        status_list = cmd_status.split("|")
        status_split_exp_len = 6

        if len(status_list) != status_split_exp_len:
            GenericUtils.log("error", "Unexpected plan status")
            return None

        plan_status = dict()

        tasks = status_list[0]
        plan_status["Total:"] = \
            tasks.split()[1].strip()

        init_tasks = status_list[1]
        plan_status["Initial:"] = \
            init_tasks.split()[1].strip()

        run_tasks = status_list[2]
        plan_status["Running:"] = \
            run_tasks.split()[1].strip()

        success_tasks = status_list[3]
        plan_status["Success:"] = \
            success_tasks.split()[1].strip()

        fail_tasks = status_list[4]
        plan_status["Failed:"] = \
            fail_tasks.split()[1].strip()

        stopped_tasks = status_list[5]
        plan_status["Stopped:"] = \
            stopped_tasks.split()[1].strip()

        return plan_status

    def get_restore_cmd(self, args=''):
        """Generate a LITP restore command.

        Kwargs:
            args (str): Other arguments (e.g. '--json').

        Returns:
            str. Correctly formatted CLI restore command.
        """
        cmd = "{0} restore {1}".format(self.litp_path, args)

        return cmd

    def get_xml_export_cmd(self, litp_path, file_path='', args=''):
        """Generate a LITP XML export command.

        Args:
            litp_path (str): The LITP path to export.

        Kwargs:
            file_path (str): An optional file to export to. If not specified,
                export results will be put to stdout.

            args (str): Other arguments (e.g. -j).

        Returns:
            str. Correctly formatted CLI export command.
        """
        cmd = "{0} export -p {1} {2}".format(self.litp_path, litp_path, args)

        if file_path != '':
            cmd += " -f {0}".format(file_path)

        return cmd

    def is_xml_export_cmd(self, cmd):
        """Returns True if passed cmd is an XML export command.

        This is used in autocleanup to keep track of what
        files have been added to the server.

        Args:
            cmd (str): The command to inspect.

        Returns:
            bool. True if the cmd is an XML export command or False otherwise.
        """
        if "{0} export".format(self.litp_path) in cmd:
            if "-f" in cmd:
                return True

        return False

    @staticmethod
    def get_export_filepath(cmd):
        """
        Returns the filepath provided after -f for the passed export command.
        This is used in cleanup.

        Args:
            cmd (str): The export command.

        Returns:
            str. The filepath or None if the filepath is not found.
        """
        if "-f" not in cmd:
            return None

        cmd_path_item = cmd.split("-f")[1]

        return cmd_path_item.split()[0]

    def get_xml_load_cmd(self, litp_path, file_path, args=''):
        """Generate a LITP XML load command.

        Args:
            litp_path (str): The LITP path to load to.

            file_path (str): The file to load from.

        Kwargs:
            args (str): Other arguments (e.g. -j).

        Returns:
            str. Correctly formatted CLI load command.
        """
        cmd = "{0} load -p {1} -f {2} {3}".format(self.litp_path, litp_path,
                                                  file_path, args)

        return cmd

    def get_import_cmd(self, source_path, dest_path, args=''):
        """Generate a LITP import command.

        Args:
            source_path (str): The path of the RPM to import.

            dest_path (str): The path the RPM should be imported to.

        Kwargs:
            args (str): Other arguments (e.g. -j).

        Returns:
            str. Correctly formatted CLI import command.
        """
        cmd = "{0} import {1} {2} {3}".format(self.litp_path, source_path,
                                              dest_path, args)

        return cmd

    def get_import_iso_cmd(self, iso_mount_path, args=''):
        """Generate a LITP import_iso command.

        Args:
            iso_mount_path (str): The path of the mounted ISO to import.

        Kwargs:
            args (str): Other arguments (e.g. -j).

        Returns:
            str. Correctly formatted CLI import_iso command.
        """

        cmd = "{0} import_iso {1} {2}".format(self.litp_path,
                                          iso_mount_path, args)
        return cmd

    def get_help_cmd(self, help_arg='--help', help_action=''):
        """Generate a LITP help command.

        Kwargs:
            help_arg (str): The help arg to use (--help is default).

            help_action (str): Define what action to get help\
                from (e.g. 'export').

        Returns:
            str. A LITP help command.
        """
        cmd = "{0} {1} {2}".format(self.litp_path, help_action, help_arg)

        return cmd

    @staticmethod
    def get_command_url(command):
        """Extracts a URL string from a LITP CLI command.

        Args:
            command (str): The command containing the URL.

        Returns:
            cmd_url (str): The URL in the command.
        """
        # Remove the /usr/bin/litp or similar string at the start of the cmd
        litp_stripped_cmd = command.replace(command.split(" ")[0], "")
        cmd_url = None

        # Loop through each part of the cmd split by space
        for cmd_part in litp_stripped_cmd.split(" "):
            # if a '/' is found set this part as the url
            if "/" in cmd_part:
                cmd_url = cmd_part.strip()
                break

        return cmd_url

    def get_litp_debug_cmd(self, debug_on=True, args=''):
        """Generate a LITP debug command which, by default, turns on debug.

        Args:
            debug_on (bool): By default is True, turns on debug.

        Kwargs:
            args (str): Extra arguments to supply (e.g. -j).

        Returns:
            str. The LITP debug command.
        """

        if debug_on:
            debug_level = "true"
        else:
            debug_level = "false"

        cmd = "{0} update -p {1} -o force_debug={2} {3}".format(self.litp_path,
                                                         self.debug_log_path,
                                                         debug_level, args)

        return cmd

    def get_cleanup_cmds(self, command):
        """Constructs a cleanup command for the passed command.

        Args:
            command (str): The command that needs to be cleaned up.

        Returns:
            list. A list of commands which need to be run as part of cleanup.
        """
        cleanup = list()

        print "Cleaning up cmd:", command

        # Loop through all CLI commands
        for mapping in self.cli_cleanup_mappings:
            # If CLI command is found in command string
            if mapping in command:
                # Split command to component parts
                # litp_cmd = command.split(" ")[0]
                cleanup_cmd = self.cli_cleanup_mappings[mapping]

                if cleanup_cmd == "remove":
                    cleanup_url = self.get_command_url(command)
                    cleanup.append(self.get_remove_cmd(cleanup_url))
                elif cleanup_cmd == "remove_plan":
                    # Since .215 we are using the 'remove_plan' command
                    cleanup.append(self.get_remove_plan_cmd())
                elif cleanup_cmd == "snapshot":
                    cleanup.append(self.get_create_snapshot_cmd())
                    cleanup.append(self.get_remove_plan_cmd())
                break

        return cleanup

    def is_parent_in_cleanup(self, cleanup_list, new_cmd):
        """Checks whether a parent of the object is
        already in the cleanup cmd list.

        Args:
            cleanup_list (list): The current list of cleanup commands.

            new_cmd (list): The new cmd to check against the list.

        Returns:
            bool. True if the parent cleanup is already present in
                the list or False otherwise.
       """
        new_cmd_url = self.get_command_url(new_cmd)

        # Loop through all cmds in list
        for cmd in cleanup_list:
            current_cmd_url = self.get_command_url(cmd)

            if current_cmd_url in new_cmd_url:

                # Checks current URL is before new in the tree
                current_path_len = len(current_cmd_url.split("/"))
                new_path_len = len(new_cmd_url.split("/"))
                if current_path_len < new_path_len:
                    return True

        return False

    def is_parent_cmd(self, parent_cmd, child_cmd):
        """Compares two commands and returns True if the prospective
        parent command contains a path which is the parent path of the path
        contained in the child command.

        Args:
            parent_cmd (str): The LITP command you think is a parent.

            child_cmd (str): The LITP command you think is a child.

        Returns:
            bool. True if the parent command contains a path that
                is parent to the child command.
        """
        parent_url = self.get_command_url(parent_cmd)
        child_url = self.get_command_url(child_cmd)

        # If both have a valid path
        if parent_url and child_url:
            if parent_url in child_url:
                parent_path_len = len(parent_url.split("/"))
                child_path_len = len(child_url.split("/"))
                if parent_path_len < child_path_len:
                    return True

        return False

    def get_properties(self, show_output):
        """Load the properties from the passed show output.

        Args:
            show_output (str): Output from running show -j on an\
                item in the LITP tree.

        Returns:
            str. The object properties or None if properties are not defined.
        """
        litp_element = show_output

        # If structure is a list, we need to convert to string
        if isinstance(litp_element, list):
            #1. Convert object to string
            output = "".join(show_output)
            litp_element = self.json_u.load_json(output)

        if isinstance(litp_element, str):
            litp_element = self.json_u.load_json(litp_element)

        # If not a list or str, we assume already in JSON format

        #3. Return None if [data][properties] not in JSON
        if not "data" in litp_element.keys():
            if not "properties" in litp_element.keys():
                return None
            else:
                return litp_element["properties"]

        if not "properties" in litp_element["data"].keys():
            return None

        # Return JSON element
        return litp_element["data"]["properties"]

    def add_creds_to_litp_cmd(self, cmd, username, password, user_first=True):
        """
        Adds the passed username and password credentials to
        the passed LITP cmd.

        Args:
            cmd (str): The LITP command you wish to add
                username/password credentials to.

            username (str): The username to add.

            password (str): The password to add.

        Kwargs:
            user_first (bool): If set to False, sets the password\
                    first instead of username.

        Returns:
            str. The command with the username/password arguments added.
        """
        if self.litp_path not in cmd:
            raise ValueError("LITP command does not contain: {0}".format(
                                        self.litp_path))

        user_param = ''
        pw_param = ''

        if username != None or username != '':
            user_param = "-u {0}".format(username)

        if password != None or password != '':
            pw_param = "-P {0}".format(password)

        if user_first:
            return cmd.replace(self.litp_path, "{0} {1} {2} ".format(
                                        self.litp_path, user_param, pw_param))

        return cmd.replace(self.litp_path, "{0} {1} {2} ".format(
                                        self.litp_path, pw_param, user_param))
