"""
File used to store string constants used throughout the utilities and
within test stories.
"""

SSH_KEYS_FOLDER = "/home/litp-admin/.ssh"
"""Folder where SSH keys are defined"""

#OS RELATED CONST
LITP_SERVICE_FILE_NAME = 'litp_service.py'
""" Name of the LITP python module """
LITP_MAINT_STATE_FILE = '/var/lib/litp/core/maintenance_job_state.txt'
""" Maintenance mode status file. """
RH_VERSION_6 = "Red Hat Enterprise Linux Server release 6.6 (Santiago)"
"""Defines the RH release file for RHEL6.6 and version string expected"""
RH_VERSION_6_10 = "Red Hat Enterprise Linux Server release 6.10 (Santiago)"
"""Defines the RH release file for RHEL6.10 and version string expected"""
RH_VERSION_7 = "Red Hat Enterprise Linux Server release 7.2 (Maipo)"
"""Defines the RH release file for RHEL7.2 and version string expected"""
RH_VERSION_7_4 = "Red Hat Enterprise Linux Server release 7.4 (Maipo)"
"""Defines the RH release file for RHEL7.4 and version string expected"""
RH_VERSION_7_9 = "Red Hat Enterprise Linux Server release 7.9 (Maipo)"
"""Defines the RH release file for RHEL7.9 and version string expected"""
SLES_VERSION_15_4 = "SUSE Linux Enterprise Server 15 SP4"
"""Defines the SLES15-4 release file version string expected"""
RH_RELEASE_FILE = "/etc/redhat-release"
"""Defines the File location of the Red Hat release information"""
SLES_RELEASE_FILE = "/etc/os-release"
"""Defines the File location of the SLES release information"""
GEN_SYSTEM_LOG_PATH = "/var/log/messages"
"""Defines the File location of general system logs"""
LOGROTATED_SYSLOG_FILE1 = "/var/log/messages.1"
"""Defines the File location of first log rotated system logs"""
LITP_LIB_PATH = "/var/lib/litp/"
"""Defines the File location of the LITP lib path"""
LITP_DOCS_PATH = "/opt/ericsson/nms/litp/share/docs"
"""Defines the path to the LITP documentation"""
LITP_EXT_DOC_PATH = "/opt/ericsson/nms/litp/share/docs/extensions"
"""Defines the path to the LITP extensions documentation"""
LITP_ITEM_TYPE_PATH = "/opt/ericsson/nms/litp/share/docs/item_types"
"""Defines the path to the LITP item types documentation"""
LITP_PROP_TYPE_PATH = "/opt/ericsson/nms/litp/share/docs/property_types"
"""Defines the path to the LITP property types documentation"""
LITP_PLUGIN_DOC_PATH = "/opt/ericsson/nms/litp/share/docs/plugins"
"""Defines the path to the LITP plugin documentation"""
LITP_PATH = "/opt/ericsson/nms/litp/"
"""Defines the LITP filepath"""
LITP_MIG_PATH = "/opt/ericsson/nms/litp/etc/migrations/"
"""Defines the LITP migrations filepath"""
LITP_EXT_PATH = "/opt/ericsson/nms/litp/etc/extensions/"
"""Defines the LITP extensions filepath"""
LITP_PLUGIN_PATH = "/opt/ericsson/nms/litp/etc/plugins/"
"""Defines the LITP plugins filepath"""
GRUB_CONFIG_FILE = "/boot/grub2/grub.cfg"
"""GRand Unified Bootloader (GRUB) Config file"""
GRUB_CONFIG_DIR = "/boot/grub2/"
"""GRand Unified Bootloader (GRUB) directory path"""
LITP_SHADOW_FILE = "/opt/ericsson/nms/litp/etc/litp_shadow"
"""Path to the LITP shadow file"""
LITP_SEC_CONF_FILE = "/etc/litp_security.conf"
"""Path to the LITP security file"""
LITP_DEFAULT_OS_PROFILE_PATH = "/var/www/html/6/os/x86_64/"
LITP_DEFAULT_OS_PROFILE_PATH_RHEL6_10 = "/var/www/html/6.10/os/x86_64/"
LITP_DEFAULT_OS_PROFILE_PATH_RHEL7 = "/var/www/html/7/os/x86_64/"
LITP_DEFAULT_OS_PROFILE_PATH_RHEL7_9 = "/var/www/html/7.9/os/x86_64/Packages/"
"""Default path to set when creating os-profile"""
ETC_HOSTS = "/etc/hosts"
"""Hosts file"""
OS_UPDATES_PATH = "/var/www/html/6/updates/x86_64/Packages"
OS_UPDATES_PATH_RHEL6_10 = "/var/www/html/6.10/updates/x86_64/Packages"
"""Path to the update packages"""
OS_UPDATES_PATH_RHEL7 = "/var/www/html/7/updates/x86_64/Packages"
"""Path to the update RHEL7 packages"""
KERNEL_CMDLINE_CONFIG_FILE = "/proc/cmdline"
"""Kernel command line parameters"""
SHUTDOWN_PATH = "/sbin/shutdown"
"""Path to shutdown"""
LITP_LAST_KNOWN_CONFIG = "/var/lib/litp/core/model/LAST_KNOWN_CONFIG"
"""Path to last known LITP model pickled backup."""
LITP_LOGGING_CONF = "/etc/litp_logging.conf"
"""Path to LITP service logging configuration file."""
KILL_PATH = "/bin/kill"
"""Path to kill command"""
PGREP_PATH = "/usr/bin/pgrep"
"""Path to pgrep command"""
LSOF_PATH = "/usr/sbin/lsof"
"""Path to lsof command"""
NOHUP_PATH = "/usr/bin/nohup"
"""Path to nohup command"""
SERVICE_PATH = "/sbin/service"
"""Path to service command"""
SYSTEMCTL_PATH = "/usr/bin/systemctl"
"""Path to systemctl command"""
SSH_WARNING_MSG = "/etc/issue"
"""Path to issue file"""
REBOOT_PATH = "/sbin/reboot"
"""Path to reboot command"""
CREATEREPO_PATH = "/usr/bin/createrepo"
"""Path to createrepo command"""
RPM_PATH = "/usr/bin/rpm"
"""Path to rpm command"""
LVCONVERT_PATH = "/sbin/lvconvert"
"""Path to lvconvert command"""
CURL_PATH = "/usr/bin/curl"
"""Path to curl command"""
STDOUT_PATH = "/dev/stdout"
"""Path to device stdout command"""
AUDIT_RULES_FILE = "/etc/audit/audit.rules"
"""Path to audit rules"""
AUDIT_RULES_LOG = "/var/log/audit/audit.log"
"""Path to audit log"""
PKILL_PATH = "/usr/bin/pkill"
"""Path to pkill command"""
GROUPS_PATH = "/usr/bin/groups"
"""Path to groups command"""
USERADD_PATH = "/usr/sbin/useradd"
"""Path to useradd command"""
USERDEL_PATH = "/usr/sbin/userdel"
"""Path to userdel command"""
CHMOD_PATH = "/bin/chmod"
"""Path to chmod command"""
KILLALL_PATH = "/usr/bin/killall"
"""Path to killall command"""
UNIQ_PATH = "/usr/bin/uniq"
"""Path to uniq command"""
REV_PATH = "/usr/bin/rev"
"""Path to rev command"""

#JAVA RELATED
JAVA_PATH = "/usr/bin/java"
"""Path to java command"""

#SYS_CONTROL RELATED
SYSCTL_CONFIG_FILE = "/etc/sysctl.conf"
"""The path to the sysctrl config file"""

#LIBVIRT RELATED
LIBVIRT_ADAPTOR_PKG_NAME = "ERIClitpmnlibvirt_CXP9031529"
"""Defines the name of the libvirt adaptor rpm"""
LIBVIRT_DIR = "/var/lib/libvirt"
"""Defines the directory in which libvirt is installed."""
LIBVIRT_INSTANCES_DIR = "{0}/instances".format(LIBVIRT_DIR)
"""Defines the directory in which the nested VM instances reside"""
LIBVIRT_MODULE_DIR = "/opt/ericsson/nms/litp/lib/litpmnlibvirt/"
"""Defines the directory in which the libvirt adaptor module resides."""
LIBVIRT_MODULE_NAME = "litp_libvirt_adaptor.py"
"""Defines the name of the libvirt adaptor module."""
LIBVIRT_IMAGE_DIR = "{0}/images".format(LIBVIRT_DIR)
"""Defines the File location where libvirt images are stored"""
VM_IMAGE_MS_DIR = "/var/www/html/images/"
"""Defines the location on the MS where images are stored"""
LIBVIRT_CONFIG_DIR = "/etc/libvirt/qemu"
"""Defines the File location of the libvirt config directory"""
LIBVIRT_ERR_LOG = "/var/log/libvirt/libvirtd.log"
"""Defines the File location of the libvirt error log"""
KOAN_ERR_LOG = "/var/log/koan/koan.log"
"""Defines the File location of the koan error log"""
LIBVIRT_VM_USERNAME = "root"
"""Defines the username used to log onto VM"""
LIBVIRT_VM_PASSWORD = "passw0rd"
"""Defines the password used to log onto VM"""
LIBVIRT_SLES_VM_PASSWORD = "12shroot"
"""Defines the password used to log onto SLES VM"""
LIBVIRT_MAX_VM_STARTUP_TIME = 600
"""Defines the maximum number of seconds to wait for VM to start"""
LITP_LIBVIRT_LOG = "/var/log/litp/litp_libvirt.log"
"""Defines the File location of the libvirt log"""
VIRT_WHAT_CMD = "/usr/sbin/virt-what"
"""Path to virt-what command"""

#NETWORK RELATED
NETWORK_SCRIPTS_DIR = "/etc/sysconfig/network-scripts"
"""Path to Network Scripts directory"""
NETWORK_SCRIPTS_SLES_DIR = "/etc/sysconfig/network"
"""Path to Network Scripts directory on sles vm"""
NETWORK_PATH = "/etc/sysconfig/network"
"""Path to Network Scripts file"""
IPTABLES_V4_PATH = "/etc/sysconfig/iptables"
"""Path to IPV4 tables"""
IPTABLES_V6_PATH = "/etc/sysconfig/ip6tables"
"""Path to IPV6 tables"""
BONDING_MASTER_FILE = "/sys/class/net/bonding_masters"
"""Path to bonding masters file"""
BOND_FILES_DIR = "/proc/net/bonding"
""" Path to Bond Files directory"""
IPTABLES_PATH = "/sbin/iptables"
"""Path to iptables"""
IP6TABLES_PATH = "/sbin/ip6tables"
"""Path to ip6tables"""
IPTABLES_SLES_PATH = "/usr/sbin/iptables"
"""Path to iptables on sles vm"""
IP6TABLES_SLES_PATH = "/usr/sbin/ip6tables"
"""Path to ip6tables on sles vm"""
RESOLV_CFG_FILE = "/etc/resolv.conf"
"""The resolve conf file for resolving hostnames"""
DHCPD_CONF_DIR = "/etc/dhcp"
"""Path to DHCPD Configuration files"""
DHCPD_DHCPDARGS_FILE = "/etc/sysconfig"
"""Path to DHCPD dir which contains configuration file for listening device"""
IFDOWN_PATH = "/sbin/ifdown"
"""Path to bring a network interface down"""
IP_PATH = "/sbin/ip"
"""Path to system ip"""
NETSTAT_PATH = "/bin/netstat"
"""Path to netstat"""
ETHTOOL_PATH = "/sbin/ethtool"
"""Path to ethtool"""

#CLI RELATED
CMD_ERROR = -1
"""CLI command returns error"""

#PLAN STATUS VALUES
PLAN_COMPLETE = 0
"""Plan status - Plan Complete with all tasks in success state"""
PLAN_IN_PROGRESS = 1
"""Plan status - Plan has tasks in a running state"""
PLAN_NOT_RUNNING = 2
"""Plan status - Plan not running. All tasks in initial state"""
PLAN_FAILED = 3
"""Plan status - Plan has failed tasks"""
PLAN_STOPPED = 4
"""Plan status - Plan stopped. All run tasks report success but
now no tasks are in a running state and the plan has not finished"""
PLAN_STOPPING = 5
"""Plan status - Plan stopping"""
PLAN_INVALID = 6
"""Plan status - Plan is in an invalid state"""

#PLAN TASK STATUS VALUES
PLAN_TASKS_SUCCESS = 0
"""All selected plan tasks have succeeded."""
PLAN_TASKS_FAILED = 1
"""At least one selected plan task has failed."""
PLAN_TASKS_INITIAL = 2
"""All selected plan tasks are Initial."""
PLAN_TASKS_RUNNING = 3
"""All selected plan tasks are running."""
PLAN_TASKS_INCONSISTENT = 4
"""The selected plan tasks are in different states.
NB: If at least one task is reported as failed PLAN_TASKS_FAILED is returned"""
PLAN_TASKS_STOPPED = 5
"""If a task is in state stopped"""

#BOOT MGR RELATED
COBBLER_SNIPPETS_DIR = "/var/lib/cobbler/snippets"
"""Defines the File location where cobbler snippet files are created"""
COBBLER_EXP_VERSION = "2.4.2"
"""Defines the current expected cobbler version of the system"""


#YUM REPOSITORY LITP PACKAGES RELATED
PARENT_PKG_REPO_DIR = "/var/www/html/"
"""Defines the parent folder for RPM packages"""
LITP_PKG_REPO_DIR = "/var/www/html/litp"
"""Defines the location of LITP RPM packages"""
PP_REPO_DIR_NAME = "3pp_rhel7"
PP_PKG_REPO_DIR = "{0}{1}".format(PARENT_PKG_REPO_DIR, PP_REPO_DIR_NAME)
"""Defines the parent folder for 3PP packages"""
YUM_CONFIG_FILES_DIR = "/etc/yum.repos.d"
"""Folder with yum config files"""
ZYPPER_CONFIG_FILES_DIR = "/etc/zypp/repos.d"
"""Folder with zypper config files"""


#PUPPET RELATED
PUPPET_PATH = "/usr/bin/puppet"
"""Path to Puppet command"""
PUPPET_CONFIG_FILE = "/etc/puppet/puppet.conf"
"""Defines the location of the puppet config file"""
PUPPET_MANIFESTS_DIR = "/opt/ericsson/nms/litp/etc/puppet/manifests/plugins/"
"""Defines the location of the puppet manifests directory"""
PUPPETMASTER_CONFIG_FILE = "/etc/httpd/conf.d/puppetmaster.conf"
"""Puppet MASTER config file"""
PASSENGER_CONFIG_DIR = "/usr/share/puppet/rack/puppetmasterd"
"""Puppet passenger config directory"""
PASSENGER_SERVER_PORT = "8140"
"""PASSENGER SERVER PORT"""
EXPECTED_PASSENGER_VERSION = "4.0.37"
"""EXPECTED PASSENGER VERSION"""
PUPPET_FAILED_DIR =\
            "/opt/ericsson/nms/litp/etc/puppet/manifests/plugins.failed"
"""Folder where puppet manifests
    are copied to when a plan fails (LITPCDS-8260)"""
PUPPET_MODULES_DIR = "/opt/ericsson/nms/litp/etc/puppet/modules/"
"""PUPPET MODULES DIRECTORY"""
PUPPET_DEFAULT_MANIFESTS_DIR = "{0}litp/default_manifests".format(
            PUPPET_MODULES_DIR)
"""Folder where puppet default manifests are held"""
PUPPET_CATALOG_LOCK_FILE = "/var/run/puppet/agent_catalog_run.lock"
"""Lock file for agent_catalog_run. This only exists during a puppet run"""
PUPPETDB_MANIFESTS_DIR = "{0}puppetdb/manifests/".format(PUPPET_MODULES_DIR)
"""Defines the location of the puppetdb module manifests directory"""
LITP_PUPPET_CONF_FILE = "{0}etc/puppet/modules/litp/"\
    "manifests/litp_puppet_conf.pp".format(LITP_PATH)
"""LITP Puppet conf file location"""
PUPPET_AGENT_DISABLED_FILE = "/var/lib/puppet/state/agent_disabled.lock"
"""This file is created when puppet agent is disabled and removed when puppet
   agent is enabled"""
PUPPET_CERT_PATH = "/var/lib/puppet/ssl/certs/ca.pem"
"""Path to Puppet certificate"""
FACTER_PATH = "/usr/bin/facter"
"""Path to facter command"""


#MCOLLECTIVE RELATED
MCOLLECTIVE_CONFIG_FILE = "/etc/mcollective/server.cfg"
"""Defines the location of the MCOLLECTIVE config file"""
MCO_AGENT_PATH = "/opt/ericsson/nms/litp/etc/mcollective/mcollective/agent/"
"""PATH TO MCO AGENT"""
MCO_LOG_FILE = "/var/log/mcollective.log"
"""Path to the MCO logfile"""
EXPECTED_ERLANG_VERSION = "17.5"
"""Expected Erlang version"""
MCO_EXECUTABLE = "/usr/bin/mco"
"""Path to MCO executable"""

#USER RELATED
SU_PATH = "/bin/su"
"""Path to su"""
SSH_PATH = "/usr/bin/ssh"
"""Path to ssh command"""
SSH_CFG_FILE = '/etc/ssh/sshd_config'
"""File which contains SSH config values"""
AUTHTICATE_FILENAME = "~/.litprc"
"""Defines the location and name of the user authentication file (.litprc)"""
PASSWD_PATH = "/etc/passwd"
"""Path to passwd file"""
PASSWD_CMD_PATH = "/usr/bin/passwd"
"""Path to passwd command"""

#BASH_RELATED
SED_PATH = "/bin/sed"
"""Path to the sed executable"""
SED_RM_TRAILING_LEADING_WS = r"/bin/sed 's/^[ \t]*//;s/[ \t]*$//'"
"""Sed which removes all leading and trailing whitespace from a string."""
FIND_PATH = "/bin/find"
"""Path to find"""
STAT_PATH = "/usr/bin/stat"
"""Path to stat"""
GREP_PATH = "/bin/grep"
"""Path to grep"""
PS_PATH = "/bin/ps"
"""Path to ps"""
AWK_PATH = "/bin/awk"
"""Path to awk"""
TAIL_PATH = "/usr/bin/tail"
"""Path to tail command"""
DIFF_PATH = "/usr/bin/diff"
"""Path to diff utility"""
ECHO_PATH = "/bin/echo"
"""Path to echo command"""
LS_PATH = "/bin/ls"
"""Path to ls command"""
EGREP_PATH = "/bin/egrep"
"""Path to egrep"""
CHKCONFIG_PATH = "/sbin/chkconfig"
"""Path to chkconfig"""
MKDIR_PATH = "/bin/mkdir"
"""Path to /bin/mkdir"""
MV_PATH = "/bin/mv"
"""Path to /bin/mv"""
RM_PATH = "/bin/rm"
"""Path to /bin/rm"""
RM_RF_PATH = "/bin/rm -rf"
"""Path to /bin/rm -rf"""
DU_PATH = "/usr/bin/du"
"""path to du command"""
CAT_PATH = "/bin/cat"
"""Path to 'cat' command"""
MOUNT_PATH = "/bin/mount"
"""Path to 'mount' command"""
UMOUNT_PATH = "/bin/umount"
"""Path to 'umount' command"""
BASH_PATH = "/bin/bash"
"""Path to 'bash' command"""
GZIP_PATH = "/bin/gzip"
"""Path to 'gzip' command"""
DD_PATH = "/bin/dd"
"""Path to 'dd' command"""
CUT_PATH = "/bin/cut"
"""Path to cut command"""
SORT_PATH = "/bin/sort"
"""Path to sort command"""

#NTP RELATED
NTP_SERVER_IP = '10.44.86.30'
"""IP ADDRESS OF THE NTP SERVER FOR TESTING"""
NTP_SERVER_IP_SECONDARY = '10.44.86.14'
"""IP ADDRESS OF THE SEONDARY NTP SERVER FOR TESTING
NOTE THIS HAS NOT YET BEEN CONFIGURED, DO NOT USE UNTIL THEN."""
NTPD_CFG_FILE = "/etc/ntp.conf"
"""Path to ntpd Configuration file"""
NTPSTAT_PATH = "/usr/bin/ntpstat"
"""Path to ntpstat command"""

#SNAPSHOT RELATED
LITP_SNAPSHOT_PATH = '/dev/vg_root/'
"""Storage location of LITP snapshots"""
VXSNAP_PATH = "/opt/VRTS/bin/vxsnap"
"""Path to VXVM snapshot function"""
VXDG_PATH = "/opt/VRTS/bin/vxdg"
"""Path to VXDG snapshot function"""

#JSON RELATED
LITP_LIB_MODEL_PATH = "/var/lib/litp/core/model/"
"""Path to the LITP JSON files"""
LITP_LIB_SUCESS_MODEL_FILE =\
                "{0}LAST_SUCCESSFUL_PLAN_MODEL".format(LITP_LIB_MODEL_PATH)
"""Path to the LITP successful model backup file"""

#NAS RELATED
MOUNT_PATH_NAME1 = '/vx/ossrc1-file_system4'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME2 = '/vx/ossrc1-file_system5'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME3 = '/home/admin/nfs_share_dir/ro_unmanaged'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME4 = '/home/admin/nfs_share_dir/rw_unmanaged'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME5_IPV6 = '/home/admin/nfs_share_dir/nfs_filesystem_ipv6_only'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME6_IPV4 = '/home/admin/nfs_share_dir/nfs_filesystem_ipv4_only'
"""Preconfigured path uses when testing SFS"""
MOUNT_PATH_NAME7_DUAL = '/home/admin/nfs_share_dir/nfs_filesystem_dual_stack'
"""Preconfigured path uses when testing SFS"""

#SFS RELATED
SFS_MASTER_USR = "master"
"""Master username for SFS"""
SFS_MASTER_PW = "master"
"""Master password for SFS"""
SFS_SUPPORT_USR = "support"
"""Support username for SFS"""
SFS_SUPPORT_PW = "symantec"
"""Support password for SFS"""

#VCS RELATED
VCS_MAIN_CF_FILENAME = "/etc/VRTSvcs/conf/config/main.cf"
"""main.cf file location"""
LLT_PATH = '/etc/sysconfig/llt'
"""Path to llt"""
GAB_PATH = '/etc/sysconfig/gab'
"""Path to gab"""
LLTHOSTS_PATH = '/etc/llthosts'
"""Path to llthosts"""
LLTTAB_PATH = '/etc/llttab'
"""Path to llttab"""
GABTAB_PATH = '/etc/gabtab'
"""Path to gabtab"""
VCS_ENG_A_LOG_FILE = '/var/VRTSvcs/log/engine_A.log'
"""Path to the Engine A log"""

#LOG ROTATE RELATED
LOGROTATE_PATH = '/etc/logrotate.d/'
"""Path to logrotate related files"""
LOGROTATE_CFG_FILE = '/etc/logrotate.conf'
"""Path to logrotate config file"""
SBIN_LOGROTATE_PATH = "/usr/sbin/logrotate"
"""Path to /usr/sbin/logrotate"""

#NODE ATTRIBUTES
NODE_ATT_ROOTPW = 'rootpw'
"""Key to fetch root password using the get_node_att method"""
NODE_ATT_IPV4 = 'ipv4'
"""Key to fetch ipv4 using the get_node_att method"""
NODE_ATT_USR = 'username'
"""Key to fetch default (non-root) username using the get_node_att method"""
NODE_ATT_PASS = 'password'
"""Key to fetch default (non-root) user
    password using the get_node_att method"""
NODE_ATT_MAC = 'mac'
"""Key to fetch node mac address for the management network item"""
NODE_ATT_IPV6 = 'ipv6'
"""Key to fetch ipv6 address using the get_node_att method"""
NODE_ATT_HOST = 'hostname'
"""Key to fetch hostname using the get_node_att method"""
NODE_ATT_NODETYPE = 'nodetype'
"""Key to fetch node type using the get_node_att method"""

#CLOUD RELATED
IPMITOOL_FILE = '/opt/ericsson/nms/litp/bin/ipmitool.cloud'
IPMITOOL_HW_FILE = '/usr/bin/ipmitool'

#HTTP RELATED
HTTPD_CFG_FILE = "/etc/httpd/conf/httpd.conf"
"""Path to httpd Configuration file"""
HTTPD_PID_FILE = "/var/run/httpd/httpd.pid"
"""Path to httpd pid file"""

#LITP SERVICE RELATED
LITP_PID_FILE = '/var/run/litp_service.py.pid'
"""Path to litp service process id."""
SUBSYS_LOCK_FILE = '/var/lock/subsys/litpd'
"""Path to litpd subsys lock file."""
STARTUP_LOCK_FILE = '/var/run/litp_startup_lock'
"""Path to litp startup lock file."""
LITP_BIN_DIR = '/opt/ericsson/nms/litp/bin/'
"""DIR with LITP bin folder"""
LITPD_SERVICE_FILE = '/usr/local/bin/litpd.sh'
"""Path to LITPD service file"""
LITPD_CONF_FILE = "/etc/litpd.conf"
"""Path to LITPD configuration file."""
LITPD_ACCESS_LOG = "/var/log/litp/litpd_access.log"
"""PATH to the LITPD access log file."""
LITPD_ERROR_LOG = "/var/log/litp/litpd_error.log"
"""PATH to the LITPD error log file."""

#CONSTANTS RELATED TO TEST ENV
ENV_CLOUD = 0
"""Used when calling verify_expected_env to check test is on cloud"""
ENV_PHYSICAL = 1
"""Used when calling verify_expected_env to check test is on physical"""
ENV_OTHER = 2
"""Used when calling verify_expected_env to check test is on other"""

#NEXUS LINK
NEXUS_LINK = "https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus"
"""Used in get_item_from_nexus method in generic utils"""

#METRICS RELATED
METRICS_LOG = "/var/log/litp/metrics.log"
"""Logfile where LITP writes metrics"""

#LITP BACKUP RELATED
LITP_BACKUP_SCRIPT = "/opt/ericsson/nms/litp/bin/litp_state_backup.sh"
"""Location of the LITP backup script"""
LITP_RESTORE_SCRIPT = "/opt/ericsson/nms/litp/bin/litp_state_restore.sh"
"""Location of the LITP restore script"""

#CELERY RELATED
CELERY_PATH = "/usr/bin/celery"
"""Path to the celery executable"""
CELERYD_PATH = "/etc/default/celeryd"
"""Path to celeryd"""
CELERYBEAT_FILE_PATH = "/etc/default/celerybeat"
"""Path to celerybeat"""

#POSTGRES RELATED
PSQL_PATH = "/usr/bin/psql"
"""Path to the psql executable"""
POSTGRESQL_CONF = "/var/lib/pgsql/data/postgresql.conf"
"""The path to the postgresql config file"""
PSQL_SERVICE_NAME = "rh-postgresql96-postgresql"
"""PostgreSQL Service Name"""
PSQL_9_6_DATA_DIR = "/var/opt/rh/rh-postgresql96/lib/pgsql/data/"
"""PostgreSQL 9.6 data directory"""
PSQL_9_6_CONF_FILE = "{0}postgresql.conf".format(PSQL_9_6_DATA_DIR)
"""Config file path for PostgreSQL 9.6"""
POSTGRES_INITIAL_PASSWORD = "AZP6E2hsxf12TdsMKX"
"""Defines the initial postgres superuser password"""
POSTGRES_PASSWORD_SCRIPT = "/usr/bin/litpmsdbpwd"
"""Path to the litpmsdbpwd script"""

#REDFISH_RELATED
REDFISH_ROOT = "/redfish/v1"
"""Root URL for executing requests against Redfish API"""
REDFISH_ACTIONS = "/redfish/v1/Systems/1/Actions/"
"""URL for executing actions requests against Redfish API"""
REDFISH_RESET = "ComputerSystem.Reset"
"""Redfish action to reset node (power On/Off)"""

#ILO_RELATED
ILO_USERNAME = "root"
"""Username used for ILO authentication"""
ILO_PASSWORD = "Amm30n!!"
"""Password used for ILO authentication"""
