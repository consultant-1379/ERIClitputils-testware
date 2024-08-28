"""
Libvirt Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""

from redhat_cmd_utils import RHCmdUtils
import test_constants
from json_utils import JSONUtils


class LibvirtUtils(object):

    """Libvirt related utilities.
    """

    def __init__(self):
        """Initialise the shared properties.
        """
        self.rhc = RHCmdUtils()
        self.adaptor_pkg_name = test_constants.LIBVIRT_ADAPTOR_PKG_NAME
        self.conf_file_name = "config.json"
        self.instances_data_dir = test_constants.LIBVIRT_INSTANCES_DIR
        self.libvirt_module_name = "litp_adaptor.py"
        self.yum_adptr_instll_cmd = \
            self.rhc.get_yum_install_cmd([self.adaptor_pkg_name])
        self.vm_images_remote_dir = test_constants.VM_IMAGE_MS_DIR
        self.json_utils = JSONUtils()

    ##############################################################
    # See: http://confluence-oss.lmera.ericsson.se/display/ELITP/
    #                              LIBVIRT+KGB+and+CDB+Deployment
    ##############################################################

    def compile_vm_config_file(self, version="0.0.0", user_vm_data=None,
                               user_adaptor_data=None):
        """
        Function to compile the VM configuration properties file of
        the VM to be deployed via libvirt.

        Args:
            version (str): Version of the JSON layout for the adaptor to\
            assimilate.

            user_vm_data (dict): Dictionary of values for the VM with which to\
                override the defaults provided in this function.

            user_adaptor_data (dict): Dictionary of values for the adaptor\
                with which to override the defaults provided in this function.

        Returns:
            dict. A compiled dictionary of the combined property values
            relating to the VM to be deployed.
        """
        if user_vm_data is None:
            user_vm_data = {}
        if user_adaptor_data is None:
            user_adaptor_data = {}

        vm_config_file = {"json_version": version}

        vm_data = {"vm_data": {"cpu": "2",
                               "ram": "256M",
                               "interfaces": {},
                               "hd": [],
                               "image": "rhel.img"}}

        adaptor_data = {"adaptor_data": {"restart-timeout": 45}}

        # UPDATE THE CONFIGURATION DICTIONARIES TO USE THE USER PROVIDED VALUES
        vm_data.update(user_vm_data)
        adaptor_data.update(user_adaptor_data)

        # UPDATE THE vm_config_file TO CONTAIN ALL OF THE SUB DICTIONARIES
        vm_config_file.update(vm_data)
        vm_config_file.update(adaptor_data)

        return self.json_utils.dump_json(vm_config_file)

    @staticmethod
    def get_virsh_destroy_cmd(vm_name):
        """
        Function to return the virsh command needed to destroy the provided
        virtual machine.

        Args:
            vm_name (str): The name of the virtual machine, as it appears in
                           the virsh console, which is to be destroyed.

        Return:
            str. The destroy command to be issued against the virtual machine.
        """

        return "/usr/bin/virsh destroy {0}".format(vm_name)

    @staticmethod
    def get_virsh_undefine_cmd(vm_name):
        """
        Function to return the virsh command needed to undefine the provided
        virtual machine.

        Args:
            vm_name (str): The name of the virtual machine, as it appears in
                           the virsh console, which is to be undefined.

        Return:
            str. The undefine command to be issued against the virtual machine.
        """

        return "/usr/bin/virsh undefine {0}".format(vm_name)

    @staticmethod
    def get_virsh_dominfo_cmd(vm_name):
        """
        Function to return the virsh command needed to get domain info
        from provided virtual machine.

        Args:
            vm_name (str): The name of the virtual machine, as it appears in
                           the virsh console, which is to be examined.

        Return:
            str. The dominfo command to be issued against the virtual machine.
        """

        return "/usr/bin/virsh dominfo {0}".format(vm_name)

    @staticmethod
    def get_virsh_dumpxml_cmd(vm_name):
        """
        Function to return the virsh command needed to get domain xml
        from provided virtual machine.

        Args:
            vm_name (str): The name of the virtual machine, as it appears in
                           the virsh console, which is to be examined.

        Return:
            str. The dumpxml command to be issued against the virtual machine.
        """

        return '/usr/bin/virsh dumpxml {0}'.format(vm_name)

    @staticmethod
    def get_virsh_vcpuinfo_cmd(vm_name):
        """
        Function to return the virsh command needed to get domain vcpu
        information from provided virtual machine.

        Args:
            vm_name (str): The name of the virtual machine, as it appears in
                           the virsh console, which is to be examined.

        Return:
            str. The vcpuinfo command to be issued against the virtual machine.
        """

        return '/usr/bin/virsh vcpuinfo {0}'.format(vm_name)

    @staticmethod
    def generate_conf_ms_srv():
        """
        Returns a dictionary which defines the required MS VM Service
        configuration for plan 1.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a MS VM Service configuration.

        2. Verify that the MS Service configuration has been
           deployed correctly.

        3. Used as a baseline for other tests.

        Returns:
            dict. Dictionary which defines MS VM Service configuration.
        """

        ms_srvs = {}

        ########################################################
        # MS SERVICE OBJECT
        ########################################################
        ms_srvs['app_per_ms_srv'] = {
            'MS_VM1': 'MS_VM1'}

        ##########################################################
        # MS SERVICE OBJECTS - MS SERVICE PROPERTIES
        ##########################################################
        ms_srvs['params_per_ms_srv'] = {
            'MS_VM1': {
                'image_name': 'vm-image-1',
                'cpus': 2,
                'ram': '512M',
                'internal_status_check': 'off',
                'hostnames': 'tmo-vm-1',
                'service_name': 'test-vm-service-ms'},
        }

        ########################################################
        # MS SERVICE - INTERFACES MAPPING
        ########################################################
        ms_srvs['interfaces_per_ms_srv'] = {
            'MS_VM1': ['net1']}

        ########################################################
        # MS SERVICE - HOSTS MAPPING
        ########################################################
        ms_srvs['hosts_per_ms_srv'] = {
            'MS_VM1': ['db1', 'db2']}

        ########################################################
        # MS SERVICE - INTERFACES
        ########################################################
        ms_srvs['vm_interfaces'] = {
            'net1': {
                'device_name': "eth0",
            }
        }

        ########################################################
        # MS SERVICE - HOSTS
        ########################################################
        ms_srvs['vm_hosts'] = {'db1': {'alias_names': 'dbsvc1',
                                       'address': '111.222.1.2'},
                               'db2': {'alias_names': 'dbsvc2.foo-domain.tld',
                                       'address': '111.222.1.3'}}

        ########################################################
        # CLOUD INIT PACKAGES
        ########################################################
        ms_srvs['cloud_init_packages'] = {
            'MS_VM1': ['empty_rpm1'],
        }

        ########################################################
        # CLOUD INIT YUM REPOS
        ########################################################
        _3pp_repos = {'3PP': 'http://%(ms_host)s/{0}'.format(
            test_constants.PP_REPO_DIR_NAME)}
        _all_repos = _3pp_repos.copy()
        _all_repos.update({'LITP': 'http://%(ms_host)s/litp'})

        ms_srvs['cloud_init_repos'] = {
            'MS_VM1': _all_repos,
        }

        ########################################################
        # MS SERVICE - VM-NFS-MOUNTS
        ########################################################
        ms_srvs['nfs_mounts_per_ms_srv'] = {
            'MS_VM1': ['vm_nfs_mount_1',
                       'vm_nfs_mount_2',
                       'vm_nfs_mount_3']}

        ########################################################
        # VM NFS MOUNTS
        ########################################################
        ms_srvs['vm_nfs_mounts'] = {
            'vm_nfs_mount_1': {
                'device_path': "%(sfs_host)s:/vx/story7815-mount_1",
                'mount_point': "/tmp/mount_1",
                'mount_options': 'retrans=8,rsize=32768'},
            'vm_nfs_mount_2': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_2",
                'mount_point': "/tmp/mount_2"},
            'vm_nfs_mount_3': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_3",
                'mount_point': "/tmp/mount_3",
                'mount_options': 'retrans=6,rsize=16384'}}

        ########################################################
        # MS VM SERVICE - VM-SSH-KEYS
        ########################################################
        ms_srvs['ssh_keys_per_ms_srv'] = {
            'MS_VM1': ['ssh_key_rsa_11',
                       'ssh_key_rsa_12',
                       'ssh_key_rsa_13']}

        ########################################################
        # VM SSH KEYS
        ########################################################
        ms_srvs['vm_ssh_keys'] = {
            'ssh_key_rsa_11': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEApPdyRQeCoh3" +
                           "6f8ayxgJLg6nZvWD3nc2kV1T+6xXY6dFTlR4TBjkj5pMq6" +
                           "fGNzSZBfzCB7LvBz0DxLWgKYhIumt1QTFDAszULwfst94X" +
                           "qHd+HSAEBQ0+cZ5VQmjXtt7OpklofsSsC4SilWCJW2g1G4" +
                           "Lo7W5BP/qeBj/yGvE9qKnctZ26OtuO7R1fcpOIXC5KFT9c" +
                           "ecvROijCBE90HQYLzt1VlDQn2DRqOH7w11S5abNskZrrpM" +
                           "2lhXorKEozORP9WrCuZW1PEnQDRGAzqKiaAw/5q/3m/L72" +
                           "NtUyiXzi5+92ZgvvxXSOernpeIocoPbUMVcma945dfm8Fx" +
                           "C60/UB//Q== root@atvts1852"},
            'ssh_key_rsa_12': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvB3N6WOJ9qA" +
                           "QjGWfwpXvUWYWz8A7Ezwv/pihAYCbObDo71Ycsa3kuz2gU" +
                           "K9uS6Pw5DlNFAbFPk4zi/52Oj+frw4W56HnStxe13zB7ca" +
                           "4N0HFHMEE1QOyZ/wzv+DubwoKuz8I5yA9BD5Oli3DJXVVq" +
                           "xhjxRjiOQ7xs+CHsqHxzgulSJpWmbkli7BoVXsCoFN0oQm" +
                           "fXc7liqCciCZCvPwc+mKtJfH4oozKajwfcvyRyQhd1hqFw" +
                           "saa7dxKuLww0mT6V+scduwCMVSuJH0b34Qow4ZR0XWwHGI" +
                           "zCf5XApypZPcuaEhRBtqpWysujlnYrkieprGn/nKna/t6U" +
                           "SJdC9uPWQ== root@atvts1852"},
            'ssh_key_rsa_13': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8g3u0guI42g" +
                           "og7dFNBoBOtXZ+/okb+HZoTj37Iz5c60+qpehKHTdqnewx" +
                           "T+BX1h/GZg0CKb8+tR3GFqifBDAVXqwHfpQnGMVsHeItM0" +
                           "9XDoYvRjWkkDAwpT3OLdEKfNmu+0rJEwvrx5w+aDsvrzfr" +
                           "DUGNWTBSogpXKLL1kCsCsfCNdU42xy6GygzgqyL/lo5RFB" +
                           "TbuDkI0Y4xSzwTxb8CPjbPcughBedWxAI0aYGh+IcV+fP2" +
                           "reMVeDyFqPeKiXcdL+8kWAb+pkR1WUr46dKxP/PkQGkpVE" +
                           "XxsjtDwisNJDFb3wC8pF3G2T5L3And01rhMg5hhLpCZn3y" +
                           "WSZUvjU6Q== root@atvts1852"}}

        return ms_srvs

    @staticmethod
    def generate_conf_plan1():
        """
        Returns a dictionary which defines the required CS configuration
        for plan 1.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a CS configuration.

        2. Verify that the CS configuration has been deployed correctly.

        3. Used as a baseline for other tests.

        Returns:
            dict. Dictionary which defines CS configuration.
        """

        conf = {}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - SERVICES
        ########################################################
        conf['app_per_cs'] = {
            'CS_VM1': 'vm_service_1'}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - NODES MAPPING
        ##########################################################
        conf['nodes_per_cs'] = {
            'CS_VM1': [1]}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - CS TYPE
        ##########################################################
        conf['params_per_cs'] = {
            'CS_VM1': {'active': 1, 'standby': 0, 'online_timeout': 1200}}

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM SERVICES
        ########################################################
        conf['lsb_app_properties'] = {
            'vm_service_1': {
                'image_name': 'vm-image-1',
                'service_name': 'test-vm-service-1',
                'cpus': '1',
                'hostnames': 'tmo-vm-1',
                'ram': '256M',
                'cleanup_command':
                    '/usr/share/litp_libvirt/vm_utils test-vm-service-1 '
                    'force-stop',
                'internal_status_check': 'on'},
        }

        ########################################################
        # List of HA config properties per app
        ########################################################
        conf["ha_service_config_properties"] = {
            "CS_VM1": {
                'restart_limit': '1'},
        }

        ##########################################################
        # Define the IP's which reside under the lsb-app
        ##########################################################
        conf['ip_per_app'] = {
            'vm_service_1': [],
        }

        ##########################################################
        # Define packages under /software/items
        ##########################################################
        conf['pkg_per_app'] = {
            'vm_service_1': [],
        }

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - IMAGES
        ##########################################################
        conf['image_per_cs'] = {
            'CS_VM1': 'vm_image_1'}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES MAPPING
        ########################################################
        conf['interfaces_per_cs'] = {
            'CS_VM1': ['net1', 'net_dhcp']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS MAPPING
        ########################################################
        conf['hosts_per_cs'] = {
            'CS_VM1': ['db1', 'db2']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES
        ########################################################
        conf['vm_interfaces'] = {
            'net1': {
                'device_name': "eth0",
            },
            'net_dhcp': {
                'device_name': "eth1",
            },
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS
        ########################################################
        conf['vm_hosts'] = {'db1': {'alias_names': 'dbsvc1',
                                    'address': '111.222.1.2'},
                            'db2': {'alias_names': 'dbsvc2.foo-domain.tld',
                                    'address': '111.222.1.3'}}

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM IMAGES
        ########################################################
        conf['vm_images'] = {
            'vm_image_1': {
                'name': 'vm-image-1',
                'source_uri':
                    'http://%(ms_host)s/images/vm_test_image-1-1.0.6.qcow2'},
        }

        ########################################################
        # CLOUD INIT PACKAGES
        ########################################################
        conf['cloud_init_packages'] = {
            'CS_VM1': ['empty_rpm1'],
        }

        ########################################################
        # CLOUD INIT YUM REPOS
        ########################################################
        _3pp_repos = {'3PP': 'http://%(ms_host)s/{0}'.format(
            test_constants.PP_REPO_DIR_NAME)}
        _all_repos = _3pp_repos.copy()
        _all_repos.update({'LITP': 'http://%(ms_host)s/litp'})

        conf['cloud_init_repos'] = {
            'CS_VM1': _all_repos,
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-NFS-MOUNTS
        ########################################################
        conf['nfs_mounts_per_cs'] = {
            'CS_VM1': ['vm_nfs_mount_1',
                       'vm_nfs_mount_2',
                       'vm_nfs_mount_3']}

        ########################################################
        # VM NFS MOUNTS
        ########################################################
        conf['vm_nfs_mounts'] = {
            'vm_nfs_mount_1': {
                'device_path': "%(sfs_host)s:/vx/story7815-mount_1",
                'mount_point': "/tmp/mount_1",
                'mount_options': 'retrans=8,rsize=32768'},
            'vm_nfs_mount_2': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_2",
                'mount_point': "/tmp/mount_2"},
            'vm_nfs_mount_3': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_3",
                'mount_point': "/tmp/mount_3",
                'mount_options': 'retrans=6,rsize=16384'}}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-SSH-KEYS
        ########################################################
        conf['ssh_keys_per_cs'] = {
            'CS_VM1': ['ssh_key_rsa_11',
                       'ssh_key_rsa_12',
                       'ssh_key_rsa_13']}

        ########################################################
        # VM SSH KEYS
        ########################################################
        conf['vm_ssh_keys'] = {
            'ssh_key_rsa_11': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEApPdyRQeCoh3" +
                           "6f8ayxgJLg6nZvWD3nc2kV1T+6xXY6dFTlR4TBjkj5pMq6" +
                           "fGNzSZBfzCB7LvBz0DxLWgKYhIumt1QTFDAszULwfst94X" +
                           "qHd+HSAEBQ0+cZ5VQmjXtt7OpklofsSsC4SilWCJW2g1G4" +
                           "Lo7W5BP/qeBj/yGvE9qKnctZ26OtuO7R1fcpOIXC5KFT9c" +
                           "ecvROijCBE90HQYLzt1VlDQn2DRqOH7w11S5abNskZrrpM" +
                           "2lhXorKEozORP9WrCuZW1PEnQDRGAzqKiaAw/5q/3m/L72" +
                           "NtUyiXzi5+92ZgvvxXSOernpeIocoPbUMVcma945dfm8Fx" +
                           "C60/UB//Q== root@atvts1852"},
            'ssh_key_rsa_12': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvB3N6WOJ9qA" +
                           "QjGWfwpXvUWYWz8A7Ezwv/pihAYCbObDo71Ycsa3kuz2gU" +
                           "K9uS6Pw5DlNFAbFPk4zi/52Oj+frw4W56HnStxe13zB7ca" +
                           "4N0HFHMEE1QOyZ/wzv+DubwoKuz8I5yA9BD5Oli3DJXVVq" +
                           "xhjxRjiOQ7xs+CHsqHxzgulSJpWmbkli7BoVXsCoFN0oQm" +
                           "fXc7liqCciCZCvPwc+mKtJfH4oozKajwfcvyRyQhd1hqFw" +
                           "saa7dxKuLww0mT6V+scduwCMVSuJH0b34Qow4ZR0XWwHGI" +
                           "zCf5XApypZPcuaEhRBtqpWysujlnYrkieprGn/nKna/t6U" +
                           "SJdC9uPWQ== root@atvts1852"},
            'ssh_key_rsa_13': {
                'ssh_key': "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8g3u0guI42g" +
                           "og7dFNBoBOtXZ+/okb+HZoTj37Iz5c60+qpehKHTdqnewx" +
                           "T+BX1h/GZg0CKb8+tR3GFqifBDAVXqwHfpQnGMVsHeItM0" +
                           "9XDoYvRjWkkDAwpT3OLdEKfNmu+0rJEwvrx5w+aDsvrzfr" +
                           "DUGNWTBSogpXKLL1kCsCsfCNdU42xy6GygzgqyL/lo5RFB" +
                           "TbuDkI0Y4xSzwTxb8CPjbPcughBedWxAI0aYGh+IcV+fP2" +
                           "reMVeDyFqPeKiXcdL+8kWAb+pkR1WUr46dKxP/PkQGkpVE" +
                           "XxsjtDwisNJDFb3wC8pF3G2T5L3And01rhMg5hhLpCZn3y" +
                           "WSZUvjU6Q== root@atvts1852"}}

        # Needed for VCS verification methods
        conf['network_per_ip'] = {}
        # IPv6 static address for IPv6 only configuration
        conf['ipv6_only_static'] = {}
        # gateway6
        conf['ipv6_only_gw6'] = {}
        # IPv6 static address for dual stack two vms parallel
        conf['ipv6_dual_stack_ps'] = {}
        conf['ipv6_dual_stack_gw6_ps'] = {}
        # IPv6 static address for IPv6 only expand CS
        conf['ipv6_only_static_expand'] = {}
        # IPv6 gateway update case
        conf['gateway6_expand_update'] = {}
        # IPv6 static address for dual stack, ipv4 dhcp
        conf['ipv6_dual_stack_dhcp4'] = {}
        # gatewa6 address
        conf['ipv6_dual_stack_gw6_dhcp4'] = {}

        return conf

    @staticmethod
    def generate_conf_plan2():
        """
        Returns a dictionary which defines the required CS configuration
        for plan 2.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a CS configuration.

        2. Verify that the CS configuration has been deployed correctly.

        3. Used as a baseline for other tests.

        Returns:
            dict. Dictionary which defines CS configuration.
        """

        conf = {}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - SERVICES
        ########################################################
        conf['app_per_cs'] = {
            'CS_VM2': 'vm_service_2'}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - NODES MAPPING
        ##########################################################
        conf['nodes_per_cs'] = {
            'CS_VM2': [2]}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - CS TYPE
        ##########################################################
        conf['params_per_cs'] = {
            'CS_VM2': {'active': 1, 'standby': 0, 'online_timeout': 1200}}

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM SERVICES
        ########################################################
        conf['lsb_app_properties'] = {
            'vm_service_2': {
                'image_name': 'vm-image-2',
                'service_name': 'test-vm-service-2',
                'cpus': '1',
                'hostnames': 'tmo-vm-2',
                'ram': '256M',
                'start_command':
                    '/bin/systemctl start test-vm-service-2',
                'stop_command':
                    '/bin/systemctl stop test-vm-service-2',
                'status_command':
                   '/usr/share/litp_libvirt/vm_utils test-vm-service-2 status',
                'cleanup_command':
                    '/usr/share/litp_libvirt/vm_utils test-vm-service-2 '
                    'force-stop',
                'internal_status_check': 'on'},
        }

        ########################################################
        # List of HA config properties per app
        ########################################################
        conf["ha_service_config_properties"] = {
            "CS_VM2": {
                'restart_limit': '1'},
        }

        ##########################################################
        # Define the IP's which reside under the lsb-app
        ##########################################################
        conf['ip_per_app'] = {
            'vm_service_2': [],
        }

        ##########################################################
        # Define packages under /software/items
        ##########################################################
        conf['pkg_per_app'] = {
            'vm_service_2': [],
        }

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - IMAGES
        ##########################################################
        conf['image_per_cs'] = {
            'CS_VM2': 'vm_image_2'}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES MAPPING
        ########################################################
        conf['interfaces_per_cs'] = {
            'CS_VM2': ['net2', 'net3', 'net_dhcp']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS MAPPING
        ########################################################
        conf['hosts_per_cs'] = {
            'CS_VM2': ['db1']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES
        ########################################################
        conf['vm_interfaces'] = {
            'net2': {
                'device_name': "eth0",
            },
            'net3': {
                'device_name': "eth1",
            },
            'net_dhcp': {
                'device_name': "eth2",
            },
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS
        ########################################################
        conf['vm_hosts'] = {'db1': {'alias_names': 'dbsvc1',
                                    'address': '111.222.1.2'}}

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM IMAGES
        ########################################################
        conf['vm_images'] = {
            'vm_image_2': {
                'name': 'vm-image-2',
                'source_uri':
                    'http://%(ms_host)s/images/vm_test_image-2-1.0.8.qcow2'},
        }

        ########################################################
        # CLOUD INIT PACKAGES
        ########################################################
        conf['cloud_init_packages'] = {
            'CS_VM2': ['empty_rpm2', 'empty_rpm3'],
        }

        ########################################################
        # CLOUD INIT YUM REPOS
        ########################################################
        _3pp_repos = {'3PP': 'http://%(ms_host)s/{0}'.format(
            test_constants.PP_REPO_DIR_NAME)}
        _all_repos = _3pp_repos.copy()
        _all_repos.update({'LITP': 'http://%(ms_host)s/litp'})

        conf['cloud_init_repos'] = {
            'CS_VM2': _all_repos,
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-NFS-MOUNTS
        ########################################################
        conf['nfs_mounts_per_cs'] = {
            'CS_VM2': []}

        ########################################################
        # VM NFS MOUNTS
        ########################################################
        conf['vm_nfs_mounts'] = {}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-SSH-KEYS
        ########################################################
        conf['ssh_keys_per_cs'] = {
            'CS_VM2': []}

        ########################################################
        # VM SSH KEYS
        ########################################################
        conf['vm_ssh_keys'] = {}

        # Needed for VCS verification methods
        conf['network_per_ip'] = {}
        # IPv6 static address for IPv6 only configuration
        conf['ipv6_only_static'] = {}
        # gateway6
        conf['ipv6_only_gw6'] = {}
        # IPv6 static address for dual stack two vms parallel
        conf['ipv6_dual_stack_ps'] = {}
        conf['ipv6_dual_stack_gw6_ps'] = {}
        # IPv6 static address for IPv6 only expand CS
        conf['ipv6_only_static_expand'] = {}
        # IPv6 gateway update case
        conf['gateway6_expand_update'] = {}
        # IPv6 static address for dual stack, ipv4 dhcp
        conf['ipv6_dual_stack_dhcp4'] = {}
        # gatewa6 address
        conf['ipv6_dual_stack_gw6_dhcp4'] = {}

        return conf

    @staticmethod
    def generate_conf_plan3():
        """
        Returns a dictionary which defines the required CS configuration
        for plan 3.
        The configuration defined in this dictionary will be used to:

        1. Generate CLI commands to create a CS configuration.

        2. Verify that the CS configuration has been deployed correctly.

        3. Used as a baseline for other tests.

        Returns:
           dict. Dictionary which defines CS configuration.
        """

        conf = {}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - SERVICES
        ########################################################
        conf['app_per_cs'] = {
            'CS_VM3': 'vm_service_3',
            'CS_VM4': 'vm_service_4',
            'CS_VM5': 'vm_service_5'}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - NODES MAPPING
        ##########################################################
        conf['nodes_per_cs'] = {
            'CS_VM3': [1, 2],
            'CS_VM4': [1, 2],
            'CS_VM5': [1, 2]}

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - CS TYPE
        ##########################################################
        conf['params_per_cs'] = {
            'CS_VM3': {'active': 1, 'standby': 1, 'online_timeout': 1200},
            'CS_VM4': {'active': 1, 'standby': 1, 'online_timeout': 1200},
            'CS_VM5': {'active': 2, 'standby': 0, 'online_timeout': 1200}}

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM SERVICES
        ########################################################
        conf['lsb_app_properties'] = {
            'vm_service_3': {
                'image_name': 'vm-image-1',
                'service_name': 'test-vm-service-3',
                'cpus': '1',
                'hostnames': 'tmo-vm-3',
                'ram': '256M',
                'cleanup_command':
                    '/usr/share/litp_libvirt/vm_utils test-vm-service-3 '
                    'force-stop',
                'internal_status_check': 'on'},
            'vm_service_4': {
                'image_name': 'vm-image-2',
                'service_name': 'test-vm-service-4',
                'cpus': '1',
                'hostnames': 'tmo-vm-4',
                'ram': '256M',
                'start_command':
                    '/bin/systemctl start test-vm-service-4',
                'stop_command':
                    '/bin/systemctl stop test-vm-service-4',
                'status_command':
                   '/usr/share/litp_libvirt/vm_utils test-vm-service-4 status',
                'cleanup_command':
                    '/usr/share/litp_libvirt/vm_utils test-vm-service-4 '
                    'force-stop',
                'internal_status_check': 'on'},
            'vm_service_5': {
                'image_name': 'vm-image-3',
                'service_name': 'test-vm-service-5',
                'cpus': '1',
                'hostnames': 'tmo-vm-5-n1,tmo-vm-5-n2',
                'ram': '256M',
                'start_command':
                    '/bin/systemctl start test-vm-service-5',
                'stop_command':
                    '/bin/systemctl stop test-vm-service-5',
                'status_command':
                   '/usr/share/litp_libvirt/vm_utils test-vm-service-5 status',
                'cleanup_command':
                    '/usr/share/litp_libvirt/vm_utils test-vm-service-5 '
                    'force-stop',
                'internal_status_check': 'on'},
        }

        ########################################################
        # List of HA config properties per app
        ########################################################
        conf["ha_service_config_properties"] = {
            "CS_VM3": {},
            "CS_VM4": {},
            "CS_VM5": {
                'restart_limit': '1'},
        }

        ##########################################################
        # Define the IP's which reside under the lsb-app
        ##########################################################
        conf['ip_per_app'] = {
            'vm_service_3': [],
            'vm_service_4': [],
            'vm_service_5': [],
        }

        ##########################################################
        # Define packages under /software/items
        ##########################################################
        conf['pkg_per_app'] = {
            'vm_service_3': [],
            'vm_service_4': [],
            'vm_service_5': [],
        }

        ##########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - IMAGES
        ##########################################################
        conf['image_per_cs'] = {
            'CS_VM3': 'vm_image_1',
            'CS_VM4': 'vm_image_2',
            'CS_VM5': 'vm_image_3'}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES MAPPING
        ########################################################
        conf['interfaces_per_cs'] = {
            'CS_VM3': ['net4', 'net5', 'net6', 'net_dhcp'],
            'CS_VM4': ['net7', 'net8', 'net9', 'net10', 'net_dhcp'],
            'CS_VM5': ['net11', 'net12', 'net13', 'net14', 'net15']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS MAPPING
        ########################################################
        conf['hosts_per_cs'] = {
            'CS_VM3': ['db1', 'db2', 'db3', 'db4'],
            'CS_VM4': [],
            'CS_VM5': ['db1', 'db4', 'db2']}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - INTERFACES
        ########################################################
        conf['vm_interfaces'] = {
            'net4': {
                'device_name': "eth0",
            },
            'net5': {
                'device_name': "eth1",
            },
            'net6': {
                'device_name': "eth2",
            },
            'net7': {
                'device_name': "eth0",
            },
            'net8': {
                'device_name': "eth1",
            },
            'net9': {
                'device_name': "eth2",
            },
            'net10': {
                'device_name': "eth4",
            },
            'net11': {
                'device_name': "eth0",
            },
            'net12': {
                'device_name': "eth1",
            },
            'net13': {
                'device_name': "eth2",
            },
            'net14': {
                'device_name': "eth3",
            },
            'net15': {
                'device_name': "eth4",
            },
            'net_dhcp': {
                'device_name': "eth3",
            },
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - HOSTS
        ########################################################
        conf['vm_hosts'] = {'db1': {'alias_names': 'dbsvc1',
                                    'address': '111.222.1.2'},
                            'db2': {'alias_names': 'dbsvc2.foo-domain.tld',
                                    'address': '111.222.1.3'},
                            'db3': {'alias_names':
                                        'dbsvc3.foo-domain.tld,' +
                                        'dbsvc3',
                                    'address': '111.222.1.4'},
                            'db4': {'alias_names':
                                        'dbsvc4.foo-domain.tld,' +
                                        'dbsvc4.foo-domain2.tld2,dbsvc4',
                                    'address': '111.222.1.5'}}

        ########################################################
        # CLOUD INIT PACKAGES
        ########################################################
        conf['cloud_init_packages'] = {
            'CS_VM3': ['empty_rpm4', 'empty_rpm5'],
            'CS_VM4': ['empty_rpm6', 'empty_rpm7', 'empty_rpm8', 'empty_rpm9'],
            'CS_VM5': [],
        }

        ########################################################
        # CLOUD INIT YUM REPOS
        ########################################################
        _3pp_repos = {'3PP': 'http://%(ms_host)s/{0}'.format(
            test_constants.PP_REPO_DIR_NAME)}
        _all_repos = _3pp_repos.copy()
        _all_repos.update({'LITP': 'http://%(ms_host)s/litp'})

        conf['cloud_init_repos'] = {
            'CS_VM3': _all_repos,
            'CS_VM4': _all_repos,
            'CS_VM5': _3pp_repos,
        }

        ########################################################
        # SOFTWARE CHILD OBJECTS - VM IMAGES
        ########################################################
        conf['vm_images'] = {
            'vm_image_1': {
                'name': 'vm-image-1',
                'source_uri':
                    'http://%(ms_host)s/images/vm_test_image-1-1.0.6.qcow2'},
            'vm_image_2': {
                'name': 'vm-image-2',
                'source_uri':
                    'http://%(ms_host)s/images/vm_test_image-2-1.0.8.qcow2'},
            'vm_image_3': {
                'name': 'vm-image-3',
                'source_uri':
                    'http://%(ms_host)s/images/vm_test_image-3-1.0.8.qcow2'}
        }

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-NFS-MOUNTS
        ########################################################
        conf['nfs_mounts_per_cs'] = {
            'CS_VM3': ['vm_nfs_mount_4'],
            'CS_VM4': ['vm_nfs_mount_5',
                       'vm_nfs_mount_6',
                       'vm_nfs_mount_7',
                       'vm_nfs_mount_8',
                       'vm_nfs_mount_9'],
            'CS_VM5': ['vm_nfs_mount_10',
                       'vm_nfs_mount_11',
                       'vm_nfs_mount_12']}

        ########################################################
        # VM NFS MOUNTS
        ########################################################
        conf['vm_nfs_mounts'] = {
            'vm_nfs_mount_4': {
                'device_path': "%(sfs_host)s:/vx/story7815-mount_4",
                'mount_point': "/tmp/mount_4",
                'mount_options': 'retrans=3,wsize=16384'},
            'vm_nfs_mount_5': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_1",
                'mount_point': "/tmp/mount_5",
                'mount_options': 'rsize=32768,wsize=32768,timeo=14,soft'},
            'vm_nfs_mount_6': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_2",
                'mount_point': "/tmp/mount_6"},
            'vm_nfs_mount_7': {
                'device_path': "%(sfs_host)s:/vx/story7815-mount_3",
                'mount_point': "/tmp/mount_7",
                'mount_options': 'rsize=65536'},
            'vm_nfs_mount_8': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_4",
                'mount_point': "/tmp/mount_8",
                'mount_options': 'rsize=32768,wsize=16384,timeo=14,soft'},
            'vm_nfs_mount_9': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_5",
                'mount_point': "/tmp/mount_9"},
            'vm_nfs_mount_10': {
                'device_path': "%(sfs_host)s:/vx/story7815-mount_2",
                'mount_point': "/tmp/mount_10"},
            'vm_nfs_mount_11': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_2",
                'mount_point': "/tmp/mount_11",
                'mount_options': 'timeo=14,soft,rsize=32768'},
            'vm_nfs_mount_12': {
                'device_path': "%(sfs_ip)s:/vx/story7815-mount_3",
                'mount_point': "/tmp/mount_12",
                'mount_options': 'timeo=14,soft'}}

        ########################################################
        # CLUSTERED SERVICES CHILD OBJECTS - VM-SSH-KEYS
        ########################################################
        conf['ssh_keys_per_cs'] = {
            'CS_VM3': ['ssh_key_rsa_14'],
            'CS_VM4': ['ssh_key_rsa_15',
                       'ssh_key_rsa_16',
                       'ssh_key_rsa_17',
                       'ssh_key_rsa_18',
                       'ssh_key_rsa_19'],
            'CS_VM5': ['ssh_key_rsa_10']}

        ########################################################
        # VM SSH KEYS
        ########################################################
        conf['vm_ssh_keys'] = {
            'ssh_key_rsa_14': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvCuWxbw+ONU' +
                           'EfFEOQo9/XaqqxCoxF2yS5CchB0AmLSoPaYdnn4THXCGNu' +
                           'xMYOv4ABXKANNamJWGBIQjqZWqCSCnxyCCvfmCAs0M+or2' +
                           'Sokor7nOD99CpTeAgtmzhrWK+aupB5REy/VzW7P6vDtQxZ' +
                           'BBXx/3vpr81ViYmuLIqSbZU1BfU2cZdDQVOXnkPAW3i3Rh' +
                           'MLj2wvJDrsEUb0Xa6s4baqa0R94TSa4AkNvdlNE+ugKN9X' +
                           '3mCAZPDNd5DUogp8Oxt2wY7cZVpaEPJFO0iP5eshKvyMXi' +
                           'kgDKwU+IqaBF8y6ShSRFSIuQFvL1OLOpo69MchE1JGu459' +
                           'YnoOHUGNw== root@atvts1852'},
            'ssh_key_rsa_15': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAny9V3hymQdO' +
                           'gm2JcPQYa9sg/tzzJaYZSaS1KJ53DadN3dFxS6nBb9pDF+' +
                           'Fj5cldOGSgeLwV+GCufXyjO+5Mp1jAhetQXWlSOzznwj2u' +
                           'zDZHDu5jj2NpoFxIDfjuTsAreC0fg9GZueIYtEkO6x1wW0' +
                           'x1foNf2Q9wAQ1WFWm0NYCaHUbS0XMQTeM8UNCFAXsm7htO' +
                           'mWwijyxPyHPzjXzFnwJUQHvb6y5mBTgrAXi8m8JWVUlM0A' +
                           'Yz/6XpgQ7P4Bl6KT+8IbwIBuOm4GbQkB0/vYBK8HrPM6F5' +
                           'z6tQBs4HaXbr+8pLA0Or5NqaE9xRMUtP+uCZdd7CUWhL7h' +
                           'jl/v0oOWQ== root@atvts1852'},
            'ssh_key_rsa_16': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAy438d6c/272' +
                           'g0nOCrBDYANfECrYFTnOSXtqPKwqePp9QxPeYgnTv44u0f' +
                           '+6bOmMdB7M8PJnRx0fIT6nUkuHqK0i2CykkJgy6ZX+nfHV' +
                           'hxT5OpuypxCICa2RHALWToAZXxKM1sr64B6PjPDKwCckdp' +
                           'QiYfoE8/Yz42+tdN3l0xFLfc8yDuca1FT3oMUhsfii/tPS' +
                           'Yn+htftzbFBSiCCwyqfRCwcXQzu9AEqTIFrdOZyg0bKTSS' +
                           '/4SCfmPc/ZHCXyKCYaNHX+T9HL18+bmOnStVy6sHGTBmtD' +
                           'ArmhlmLC1OCaLE5/DjhhBFP23St84GDShYN1gAz4lAr2p6' +
                           'ot2rIPojw== root@atvts1852'},
            'ssh_key_rsa_17': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyg4oyr0K706' +
                           'YERlCHYtE4JS1WBmM+mXMdgpjXgzKCKFIGW4gxfB78I4LR' +
                           'n/giWE6JLOAfy4YJOVaNfjx/Oui4/QXpkc4AhgtYXVGRpB' +
                           'y5lSxlLZ0PMMD2KKi2KSFayIpqW3joOLDFkNi6xtdie5+i' +
                           'W622Kd450swcEQVwWdjLGHy/asBL+Kjzk5lnl46A/AwKl1' +
                           'Mr39avTj5gQrSwuZlXgi/gAdB2j78VB86cPvwgGKZGRmh/' +
                           'x4olCzucb4hdgJBX9WC7MwkCqQBtFesrJmbI37wadQbOBz' +
                           'H9pkKzt2HaFKpULigB03EKDgqfy62XYKfIHbbWMjHhIJci' +
                           'y3o30NGdw== root@atvts1852'},
            'ssh_key_rsa_18': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAtRpgOw67RQh' +
                           'CsiFpZQuUUyZHNUewAwGjZEjKS5McII4ULdc6+hbfq+bFn' +
                           '1KG0gok3aEiVFfh6DgLLQzJHT8Ovt1C7SagSyl5EwZ70X1' +
                           'J9Vyf+E/DGu0D8+/dppMaPTssU0O1O4vH1R8WMixgRLqxq' +
                           'dncJSmq+yM1P85KIxoR4RIp/ohxfYGdIwfGMBKgfVOjaEv' +
                           '527DG28vidAAYy/EnZyxtVe13b37CPh1CARYpvYRaLi4dC' +
                           'Z1jeCKbIsDKAU81pnfQEfElpYAfMWNbd9ZKwzphJCUucw0' +
                           'WH+JjXFa1HqWE31TN1vSdbPeP+3U+74q4CvA+htR7q7Yyt' +
                           'j589XEldw== root@atvts1852'},
            'ssh_key_rsa_19': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAy0TFTSwmA69' +
                           'vlZIytcOqlj4F19HBlcjuQQ+bSupOMAB2xgoG3Gp0z7B3D' +
                           '+FgBmMS2PCGejVHgywjqx0B5AIJ4hk0zPHSBxrNGK7EqD4' +
                           'nhfpXLv307GRiaGXt/kgOTJfSFV1xk1NmB03WkmymtedPp' +
                           'ppJGQy1eev+jcjI4y7aDXOr/LWm7gfdbehSqiKDlYpfGZb' +
                           'hByDtfjOZGf+XPf3aROyy8DIMIcfHRP+MqHkQlhmv81I+3' +
                           'F5IhN2JhJFvRGZMTSd+1IsK0EZmmETrseY6HXB/H6xSxJE' +
                           'AbJjAUo+Ufr/Xlb0Pg/evQJUA2Om7BpPfGbwXfHh5NbeQA' +
                           '6m7ReMwQQ== root@atvts1852'},
            'ssh_key_rsa_10': {
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA1sotosrlehl' +
                           '1llmO+7j/c0dH/Kj508jwONePNfgWUPbWVtZ5UEH0GI150' +
                           'R2iizVVe9+lqff5rRoA593xogE6ImR6ydqvXm200u6KveA' +
                           'LiRa1iqZyhDN3aJNabgziqCj5Db/HcXI38zOGYRulUQ2Eo' +
                           'kFS8M058O2ungmli0VlWvmdUbpIXU5rylaOHKecPmBw6VU' +
                           'xGnC+CgUDd+gUOdmeDtxml6wAuKHbz7jfnw9Odd5AfoCOL' +
                           '4pxFkFUBsyQb4L/hu6DCiwPv1hzsVI3P/izEGVS01ehpbW' +
                           'kKDHAkPxddqW24X6MyRLZpXwY6Hwf0JSkWF52seqjGf/MM' +
                           'Jd/h8AJdQ== root@atvts1852'}
        }

        # Needed for VCS verification methods
        conf['network_per_ip'] = {}
        # IPv6 static address for IPv6 only configuration
        conf['ipv6_only_static'] = {'CS_VM4': '2001:db8:85a3::7516:2/48'}
        # gateway6 address
        conf['ipv6_only_gw6'] = {'CS_VM4': '2001:db8:85a3::7516:1'}
        # IPv6 static address for dual stack two vms in parallel
        conf['ipv6_dual_stack_ps'] = {
            'CS_VM5':
                '2001:db8:85a3::7516:13/48,2001:db8:85a3::7516:14/48'}
        # gateway6
        conf['ipv6_dual_stack_gw6_ps'] = {
            'CS_VM5': '2001:db8:85a3::7516:12'}
        # IPv6 static address for IPv6 only expand CS
        conf['ipv6_only_static_expand'] = {
            'CS_VM4':
                '2001:db8:85a3::7516:15,2001:db8:85a3::7516:16'}
        # IPv6 gateway update case
        conf['gateway6_expand_update'] = {
            'CS_VM4':
                '2001:db8:85a3::7516:17'}
        # IPv6 static address for dual stack, ipv4 dhcp
        conf['ipv6_dual_stack_dhcp4'] = {
            'CS_VM3': '2001:db8:85a3::7516:11/48'}
        # gatewa6 address
        conf['ipv6_dual_stack_gw6_dhcp4'] = {
            'CS_VM3': '2001:db8:85a3::7516:10'}

        return conf

    @staticmethod
    def define_online_ordering_dependencies():
        """
        Returns a dictionary of clustered-services which define
        their VCs onlining order.

        Returns:
           dict. Dictionary which defines online dependencies.
        """
        online_dependencies = {'CS_VM1': [],
                               'CS_VM2': [],
                               'CS_VM3': [],
                               'CS_VM4': ['CS_VM3'],
                               'CS_VM5': ['CS_VM3', 'CS_VM4']}
        return online_dependencies

    def generate_cli_commands_ms_service(self, conf, ms_service, ipaddresses,
                                         ms_host_name, mgmt_bridge_info,
                                         sfs_host_name, sfs_ip_addr,
                                         replace_map=None):
        """
        Function to generate CLI commands that will setup the supplied ms
        service, IP's and lsb resources. They will be in format so
        they can be used with the execute_cli_<create/link>_cmd functions.

        Args:
            conf (dict): The required configuration of ms services.

            ms_service (str): Name of ms service as defined in
            configuration.

            ipaddresses (dict): Dynamically generated dictionary of IP
            addresses per network.

            ms_host_name (str): Hostname of MS used for adding to host data
            on nested VMs.

            mgmt_bridge_info (dict): Dictionary containing mgmt network name,
            device name and ipaddress.

            sfs_host_name (str): Hostname of SFS.

            sfs_ip_addr (str): IP address of SFS.

        Kwargs:
            replace_map (dict): The dictionary that will be used to replace
            named placeholders in the properties.

        Return:
            dict. Dictionary of CLI commands.
        """
        # Empty list of dictionaries to be built up and returned
        interfaces_data = []
        hosts_data = []
        interfaces_ip_data = []
        repos_data = []
        packages_data = []
        mounts_data = []
        keys_data = []

        # MS Service URL
        srv_url = '/ms/services/' + ms_service
        # Properties for vm service
        srv_params = conf["params_per_ms_srv"][ms_service]
        #########################################
        # Define MS Services in the model       #
        #########################################
        class_type = "vm-service"
        options = "image_name={0} " \
                  "cpus={1} " \
                  "ram='{2}' " \
                  "internal_status_check={3} " \
                  "hostnames={4} " \
                  "service_name='{5}'".format(srv_params["image_name"],
                                              srv_params["cpus"],
                                              srv_params["ram"],
                                           srv_params["internal_status_check"],
                                              srv_params["hostnames"],
                                              srv_params['service_name'])

        srv_data = {'url': srv_url,
                    'class_type': class_type,
                    'options': options}

        #########################################################
        # Create interfaces under                               #
        # /ms/services/<service_name>/network_interfaces/       #
        #########################################################
        if 'interfaces_per_ms_srv' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            interfaces_url = \
                "/ms/services/{0}/vm_network_interfaces/".format(service)
            interfaces = conf["interfaces_per_ms_srv"][ms_service]
            class_type = 'vm-network-interface'
            conf_key = 'vm_interfaces'

            for interface in interfaces:
                inter_data = conf[conf_key][interface]
                inter_data['network_name'] = \
                    mgmt_bridge_info['network_name']
                inter_data['host_device'] = \
                    mgmt_bridge_info['host_device']
                obj_url = interfaces_url + interface
                interfaces_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, inter_data,
                        replace_map=replace_map))
                ms_vm_int_url = ("/ms/services/" + ms_service +
                                 "/vm_network_interfaces/" +
                                 interface)
                interfaces_ip_data.append({'url': ms_vm_int_url,
                                           'options': ipaddresses
                                           [interface]})

        # Create Hosts under /ms/services/<service_name>/hosts/
        if 'hosts_per_ms_srv' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            hosts_url = "/ms/services/{0}/vm_aliases/".format(service)
            hosts = conf["hosts_per_ms_srv"][ms_service]
            class_type = 'vm-alias'
            conf_key = 'vm_hosts'
            for host in hosts:
                obj_url = hosts_url + host
                hosts_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, conf[conf_key][host],
                        replace_map=replace_map))
            obj_url = hosts_url + "ms"
            ms_ip_addr = mgmt_bridge_info['ipaddress_ms']
            ms_host_conf = {'alias_names': ms_host_name,
                            'address': ms_ip_addr}
            hosts_data.append(
                self.compile_object_data_for_cli_creation_cmds(
                    obj_url, class_type, ms_host_conf,
                    replace_map=replace_map))
            obj_url = hosts_url + "sfs"
            sfs_host_conf = {'alias_names': sfs_host_name,
                             'address': sfs_ip_addr}
            hosts_data.append(
                self.compile_object_data_for_cli_creation_cmds(
                    obj_url, class_type, sfs_host_conf,
                    replace_map=replace_map))

        ####################################################
        # Create VM YUM repos under
        #   /ms/services/<service_name>/vm_yum_repos/
        ####################################################
        if 'cloud_init_repos' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            repos_url = \
                "/ms/services/{0}/vm_yum_repos/".format(service)
            repos = conf["cloud_init_repos"][ms_service]
            class_type = 'vm-yum-repo'
            for repo in repos:
                obj_url = repos_url + 'repo_{0}'.format(repo)
                obj_props = {
                    'name': repo,
                    'base_url': repos[repo],
                }
                repos_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, obj_props,
                        replace_map=replace_map))

        ####################################################
        # Create VM packages under
        #   /ms/services/<service_name>/vm_packages/
        ####################################################
        if 'cloud_init_packages' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            packages_url = \
                "/ms/services/{0}/vm_packages/".format(service)
            packages = conf["cloud_init_packages"][ms_service]
            class_type = 'vm-package'
            for package in packages:
                obj_url = packages_url + 'pkg_{0}'.format(package)
                obj_props = {
                    'name': package,
                }
                packages_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, obj_props,
                        replace_map=replace_map))

        #########################################################
        # Create VM-NFS-MOUNTS under                            #
        # /ms/services/<service_name>/vm_nfs_mounts/      #
        #########################################################
        if 'vm_nfs_mounts' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            mounts_url = \
                "/ms/services/{0}/vm_nfs_mounts/".format(service)
            mounts = conf['nfs_mounts_per_ms_srv'][ms_service]
            class_type = 'vm-nfs-mount'
            conf_key = 'vm_nfs_mounts'
            for mount in mounts:
                mount_conf_data = conf[conf_key][mount]
                obj_url = mounts_url + mount
                mounts_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, mount_conf_data,
                        replace_map=replace_map))

        #########################################################
        # Create VM-SSH-KEYS under                              #
        # /ms/services/<service_name>/vm_ssh_keys/        #
        #########################################################
        if 'vm_ssh_keys' in conf.keys():
            service = conf["app_per_ms_srv"][ms_service]
            keys_url = \
                "/ms/services/{0}/vm_ssh_keys/".format(service)
            keys = conf['ssh_keys_per_ms_srv'][ms_service]
            class_type = 'vm-ssh-key'
            conf_key = 'vm_ssh_keys'
            for key in keys:
                key_conf_data = conf[conf_key][key]
                obj_url = keys_url + key
                keys_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, key_conf_data,
                        replace_map=replace_map))

        full_list = {}
        full_list['vm_srv'] = srv_data
        full_list['vm_interfaces'] = interfaces_data
        full_list['vm_interfaces_ips'] = interfaces_ip_data
        full_list['vm_hosts'] = hosts_data
        full_list['vm_repos'] = repos_data
        full_list['vm_packages'] = packages_data
        full_list['vm_nfs_mounts'] = mounts_data
        full_list['vm_ssh_keys'] = keys_data

        return full_list

    def generate_cli_commands(self, conf, vcs_cluster_url, clustered_service,
                              ipaddresses, ms_host_name, mgmt_bridge_info,
                              dhcp_bridge_info, sfs_host_name, sfs_ip_addr,
                              replace_map=None):
        """
        Function to generate CLI commands that will setup the supplied VCS
        clustered-services, IP's and lsb resources. They will be in format so
        they can be used with the execute_cli_<create/link>_cmd functions.

        Args:
            conf (dict): The required configuration of clustered-services.

            vcs_cluster_url (str): URL for the cluster in the model.

            clustered_service (str): Name of clustered service as defined in
            configuration.

            ipaddresses (dict): Dynamically generated dictionary of IP
            addresses per network.

            ms_host_name (str): Hostname of MS used for adding to host data
            on nested VMs.

            mgmt_bridge_info (dict): Dictionary containing mgmt network name,
            device name and ipaddress.

            dhcp_bridge_info (dict): Dictionary containing dhcp network name,
            device name and ipaddress.

            sfs_host_name (str): Hostname of SFS.

            sfs_ip_addr (str): IP address of SFS.

        Kwargs:
            replace_map (dict): The dictionary that will be used to replace
            named placeholders in the properties.

        Return:
            dict. Dictionary of CLI commands.
        """
        # Empty list of dictionaries to be built up and returned
        interfaces_data = []
        hosts_data = []
        interfaces_ip_data = []
        repos_data = []
        packages_data = []
        mounts_data = []
        keys_data = []

        #########################################################
        # Create interfaces under                               #
        # /software/services/<service_name>/network_interfaces/ #
        #########################################################
        if 'interfaces_per_cs' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            interfaces_url = \
                "/software/services/{0}/vm_network_interfaces/".format(service)
            interfaces = conf["interfaces_per_cs"][clustered_service]
            class_type = 'vm-network-interface'
            conf_key = 'vm_interfaces'

            static_ipv6 = \
                conf.get('ipv6_only_static', {}).get(clustered_service)
            static_ipv6_gw6 = \
                conf.get('ipv6_only_gw6', {}).get(clustered_service)
            dualstck_stat_ipv6 = \
                conf.get('ipv6_dual_stack_dhcp4', {}).get(clustered_service)
            dualstck_stat_gw6 = \
                conf.get('ipv6_dual_stack_gw6_dhcp4', {}).get(
                    clustered_service)
            dualstck_ipv6_ps = \
                conf.get('ipv6_dual_stack_ps', {}).get(clustered_service)
            dualstck_gw6_ps = \
                conf.get('ipv6_dual_stack_gw6_ps', {}).get(clustered_service)
            for interface in interfaces:
                if_conf_data = conf[conf_key][interface]
                if 'dhcp' in interface:
                    if_conf_data['network_name'] = \
                        dhcp_bridge_info['network_name']
                    if_conf_data['host_device'] = \
                        dhcp_bridge_info['host_device']
                else:
                    if_conf_data['network_name'] = \
                        mgmt_bridge_info['network_name']
                    if_conf_data['host_device'] = \
                        mgmt_bridge_info['host_device']
                obj_url = interfaces_url + interface
                interfaces_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, if_conf_data,
                        replace_map=replace_map))
                if 'dhcp' in interface and static_ipv6_gw6:
                    interfaces_data[-1]['options'] = \
                        interfaces_data[-1]['options'] + "gateway6='{0}'". \
                            format(static_ipv6_gw6)
                elif 'dhcp' in interface and dualstck_stat_gw6:
                    interfaces_data[-1]['options'] = \
                        interfaces_data[-1]['options'] + "gateway6='{0}'". \
                            format(dualstck_stat_gw6)
                elif 'net15' in interface and dualstck_gw6_ps:
                    interfaces_data[-1]['options'] = \
                        interfaces_data[-1]['options'] + "gateway6='{0}'". \
                            format(dualstck_gw6_ps)
                cs_app_url = (vcs_cluster_url + "/services/" +
                              clustered_service + "/applications/" +
                              service + "/vm_network_interfaces/" + interface)
                if 'dhcp' in interface and static_ipv6:
                    interfaces_ip_data.append({'url': cs_app_url,
                                               'options':
                                                   'ipv6addresses="{0}"'.
                                              format(static_ipv6)})
                elif 'dhcp' in interface and dualstck_stat_ipv6:
                    interfaces_ip_data.append({'url': cs_app_url,
                                               'options':
                                                   'ipv6addresses="{0}" {1}'.
                                              format(dualstck_stat_ipv6,
                                                     ipaddresses
                                                     [interface])})
                elif 'net15' in interface and dualstck_ipv6_ps:
                    interfaces_ip_data.append({'url': cs_app_url,
                                               'options':
                                                   'ipv6addresses="{0}" {1}'.
                                              format(dualstck_ipv6_ps,
                                                     ipaddresses
                                                     [interface])})
                else:
                    interfaces_ip_data.append({'url': cs_app_url,
                                               'options': ipaddresses
                                               [interface]})

        # Create Hosts under /software/services/<service_name>/hosts/
        if 'hosts_per_cs' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            hosts_url = "/software/services/{0}/vm_aliases/".format(service)
            hosts = conf["hosts_per_cs"][clustered_service]
            class_type = 'vm-alias'
            conf_key = 'vm_hosts'
            for host in hosts:
                obj_url = hosts_url + host
                hosts_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, conf[conf_key][host],
                        replace_map=replace_map))
            obj_url = hosts_url + "ms"
            ms_ip_addr = mgmt_bridge_info['ipaddress_ms']
            ms_host_conf = {'alias_names': ms_host_name,
                            'address': ms_ip_addr}
            hosts_data.append(
                self.compile_object_data_for_cli_creation_cmds(
                    obj_url, class_type, ms_host_conf,
                    replace_map=replace_map))
            obj_url = hosts_url + "sfs"
            sfs_host_conf = {'alias_names': sfs_host_name,
                             'address': sfs_ip_addr}
            hosts_data.append(
                self.compile_object_data_for_cli_creation_cmds(
                    obj_url, class_type, sfs_host_conf,
                    replace_map=replace_map))

        ####################################################
        # Create VM YUM repos under
        #   /software/services/<service_name>/vm_yum_repos/
        ####################################################
        if 'cloud_init_repos' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            repos_url = \
                "/software/services/{0}/vm_yum_repos/".format(service)
            repos = conf["cloud_init_repos"][clustered_service]
            class_type = 'vm-yum-repo'
            for repo in repos:
                obj_url = repos_url + 'repo_{0}'.format(repo)
                obj_props = {
                    'name': repo,
                    'base_url': repos[repo],
                }
                repos_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, obj_props,
                        replace_map=replace_map))

        ####################################################
        # Create VM packages under
        #   /software/services/<service_name>/vm_packages/
        ####################################################
        if 'cloud_init_packages' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            packages_url = \
                "/software/services/{0}/vm_packages/".format(service)
            packages = conf["cloud_init_packages"][clustered_service]
            class_type = 'vm-package'
            for package in packages:
                obj_url = packages_url + 'pkg_{0}'.format(package)
                obj_props = {
                    'name': package,
                }
                packages_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, obj_props,
                        replace_map=replace_map))

        #########################################################
        # Create VM-NFS-MOUNTS under                            #
        # /software/services/<service_name>/vm_nfs_mounts/      #
        #########################################################
        if 'vm_nfs_mounts' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            mounts_url = \
                "/software/services/{0}/vm_nfs_mounts/".format(service)
            mounts = conf['nfs_mounts_per_cs'][clustered_service]
            class_type = 'vm-nfs-mount'
            conf_key = 'vm_nfs_mounts'
            for mount in mounts:
                mount_conf_data = conf[conf_key][mount]
                obj_url = mounts_url + mount
                mounts_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, mount_conf_data,
                        replace_map=replace_map))

        #########################################################
        # Create VM-SSH-KEYS under                              #
        # /software/services/<service_name>/vm_ssh_keys/        #
        #########################################################
        if 'vm_ssh_keys' in conf.keys():
            service = conf["app_per_cs"][clustered_service]
            keys_url = \
                "/software/services/{0}/vm_ssh_keys/".format(service)
            keys = conf['ssh_keys_per_cs'][clustered_service]
            class_type = 'vm-ssh-key'
            conf_key = 'vm_ssh_keys'
            for key in keys:
                key_conf_data = conf[conf_key][key]
                obj_url = keys_url + key
                keys_data.append(
                    self.compile_object_data_for_cli_creation_cmds(
                        obj_url, class_type, key_conf_data,
                        replace_map=replace_map))

        full_list = {}
        full_list['vm_interfaces'] = interfaces_data
        full_list['vm_interfaces_ips'] = interfaces_ip_data
        full_list['vm_hosts'] = hosts_data
        full_list['vm_repos'] = repos_data
        full_list['vm_packages'] = packages_data
        full_list['vm_nfs_mounts'] = mounts_data
        full_list['vm_ssh_keys'] = keys_data

        return full_list

    def generate_cli_commands_vmimage(self, conf, vm_image_id,
                                      replace_map=None):
        """
        Function to generate CLI commands that will setup the supplied VCS
        clustered-services, IP's and lsb resources. They will be in format so
        they can be used with the execute_cli_<create/link>_cmd functions.

        Args:
            conf (dict): The required configuration of VM images.

            vm_image_id (dict): The dictionary key of the VM image.

        Kwargs:
            replace_map (dict): The dictionary that will be used to replace
            named placeholders in the properties.

        Return:
            dict. Dictionary of CLI commands.
        """
        # Empty list of dictionaries to be built up and returned
        vm_images_data = {}

        #########################################################
        # Define any vm-image properties under /software/images #
        #########################################################
        if 'vm_images' in conf.keys():
            obj_url = '/software/images/' + vm_image_id
            class_type = 'vm-image'
            conf_key = 'vm_images'
            vm_images_data = \
                self.compile_object_data_for_cli_creation_cmds(
                    obj_url, class_type, conf[conf_key][vm_image_id],
                    replace_map=replace_map)

        full_list = {}
        full_list['vm_images'] = vm_images_data
        return full_list

    @staticmethod
    def compile_object_data_for_cli_creation_cmds(obj_url, class_type,
                                                  obj_props, replace_map=None):
        """
        Function to compile the object dictionary of CLI commands.

        Args:
            obj_url (str): URL under which the object should be created.

            class_type (str): LITP object class type of the object to be\
               created.

            obj_props (dict): The required item properties and their values.

        Kwargs:
            replace_map (dict): The dictionary that will be used to replace\
               named placeholders in the properties.

        Return:
            dict. Dictionary of CLI commands.
        """
        options = ""
        for obj_prop, value in obj_props.items():
            if replace_map:
                value = value % replace_map
            options = options + obj_prop + "='" + value + "' "

        obj_data = {'url': obj_url,
                    'class_type': class_type,
                    'options': options}
        return obj_data

    @staticmethod
    def compile_object_data_for_cli_update_cmds(parent_url, conf,
                                                conf_key, conf_subkey):
        """
        Function to compile the object dictionary of CLI commands.

        Args:
            parent_url (str): URL under which the object should be created.

            conf (dict): The required configuration of clustered-services.

            conf_key (str): The key identifier of the dictionary to retrieve\
               from inside the dictionary container.

            conf_subkey (str): The sub key, typically the clustered-service\
               name, from which the data is to be selected.

        Return:
            dict. Dictionary of CLI commands.
        """
        options = ""
        obj_props = conf[conf_key][conf_subkey].keys()
        for obj_prop in obj_props:
            value = \
                conf[conf_key][conf_subkey][obj_prop]
            options = options + obj_prop + "='" + value + "' "

        obj_data = {'url': parent_url,
                    'options': options}
        return obj_data

    def get_libvirt_service_start_cmd(self, service_name):
        """
        Description:
            Function to construct the libvirt service start command against
            the provided service.

        Args:
            service_name (str): The name of the service against which the
                                start command is to be issued.

        Returns:
            str. The command to start the VM service.
        """

        return '{0}/{1} {2} start'.format(self.instances_data_dir.rstrip('/'),
                                          self.libvirt_module_name,
                                          service_name)

    def get_libvirt_service_stop_cmd(self, service_name):
        """
        Description:
            Function to construct the libvirt service stop command against
            the provided service.

        Args:
            service_name (str): The name of the service against which the
                                stop command is to be issued.

        Returns:
            str. The command to stop the VM service.
        """

        return '{0}/{1} {2} stop'.format(self.instances_data_dir.rstrip('/'),
                                         self.libvirt_module_name,
                                         service_name)

    def get_libvirt_service_status_cmd(self, service_name):
        """
        Description:
            Function to construct the libvirt service status command against
            the provided service.

        Args:
            service_name (str): The name of the service against which the
                                status command is to be issued.

        Returns:
            str. The command to status check the VM service.
        """

        return '{0}/{1} {2} status'.format(self.instances_data_dir.rstrip('/'),
                                           self.libvirt_module_name,
                                           service_name)

    def get_vm_config_path(self, service_name):
        """
        Description:
            Returns the full path to the VM config file based on the passed
            VM service name.

        Args:
            service_name (str): The name of the VM service.

        Returns:
            str. Path to the VM config file.
        """

        path = "{0}/{1}/config.json"
        return path.format(self.instances_data_dir.rstrip('/'),
                           service_name)

    def get_vm_image_path(self, service_name, image_name):
        """
        Description:
            Returns the full path to the VM image file based on the passed
            VM service name and VM image name.

        Args:
            service_name (str): The name of the VM service.

            image_name (str): The name of the VM image.

        Returns:
            str. Path to the VM image file.
        """

        path = "{0}/{1}/{2}"
        return path.format(self.instances_data_dir.rstrip('/'),
                           service_name, image_name)

    @staticmethod
    def get_vm_service_inherited_item_url(cluster_url, cs_name, app_name):
        """
        Description:
            Returns the URL of the inherited vm-service item under cluster.

        Args:
            cluster_url (str): URL of the cluster.

            cs_name (str): Item name of the clustered service.

            app_name (str): Item name of the application.

        Returns:
            str. URL of inherited vm-service item under cluster.
        """
        url = '{0}/services/{1}/applications/{2}'.format(
            cluster_url, cs_name, app_name)
        return url

    @staticmethod
    def get_vm_network_base_item_url(app_name, if_name):
        """
        Description:
            Returns the URL of the base vm-network-interface
            item under /software

        Args:
            app_name (str): Item name of the application.

            if_name (str): Item name of the network interface.

        Returns:
            str. URL of base vm-network-interface item under /software
        """
        url = \
            '/software/services/{0}/vm_network_interfaces/{1}'.format(
                app_name, if_name)
        return url

    @staticmethod
    def get_vm_network_inherited_item_url(cluster_url, cs_name, app_name,
                                          if_name):
        """
        Description:
            Returns the URL of the inherited vm-network-interface
            item under cluster.

        Args:
            cluster_url (str): URL of the cluster.

            cs_name (str): Item name of the clustered service.

            app_name (str): Item name of the application.

            if_name (str): Item name of the network interface.

        Returns:
            str. URL of inherited vm-network-interface item under cluster.
        """
        url = ('{0}/services/{1}/applications/{2}/' +
               'vm_network_interfaces/{3}').format(
            cluster_url, cs_name, app_name, if_name)
        return url

    @staticmethod
    def get_vm_alias_base_item_url(app_name, alias_name):
        """
        Description:
            Returns the URL of the base vm-alias item under /software

        Args:
            app_name (str): Item name of the application.

            alias_name (str): Item name of the alias.

        Returns:
            str. URL of base vm-alias item under /software
        """
        url = \
            '/software/services/{0}/vm_aliases/{1}'.format(
                app_name, alias_name)
        return url

    @staticmethod
    def get_vm_nfs_mount_base_item_url(app_name, mount_name):
        """
        Description:
            Returns the URL of the base vm-nfs-mount item under /software

        Args:
            app_name (str): Item name of the application.

            mount_name (str): Item name of the mount.

        Returns:
            str. URL of base vm-nfs-mount item under /software
        """
        url = \
            '/software/services/{0}/vm_nfs_mounts/{1}'.format(
                app_name, mount_name)
        return url

    @staticmethod
    def get_vm_alias_inherited_item_url(cluster_url, cs_name, app_name,
                                        alias_name):
        """
        Description:
            Returns the URL of the inherited vm-alias item under cluster.

        Args:
            cluster_url (str): URL of the cluster.

            cs_name (str): Item name of the clustered service.

            app_name (str): Item name of the application.

            alias_name (str): Item name of the alias.

        Returns:
            str. URL of inherited vm-alias item under cluster.
        """
        url = ('{0}/services/{1}/applications/{2}/vm_aliases/{3}').format(
            cluster_url, cs_name, app_name, alias_name)
        return url

    @staticmethod
    def get_vm_repo_inherited_item_url(cluster_url, cs_name, app_name,
                                       repo_name):
        """
        Description:
            Returns the URL of the inherited vm-yum-repo item under cluster.

        Args:
            cluster_url (str): URL of the cluster.

            cs_name (str): Item name of the clustered service.

            app_name (str): Item name of the application.

            repo_name (str): Item name of the repo.

        Returns:
            str. URL of inherited vm-yum-repo item under cluster.
        """
        url = '{0}/services/{1}/applications/{2}/vm_yum_repos/{3}'.format(
            cluster_url, cs_name, app_name, repo_name)
        return url
