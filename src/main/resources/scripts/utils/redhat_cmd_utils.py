"""
RedHat Command Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""


class RHCmdUtils(object):

    """Red Hat command related utilities.
    """

    def __init__(self):
        """Initialise LITP path variables.
        """
        self.grep_path = "/bin/grep"
        self.rpm_path = "/bin/rpm"
        self.find_path = "/bin/find"
        self.xargs_path = "/usr/bin/xargs"
        self.sed_path = "/bin/sed"
        self.sysctl_path = "/sbin/sysctl"
        self.cpu_info = "/proc/cpuinfo"
        self.mem_info = "/proc/meminfo"
        self.tar_path = "/bin/tar"
        self.fallocate_path = "/usr/bin/fallocate"
        self.md5sum_path = "/usr/bin/md5sum"
        self.ps_path = "/bin/ps"
        self.df_path = "/bin/df"
        # RHEL7 command.
        self.time_path = "/usr/bin/timedatectl"
        self.systemctl_path = "/usr/bin/systemctl"
        self.tail_path = "/usr/bin/tail"

    def get_tar_cmd(self, args, tar_file, source="", dest=""):
        """
        Returns the tar command with supplied arguments.

        Args:
            args (str): Arguments to supply to the tar function.

            tar_file (str): Tar file to create/extract/list.

        Kwargs:
            source (str): Directory to tar if creating an archive.

            dest (str): Destination directory.

        Returns:
            str. The tar command to run.
        """
        return "{0} {1} {2} {3} {4}".format(self.tar_path, args,
                                            tar_file, source, dest)

    def get_fallocate_cmd(self, args, file_name):
        """
        Returns the fallocate command with supplied arguments.

        Args:
            args (str): Arguments to supply to fallocate.

            file_name (str): File to allocate in disk.

        Returns:
            str. The fallocate command to run.
        """
        return "{0} {1} {2}".format(self.fallocate_path, args, file_name)

    def get_md5sum_cmd(self, args, file_name):
        """
        Returns the md5sum command with supplied arguments.

        Args:
            args (str): Arguments to supply to md5sum.

            file_name (str): File to calculate checksum for.

        Returns:
            str. The md5sum command to run.
        """
        return "{0} {1} {2}".format(self.md5sum_path, args, file_name)

    @staticmethod
    def get_stat_cmd(filename, args=''):
        """
        Returns a stat command for passed filename with passed arguments.

        Args:
            filename (str): The filename to check.

        Kwargs:
            args (str): Optional arguments to supply to the stat function.

        Returns:
            str. The stat command to run.
        """
        return "/usr/bin/stat {0} {1}".format(filename, args)

    def get_sysctl_cmd(self, args=''):
        """
        Returns the sysctl command with supplied arguments.

        Kwargs:
            args (str): Optional arguments to supply to the sysctl function.

        Returns:
            str. The sysctl command to run.
        """
        return "{0} {1}".format(self.sysctl_path, args)

    def get_replace_str_in_file_cmd(self, old_str, new_str, filepath,
                                    sed_args='', line_number=""):
        """Returns a sed command to replace a string in a file.

        Args:
            old_str (str): The old string that should be replaced.

            new_str (str): The new string.

            filepath (str): The filepath.

        Kwargs:
            sed_args (str): Arguments to pass to sed.
            line_number (str): The line you wish to replace the str on

        Returns:
            str. cmd to replace a string in a file.
        """
        cmd = "{0} {1} '{2}s/{3}/{4}/g' {5}".format(self.sed_path, sed_args,
                                     line_number, old_str, new_str, filepath)

        return cmd

    def get_grep_file_cmd(self, filepath, grep_items, grep_args='',
                          file_access_cmd='/bin/cat'):
        """Constructs a grep command to grep files for
        all of the strings passed in the grep items list.

        Args:
            filepath (str): The file you wish to grep.

            grep_items (list): List of items to be checked for in grep command.

        Kwargs:
            grep_args (str): Arguments to use for grep can be
                passed here if same args apply for all grep search terms.

            file_access_cmd (str): Method to use when greping the file
                (e.g. 'tail -n 10' will only grep the last 10 lines).

        Returns:
            str. A string corresponding to the required grep command or None
                if the parameter list was empty.
        """
        # If user only passes string will create a list of 1 item
        if isinstance(grep_items, str):
            grep_items = [grep_items]

        if filepath and grep_items:
            command = "{0} {1} | {2}".format(file_access_cmd,
                                                filepath, self.grep_path)

            if len(grep_items) == 1:
                command += " {0} \"{1}\"".format(grep_args, grep_items[0])
            else:
                command += " -E {0} \"{1}\"".format(grep_args,
                                                   "|".join(grep_items))

            return command

        return None

    def get_find_cmd(self, args):
        """
        Returns the find command.

        Args:
            args (str): The arguments to pass to the find command.

        Returns:
            str. The find command with supplied arguments.
        """
        return "{0} {1}".format(self.find_path, args)

    def get_find_files_in_dir_cmd(self, find_args, grep_items, grep_args):
        """
        Constructs a cmd which searches the entire directory structure starting
        at the passed path for files containing items matched by the grep.

        Args:
            find_args (str): The parameters to pass to the find cmd\
                (including the path).

            grep_items (list): List of items to be checked for in grep command.

            grep_args (str): Extra arguments to use in grep can be passed here.

        Returns:
            str. A command which pipes a find on the passed filepath to
                the grep command constructed using your grep args.
        """
        cmd = "{0} {1} | {2} {3}".format(self.find_path, find_args,
                                         self.xargs_path, self.grep_path)

        if len(grep_items) == 1:
            cmd += " {0} \"{1}\"".format(grep_args, grep_items[0])
        else:
            cmd += " -E {0} \"{1}\"".format(grep_args, "|".join(grep_items))

        return cmd

    def get_systemctl_cmd(self, args=''):
        """
        Returns the systemctl command with supplied arguments.

        Kwargs:
            args (str): Optional arguments to supply to the systemctl function.

        Returns:
            str. The systemctl command to run.
        """
        return "{0} {1}".format(self.systemctl_path, args)

    def get_systemctl_mainpid(self, service_name):
        """Returns a string corresponding to the pid of the service being
        checked.

        Args:
            service_name (str): Name of the service to check.

        Returns:
            str. The MainPID of the service that is running.
        """
        pid = '{0} show --property MainPID value {1}.service | {2} -1'.format(
            self.systemctl_path, service_name, self.tail_path)

        return pid

    def get_systemctl_is_active_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl is-active" check.

        Args:
            service_name (str): Name of the service to check.

        Returns:
            str. Command for checking the is-active of a service in RHEL7.
        """
        is_active_command = '{0} is-active {1}'.format(
            self.systemctl_path, service_name)
        return is_active_command

    def get_systemctl_reload_cmd(self):
        """Returns a string corresponding to a "systemctl daemon-reload"
           check.

        Returns:
            str. Command for reloading daemon in RHEL7.
        """

        reload_cmd = '{0} daemon-reload'.format(
            self.systemctl_path)

        return reload_cmd

    @staticmethod
    def get_service_running_cmd(service_name):
        """Returns a string corresponding to a "is service running" check.

        Args:
            service_name (str): Name of the service to check.

        Returns:
            str. Command for checking the status of a service in RHEL6.
        """
        status_command = '/sbin/service {0} status'.format(service_name)
        return status_command

    @staticmethod
    def get_service_restart_cmd(service_name):
        """Returns a string corresponding to a "service restart" cmd.

        Args:
            service_name (str): Name of the service to restart.

        Returns:
            str. Command for restarting the service in RHEL6.
        """
        service_action = '/sbin/service {0} restart'\
            .format(service_name)

        return service_action

    @staticmethod
    def get_service_stop_cmd(service_name):
        """Returns a string corresponding to a "service stop" cmd.

        Args:
            service_name (str): Name of the service to stop.

        Returns:
            str. Command for stopping the service in RHEL6.
        """
        service_action = '/sbin/service {0} stop'\
            .format(service_name)

        return service_action

    @staticmethod
    def get_service_start_cmd(service_name):
        """Returns a string corresponding to a "service start" cmd.

        Args:
            service_name (str): Name of the service to start.

        Returns:
            str. Command for starting the service in RHEL6.
        """
        service_action = '/sbin/service {0} start'\
            .format(service_name)

        return service_action

    def get_systemctl_isenabled_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl is-enabled" command.

        Args:
            service_name (str): Name of the service to check.

        Returns:
            str. Command for checking if a service is enabled in RHEL7.
        """
        is_enabled_command = '{0} is-enabled {1}'.\
                         format(self.systemctl_path, service_name)
        return is_enabled_command

    def get_systemctl_disable_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl disable" command.

        Args:
            service_name (str): Name of the service to disable.

        Returns:
            str. Command for disabling a service in RHEL7.
        """
        disable_command = '{0} disable {1}'.\
                         format(self.systemctl_path, service_name)
        return disable_command

    def get_systemctl_status_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl status" check.

        Args:
            service_name (str): Name of the service to check.

        Returns:
            str. Command for checking the status of a service in RHEL7.
        """
        status_command = '{0} status {1}'.\
                         format(self.systemctl_path, service_name)
        return status_command

    def get_systemctl_restart_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl restart" cmd.

        Args:
            service_name (str): Name of the service to restart.

        Returns:
            str. Command for restarting the service in RHEL7.
        """
        restart_cmd = '{0} restart {1}; exit $?'.\
                       format(self.systemctl_path, service_name)
        return restart_cmd

    def get_systemctl_stop_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl stop" cmd.

        Args:
            service_name (str): Name of the service to stop.

        Returns:
            str. Command for stopping the service in RHEL7.
        """
        stop_cmd = '{0} stop {1}; exit $?'.format(self.systemctl_path,
                                                  service_name)
        return stop_cmd

    def get_systemctl_start_cmd(self, service_name):
        """Returns a string corresponding to a "systemctl start" cmd.

        Args:
            service_name (str): Name of the service to start.

        Returns:
            str. Command for starting the service in RHEL7.
        """
        start_cmd = '{0} start {1}; exit $?'.format(self.systemctl_path,
                                                    service_name)
        return start_cmd

    @staticmethod
    def get_copy_cmd(curr_path, new_path, overwrite=True):
        """Returns a string copy command.

        Args:
            curr_path (str): Directory to copy from.

            new_path (str): Directory to copy to.

        Kwargs:
            overwrite (bool): Whether to overwrite existing
                files at the new path. Default is True.

        Returns:
            str. The copy command as a string.
        """
        # By default we overwrite
        cp_arg = "-f"

        if not overwrite:
            cp_arg = "-n"

        cp_path_cmd = "/bin/cp -r %s %s %s" % (cp_arg, curr_path, new_path)

        return cp_path_cmd

    @staticmethod
    def get_move_cmd(curr_path, new_path, overwrite=True):
        """Returns a string move command.

        Args:
            curr_path  (str): Directory to move.

            new_path  (str): Directory to move to.

        Kwargs:
            overwrite (bool): Whether to overwrite existing\
                files at the new path. Default is True.

        Returns:
            str. The move command as a string.
        """
        # By default we overwrite
        mv_arg = "-f"

        if not overwrite:
            mv_arg = "-n"

        mv_path_cmd = "/bin/mv -%s %s %s" % (mv_arg, curr_path, new_path)

        return mv_path_cmd

    @staticmethod
    def get_cat_cmd(filepath, cat_args=''):
        """Returns the command required to view
        the contents of the given filename.

        Args:
            filepath (str): The path/filename to test.

        Kwargs:
            cat_args (str): Optional arguments for the 'cat' command.

        Returns:
            str. Command used to retrieve the contents of the given filename.
        """

        if cat_args != '':
            return '/bin/cat {0} {1}'.format(cat_args, filepath)

        return '/bin/cat {0}'.format(filepath)

    @staticmethod
    def get_file_len_cmd(filepath):
        """Returns the command to use to determine the total length
        of a text file (in lines).

        Args:
            filepath (str): The file to test for length.

        Returns:
            str. Command to get the number of lines in a file.
        """
        return "/bin/cat {0} | wc -l".format(filepath)

    @staticmethod
    def get_rpm_pkg_name(pkg_name, option):
        """Returns the command to get the version of an installed RPM.

        Args:
            pkg_name (str): The package name to check.

            option (str): name/version/source rpm/release/.

        Returns:
            str. Command that will give the value of the option given.
        """

        if not pkg_name:
            raise ValueError("Value passed through for pkg_name is {0}".format(
                pkg_name
                )
            )

        if not option:
            raise ValueError("Value passed through for option is {0}".format(
                option
                )
            )

        if option == "name":
            cmd = "/bin/rpm -qi {0}".format(
                pkg_name
            ) + " | grep Name | grep Relocations | awk '{print $3;}'"
            return cmd
        if option == "version":
            cmd = "/bin/rpm -qi {0}".format(
                pkg_name
            ) + " | grep Version | grep Vendor | awk '{print $3;}'"
            return cmd
        if option == "release":
            cmd = "/bin/rpm -qi {0}".format(
                pkg_name
            ) + " | grep Release | grep Build | awk '{print $3;}'"
            return cmd
        if option == "source rpm":
            cmd = "/bin/rpm -qi {0}".format(
                pkg_name
            ) + " | grep Group | grep -o 'Source RPM: .*' | awk '{print $3;}'"
            return cmd

        raise ValueError("Invalid option given for option")

    @staticmethod
    def check_pkg_installed(pkg_names):
        """Returns the command to get the version of an installed RPM.

        Args:
            pkg_names (list): List of packages to check if installed.

        Returns:
            str. Command that will grep for the given list of packages
                which will be returned in a list if they are installed.
        """

        if pkg_names == []:
            raise ValueError("Empty list passed through for pkg_names")

        cmd = "/bin/rpm -qa"

        if len(pkg_names) > 1:
            cmd = cmd + ' | grep -E "{0}'.format(pkg_names[0])
            for num in range(len(pkg_names) - 1):
                cmd = cmd + "|{0}".format(pkg_names[num + 1])

            cmd = cmd + '"'

        else:
            cmd = cmd + ' | grep "{0}"'.format(pkg_names[0])

        return cmd

    @staticmethod
    def check_yum_repo_cmd():
        """
        Returns the command to get the list of installed yum repos.

        Returns:
            str. Command that will return the list from "yum repolist".
        """

        cmd = "/usr/bin/yum repolist"
        return cmd

    @staticmethod
    def check_repo_cmd(repo_names):
        """
        Returns a "yum repolist" command with a piped grep for the repo name.

        Args:
            repo_names (list): List of repo names to check.

        Returns:
            str. Command that will grep for the given list of repos
                which will be returned in a list if they are installed.
        """
        if repo_names == []:
            raise ValueError("Empty list passed through for pkg_names")

        cmd = "/usr/bin/yum repolist enabled"

        if len(repo_names) > 1:
            cmd = cmd + ' | awk \'{{print $1}}\' | grep -iE "{0}'\
                .format(repo_names[0])
            for num in range(len(repo_names) - 1):
                cmd = cmd + "|{0}".format(repo_names[num + 1])

            cmd = cmd + '"'

        else:
            cmd = cmd + ' | awk \'{{print $1}}\' | grep -i "{0}"'\
                .format(repo_names[0])

        return cmd

    @staticmethod
    def get_yum_install_cmd(package_list):
        """
        Description:
            Get the "yum install" command to install a list of packages.

        Args:
            package_list (list): List of packages to install.

        Returns:
            str. Command that will use yum to install the specified packages.
        """

        return '/usr/bin/yum install -y {0}'.format(' '.join(package_list))

    @staticmethod
    def get_yum_remove_cmd(package_list):
        """
        Description:
            Get the "yum remove" command to uninstall a list of packages.

        Args:
            package_list (list): List of packages to uninstall.

        Returns:
            str. Command that will use yum to uninstall the specified packages.
        """

        return '/usr/bin/yum remove -y {0}'.format(' '.join(package_list))

    @staticmethod
    def get_yum_upgrade_cmd(package_list):
        """
        Description:
            Get the "yum upgrade" command to upgrade a list of packages.

        Args:
            package_list (list): List of packages to upgrade.

        Return:
            str. Command that will use yum to upgrade the specified packages.
        """

        return '/usr/bin/yum upgrade -y {0}'.format(' '.join(package_list))

    def get_createrepo_cmd(self, directory, args='', update=True):
        """
        Description:
            Return the "createrepo" && "yum clean all" commands.
            See notes here:
            `<https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/\
            content/sites/litp2/ERIClitpdocs/latest/plugin_sdk/\
            installation.html>`_

        Args:
            directory (str): Directory where the commands will be run.

        Kwargs:
            args (str) : Optional arguments to supply to createrepo.

            update (bool): If True add --update option in command.
                           Otherwise exclude --update.

        Return:
            str. Command to run both the "createrepo" and
                "yum clean all" commands.
        """
        if update:
            cmd = "/usr/bin/createrepo --update {0} {1} -g {0}/comps.xml"\
                     .format(directory, args)
        else:
            cmd = "/usr/bin/createrepo {0} {1}".format(directory, args)
        yum_clean_all = self.get_yum_cmd("clean all")

        return cmd + " ; " + yum_clean_all

    @staticmethod
    def get_yum_cmd(args):
        """Returns a yum command with the supplied arguments.

        Args:
            args (str): Arguments for the yum command.

        Returns:
            str. Yum command with the given arguments.
        """
        return "/usr/bin/yum {0}".format(args)

    @staticmethod
    def get_does_posix_usr_exist_cmd(username):
        """
        Returns a command that tests whether a posix user exists.

        Args:
            username (str): The username you wish to test.

        Returns:
            str. Command that can be run to test if a user exists.
        """

        return "/usr/bin/id {0}".format(username)

    @staticmethod
    def get_remove_posix_usr_cmd(username):
        """
        Returns a command that removes a user.

        Args:
            username (str): The username you wish to remove.

        Returns:
            str. Command to delete the given user.
        """
        return "/usr/sbin/userdel -rf {0}".format(username)

    def get_ps_cmd(self, args=''):
        """
        Returns a ps command with the supplied arguments.

        Kwargs:
            args (str): Optional arguments for the 'ps' command.

        Returns:
            str. ps command with the given arguments.
        """
        return "{0} {1}".format(self.ps_path, args)

    def get_df_cmd(self, args=''):
        """
        Description:
            Function to return the df cmd with supplied
            arguments.

        Kwargs:
            args (str): Optional arguments for the 'df' command.

        Returns:
            strt. df command with the given arguments.
        """
        return "{0} {1}".format(self.df_path, args)

    def get_timedatectl_cmd(self, args=''):
        """
        Description:
            Function to return the timedatectl cmd with supplied
            arguments. Command is NOT available on RHEL6.

        Kwargs:
            args (str): Optional arguments for the 'timedatectl' command.

        Returns:
            str. timedatectl command with the given arguments.
        """
        return "{0} {1}".format(self.time_path, args)

    def get_package_name_from_rpm(self, local_path_to_rpm):
        """
        Description:
            Function to return a command that will provide the name a package
            will have once installed using the rpm.

        Args:
            local_path_to_rpm (str): The path to the rpm.
        """
        return r'{0} -qpi {1} | {2} -Po "^Name +: \K([\S]*)"'\
               .format(self.rpm_path, local_path_to_rpm, self.grep_path)
