"""
VCS Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""

from redhat_cmd_utils import RHCmdUtils
import re


class VCSUtils(object):

    """VCS command related utilities.
    """
    HAGRP_PATH = "/opt/VRTS/bin/hagrp"

    def __init__(self):
        """Initialise LITP path variables.
        """
        self.rhc = RHCmdUtils()
        self.hares_path = "/opt/VRTS/bin/hares"
        self.hagrp_path = self.HAGRP_PATH
        self.hasys_path = "/opt/VRTSvcs/bin/hasys"
        self.haclus_path = "/opt/VRTSvcs/bin/haclus"

    @staticmethod
    def get_hastatus_sum_cmd():
        """Returns a command to run "hastatus -sum" on a VCS node.

        This command gives a high level summary of the VCS cluster and
        service groups running within it.

        Returns:
            str. The "hastatus -sum" command.
        """

        return "/opt/VRTSvcs/bin/hastatus -sum"

    @staticmethod
    def get_hastatus_sum_sg_list(hastatus_output):
        """Based on output passed through from the "hastatus -sum" command,
        this method parses the output and returns service group names.

        Args:
            hastatus_output (list): List output returned from running:
                "get_hastatus_sum_cmd()".

        Returns:
            list. A list of service groups running in VCS.
        """

        sg_list = []

        for line in hastatus_output:
            if line.startswith("B "):
                sgname = line.split()
                if sgname[1] not in sg_list:
                    sg_list.append(sgname[1])

        return sg_list

    @staticmethod
    def get_hastatus_sg_systems_list(hastatus_output, sgname):
        """Based on output passed through from the "hastatus -sum" command,
        this method parses the output and returns the systems where the passed
        service group is running on.

        Args:
            hastatus_output (list): List output returned from running:
                "get_hastatus_sum_cmd()".

            sgname (str): Name of SG to get system list.

        Returns:
            list. List of systems that a service group is running on.
        """

        sys_list = []

        for line in hastatus_output:
            if line.startswith("B ") and sgname in line:
                sg_name = line.split()
                if sg_name[2] not in sys_list:
                    sys_list.append(sg_name[2])

        return sys_list

    @staticmethod
    def get_hastatus_sg_sys_state(hastatus_output, sgname, system):
        """Based on output passed through from the "hastatus -sum" command,
        this method parses the output for the given service group on
        the given system and returns its status.

        Args:
            hastatus_output (list): List output returned from running:
                "get_hastatus_sum_cmd()".

            sgname (str): Name of SG to get state.

            system (str): System of SG to get state.

        Returns:
            str. State of a service group.
        """

        state = None

        for line in hastatus_output:
            if line.startswith("B ") and sgname in line and system in line:
                sg_name = line.split()
                state = sg_name[5]

        return state

    @staticmethod
    def get_hastatus_sys_state(hastatus_output, system):
        """Based on the output passed through from the "hastatus -sum"
        command, this method parses the output and returns
        the state of the given system.

        Args:
            hastatus_output (list): List output returned from running:
                "get_hastatus_sum_cmd".

            system (str): System to get state of.

        Returns:
            str. State of the given system.
        """

        state = None

        for line in hastatus_output:
            if line.startswith("A ") and system in line:
                sys_name = line.split()
                state = sys_name[2]

        return state

    @staticmethod
    def get_hastatus_sys_list(hastatus_output):
        """Based on output passed through from the "hastatus -sum" command,
        this method parses the output and returns the list of VCS systems.

        Args:
            hastatus_output (list): List output returned from running:
                "get_hastatus_sum_cmd"

        Returns:
            list. List of systems in VCS.
        """

        systems = []

        for line in hastatus_output:
            if line.startswith("A "):
                sys_name = line.split()
                systems.append(sys_name[2])

        return systems

    @staticmethod
    def get_hastop_force(system):
        """
        Returns a command to run a "hastop" command with supplied arguments.
        Stop the VCS server and related processes on all systems
            (the local/specific systems).
        The -force option stops the VCS server, but allows
            the service groups to continue running.

        Args:
            system (str): Target system to be VCS disabled.

        Possible values:
            (-local) = Stops the VCS server on the system on which
                the command is issued. Note that when the VCS server stops a
                 system, the system's service groups are also stopped.

            (-sys node1) =  Stop the VCS server on the running system.

            (-all) = Stops the VCS server on all systems in the cluster and
                take all service groups offline. Note that this specifies
                that the VCS server stops on all systems but that
                service groups continue running.
            For more details please refer to VCS manual.

        Returns:
            str. The "hastop" command to run.
        """
        return "/opt/VRTS/bin/hastop {0} -force".format(system)

    @staticmethod
    def get_hastart():
        """
        Returns a command to run a "hastart" command.
        The hastart command, without options, starts the VCS server
        and related processes on the local system.
        The VCS server and related processes then
        automatically join the cluster.

        Returns:
            str. The "hastart" command to run.
        """
        return '/opt/VRTS/bin/hastart'

    def get_hagrp_cmd(self, args):
        """
        Returns a "hagrp" command with supplied arguments.

        Args:
            args (str): Arguments to pass to the "hagrp" command.

        Returns:
            str. The "hagrp" command to run.
        """
        return "{0} {1}".format(self.hagrp_path, args)

    def get_hares_cmd(self, args):
        """
        Returns a "hares" command with supplied arguments.

        Args:
            args (str): Arguments to pass to the "hares" command.

        Returns:
            str. The "hares" command to run.
        """
        return "{0} {1}".format(self.hares_path, args)

    def get_hagrp_resource_list_cmd(self, sgname):
        """Returns a command to run a "hagrp" command on a VCS node.
        This command gives the list of resources for a given service group.

        Args:
            sgname (str): Name of SG to get state of.

        Returns:
           str. A command to return "/opt/VRTS/bin/hagrp -resources <sg-name>"
        """

        return "{0} -resources {1}".format(self.hagrp_path, sgname)

    def get_resource_attribute_cmd(self, resource_id, attribute):
        """Returns a command to get attribute information for a given resource.

        Args:
            resource_id (str): Name of resource to get attribute of.

            attribute (str): Attribute to get from resource.

        Returns:
            str. The command to get the attribute of a resource.
        """

        return "{0} -display {1} | grep {2}".format(
            self.hares_path, resource_id, attribute)

    def get_service_attribute_cmd(self, cs_id, attribute):
        """Returns a command to get attribute information
           for a given clustered service.

        Args:
            cs_id (str): Name of clustered service to get attribute of.

            attribute (str): Attribute to get from clustered service.

        Returns:
            str. The command to get the attribute of a
                 clustered service.
        """

        return "{0} -display {1} | grep {2}".format(
            self.hagrp_path, cs_id, attribute)

    @staticmethod
    def get_llt_status_cmd():
        """Returns a command to check the status of LLT.

        Returns:
           str. A command to return "/sbin/lltconfig".
        """

        return "/sbin/lltconfig"

    @staticmethod
    def get_llt_stat_cmd(args=''):
        """Returns an lltstat command with n supplied arguments.

        Kwargs:
            args (str): Optional arguments to pass to the lltstat command.

        Returns:
            str. The lltstat command.
        """

        return "/sbin/lltstat {0}".format(args)

    @staticmethod
    def validate_main_cf_cmd():
        """Returns a command that validates the main.cf file in VCS.

        Returns:
            str. Command that validates main.cf. Output will
                be empty if it is ok.
        """

        return "/opt/VRTSvcs/bin/hacf -verify /etc/VRTSvcs/conf/config/"

    def get_haclus_cmd(self, args=''):
        """Returns the "haclus" command.

        Kwargs:
            args (str): Optional arguments to pass to the "hasclus" command.

        Returns:
            str. The "hasclus" command with supplied arguments.
        """

        return "{0} {1}".format(self.haclus_path, args)

    @staticmethod
    def get_gabconfig_cmd():
        """Returns a command that gives cluster membership information.

        Returns:
            str. A command that runs "gabconfig -a".
        """

        return "/sbin/gabconfig -a"

    def get_hasys_cmd(self, args=''):
        """
        Returns the VCS "hasys" command for finding the state of a system.
        Can be used as is or by adding a system (node hostname).

        Kwargs:
            args (str): Optional arguments to supply to "hasys" cmd.

        Returns:
            str. The "hasys" command.
        """
        cmd = "{0} {1}".format(self.hasys_path, args)

        return cmd

    @staticmethod
    def get_hasys_state_cmd():
        """
        Returns the VCS command for finding the state of a system.

        Returns:
            str. The "hasys -state" command.
        """
        cmd = "/opt/VRTSvcs/bin/hasys -state "

        return cmd

    @staticmethod
    def get_hagrp_state_cmd():
        """
        Returns the VCS command for finding the state of a service group.

        Returns:
            str. The "hagrp -state" command.
        """
        cmd = "/opt/VRTSvcs/bin/hagrp -state "

        return cmd

    @staticmethod
    def get_hares_state_cmd():
        """
        Returns the VCS command for finding the state of a resource.

        Returns:
            str. The "hares -state" command.
        """
        cmd = "/opt/VRTSvcs/bin/hares -state "

        return cmd

    @staticmethod
    def get_hagrp_dep_cmd(dep_to_dis):
        """
        Returns the "hagrp" command with service dependencies.

        Args:
            dep_to_dis (str): The name of the service to examine.

        Returns:
            str. The "hagrp -dep" command with service dependencies specified.
        """
        cmd = "/opt/VRTSvcs/bin/hagrp -dep {0}".format(dep_to_dis)

        return cmd

    @staticmethod
    def get_hares_del_cmd(app_to_del):
        """
        Returns the VCS command for deleting a resource.

        Args:
            app_to_del (str): The name of the app to delete.

        Returns:
            str. The "hares" command to delete the specified app.

        """
        cmd = "/opt/VRTSvcs/bin/hares -delete {0}".format(app_to_del)

        return cmd

    @staticmethod
    def get_hagrp_del_cmd(ser_to_del):
        """
        Returns the "hagrp" delete command for deleting a service.

        Args:
            ser_to_del (str): The name of the service to delete.

        Returns:
            str. The "hagrp" command to delete the specified service.
        """
        cmd = "/opt/VRTSvcs/bin/hagrp -delete {0}".format(ser_to_del)

        return cmd

    @staticmethod
    def get_haconf_cmd(args):
        """
        Returns the "haconf" command.

        Args:
            args (str): Arguments to pass to the command.

        Returns:
            str. The "haconf" command with the given arguments.
        """
        cmd = "/opt/VRTSvcs/bin/haconf {0}".format(args)

        return cmd

    @staticmethod
    def generate_clustered_service_name(cs_id, cluster_id):
        """
        Returns the unique clustered service name given both the
        clustered service name and cluster name as input.

        Args:
            cs_id (str): Name of the clustered-service
                item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

        Returns:
            str. Unique name of the VCS service group as it appears in VCS.
        """
        return "Grp_CS_" + cluster_id + "_" + cs_id

    @staticmethod
    def generate_application_resource_name(cs_id, cluster_id, app_id):
        """
        Returns the unique application resource name given the
        clustered service name, cluster name and app name as input.

        Args:
            cs_id (str): Name of the clustered
                service item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

            app_id (str): Name of application item as defined in the model.

        Returns:
            str. Unique name of the VCS application resource as it
                   appears in VCS.
        """
        return "Res_App_" + cluster_id + "_" + cs_id + "_" + app_id

    @staticmethod
    def generate_applications_resource_name(cs_id, cluster_id, app_id):
        """
        Returns the unique applications resource name given the
        clustered service name, cluster name and apps name as input.

        Args:
            cs_id (str): Name of the clustered
                service item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

            app_id (list): Name of applications item as defined in the model.

        Returns:
            list. Unique name of the VCS applications resource as it
                   appears in VCS.
        """
        res_app = []
        for app in app_id:
            res_app.append("Res_App_" + cluster_id + "_" + cs_id + "_" + app)
        return res_app

    @staticmethod
    def generate_ip_resource_name(cs_id, cluster_id, app_id,
                                  network_name, index):
        """
        Returns the unique application resource name given the
        clustered service name, cluster name, app name, network
        name and index as input.

        Args:
            cs_id (str): Name of the clustered
                service item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

            app_id (str): Name of application item as defined in the model.

            network name (str): Network name as defined in the model.

            index (int): Index of the resource within network.

        Returns:
            str. Unique name of application resource as defined in the model.
        """
        return "Res_IP_" + cluster_id + "_" + cs_id + "_" + app_id + \
               "_" + network_name + "_" + str(index)

    @staticmethod
    def generate_ip_resource_name_multi_srvs(cs_id, cluster_id,
                                             network_name, index):
        """
        The following function is potential candidate to be moved to general
        test-utils. (so far is used only by ST testware not from vcs-testware).
        Returns the unique application resource name given the clustered
        service name, cluster name, network name and index as input. This
        method is valid only for multi apps tests.

        Args:
            cs_id (str): Name of the clustered
                service item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

            network name (str): Network name as defined in the model.

            index (int): Index of the resource within network.

        Returns:
            str. Unique name of application resource as defined in the model.
        """
        return "Res_IP_" + cluster_id + "_" + cs_id + \
               "_" + network_name + "_" + str(index)

    @staticmethod
    def generate_nic_proxy_resource_name(cs_id, cluster_id, network_name):
        """
        Returns the unique NIC proxy resource name given the clustered
        service name, cluster name and network name as input.

        Args:
            cs_id (str): Name of the clustered
            service item as defined in the model.

            cluster_id (str): Name of cluster item as defined in the model.

            network name (str): Name of the network.

        Returns:
            str. Unique name of the NIC proxy resource as defined in the model.
        """
        return "Res_NIC_Proxy_" + cluster_id + "_" + cs_id + "_" + \
               network_name

    @staticmethod
    def generate_nic_resource_name(cluster_id, device_name):
        """
        Returns the unique NIC resource name given
        the cluster name and device name as input.

        Args:
            cluster_id (str): Name of cluster item as defined in the model.

            device name (str): Name of the device.

        Returns:
            str. Unique name of the NIC resource as defined in the model.
        """
        return "Res_NIC_" + cluster_id + "_" + device_name

    @staticmethod
    def generate_mount_resource_name(cluster_item_id, cs_item_id,
                                     runtime_item_id, filesystem_id):
        """
        Returns full name of Mount resource based on the parameters passed.

        Args:
            cluster_item_id (str): Cluster item ID.

            cs_item_id (str): Clustered service item ID.

            runtime_item_id (str): Application ID.

            filesystem_id (str): Filesystem ID.

        Returns:
            str. Unique name of the Mount resource as defined in the model.
        """
        return "Res_Mnt_{0}_{1}_{2}_{3}".format(
            cluster_item_id, cs_item_id, runtime_item_id, filesystem_id)

    @staticmethod
    def generate_diskgrp_resource_name(cluster_item_id, cs_item_id,
                                       runtime_item_id, filesystem_id):
        """
        Returns full name of Disk Group resource based
        on the parameters passed.

        Args:
            cluster_item_id (str): Cluster item ID.

            cs_item_id (str): Clustered service item ID.

            runtime_item_id (str): Application ID.

            filesystem_id (str): Filesystem ID.

        Returns:
            str. Unique name of the DiskGroup resource as defined in the model.
        """
        return "Res_DG_{0}_{1}_{2}_{3}".format(
            cluster_item_id, cs_item_id, runtime_item_id, filesystem_id)

    @staticmethod
    def generate_plan_conf(traffic_networks):
        """
        Returns a dictionary which defines the required VCS configuration.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Args:
            traffic_networks (list): List of the traffic networks.

        Returns:
            dict. Dictionary which defines VCS configuration.

        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS1': 'APP1',
            'CS2': 'APP2',
            'CS3': 'APP3',
            'CS4': 'APP4',
            'CS5': 'APP5',
            'CS6': 'APP6',
            'CS7': 'APP7',
            'CS8': 'APP8',
            'CS9': 'APP9',
            'CS10': 'APP10',
            'CS11': 'APP11',
            'CS12': 'APP12',
            'CS13': 'APP13',
            'CS14': 'APP14',
            'CS15': 'APP15',
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS1': [1, 2],
            'CS2': [1, 2],
            'CS3': [1, 2],
            'CS4': [1, 2],
            'CS5': [1, 2],
            'CS6': [1, 2],
            'CS7': [1, 2],
            'CS8': [1, 2],
            'CS9': [1],
            'CS10': [2],
            'CS11': [1],
            'CS12': [2],
            'CS13': [1, 2],
            'CS14': [1, 2],
            'CS15': [2],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS1': {'active': 1, 'standby': 1, 'online_timeout': 180},
            'CS2': {'active': 1, 'standby': 1, 'online_timeout': 180},
            'CS3': {'active': 1, 'standby': 1, 'online_timeout': 180},
            'CS4': {'active': 1, 'standby': 1, 'online_timeout': 30},
            'CS5': {'active': 2, 'standby': 0, 'online_timeout': 180},
            'CS6': {'active': 2, 'standby': 0},
            'CS7': {'active': 2, 'standby': 0, 'online_timeout': 180},
            'CS8': {'active': 2, 'standby': 0, 'online_timeout': 180},
            'CS9': {'active': 1, 'standby': 0, 'online_timeout': 60},
            'CS10': {'active': 1, 'standby': 0},
            'CS11': {'active': 1, 'standby': 0},
            'CS12': {'active': 1, 'standby': 0, 'online_timeout': 60},
            'CS13': {'active': 1, 'standby': 1, 'online_timeout': 180},
            'CS14': {'active': 2, 'standby': 0, 'online_timeout': 180},
            'CS15': {'active': 1, 'standby': 0, 'online_timeout': 60},
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {
            'APP1': ['172.16.100.10'],
            'APP2': ['172.16.100.20',
                     '172.16.200.140',
                     '172.16.200.141'],
            'APP3': ['172.16.200.150',
                     '172.16.100.30',
                     '172.16.100.31'],
            'APP4': [],
            'APP5': [],
            'APP6': ['172.16.100.60',
                     '172.16.100.61'],
            'APP7': ['172.16.200.170',
                     '172.16.200.171',
                     '172.16.200.172',
                     '172.16.200.173'],
            'APP8': ['172.16.200.180',
                     '172.16.200.181',
                     '172.16.200.182',
                     '172.16.200.183',
                     '172.16.100.80',
                     '172.16.100.81'],
            'APP9': ['172.16.200.190'],
            'APP10': ['172.16.200.200',
                      '172.16.200.201'],
            'APP11': [],
            'APP12': ['172.16.100.120',
                      '172.16.100.121',
                      '172.16.100.122',
                      '172.16.200.220'],
            'APP13': ['172.16.100.130',
                      '172.16.200.230',
                      '172.16.200.231'],
            'APP14': ['172.16.200.240',
                      '172.16.200.241',
                      '172.16.200.242',
                      '172.16.200.243',
                      '172.16.100.240',
                      '172.16.100.241'],
            'APP15': ['172.16.100.150',
                      '172.16.100.151',
                      '172.16.100.152',
                      '172.16.200.250'],
        }

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        nets = traffic_networks
        conf["network_per_ip"] = {
            '172.16.100.10': nets[0],
            '172.16.100.20': nets[0],
            '172.16.100.30': nets[0],
            '172.16.100.31': nets[0],
            '172.16.100.60': nets[0],
            '172.16.100.61': nets[0],
            '172.16.100.80': nets[0],
            '172.16.100.81': nets[0],
            '172.16.100.120': nets[0],
            '172.16.100.121': nets[0],
            '172.16.100.122': nets[0],
            '172.16.100.130': nets[0],
            '172.16.100.240': nets[0],
            '172.16.100.241': nets[0],
            '172.16.100.150': nets[0],
            '172.16.100.151': nets[0],
            '172.16.100.152': nets[0],
            '172.16.200.140': nets[1],
            '172.16.200.141': nets[1],
            '172.16.200.150': nets[1],
            '172.16.200.170': nets[1],
            '172.16.200.171': nets[1],
            '172.16.200.172': nets[1],
            '172.16.200.173': nets[1],
            '172.16.200.180': nets[1],
            '172.16.200.181': nets[1],
            '172.16.200.182': nets[1],
            '172.16.200.183': nets[1],
            '172.16.200.190': nets[1],
            '172.16.200.200': nets[1],
            '172.16.200.201': nets[1],
            '172.16.200.220': nets[1],
            '172.16.200.230': nets[1],
            '172.16.200.231': nets[1],
            '172.16.200.240': nets[1],
            '172.16.200.241': nets[1],
            '172.16.200.242': nets[1],
            '172.16.200.243': nets[1],
            '172.16.200.250': nets[1],
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP1": {'EXTR-lsbwrapper1': {'version': '1.1.0-1'},
                     'EXTR-lsbwrapper4': {'version': '1.1.0-1'}},
            "APP2": {'EXTR-lsbwrapper2': {'version': '1.1.0-1'}},
            "APP3": {'EXTR-lsbwrapper3': {'version': '1.1.0-1'},
                     'EXTR-lsbwrapper23': {'version': '1.1.0-1'}},
            "APP4": {},
            "APP5": {'EXTR-lsbwrapper5': {'version': '1.1.0-1'}},
            "APP6": {'EXTR-lsbwrapper6': {'version': '1.1.0-1'}},
            "APP7": {'EXTR-lsbwrapper7': {'noversion': '0'}},
            "APP8": {'EXTR-lsbwrapper8': {'noversion': '0'}},
            "APP9": {'EXTR-lsbwrapper9': {'version': '1.1.0-1'}},
            "APP10": {'EXTR-lsbwrapper10': {'version': '1.1.0-1'}},
            "APP11": {'EXTR-lsbwrapper11': {'version': '1.1.0-1'}},
            "APP12": {'EXTR-lsbwrapper12': {'version': '1.1.0-1'}},
            "APP13": {'EXTR-lsbwrapper13': {'version': '1.1.0-1'}},
            "APP14": {'EXTR-lsbwrapper14': {'version': '1.1.0-1'}},
            "APP15": {'EXTR-lsbwrapper15': {'version': '1.1.0-1'}},
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP1": {
                'name': 'test-lsb-1',
                'user': 'root',
                'service_name': 'test-lsb-1',
                'start_command': '/usr/bin/systemctl start test-lsb-1',
                'stop_command': '/usr/bin/systemctl stop test-lsb-1',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-1 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-1.cleanup'},
            "APP2": {
                'name': 'test-lsb-2',
                'user': 'root',
                'service_name': 'test-lsb-2'},
            "APP3": {
                'name': 'test-lsb-3',
                'service_name': 'test-lsb-3',
                'start_command': '/usr/bin/systemctl start test-lsb-3',
                'stop_command': '/usr/bin/systemctl stop test-lsb-3',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-3 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-3.cleanup'},
            "APP4": {
                'name': 'test-lsb-4',
                'user': 'root',
                'service_name': 'test-lsb-4',
                'start_command': '/usr/bin/systemctl start test-lsb-4',
                'stop_command': '/usr/bin/systemctl stop test-lsb-4',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-4 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-4.cleanup'},
            "APP5": {
                'name': 'test-lsb-5',
                'user': 'root',
                'service_name': 'test-lsb-5',
                'start_command': '/usr/bin/systemctl start test-lsb-5',
                'stop_command': '/usr/bin/systemctl stop test-lsb-5',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-5 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-5.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP6": {
                'name': 'test-lsb-6',
                'user': 'root',
                'service_name': 'test-lsb-6',
                'start_command': '/usr/bin/systemctl start test-lsb-6',
                'stop_command': '/usr/bin/systemctl stop test-lsb-6',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-6 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-6.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP7": {
                'name': 'test-lsb-7',
                'user': 'root',
                'service_name': 'test-lsb-7',
                'start_command': '/usr/bin/systemctl start test-lsb-7',
                'stop_command': '/usr/bin/systemctl stop test-lsb-7',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-7 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-7.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP8": {
                'name': 'test-lsb-8',
                'user': 'root',
                'service_name': 'test-lsb-8',
                'start_command': '/usr/bin/systemctl start test-lsb-8',
                'stop_command': '/usr/bin/systemctl stop test-lsb-8',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-8 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-8.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP9": {
                'name': 'test-lsb-9',
                'user': 'root',
                'service_name': 'test-lsb-9',
                'start_command': '/usr/bin/systemctl start test-lsb-9',
                'stop_command': '/usr/bin/systemctl stop test-lsb-9',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-9 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-9.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP10": {
                'name': 'test-lsb-10',
                'user': 'root',
                'service_name': 'test-lsb-10',
                'start_command': '/usr/bin/systemctl start test-lsb-10',
                'stop_command': '/usr/bin/systemctl stop test-lsb-10',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-10 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-10.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP11": {
                'name': 'test-lsb-11',
                'user': 'root',
                'service_name': 'test-lsb-11',
                'start_command': '/usr/bin/systemctl start test-lsb-11',
                'stop_command': '/usr/bin/systemctl stop test-lsb-11',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-11 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-11.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP12": {
                'name': 'test-lsb-12',
                'user': 'root',
                'service_name': 'test-lsb-12',
                'start_command': '/usr/bin/systemctl start test-lsb-12',
                'stop_command': '/usr/bin/systemctl stop test-lsb-12',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-12 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-12.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP13": {
                'name': 'test-lsb-13',
                'user': 'root',
                'service_name': 'test-lsb-13',
                'status_interval': '20',
                'status_timeout': '20',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP14": {
                'name': 'test-lsb-14',
                'user': 'root',
                'service_name': 'test-lsb-14',
                'start_command': '/usr/bin/systemctl start test-lsb-14',
                'stop_command': '/usr/bin/systemctl stop test-lsb-14',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-14 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-14.cleanup',
                'status_interval': '20',
                'status_timeout': '20',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP15": {
                'name': 'test-lsb-15',
                'user': 'root',
                'service_name': 'test-lsb-15',
                'start_command': '/usr/bin/systemctl start test-lsb-15',
                'stop_command': '/usr/bin/systemctl stop test-lsb-15',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-15 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-15.cleanup',
                'status_interval': '20',
                'status_timeout': '20',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
        }

        return conf

    @staticmethod
    def generate_plan_conf_v6(traffic_networks):
        """
        Returns a dictionary which defines the required VCS
        configuration for IPv6 enabled clustered services.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Args:
            traffic_networks (list): List of the traffic networks.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS16': 'APP16',
            'CS17': 'APP17',
            'CS18': 'APP18',
            'CS20': 'APP20',
            'CS21': 'APP21',

        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS16': [1, 2],
            'CS17': [1, 2],
            'CS18': [1, 2],
            'CS20': [1, 2],
            'CS21': [1, 2],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS16': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS17': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS18': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS20': {'active': 2, 'standby': 0, 'online_timeout': 60},
            'CS21': {'active': 2, 'standby': 0, 'online_timeout': 60},
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {
            'APP16': ['172.16.100.174',
                      '2001:2200:ef::1/64'],
            'APP17': ['172.16.100.175',
                      '2001:2100:ef::2/64',
                      '2001:2100:ef::3/64'],
            'APP18': ['172.16.100.176',
                      '2001:2200:ef::4/64'],
            'APP20': ['172.16.100.178',
                      '2001:2100:ef::6/64',
                      '172.16.100.180',
                      '2001:2100:ef::9/64'],
            'APP21': ['172.16.100.179',
                      '172.16.100.189',
                      '2001:2200:ef::7/64',
                      '2001:2200:ef::8/64'],
        }

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        nets = traffic_networks
        conf["network_per_ip"] = {
            '172.16.100.174': nets[0],
            '172.16.100.175': nets[0],
            '172.16.100.176': nets[0],
            '172.16.100.178': nets[0],
            '172.16.100.179': nets[0],
            '172.16.100.180': nets[0],
            '172.16.100.189': nets[0],
            '2001:2100:ef::2/64': nets[0],
            '2001:2100:ef::3/64': nets[0],
            '2001:2100:ef::6/64': nets[0],
            '2001:2100:ef::9/64': nets[0],
            '2001:2200:ef::1/64': nets[1],
            '2001:2200:ef::4/64': nets[1],
            '2001:2200:ef::7/64': nets[1],
            '2001:2200:ef::8/64': nets[1],
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP16": {'EXTR-lsbwrapper16': {'version': '1.1.0-1'}},
            "APP17": {'EXTR-lsbwrapper17': {'version': '1.1.0-1'}},
            "APP18": {'EXTR-lsbwrapper18': {'version': '1.1.0-1'}},
            "APP20": {'EXTR-lsbwrapper20': {'version': '1.1.0-1'}},
            "APP21": {'EXTR-lsbwrapper21': {'version': '1.1.0-1'}}
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP16": {
                'name': 'test-lsb-16',
                'user': 'root',
                'service_name': 'test-lsb-16',
                'start_command': '/usr/bin/systemctl start test-lsb-16',
                'stop_command': '/usr/bin/systemctl stop test-lsb-16',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-16 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-16.cleanup'},
            "APP17": {
                'name': 'test-lsb-17',
                'user': 'root',
                'service_name': 'test-lsb-17',
                'start_command': '/usr/bin/systemctl start test-lsb-17',
                'stop_command': '/usr/bin/systemctl stop test-lsb-17',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-17 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-17.cleanup'},
            "APP18": {
                'name': 'test-lsb-18',
                'user': 'root',
                'service_name': 'test-lsb-18',
                'start_command': '/usr/bin/systemctl start test-lsb-18',
                'stop_command': '/usr/bin/systemctl stop test-lsb-18',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-18 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-18.cleanup'},
            "APP20": {
                'name': 'test-lsb-20',
                'user': 'root',
                'service_name': 'test-lsb-20',
                'start_command': '/usr/bin/systemctl start test-lsb-20',
                'stop_command': '/usr/bin/systemctl stop test-lsb-20',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-20 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-20.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
            "APP21": {
                'name': 'test-lsb-21',
                'user': 'root',
                'service_name': 'test-lsb-21',
                'start_command': '/usr/bin/systemctl start test-lsb-21',
                'stop_command': '/usr/bin/systemctl stop test-lsb-21',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-21 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-21.cleanup',
                'restart_limit': '10',
                'startup_retry_limit': '10'},
        }

        return conf

    @staticmethod
    def generate_plan_conf_cs_filesystem():
        """
        Returns a dictionary which defines the required VCS configuration.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # List of VCS clustered services names and associated run-time names
        conf['app_per_cs'] = {
            'CS22': 'APP22',
        }

        # List of nodes defined per vcs-clustered-service
        conf['nodes_per_cs'] = {
            'CS22': [1, 2],
        }

        # Parameters per clustered-service
        conf['params_per_cs'] = {
            'CS22': {'active': 1, 'standby': 1, 'online_timeout': 180},
        }

        # List of IP resources per run-time in a clustered service
        conf['ip_per_app'] = {
            'APP22': [],
        }

        # List of IP addresses and their associated networks
        conf["network_per_ip"] = {}

        # List of packages that will exist per run-time
        conf["pkg_per_app"] = {
            "APP22": {'EXTR-lsbwrapper22': {'version': '1.1.0-1'}},
        }

        # List of properties per lsb runtime
        conf["lsb_app_properties"] = {
            "APP22": {
                'service_name': 'test-lsb-22',
                'start_command': '/usr/bin/systemctl start test-lsb-22',
                'stop_command': '/usr/bin/systemctl stop test-lsb-22',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-22 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-22.cleanup'},
        }

        return conf

    @staticmethod
    def generate_plan_conf_cs_online_offline_timeout():
        """
        Returns a dictionary which define the required VCS configuration.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as single node.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # List of VCS clustered services names and associated run-time names
        conf['app_per_cs'] = {
            'CS44': 'APP57',
            'CS45': 'APP58',
        }

        # List of nodes defined per vcs-clustered-service
        conf['nodes_per_cs'] = {
            'CS44': [1],
            'CS45': [2],
        }

        # Parameters per clustered-service
        conf['params_per_cs'] = {
            'CS44': {'active': 1, 'standby': 0, 'online_timeout': 180},
            'CS45': {'active': 1, 'standby': 0, 'offline_timeout': 401},
        }

        # List of IP resources per run-time in a clustered service
        conf['ip_per_app'] = {
            'APP57': [],
            'APP58': [],
        }

        # List of IP addresses and their associated networks
        conf["network_per_ip"] = {}

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP57": {'EXTR-lsbwrapper57': {'version': '1.1.0-1'}},
            "APP58": {'EXTR-lsbwrapper58': {'version': '1.1.0-1'}},
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP57": {
                'service_name': 'test-lsb-57',
                'start_command': '/usr/bin/systemctl start test-lsb-57',
                'stop_command': '/usr/bin/systemctl stop test-lsb-57',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-57 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-57.cleanup'},
            "APP58": {
                'service_name': 'test-lsb-58',
                'start_command': '/usr/bin/systemctl start test-lsb-58',
                'stop_command': '/usr/bin/systemctl stop test-lsb-58',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-58 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-58.cleanup'},
        }

        conf["ha_service_config_properties"] = {
            "CS44": {'restart_limit': '10',
                     'startup_retry_limit': '10'},
            "CS45": {'restart_limit': '10',
                     'startup_retry_limit': '10'},
        }

        return conf

    @staticmethod
    def generate_plan_conf_expanded_cluster():
        """
        Returns a dictionary which defines the required VCS configuration for
        clustered services on an expanded cluster.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS37': 'APP37',
            'CS38': 'APP38',
            'CS26': 'APP26',
            'CS27': 'APP27'
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS37': [1, 3],
            'CS38': [1],
            'CS26': [1, 2, 3],
            'CS27': [1, 3]
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS37': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS38': {'active': 1, 'standby': 0, 'online_timeout': 60},
            'CS26': {'active': 3, 'standby': 0, 'online_timeout': 60},
            'CS27': {'active': 2, 'standby': 0, 'online_timeout': 60}
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {
            'APP37': [],
            'APP38': [],
            'APP26': [],
            'APP27': []
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP37": {'EXTR-lsbwrapper37': {'version': '1.1.0-1'}},
            "APP38": {'EXTR-lsbwrapper38': {'version': '1.1.0-1'}},
            "APP26": {'EXTR-lsbwrapper26': {'version': '1.1.0-1'}},
            "APP27": {'EXTR-lsbwrapper27': {'version': '1.1.0-1'}}
        }

        conf["network_per_ip"] = {
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP37": {
                'name': 'test-lsb-37',
                'user': 'root',
                'service_name': 'test-lsb-37',
                'start_command': '/usr/bin/systemctl start test-lsb-37',
                'stop_command': '/usr/bin/systemctl stop test-lsb-37',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-37 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-37.cleanup'},
            "APP38": {
                'name': 'test-lsb-38',
                'user': 'root',
                'service_name': 'test-lsb-38',
                'start_command': '/usr/bin/systemctl start test-lsb-38',
                'stop_command': '/usr/bin/systemctl stop test-lsb-38',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-38 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-38.cleanup'},
            "APP26": {
                'name': 'test-lsb-26',
                'user': 'root',
                'service_name': 'test-lsb-26',
                'start_command': '/usr/bin/systemctl start test-lsb-26',
                'stop_command': '/usr/bin/systemctl stop test-lsb-26',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-26 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-26.cleanup'},
            "APP27": {
                'name': 'test-lsb-27',
                'user': 'root',
                'service_name': 'test-lsb-27',
                'start_command': '/usr/bin/systemctl start test-lsb-27',
                'stop_command': '/usr/bin/systemctl stop test-lsb-27',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-27 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-27.cleanup'}
        }

        return conf

    @staticmethod
    def generate_plan_conf_service():
        """
        Returns a dictionary which defines the required VCS configuration for
        clustered services to be created with class type service rather than
        lsb-runtime.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS28': 'APP28',
            'CS29': 'APP29',
            'CS30': 'APP30',
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS28': [1, 2],
            'CS29': [1],
            'CS30': [1, 2],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS28': {'active': 2, 'standby': 0, 'online_timeout': 60},
            'CS29': {'active': 1, 'standby': 0, 'online_timeout': 60},
            'CS30': {'active': 1, 'standby': 1, 'online_timeout': 60},
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {
            'APP28': [],
            'APP29': [],
            'APP30': [],
        }

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        conf["network_per_ip"] = {
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP28": {'EXTR-lsbwrapper28': {'version': '1.1.0-1'},
                      'EXTR-lsbwrapper30': {'version': '1.1.0-1'}},
            "APP29": {'EXTR-lsbwrapper29': {'version': '1.1.0-1'}},
            "APP30": {},
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP28": {
                'service_name': 'test-lsb-28',
                'start_command': '/usr/bin/systemctl start test-lsb-28',
                'stop_command': '/usr/bin/systemctl stop test-lsb-28',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-28 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-28.cleanup'},
            "APP29": {
                'service_name': 'test-lsb-29',
                'start_command': '/usr/bin/systemctl start test-lsb-29',
                'stop_command': '/usr/bin/systemctl stop test-lsb-29',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-29 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-29.cleanup'},
            "APP30": {
                'service_name': 'test-lsb-30',
                'start_command': '/usr/bin/systemctl start test-lsb-30',
                'stop_command': '/usr/bin/systemctl stop test-lsb-30',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-30 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-30.cleanup'},
        }

        return conf

    @staticmethod
    def generate_plan_conf_service_and_vip_children(traffic_networks):
        """
        Returns a dictionary which defines the required VCS configuration for
        VCS clustered services which shall contain a ha-service-config child.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Args:
            traffic_networks (list): List of the traffic networks.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS31': 'APP31',
            'CS32': 'APP32',
            'CS33': 'APP33',
            'CS34': 'APP34',
            'CS35': 'APP35',
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {'APP31': ["172.16.100.181",
                                        "172.16.100.182",
                                        "2001:2200:ef::10/64",
                                        "2001:2200:ef::11/64"],
                              'APP32': ["172.16.100.183",
                                        "172.16.100.184",
                                        "2001:2200:ef::12/64",
                                        "2001:2200:ef::13/64"],
                              'APP33': ["172.16.100.185",
                                        "172.16.100.186",
                                        "2001:2200:ef::14/64",
                                        "2001:2200:ef::15/64"],
                              'APP34': ["172.16.100.187",
                                        "172.16.100.188"],
                              'APP35': ["2001:2200:ef::16/64",
                                        "2001:2200:ef::17/64"]}

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        nets = traffic_networks
        conf["network_per_ip"] = {
            '172.16.100.181': nets[0],
            '172.16.100.182': nets[0],
            '172.16.100.183': nets[0],
            '172.16.100.184': nets[0],
            '172.16.100.185': nets[0],
            '172.16.100.186': nets[0],
            '172.16.100.187': nets[0],
            '172.16.100.188': nets[0],
            '2001:2200:ef::10/64': nets[1],
            '2001:2200:ef::11/64': nets[1],
            '2001:2200:ef::12/64': nets[1],
            '2001:2200:ef::13/64': nets[1],
            '2001:2200:ef::14/64': nets[1],
            '2001:2200:ef::15/64': nets[1],
            '2001:2200:ef::16/64': nets[1],
            '2001:2200:ef::17/64': nets[1],
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS31': [1, 2],
            'CS32': [1, 2],
            'CS33': [1],
            'CS34': [1, 2],
            'CS35': [1, 2],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS31': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS32': {'active': 2, 'standby': 0, 'online_timeout': 60},
            'CS33': {'active': 1, 'standby': 0, 'online_timeout': 60},
            'CS34': {'active': 1, 'standby': 1, 'online_timeout': 60},
            'CS35': {'active': 1, 'standby': 1, 'online_timeout': 60},
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP31": {'EXTR-lsbwrapper31': {'version': '1.1.0-1'}},
            "APP32": {'EXTR-lsbwrapper32': {'version': '1.1.0-1'}},
            "APP33": {'EXTR-lsbwrapper33': {'version': '1.1.0-1'}},
            "APP34": {'EXTR-lsbwrapper34': {'version': '1.1.0-1'}},
            "APP35": {'EXTR-lsbwrapper35': {'version': '1.1.0-1'}}
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP31": {
                'service_name': 'test-lsb-31',
                'start_command': '/usr/bin/systemctl start test-lsb-31',
                'stop_command': '/usr/bin/systemctl stop test-lsb-31',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-31 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-31.cleanup'},
            "APP32": {
                'service_name': 'test-lsb-32',
                'start_command': '/usr/bin/systemctl start test-lsb-32',
                'stop_command': '/usr/bin/systemctl stop test-lsb-32',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-32 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-32.cleanup'},
            "APP33": {
                'service_name': 'test-lsb-33',
                'start_command': '/usr/bin/systemctl start test-lsb-33',
                'stop_command': '/usr/bin/systemctl stop test-lsb-33',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-33 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-33.cleanup'},
            "APP34": {
                'service_name': 'test-lsb-34',
                'start_command': '/usr/bin/systemctl start test-lsb-34',
                'stop_command': '/usr/bin/systemctl stop test-lsb-34',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-34 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-34.cleanup'},
            "APP35": {
                'service_name': 'test-lsb-35',
                'start_command': '/usr/bin/systemctl start test-lsb-35',
                'stop_command': '/usr/bin/systemctl stop test-lsb-35',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-35 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-35.cleanup'},
        }

        conf["ha_service_config_properties"] = {
            "CS31": {},
            "CS32": {'restart_limit': '10',
                     'startup_retry_limit': '10'},
            "CS33": {'restart_limit': '10',
                     'startup_retry_limit': '10'},
            "CS34": {},
            "CS35": {}
        }

        return conf

    @staticmethod
    def generate_plan_conf_priority_order():
        """
        Returns a dictionary which defines the required VCS configuration for
        clustered services to be created with class type service rather than
        lsb-runtime.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS24': 'APP24',
            'CS25': 'APP25',
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS24': [2, 1],
            'CS25': [2, 1],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            # Parallel (2 active nodes)
            'CS24': {'active': 2, 'standby': 0, 'online_timeout': 60},
            # Failover (standby > 0)
            'CS25': {'active': 1, 'standby': 1, 'online_timeout': 60},
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {
            'APP24': [],
            'APP25': [],
        }

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        conf["network_per_ip"] = {
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP24": {'EXTR-lsbwrapper24': {'version': '1.1.0-1'}},
            "APP25": {'EXTR-lsbwrapper25': {'version': '1.1.0-1'}},
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================
        conf["lsb_app_properties"] = {
            "APP24": {
                'service_name': 'test-lsb-24',
                'stop_command': '/usr/bin/systemctl stop test-lsb-24',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-24 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-24.cleanup'},
            "APP25": {
                'service_name': 'test-lsb-25',
                'start_command': '/usr/bin/systemctl start test-lsb-25',
                'stop_command': '/usr/bin/systemctl stop test-lsb-25',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-25 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-25.cleanup'},
        }
        return conf

    @staticmethod
    def generate_plan_conf_single_node(traffic_networks):
        """
        Returns a dictionary which defines the required VCS configuration for
        VCS clustered services which shall contain a ha-service-config child.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Args:
            traffic_networks (list): List of the traffic networks.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS39': 'APP39',
        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {'APP39': ["172.16.100.191",
                                        "172.16.200.191"]}

        ######################################################
        # List of IP addresses and their associated networks #
        # as per                                             #
        #   https://confluence-oss.lmera.ericsson.se/        #
        #           display/ELITP/2.1.6+Test+Setup           #
        ######################################################
        nets = traffic_networks
        conf["network_per_ip"] = {
            '172.16.100.191': nets[0],
            '172.16.200.191': nets[1],
        }

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS39': [1],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS39': {'active': 1, 'standby': 0, 'online_timeout': 60},
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP39": {'EXTR-lsbwrapper39': {'version': '1.1.0-1'}},
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP39": {
                'service_name': 'test-lsb-39',
                'start_command': '/usr/bin/systemctl start test-lsb-39',
                'stop_command': '/usr/bin/systemctl stop test-lsb-39',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-39 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-39.cleanup'},
        }

        conf["ha_service_config_properties"] = {
            "CS39": {'restart_limit': '10',
                     'startup_retry_limit': '10'},
        }

        return conf

    @staticmethod
    def define_online_ordering_depencencies_kgb():
        """
        Returns a dictionary of clustered-services which define
        their VCS onlining order.

        Returns:
            dict. Dictionary which defines online dependencies.
        """
        online_dependencies = {'CS28': ['CS32', 'CS2'],
                               'CS35': ['CS32'],
                               'CS32': ['CS31'],
                               'CS31': ['CS34'],
                               'CS34': ['CS2'],
                               'CS9': ['CS1'],
                               'CS10': ['CS12'],
                               'CS5': ['CS6'],
                               'CS7': ['CS8'],
                               'CS3': ['CS2', 'CS6', 'CS4', 'CS5',
                                       'CS1', 'CS7', 'CS8', 'CS31',
                                       'CS32', 'CS34']}
        return online_dependencies

    @staticmethod
    def generate_plan_conf_ha_service_config():
        """
        Returns a dictionary which defines the required VCS configuration for
        VCS clustered services which shall contain a ha-service-config child.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a VCS configuration.

        2. Verify that the VCS configuration has been deployed correctly.

        3. Used as a baseline for other tests such as failover.

        Returns:
            dict. Dictionary which defines VCS configuration.
        """

        conf = {}

        # ===================================================================
        # List of VCS clustered services names and associated run-time names.
        # Only 1 runtime per clustered service is currently allowed.
        # ===================================================================
        conf['app_per_cs'] = {
            'CS36': 'APP36',

        }

        # =========================================================
        # List of IP resources per run-time in a clustered service
        # =========================================================
        conf['ip_per_app'] = {'APP36': []}

        ######################################################
        # List of IP addresses and their associated networks #
        ######################################################
        conf["network_per_ip"] = {}

        # ======================================================
        # List of nodes defined per vcs-clustered-service.
        # Assumption is that at most a 2 node vcs-cluster exists
        # which allows either 1 or 2 node clustered-service.
        # ======================================================
        conf['nodes_per_cs'] = {
            'CS36': [1, 2],
        }

        # ================================
        # Parameters per clustered-service
        # ================================
        conf['params_per_cs'] = {
            'CS36': {'active': 2, 'standby': 0, 'online_timeout': 60},
        }

        # ==============================================
        # List of packages that will exist per run-time
        # ==============================================
        conf["pkg_per_app"] = {
            "APP36": {'EXTR-lsbwrapper36': {'version': '1.1.0-1'}}
        }

        # ==================================
        # List of properties per lsb runtime
        # ==================================

        conf["lsb_app_properties"] = {
            "APP36": {
                'service_name': 'test-lsb-36',
                'start_command': '/usr/bin/systemctl start test-lsb-36',
                'stop_command': '/usr/bin/systemctl stop test-lsb-36',
                'status_command': '/usr/share/litp/vcs_lsb_status test-lsb-36 '
                                  'status',
                'cleanup_command': '/bin/touch /tmp/test-lsb-36.cleanup'},
        }

        conf["ha_service_config_properties"] = {
            "CS36": {'status_interval': '18',
                     'status_timeout': '17',
                     'restart_limit': '16',
                     'startup_retry_limit': '15'}
        }

        return conf

    @staticmethod
    def verify_vcs_systems_ok(nodes_urls, hasys_state):
        """
        Returns False if the state of any
        of the VCS systems is not online.

        Args:
            nodes_urls (list): List of the node URLs as
                defined under the vcs-cluster.

            hasys_state (list): Output from the VCS "hasys -state" command.

        Returns:
            bool. Returns True if all VCS systems are online.
        """
        # Nr of nodes in VCS cluster
        nr_of_nodes_cluster = len(nodes_urls)

        # Count of nr of systems in state running
        total_nr_state_running = 0

        # Loop through output from command and count
        # the number of systems online
        for line in hasys_state:
            if re.search(r'\S+\s+\S+\s+RUNNING', line):
                total_nr_state_running = total_nr_state_running + 1

        # All nodes in VCS cluster should be online
        if nr_of_nodes_cluster == total_nr_state_running:
            return True
        return False

    def generate_ip_resource_names_from_conf(self, conf, cluster_id):
        """
        Returns a dictionary containing IP resource names that are
        expected to exist in the cluster, based on the passed configuration.

        Args:
            conf (dict): Tested cluster configuration.

            cluster_id (str): ID of the cluster in the model.

        Returns:
            dict. Names of the IP resources as keys of the dictionary.
            The values are dictionaries in the format:

            |   {
            |        "online": expected_online_count,
            |        "offline": expected_offline_count
            |   }

        """
        ip_resources_dict = {}

        unique_networks = set(conf["network_per_ip"].values())
        for clustered_service in conf["app_per_cs"]:
            cs_params = conf["params_per_cs"][clustered_service]
            cs_active_count = cs_params["active"]
            app_name = conf["app_per_cs"][clustered_service]

            for network_name in unique_networks:
                # Get number of application's IP addresses belonging
                # to this network
                app_ips_per_network = 0
                for ip_addr in conf["ip_per_app"][app_name]:
                    if conf["network_per_ip"][ip_addr] == network_name:
                        app_ips_per_network += 1

                app_ips_per_node = int(app_ips_per_network / cs_active_count)
                for index in range(1, app_ips_per_node + 1):
                    ip_res_name = self.generate_ip_resource_name(
                        clustered_service,
                        cluster_id,
                        app_name,
                        network_name,
                        index)
                    ip_resources_dict[ip_res_name] = {
                        "online": cs_params["active"],
                        "offline": cs_params["standby"],
                    }

        return ip_resources_dict

    @staticmethod
    def cnt_instances_of_reg_ex(reg_ex, text_list):
        """
        Function which counts the number of times a reg_ex appears in a list.

        Arg:
            reg_ex (regular_expression): Compile regular expression.

            text_list (list): List of text.

        Returns:
            int. Number of times the regular expression appears in the list.
        """
        cnt = 0
        for line in text_list:
            if re.search(reg_ex, line):
                cnt = cnt + 1

        return cnt

    def verify_vcs_clustered_services(self, cs_key, cluster_id, conf, hagrp,
                                      hares, net_dev_map):
        """
        Function which verifies whether a clustered-service and
        all of its resources are online on the correct nodes.

        Args:
            cs_key (str): Clustered Service name; key used in the conf.

            cluster_id (str): ID of the cluster in the model.

            conf (dict): Definition of the expected configuration.

            hagrp (list): Output of the VCS "hagrp -state" command.

            hares (list): Output of the VCS "hares -state" command.

            net_dev_map (dict): Network names and their device name.

        Returns:
            bool. True if all groups and resources are okay, False otherwise.
        """
        # VCS group name of clustered-service
        cs_name = self.generate_clustered_service_name(cs_key,
                                                       cluster_id)

        # Properties of clustered-service used during its creation
        cs_params = conf["params_per_cs"][cs_key]

        # Nodes per clustered-service
        cs_nodes = conf["nodes_per_cs"][cs_key]

        # Name of lsb runtine app as defined in configuration
        app_name = conf["app_per_cs"][cs_key]

        # VCS resource name of lsb runtime
        app_res_name = self.generate_application_resource_name(
            cs_key,
            cluster_id,
            app_name)

        # ===================================================
        # For each clustered service verify that it is online
        # in N nodes, where N depends on availability model
        # of the CS.
        # ===================================================

        reg_ex = re.compile(cs_name + r'\s+State\s+\s+\S+\s+\|?ONLINE\|?')
        active_cnt = self.cnt_instances_of_reg_ex(reg_ex, hagrp)

        # Return False if resource is not online on correct number of nodes
        if cs_params["active"] != active_cnt:
            return False

        # ================================================
        # Verify that all application resources are online
        # ================================================
        reg_ex = re.compile(app_res_name + r'\s+State\s+\s+\S+\s+\|?ONLINE\|?')
        active_cnt = self.cnt_instances_of_reg_ex(reg_ex, hares)

        # Return False if resource is not online on correct number of nodes
        if cs_params["active"] != active_cnt:
            return False

        # ============================================================
        # Verify that all NIC Proxy resources are in place and online
        # ============================================================

        # List of what network the IP resources are on
        ip_networks = []
        for ip_addr in conf["ip_per_app"][app_name]:
            ip_network = conf["network_per_ip"][ip_addr]
            ip_networks.append(ip_network)

        for network_name in set(ip_networks):
            # VCS resource name for NIC proxy
            nic_proxy_res_name = self.generate_nic_proxy_resource_name(
                cs_key, cluster_id, network_name)

            reg_ex = re.compile(nic_proxy_res_name +
                                r'\s+State\s+\s+\S+\s+\|?ONLINE\|?')
            active_cnt = self.cnt_instances_of_reg_ex(reg_ex, hares)

            # Return False if resource is not online on correct number of nodes
            if len(cs_nodes) != active_cnt:
                return False

        # ========================================
        # Verify that all IP resources are online
        # ========================================

        # VCS resource names for the IPs
        expected_ip_resources = \
            self.generate_ip_resource_names_from_conf(conf, cluster_id)

        network_ip_cnt = {}
        for device in net_dev_map:
            if 'network_name' in net_dev_map[device].keys():
                network_ip_cnt[net_dev_map[device]['network_name']] = 1

        for ip_address in conf['ip_per_app'][app_name]:
            network_name = conf["network_per_ip"][ip_address]
            ip_res_name = self.generate_ip_resource_name(cs_key, cluster_id,
                                                         app_name,
                                                         network_name,
                                                         network_ip_cnt
                                                         [network_name])

            network_ip_cnt[network_name] = network_ip_cnt[network_name] + 1

            # Only check for resources that we are expecting.
            # In parallel service groups 2 or more IPs may exist in the
            # same IP resource.
            if ip_res_name in expected_ip_resources:

                reg_ex = re.compile(ip_res_name +
                                    r'\s+State\s+\s+\S+\s+\|?ONLINE\|?')
                active_cnt = self.cnt_instances_of_reg_ex(reg_ex, hares)

                # Return False if resource is not online on correct
                # number of nodes
                if expected_ip_resources[ip_res_name]["online"] != active_cnt:
                    return False

                reg_ex = re.compile(ip_res_name +
                                    r'\s+State\s+\s+\S+\s+\|?OFFLINE\|?')
                offline_cnt = self.cnt_instances_of_reg_ex(reg_ex, hares)

                # Return False if resource is not offline on
                # correct number of nodes
                if expected_ip_resources[ip_res_name]["offline"] != \
                        offline_cnt:
                    return False
        return True

    def add_online_dep_for_clustered_service(self, clustered_service,
                                             online_dep, options):
        """
        This function will add dependency_list option to
        the existing options required to create a clustered service.

        Args:
            clustered_service (str): Clustered Service name; key
                used in the conf.

            online_dep (dict): List of dependencies per clustered_service.

            options (str): Existing options used to create a clustered_service.

        Returns:
            (dict): Updated list of options to be used in the create command.
        """
        # If online_dep hasn't been defined then default it
        # to the version used in KGB
        if online_dep is None:
            online_dep = self.define_online_ordering_depencencies_kgb()

        # If the clustered-service has defined dependencies
        if clustered_service in online_dep.keys():
            dependency_list = ' dependency_list="' + \
                              ','.join(online_dep[clustered_service]) + \
                              '"'

            options += dependency_list

        return options

    def generate_cli_commands(self, vcs_cluster, conf, clustered_service,
                              app_class="lsb-runtime", online_dep=None):
        """
        Function to generate CLI commands that will setup the supplied
        VCS clustered-services, IPs and lsb resources.
        They will be in format so they can be used with the
        execute_cli_<create/link>_cmd functions.

        Args:
            vcs_cluster (str): URL of the VCS cluster.

            conf (dict): The required configuration of clustered-services.

            clustered_service (str): Name of clustered service as
                defined in configuration.

        Kwargs:
            app_class (str): Class name of the application item
                       ("lsb-runtime" | "service" | "vm-service").

            online_dep (dict): List of dependencies per clustered_service.

        Returns:
            dict. Dictionary of CLI commands.
        """
        # Counter to be used to help generate the different IP items
        ip_counter = 1

        # Empty list of dictionaries to be built up and returned
        ip_data = []
        pkg_data = []
        ha_config_data = {}
        pkg_links_data = []

        # Clustered-service URL
        cs_url = vcs_cluster + '/services/' + clustered_service

        # Properties for clustered-service
        cs_params = conf["params_per_cs"][clustered_service]

        #########################################
        # Define clustered service in the model #
        #########################################
        class_type = "vcs-clustered-service"
        options = "active={0} standby={1} name='{2}'".format(
            cs_params["active"], cs_params["standby"], clustered_service)

        if 'online_timeout' in cs_params:
            options += " online_timeout={0}".format(
                cs_params['online_timeout'])
        elif 'offline_timeout' in cs_params:
            options += " offline_timeout={0}".format(
                cs_params['offline_timeout'])

        options = self.add_online_dep_for_clustered_service(clustered_service,
                                                            online_dep,
                                                            options)

        cs_data = {'url': cs_url,
                   'class_type': class_type,
                   'options': options}

        ################################################################
        # Define the lsb app which resides under the clustered service #
        ################################################################
        application = conf["app_per_cs"][clustered_service]
        app_properties = conf["lsb_app_properties"][application]
        app_url_in_cluster = None
        if app_class == "lsb-runtime":
            app_url = cs_url + '/runtimes/' + application
            class_type = "lsb-runtime"
        else:
            app_url = '/software/services/' + application
            class_type = app_class
            app_url_in_cluster = cs_url + '/applications/' + application

        options = []
        for prop in app_properties:
            options.append(prop + "='" + app_properties[prop] + "'")
        option_str = " ".join(options)

        app_data = {'url': app_url,
                    'class_type': class_type,
                    'options': option_str}
        if app_url_in_cluster:
            app_data['app_url_in_cluster'] = app_url_in_cluster

        ###############################################################
        # Define any ha config properties under the clustered service #
        ###############################################################
        if 'ha_service_config_properties' in conf.keys():
            ha_config_url = cs_url + '/ha_configs/service_config'
            class_type = "ha-service-config"
            ha_props = conf["ha_service_config"
                            "_properties"][clustered_service]
            options = ""
            for ha_prop in ha_props:
                value = conf["ha_service_config"
                             "_properties"][clustered_service][ha_prop]
                options = options + ha_prop + '=' + value + ' '
            ha_config_data = {'url': ha_config_url,
                              'class_type': class_type,
                              'options': options}

        ##################################################
        # Define the IPs which reside under the lsb-app #
        ##################################################
        ip_addresses = conf["ip_per_app"][application]
        parent_url = self.define_ip_res_cli_parent_url(app_class,
                                                       cs_url, app_url)
        for ip_address in ip_addresses:
            ip_url = parent_url + '/ipaddresses/ip' + str(ip_counter)
            ip_network = conf["network_per_ip"][ip_address]
            class_type = "vip"
            options = "ipaddress='{0}' network_name='{1}'".format(
                ip_address, ip_network)

            ip_data.append({'url': ip_url,
                            'class_type': class_type,
                            'options': options})
            ip_counter += 1

        ##################################################
        # Create Packages under /software/items and link #
        # packages to items under VCS cluster ############
        ##################################################
        packages_url = "/software/items/"
        packages = conf["pkg_per_app"][application]
        for pkg in packages:
            pkg_url = packages_url + pkg
            options = "name='" + pkg + "'"
            for version in conf["pkg_per_app"][application][pkg]:
                if version == 'version':
                    options = options + ' version' + "=" + \
                              conf["pkg_per_app"][application][pkg]['version']
            class_type = 'package'
            pkg_data.append({'url': pkg_url,
                             'class_type': class_type,
                             'options': options})

            link_url = app_url + '/packages/' + pkg
            pkg_links_data.append({'child_url': link_url,
                                   'class_type': class_type,
                                   'parent_url': pkg_url})

        full_list = {}
        full_list['cs'] = cs_data
        full_list['apps'] = app_data
        full_list['pkgs'] = pkg_data
        full_list['ips'] = ip_data
        full_list['pkg_links'] = pkg_links_data
        full_list['ha_service_config'] = ha_config_data

        return full_list

    def cluster_service_model_definition(self, clustered_service, vcs_cluster,
                                         cs_params, online_dep):
        """
        Function to define clustered service in the model.
        The output is used from the generate_cli_commands_multi_srvs function.

        Args:
            clustered_service (str): Name of clustered service as
                defined in configuration.

            vcs_cluster (str): URL of the VCS cluster.

            cs_params (dict): The required configuration of clustered-services.

            online_dep (str): Class name of the application item.

        Returns:
            cs_url (str): Clustered-service URL.
            cs_data (dict): Clustered-service params.
        """
        # Clustered-service URL
        cs_url = vcs_cluster + '/services/' + clustered_service

        # Define clustered service in the model
        class_type = "vcs-clustered-service"
        options = \
            "active={0} standby={1} name='{2}'".format(cs_params["active"],
                                                       cs_params["standby"],
                                                       clustered_service)

        if 'online_timeout' in cs_params:
            options += " online_timeout={0}".format(
                cs_params['online_timeout'])

        options = self.add_online_dep_for_clustered_service(clustered_service,
                                                            online_dep,
                                                            options)

        cs_data = {'url': cs_url,
                   'class_type': class_type,
                   'options': options}

        return cs_url, cs_data

    def generate_cli_commands_multi_srvs(self, vcs_cluster, conf,
                                         clustered_service,
                                         app_class="lsb-runtime",
                                         online_dep=None):
        """
        Function to generate CLI commands that will setup the supplied
        VCS multi clustered-services, IPs and lsb resources.
        They will be in format so they can be used with the
        execute_cli_<create/link>_cmd functions.

        Args:
            vcs_cluster (str): URL of the VCS cluster.

            conf (dict): The required configuration of clustered-services.

            clustered_service (str): Name of clustered service as
                defined in configuration.

            app_class (str): Class name of the application item
                       ("lsb-runtime" | "service" | "vm-service").

            online_dep (str): Class name of the application item.

        Returns:
            dict. CLI commands.
        """
        # Counter to be used to help generate the different IP items

        # Empty list of dictionaries to be built up and returned
        apps_data = []
        app_data = {}
        ip_data = []
        pkg_data = []
        pkg_links_data = []
        full_list = {}
        full_list['ha_service_config'] = []

        # Properties for clustered-service
        cs_params = conf["params_per_cs"][clustered_service]

        # Define clustered service in the model
        cs_url, cs_data = \
            self.cluster_service_model_definition(clustered_service,
                                                  vcs_cluster, cs_params,
                                                  online_dep)

        # Define the lsb app which resides under the clustered service
        application_list = conf["app_per_cs"][clustered_service]
        if type(application_list) is str:
            application_list = [application_list]
        ip_counter = 1

        for application in application_list:
            ip_counter += len(conf["ip_per_app"][application])
            app_properties = conf["lsb_app_properties"][application]
            app_url_in_cluster = None
            if app_class == "lsb-runtime":
                app_url = cs_url + '/runtimes/' + application
                class_type = "lsb-runtime"
            else:
                app_url = '/software/services/' + application
                class_type = app_class
                app_url_in_cluster = cs_url + '/applications/' + application

            options = []
            for prop in app_properties:
                options.append(prop + "='" + app_properties[prop] + "'")
            option_str = " ".join(options)

            app_data = {'url': app_url,
                        'class_type': class_type,
                        'options': option_str}
            if app_url_in_cluster:
                app_data['app_url_in_cluster'] = app_url_in_cluster

            apps_data.append(app_data)

            # Define any ha config properties under the clustered service
            ha_configs_data = []
            if 'ha_service_config_properties' in conf.keys():
                class_type = "ha-service-config"
                ha_props = \
                    conf["ha_service_config" +
                         "_properties"][clustered_service]
                for ha_prop in ha_props:
                    options = ""
                    for key, value in ha_prop.items():
                        options = options + key + '=' + value + ' '
                    ha_configs_data.append({'url': cs_url + '/ha_configs/' +
                                                   ha_prop['service_id'],
                                            'class_type': class_type,
                                            'options': options})

            # Define the IPs which reside under the lsb-app
            ip_addresses = conf["ip_per_app"][application]
            parent_url = \
                self.define_ip_res_cli_parent_url(app_class, cs_url, app_url)
            for ip_address in ip_addresses:
                ip_url = parent_url + '/ipaddresses/ip' + str(ip_counter)
                ip_network = conf["network_per_ip"][ip_address]
                class_type = "vip"
                options = "ipaddress='{0}' network_name='{1}'".format(
                    ip_address, ip_network)

                ip_data.append({'url': ip_url,
                                'class_type': class_type,
                                'options': options})
                ip_counter += 1

            # Create Packages under /software/items and link
            # packages to items under VCS cluster
            packages_url = "/software/items/"
            packages = conf["pkg_per_app"][application]
            for app_id, app_content in packages.items():
                if app_content.values():
                    for version in app_content.values():
                        pkg_url = packages_url + app_id
                        options = "name='" + app_id + "'"
                        options = options + ' version' + "=" + \
                                  version
                        class_type = 'package'
                        link_url = app_url + '/packages/' + app_id
                        pkg_data.append({'url': pkg_url,
                                         'class_type': class_type,
                                         'options': options})
                        pkg_links_data.append({'child_url': link_url,
                                               'class_type': class_type,
                                               'parent_url': pkg_url})
                else:
                    pkg_url = packages_url + app_id
                    class_type = 'package'
                    link_url = app_url + '/packages/' + app_id
                    options = "name='" + app_id + "'"
                    pkg_data.append({'url': pkg_url,
                                     'class_type': class_type,
                                     'options': options})
                    pkg_links_data.append({'child_url': link_url,
                                           'class_type': class_type,
                                           'parent_url': pkg_url})

        full_list['cs'] = cs_data
        full_list['apps'] = apps_data
        full_list['pkgs'] = pkg_data
        full_list['ips'] = ip_data
        full_list['pkg_links'] = pkg_links_data
        full_list['ha_service_config'].append(ha_configs_data)

        return full_list

    @staticmethod
    def define_ip_res_cli_parent_url(app_class, cs_url, app_url):
        """
        Function to define the parent url of an ip resource in the LITP
        deployment model.
        """
        parent_url = ""
        if app_class == "lsb-runtime":
            parent_url = app_url
        else:
            parent_url = cs_url
        return parent_url

    def get_hagrp_cs_clear_cmd(self, cs_name, system):
        """Returns a command to run a "hagrp -clear" command on a VCS node.
        This command clears the fault related to the supplied clustered
        service in the provided system.

        Args:
            cs_name (str): Name of clustered service group to be cleared.

            system (str): Hostname of the system.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -clear <cs_name> -sys <system>"
        """

        return "{0} -clear {1} -sys {2}".format(self.hagrp_path, cs_name,
                                                system)

    @staticmethod
    def get_hagrp_cs_online_cmd(cs_name, system, propagate=True):
        """Returns a command to run a "hagrp -online" command on a VCS node.
        This command onlines the supplied clustered
        service in the provided system.

        Args:
            cs_name (str): Name of clustered service group to be onlined.

            system (str): Hostname of the system.

        Kwargs:
            propagate (bool): When a group is brought online, all of its
                required child groups are also brought online. Default is True.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -online <cs_name> -sys <system>"
        """
        if propagate:
            return "{0} -online -propagate {1} -sys {2}".format(
                VCSUtils.HAGRP_PATH,
                cs_name, system)
        return "{0} -online {1} -sys {2}".format(VCSUtils.HAGRP_PATH,
                                                 cs_name, system)

    @staticmethod
    def get_hagrp_cs_offline_cmd(cs_name, system, propagate=True):
        """
        Description:
            Returns a command to run a "hagrp -offline" command on a VCS node.
            This command offlines the supplied clustered
            service in the provided system.

        Args:
            cs_name (str): Name of clustered service group to be offlined.

            system (str): Hostname of the system.

        KwArgs:
            propagate (bool): When a group is brought offline, all of its
                required child groups are also brought offline. Default is True

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -offline <cs_name> -sys <system>"
        """
        if propagate:
            return "{0} -offline -propagate {1} -sys {2}".format(
                VCSUtils.HAGRP_PATH,
                cs_name, system)
        return "{0} -offline {1} -sys {2}".format(VCSUtils.HAGRP_PATH, cs_name,
                                                  system)

    @staticmethod
    def get_hagrp_cs_freeze_cmd(cs_name, system, persistent=True):
        """
        Description:
            Returns a command to run a "hagrp -freeze" command on a VCS node.
            This command freezes the supplied clustered
            service in the provided system.

        Args:
            cs_name (str): Name of clustered service group to be frozen.

            system (str): Hostname of the system.

        KwArgs:
            persistent (bool): Flag to specify whether to include the
                               -persistent argument in the freeze
                               command. Default is True

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -freeze <cs_name> -sys <system>"
        """
        if persistent:
            return "{0} -freeze {1} -persistent".format(VCSUtils.HAGRP_PATH,
                                                        cs_name)
        return "{0} -freeze {1} -sys {2}".format(VCSUtils.HAGRP_PATH, cs_name,
                                                 system)

    @staticmethod
    def get_hagrp_cs_unfreeze_cmd(cs_name, system, persistent=True):
        """
        Description:
            Returns a command to run a "hagrp -unfreeze" command on a VCS node.
            This command unfreezes the supplied clustered service in the
            provided system.

        Args:
            cs_name (str): Name of clustered service group to be unfrozen.

            system (str): Hostname of the system.

        KwArgs:
            persistent (bool): Flag to specify whether to include the
                               -persistent argument in the unfreeze
                               command. Default is True

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -unfreeze <cs_name> -sys <system>"
        """
        if persistent:
            return "{0} -unfreeze {1} -persistent".format(VCSUtils.HAGRP_PATH,
                                                          cs_name)
        return "{0} -unfreeze {1} -sys {2}".format(VCSUtils.HAGRP_PATH,
                                                   cs_name,
                                                   system)

    @staticmethod
    def get_hagrp_attribute_cmd(cs_name, attribute):
        """
        Description:
            Returns a formatted command to retrieve a specific
            attribute value for the specified cluster service.

        Args:
            cs_name (str): Name of clustered service group to retrieve
                attribute from.
            attribute (str): Name of the attribute to be retrieved

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hagrp -display <cs_name> -attribute <system>"
        """
        return "{0} -display {1} -attribute {2}".format(VCSUtils.HAGRP_PATH,
                                                        cs_name,
                                                        attribute)

    def get_hagrp_value_cmd(self, sg_name, sg_attr, system=None):
        """Returns a "hagrp -value" command with supplied argument
        for a particular service group to run on a VCS node.

        Args:
            sg_name (str): Name of a service group.

            sg_attr (str): Single VCS service group attribute.
                Attribute examples: Parallel, SystemList, AutoStartList

        Kwargs:
            system (str): Optional. Name of a system for
                which the check should be performed.

        Returns:
            str. A command to run "hagrp -value <sg_name> <attr> [<system>]"
        """
        sg_attrs = "-value {0} {1}".format(sg_name, sg_attr)
        if system is not None:
            sg_attrs += " {0}".format(system)
        return self.get_hagrp_cmd(sg_attrs)

    def get_hares_ip_resource_address(self, resource):
        """Returns a command to run a "hares -value" command on
            a VCS node with the passed resource value.

        Args:
            resource (str): Name of resource whose address is to be retrieved.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hares -value <resource_name> Address"
        """

        return "{0} -value {1} Address".format(self.hares_path, resource)

    def get_hares_resource_attr(self, resource, attr):
        """Returns a command to run a "hares -value" command on
            a VCS node with the passed resource and attribute values.

        Args:
            resource (str): Name of resource whose address is to be retrieved.

            attr (str): Name of VCS Resource Attribute whose
                is to be retrieved.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hares -value <resource_name> <attribute_name>"
        """

        return "{0} -value {1} {2}".format(self.hares_path, resource, attr)

    def get_hares_resource_online_timeout(self, resource):
        """Returns a command to run a hares
        OnlineTimeout command on a VCS node.

        Args:
            resource (str): Name of resource whose
                OnlineTimeout is to be retrieved.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hares -value <resource_name> OnlineTimeout"
        """

        return "{0} -value {1} OnlineTimeout".format(self.hares_path, resource)

    def get_hares_resource_offline_timeout(self, resource):
        """Returns a command to run a hares
        OfflineTimeout command on a VCS node.

        Args:
            resource (str): Name of resource whose
                OfflineTimeout is to be retrieved.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hares -value <resource_name> OfflineTimeout"
        """

        return "{0} -value {1} OfflineTimeout".format(self.hares_path,
                                                      resource)

    @staticmethod
    def get_hares_resource_attribute(resource_id, attribute):
        """Returns a command to run a "hares -dislay" command on a VCS node.

        Args:
            resource_id (str): Name of resource whose
                attributes are to be queried.

            attribute (str): The name of the attribute to be queried.

        Returns:
            str. A command to run "/opt/VRTSvcs/bin/hares -display
                                        <resource_id> -attribute <attribute>"
        """

        return "/opt/VRTSvcs/bin/hares -display {0} " \
               "-attribute {1}".format(resource_id, attribute)

    def get_hares_cs_clear_cmd(self, resource, system):
        """Returns a command to run a "hares -clear" command on a VCS node.
        This command clears the fault related to the supplied clustered
        service in the provided system.

        Args:
            resource (str): Name of resource that is to be cleared.

            system (str): Hostname of the system.

        Returns:
            str. A command to run
                "/opt/VRTS/bin/hares -clear <cs_name> -sys <system>"
        """

        return "{0} -clear {1} -sys {2}".format(self.hares_path, resource,
                                                system)

    @staticmethod
    def get_resource_state(hares_output):
        """
        Parses VCS resource state from "hares -state" command.

        Args:
            hares_output (str): Output of the VCS "hares -state" command.

        Returns:
            dict. Status of the given resource per node.
        """

        res_state_per_node = {}
        for line in hares_output[1:]:
            match = re.match(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$", line)
            node = match.group(3)
            state = match.group(4)
            res_state_per_node[node] = state.lower()

        return res_state_per_node

    @staticmethod
    def check_hostname_cs_online(hostnames, clustered_service,
                                 vcs_output, cs_active_node_dict):
        """
        Function to check whether a clustered service is
        active on the provided hostnames.

        Args:
            hostnames (list): List of hostnames of nodes to be checked against.

            clustered_service (str): Name of the clustered service as
                it appears in the conf dictionary.

            vcs_output (list): The output from the VCS query issued against\
                the clustered service.

            cs_active_node_dict (dict): Lists of nodes on which
                each C-S is active.

        Returns:
            dict. A dictionary that identifies which C-S's are online on\
            each node.
        """
        # CREATE AN ENTRY FOR THE CLUSTERED SERVICE IN THE DICTIONARY
        cs_active_node_dict[clustered_service] = []
        # ADD THE HOSTNAMES OF ALL THE NODES ON WHICH THIS CLUSTERED
        # SERVICE IS FOUND TO BE IN AN ONLINE STATE.
        for hostname in hostnames:
            for line in vcs_output:
                if hostname in line and "ONLINE" in line:
                    cs_active_node_dict[clustered_service].append(hostname)
        # SHOULD THE CLUSTERED SERVICE FOUND TO NOT BE IN AN ONLINE
        # STATE ON ANY NODE THEN DELETE THE CLUSTERED SERVICE KEY
        # FROM THE DICTIONARY
        if cs_active_node_dict[clustered_service] == []:
            del cs_active_node_dict[clustered_service]
        return cs_active_node_dict

    @staticmethod
    def map_node_file_to_clustered_services(cs_active_node_dict,
                                            clustered_service,
                                            node_mapping, node_cs_list):
        """
        Function to map the nodes files to the clustered
        services that reside upon the nodes to which they connect.

        Args:
            cs_active_node_dict (dict): Dictionary with keys of cs names and
                a value of a list of hostnames on which the cs's are active.

            clustered_service (str): Name of the clustered service as it
                appears in the conf dictionary.

            node_mapping (dict): Dictionary with hostname keys and a value
                identifying the node filename.

            node_cs_list (dict): Dictionary identifying which C-S's are
            active on which node filenames; some c-s's shall be
            active upon multiple nodes.

        Returns:
            dict. A dictionary identifying which C-S's are
            active on which node filenames.

        """

        # FOR THE CLUSTERED SERVICE PROVIDED RETRIEVE THE LIST
        # OF NODE HOSTNAMES ON WHICH THE C-S IS ONLINE
        active_nodes = cs_active_node_dict[clustered_service]
        if len(active_nodes) > 1:
            # IF C-S IS ONLINE ON MULTIPLE HOSTS THEN FOR EACH
            # HOST RETRIEVE THE CORRESPONDING CONNECTION
            # FILE NAME WHICH SHALL BE USED AS A KEY IN
            # THE RETURNED DICT WITH VALUE OF A LIST OF
            # C-S NAMES WHICH ARE ONLINE ON THAT NODE.
            for active_node in range(len(active_nodes)):
                hostname = active_nodes[active_node]
                node_filename = node_mapping[hostname]
                if node_filename not in node_cs_list.keys():
                    node_cs_list[node_filename] = []
                node_cs_list[node_filename].append(clustered_service)
        else:
            # IF C-S IS ONLINE ON ONLY A SINGLE NODE THEN
            # RETRIEVE THE CORRESPONDING CONNECTION
            # FILE NAME WHICH SHALL BE USED AS A KEY IN
            # THE RETURNED DICT WITH VALUE OF A LIST OF
            # C-S NAMES WHICH ARE ONLINE ON THAT NODE.
            hostname = active_nodes[0]
            node_filename = node_mapping[hostname]
            if node_filename not in node_cs_list.keys():
                node_cs_list[node_filename] = []
            node_cs_list[node_filename].append(clustered_service)

        return node_cs_list

    @staticmethod
    def map_node_host_to_clustered_services(cs_active_node_dict,
                                            clustered_service,
                                            hostname_mapping):
        """
        Function to map the nodes hostnames to the
        clustered services that reside upon them.

        Args:
            cs_active_node_dict (dict): Dictionary with keys of cs names and
            a value of a list of hostnames on which the cs's are active.
            C-S's may be active upon multiple nodes simultaneously.

            clustered_service (Str): Name of the clustered service as it
            appears in the conf dictionary.

            hostname_mapping (dict): Dictionary with hostname keys and
            a value of a list of clustered services.

        Returns:
            dict. A dictionary identifying which C-S's are
            active on each hostname.

        """
        # FOR THE CLUSTERED SERVICE PROVIDED RETRIEVE THE LIST
        # OF NODE HOSTNAMES ON WHICH THE C-S IS ONLINE
        active_nodes = cs_active_node_dict[clustered_service]
        if len(active_nodes) > 1:
            # IF C-S IS ONLINE ON MULTIPLE HOSTS THEN FOR EACH
            # HOST ON WHICH IT IS ONLINE CREATE A KEY ENTRY
            # IN THE DICT TO BE RETURNED - IF ONE DOES NOT
            # ALREADY EXIST - AND ADD THE C-S AS AN ENTRY
            # IN THE LIST VALUE.
            for active_node in range(len(active_nodes)):
                hostname = active_nodes[active_node]
                if hostname not in hostname_mapping.keys():
                    hostname_mapping[hostname] = []
                hostname_mapping[hostname].append(clustered_service)
        else:
            hostname = active_nodes[0]
            # IF C-S IS ONLINE ON ONLY A SINGLE HOSTS THEN
            # CREATE A KEY ENTRY IN THE DICT TO BE RETURNED
            # - IF ONE DOES NOT ALREADY EXIST - AND ADD THE C-S
            # AS AN ENTRY IN THE LIST VALUE.
            if hostname not in hostname_mapping.keys():
                hostname_mapping[hostname] = []
            hostname_mapping[hostname].append(clustered_service)
        return hostname_mapping

    #Underscore to avoid pylint error in testset_vcs_setup.py
    @staticmethod
    def order_node_list(node_paths, conf, service):
        """
        Description:
            Sort LITP nodes paths for a particular service, accordingly to
            the order defined in conf['nodes_per_cs'] in
            generate_plan_conf_service(). conf['nodes_per_cs'] holds a
            list of numeric values representing nodes defined per
            vcs-clustered-service.
            With this hook, we can modify and utilize the nodes order
            as suits, ex.:
            conf['nodes_per_cs'] = {
                'CS24': [2, 1]
                }

        Args:
            node_paths (list): LITP nodes paths

            conf (dict): output of generate_plan_conf_service()

            service (str): name of a clustered service

        Returns:
            list. The list of LITP node paths, ordered according to
            conf['nodes_per_cs'].
        """
        nodes = {}
        for index, path in enumerate(node_paths, start=1):
            nodes[index] = path

        node_paths = [nodes[i] for i in conf['nodes_per_cs'][service]]
        return node_paths
