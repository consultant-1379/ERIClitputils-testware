"""
LITP Generic Test util

Note: :synopsis for this file is located in source_code_docs.rst
"""

import unittest
from litp_generic_cluster import GenericCluster
from litp_generic_node import GenericNode
from litp_generic_utils import GenericUtils
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
from json_utils import JSONUtils
from vcs_utils import VCSUtils
from storage_utils import StorageUtils
from networking_utils import NetworkingUtils
from nose.plugins.attrib import attr  # pylint: disable=unused-import
from os import environ
from collections import defaultdict  # pylint: disable=unused-import
import redfishtool
import redfish

import math
import os
import time
import test_constants
import re
import netaddr
import json

#############################################
# THIS IS A DUMMY DECORATOR NEEDED FOR TEST #
# CASES FOR TMS (TEST MANAGEMENT SYSTEM).   #
# THIS SHOULD NOT BE CALLED DIRECTLY OR     #
# USED OTHER THAN AT THE BEGINNING OF A     #
# TEST CASE WITH @tmsid('<id>')             #
#############################################


def tmsid(*args):
    """ Dummy argument handler method """
    #uses args to pass pylint
    for arg in args:
        print arg

    def myval(obd):
        """Dummy decorator"""
        return obd
    return myval


class GenericTest(unittest.TestCase):

    """Extension of class TestCase from Python unittest module.
       Intention is to have here methods:
          - Shared and generic among all tests
          - Methods to run any commands
          - API to access and process the results
          - Logging


    .. note::
       For your story you inherit directly from here.
    """

    # Group 1 - Setup and teardown
    def setUp(self):
        """
        Executed at the start of each test.
        """
        self.stopped_service_list = list()

        # Set to False if you don't want to unlock the nodes on a failed plan
        # the failed plan.
        self.unlock_on_cleanup = True
        self.unlock_required = False

        self.nics_to_delete = list()

        # Create required utility objects
        self.vcs = VCSUtils()
        self.cluster = GenericCluster()
        self.cli = CLIUtils()
        self.rhc = RHCmdUtils()
        self.g_util = GenericUtils()
        self.json_u = JSONUtils()
        self.net = NetworkingUtils()
        self.sto = StorageUtils()
        # Log the start of the test
        self.log('info', 'START ' + self.id())
        print '\n'

        # Create a global variable holding all node objects
        # in a list
        self.nodes = self.cluster.nodes

        ########################
        # RELATED TO AUTO CLEANUP
        # List to hold all commands executed successfully
        self.successful_commands = list()
        self.final_cleanup_cmds = list()

        #List to hold inherit commands, we need to run these first in cleanup.
        self.inherit_commands = list()
        # Dictionary keys used to construct a dict representing the
        # exact command run
        self.cleanup_key_node = "NODE"
        self.cleanup_key_cmd = "CMD"
        self.cleanup_key_usr = "USR"
        self.cleanup_key_pw = "PW"
        self.cleanup_key_ipv4 = "IPV4"
        self.cleanup_key_su = "SU"
        self.cleanup_key_nic = "NIC"
        self.cleanup_key_isbond = "BOND"
        self.cleanup_key_isbridge = "BRIDGE"
        self.cleanup_key_fluship = "FLUSH"
        #If we create users we want to delete them afterwards
        self.users_to_delete = list()
        self.files_to_delete = list()
        self.del_file_list = list()
        self.files_to_check = list()
        self.rpms_to_delete = dict()
        self.cleanup_key_filepath = "PATH"

        ###########################
        ##Timeout of cleanup_plan in mins
        self.cleanup_plan_timeout = 20

        #########################
        #Related to network
        #These keys are used to extract data from the dict
        #returned with the get_node_net_from_tree method
        self.hostname_key = 'hostname'
        self.ips_key = 'ips'
        self.interface_mac_key = 'in_mac'

        #Key used to check for sles
        self.sles_vm = "sles"

        #Which ids correspond to a control node
        self.control_node_ids = [1, 2]

        ##Related to backup of files
        self.backup_filelist = list()
        self.backup_filelist_after_plan = list()
        self.backup_dir_num = 1
        self.backup_dir_name = "backup_"

        ##Related to backup_props
        self.path_restore_list = list()

        ##
        self.cluster_created = False
        self.iso_import_command_run = False
        ##SFS SHARE RELATED
        self.sfs_path_key = "PATH"
        self.sfs_ip_key = "IP"
        self.sfs_perm_key = "PERM"
        ##SFS FS RELATED
        self.sfs_fs_key = "FS"
        self.sfs_fs_status_key = "STATUS"
        self.sfs_fs_size_key = "SIZE"
        self.sfs_fs_layout_key = "LAYOUT"
        self.sfs_fs_mirror_key = "MIRROR"
        self.sfs_fs_column_key = "COLUMN"
        self.sfs_fs_use_key = "USE"
        self.sfs_fs_used_key = "USED"
        self.sfs_fs_shared_key = "SHARED"
        self.sfs_fs_ftpshared_key = "FTPSHARED"
        self.sfs_fs_cifsshared_key = "CIFSSHARED"
        self.sfs_fs_sectier_key = "SECTIER"
        self.sfs_fs_pool_key = "POOL"
        self.sfs_snapshot_name_key = "NAME"
        self.sfs_snapshot_type_key = "TYPE"
        self.sfs_snapshot_fs_key = "FS"
        self.sfs_snapshot_date_key = "DATE"
        self.sfs_snapshot_time_key = "TIME"
        self.sfs_cache_name_key = "NAME"
        self.sfs_cache_total_key = "TOTAL"
        self.sfs_cache_used_key = "USED"
        self.sfs_cache_percent_key = "PERCENT"
        self.sfs_cache_available_key = "AVAILABLE"
        self.sfs_cache_percent_avail_key = "PERCENT_AVAIL"
        self.sfs_cache_sdcnt_key = "SDCNT"

        # Possible NAS server types and banner locations
        self.nas_server_banners = ['/opt/SYMCsnas/conf/banner',
                                '/opt/VRTSnasgw/conf/banner']
        self.sfs_full_name = 'Symantec FileStore'
        self.va_full_name = 'Veritas'
        self.nas_type_list = [self.sfs_full_name, self.va_full_name]

        # This is where the new style taf file format is found
        if "LITP_CONN_DATA_FILE" in environ:
            self.con_data_path = environ['LITP_CONN_DATA_FILE']
        else:
            self.con_data_path = '/opt/ericsson/SIT/connection_data_files/'

        print "NOTE: Using connection data in this path: {0}"\
            .format(self.con_data_path)
        # Model export

        if os.getenv("EXPORT_MODEL", "false") == "true":
            print "Time before export: " + time.asctime()
            xml_filename_before = "/tmp/b_" + self.id() + ".xml"
            self.execute_cli_export_cmd(self.get_management_node_filename(),
                                        "/",
                                        xml_filename_before,
                                        add_to_cleanup=False)
            print "Time after export: " + time.asctime()

    def tearDown(self):
        """Executed by each test by default.
        """
        print '\n\n\n'
        print "###################################################\n"
        self.log('info', 'END OF TEST, START CLEANUP: ' + self.id())
        print '\n'
        self.run_cleanup()
        print '\n'
        self.log('info', 'END ' + self.id())
        self.disconnect_all_nodes()
        #print "###END MODEL SNAPSHOT"
        #show_cmd = self.cli.get_show_cmd("/", "-r")
        #self.run_command(self.get_management_node_filename(), show_cmd)
        #print "###END MODEL SNAPSHOT"

        #model export
        if os.getenv("EXPORT_MODEL", "false") == "true":
            print "Time before export: " + time.asctime()
            xml_filename_after = "/tmp/a_" + self.id() + ".xml"
            self.execute_cli_export_cmd(self.get_management_node_filename(),
                                        "/",
                                        xml_filename_after,
                                        add_to_cleanup=False)
            print "Time after export: " + time.asctime()

    def disconnect_all_nodes(self):
        """
        Disconnects all nodes that may have been connected during the test.

        """
        ##Loop through all nodes and call the disconnect method.
        for node in self.nodes:
            node.disconnect()

    def run_cleanup(self):
        """Looks through all commands that ran successfully in this test
        and runs the automatic cleanup, if available.

        Actions:

        1. Remove any children of other cmds in cmd lists.

        2. Restore any changed properties to their backed up value.

        3. Stop any currently running plans.

        4. Remove any created paths in model.

        5. Delete any users added.

        6. Delete files created during test.

        7. Restore any backed up files.

        8. Run any plans needed to apply removed paths.

        9. Cleanup snapshots.

        10. Wait for puppet cycle (if applicable).

        11. Restore any post plan backed up files.

        12. Delete any required nic files.

        13. Delete any rpms installed

        """
        plan_run_nodels = []
        snapshot_run_nodels = []

        self.start_stopped_services(False)
        # 1. Remove any children of other cmds to make cleanup more efficient
        self.successful_commands = \
            self.__remove_children_from_ls(self.successful_commands)

        self.inherit_commands = \
            self.__remove_children_from_ls(self.inherit_commands)

        # 2. Restore any changed properties to their backup value
        self.restore_props()

        #3. Stop any running plans
        plan_run_nodels = self.__stop_running_plans()

        #4. Remove any created paths
        ms_node, snapshot_run_nodels, tagged_snapshots \
                              = self.__run_cleanup_cli_remove_cmds()

        #5. Delete any users added
        for user in self.users_to_delete:
            self.delete_posix_usr(user['node'], user['usr'])

        #6. Delete files created during test
        for file_item in self.files_to_delete:
            self.remove_item(file_item[self.cleanup_key_node],
                             file_item[self.cleanup_key_filepath],
                             file_item[self.cleanup_key_usr],
                             file_item[self.cleanup_key_pw],
                             file_item[self.cleanup_key_su])

        #7. Restore any backed up files
        self.restore_backup_files()

        #8. Run any plans needed
        self.__run_cleanup_plans(plan_run_nodels)

        #9. Cleanup snapshots
        self.__cleanup_snapshots(snapshot_run_nodels, tagged_snapshots)

        for file_item in self.del_file_list:
            if not file_item["PUPPET"]:
                self.run_command(file_item["NODE"],
                                 "/bin/rm -rf {0}"\
                                     .format(file_item["PATH"]),
                                 su_root=True)

                self.del_file_list.remove(file_item)

        #10. Wait for current puppet cycle to finish, then sleep while the
        #new one starts.
        #Needed if doing anything file related which occurs after a plan run
        if self.backup_filelist_after_plan != [] or \
                self.nics_to_delete != [] or \
                self.del_file_list != []:
            if not ms_node:
                ms_node = self.get_management_node_filename()
            self.log("info", "Sleeping for puppet interval")
            self.wait_for_puppet_idle(ms_node)

        #11. Restore any backed up files that were
        # specified for restoreation after running cleanup plan.
        for backup in self.backup_filelist_after_plan:
            self.log("info", "Restoring file backup")
            if backup["DEL"]:
                self.remove_item(backup["NODE"],
                                 backup["TARGET_PATH"],
                                 su_root=True)
            self.mv_file_on_node(backup["NODE"],
                                 backup["SOURCE_PATH"],
                                 backup["TARGET_PATH"],
                                 su_root=True,
                                 add_to_cleanup=False)

        #12. delete nic related files
        self.__cleanup_nic_files()

        for file_item in self.del_file_list:
            self.run_command(file_item["NODE"],
                             "/bin/rm -rf {0}"\
                                 .format(file_item["PATH"]),
                                         su_root=True)

        files_not_deleted = []
        for file_item in self.files_to_check:
            file_exists = self.remote_path_exists(file_item["NODE"],
                                                  file_item["PATH"],
                                                  su_root=True)

            if file_exists:
                files_not_deleted.append(\
                    "File {0} on node {1} has not been deleted."\
                        .format(file_item["PATH"],
                                file_item["NODE"]))

        if self.iso_import_command_run:
            ms_node = self.get_management_node_filename()
            cmd = "/usr/bin/mco puppet status"
            self.run_command(ms_node, cmd, su_root=True)
            cmd = "/usr/bin/mco puppet enable"
            self.run_command(ms_node, cmd, su_root=True)

        self.assertEqual([], files_not_deleted)

        for cmd in self.final_cleanup_cmds:
            self.run_commands(cmd['NODE'], cmd['CMDS'], su_root=cmd['SU'])

        # 13. Delete any rpms installed
        for node in self.rpms_to_delete:
            if self.get_node_att(node, 'nodetype') == 'management':
                self.log('info', 'Stopping puppet for RPM upgrade')
                self.stop_service(node, 'puppet')

            self.run_command(node,
                             self.rhc.get_yum_remove_cmd(
                                 self.rpms_to_delete[node]),
                             add_to_cleanup=False,
                             su_root=True
                             )

            # restart the litpd service. Only on MS.
            if self.get_node_att(node, 'nodetype') == 'management':
                self.start_service(node, 'puppet')
                self.restart_litpd_service(node)

        #13. Set debug to on in case test has accidently turned it off.
        #Removed - Risk deemed low as tests are no not all run in
        #but rather mostly on KGBs.
        #if ms_node:
            #turn_on_debug_cmd = self.cli.get_litp_debug_cmd()
            #self.run_command(ms_node,
                             #turn_on_debug_cmd)

    def run_commands_after_cleanup(self, node, cmd_list, su_root=False):
        """
        Runs the passed list of commands on the selected node at the end
        of the cleanup plan.

        Args:

          node (str): The reference to the node where these commands should
          be run.

          cmd_list (list): The list of commands to run.

          su_root (bool): Set to True to run cleanup commands as root.
        """
        cmd_items = dict()

        cmd_items['NODE'] = node
        cmd_items['CMDS'] = cmd_list
        cmd_items['SU'] = su_root

        self.final_cleanup_cmds.append(cmd_items)

    def restore_backup_files(self, node=None, filepath=None):
        """
        Restores files backed up using the backup file utility.

        By default, restores all backed up files but can be set to backup
        only on the specified node/filepath.

        Kwargs:
           node (str): If set, will only back up files on the selected node.

           filepath (str): If set, will only back up files on the selected path

        Returns:
           bool. True if at least one file was restored or False if no files
           could be found matching arguments.
        """
        restored = False

        for backup in list(self.backup_filelist):
            node_found = False
            path_found = False

            if node:
                if backup["NODE"] == node:
                    node_found = True
            else:
                node_found = True

            if filepath:
                if backup["TARGET_PATH"] == filepath:
                    path_found = True
            else:
                path_found = True

            if node_found and path_found:
                if backup["DEL"]:
                    self.remove_item(backup["NODE"],
                                     backup["TARGET_PATH"],
                                     su_root=True)

                self.mv_file_on_node(backup["NODE"],
                                     backup["SOURCE_PATH"],
                                     backup["TARGET_PATH"],
                                     su_root=True,
                                     add_to_cleanup=False)

                self.backup_filelist.remove(backup)
                restored = True

        return restored

    def start_stopped_services(self, assert_success=True):
        """
        Will restart all services that were stopped
        during the test with the stop_service method.

        Kwargs:
           assert_success: By default, will assert each stopped service starts
           again successfully.
        """
        for service in list(self.stopped_service_list):
            self.get_service_status(service['NODE'], service['NAME'],
                                    False)
            self.start_service(service['NODE'], service['NAME'],
                               assert_success)

            if 'litpd' in service['NAME']:
                self.turn_on_litp_debug(service['NODE'], False)

    def __cleanup_nic_files(self):
        """
        Deletes ifconfig files on the node that were added to a delete list
        during a test by calling the add_nic_to_cleanup method.
        """
        for item in self.nics_to_delete:
            ##IFDOWN NIC
            cmd = "/sbin/ifdown {0}".format(item[self.cleanup_key_nic])
            self.run_command(item[self.cleanup_key_node], cmd, su_root=True)

            ##DELETE NIC IFCONFIG FILE
            self.remove_item(item[self.cleanup_key_node],
                             item[self.cleanup_key_filepath],
                             item[self.cleanup_key_usr],
                             item[self.cleanup_key_pw],
                             item[self.cleanup_key_su])

            ##DELETE NIC IFCONFIG FILE
            if item[self.cleanup_key_isbond]:
                cmd = "/bin/echo -{0} > /sys/class/net/bonding_masters".\
                    format(item[self.cleanup_key_nic])
                self.run_command(item[self.cleanup_key_node], cmd,
                                 su_root=True)

            ##IF bridge special case
            if item[self.cleanup_key_isbridge]:
                cmd = "/usr/sbin/brctl delbr {0}"\
                    .format(item[self.cleanup_key_nic])
                self.run_command(item[self.cleanup_key_node], cmd,
                                 su_root=True)

            if item[self.cleanup_key_fluship]:
                cmd = \
                    "/sbin/ip addr flush dev {0}"\
                    .format(item[self.cleanup_key_nic])

                self.run_command(item[self.cleanup_key_node], cmd,
                                 su_root=True)

    def __stop_running_plans(self):
        """
        Find all nodes where a plan was run and call stop_plan
        of the plan is still in a running state.

        Add to a list all nodes where a plan was run.

        Returns:
        list. The list of all nodes where a plan was run.
        """
        plan_run_nodels = list()

        for cmd in self.successful_commands:
            #If a plan has been run on the node we need to apply changes
            if self.cli.is_run_plan_cmd(cmd[self.cleanup_key_cmd]) or \
                    self.cli.is_snapshot_cmd(cmd[self.cleanup_key_cmd]):

                if not cmd[self.cleanup_key_node] in plan_run_nodels:
                    plan_run_nodels.append(cmd[self.cleanup_key_node])
                    self.stop_plan_if_running(cmd[self.cleanup_key_node])

        return plan_run_nodels

    def set_cleanup_plan_timeout(self, timeout_mins):
        """
        Overwrite the default timeout for the cleanup plan to run.

        Args:
           timeout_mins (str): The length of time in minutes to allow the
           cleanup plan to run.
        """
        self.cleanup_plan_timeout = timeout_mins

    def __run_cleanup_plans(self, plan_run_nodels):
        """
        Looks through the list of passed MSs and performs the actions to
        create, run and then remove plans on each of them.

        Args:
        plan_run_nodels (list): List of all nodes for which a
                                run_plan command has been called.
        """
        #Remove any duplicate values in list of MSs to run plans
        run_plan_ls = list(set(plan_run_nodels))

        for node in run_plan_ls:
            _, _, re_c = self.run_command(node,
                                          self.cli.get_create_plan_cmd())

            #If create_plan successful run the plan
            if re_c == 0:
                _, _, re_c = self.run_command(node,
                                                   self.cli.get_run_plan_cmd())
                plan_success = \
                    self.wait_for_plan_state(node,
                                             test_constants.PLAN_COMPLETE,
                                             self.cleanup_plan_timeout)

                self.assertTrue(plan_success, "The cleanup plan has failed")

                if not plan_success:
                    self.log("error", "Cleanup plan failed")

            self.run_command(node, self.cli.get_remove_plan_cmd())

    def __cleanup_snapshots(self, snapshot_run_nodels, tagged_snapshots):
        """
        Looks through the list of passed MSs in snapshot_run_nodels and
        performs the actions to remove and then create new deployment
        snapshots.

        Looks through the list tagged_snapshots of dict and executes the
        appropriate commands to cleanup tagged snapshots on each MS.

        Args:
            snapshot_run_nodels (list): List of all nodes for which a
            deployment snapshot related command has been called.

            tagged_snapshots (dict): Dict containing list of node(s) and the
            tagged snapshot command(s) executed towards that node.
        """
         #Remove any duplicate values in list of MSs to run plans
        snapshot_ls = list(set(snapshot_run_nodels))

        self.log("info", snapshot_ls)
        self.log("info", tagged_snapshots)

        # First cleanup named/tagged snapshots.
        for snap in tagged_snapshots:
            cmd = snap[self.cleanup_key_cmd]
            node = snap[self.cleanup_key_node]
            args = '-n ' + self.cli.get_tagged_snapshot_name(cmd)

            if 'create' in cmd:
                ## Remove snapshot
                _, _, re_c = self.run_command(node,
                                self.cli.get_remove_snapshot_cmd(args=args))

                if re_c == 0:
                    plan_success = self.wait_for_plan_state(node,
                                             test_constants.PLAN_COMPLETE)

                    if not plan_success:
                        self.log("error", "Cleanup tagged snapshot failed")

        # Secondly cleanup Deployment snapshots.
        for node in snapshot_ls:
            ##Remove existing snapshot
            _, _, re_c = self.run_command(node,
                                          self.cli.get_remove_snapshot_cmd())

            if re_c == 0:
                plan_success = \
                    self.wait_for_plan_state(node,
                                             test_constants.PLAN_COMPLETE)

            #Create new snapshot
            _, _, re_c = self.run_command(node,
                                          self.cli.get_create_snapshot_cmd())

            if re_c == 0:
                plan_success = \
                    self.wait_for_plan_state(node,
                                             test_constants.PLAN_COMPLETE)

                if not plan_success:
                    self.log("error", "Cleanup snapshot failed")

            #Remove any left over plans
            self.run_command(node, self.cli.get_remove_plan_cmd())

    def __run_cleanup_cli_remove_cmds(self):
        """
        Performs a remove command for any item created in the model
        during the test.

        Commands that are inherited are removed first to avoid
        validation errors.

        N.B.: All cleanup functions written to support multiply MS deployment.

        Returns:
            str. Name of ms_node that commands were run on.
            list. List of nodes where snapshot commands were run.
            dict. Node(s) where tagged snapshot commands were run and
                  list of those commands.
        """
        # List keeps count of nodes where a deployment snapshot command was
        # run.
        snapshot_run_nodels = list()
        # Keep list of dict to track where/which Tagged snapshot command used
        tagged_snapshots = list()
        ms_node = None

        #4. Remove any created inherited paths. These have to be removed before
        #other successful commands or there may be validation errors
        for cmd in list(self.inherit_commands):
            self.run_commands(
                cmd[self.cleanup_key_node],
                self.cli.get_cleanup_cmds(cmd[self.cleanup_key_cmd]),
                cmd[self.cleanup_key_usr],
                cmd[self.cleanup_key_pw],
                cmd[self.cleanup_key_ipv4],
                su_root=cmd[self.cleanup_key_su],
                add_to_cleanup=False)

            #if not set set the ms_node to the correct command being cleaned up
            ms_node = cmd[self.cleanup_key_node]

        # 5. Run the cleanup for all commands left in the list
        for cmd in list(self.successful_commands):

            #Ignore run_command, this will be cleaned up later
            if self.cli.is_run_plan_cmd(cmd[self.cleanup_key_cmd]):
                continue

            #If snapshot related command add to list for cleanup later
            if self.cli.is_snapshot_cmd(cmd[self.cleanup_key_cmd]):
                command = cmd[self.cleanup_key_cmd]
                if self.cli.is_tagged_snapshot_cmd(command) and \
                    self.cli.get_tagged_snapshot_name(command) != \
                                                               'snapshot':
                    # Tagged snapshot excluding those with name 'snapshot'
                    tagged_snapshot_cmd = dict()
                    node = cmd[self.cleanup_key_node]

                    tagged_snapshot_cmd = {self.cleanup_key_node: node,
                                           self.cleanup_key_cmd: command}

                    tagged_snapshots.append(tagged_snapshot_cmd)
                    continue
                else:
                    # Deployment snapshot
                    if not cmd[self.cleanup_key_node] in snapshot_run_nodels:
                        snapshot_run_nodels.append(cmd[self.cleanup_key_node])
                    continue

            #Perform the remove command
            self.run_commands(
                cmd[self.cleanup_key_node],
                self.cli.get_cleanup_cmds(cmd[self.cleanup_key_cmd]),
                cmd[self.cleanup_key_usr],
                cmd[self.cleanup_key_pw],
                cmd[self.cleanup_key_ipv4],
                su_root=cmd[self.cleanup_key_su],
                add_to_cleanup=False)

            #if not set set the ms_node to the correct command being cleaned up
            ms_node = cmd[self.cleanup_key_node]

        return ms_node, snapshot_run_nodels, tagged_snapshots

    def restore_props(self, filter_path=None):
        """
        Restores all paths that were backed up to their original values.

        For each backed up path, the following is done:

        1. Get current list of properties and their value.
        2. Compare to original backed up values to find out:
           a. Property values that have been changed.
           b. Property values that have been added to the item.
           c. Property values that have been deleted from the item.
        3. Run commands to delete added props and restore changed props to
           original value.
        4. Run commands to add back deleted properties.

        Args:
           filter_path (str): If set, will only restore props on the path
           passed.
        """
        changed_props = list()
        delete_props = list()

        for path in list(self.path_restore_list):
            if filter_path:
                if filter_path != path["PATH"]:
                    continue

            new_props = self.get_props_from_url(path["MS_NODE"],
                                                path["PATH"])

            changed_props, delete_props = self.get_changed_props(new_props,
                                                                 path["PROPS"])

            deleted_props = self.get_deleted_props(new_props,
                                                   path["PROPS"])
            ##IF A NEW PROP HAS BEEN ADDED
            for prop in delete_props:
                delete_prop_cmd = self.cli.get_update_cmd(path["PATH"],
                                                          prop,
                                                          action_delete=True)

                self.run_command(path["MS_NODE"], delete_prop_cmd)

            update_props = ""
            update_inherit_props = ""
            ###IF A PROP HAS CHANGED
            for prop in changed_props:
                if self.is_inherited_prop(path["PROPS"][prop]):
                    update_inherit_props += '{0} '\
                        .format(prop)
                else:
                    update_props += "{0}={1} "\
                        .format(prop,
                                self.excl_inherit_symbol(path["PROPS"][prop]))

            ##IF A PROP HAS BEEN DELETED
            for prop in deleted_props:
                if self.is_inherited_prop(path["PROPS"][prop]):
                    self.log("error",
                        "Deleted an inherited property. Not supported in LITP")
                else:
                    update_props += "{0}={1} "\
                        .format(prop,
                              self.excl_inherit_symbol(path["PROPS"][prop]))

            if update_props != "":
                update_cmd = self.cli.get_update_cmd(path["PATH"],
                                                     update_props)

                self.run_command(path["MS_NODE"], update_cmd)

            if update_inherit_props != "":
                update_cmd = self.cli.get_update_cmd(path["PATH"],
                                                     update_inherit_props,
                                                     action_delete=True)

                self.run_command(path["MS_NODE"], update_cmd)

            self.path_restore_list.remove(path)

    def is_all_applied(self, ms_node, ignored_paths=None):
        """
        Looks through the tree and returns True if all items are
        in Applied State or False otherwise.

        If a state of not Applied is found, will perform a show of the entire
        tree for debugging purposes and then show the list of all URLs in an
        unexpected state.

        Args:
            ms_node (str): The MS node to check.

            ignored_paths (list): List of paths in the LITP model that can
            be ignored when checking for applied state.

        Returns:
            bool. True if all items with state field are in Applied state or
            False otherwise.

        """
        all_applied = True

        get_state_cmd = self.cli.get_grep_all_state_cmd()

        std_out, std_err, returnc = self.run_command(ms_node,
                                                     get_state_cmd)
        #If error running cmd return False
        if returnc != 0 or std_err != []:
            return False

        #Check if any state is not applied
        for line in std_out:
            if "Applied" not in line:
                self.log("error",
                         "Items not in Applied state found performing " +\
                             "show of tree")
                all_applied = False
                break

        #if state found that is not applied run cmd to find these paths
        if not all_applied:

            get_state_cmd = \
                    self.cli.get_grep_unexpected_state_cmd('/', 'Applied')

            std_out, std_err, returnc = self.run_command(ms_node,
                                                         get_state_cmd)

            #if there are some paths that are safe to ignore check do
            #check to see if it is these paths
            if ignored_paths:
                for line in std_out:

                    if "/" not in line:
                        continue

                    allowed_path = False

                    for path in ignored_paths:
                        if path in line:
                            self.log("info",
                                     "Path {0} in allowed list. Ignoring."\
                                 .format(line))
                            allowed_path = True

                    if allowed_path:
                        continue

                    self.log("error", "Path is not in applied state: {0}"\
                                 .format(line))
                    return False
            else:
                return False

        return True

    def is_expected_state(self, ms_node, path, state, excl_child_paths=None):
        """
        Checks if all items in the LITP tree under the specified path
        are in the specified state.

        Args:
           ms_node (str): The MS node to check.

           path (str): The path to look under.

           state (str): The state to expect (e.g. Applied or Initial).

        Kwargs:
           excl_child_paths (list): A list of child paths immediately under the
           path provided to ignore when checking state.

        Returns:
           bool. True if all paths are of that expected state or False
           otherwise.
        """
        if excl_child_paths == None:
            excl_child_paths = []

        if excl_child_paths != []:

            all_paths, _, _ = \
                self.execute_cli_show_cmd(ms_node, path, "-l")

            for path in all_paths:
                ##ignore /litp as it has no state values under it
                if path in excl_child_paths or path == '/' or path == '/litp':
                    continue

                get_state_cmd = self.cli.get_grep_all_state_cmd(path)

                std_out, std_err, returnc = self.run_command(ms_node,
                                                     get_state_cmd)

                if returnc != 0 or std_err != []:
                    return False

                for line in std_out:
                    if state not in line:
                        self.log("error",
                                 "Items not in expected state performing " +\
                                     "show of tree")
                        self.execute_cli_show_cmd(ms_node, path, "-r")
                        get_state_cmd = \
                            self.cli.get_grep_unexpected_state_cmd(path, state)

                        std_out, std_err, returnc = self.run_command(ms_node,
                                                     get_state_cmd)
                        return False

            return True

        else:

            get_state_cmd = self.cli.get_grep_all_state_cmd(path)

            std_out, std_err, returnc = self.run_command(ms_node,
                                                     get_state_cmd)

            if returnc != 0 or std_err != []:
                return False

            for line in std_out:
                if state not in line:
                    self.log("error",
                             "Items not in expected state performing " +\
                                 "show of tree")
                    self.execute_cli_show_cmd(ms_node, path, "-r")
                    get_state_cmd = \
                        self.cli.get_grep_unexpected_state_cmd(path, state)

                    std_out, std_err, returnc = self.run_command(ms_node,
                                                     get_state_cmd)
                    return False

            return True

    @staticmethod
    def is_inherited_prop(prop_value):
        """
        Returns True if the property value passed is inherited.
        It does this by checking for the inherit symbol.

        Args:
           prop_value (str): The value of the property fetched from the model.

        Returns:
           bool. True if the inherit symbol is found on a property.
        """
        if "[*]" in prop_value:
            return True

        return False

    def get_changed_props(self, new_props, old_props):
        """
        Returns two lists - the first containing all properties that have been
        changed. The second list contains the properties in the new_props dict
        which are not in the old_props dict. In other words, properties which
        will need to be deleted during cleanup.

        Args:
           new_props (dict) : A dictionary of property values.

           old_props (dict):  A dictionary of property values.

        Returns:
            list, list. The first list corresponds to all value names which
            have changed in the new_props compared to the old. The second
            corresponds to all properties which exist in new dict but not in
            old dict.
        """
        changed_props = list()
        props_to_delete = list()

        for prop in new_props.keys():
            if prop in old_props.keys():
                if self.excl_inherit_symbol(new_props[prop]) !=\
                        self.excl_inherit_symbol(old_props[prop]):
                    changed_props.append(prop)
            else:
                props_to_delete.append(prop)

        return changed_props, props_to_delete

    @staticmethod
    def get_deleted_props(new_props, old_props):
        """
        Returns a list containing all properties that have been deleted
        in the new dict compared to the old.

        Args:
           new_props (dict) : A dictionary of property values.

           old_props (dict):  A dictionary of property values.

        Returns:
            list. List of all props that have been deleted.
        """
        deleted_props = list()

        for prop in old_props.keys():
            if prop not in new_props.keys():
                deleted_props.append(prop)

        return deleted_props

    @staticmethod
    def excl_inherit_symbol(property_value):
        """
        Deletes the symbol used to specify that a property is inherited.

        Args:
           property_value (str): The property value.

        Returns:
           str. The property value with the inherit symbol removed.
        """
        return property_value.replace(" [*]", "")

    def stop_plan_if_running(self, node):
        """
        Checks if a plan is running and, if so, attempts to stop it.
        Will wait the default timeout period for the plan to stop.

        Args:
         node (str) : The node to stop the plan on.

        Returns:
           bool. True if the plan was stopped or is not in progress.
           False if the Plan could not be stopped.
        """
        plan_state = self.get_current_plan_state(node, full_show=True)

        if plan_state == test_constants.PLAN_IN_PROGRESS:

            stop_plan_cmd = self.cli.get_stop_plan_cmd()

            _, stderr, rc = self.run_command(
                node, stop_plan_cmd
            )

            if rc != 0:
                self.log("error", "Unable to stop plan {0}:".format(stderr))
                return False
            else:
                return self.wait_for_plan_state(node,
                                                test_constants.PLAN_STOPPED)

        if self.get_current_plan_state(node) == \
                test_constants.PLAN_STOPPING:
            return self.wait_for_plan_state(node,
                                            test_constants.PLAN_STOPPED)

        return True

    def restart_litpd_when_task_state(self, ms_node, task, timeout_mins=5,
                                      task_state=0):
        """
        Restart LITP service on the MS node  when the task has reached
        the specified state. Wait for plan to transition to state
        'Stopped' after service restarts.

        Args:
            ms_node (str): The node on which to run the command on
            task (str): Task to wait for to be in specified state
            before restarting LITP service
        Kwargs:
            timeout_mins (int): Time (in minutes) to wait for task
            to be in specified state
            task_state (int): id of task state
            i.e Initial, Failed, Success. These id's can be found
            in test_constants.
            Default is 0 (Success)
            """
        self.assertTrue(self.wait_for_task_state(ms_node,
                                                 task,
                                                 task_state,
                                                 False, timeout_mins),
                                                 'Task {0} did not transition'
                                                 ' to the specified state'
                                                 'within the expected time'
                                                 .format(task))

        self.log('info', 'Task {0} completed successfully.\nRestarting litpd.'
                 .format(task))
        self.restart_litpd_service(ms_node)
        self.log('info', 'litpd restarted, waiting for plan to go to state'
                         ' Stopped(up to 10 mins).')
        self.wait_for_plan_state(ms_node, test_constants.PLAN_STOPPED,
                                 timeout_mins=10)
        self.log('info', 'Plan should now be Stopped.')

    def __remove_children_from_ls(self, cmd_list):
        """Searches through the command lists and removes any create
        or inherit commands on child paths. This is to avoid delete
        attempts of child paths when the parent has already been deleted.

        So, for example, if parent cmd contains the path /deployment/nodes then
        a command in the list which contains /deployment/nodes/node1 will be
        removed.

        Args:
            cmd_list (list): The list of commands to search.

        Return:
            list. The list with any child commands stripped out.
        """

        for parent_cmd in list(cmd_list):
            # Get the node where the parent command was run
            p_cmd_node = parent_cmd[self.cleanup_key_node]

            # Loop through all successfully run commands
            for cmd in list(cmd_list):
                # if cmd was run on same node
                if p_cmd_node == cmd[self.cleanup_key_node]:

                    # if passed cmd is a parent current cmd in loop
                    if self.cli.is_parent_cmd(parent_cmd[self.cleanup_key_cmd],
                                          cmd[self.cleanup_key_cmd]):
                        # Delete the current command from successful cmd list
                        cmd_list.remove(cmd)

        return cmd_list

    # Group 2 - Logging Related
    def log(self, logtype, msg, *args, **kwargs):
        """Simple log wrapper for Python logger functions.

        Args:
           logtype  (str): Type of log message.
                           Supported types: 'info', 'warning',
                           'debug', 'error', 'critical'.

           msg      (str): Message to log.

        Kwargs:
           args      Keep compatibility with standard logger.

           kwargs    Keep compatibility with standard logger.

        Returns:
           str. Call to the Python logger with specified type and msg.
        """
        return self.g_util.log(logtype, msg, *args, **kwargs)

    # Group 3 - Node list related
    def set_node_connection_data(self, node, ipv4=None, ipv6=None, mac=None,
                                 hostname=None, nodetype=None, username=None,
                                 password=None):
        """Updates the connection data of an existing node object. Will only
        update the connection data passed in as parameters and leave
        unspecified data unchanged.

        Args:
           node      (str): Node filename.

        kwargs:
           ipv4      (str): IPV4 address.

           ipv6      (str): IPV6 address.

           mac       (str): mac address to update.

           hostname  (str): hostname to update.

           nodetype  (str): nodetype to update.

           username  (str): username to update.

           password  (str): password to update.


        Returns:
           bool. False if node cannot be found or True if node was updated.
        """

        real_node_ls = self.get_node_list_by_name(node)
        if not real_node_ls:
            self.log("error", "Node {0} cannot be found".format(node))
            return False

        real_node = real_node_ls[0]
        real_node.disconnect()

        if ipv4:
            real_node.ipv4 = ipv4

        if ipv6:
            real_node.ipv6 = ipv6

        if mac:
            real_node.mac = mac

        if hostname:
            real_node.hostname = hostname

        if nodetype:
            real_node.nodetype = nodetype

        if username:
            real_node.username = username

        if password:
            real_node.password = password

        return True

    def add_vm_to_nodelist(self, hostname, ipv4, username, password,
                           ipv6=None, mac=None):
        """
        PLEASE USE add_vm_to_node_list instead of this function.
        This will be removed when all test files have been updated.
        Creates a new node object of type vm with the passed parameters.

        Args:
           hostname      (str): Node hostname.

           ipv4          (str): The ipv4 address of node.

           username  (str): username to update.

           password  (str): password to update.

        kwargs:
           ipv6      (str): IPV6 address.

           mac       (str): mac address to update.

        This node object can now be used in other framework commands by calling
        get_vm_node_filenames.
        """

        vm_node = GenericNode()

        vm_node.ipv4 = ipv4
        vm_node.ipv6 = ipv6
        vm_node.mac = mac
        vm_node.hostname = hostname
        vm_node.filename = hostname
        vm_node.nodetype = "vm"
        vm_node.username = username
        vm_node.password = password

        self.nodes.append(vm_node)

    def add_vm_to_node_list(self, hostname, username, password,
                           ipv4=None, ipv6=None, mac=None):
        """
        Creates a new node object of type vm with the passed parameters.

        Args:
           hostname      (str): Node hostname.

           username  (str): username to update.

           password  (str): password to update.

        kwargs:
           ipv4      (str): The ipv4 address of node.

           ipv6      (str): The IPV6 address of node.

           mac       (str): mac address to update.

        This node object can now be used in other framework commands by calling
        get_vm_node_filenames.
        """
        vm_node = GenericNode()

        vm_node.ipv4 = ipv4
        vm_node.ipv6 = ipv6
        vm_node.mac = mac
        vm_node.hostname = hostname
        vm_node.filename = hostname
        vm_node.nodetype = "vm"
        vm_node.username = username
        vm_node.password = password

        self.nodes.append(vm_node)

    def get_vm_node_filenames(self):
        """
        Returns a list of all defined vm nodes.

        vm nodes can be defined dynamically with the add_vm_to_nodelist method.

        Returns:
           list. The list of vm nodes defined.

        """
        vm_nodes = list()
        vm_nodes.extend(self.get_node_list_filename_by_type("vm"))

        return vm_nodes

    def add_node_to_connfile(self, hostname, ipv4, username, password,
                           nodetype, rootpw=None, port='22', ipv6=None,
                           mac=None):
        """
        Add a node to the host.properties file with the passed parameters.

        Args:
           hostname      (str): Node hostname.

           ipv4          (str): The ipv4 address of node.

           username  (str): username to update.

           password  (str): password to update.

           nodetype  (str): type of node.

        kwargs:
           rootpw    (str): root user password.

           port      (str): ssh port number. Defaults to 22.

           ipv6      (str): IPV6 address.

           mac       (str): mac address to update.

        Returns:
            bool. True if node added to file. False if node was already in
            file.
        """

        # First verify that hostname is not already in the file.
        file1 = open(self.con_data_path, 'r')
        lines = file1.readlines()
        file1.close()
        for line in lines:
            if hostname in line:
                self.log("error", "Host {0} already in {1}".format(hostname,
                                                           self.con_data_path))
                return False

        # Create lines to add to file.
        prefix = "host." + hostname
        lines = list()
        lines.append(prefix + ".ip=" + ipv4)
        lines.append(prefix + ".user." + username + ".pass=" + password)
        lines.append(prefix + ".type=" + nodetype)
        if rootpw:
            lines.append(prefix + ".user.root.pass=" + rootpw)
        if port:
            lines.append(prefix + ".port.ssh=" + port)
        if ipv6:
            lines.append(prefix + ".ipv6=" + ipv6)
        if mac:
            lines.append(prefix + ".mac=" + mac)

        # Add lines to file.
        with open(self.con_data_path, 'a') as nodefile:
            nodefile.write("\n")
            for line in lines:
                nodefile.write(line + '\n')

        node = GenericNode()

        node.ipv4 = ipv4
        node.ipv6 = ipv6
        node.mac = mac
        node.hostname = hostname
        node.filename = hostname
        node.nodetype = nodetype
        node.username = username
        node.password = password
        node.rootpw = rootpw

        self.nodes.append(node)

    def remove_node_from_connfile(self, hostname):
        """
        Removes a host from the host.properties file.

        Args:
           hostname      (str): Node hostname to remove from file.

        Returns:
            bool. Always returns True, even if node was not in file initially.
        """

        file1 = open(self.con_data_path, 'r')
        lines = file1.readlines()
        file1.close()
        file2 = open(self.con_data_path, 'w')
        previous_line = ""
        for line in lines:
            # If line contains no name/value parts, skip line
            if line in ['\n', 'r\n'] and previous_line in ['\n', 'r\n']:
                previous_line = line
                continue
            if hostname not in line:
                print line
                previous_line = line
                file2.write(line)
        file2.close()

        for node in list(self.nodes):
            if hostname == node.hostname:
                self.nodes.remove(node)

    def update_node_in_connfile(self, hostname, ipv4, username, password,
                           nodetype, rootpw=None, port='22', ipv6=None,
                           mac=None):
        """
        Update a node in the host.properties file with the passed parameters.
        If the parameter already exists in node connection file, it will simply
        be updated. If not already in file, it will be appended.

        Args:
           hostname      (str): Node hostname.

           ipv4          (str): The ipv4 address of node.

           username  (str): username to update.

           password  (str): password to update.

           nodetype  (str): type of node.

        kwargs:
           rootpw    (str): root user password.

           port      (str): ssh port number. Defaults to 22.

           ipv6      (str): IPV6 address.

           mac       (str): mac address to update.

        Returns:
            bool. True if node updated in file. Otherwise False.
        """
        new_lines = list()
        prefix = "host." + hostname

        if ipv4:
            new_lines.append(prefix + ".ip=" + ipv4)

        if ipv6:
            new_lines.append(prefix + ".ipv6=" + ipv6)

        if mac:
            new_lines.append(prefix + ".mac=" + mac)

        if nodetype:
            new_lines.append(prefix + ".type=" + nodetype)

        if username and password:
            new_lines.append(\
                prefix + ".user." + username + ".pass=" + password)

        if port:
            new_lines.append(prefix + ".port.ssh=" + port)

        if rootpw:
            new_lines.append(prefix + ".user.root.pass=" + rootpw)

        if not self._is_host_in_node_conn_file(hostname):
            return False

        with open(self.con_data_path, 'r') as nodefile:
            for line in nodefile:
                for new_line in new_lines:
                    # Ignore hash comments
                    if not line.startswith('#'):
                        # Split variable between value and variable name.
                        variable_parts = line.split("=", 1)
                        # If line contains no name/value parts, skip line
                        if len(variable_parts) < 2:
                            continue

                        attribute = new_line.split("=", 1)
                        attribute_name = attribute[0]

                        variable_name = variable_parts[0]

                        if variable_name == attribute_name:
                            old_text = line
                            new_text = new_line + "\n"
                            file1 = open(self.con_data_path, 'r').read()
                            file2 = open(self.con_data_path, 'w')

                            self.log("info", "Replacing '{0}' with '{1}'"\
                                       .format(old_text.split()[0], new_text))
                            new_content = file1.replace(old_text, new_text)
                            file2.write(new_content)
                            new_lines.remove(new_line)
                            file2.close()

        # Append new parameters to end of file.
        with open(self.con_data_path, 'a') as nodefile:
            for append_line in new_lines:
                nodefile.write(append_line + '\n')
                self.log("info", "Adding '{0}' as not found in {1}"\
                               .format(append_line, self.con_data_path))

        self.set_node_connection_data(hostname, ipv4, ipv6, mac,
                                 hostname, nodetype, username,
                                 password)

        return True

    def _is_host_in_node_conn_file(self, hostname):
        """Private function to check if host is in node conn file.

        Args:
           hostname (str): Host to search for in node connection file.

        Returns:
            bool. True if node is in file. Otherwise False.
        """
        host_found = False
        with open(self.con_data_path, 'r') as nodefile:
            for line in nodefile:
                # Ignore hash comments
                if not line.startswith('#'):
                    # Split variable between value and variable name.
                    # N.b. We limit the split as value may contain '=',
                    # e.g. in password
                    variable_parts = line.split("=", 1)
                    # If line contains no name/value parts, skip line
                    if len(variable_parts) < 2:
                        continue
                    variable_name = variable_parts[0]

                    # Get hostname from variable name
                    host = variable_name.split(".")[1]
                    if host == hostname:
                        host_found = True
                        return True

        if not host_found:
            self.log("error", "Hostname '{0}' not found in '{1}'"\
                              .format(hostname, self.con_data_path))
            return False

    def __get_node_list_by_att(self, att, atts):
        """Private function to get node list by attribute.

        Args:
           att     (str): Attribute you want to use to get list of nodes.

           atts   (list): Attributes you are searching for.

        Returns:
           A list of nodes matching the attribute.
        """
        nodelist = []

        if att == None:
            self.log("Error", "Passed attribute is None")
            return nodelist

        if atts == None:
            self.log("Error", "Passed attributes are None")
            return nodelist

        for node in self.nodes:
            if getattr(node, att) in atts:
                nodelist.append(node)

        return nodelist

    def get_node_att(self, node, att):
        """Get node attribute based on supplied filename.

        Args:
           node    (str): Filename of the questioned node.

           att     (str): Property you want to return.
           Allowed values are: rootpw, ipv4, username, password,
           mac, ipv6, hostname, nodetype.

        Returns:
           str. A string representing the matched attribute
           on the specified node. This is the attribute read directly
           as defined in the connection data file(s).
        """
        if att == None:
            self.log("Error", "Passed attribute is None")
            return None

        for item in self.nodes:
            if getattr(item, 'filename') == node:
                return getattr(item, att)

    def get_node_list_by_hostname(self, hostnames):
        """Get node list based on hostnames.

        Args:
           hostnames (list): List of hostnames for nodes.

        Returns:
           list. A list of nodes returned with the specified hostname.
        """
        return self.__get_node_list_by_att('hostname', hostnames)

    def get_node_list_by_ipv4(self, ips):
        """Get node list based on IPs.

        Args:
           ips (list): List of IPs for nodes.

        Returns:
           list. A list of nodes returned with the specified IPs.
        """
        return self.__get_node_list_by_att('ipv4', ips)

    def get_node_list_by_name(self, filenames):
        """Get node list based on filenames.

        Args:
           filenames (list): List of filenames for nodes.

        Returns:
           list. A list of nodes returned from the specified
           connection filename.
        """
        return self.__get_node_list_by_att('filename', filenames)

    def get_node_list_by_type(self, types):
        """Get node list based on types.

        Args:
           types (list): List of types for nodes.

        Returns:
           list. A list of node objects matching the specified types.
        """
        return self.__get_node_list_by_att('nodetype', types)

    def get_hostname_of_node(self, ms_node, node_path):
        """
        Gets the hostname of a modeled node.

        Args:
            ms_node (str): Node with LITP model
            node_path (str): Model path of the node

        Returns:
            Str. Hostname of the node
        """
        hostname = self.get_node_filename_from_url(
             ms_node, node_path)
        return self.get_node_att(hostname, 'hostname')

    def get_node_list_filename_by_type(self, n_type, include_type=True):
        """Returns the list of all nodes which either match the given type or
        do not match the given type as determined by the include flag.

        Args:
           n_type       (str): The node type to search for (e.g. management).

        Kwargs:
           include_type (bool): Defaults to True and controls how the method
           behaves. When True, method returns only nodes that match the passed
           nodetype. When False, method returns only nodes that DO NOT match
           the passed nodetype.

        Returns:
            list. A list of node filenames.
        """
        node_list = list()

        # loop through all nodes
        for node in self.nodes:

            if n_type == node.nodetype and include_type:
                node_list.append(node.filename)
            elif n_type != node.nodetype and not include_type:
                node_list.append(node.filename)

        return node_list

    def get_management_node_filenames(self):
        """Returns a list of all management node objects.

        Returns:
           list. List of all management node filenames.
        """
        ms_nodes = self.get_node_list_filename_by_type("management")

        if ms_nodes == []:
            raise ValueError("No management nodes defined in deployment")

        return ms_nodes

    def get_management_node_filename(self, node_index=0):
        """Return the filename of a management node. If no parameter is
        passed, will return the first management node otherwise will return the
        nth management node in the list of nodes as determined by the
        node_index parameter.

        Kwargs:
           node_index (int): The index for the MS you wish to get from the
                              nodelist.

        Returns:
           str. A string corresponding to the filename used to define the MS.

        Raises:
           AssertionError: If the number of defined MS nodes is less than the
           index passed.
        """
        ms_nodelist = self.get_management_node_filenames()

        self.assertTrue(len(ms_nodelist) > node_index)

        return ms_nodelist[node_index]

    def get_managed_node_filenames(self):
        """Gets all managed nodes.

        Returns:
            list. A list of all managed nodes as a list filenames.

        Raises:
           AssertionError: If no management nodes are found.
        """

        managed_nodes = self.get_node_list_filename_by_type("managed")

        self.assertNotEqual([], managed_nodes)

        return managed_nodes

    def get_sfs_node_from_ipv4(self, sfs_ipv4_ip):
        """Get an SFS server by it's ipv4 address.

        Returns:
            list. A list of all SFS systems which match the given ipv4 address.

        Raises:
           AssertionError: If no matching SFS IP is found.
        """

        sfs_nodes = list()
        n_type = "sfs"
        # loop through all nodes
        for node in self.nodes:
            if n_type == node.nodetype and sfs_ipv4_ip == node.ipv4:
                sfs_nodes.append(node.filename)

        self.assertNotEqual([], sfs_nodes)

        return sfs_nodes

    def get_sfs_node_filenames(self):
        """Gets all defined SFS nodes.

        Returns:
            list. A list of all SFS nodes as a list filenames.

        Raises:
            AssertionError: If no SFS nodes are found.
        """

        sfs_nodes = self.get_node_list_filename_by_type("sfs")

        self.assertNotEqual([], sfs_nodes)

        return sfs_nodes

    def get_rhel_server_node_filenames(self):
        """Gets all NFS RHEL nodes.

        Returns:
            list. A list of all NFS RHEL nodes as a list filenames.

        Raises:
            AssertionError: If no NFS RHEL nodes are found.
        """

        rhel_nodes = self.get_node_list_filename_by_type("rhel")

        self.assertNotEqual([], rhel_nodes)

        return rhel_nodes

    def is_control_node(self, node_id):
        """Returns a boolean based on whether the node id passed to it
        corresponds to a control node or not.

        Args:
          node_id (int): The node id as reported in the LITP tree model.

       Returns:
          bool. True if the node id corresponds to a control node or
          False otherwise.
      """
        # Convert to int if parameter is passed as a string
        node_id = int(node_id)

        if node_id in self.control_node_ids:
            return True

        return False

    def get_control_payload_filenames_from_tree(self, ms_node):
        """Checks the LITP tree of the passed MS server and
        returns a list of control nodes and payload nodes.

        Args:
        ms_node (str): The filename of the connection data file defining
        the MS with the LITP tree you wish to query.

        Returns:
           list, list. The first list corresponds to all control nodes and
           the second corresponds to all payload nodes.
        """
        node_filen_con = list()
        node_filen_pay = list()
        #Get all node urls in the tree
        node_urls = self.find(ms_node, "/deployments", "node")

        for url in node_urls:
            #Get the node_id property for each node
            node_id = self.get_props_from_url(
                ms_node, url, "node_id")
            if node_id:
                if self.is_control_node(node_id):
                    node_filen_con.append(
                        self.get_node_filename_from_url(ms_node, url))
                else:
                    node_filen_pay.append(
                        self.get_node_filename_from_url(ms_node, url))

        return node_filen_con, node_filen_pay

    def get_node_filename_from_url(self, ms_node, node_url):
        """Given a node URL from the LITP tree on the specified node,
        finds the related connection file by comparing hostnames.

        Args:
          ms_node (str): The MS with the LITP tree you wish to query.

          node_url (str): The URL of the node you wish to find the connection
                          data file for.

        Returns:
            str. The connection data filename which corresponds to the node URL
            or None if the node filename cannot be found in the connection data
            files.

        The returned connection data filename can be used in the
        run_command/run_commands method.
        """
        node_hname_from_tree = self.get_props_from_url(
            ms_node, node_url, "hostname")

        for node in self.nodes:
            if node_hname_from_tree == node.hostname:
                return node.filename

        self.log("error",
                 "Node filename cannot be found." +\
                     "Please check connection data file hostname is correct.")
        return None

    def get_node_url_from_filename(self, ms_node, node_filename):
        """Given a node filename, uses the hostname to cross reference which
        path the node corresponds to in the LITP tree.

        Args:
          ms_node (str): The MS with the LITP tree you wish to query.

          node_filename (str): The node filename used when running commands
                               on the node.

        Returns:
            str. The path which corresponds to the node filename passed in
            or None if no matching path can be found.
        """
        node_paths = self.find(ms_node, "/deployments", "node")

        node_hname_in_file = self.get_node_att(node_filename,
                                                  "hostname")

        for path in node_paths:
            node_hname_from_tree = self.get_props_from_url(
                ms_node, path, "hostname")

            if node_hname_from_tree == node_hname_in_file:
                return path

        return None

    def get_all_node_filenames(self):
        """Gets a list of all nodes defined in connection data files.

        Returns:
           list. List of all nodes in connection data files.
        """
        # Node Type cannot be None so by passing the match to false
        # we will return all node types
        return self.get_node_list_filename_by_type(None, False)

    # Group 4 - Related to run

    def run_command_local(self, cmd, logging=True):
        """Runs the given command from the machine the test is being run from.

        This method just calls the method of the same name in Generic Utils.
        This is because there are use cases where some utilities need to run
        local commands (such as the curl command).

        Args:
           cmd  (str): The command to be run.

        Kwargs:
           logging (bool): Set to False to remove logging of command results.

        Result:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        return self.g_util.run_command_local(cmd, logging)

    def run_command_via_node(self, via_node, cmd_node, cmd,
                             username=None, password=None,
                             timeout_secs=60,
                             ip_protocol=None):
        """
        Connects to the cmd_node via the via_node and runs the passed cmd.

        Args:
           via_node     (str): The node to connect via.

           cmd_node     (str): The node to run the command on.

           cmd          (str): The command to run.

        Kwargs:
           username   (str): Username to use to login to the cmd_node. If not
                             set, default from node object will be used.

           password   (str): Password to use to login to the cmd_node. If not
                             set, default from node object will be used.

           timeout_secs (int): The timeout value of the passed command
                               in seconds.

           ip_protocol (str): Controls ip protocol used to connect to node.
                        Possible values are None, 'ipv4' and 'ipv6'.
                        If None, will attempt using ipv4. If no ipv4 address
                        will attempt ipv6.
                        If ipv4, will attempt to connect using ipv4 only.
                        If ipv6, will attempt to connect using ipv6 only.
                        Defaults to None

        Works by logging onto the via_node and then running an ssh command to
        connect and run a command on the cmd_node. Most used when connecting
        to vms which are not reachable from the gateway machine.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        ##Get login credentials for node
        if not username:
            username = self.get_node_att(cmd_node, 'username')

        if not password:
            password = self.get_node_att(cmd_node, 'password')

        if not ip_protocol:
            node_ip = self.get_node_att(cmd_node, 'ipv4')
            if not node_ip:
                node_ip = self.get_node_att(cmd_node, 'ipv6')
        elif ip_protocol == 'ipv4':
            node_ip = self.get_node_att(cmd_node, 'ipv4')
        else:
            # ipv6
            node_ip = self.get_node_att(cmd_node, 'ipv6')

        self.assertTrue(node_ip, "ipaddress of node could not be determined")

        #Create command which performs ssh
        cmd_str = '/usr/bin/ssh -o StrictHostKeyChecking=no ' \
        + '-o UserKnownHostsFile=/dev/null {0}@{1} "{2}"'.format(username,
                                                    node_ip,
                                                    cmd)

        #Create expects dict to supply password
        res_list = list()

        #Create expected prompt
        if self.sles_vm in cmd_node:
            prompt = "Password:"
        else:
            prompt = "{0}@{1}'s password:".format(username, node_ip)

        res_dict = self.get_expects_dict(prompt, password)
        res_list.append(res_dict)

        stdout, stderr, returnc = \
            self.run_expects_command(via_node, cmd_str, res_list,
                                     timeout_secs=timeout_secs)

        #Strip lines related to acceptance of ssh key from stdout
        stdout = stdout[1:]

        return stdout, stderr, returnc

    def run_command(self, node, cmd, username=None, password=None,
                    ipv4=True, sudo=False, logging=True, add_to_cleanup=True,
                    su_root=False, su_timeout_secs=120, execute_timeout=0.25,
                    connection_timeout_secs=600, default_asserts=False,
                    return_immediate=False):
        """Runs the passed command on specified node.

        Args:
           node            (str): Node to run command on. Node is identified
                                  by filename of connection data file that
                                  defines it.

           cmd             (str): Command to be executed on node.

        Kwargs:
           username        (str): Username to use to run the command. If not
                                  set, default in data file will be used.

           password        (str): Password to use to run the command. If not
                                  set, default in data file will be used.

           ipv4            (bool): Switch between ipv4 and ipv6.

           sudo            (bool): If True, use sudo to run command.

           logging         (bool): If False, turn off logging of command to run
                                   and results.

           add_to_cleanup  (bool): If False, do not add command to autocleanup.

           su_root         (bool): Set to True to run command as root. If set
                                   all stderr will be returned as part of the
                                   stdout channel. The stderr channel be empty.

           su_timeout_secs (bool): Default timeout for root commands to
                                   finish running.

           execute_timeout (float): If set, changes the execute timeout
                                    from the default. That is, the time the
                                    channel waits in seconds after executing a
                                    command before polling for data.
                                    Default is 0.25 seconds.

          connection_timeout_secs (int): Time to wait for command to finish
          before exiting with an error. Defaults to 600 seconds (10 minutes).

          default_asserts (bool): If set, will assert stderr is empty and
                                  return code is 0.

          return_immediate (bool): If set returns immediately after executing
                                   the command without waiting for command
                                   to return. Does not work when su_root flag
                                   is set.

        Returns:
           list, list, int. Returns stdout, stderr and rc after running
           the command.

           NB: If the su_root flag is set all stderr will be returned as part
           of the stdout channel. The stderr channel will be empty.
        """
        if isinstance(cmd, list):
            raise ValueError("run_command expects a single cmd, not a list")

        real_node_ls = self.get_node_list_by_name([node])

        if not real_node_ls:
            self.log("error", "Node {0} cannot be found".format(node))
            return None, None, None

        real_node = real_node_ls[0]

        if not su_root and logging:
            self.g_util.log_now()

            if username:
                print "[{0}@{1}]# {2}".format(username,
                                              real_node.ipv4, cmd)
            else:
                print "[{0}@{1}]# {2}".format(real_node.username,
                                              real_node.ipv4, cmd)

        stdout, stderr, exit_code = real_node.execute(
            cmd, username, password, ipv4,
            sudo, su_root, su_timeout_secs, execute_timeout,
            connection_timeout_secs, return_immediate)

        if logging:
            print '\n'.join(stdout)
            print '\n'.join(stderr)
            print exit_code

        if not logging and exit_code != 0:
            print "Failure detected logging suppressed output"
            self.g_util.log_now()

            if username:
                print "[{0}@{1}]# {2}".format(username,
                                              real_node.ipv4, cmd)
            else:
                print "[{0}@{1}]# {2}".format(real_node.username,
                                              real_node.ipv4, cmd)
            print '\n'.join(stdout)
            print '\n'.join(stderr)
            print exit_code

        #If successful create add to cleanup list
        if exit_code == 0 and add_to_cleanup:
            nodeindex = real_node.filename

            if self.cli.is_create_link_cmd(cmd) or \
                    self.cli.is_run_plan_cmd(cmd) or \
                    self.cli.is_snapshot_cmd(cmd):
                self.__add_to_cleanup(nodeindex, cmd, username, password,
                                      ipv4, su_root)
            elif self.cli.is_remove_cmd(cmd):
                self.__remove_from_cleanup(nodeindex, cmd)
            elif self.cli.is_xml_export_cmd(cmd):
                export_filepath = self.cli.get_export_filepath(cmd)
                self.__add_to_filepath_cleanup(nodeindex,
                                               export_filepath,
                                               username, password)
            elif self.cli.is_inherit_cmd(cmd):
                self.__add_to_cleanup(nodeindex, cmd, username, password,
                                      ipv4, su_root, inherit_cleanup=True)

        if default_asserts:
            self.assertEqual([], stderr)
            self.assertEqual(0, exit_code)

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        for i, std_msg in enumerate(stdout):
            stdout[i] = ansi_escape.sub('', std_msg)

        return stdout, stderr, exit_code

    def __add_to_cleanup(self, node, cmd, username, password, ipv4, su_root,
                         inherit_cleanup=False):
        """Add all parameters used to run a command to a dict which then gets
        appended to the successful_cmd list. This list is then used in cleanup.

        Args:
           node            (str): Node command was run on.

           cmd             (str): Command that was executed.

           username        (str): Username command was run as.

           password        (str): Password command was run as.

           ipv4            (bool): Whether command was run with ipv4 or ipv6.

           su_root         (bool): Whether command was run as root.
        """

        successful_cmd = dict()
        successful_cmd[self.cleanup_key_node] = node
        successful_cmd[self.cleanup_key_cmd] = cmd
        successful_cmd[self.cleanup_key_usr] = username
        successful_cmd[self.cleanup_key_pw] = password
        successful_cmd[self.cleanup_key_ipv4] = ipv4
        successful_cmd[self.cleanup_key_su] = su_root

        #self.successful_commands.append(successful_cmd)
        if inherit_cleanup:
            self.inherit_commands.append(successful_cmd)
        else:
            self.successful_commands.append(successful_cmd)

    def __add_to_filepath_cleanup(self, node, filepath, username=None,
                              password=None, su_root=False):
        """Creates a list of files/dirs that have been added to the node
        that need to be cleaned up after the test.

        Args:
           node     (str): Node command was run on.

           filepath (str): The filepath that was created.

        Kwargs:
           username (str): Username to use to run the command.
                           (if different from default).

           password (str): Password used to run command.

           su_root (bool): Whether command was run as root.
        """
        added_file = dict()
        added_file[self.cleanup_key_node] = node
        added_file[self.cleanup_key_filepath] = filepath
        added_file[self.cleanup_key_usr] = username
        added_file[self.cleanup_key_pw] = password
        added_file[self.cleanup_key_su] = su_root

        self.files_to_delete.append(added_file)

    def __update_cleanup_files(self, node, current_path, new_path, su_root):
        """Called when a file is moved. If file existed in cleanup,
        the filepath to remove will be updated.

        Args:
            node         (str): The node the file exists on.

            current_path (str): The original path of the file.

            new_path     (str): The new path of the file.

            su_root      (str): If set, delete the file at cleanup with root
                                privileges.
        """
        index = 0
        for file_item in list(self.files_to_delete):

            if (node == file_item[self.cleanup_key_node] and
                current_path == file_item[self.cleanup_key_filepath]):

                self.files_to_delete[index][self.cleanup_key_filepath] = \
                    new_path
                self.files_to_delete[index][self.cleanup_key_su] = su_root

            index += 1

    def __remove_from_cleanup(self, node, cmd):
        """If the passed remove cmd has been run on the same node and LITP URL
        as an existing cmd in the cleanup list, the command will be removed
        from the cleanup list.

        This is used to remove items that have already been removed
        successfully so cleanup does not attempt to remove them again.

        Args:
          node (str): The node the command was run on.

          cmd (str): The command that was run.
        """
        for command in list(self.successful_commands):
            if command[self.cleanup_key_node] == node:
                if self.cli.get_command_url(command[self.cleanup_key_cmd]) == \
                        self.cli.get_command_url(cmd):
                    self.successful_commands.remove(command)

        for command in list(self.inherit_commands):
            if command[self.cleanup_key_node] == node:
                if self.cli.get_command_url(command[self.cleanup_key_cmd]) == \
                        self.cli.get_command_url(cmd):
                    self.inherit_commands.remove(command)

    def backup_path_props(self, ms_node, path):
        """
        Stores the properties of a specific path for restoration at the
        end of the test.

        Args:
           ms_node (str): The name of the MS node.

           path (str): The path in the LITP tree you wish to backup.

        Returns:
           bool. True if the path could be found or False otherwise.
        """
        print "Backing up path: {0}".format(path)

        current_prop_values = self.get_props_from_url(ms_node, path,
                                                      show_option="")

        #If we returned values from path call
        if current_prop_values:
            #If this path has not already been backed up in this test
            if not self.is_text_in_list(path, self.path_restore_list):
                path_to_restore = dict()
                path_to_restore["PATH"] \
                    = path
                path_to_restore["PROPS"] = current_prop_values
                path_to_restore["MS_NODE"] \
                    = ms_node
                self.path_restore_list.append(path_to_restore)

                return True
            else:
                self.log("error", "This path has already been backed up.")
        else:
            self.log("error", "Could not read path for property backup.")

        return False

    def run_commands(self, nodes, cmdlist, username=None, password=None,
                     ipv4=True, sudo=False, break_on_error=False,
                     add_to_cleanup=True, su_root=False, su_timeout_secs=60):
        """Run a list of commands on a list of nodes.

        Args:
           nodes (list/str): List of filenames for nodes. If a str is
                             passed instead of a list, the system assumes
                             there is just one node.

           cmdlist   (list): List of commands to be executed on the nodes.


        Kwargs:
           username        (str): Username to use to run the command. If not
                                  set, default in data file will be used.

           password        (str): Password to use to run the command. If not
                                  set, default in data file will be used.

           ipv4            (bool): Switch between ipv4 and ipv6.

           sudo            (bool): If True, use sudo to run command.

           break_on_error  (bool): If True, will break if a cmd fails.

           add_to_cleanup  (bool): If False, do not add command to autocleanup.

           su_root         (bool): Set to True to run command as root.

           su_timeout_secs (bool): Default timeout for root commands to
                                   finish running.

        Returns:
           dict.      {'node_filename':
                       {cmd_number_index:
                           {'rc': return_code_number,
                            'stderr': [list from standard error],
                            'stdout': [list from standard output]}}}
        """
        result = {}

        # If nodes is string will make a list of len 1 otherwise
        # will make nodelist equal to nodes
        if isinstance(nodes, str):
            nodelist = [nodes]
        else:
            nodelist = nodes

        real_nodelist = self.get_node_list_by_name(nodelist)

        for node in real_nodelist:
            nodeindex = node.filename
            result[nodeindex] = {}
            for cmd in cmdlist:
                self.g_util.log_now()
                if username:
                    print "[{0}@{1}]# {2}".format(username,
                                                  node.ipv4, cmd)
                else:
                    print "[{0}@{1}]# {2}".format(node.username,
                                                  node.ipv4, cmd)

                stdout, stderr, exit_code = node.execute(
                    cmd, username, password, ipv4, sudo, su_root,
                    su_timeout_secs)
                print '\n'.join(stdout)
                print '\n'.join(stderr)
                print exit_code

                # If successful create add to cleanup list
                if exit_code == 0 and add_to_cleanup:

                    if self.cli.is_create_link_cmd(cmd) or \
                            self.cli.is_run_plan_cmd(cmd) or \
                            self.cli.is_snapshot_cmd(cmd):
                        self.__add_to_cleanup(nodeindex, cmd, username,
                                              password, ipv4, su_root)
                    elif self.cli.is_remove_cmd(cmd):
                        self.__remove_from_cleanup(nodeindex, cmd)
                    elif self.cli.is_xml_export_cmd(cmd):
                        filepath = self.cli.get_export_filepath(cmd)
                        self.__add_to_filepath_cleanup(nodeindex, filepath,
                                                   username, password)
                    elif self.cli.is_inherit_cmd(cmd):
                        self.__add_to_cleanup(nodeindex, cmd, username,
                                              password, ipv4, su_root,
                                              inherit_cleanup=True)

                cmdindex = cmdlist.index(cmd)
                result[nodeindex][cmdindex] = {}
                result[nodeindex][cmdindex]['stdout'] = stdout
                result[nodeindex][cmdindex]['stderr'] = stderr
                result[nodeindex][cmdindex]['rc'] = exit_code

                if break_on_error and exit_code != 0:
                    break

        return result

    def check_for_log(self, node, msg_str, log_path, log_len, su_root=True,
                      return_log_msg=False):
        """
        Checks whether a log exists in the stated log file on the stated node.

        Args:
           node (str): The node whose log you wish to check.

           msg_str (str): Message string to search for in the log file.

           log_path (str): Full path to the log file in question.

           log_len (int): Will look for logs starting at log length
                          stated in this variable.

        Kwargs:

           su_root (bool): If set, runs the command as root.

           return_log_msg (bool): If set, returns the matching message found
                                  in the log file.

        Returns:
           bool; True if log message found or false otherwise, OR
           list; if return_log_msg is set to True, returns ouput from the
                    logs which matches the message string. This will be
                    empty if no match was found.
        """

        cmd = self.rhc.get_grep_file_cmd(log_path, msg_str,
                                         file_access_cmd="tail -n +{0}"
                                         .format(log_len))

        if su_root and \
                self.get_node_att(node, 'nodetype') == 'management':
            root_pw = self.get_node_att(node, 'rootpw')
            out, err, ret_code = self.run_command(node,
                                                          cmd,
                                                          'root',
                                                          root_pw)

        else:
            out, err, ret_code = self.run_command(node,
                                                          cmd,
                                                          su_root=su_root)

        self.assertTrue(ret_code < 2)
        self.assertEqual([], err)

        if return_log_msg:
            return out

        return self.is_text_in_list(msg_str, out)

    def wait_for_log_msg(self, node, msg_str, log_file='/var/log/messages',
                         timeout_sec=600, log_len=None,
                         rotated_log='/var/log/messages.1',
                         return_log_msgs=False):
        """
        In the case of a single message string, will wait for next occurrence
        of a message to appear in the message log.
        In the case of a list of message strings, will wait for all messages
        to appear in the message log.
        Will tail the log from the point it is at when method is called
        (unless log_len parameter sent in)so only
        new logs generated will be found.

        Contains logic to detect and handle log rotation while waiting for
        expected message.

        Args:
           node (str): The node whose log you wish to check.

           msg_str (str/list): Message string or list of message strings to
                               search for in the log file.

        Kwargs:
           log_file (str): Path to the log file in question,
                           defaults to /var/log/messages.

           timeout_sec (int): Timeout in seconds.

           log_len (int): If set will look for logs starting at log length
                          stated in this variable.
                          Otherwise will get check log length at time
                          method is called.

           rotated_log (str): Path to the rotated log where log rotateion is
                              enabled. Defaults to /var/log/messages.1

           return_log_msgs (bool): Option to return a concatenated list of all
                                    log messages found or empty if messages not
                                    found before timeout.

        Returns:
            bool; True if found or False if not found after timeout_sec, OR
            str/list; If return_log_msgs kwarg is set to True, a list of all
                      matching log messages found is returned.
        """
        elapsed_sec = 0
        check_interval_secs = 10
        matching_logs = []

        if isinstance(msg_str, str):
            msg_strs = [msg_str]
        else:
            msg_strs = msg_str

        # 1. Get current log length
        log_path = log_file

        if not log_len:
            log_len = self.get_file_len(node, log_path)

        self.assertTrue(log_len, "Log file not found")

        all_messages_found = True
        for msg_str in msg_strs:
            msg_found = False

            while elapsed_sec < timeout_sec:
                curr_log_pos = self.get_file_len(node, log_path)

                #If length of log is less than original log length we must have
                #rotated.
                if curr_log_pos < log_len:

                    unzip_cmd = "gunzip {0}.gz".format(rotated_log)
                    self.run_command(node, unzip_cmd, su_root=True)

                    #check rotated log file from original log_len
                    matching_log_str = self.check_for_log(node, msg_str,
                                                   rotated_log,
                                                   log_len,
                                                   return_log_msg=True)

                    if matching_log_str:
                        msg_found = True
                        matching_logs.extend(matching_log_str)

                    #set tail to be entire length of log file as it is new
                    starting_log_len = 0

                    # Set log_len to value 0 as it is new.
                    log_len = 0

                #If log has not been recycled
                else:
                    starting_log_len = log_len

                # 2. Check if message is in the latest log

                matching_log_str = self.check_for_log(node, msg_str,
                                                   log_path,
                                                   starting_log_len,
                                                   return_log_msg=True)

                if matching_log_str:
                    msg_found = True
                    matching_logs.extend(matching_log_str)

                if msg_found:
                    break

                time.sleep(check_interval_secs)
                elapsed_sec += check_interval_secs

                self.log("info", "String '{0}' not found in last {1}s."
                         .format(msg_str, str(elapsed_sec)))

            if not msg_found:
                self.log('error', 'Message {0} not found'.format(msg_str))
                all_messages_found = False

            #In the case of searching for a list of messages, set
            #all_messages_found to false if at lease one is not found.
            #if not msg_found:
            #    all_messages_found = False

        if return_log_msgs:
            if all_messages_found:
                return matching_logs
            else:
                return []

        return all_messages_found

    def wait_for_cmd(self, node, cmd, expected_rc, expected_stdout=None,
                     timeout_mins=1, su_root=False, default_time=10,
                     direct_root_login=False):
        """
        Runs a command repeatedly until the expected return code is received or
        timeout occurs.

        Args:
           node         (str): The node the command will be run on.

           cmd          (str): The command you wish to run.

           expected_rc  (int): The return code to wait for.

        Kwargs:
           expected_stdout (str): Optionally a stdout to wait for.

           timeout_mins (int): Timeout in minutes before breaking.

           su_root     (bool): Set flag to True to run the command as root.

           default_time  (int): The time to wait between each poll.
                                Defaults to 10 seconds.

           direct_root_login (bool): Set flag to True to run command as root
                                     without first logging in as a litp user

        Returns:
           bool. True if the expected return code is returned before timeout
           or False otherwise.
        """
        timeout_seconds = timeout_mins * 60
        seconds_passed = 0

        while True:
            self.log("info",
                     "Waiting for RC: {0}".format(expected_rc))

            if expected_stdout:
                self.log("info",
                         "Waiting for stdout: {0}".format(expected_stdout))

            self.log("info",
                     "Waited {0} out of {1} secs".format(seconds_passed,
                                                         timeout_seconds))

            if direct_root_login:
                root_pw = self.get_node_att(node, "rootpw")
                stdout, _, returnc = self.run_command(node, cmd,
                                                      username="root",
                                                      password=root_pw)
            else:
                stdout, _, returnc = self.run_command(node, cmd,
                                                      su_root=su_root)

            if returnc == expected_rc:
                #optional check stdout matches
                if expected_stdout:
                    if self.is_text_in_list(expected_stdout, stdout):
                        return True
                else:
                    return True

            time.sleep(default_time)
            seconds_passed += default_time

            if seconds_passed > timeout_seconds:
                return False

    def get_expects_dict(self, prompt, response):
        """Returns a prompt-response dictionary pair used in the
        run_expects_command method.

        Args:
           prompt (str): A prompt to expect when running a command.

           response (str): The response to send when the prompt is encountered.

        Return:
           dict. A dictionary with two entries (prompt and response).
        """

        return self.g_util.get_expects_dict(prompt, response)

    def run_mco_command(self, node, cmd, timeout_secs=60):
        """
        Logs in as the mco user and attempts to run an mco command.

        Args:
           node  (str): Node to run mco command on.

           cmd   (str): mco command to run.

        Kwargs:
           timeout_secs (int): A timeout to wait for the command to run,\
              given in seconds.

        Returns:
           stdout, stderr and rc for running the mco command.
        """
        ##Assumes mco command is only run on MS which allows
        ##root password.
        rootpw = self.get_node_att(node, "rootpw")

        ##timeout_secs parameter is future proof in case
        ##mco commands are run on nodes in future so we will use
        #su_root flag.
        return self.run_command(node, cmd, "root", rootpw,
                                su_timeout_secs=timeout_secs)

    def run_expects_command(self, node, cmd, expects_list, username=None,
                            password=None, ipv4=True, su_root=False,
                            timeout_secs=15, suppress_output=False):
        """
        Runs a command on the selected test node and responds to expected
        prompts as defined in the expects dict list.

        Args:
            node         (str): The node the command will be run on.

             cmd          (str): Command to execute

             expects_list (list): A list of expect dicts created using the\
                get_expects_dict command.

        Kwargs:
            username        (str): Username to use to run the command. If not\
                set, default in data file will be used.

            password        (str): Password to use to run the command. If not\
                set, default in data file will be used.

            ipv4            (bool): Switch between ipv4 and ipv6.

            su_root         (bool): Set flag to True to run the command as root

            timeout_secs     (int): The timeout to wait for the cmd passed to\
              execute.

            suppress_output (bool): If set will not print output of command
            to screen.

        Returns:
            list, list, int. Returns std_out, std_err and rc after running
                the command.
        """
        #If only a single expects dict has been passed make it a list of
        #length 1 as a list is expected
        if not isinstance(expects_list, list):
            expects_list = [expects_list]

        real_node_ls = self.get_node_list_by_name(node)

        if not real_node_ls:
            self.log("error", "Node {0} cannot be found".format(node))
            return None, None, None

        real_node = real_node_ls[0]

        stdout, stderr, returnc = real_node.execute_expects(cmd,
                                                            expects_list,
                                                            username,
                                                            password,
                                                            ipv4,
                                                            su_root,
                                                            timeout_secs)

        if suppress_output:
            self.log("info", "Surpressing large output ({0} lines)"\
                         .format(len(stdout)))
        else:
            print '\n'.join(stdout)
            print '\n'.join(stderr)
            print returnc

        return stdout, stderr, returnc

    # Group 5 - Checking results
    def get_errors(self, result):
        """Loops through a result dictionary and
        returns a list of commands (ref by number) which reported errors.

        Args:
           result (dict): Result dictionary returned from the
                          run_commands method.

        Returns:
           list. A list of commands which returned errors (ref by number).
        """
        return self.g_util.get_errors(result)

    def get_stderr(self, result):
        """Loops through a result dictionary and returns a list of all the
        errors reported (the total stderr stream).

        Args:
           result (dict): Result dictionary returned from the
                          run_commands method.

        Returns:
           list. A list of errors reported or empty list if all commands ran
           successfully.
        """
        stderr_list = list()
        cmds_with_error = self.g_util.get_errors(result)

        for cmd in cmds_with_error:
            stderr_list.append("".join(cmd['stderr']))

        return stderr_list

    def get_std_out_by_node(self, result, node):
        """Gets the stdout from the result dictionary for all commands run
        on the specified node.

        Args:
           result (dict): Result dictionary returned from the
                          run_commands method.

           node    (str): The node to filter by. Node is identified
                          by filename of connection data file that
                          defines it.

        Returns:
           list. A list of the std_out returned for all commands ran.
        """
        return self.g_util.get_std_out_by_node(result, node)

    def is_std_out_empty(self, result):
        """Returns True if all stdout is empty for all commands
        in the result dictionary.

        Args:
           result (dict): Result dictionary returned from the\
              run_commands method.

        Returns:
           bool. True if std_out is empty or False otherwise.
        """
        return self.g_util.is_std_out_empty(result)

    def is_std_out_in_all(self, result):
        """Returns True if each command returns something to std_out
        or False if at least one command returns nothing to std out.

        Useful when asserting that grep commands all found their expected item.

        Args:
           result (dict): Result dictionary returned from the
                          run_commands method.

        Returns:
           bool. Returns True if all cmds contain std_out or False otherwise.
        """
        return self.g_util.is_std_out_in_all(result)

    # Group 7 - Find command related methods
    def get_all_collections(self, node, path):
        """Returns all collections from the LITP tree under the
        supplied path.

        Args:
           node  (str): MS with tree to query. Node is identified
           by filename of connection data file that defines it.

           path  (str): The LITP path to search under.

        Returns:
           list. A list of URL strings of all the collections found under
           the supplied path or empty list if no collections
           exist under the path.

        """
        show_cmd = CLIUtils().get_show_cmd(path, "-r")
        grep_cmd = "| grep -B 2 'type'|grep -B 2 'collection-of'|grep ^'/'"

        show_cmd += grep_cmd

        # 4. Run the command and return output
        std_out, _, _ = \
            self.run_command(node, show_cmd, logging=True)

        return std_out

    def find_children_of_collect(self, node, path, collect_type,
                                 include_collect=False,
                                 find_all_collect=False):
        """
        Returns the paths of all immediate children of the passed
        collection type.

        Args:
           node     (str): MS with tree to query. Node is identified
                            by filename of connection data file that
                            defines it.

           path     (str): The LITP path to search under (e.g. '/deployments').

           collect_type (str): The resource type to filter by.

        Kwargs:
          include_collect (bool): If set to True, will return the collection
                                   itself.

          find_all_collect (bool): If set to True, will find all collections.

        Returns:
            list. List of all children of the collection.
        """
        collections = list()
        all_collects = list()

        collection_paths = self.find(node, path, collect_type,
                                     False, assert_not_empty=False)

        if collection_paths == []:
            return []

        #If we just want to look in the first collection matched
        if not find_all_collect:
            collection_path = collection_paths[0]
            collections.append(collection_path)
        #Else if we want to check in all collections
        else:
            collections.extend(collection_paths)

        for collect_item in collections:
            stdout, _, _ = self.execute_cli_show_cmd(node,
                                                     collect_item, "-l")
            if include_collect:
                all_collects.extend(stdout)
            else:
                all_collects.extend(stdout[1:])

        return all_collects

    @staticmethod
    def get_parent_path(path):
        """
        Returns the parent path of the passed path.

        For example, if you pass '/deployments/clusters' it will return
        '/deployments'.

        Args:
            path (str): The path you wish to find the parent for.

        Returns:
            str. The parent path or None if there is no parent.
        """
        path = path.strip()

        ##If we pass the actual root path return None
        if path == "/":
            return None

        #pass something on the root path (eg /ms) pass the root path
        if path.count("/") == 1:
            return "/"

        return path.rsplit("/", 1)[0]

    def find_parent_path_from_item_type(self, node, item_type, path):
        """
        Finds the parent path matching the item_type parameter from
        the passed path.

        For example, if you pass item_type 'storage-profile' and path
        /deployments/d1/clusters/c1/nodes/n1/storage_profile/volume_groups/\
        vg1/file_systems/fs1
        it will return
        /deployments/d1/clusters/c1/nodes/n1/storage_profile

        Args:
            node     (str): MS with tree to query. Node is identified by
                            filename of connection data file that defines it.

            item_type (str): The item type to search for in path.

            path (str): The path from which you want to find the parent.

        Returns:
            str. The parent path or None if there is no parent matching
                 the item_type parameter.
        """
        url = path.strip()

        ##If we pass the actual root path return None
        if url == "/":
            return None

        #pass something on the root path (eg /ms) pass the root path
        if url.count("/") == 1:
            return "/"

        while url.count("/") > 1:
            show_cmd = self.cli.get_show_cmd(url)
            resource_filter = \
                        "-E 'type: {0}$|type: reference-to-{0}$'"\
                        .format(item_type)
            grep_cmd = \
                " | grep -B 2 {0} | grep ^'/'".format(resource_filter)
            show_cmd += grep_cmd
            _, _, rc = \
                self.run_command(node, show_cmd)
            if rc == 0:
                return url

            count = url.count("/")
            split_url = url.split('/')
            url = "/".join([split_url[num] for num in xrange(0, count)])

        return None

    def find(self, node, path, resource, rtn_type_children=True,
             assert_not_empty=True, exact_match=False, find_refs=False,
             exclude_services=False):
        """Returns a list of paths that match the resource type filter criteria
        and are are under the supplied path.

        Filter is by resource type and, depending on the value of the
        rtn_type_children, will either return only children nodes or return
        only collections of the specified resource type.

        Args:
           node     (str): MS with tree to query. Node is identified by
                            filename of connection data file that defines it.

           path     (str): The LITP path to search under (e.g. '/deployments').

           resource (str): The resource type to filter by.

        Kwargs:
           rtn_type_children (bool): Default returns only children. Set to
                                     False to return collections.

           assert_not_empty  (bool): By default, asserts find does not
                                     return empty.

           exact_match        (bool): If set, ignores legacy logic and checks
                                      for a type which exactly matches the
                                      resource parameter text.

           find_refs        (bool): If set, will not exclude ref collections.

           exclude_services (bool): If set, will not return paths with
                                        /services in.

        Returns:
            list. List of all paths matched by find.
        """
        # 0. Construct recursive show command on path
        show_cmd = CLIUtils().get_show_cmd(path, "-r")

        resource_filter2 = None

        if exact_match:
            resource_filter = "-E 'type: {0}$'".format(resource)

        else:
            # 1. Construct resource search term based on flag

            #new find
            if rtn_type_children:
                #This grep does not matches children only

                #Temp workaround to fix node error
                if resource == "node":
                    resource_filter = "-E 'type: {0}$'".format(resource)
                else:
                    resource_filter = \
                        "-E 'type: {0}$|type: reference-to-{0}$'"\
                        .format(resource)
            else:
                # This grep matches collections only
                #tmp match to ignore ref collection
                if resource == "node":
                    resource_filter = "'type' |  grep -v 'ref-collection'" +\
                        " | grep -B 2 'collection-of-{0}'$".format(resource)
                else:
                    # This grep matches collections only
                    collection_grep1 = \
                        " -e 'collection-of-{0}'$ ".format(resource)
                    collection_grep2 = "-e 'collection-of-{0}-base'$"\
                        .format(resource)

                    collection_grep = collection_grep1 + collection_grep2

                    if find_refs:
                        resource_filter = "'type' | grep -B 2 {0}"\
                            .format(collection_grep)
                        resource_filter2 = "'type' " +\
                            "| grep -v 'ref-collection' " +\
                            "| grep -B 2 {0}"\
                            .format(collection_grep)
                        resource_filter = "'type' | grep -B 2 {0}"\
                            .format(collection_grep)
                    else:
                        resource_filter = \
                            "'type' | grep -v 'ref-collection' " +\
                            "| grep -B 2 {0}"\
                            .format(collection_grep)
                        resource_filter2 = "'type' | grep -B 2 {0}"\
                            .format(collection_grep)

        # 3. Add the piped grep to our show command
        grep_cmd = \
            " | grep -B 2 {0} | grep ^'/'".format(resource_filter)
        show_cmd += grep_cmd

        # 4. Run the command and return output
        std_out, _, _ = \
            self.run_command(node, show_cmd, logging=True)

        if exclude_services:
            for path in list(std_out):
                if 'services' in path:
                    std_out.remove(path)

        if std_out == [] and resource_filter2 != None:
            show_cmd = CLIUtils().get_show_cmd(path, "-r")
            grep_cmd = \
                " | grep -B 2 {0} | grep ^'/'".format(resource_filter2)
            show_cmd += grep_cmd
            std_out, _, _ = \
                self.run_command(node, show_cmd, logging=True)

        if exclude_services:
            for path in list(std_out):
                if 'services' in path:
                    std_out.remove(path)

        if assert_not_empty:
            self.assertNotEqual([], std_out,
                                "Find command did not return any paths")

        return std_out

    # Group 8 - File operations
    def create_file_on_node(self, node, filepath, file_contents_ls,
                            su_root=False, add_to_cleanup=True,
                            empty_file=False, file_permissions='775'):
        """Creates a new file on the specified node.

        Args:
           node              (str): The node to create the file on.

           filepath          (str): The filepath of the new file.

           file_contents_ls (list): A list containing the contents of the\
              new file. A new line will be written for each index in the list.

        Kwargs:
           su_root          (bool): Set to True if you need root permissions\
              to create the file.

           add_to_cleanup   (bool): Set to False if you do not want file to be\
              deleted automatically after the test.

           empty_file       (bool): Set to True if created file should be empty

           file_permissions (str): Permissions to set for created file using
                                   chmod notation. Defaults to '775'.

        Returns:
           bool. True if file created successfully or False otherwise.
        """
        if not file_contents_ls and not empty_file:
            return False

        if self.remote_path_exists(node, filepath):
            self.log("error", "Cannot create file, already exists")
            return False

        touch_cmd = "/bin/touch {0} && chmod {1} {0}".format(filepath,
                                                       file_permissions)

        stdout, stderr, returnc = self.run_command(node, touch_cmd,
                                                   su_root=su_root)

        if returnc != 0 or stderr != [] or stdout != []:
            return False

        if add_to_cleanup:
            self.__add_to_filepath_cleanup(node,
                                           filepath,
                                           su_root=su_root)

        if not empty_file:
            cmd = ""
            for file_line in file_contents_ls:
                cmd += "/bin/echo '{0}' >> {1};".format(file_line, filepath)

            stdout, stderr, returnc = self.run_command(node, cmd,
                                                       su_root=su_root)

            if returnc != 0 or stderr != [] or stdout != []:
                return False

        return True

    def remote_path_exists(self, node, path, expect_file=True, su_root=False):
        """Tests if the remote path exists. By default, checks for
        path as a file. On setting expect_file flag to false will
        check if path is a directory.

        Args:
           node         (str): Node to check. Node is identified
                               by filename of connection data file that
                               defines it.

           path         (str): Filepath to test.

        Kwargs:
           expect_file (bool): By default checks if file exists. Set to False
                               to check for directory.

           su_root     (bool): By default, it will not su to root user.

        Returns:
            bool. True if path exists and is of the expected type
            (e.g. a file or a directory).
        """
        if expect_file:
            path_cmd = "[ -f {0} ]".format(path)
        else:
            path_cmd = "[ -d {0} ]".format(path)

        _, _, exit_code = self.run_command(node, path_cmd, su_root=su_root)

        if exit_code == 0:
            return True
        return False

    def remove_item(self, node, remote_filepath, username=None, password=None,
                    su_root=False):
        """Remove a file or directory at the specified filepath
        from the specified node.

        Args:
           node            (str): Node to remove the file from.

           remote_filepath (str): Path of the file/directory to remove.

        Kwargs:
           username        (str): Username to use to run the command. If not\
              set, default in data file will be used.

           password        (str): Password to use to run the command. If not\
              set, default in data file will be used.

           su_root        (bool): If set to True, will delete with root\
              permissions.

        Returns:
           bool. True if path removed or False otherwise.
        """
        remove_cmd = "/bin/rm -rf {0}".format(remote_filepath)

        _, stderr, exit_code = self.run_command(node, remove_cmd,
                                                username, password,
                                                su_root=su_root)

        if exit_code != 0:
            self.log("error", "Could not delete item: {0}".format(stderr))
            return False

        return True

    def get_puppet_interval(self, node):
        """
        Returns the interval between puppet runs (runinterval). This is
        configured in the file referenced by the PUPPET_CONFIG_FILE constant.

        Args:
           node (str): The node you wish to check the puppet interval in.

        Returns:
          int. The puppet interval in seconds or None if it could not be found.
        """
        pp_cfg_file = test_constants.PUPPET_CONFIG_FILE
        pp_cfg_var = "runinterval"

        cmd = self.rhc.get_grep_file_cmd(pp_cfg_file, pp_cfg_var)
        out, err, ret_code = self.run_command(node, cmd, su_root=True)

        self.assertEqual(0, ret_code)
        self.assertEqual([], err)
        self.assertTrue(self.is_text_in_list(pp_cfg_var, out),
                        "{0} not in file".format(pp_cfg_var))

        sreg = r'{0}\s+=\s+(\d+)'.format(pp_cfg_var)
        reg_exp = re.compile(sreg, re.DOTALL)
        reg_match = reg_exp.search(str(out))
        if reg_match:
            str_val = reg_match.group(1)
            self.log('info', "Puppet runinterval is [{0}]".format(str_val))
            return int(str_val)
        else:
            self.log('error', "Couldn't find {0} in file {1}".format(
                pp_cfg_var, pp_cfg_file))
            return None

    def get_puppet_splaylimit(self, node):
        """
        Returns the splay limit(splaylimit) used in puppet timeout. This is
        configured in the file referenced by the PUPPET_CONFIG_FILE constant.

        Args:
           node (str): The node you wish to check the puppet splay limit in.

        Returns:
          int. The splay in seconds or None if it could not be found.
        """
        pp_cfg_file = test_constants.PUPPET_CONFIG_FILE
        pp_cfg_var = "splaylimit"

        cmd = self.rhc.get_grep_file_cmd(pp_cfg_file, pp_cfg_var)
        out, _, _ = self.run_command(
            node, cmd, su_root=True, default_asserts=True)

        sreg = r'{0}\s*=\s*(\d+)'.format(pp_cfg_var)
        reg_exp = re.compile(sreg, re.DOTALL)
        reg_match = reg_exp.search(str(out))
        if reg_match:
            str_val = reg_match.group(1)
            self.log('info', "Puppet splaylimit is [{0}]".format(str_val))
            return int(str_val)
        else:
            self.log('error', "Couldn't find {0} in file {1}".format(
                pp_cfg_var, pp_cfg_file))
            return 0

    def set_puppet_runinterval(self, node, new_value):
        """
        Description:

        Args:
            node (str): Node to run the command on
            new_value (str): value to update the puppet
                         runinterval to
        Returns:
             str. The original puppet runinterval value
        """

        orig_interval_value = self.get_puppet_interval(node)

        start_log_pos = self.get_file_len(node,
                                          test_constants.
                                          GEN_SYSTEM_LOG_PATH)

        cmd = self.rhc.get_grep_file_cmd(
                            test_constants.LITP_PUPPET_CONF_FILE,
                            "setting => 'runinterval',",
                            grep_args="-n")

        stdout, _, _ = self.run_command(node, cmd, su_root=True)

        line_number = stdout[0].split(":")[0]

        sed_cmd = self.rhc.get_replace_str_in_file_cmd(
            orig_interval_value, new_value,
            test_constants.LITP_PUPPET_CONF_FILE,
            sed_args='-in', line_number=int(line_number) + 1
        )

        self.run_command(node, sed_cmd, su_root=True,
                         default_asserts=True)

        self.start_new_puppet_run(node)

        log_msg = "{0} puppet-agent.*value changed "\
                  "'{1}' to '{2}'".format(node, orig_interval_value, new_value)

        self.assertTrue(self.wait_for_log_msg(node, log_msg,
                        log_len=start_log_pos))

        new_interval_value = self.get_puppet_interval(node)
        self.assertTrue(new_value, new_interval_value)
        return orig_interval_value

    def start_new_puppet_run(self, ms_node, assert_success=True):
        """
        Will wait for the current puppet cycles to complete
        and will then trigger a new run with the 'mco puppet runonce' command.

        Args:
            ms_node (str): The MS node.

       Kwargs:
           assert_success (str): By default, will assert puppet is
           successfully triggered.

       Raises:
          AssertionError if a puppet run fails to start.
      """
        if assert_success:
            self.assertTrue(self.wait_for_puppet_idle(ms_node))
        else:
            self.wait_for_puppet_idle(ms_node)

        clear_cache_cmd = "mco rpc puppetcache clean -I {0}".format(ms_node)
        self.run_command(ms_node, clear_cache_cmd, su_root=True)

        kick_puppet_cmd = "mco puppet runonce"
        _, _, _ = self.run_command(ms_node, kick_puppet_cmd, su_root=True)
        #if assert_success:
        #    self.assertEqual([], stdout)
        #    self.assertEqual([], stderr)
        #    self.assertEqual(0, returnc)

    def wait_full_puppet_run(self, ms_node, assert_success=True):
        """
        Will wait for the current puppet cycles to complete
        and will then trigger a new run with the 'mco puppet runonce'
        command. Will then wait for new run to complete.

        Args:
            ms_node (str): The MS node.

       Kwargs:
           assert_success (str): By default, will assert puppet is
                                 successfully triggered.

       Raises:
          AssertionError if a puppet run fails to start.
      """
        if assert_success:
            self.assertTrue(self.wait_for_puppet_idle(ms_node))
        else:
            self.wait_for_puppet_idle(ms_node)

        self.run_puppet_once(ms_node)

        if assert_success:
            self.assertTrue(self.wait_for_puppet_idle(ms_node))
        else:
            self.wait_for_puppet_idle(ms_node)

    def run_puppet_once(self, ms_node):
        """
        Clears cache and triggers a new run of puppet with the 'mco puppet
        runonce' command.

        Args:
            ms_node (str): The MS node.

        """
        clear_cache_cmd = "mco rpc puppetcache clean -I {0}".format(ms_node)
        self.run_command(ms_node, clear_cache_cmd, su_root=True)

        kick_puppet_cmd = "mco puppet runonce"
        self.run_command(ms_node, kick_puppet_cmd, su_root=True)

    def wait_for_puppet_idle(self, ms_node, node_hostname=None):
        """
        Waits for puppet to reach an idle state, meaning it has ended its
        current poll.

        Args:
           ms_node (str): The MS node which runs the puppet server.

        Kwargs:
           node_hostname (str): The hostname of the node which you wish
                                    to check has finished applying a
                                    catalog.

        Returns:
            bool. True if idle found or False if idle not found after puppet
              cycle interval has expired.
        """
        ##Timeout is interval * 3
        splay_limit = self.get_puppet_splaylimit(ms_node)
        puppet_timeout = self.get_puppet_interval(ms_node) * 3 + splay_limit
        puppet_timeout_mins = puppet_timeout / 60

        if node_hostname:
            search_str = '"{0}: Currently applying a catalog"'.format(
                                                                node_hostname)
            puppet_status = '/usr/bin/mco puppet status | '\
                            + '/bin/grep ' + search_str
        else:
            puppet_status = '/usr/bin/mco puppet status | '\
                            + '/bin/grep "Currently applying a catalog"'

        return self.wait_for_cmd(ms_node, puppet_status, 1,
                                 timeout_mins=puppet_timeout_mins,
                                 su_root=True, default_time=2)

    def wait_for_puppet_action(self, ms_node, node, check_cmd, expected_rc,
                               expected_stdout=None, su_root=False):
        """
        Waits for puppet to complete an action.

        Args:
           ms_node (str): The MS node which runs the puppet server.

           node (str): The node you want to check for action.

           check_cmd (str): The command to use to check for puppet changes
                            (e.g. grep command for a file).

           expected_rc (int): The return code to wait for.

        Kwargs:
           expected_stdout (str): Optionally an stdout to wait for in addition
                                  to the return code.

           su_root     (bool): Set to True if command must be run as root.

        Returns:
           bool. True if expected return code is reached before puppet poll
           or False otherwise.
        """
        self.log("info", "Waiting for puppet action")
        splay_limit = self.get_puppet_splaylimit(ms_node)
        puppet_interval_secs = self.get_puppet_interval(ms_node) + splay_limit

        #wait for 2 cycles at a maximum
        puppet_wait_mins = (puppet_interval_secs / 60) * 2

        # Kick puppet to run test faster
        #In some cases kick may fail so we don't assert return types.
        #If kick fails test is still valid but we have to actually wait for
        #puppets normal looping

        #Tmp removed due to authentication problems
        #kick_puppet = "/usr/bin/mco puppet runall 1"
        #self.run_mco_command(ms_node, kick_puppet)

        return self.wait_for_cmd(node, check_cmd, expected_rc, expected_stdout,
                                 puppet_wait_mins, su_root)

    def is_puppet_synched(self, node, puppetserver_hostname, fact):
        """
        Check if puppet facts are synched from peer node to server
        Args:
            node(str): Node for which we want to gather the facts
            puppetserver_hostname(str): hostname of node on which puppet
                                        server is deployed
            fact(str): Fact to check the presence of in the list of facts
        Returns(Bool): True if given fact is present on Puppet Server.
                        False otherwise
        """
        calculated_puppet_facts = self.run_command(puppetserver_hostname,
                                                   "{0} facts find {1} \
                                                   --terminus rest \
                                                   --server={2}".format(
                                                    test_constants.PUPPET_PATH,
                                                    node,
                                                    puppetserver_hostname))[0]
        return True if fact in "".join(calculated_puppet_facts) else False

    def backup_dir(self, node, filepath, backup_mode_cp=True,
                     backup_path='/tmp', restore_after_plan=False,
                   del_tar_at_restore=True):
        """
        Backs up a directory on the specified node.

        Args:
           node (str): The node you wish to perform the backup command on.

           filepath (str): The path of the directory that you wish to backup.

        Kwargs:
           backup_mode_cp  (bool): If set to False, will move the file\
              instead of making a copy.

           backup_path (str): The directory to backup to, by default tmp\
              will be used.

           restore_after_plan (bool): By default, set to False so files are\
              restored before cleanup plan runs. Override to True to restore\
              the files as the last cleanup step.

           del_tar_at_restore (bool): By default, will delete the contents of
           the tar dir before performing the restore to remove newly created
           files since backup was run.

        Returns:
           Throws exception if backup fails.
        """
        self.log("info", "Performing file backup")

        backup_dir_parts = filepath.split("/")
        final_index = len(backup_dir_parts) - 1

        if backup_dir_parts[final_index]:
            backup_dir = backup_dir_parts[final_index]
        else:
            backup_dir = backup_dir_parts[final_index - 1]

        if backup_mode_cp:
            success = self.cp_file_on_node(node, filepath, backup_path, "-r",
                                           add_to_cleanup=False, su_root=True,
                                           dir_cpy=True)
            backup_restore_path = "/".join(backup_dir_parts[:-1])
            backup_from_path = self.join_paths(backup_path, backup_dir)
        else:
            backup_restore_path = "/".join(backup_dir_parts[:-1])
            backup_from_path = self.join_paths(backup_path, backup_dir)
            success = self.mv_file_on_node(node, filepath, backup_path,
                                           su_root=True, add_to_cleanup=False)

        self.assertTrue(success, "Backup_failed")

        #Directory backup so we trim the actual directory we are restore to

        backup_restore_path = "/".join(backup_dir_parts[:-1])
        self.__add_to_backup_list(node, backup_restore_path,
                                  backup_from_path,
                                  restore_after_plan,
                                  del_tar_at_restore)

    ##FILE RELATED
    def get_file_modify_time(self, node, filename):
        """
        Returns an epoch timestamp of the last time the selected file was
        modified.

        Args:
           node (str): The node with the selected file.

           filename (str): The filename to check.

        Returns:
           int. Unix timestamp of modify time of file.
        """
        cmd = self.rhc.get_stat_cmd(filename, "-c %Y")

        stdout, _, returnc = self.run_command(node, cmd, su_root=True)

        self.assertEqual(0, returnc)

        return int(stdout[0])

    def generate_file(self, node, filepath, size_kb, add_to_cleanup=True):
        """
        Generates a file with random input on the specified node at the set
        filepath and configured size.

        Args:
            node (str): The filename of the node in question.

            filepath (str): The location where you want the file to exist.

            size_kb (int): The size of the requested file in KB.

        Kwargs:
            add_to_cleanup (bool): By default, deletes the file at the end of
            the test. Set to False if you want the file to persist.

        Returns:
            Throws assertion error if file creation fails.
        """
        bytes_in_kb = 1024

        cmd = \
        "/bin/dd if=/dev/urandom of={0} bs={1} \
            count={2}".format(filepath, bytes_in_kb, size_kb)

        std_out, std_err, rc = self.run_command(
            node, cmd, su_root=True)

        self.assertEquals(0, rc)
        self.assertNotEqual([], std_out)
        self.assertEquals([], std_err)

        if add_to_cleanup:
            self.__add_to_filepath_cleanup(node,
                                           filepath,
                                           su_root=True)

    def append_files(self, node, filepath1, filepath2):
        """
        Appends the two specified files together.

        Args:
           node (str): The filename of the node in question.

           filepath1 (str): The location you want to append to.

           filepath2 (str): The location where you want the file append to the\
                            1st file.

        Returns:
            Throws assertion error if append fails.
        """
        appendcmd = \
            "/bin/cat {0} >> \
            {1}".format(filepath2, filepath1)

        std_out, std_err, rc = self.run_command(
            node, appendcmd, su_root=True)
        self.assertEquals(0, rc)
        self.assertEquals([], std_out)
        self.assertEquals([], std_err)

    def backup_file(self, node, filepath, backup_mode_cp=True,
                    backup_path='/tmp', restore_after_plan=False,
                    assert_backup=True):
        """
        Moves the selected file to a backup path and then at the end of
        a test will move the file back to its original location.

        Args:
           node (str): The node you wish to perform the backup command on.

           filepath (str): The path of the file that you wish to backup.

        Kwargs:
           backup_mode_cp  (bool): If set to False, will move the file\
              instead of making a copy.

           backup_path (str): The directory to backup to, by default tmp\
              will be used.

           restore_after_plan (bool): By default, set to False so files are\
              restored before cleanup plan runs. Override to True to restore\
              the files as the last cleanup step.

           assert_backup (bool): If set to False, will not assert if backup\
              succeeds.

        Returns:
           bool. True if backup was successful or False otherwise.
        """
        self.log("info", "Performing file backup")
        #Check backup file exists
        backup_success = True

        if not self.remote_path_exists(node, filepath, su_root=True):
            self.log("error", "Cannot locate file {0} for backup" \
                         .format(filepath))
            backup_success = False

        else:

            #If backup fails return False
            if backup_mode_cp:
                if not self.cp_file_on_node(node, filepath, backup_path,
                                            su_root=True,
                                            add_to_cleanup=False):
                    backup_success = False
            else:
                if not self.mv_file_on_node(node, filepath, backup_path,
                                        su_root=True, add_to_cleanup=False):
                    backup_success = False

            if backup_success:
                #Infer filename of backed up file
                fileparts = filepath.split("/")
                filename = fileparts[len(fileparts) - 1]

                full_backup_path = self.join_paths(backup_path, filename)

                self.__add_to_backup_list(node, filepath, full_backup_path,
                                  restore_after_plan)
                self.log("info", "Successfully backed up {0}".format(filepath))

            if assert_backup:
                self.assertTrue(backup_success,
                                "Backup of file {0} failed, aborting test"\
                                    .format(filepath))

        return backup_success

    def __add_to_backup_list(self, node, filepath_orig, filepath_backup,
                             restore_after_plan,
                             del_target_at_restore=False):
        """
        Adds the passed filepaths to the list of backed up files to
        restore at the end of a test.

        Args:
           node (str): The node the backup exists on.

           filepath_orig (str): The filepath that needs to be restored to.

           filepath_back (str): The location of the backed up file.

           restore_after_plan (bool): By default, set to False so files are
                                      restored before cleanup plan runs.
                                      Override to True to restore the files
                                      as the last cleanup step.

       KwArgs:
          del_target_at_restore (bool): By default, set to False. If true, will
          do a delete on the path that was backed up before restoring the
          files.
       """
        backup_dict = dict()

        backup_dict["NODE"] = node
        backup_dict["TARGET_PATH"] = filepath_orig
        backup_dict["SOURCE_PATH"] = filepath_backup
        backup_dict["DEL"] = del_target_at_restore

        if restore_after_plan:
            self.backup_filelist_after_plan.append(backup_dict)
        else:
            self.backup_filelist.append(backup_dict)

    def assert_file_del_after_run(self, node, filepath):
        """
        This method will assert the specified file on the specified node
        no longer exists when the test cleanup has completed.

        Args:
           node (str): The node the backup exists on.

           filepath (str): The filepath that needs to be checked.
        """

        test_file = dict()
        test_file["NODE"] = node
        test_file["PATH"] = filepath

        self.files_to_check.append(test_file)

    def del_file_after_run(self, node, filepath,
                           wait_for_puppet=False):
        """
        Will delete the file on the specified node at the specified filepath
        after the test completes.

        Args:
           node (str): The node the backup exists on.

           filepath (str): The filepath that needs to be deleted.

           wait_for_puppet(str): If set to True, will wait a full puppet
           cycle before deleting file.
        """
        del_file = dict()

        del_file["NODE"] = node
        del_file["PATH"] = filepath
        del_file["PUPPET"] = wait_for_puppet

        self.del_file_list.append(del_file)

    def mv_file_on_node(self, node, current_path, new_path,
                        mv_args='', su_root=False,
                        add_to_cleanup=True):
        """Performs a mv command. If the file being moved is listed in
        autocleanup, the file path in cleanup will be updated.

        Args:
          node (str): The node you wish to perform the move command on.

          current_path (str): The current location of the item.

          new_path (str): The new path you wish to copy the item to.

        Kwargs:
          mv_args  (str): Arguments to pass to the mv command.

          su_root  (bool): Set to true to run command as root.

          add_to_cleanup (bool): Set to False if you don't want the file
                                 removed at the end of the test.

        Returns:
            bool. True if mv succeeds or False if mv fails.
        """
        #If the new filepath already exists we should not handle deletion
        if self.remote_path_exists(node, new_path):
            add_to_cleanup = False

        cmd = "/bin/mv {0} {1} {2}".format(mv_args, current_path, new_path)

        _, _, returnc = self.run_command(node, cmd, su_root=su_root)

        if returnc == 0 and add_to_cleanup:
            self.__update_cleanup_files(node, current_path, new_path, su_root)

        return returnc == 0

    def cp_file_on_node(self, node, current_path, new_path, cp_args='',
                        su_root=False, add_to_cleanup=True,
                        dir_cpy=False):
        """Performs a cp command. If the file being copied is listed in
        autocleanup and does not overwrite an existing file in copy, the
        new file will be deleted at end of the test.

        Args:
          node         (str): The node you wish to perform the cp command on.

          current_path (str): The current location of the item.

          new_path     (str): The new path you wish to copy the item to.

        Kwargs:
          cp_args        (str): Arguments to pass to the cp command.

          su_root        (bool): Set to true to run command as root.

          add_to_cleanup (bool): Set to False if you don't want the file\
             removed at the end of the test.

        Returns:
           bool. True if cp succeeds or False if cp fails.
        """
        #If the new filepath is a directory we should infer the filename from
        #original
        if not dir_cpy:
            if self.remote_path_exists(node, new_path, False):
                fileparts = current_path.split("/")
                orig_filename = fileparts[len(fileparts) - 1]
                new_path = self.g_util.join_paths(new_path, orig_filename)

            #if the new filepath exists we should not delete it at cleanup
            if self.remote_path_exists(node, new_path):
                add_to_cleanup = False

        cmd = "/bin/cp {0} {1} {2}".format(cp_args, current_path, new_path)

        _, _, returnc = self.run_command(node, cmd, su_root=su_root)

        if returnc == 0 and add_to_cleanup:
            self.__add_to_filepath_cleanup(node, new_path, su_root=su_root)

        return returnc == 0

    def copy_and_install_rpms(self, node, local_rpm_paths,
                              rpm_repo_path=None, add_to_cleanup=False):
        """
        Copies the list of RPMs passed to the specified server and installs
        them. This method should be used when installing LITP plugins.

        Args:
           node (str): The node to copy and install the RPMS to.

           local_rpm_paths (list): List of filepaths containing the RPMs.

        Kwargs:
           rpm_path (str): The path on the node to install the rpm to. If not\
              set, uses the main LITP repo directory.
              NOTE: Must be set if copying/installing to Managed Node.

           add_to_cleanup (bool): Set to True if you want the rpms removed\
              at the end of the test.

        Returns:
           bool. True if install is successful or False otherwise.
        """
        if self.get_node_att(node, 'nodetype') == 'management':
            self.log('info', 'Stopping puppet for RPM upgrade')
            self.stop_service(node, 'puppet')

        if rpm_repo_path:
            litp_pkg_dir = rpm_repo_path
        else:
            litp_pkg_dir = test_constants.LITP_PKG_REPO_DIR

            if self.get_node_att(node, 'nodetype') != 'management':
                self.assertTrue(rpm_repo_path,
                    "Must specify rpm_repo_path for managed nodes")

        # buld dictionary for transferring rpm files to the MS
        rpm_sftp_dict = [
            self.get_filelist_dict(local_rpm_path, litp_pkg_dir)
            for local_rpm_path in local_rpm_paths
        ]

        # parse RPM names from full paths in 'local_rpm_paths'
        rpm_names = [rpm_name.split("/")[-1] for rpm_name in local_rpm_paths]

        installed_rpm_names = []
        for rpm in local_rpm_paths:
            std_out, std_err, rc = self.run_command_local(
                self.rhc.get_package_name_from_rpm(rpm))
            self.assertEquals(0, rc)
            self.assertEquals([], std_err)
            self.assertEquals(1, len(std_out))

            installed_rpm_names.append(std_out[0])

        # get remote paths that the rpms will be installed to on the MS
        rpm_remote_fpaths = [
            os.path.join(litp_pkg_dir, rpm_name) for rpm_name in rpm_names
        ]

        # copy across the rpms
        for flist in rpm_sftp_dict:
            if not self.copy_filelist_to(node, [flist], True, False):
                return False

        # createrepo is only available on the MS.
        if self.get_node_att(node, 'nodetype') == 'management':
            # run 'createrepo' command
            _, stderr, rcode = self.run_command(
                node, self.rhc.get_createrepo_cmd(litp_pkg_dir),
                su_root=True
            )

            if rcode != 0 or stderr != []:
                return False

        # install the rpms
        _, stderr, rcode = self.run_command(
            node,
            self.rhc.get_yum_install_cmd(rpm_remote_fpaths),
            su_root=True
        )

        if rcode != 0 or stderr != []:
            return False

        # restart the litpd service. Only on MS.
        if self.get_node_att(node, 'nodetype') == 'management':
            self.start_service(node, 'puppet')
            self.restart_litpd_service(node)

        if add_to_cleanup:
            if node not in self.rpms_to_delete:
                self.rpms_to_delete[node] = list()
            self.rpms_to_delete[node].extend(installed_rpm_names)
            for path in rpm_remote_fpaths:
                self.del_file_after_run(node, path)

        #self.start_service(node, 'puppet')

        return True

    def install_rpm_on_node(self, node, pkg_name):
        """
        Performs a yum install on the passed RPM.

         Args:
           node (str): The node which has the package to be installed.

           pkg_name (str/list): The name of a RPM package or a list of
                                names of rpm packages to install.

        Returns:
           bool. True if the package is installed without error. If flag set
           will output list, list, int. (stdout, stderr and rc.)
        """

        if isinstance(pkg_name, list):
            cmd = self.rhc.get_yum_install_cmd(pkg_name)
        else:
            cmd = self.rhc.get_yum_install_cmd([pkg_name])

        stdout, stderr, return_code = self.run_command(node, cmd,
                                                       su_root=True)

        self.assertEquals([], stderr)
        self.assertEquals(0, return_code)

        return stdout, stderr, return_code

    def remove_rpm_on_node(self, node, pkg_name):
        """
        Performs a yum remove on the passed RPM.

         Args:
           node (str): The node which has the package to be removed.

           pkg_name (str/list): The name of a RPM package or a list of
                                names of rpm packages to remove.

        Returns:
           list, list, int. (stdout, stderr and rc.)
        """

        if isinstance(pkg_name, list):
            cmd = self.rhc.get_yum_remove_cmd(pkg_name)
        else:
            cmd = self.rhc.get_yum_remove_cmd([pkg_name])

        stdout, stderr, return_code = self.run_command(node, cmd, su_root=True)

        self.assertEquals([], stderr)
        self.assertEquals(0, return_code)

        return stdout, stderr, return_code

    def upgrade_rpm_on_node(self, node, pkg_name):
        """
        Performs a yum upgrade on the passed RPM.

         Args:
           node (str): The node which has the package to be upgraded.

           pkg_name (str/list): The name of a RPM package or a list of
                                names of rpm packages to upgrade.

        Returns:
           list, list, int. (stdout, stderr and rc.)
        """

        if isinstance(pkg_name, list):
            cmd = self.rhc.get_yum_upgrade_cmd(pkg_name)
        else:
            cmd = self.rhc.get_yum_upgrade_cmd([pkg_name])

        stdout, stderr, return_code = self.run_command(node, cmd, su_root=True)

        self.assertEquals([], stderr)
        self.assertEquals(0, return_code)

        return stdout, stderr, return_code

    def check_pkgs_installed(self, node, pkg_names, su_root=True):
        """
        Checks if the passed list of packages are installed on the system
        using rpm -qa and a grep command. If the grep matches less lines than
        the length of the list of packages passed in, it is assumed a package
        is missing and False will be returned.

        Args:
           node (str): The node you wish to run the command on.

           pkg_names (list): The package names you wish to test.

        Kwargs:
           su_root (bool): Defaults to True. Set to False to run command as
           current default user.

        Returns:
           bool. True if all the packages are installed or False otherwise.
        """
        cmd = self.rhc.check_pkg_installed(pkg_names)

        stdout, stderr, returnc = self.run_command(node, cmd,
                                                   su_root=su_root)

        self.assertEqual([], stderr)

        ##If return code is 0 or the length of the
        ##returned grep is less than list of packages passed in
        if returnc != 0 \
                or len(stdout) != len(pkg_names):
            return False

        return True

    def check_repos_on_node(self, node, repo_names, su_root=True):
        """
        Checks if the passed list of repos are on the node using 'yum
        repolist enabled' and a grep command with repo names.
        If the grep matches less lines than the length of the list of repos
        passed in, it is assumed a repo is missing and False will be returned.

        Args:
           node (str): The node you wish to run the command on.

           repo_names (list): The repo names you wish to test.

        Kwargs:
           su_root (bool): Defaults to True. Set to False to run command as
           current default user.

        Returns:
           bool. True if all the repos are present or False otherwise.
        """
        cmd = self.rhc.check_repo_cmd(repo_names)

        stdout, stderr, returnc = self.run_command(node, cmd,
                                                   su_root=su_root)
        self.assertEqual([], stderr)

        ##If return code is 0 or the length of the
        ##returned grep is less than list of packages passed in
        if returnc != 0 \
                or len(stdout) != len(repo_names):
            return False

        return True

    def get_filelist_dict(self, local_filepath, remote_filepath):
        """Returns a dictionary based on the local and remote paths
        passed to it.

        Args:
          local_filepath (str): The local filepath of the file to copy.

          remote_filepath (str): The filepath on the remote machine you wish to
                                 copy to.

        Returns:
           dict.  {'local_path': local_filepath parameter,
                  'remote_path': remote_filepath parameter}
        """
        return self.g_util.get_filelist_dict(local_filepath, remote_filepath)

    def copy_filelist_to(self, node, filelist, root_copy=False,
                         add_to_cleanup=True, file_permissions=0777):
        """Copies a list of files to the specified node.

        Args:
           node (str): The node to copy the files to.

           filelist (list): A list of dictionary pairs. Created by\
              get_filelist_dict which contains the local and remote paths to\
              copy to.

        Kwargs:
           root_copy (bool): If set to True, copies all files with root\
              privileges.

           add_to_cleanup (bool): If set to True (default), adds files to\
              cleanup list for deletion later.

           file_permissions (int): Permissions to set for copied file using\
              chmod notation. Defaults to 0777.

        Returns:
           bool. If all copies succeed returns True, otherwise returns False.
        """
        all_success = True

        for file_item in filelist:
            successful_copy = self.copy_file_to(node, file_item['local_path'],
                                                file_item['remote_path'],
                                                root_copy,
                                                add_to_cleanup,
                                                file_permissions)

            if not successful_copy:
                self.log("error",
                         "Failed to copy local path {0} to remote path {1}"\
                             .format(file_item['local_path'],
                                     file_item['remote_path']))

                if all_success:
                    all_success = False

        return all_success

    def copy_file_to(self, node, local_filepath, remote_filepath,
                     root_copy=False, add_to_cleanup=True,
                     file_permissions=0777):
        """Copy a file to the specified node.

        Args:
           node            (str): Node to copy file to.

           local_filepath  (str): Path of the local file/directory to copy.

           remote_filepath (str): Path on node to copy to.

        Kwargs:
           root_copy      (bool): Set to True to copy as the root user.

           add_to_cleanup (bool): By default, deletes all files copied\
              after test. Set to False to prevent auto-deletion.

           file_permissions (int): Permissions to set for copied file using\
              chmod notation. Defaults to 0777.

        Raises:
           IOError if filepaths are invalid.

        Returns:
           bool. True if copy is successful or False otherwise.
        """
        if os.path.exists(local_filepath):

            real_node = self.get_node_list_by_name(node)[0]

            if real_node:
                ####
                self.log(
                    "info",
                    "Copying: {0} to remote path {1} (root_copy={2})"\
                        .format(local_filepath, remote_filepath, root_copy))

                #If filename is not provied for remote path use the filename
                #of the local file
                if self.remote_path_exists(node, remote_filepath, False,
                                           su_root=root_copy):
                    local_fileparts = local_filepath.split("/")
                    local_filename = local_fileparts[len(local_fileparts) - 1]

                    remote_filepath = \
                        self.g_util.join_paths(remote_filepath,
                                               local_filename)

                ##if peer node cannot connect directly as root
                #so copy as non-root to tmp and then move file
                if self.get_node_att(node, 'nodetype') != 'management' \
                        and root_copy:
                    real_node.copy_file(local_filepath, '/tmp/tmp_file',
                                        False, file_permissions)
                    self.mv_file_on_node(node, '/tmp/tmp_file',
                                         remote_filepath,
                                         su_root=True,
                                         add_to_cleanup=False)

                ####
                else:
                    real_node.copy_file(local_filepath, remote_filepath,
                                        root_copy, file_permissions)

                if add_to_cleanup:
                    self.__add_to_filepath_cleanup(node,
                                                   remote_filepath,
                                                   su_root=root_copy)
                return True

        else:
            self.log("error", "Cannot copy {0}, local path does not exist"
                     .format(local_filepath))

        return False

    def download_file_from_node(self, node, remote_filepath, local_filepath,
                                root_copy=False):
        """Download a file from a node to gateway.

        Args:
            node (str): Node from which file download wanted.

            remote_filepath  (str): Path of the remote file on node.

            local_filepath (str): Path on gateway node to copy to.

        Kwargs:
            root_copy (bool): Set to True to copy as the root user.

        Raises:
            AssertionError (Exception): If contents of file at source path
            cannot be acquired or if destination file cannot be created.

        Returns:
           bool. True if download is successful or False otherwise.
        """
        real_node = self.get_node_list_by_name(node)[0]

        if real_node:
            self.log(
                "info",
                "Copying: {0} to local path {1} (root_copy={2})"\
                    .format(remote_filepath, local_filepath, root_copy))

            if self.remote_path_exists(node, remote_filepath, True,
                                       su_root=root_copy):

                ##if peer node, cannot connect directly as root
                #so copy to tmp and then download file
                if self.get_node_att(node, 'nodetype') != 'management' \
                        and root_copy:
                    self.cp_file_on_node(node, remote_filepath,
                                         '/tmp/tmp_file',
                                         su_root=True,
                                         add_to_cleanup=True,
                                         dir_cpy=False)
                    real_node.download_file(local_filepath, '/tmp/tmp_file',
                                            False)
                    return True
                else:
                    real_node.download_file(local_filepath, remote_filepath,
                                            root_copy)

                    return True
            else:
                self.log("error", "Cannot copy {0}, remote path does not exist"
                         .format(remote_filepath))
                return False

    def create_dir_on_node(self, node, remote_filepath,
                           su_root=False, add_to_cleanup=True):
        """Create a file/directory to the specified node.

        Args:
           node            (str): Node to create directory on.

           remote_filepath (str): Full path of new directory to create.

        Kwargs:
           su_root        (bool): Set to True to create directory as\
              root user.

           add_to_cleanup (bool): By default, directory is deleted at end\
              of test. Set to False to prevent cleanup.

        Returns:
           bool. True if mkdir is successful or False otherwise.
        """

        cmd = "/bin/mkdir {0}".format(remote_filepath)

        _, stderr, retc = self.run_command(node, cmd,
                                           su_root=su_root)

        if retc != 0:
            self.log("error", "Failed to perform directory creation {0}" \
                         .format(stderr))
            return False
        else:
            if add_to_cleanup:
                self.__add_to_filepath_cleanup(node,
                                               remote_filepath,
                                               su_root=su_root)
            return True

    def list_dir_contents(self, node, path, su_root=False, grep_args=None):
        """Provides a list of the directory contents.

        Args:
           node     (str): Node to use.

           path     (str): Directory to list the contents of.

        Kwargs:
           su_root (bool): Set to True if directory needs root permissions.

           grep_args (str): If a value is provided, this will be passed to a
                            grep pipe to filter the filelist.

        Raises:
           AssertionError (Exception): If the ls command reports an error
                                       (such as directory does not exist).

        Returns:
           list. Returns a list of items returned from the ls command.
        """
        success = True
        list_path_cmd = "/bin/ls -1 {0}".format(path)

        if grep_args:
            list_path_cmd = list_path_cmd +\
                " | /bin/grep {0}".format(grep_args)

        stdout, stderr, exit_code = self.run_command(node, list_path_cmd,
                                                     su_root=su_root)

        #If we are using a grep it will override exit code so we also
        #check stderr
        if stderr != [] and exit_code != 0:
            success = False

        self.assertTrue(success, "Error reported running command: {0}"\
                            .format(stderr))

        return stdout

    def list_dir_contents_local(self, path, grep_args=None):
        """Provides a list of the directory contents.

        Args:
           path     (str): Directory to list the contents of.

        Kwargs:
           grep_args (str): If a value is provided, this will be passed to a
                            grep pipe to filter the filelist.

        Raises:
           AssertionError (Exception): If the ls command reports an error
                                       (such as directory does not exist).

        Returns:
           list. Returns a list of items returned from the ls command.
        """
        success = True
        list_path_cmd = "/bin/ls -1 {0}".format(path)

        if grep_args:
            list_path_cmd = list_path_cmd +\
                " | /bin/grep {0}".format(grep_args)

        stdout, stderr, exit_code = self.run_command_local(list_path_cmd)

        #If we are using a grep it will override exit code so we also
        #check stderr
        if stderr != [] and exit_code != 0:
            success = False

        self.assertTrue(success, "Error reported running command: {0}"\
                            .format(stderr))

        return stdout

    def check_repo_url_exists(self, node, url):
        """Checks if a URL is reachable from a node.

        Args:
           node      (str): The node to run the command on.

           url       (str): URL to check.

        Returns:
            bool. Returns True if repo exists, False if it doesn't.
        """
        curl_cmd = "/usr/bin/curl -Is '{0}' | grep 'HTTP/1.1 200 OK'"\
                                                                .format(url)
        stdout, _, returnc = self.run_command(node, curl_cmd,
                                              su_root=True)

        if stdout == [] or returnc != 0:
            return False
        if returnc == 0 and "HTTP/1.1 200 OK" in stdout[0]:
            return True

        return False

    def get_file_len(self, node, filepath):
        """Returns the number of lines for the specified file.

        Args:
           node      (str): The node to run the command on.

           filepath  (str): The file to check.

        Returns:
            int. Returns the number of lines in the file.
        """
        log_pos_cmd = self.rhc.get_file_len_cmd(filepath)
        stdout, stderr, returnc = self.run_command(node, log_pos_cmd,
                                                   su_root=True)

        if returnc != 0 or stderr != []:
            return None

        if stdout:
            file_len = int(stdout[0])

        return file_len

    def get_file_contents(self, node, filepath, tail=None,
                          su_root=False, assert_not_empty=False):
        """Returns the contents of the file at the given filepath,
        optionally tailed if a tail parameter is provided.

        Args:
           node (str): The node to find the file on.

           filepath (str): The filepath of the file.

        Kwargs:
          tail   (int): If set will tail the file by this number, otherwise
                         returns the entire file.

          su_root (bool): If set, runs the command as root.

        Returns:
            list. The contents of the file, optionally tailed.
        """
        if tail:
            file_cmd = "tail -n {0} {1}".format(tail, filepath)
        else:
            file_cmd = "cat {0}".format(filepath)

        #TMP workaround while cat of file with no \r is being investigated
        if su_root and \
                self.get_node_att(node, 'nodetype') == 'management':
            root_pw = self.get_node_att(node, 'rootpw')
            stdout, stderr, returnc = self.run_command(node, file_cmd,
                                                       'root', root_pw)

        else:
            stdout, stderr, returnc = self.run_command(node, file_cmd,
                                                       su_root=su_root)

        ##If error accessing file fail assertion.
        self.assertEquals([], stderr)
        self.assertEquals(0, returnc)

        if assert_not_empty:

            self.assertNotEqual([], stdout)

        return stdout

    def get_file_contents_local(self, filepath, tail=None):
        """Returns the contents of the file at the given local filepath,
        optionally tailed if a tail parameter is provided.

        Args:
           filepath (str): The filepath of the file.

        Kwargs:
          tail   (int): If set, will tail the file by this number, otherwise
                         returns the entire file.

        Returns:
            list. The contents of the file, optionally tailed.
        """
        if tail:
            file_cmd = "tail -n {0} {1}".format(tail, filepath)
        else:
            file_cmd = "cat {0}".format(filepath)

        stdout, stderr, returnc = self.run_command_local(file_cmd)

        ##If error accessing file fail assertion.
        self.assertEquals([], stderr)
        self.assertEquals(0, returnc)

        return stdout

    # Group 9 CLI Related (which require node connections)
    def is_itemtype_registered(self, ms_node, itemtype_name):
        """
        Checks if the named item type exists in the registered itemtype
        list shown by calling show on the /item-type path.

        Args:
           ms_node (str): The MS node with the model.

           itemtype_name (str): The name of the item type.

        Returns:
            bool. True if item type is registered or False otherwise.
        """
        all_item_types = self.get_all_itemtypes(ms_node)

        if itemtype_name in all_item_types:
            return True

        return False

    def get_all_itemtypes(self, ms_node):
        """
        Gets a list of all itemtypes registered under the itemtypes path.

        Args:
           ms_node (str): The MS node with the model in question.

        Returns:
            list. A list of all item types.
        """
        item_list = list()
        item_types_path = "/item-types"

        stdout, _, _ = self.execute_cli_show_cmd(ms_node, item_types_path)

        for line in stdout:
            if 'name:' in line:
                item_name = line.split(':')[1].strip()
                item_list.append(item_name)

        return item_list

    @staticmethod
    def increment_ip(ip_value):
        """
        Increments the passed IP by one.

        Args:
           ip_value (str): An ipv4 format IP.

        Returns:
          str. The ip incremented by 1. So 10.10.10.10
          will return as 10.10.10.11.
        """
        #split ip in parts
        ip_parts = ip_value.split(".")

        #get final value and increment
        final_part = int(ip_parts[len(ip_parts) - 1].strip())
        incremented_part = final_part + 1

        #reset final part to increment value and return
        ip_parts[len(ip_parts) - 1] = str(incremented_part)

        return ".".join(ip_parts)

    def get_fs_size_mb(self, ms_node, fs_url):
        """
        Get the size in Mb of the file system.

        Args:
           ms_node (str): The node with the deployment tree.

           fs_url (str): The LITP URL of the file system.

        Returns:
            str. The size of the file system in Mb.
        """
        fs_props = \
        self.get_props_from_url(ms_node, fs_url)
        fs_size = fs_props["size"]

        if "G" in fs_size:
            return self.sto.convert_gb_to_mb(fs_size)
        else:
            return fs_size[:-1]

    def get_local_disk_uuid(self, node, vg_name):
        """
        Will query the requested node with factor -p to
        find the correct uuid in a LITP friendly format (600...).

        Args:
           node (str): The node where you wish to find the uuid.

           vg_name (str): The name of the vg for which you want the uuid.

        returns:
           str. The uuid of the disk as a string or None if uuid cannot
           be found.
        """
        self.log("info", "Calculating disk UUID")
        find_pv_name = "/sbin/pvs --options pv_name,vg_name " +\
            " | /bin/grep {0} ".format(vg_name) +\
            "| awk '{print $1}'"

        stdout, stderr, returnc = self.run_command(node, find_pv_name,
                                                   su_root=True)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        self.assertNotEqual([], stdout)

        find_uuid_cmd = "/usr/bin/facter -p | /bin/grep {0}".format(stdout[0])

        stdout, stderr, returnc = \
            self.run_command(node, find_uuid_cmd, su_root=True)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        self.assertNotEqual([], stdout)

        for line in stdout:
            if 'disk_6' in line:
                uuid = line.split('_')[1]
                self.log("info", "Return UUID {0}".format(uuid))
                return uuid

        return None

    def get_vg_info_on_node(self, node):
        """Returns key information from running vgdisplay on the selected node
        as a dict.

        Args:
           node (str): The node you wish to query with vgdisplay.

        Returns:
           dict. Dictionary of dictionaries each representing a volume group
           and indexed by volume group name.

           |       Example:
           |     {'vg_root':
           |          {'VG_SIZE_ALLOC_GB': '314.00',
           |            'VG_SIZE_FREE_GB': '244.24',
           |            'VG_SIZE_GB': '558.24',
           |            'VG_UUID': 'ZgI1jg-Vu4W-w0mc-dKCT-wMWp-A4H8-hL9mWs',
           |            'VG_STATUS': 'resizable'}
           |     }
        """
        query_cmd = "/sbin/vgdisplay"

        vgsize_key = "VG_SIZE_GB"
        vgsize_alloc_key = "VG_SIZE_ALLOC_GB"
        vgsize_free_key = "VG_SIZE_FREE_GB"
        vg_uuid_key = "VG_UUID"
        vgstatus_key = "VG_STATUS"

        stdout, stderr, returnc = self.run_command(node, query_cmd,
                                                   su_root=True)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)

        vg_item = dict()

        for line in stdout:
            if 'VG Name' in line:
                name = line.split('Name')[1].strip()
                vg_item[name] = dict()
                continue

            if 'VG Status' in line:
                status = line.split('Status')[1].strip()
                vg_item[name][vgstatus_key] = status
                continue

            if 'VG Size' in line:
                size = line.split('Size')[1].strip().split()[0]
                vg_item[name][vgsize_key] = size
                continue

            if 'Alloc PE' in line:
                size_alloc = line.split('Size')[1].strip().split()[2]
                vg_item[name][vgsize_alloc_key] = size_alloc
                continue

            if 'Free  PE' in line:
                size_free = line.split('Size')[1].strip().split()[2]
                vg_item[name][vgsize_free_key] = size_free
                continue

            if 'VG UUID' in line:
                uuid = line.split('UUID')[1].strip()
                vg_item[name][vg_uuid_key] = uuid
                continue

        return vg_item

    def get_lv_info_on_node(self, node):
        """
        Returns key information from running lvdisplay on the selected node
        as a dict.

        Args:
           node (str): The node you wish to query with lvdisplay.

        Returns:
           dict. Dictionary of dictionaries each representing a logical volume
           and index by volume name.

           |    Example:
           |        {
           |            'lv_var':
           |              {
           |                  'LV_SIZE_GB': '100.00',
           |                  'LV_PATH': '/dev/vg_root/lv_var',
           |                  'LV_STATUS': 'available',
           |                  'VG_NAME': 'vg_root',
           |                  'LV_UUID': 'VJgUYt-AtWS-PcUq-Br1R-NKlg-dwSf-\
                              YCzyXx',
           |                  'LV_SNAP_STATUS': 'source of \
                              litp_lv_var_snapshot [active]',
           |              },
           |            'litp_lv_home_snapshot':
           |              {
           |                  'LV_SIZE_GB': '6.00',
           |                  'LV_PATH': '/dev/vg_root/litp_lv_home_snapshot',
           |                  'LV_STATUS': 'available',
           |                  'VG_NAME': 'vg_root',
           |                  'LV_UUID': 'rSg0Zt-nYJb-ac9h-EyYm-njxr-DqLl-\
                              O7TOrW'
           |                  'LV_SNAP_STATUS': 'active destination for \
                               lv_home',
           |              }
           |        }
        """
        query_cmd = "/sbin/lvdisplay"

        lvpath_key = "LV_PATH"
        lvsize_key = "LV_SIZE_GB"
        lvstatus_key = "LV_STATUS"
        lvuuid_key = "LV_UUID"
        lv_vg_key = "VG_NAME"
        lvsnapstatus_key = "LV_SNAP_STATUS"
        cow_table_size_key = "COW_TABLE_SIZE_MB"

        stdout, stderr, returnc = self.run_command(node, query_cmd,
                                                   su_root=True)
        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        stdout_mb, stderr_mb, returnc_mb = self.run_command(node,
                                                   query_cmd + " --units M",
                                                   su_root=True)
        self.assertEqual([], stderr_mb)
        self.assertEqual(0, returnc_mb)

        lv_item = dict()

        skip_flag = False
        for line in stdout:
            if not skip_flag:
                if 'LV Path' in line:
                    path = line.split('Path')[1].strip()
                    continue

                if 'LV Name' in line:
                    name = line.split('Name')[1].strip()
                    lv_item[name] = dict()
                    lv_item[name][lvpath_key] = path
                    continue

                if 'LV Size' in line:
                    size = line.split('Size')[1].strip().split()[0]
                    lv_item[name][lvsize_key] = size
                    continue

                if 'LV Status' in line:
                    size = line.split('Status')[1].strip()
                    lv_item[name][lvstatus_key] = size
                    continue

                if 'LV UUID' in line:
                    uuid = line.split('UUID')[1].strip()
                    lv_item[name][lvuuid_key] = uuid
                    continue

                if 'VG Name' in line:
                    vg_name = line.split('Name')[1].strip()
                    lv_item[name][lv_vg_key] = vg_name
                    continue

                # The LV snapshot status may be split over two lines:
                # E.G. LV snapshot status     source of
                #      litp_lv_root_snapshot [active]
                if 'LV snapshot status' in line:
                    lv_snap_status = line.split('status')[-1].strip()
                    if "source of" in lv_snap_status:
                        skip_flag = True
                        continue
                    else:
                        lv_item[name][lvsnapstatus_key] = lv_snap_status
                        continue
            else:
                lv_snap_status = line.split('status')[-1].strip()
                lv_item[name][lvsnapstatus_key] = "source of {0}"\
                                                  .format(lv_snap_status)
                skip_flag = False
                continue

        for line in stdout_mb:
            if 'LV Name' in line:
                name = line.split('Name')[1].strip()
                if name not in lv_item.keys():
                    lv_item[name] = dict()
                continue

            if "COW-table size" in line:
                size = line.split('size')[1].split("MB")[0].strip()
                lv_item[name][cow_table_size_key] = size
                continue

        return lv_item

    def get_pv_info_on_node(self, node):
        """
        Returns key information from running pvdisplay on the selected node
        as a dict.

        Args:
           node (str): The node you wish to query with pvdisplay.

        Returns:
           dict. Dictionary of dictionaries each representing a physical volume
           and index by volume name.

           |    Example:
           |    {'/dev/sda2':
           |        {'PV_UUID': 'zSOKWD-NrTc-gXZO-unKh-z5bR-mcWT-ZRSnbv',
           |         'PV_SIZE': '175.51 GiB / not usable 3.00 MiB',
           |         'VG_NAME': 'vg_root'}
           |    }
        """
        query_cmd = "/sbin/pvdisplay"

        vgname_key = "VG_NAME"
        pvsize_key = "PV_SIZE"
        pvuuid_key = "PV_UUID"

        stdout, stderr, returnc = self.run_command(node, query_cmd,
                                                   su_root=True)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)

        pv_item = dict()

        for line in stdout:
            if 'PV Name' in line:
                name = line.split('Name')[1].strip()
                pv_item[name] = dict()
                continue

            if 'VG Name' in line:
                vgname = line.split('Name')[1].strip()
                pv_item[name][vgname_key] = vgname
                continue

            if 'PV Size' in line:
                size = line.split('Size')[1].strip()
                pv_item[name][pvsize_key] = size
                continue

            if 'PV UUID' in line:
                uuid = line.split('UUID')[1].strip()
                pv_item[name][pvuuid_key] = uuid
                continue

        return pv_item

    def get_min_vxvm_snap_size(self, ms_node,
                               file_system_path):
        """
        Queries the model and returns the minimum allowed
        snap size for a VXVM disk. VXVM requires at least 13MB
        to perform any snapshotting so the min allowed snapsize is
        calculated based on the size of current disks configured.

        Args:
           ms_node (str): The node with the deployment tree.

           file_system_path (str): The path to the selected file system.

        Return:
          int. The min allowed snapsize for the VXVM disks.
        """
        lowest_vxvm_size = 13
        mb_size = self.get_fs_size_mb(ms_node, file_system_path)
        print "SIZE MB", mb_size
        unrounded_size = float((float(lowest_vxvm_size) / \
                                   + float(mb_size)) * 100)

        rounded_size = math.ceil(unrounded_size)

        return int(rounded_size)

    def get_storage_profile_paths(self, ms_node, profile_driver="lvm", \
                path_url="/infrastructure"):
        """
        Returns paths for storage profile in the system filtered by the passed
        profile driver type.

        Args:
            ms_node (str): The node in use.

            profile_driver (str): The type of storage profile you are looking
                                  for (e.g. 'lvm' or 'vxvm').

            path_url (str): URL to search under, default is given.

        Returns:
            list. List of all storage profile paths of that type.
        """
        filtered_profiles = list()

        storage_profiles = self.find(ms_node, path_url,
                                     "storage-profile", True)

        for path in storage_profiles:
            volume_driver = self.execute_show_data_cmd(ms_node,
                                                       path, "volume_driver")

            if profile_driver in volume_driver:
                filtered_profiles.append(path)

        return filtered_profiles

    def get_create_node_deploy_cmds(self, ms_node, node_name="node_99",
                                    system_path="/",
                                    system_type="system", hostname="mn99",
                                    mac_addr="BB:BB:BB:BB:BB:BB",
                                    device_name=None,
                                    os_profile_name=None,
                                    management_network=None,
                                    create_system=True):
        """Queries the current system using find and constructs a list of
        commands making use of existing system resources to create an
        additional peer node in the deployment.
        N.B.: The command list returned does not contain create or run plan.

        Args:
           ms_node           (str): The MS node you intend to run these
                                    deployment cmds on.

        Kwargs:
           node_name         (str): The name used in the URL tree for the node.

           system_path       (str): The path to the system you wish to link to.

           system_type       (str): The type of the system to be created or
                                    linked to.

           hostname          (str): The hostname for the node.

           mac_addr          (str): The mac address for the nodes network card.
                                    Set this if you intend to run the plan and
                                    PXE boot a node with matching address.

           device_name       (str): The device to use for your node (e.g. eth0)


           os_profile_name   (str): Set this to link nodes to your os profile,
                                    otherwise will search the tree
                                    to find a profile to use.

           management_network (str): Set this to link to your own management
                                     network otherwise will search the
                                     tree for a management network.

           create_system      (str): Set to False if you wish to link to an
                                     existing system matching the system name
                                     parameter instead of creating a new system
                                     of that name.

        Returns:
            list. A list of LITP commands to run in order to create the
                node in the LITP tree.
        """
        # 0. Fetch require parameters and URLs
        deployment_cmds = list()
        # 0a. Get the nodes collection url
        cluster_url = self.find(ms_node, "/deployments",
                                "cluster", False)[0]
        if not self.cluster_created:
            deployment_cmds.append(\
                self.cli.get_create_cmd(cluster_url + "/tmp",
                                        "cluster"))
            self.cluster_created = True

        nodes_url = cluster_url + "/tmp/nodes"

        # 0b. Get the os profile from the current system state
        os_url = self.find(ms_node, "/software",
                           "os-profile")[0]

        if not os_profile_name:
            os_profile_name = self.get_props_from_url(ms_node, os_url,
                                                      "name")

        # 0c. Get network url
        net_urls = self.find(ms_node, "/infrastructure",
                                "network")

        # get device name
        if not device_name:
            device_name = "eth0"

        # get default route
        default_route_path = None
        route_urls = self.find(ms_node, "/infrastructure", "route")
        for route_url in route_urls:
            route = self.get_props_from_url(ms_node, route_url)
            if route["subnet"] == "0.0.0.0/0":
                default_route_path = route_url

        # get management network
        if not management_network:
            for net_url in net_urls:
                network = self.get_props_from_url(ms_node, net_url)
                if network["litp_management"] == "true":
                    management_network = network["name"]
                    break

        # get storage profile url
        stor_pro_url = self.get_storage_profile_paths(ms_node)[0]

        # If boolean set in parameter create the system otherwise assume the
        # system already exists
        if create_system:
            system_url = self.find(ms_node, "/infrastructure",
                                   "system", False)
            system_url = system_url[0]

            # 1a. Create system
            system_path = self.join_paths(system_url,
                                              "system_{0}".format(node_name))

            props = "system_name='MNTEST'"
            deployment_cmds.append(self.cli.get_create_cmd(system_path,
                                                           system_type, props))

            # 1b. Add all disks in storage profile to new system
            #Get physical disk paths
            physical_paths = self.find(ms_node, stor_pro_url,
                                      "physical-device")

            disk_count = 0
            for physical_path in physical_paths:

                physical_device_name = self.get_props_from_url(ms_node,
                                                               physical_path,
                                                               "device_name")

                disk_url = self.join_paths(system_path,
                                           "/disks/disk{0}".format(disk_count))

                if disk_count == 0:
                    props = "name={0} size=100G bootable=true "\
                        .format(physical_device_name) + \
                        "uuid='ee7cf0a0-1922-401b-a1ae-6ec9261484c{0}'"\
                        .format(disk_count)
                else:
                    props = "name={0} size=100G bootable=false "\
                        .format(physical_device_name) + \
                        "uuid='ee7cf0a0-1922-401b-a1ae-6ec9261484c{0}'"\
                        .format(disk_count)

                deployment_cmds.append(self.cli.get_create_cmd(disk_url,
                                                               "disk", props))
                disk_count += 1

        # 3a. Create node
        full_node_url = \
            self.join_paths(nodes_url, node_name)
        props = "hostname='{0}'".format(hostname)
        deployment_cmds.append(self.cli.get_create_cmd(full_node_url,
                                                       "node", props))

        ##3aa Link to ip_route
        ip_route_link_url = self.join_paths(full_node_url, "/routes/r1")
        deployment_cmds.append(self.cli.get_inherit_cmd(ip_route_link_url,
                                                     default_route_path))

        # 3b. Link system
        system_url = self.join_paths(full_node_url, "/system")
        #props = "system_name='{0}'".format(system_name)
        deployment_cmds.append(self.cli.get_inherit_cmd(system_url,
                                                        system_path))
        # 3c. Link os
        os_url_node = self.join_paths(full_node_url, "/os")
        deployment_cmds.append(self.cli.get_inherit_cmd(os_url_node,
                                                        os_url))
        # 3f. Link storage profile
        store_pro_url_node = self.join_paths(full_node_url, "/storage_profile")
        deployment_cmds.append(self.cli.get_inherit_cmd(store_pro_url_node,
                                                        stor_pro_url))

        # 3d. Link network interface
        if_url = self.join_paths(full_node_url, "/network_interfaces/if0")
        ip_addr = self.get_free_ip_by_net_name(ms_node, management_network)
        # At least one IP must be assigned to the management network
        props = "device_name='{0}' macaddress='{1}' " \
            "ipaddress='{2}' network_name='{3}'".\
            format(device_name, mac_addr, ip_addr, management_network)
        deployment_cmds.append(self.cli.get_create_cmd(if_url, "eth", props))

        return deployment_cmds

    def get_current_plan_state(self, node, full_show=False):
        """Returns the status of the currently running commands.

        Args:
         node      (str): The MS node you intend to test.

        Kwargs:
         full_show (bool): If set to True, does not tail the show_plan
                           so that logs have the full plan output.

        Returns:
            int. An integer corresponding to the status of the
                plan as defined in test_constants.
        """
        if full_show:
            show_pln_cmd = self.cli.get_show_plan_cmd()
            stdout, stderr, exit_code = self.run_command(node,
                                                     show_pln_cmd)
            if stderr != [] or exit_code != 0:
                return test_constants.CMD_ERROR

            stdoutlen = len(stdout)
            if stdoutlen != 0:
                #assume status is always on the last line
                plan_status = stdout[stdoutlen - 1]
            else:
                self.log("info", "Output returned from show_plan is empty")
                return test_constants.CMD_ERROR

        else:
            plan_status = str(self.get_props_from_url(node, "/plans/plan",
                            filter_prop="state", log_output=True,
                            show_option=""))

            if plan_status is None:
                self.log('info',
                         "[TORF-324244] - LITP plan state returned a None "
                         "value, waiting for node to come up before executing "
                         "again")
                if self.wait_for_node_up(node, wait_for_litp=True):
                    plan_status = str(
                        self.get_props_from_url(node, "/plans/plan",
                                                filter_prop="state",
                                                log_output=True,
                                                show_option=""))

        if "initial" in plan_status.lower():
            return test_constants.PLAN_NOT_RUNNING
        elif "running" in plan_status.lower():
            return test_constants.PLAN_IN_PROGRESS
        elif "stopping" in plan_status.lower():
            return test_constants.PLAN_STOPPING
        elif "stopped" in plan_status.lower():
            return test_constants.PLAN_STOPPED
        elif "successful" in plan_status.lower():
            return test_constants.PLAN_COMPLETE
        elif "failed" in plan_status.lower():
            return test_constants.PLAN_FAILED
        elif "invalid" in plan_status.lower():
            return test_constants.PLAN_INVALID

        self.log("info", "Unexpected plan state: {0}".format(plan_status))

        return test_constants.CMD_ERROR

    def set_pws_new_node(self, ms_node, node,
                         workspace='/home/lciadm100/jenkins/workspace/'):
        """
        Takes as argument the node id which is defined in the connection data
        file. Will login to the node with default post-installation passwords
        and set passwords to those found in connection data file for this node.

        Args:
           ms_node (str): The ms_node id.

           node (str): ID of the new node.
                       NB: In most cases this will be the node hostname.

        KWargs:

           workspace (str): Path to workspace area. Defaults to vapp default.

        Returns:
           bool. True if password correctly set or False otherwise.
        """
        ##1. Define all scripts needed
        password_setup = False
        needed_scripts = list()
        set_admin_pw = 'passwdsetup_litp_admin.exp'
        check_admin_pw = 'check_litp_admin_pw.exp'
        set_root_pw = 'passwdsetup_root.exp'
        check_root_pw = 'check_root_pw.exp'

        needed_scripts = list()
        needed_scripts.append(set_admin_pw)
        needed_scripts.append(check_admin_pw)
        needed_scripts.append(set_root_pw)
        needed_scripts.append(check_root_pw)

        #2. Copy all scripts from gateway to peer node
        filelist = list()
        for script in needed_scripts:
            cmd = "/bin/find {0} -name '{1}'"\
            .format(workspace,
                    script)
            stdout, _, _ = self.run_command_local(cmd)
            self.assertNotEqual([], stdout)
            script_file = stdout[0]

            filelist.append(self.get_filelist_dict(script_file,
                                                   '/tmp/'))

        self.copy_filelist_to(ms_node, filelist,
                              root_copy=True)

        #3. Run scripts to set passwords
        pw_attempts = 10
        hostname = self.get_node_att(node, 'hostname')
        admin_usr = 'litp-admin'
        default_admin_pw = 'passw0rd'
        tmp_admin_pw = '@dm1nS3rv3r'
        default_root_pw = 'litpc0b6lEr'
        new_admin_pw = self.get_node_att(node, 'password')
        new_root_pw = self.get_node_att(node, 'rootpw')

        #Set litp-admin password to tmp value
        for _ in range(pw_attempts):
            cmd = "/tmp/{0} {1} {2} {3}".format(set_admin_pw,
                                                hostname,
                                                default_admin_pw,
                                                tmp_admin_pw)
            self.run_command(ms_node, cmd)

            cmd = "/tmp/{0} {1} {2} {3}".format(check_admin_pw,
                                                admin_usr,
                                                tmp_admin_pw,
                                                hostname)

            _, _, returnc = self.run_command(ms_node, cmd)

            if returnc == 0:
                break

        #Set litp-admin and root paswords to final value
        for _ in range(pw_attempts):
            cmd = "/tmp/{0} {1} {2} {3} {4} {5}".format(set_root_pw,
                                                hostname,
                                                tmp_admin_pw,
                                                new_admin_pw,
                                                default_root_pw,
                                                new_root_pw)
            self.run_command(ms_node, cmd)

            cmd = "/tmp/{0} {1} {2} {3}".format(check_admin_pw,
                                                admin_usr,
                                                new_admin_pw,
                                                hostname)

            _, _, returnc = self.run_command(ms_node, cmd)

            if returnc != 0:
                continue

            cmd = "/tmp/{0} {1} {2} {3} {4}".format(check_root_pw,
                                                admin_usr,
                                                new_admin_pw,
                                                hostname,
                                                new_root_pw)

            _, _, returnc = self.run_command(ms_node, cmd)

            if returnc == 0:
                password_setup = True
                break

        return password_setup

    def wait_for_plan_state(self, node, state_value, timeout_mins=20,
                            seconds_increment=3, full_show=True):
        """Waits until the plan reports the specified status
        or has completed its run

         Args:
          node        (str): The ms node you intend to test.

          state_value (int): The state value to wait for as
                             recorded in test_constants.
                             PLAN_COMPLETE = 0.
                             PLAN_IN_PROGRESS = 1.
                             PLAN_NOT_RUNNING = 2.
                             PLAN_FAILED = 3.
                             PLAN_STOPPED = 4.

        Kwargs:
          timeout_mins (int): When to timeout from the method
                              if the plan is still running.

         seconds_increment (int): The time in seconds between polling
                                  for the plan state.

         full_show (bool): If set to False, will never run a show_plan
                           command, only a show of /plans/plan

        Returns:
         bool. True is the specified Plan State is reached or False
         if plan reachea a final state different to that expected.


        Returns when the task reaches the stated state or when
        the state can no longer be reached. (ie plan is in error case
        or has completed).
        """
        self.log("info", "Entering wait_for_plan_state method")

        retries = 3
        start_time = time.time()
        full_show_increment_count = seconds_increment
        seconds_count = seconds_increment
        full_show_increment_secs = 60

        plan_state = self.get_current_plan_state(node, full_show)

        while True:

            time.sleep(seconds_increment)
            seconds_count += seconds_increment
            full_show_increment_count += seconds_increment
            minutes_passed = seconds_count / 60

            if full_show_increment_count > full_show_increment_secs:
                self.get_current_plan_state(node, full_show)
                full_show_increment_count = 0

            if minutes_passed > timeout_mins:
                self.get_current_plan_state(node, full_show)
                elapsed_time = int(time.time() - start_time)
                self.log("info",
                         "Exiting wait_for_plan_state method after " + \
                             "{0} seconds (TIMEOUT)".format(elapsed_time))
                return False

            plan_state = self.get_current_plan_state(node)

            if plan_state == test_constants.PLAN_STOPPED or \
                    plan_state == test_constants.PLAN_FAILED:
                self.unlock_required = True

            #This covers case where you are waiting for plan to start
            if plan_state == state_value:
                self.get_current_plan_state(node, full_show)
                elapsed_time = int(time.time() - start_time)
                self.log("info",
                         "Exiting wait_for_plan_state method after " + \
                             "{0} seconds (SUCCESS)".format(elapsed_time))
                return True

            #If plan is not in progress need to exit or you will
            #loop forever
            if plan_state != test_constants.PLAN_IN_PROGRESS:
                if plan_state == state_value:
                    self.get_current_plan_state(node, full_show)
                    elapsed_time = int(time.time() - start_time)
                    self.log("info",
                             "Exiting wait_for_plan_state method after " + \
                                 "{0} seconds (SUCCESS)".format(elapsed_time))
                    return True
                elif state_value == test_constants.PLAN_STOPPED and \
                        plan_state == test_constants.PLAN_STOPPING:
                    continue
                elif state_value == test_constants.PLAN_COMPLETE and \
                        plan_state == test_constants.PLAN_STOPPING:
                    continue
                elif plan_state == test_constants.PLAN_NOT_RUNNING and \
                         retries > 0:
                    self.log("info",
                             "LITP Plan is not running. Retries left: {0}" \
                                                            .format(retries))
                    retries -= 1
                    continue
                else:
                    self.get_current_plan_state(node, full_show)
                    elapsed_time = int(time.time() - start_time)
                    self.log("info",
                             "Exiting wait_for_plan_state method after " + \
                                 "{0} seconds (UNEXPECTED FINAL STATE: {1})" \
                                 .format(elapsed_time, plan_state))
                    return False

    def get_task_state(self, ms_node, task_desc, ignore_variables=True):
        """
        Checks the state of tasks matching the selected description.
        NB: Anything inside "" is ignored unless flag is set.

        Args:
           ms_node (str): The node running the plan.

           task_desc (str): The task description. Note anything inside ""\
              by default is ignored. eg. If this is passed in: 'Create\
              partition kickstart snippet for node "node1"'. The actual match\
              will be: 'Create partition kickstart snippet for node .*' This\
              is because variables are liable to change depending on\
              deployment script.

           ignore_variables (bool): If this is set to False then will do exact\
              match including variables. So if this is passed in: 'Create\
              partition kickstart snippet for node "node1"'. It will match for\
              the exact line. This is only allowed if your test creates the\
              variable in question.

        Returns:
           int. Constants value relating to the tasks state.
        """
        grep_variables = ""

        if not ignore_variables:
            found_var = False
            var_str_ls = list()
            var_str_ls = re.findall('\"(.+?)\"', task_desc)
            grep_variables = str()
            grep_variables += "| /bin/grep -A4 "

            for var in var_str_ls:
                found_var = True
                grep_variables += ".*'{0}'"\
                    .format(var)

            if not found_var:
                grep_variables = ""

            #grep_variables = \
                #"| /bin/grep -A3 -E '{0}'".format("|".join(var_str_ls))

        #Replace all strings in "" with a match all charachter to ignore
        #variables from the desc
        task_desc = re.sub(r'\"(.+?)\"', '.*', task_desc)

        show_plan_cmd = self.cli.get_show_plan_cmd("-j")
        grep_task_desc = " |/bin/grep -A4 description | /bin/grep -A4 '{0}'" \
            .format(task_desc)
        grep_state = ' | /bin/grep \'"state":\''

        grep_state_cmd = show_plan_cmd + grep_task_desc \
            + grep_variables + grep_state

        stdout, stderr, returnc = self.run_command(ms_node,
                                                   grep_state_cmd)

        #If no tasks are matched return error
        if stderr != [] or returnc != 0:
            return test_constants.CMD_ERROR

        #If at least one task has failed return task failed
        if self.is_text_in_list("Fail", stdout):
            return test_constants.PLAN_TASKS_FAILED

        #If the tasks matched have different states return INCONSISTENT
        if not all(x == stdout[0] for x in stdout):
            return test_constants.PLAN_TASKS_INCONSISTENT

        if self.is_text_in_list("Success", stdout):
            return test_constants.PLAN_TASKS_SUCCESS

        if self.is_text_in_list("Initial", stdout):
            return test_constants.PLAN_TASKS_INITIAL

        if self.is_text_in_list("Stopped", stdout):
            return test_constants.PLAN_TASKS_STOPPED

        if self.is_text_in_list("Run", stdout):
            return test_constants.PLAN_TASKS_RUNNING

    def wait_for_task_state(self, ms_node, task_desc, expected_state,
                            ignore_variables=True, timeout_mins=10,
                            seconds_increment=3):
        """
        Waits until the plan tasks reaches the expected state.
        NOTE: Will return True if expected_state is Running and the task is
        already Successful.

        Args:
           ms_node (str): The node running the plan.

           task_desc (str): The task description. Note anything inside "" is
           automatically ignored unless flag is passed. e.g. If this is
           passed in: Create partition kickstart snippet for node 'node1'
           The actual match will be: Create partition kickstart snippet for
           node. This is because variables are liable to change depending on
           deployment script.

           expected_state (int): The task state to wait for as defined in
           test_constants.

        Kwargs:
           ignore_variables (bool): If this is set to False then will do exact
           match including variables. So if this is passed in: Create
           partition kickstart snippet for node 'node1', it will match for
           the exact line. This is only allowed if your test creates the
           variable in question.

           timeout_mins (int) : How long to wait before exiting if expected
           state not reached. Default is 10 mins.

           seconds_increment (int): How long to wait between each poll of the
           plan tasks. Decrease this number if you expect task to only be in
           expected state for a short time. Defaults to 3 seconds.

        Returns:
           bool. True if task reaches expected state or False otherwise.
        """

        seconds_count = seconds_increment

        #Only keep checking while the plan is current running
        while(self.get_current_plan_state(ms_node)
              == test_constants.PLAN_IN_PROGRESS):

            time.sleep(seconds_increment)
            seconds_count += seconds_increment
            minutes_passed = seconds_count / 60

            if minutes_passed > timeout_mins:
                self.get_current_plan_state(ms_node, True)
                self.log("info",
                         "Exiting wait_for_task_state method after " + \
                             "{0} seconds (TIMEOUT)".format(seconds_count))
                return False

            task_state = self.get_task_state(ms_node, task_desc,
                                             ignore_variables)

            if task_state == expected_state:
                return True

            # Already achieved running state if it's successful
            if task_state == test_constants.PLAN_TASKS_SUCCESS and \
               expected_state == test_constants.PLAN_TASKS_RUNNING:
                return True

            #If the task has failed return False
            if task_state == test_constants.PLAN_TASKS_FAILED:
                return False

        #If the plan has stopped running before reaching expected state exit
        return False

    # Group 9 - Networking related

    def verify_backup_free_nics(self, ms_node, node_path, required_free_nics=1,
                                backup_files=True, specific_nics=None):
        """
        Finds the required number of free nics on the selected node and backup
        the ifconfig files. Also returns the list of free nics. (note will not
        return a list greater than the required number of nics requested.)

        Args:
           ms_node (str) : The filename of the ms node.

           node_path (str): The path of the node you wish to get free nics\
              from.

        Kwargs:
           required_free_nics (int): The number of free nics required.
                                 By default 1.

           backup_files (bool): Set to True by default and will backup\
              ifconfig files. If set to False will not perform backup of files.

           specific_nics (list): List of specific nics that can be returned\
              used in the case where a specific vlan is required.

        Returns:
           list. List of free nics.
        """
        if specific_nics is None:
            specific_nics = []
        req_nic_list = list()
        #Get node filename
        node_filename = self.get_node_filename_from_url(ms_node,
                                                        node_path)

        ##Get all free nics
        free_nics = self.get_free_nics_on_node(ms_node, node_path)

        ##Check we have the required number of nics
        self.assertTrue(len(free_nics) >= required_free_nics,
                        "Require {0} free nics but only {1} available"\
                            .format(required_free_nics,
                                    len(free_nics)))

        ##backup ifconfig files of all free nics
        for nic_item in free_nics:
            if specific_nics:
                if nic_item["NAME"] not in specific_nics:
                    continue
            if backup_files:
                ifcfg_file = "{0}/ifcfg-{1}".format(
                    test_constants.NETWORK_SCRIPTS_DIR,
                    nic_item["NAME"])
                self.backup_file(node_filename, ifcfg_file,
                                 restore_after_plan=True,
                                 assert_backup=False)

            req_nic_list.append(nic_item)

            ##Break when we have the required number of free nics in our
            #new list
            if len(req_nic_list) == required_free_nics:
                break

        return req_nic_list

    def add_nic_to_cleanup(self, node_with_nic, nic_name, is_bond=False,
                           is_bridge=False, flush_ip=False):
        """Will delete the ifconfig file of the selected nic
        on the selected node at the end of the test. (after remove plan)

        Args:
          node_with_nic (str): Node with ifconfig file you wish to remove.

          nic_name (str): The name of the nic whose ifconfig file is to\
             be deleted.

          is_bond (bool): If  set to true also removes bond from bonding\
             masters file.

          is_bridge (bool): If  set to true also removes bridge with delbr\
             command.

          flush_ip (bool): If set will call ip addr flush dev at end of test.

        """
        added_file = dict()
        if nic_name is not None:
            added_file[self.cleanup_key_node] = node_with_nic
            added_file[self.cleanup_key_filepath] = "{0}/ifcfg-{1}".format(
              test_constants.NETWORK_SCRIPTS_DIR, nic_name)
            added_file[self.cleanup_key_usr] = None
            added_file[self.cleanup_key_pw] = None
            added_file[self.cleanup_key_su] = True
            added_file[self.cleanup_key_nic] = nic_name
            added_file[self.cleanup_key_isbond] = is_bond
            added_file[self.cleanup_key_isbridge] = is_bridge
            added_file[self.cleanup_key_fluship] = flush_ip

            self.nics_to_delete.append(added_file)

    def get_network_props(self, ms_node, network_name):
        """For a given network  'network_name', returns the properties
        for that network. A start and end ip range are calculated for you
        based on the subnet.

        Args:
          ms_node (str): The MS node with the deployment tree.

          network_name (str): The name of the network you wish to look up.

        Returns:
        dict. Details fot the network inccluding subnet, name and calculated
        ip start and end range. Returns None if network name cannot be found.
        """
        networks = self.find(ms_node, "/infrastructure", "network")

        for network_url in networks:
            name = self.get_props_from_url(ms_node, network_url, "name")
            if name == network_name:
                # get all properties
                net_info = self.get_props_from_url(ms_node, network_url)
                if net_info is None:
                    return None

                ip_range = netaddr.IPNetwork(net_info["subnet"])
                start = int(netaddr.IPAddress(ip_range.first)) + 1
                end = int(netaddr.IPAddress(ip_range.last)) - 1
                net_info["start"] = netaddr.IPAddress(start)
                net_info["end"] = netaddr.IPAddress(end)

                return net_info

        return None

    def get_allowed_ips(self, ms_node, network_name):
        """
        For a given network 'network_name', return the
        complete list of IP addresses that are allowed to be
        assigned within the network. These ips are calculated based on
        the network subnet.

        Args:
           ms_node (str): The MS node with the deployment tree.

           network_name (str): The name of the network you wish to look up.

        Returns:
        list. All valid IP address in the network.
        """
        net_info = self.get_network_props(ms_node, network_name)

        return self.net.get_allowed_ips(net_info['start'], net_info['end'])

    def get_free_ip_by_net_name(self, ms_node, network_name, full_list=False):
        """
        For a network 'network_name', return an IP
        address which is valid within the network and not
        already being used by the MS or another node.

        Args:
            ms_node (str): The MS node with the deployment tree.

            network_name (str): The name of the network you wish to look up.

        Kwargs:
           full_list (bool): If set to true returns all ips that are free
           rather than just the first.

        Returns:
           str|list|None. A free IP address or None if there are no free ips
           available. If full_list arg given returns a list of all free ips.
        """

        # get list of allowed ips by network name
        allowed_ips = self.get_allowed_ips(ms_node, network_name)

        if allowed_ips == None:
            return None

        # get list of ips being used by managed nodes
        node_paths = self.find(ms_node, "/deployments", "node")
        node_paths.append("/ms")
        node_ips = []
        for node_path in node_paths:
            node_ips.extend(
                self.get_node_net_from_tree(ms_node, node_path)['ips']
            )

        # get gateway ips being used by managed nodes
        route_paths = self.find(ms_node, "/infrastructure", "route")
        gw_ips = []
        for route_path in route_paths:
            gw_ips.append(
                self.get_props_from_url(ms_node, route_path, "gateway")
            )

        vm_ips = []
        list_of_vm_interfaces = \
            self.find_children_of_collect(ms_node,
                                          "/deployments",
                                          "vm-network-interface",
                                          find_all_collect=True)

        list_of_vm_interfaces.extend(
                self.find_children_of_collect(ms_node,
                                              "/ms",
                                              "vm-network-interface",
                                              find_all_collect=True))

        for vm_interface in list_of_vm_interfaces:
            ##this property can contain a , seperated list of ips
            ip_list = self.get_props_from_url(ms_node, vm_interface,
                                              "ipaddresses")
            if not ip_list:
                continue
            all_ips = ip_list.split(',')
            vm_ips.extend(all_ips)

        used_ips = list()
        used_ips.extend(node_ips)
        used_ips.extend(gw_ips)
        used_ips.extend(vm_ips)

        # remove managed node IP addresses from list of IPs that we
        # can use
        valid_ips = [ip for ip in allowed_ips if ip not in used_ips]

        #In some cases on physical even private ips may clash with other
        #systems. Test the first 3 ips are not pingable before returning data.

        valid_ip_count = 0
        for ip_addr in list(valid_ips):
            if self.is_ip_pingable(ms_node, ip_addr):
                valid_ips.remove(ip_addr)
                continue

            valid_ip_count += 1

            if valid_ip_count > 2:
                break

        # make sure there are some free IP addresses
        if len(valid_ips) < 1:
            return None

        # give back first available ip
        if full_list:
            return valid_ips
        else:
            return valid_ips[0]

    def find_ipv4_in_model(self, ms_node, ip_address):
        """
        Looks for a specific ip address assigned to a nic in the model.

        Args:
             ms_node (str): The MS with the tree you wish to query.

             ipaddress (str): An ipv4 address you want to search for.
                              (eg 10.10.10.10)

        Returns:
        str. The path of the nic with this ip address or None if ip is
        not found.
        """
        nic_paths = self.find_children_of_collect(ms_node, "/",
                                                  "network-interface",
                                                  find_all_collect=True)
        #nic_paths = self.find(ms_node, "/", "eth")

        for path in nic_paths:
            ipaddress_model = \
                self.execute_show_data_cmd(ms_node, path, "ipaddress",
                                           assert_value=False)

            #If a nic does not have an ipaddress skip check
            if not ipaddress_model:
                continue

            if ip_address in ipaddress_model:
                return path

        return None

    def find_ipv6_in_model(self, ms_node, ipv6_address):
        """
        Looks for a specific ipv6 address assigned to a nic in the model.

        Args:
             ms_node (str): The MS with the tree you wish to query.

             ipv6address (str): An ipv6 address you want to search for.
                              (eg 2001:1b70:82a1:0103::44)

        Returns:
        str. The path of the nic with this ip address or None if ip is
        not found.
        """
        nic_paths = self.find_children_of_collect(ms_node, "/",
                                                  "network-interface",
                                                  find_all_collect=True)

        ipv6_address = ipv6_address.split("/",)[0]
        ipv6_address = ipv6_address.replace(":0", ":")

        for path in nic_paths:
            ipaddress_model = \
                self.execute_show_data_cmd(ms_node, path, "ipv6address",
                                           assert_value=False)

            #If a nic does not have an ipaddress skip check
            if not ipaddress_model:
                continue

            ipaddress_model = ipaddress_model.split("/",)[0]
            ipaddress_model = ipaddress_model.replace(":0", ":")

            if ipv6_address in ipaddress_model:
                return path

        return None

    def get_all_macs_in_model(self, ms_node, node_path="/"):
        """Returns all mac addresses listed in the model.

        Args:
          ms_node (str): The MS with the tree you wish to query.

        Kwargs:
          node_path (str): Optional filter to only look for macs in a
                           certain path.

        Returns:
           list. A list of all mac address in the LITP model.
        """
        macs_in_model = list()
        show_cmd = self.cli.get_show_cmd(node_path, "-r")
        cmd = "niclist=( $({0} | grep -B 2 -E ".format(show_cmd) \
            + "'type: eth$|type: reference-to-eth' | grep ^'/') ); for line " \
            + "in \"${niclist[@]}\"; do litp show -p $line | sed " \
            + "'s/^[ ]*//;s/[ ]*$//' | grep ^'macaddress:' " \
            + "| sed 's/macaddress: //'; done"

        stdout, stderr, retc = self.run_command(ms_node, cmd)
        #macs_in_model = list()

        #eth_urls = self.find(ms_node, node_path, "eth")

        #for device_url in eth_urls:
        #    macs_in_model.append(self.execute_show_data_cmd(ms_node,
        #                                                    device_url,
        #                                                   "macaddress"))

        if stdout != [] and stderr == [] and retc == 0:
            macs_in_model.extend(stdout)

        return macs_in_model

    def get_all_nics_from_node(self, ms_node, node_path):
        """
        This method runs ifconfig command on the passed node and
        returns a dict of all interfaces on that node.

        Args:
           ms_node (str): The MS node

           node_path (str): The path to the node for which you want to
           run ifconfig.

        Returns:
            list. A list of dicts representing on interfaces on specified node.
        """

        self.log("info", "START - get_all_nics_from_node")
        example_node = self.get_node_filename_from_url(ms_node,
                                                       node_path)

        if not example_node:
            return []

        get_all_nics_cmd = self.net.get_node_nic_interfaces_cmd()

        print "EXAMPLE_NODE", example_node
        stdout, stderr, returnc = self.run_command(example_node,
                                                   get_all_nics_cmd)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        self.assertNotEqual([], stdout)
        nics_ls = stdout

        get_all_nics_detail_cmd = self.net.get_ifconfig_cmd(ifc_args="-a")

        stdout, stderr, returnc = self.run_command(example_node,
                                                   get_all_nics_detail_cmd)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        self.assertNotEqual([], stdout)
        nic_details_ls = stdout

        nic_dict_ls = list()

        for nic in nics_ls:
            nic_dict = self.net.get_ifcfg_dict(nic_details_ls, nic)
            nic_dict_ls.append(nic_dict)

        self.log("info", "END - get_all_nics_from_node")

        return nic_dict_ls

    def get_free_nics_on_node(self, ms_node, node_path):
        """
        This method compares the model to ifconfig
        output and returns a list of free nics on the node.

        Args:
           ms_node (str): The MS node.

           node_path (str): The path to the node for which you want to
           find a free nic.

        Returns:
            list. A list of dicts representing interfaces on the
            specified node.
        """
        free_nics = list()

        macs_in_model = self.get_all_macs_in_model(ms_node, node_path)

        print "MAC_MODEL:", macs_in_model
        nics_in_node = self.get_all_nics_from_node(ms_node, node_path)

        print "NICS_NODE:", nics_in_node

        for nic in nics_in_node:
            #If MAC not in NIC and IP address
            if not nic[self.net.dict_key_mac].upper() in \
                    (mac.upper() for mac in macs_in_model) and \
                    not nic[self.net.dict_key_ipv4]:
                free_nics.append(nic)

        print "FREE_NICS:", free_nics

        return free_nics

    def get_used_nics_on_node(self, ms_node, node_path):
        """
        This method compares the model to ifconfig
        output and returns a list of used nics on the node.

        Args:
           ms_node (str): The MS node

           node_path (str): The path to the node for which you want to
           find a free nic.

        Returns:
            list. A list of dicts representing interfaces on specified node.
        """
        used_nics = list()

        macs_in_model = self.get_all_macs_in_model(ms_node)

        nics_in_node = self.get_all_nics_from_node(ms_node, node_path)

        for nic in nics_in_node:
            #If MAC not in NIC and IP address
            if nic[self.net.dict_key_mac] in macs_in_model:
                used_nics.append(nic)

        return used_nics

    def get_nodes_using_resource(self, ms_node, resource_path,
                                 resource_type):
        """Returns the paths to all nodes which inherit from this resource.

        Args:
         ms_node (str): The MS with the tree you wish to query.

         resource_path (str): The full path of the resource in
                              '/infrastructure'.

         resource_type (str): The resource type to look for.

        Returns:
           list. All node paths which inherit from this resource.
        """
        nodes_using_resource = list()

        #Find all nodes in deployment
        node_paths = self.find(ms_node,
                               "/deployments",
                               "node")

        #For each node find what network profile it links to
        for path in node_paths:
            paths_to_check = self.find(ms_node, path, resource_type)

            for item_path in paths_to_check:
                resource_links_path = \
                    self.execute_show_data_cmd(ms_node,
                                               item_path,
                                               "inherited from")

                if resource_links_path == resource_path:
                    nodes_using_resource.append(path)
                    break

        return nodes_using_resource

    def get_node_network_devices(self, ms_node, node_path):
        """Returns a dict of all nics on the selected node
        and there related details.

        Args:
           ms_node (str) : The MS node.

           node_path (str): The path to the node in question.

       Returns:
         dict. Dictionary containg macaddress, ipaddress, network name
         for each device name.
       """

        #list_of_networks_to_device = {}
        # Find all eth interfaces under provided base URL
        eth_urls = self.find_children_of_collect(ms_node,
                                                 node_path,
                                                 "network-interface")
        network_devices = dict()

        for eth_url in eth_urls:
            device_details = self.get_props_from_url(ms_node, eth_url)

            device_name = device_details['device_name']
            del device_details['device_name']
            network_devices[device_name] = dict()
            network_devices[device_name] = device_details

        return network_devices

    def get_default_route_path(self, ms_node):
        """
        Returns the default path of the default route.

        Args:
        ms_node (str): The ms node filename.

        Returns:
        str. Path of the default route.
        """
        route_urls = self.find(ms_node, "/infrastructure", "route")
        default_subnet = "0.0.0.0/0"

        found = False

        for route_url in route_urls:
            route_subnet = self.get_props_from_url(ms_node, route_url,
                                                   filter_prop="subnet")
            if route_subnet == default_subnet:
                found = True
                return route_url

        self.assertTrue(found, "Default route url is not found")

    def get_management_network_name(self, ms_node, return_path=False):
        """
        Description:
            Get management network name and optionally the path.

        Args:
           ms_node (str) : The MS node with the deployment tree.

           return_path (str): By default set to False. If set to true will
           also return the path to the management network.

        Results:
            str, str. management network name and optinally the path.
            None returned if management network not found.
        """
        # GET NETWORKS
        networks = self.find(ms_node, "/infrastructure", "network")

        for network_url in networks:
            props = self.get_props_from_url(ms_node, network_url)
            if props["litp_management"] == "true":
                if return_path:
                    return props["name"], network_url
                else:
                    return props["name"]

        return None

    def get_management_network(self, ms_node):
        """
        Description:
            Returns the name and path to the management network.

        Args:
           ms_node (str) : The MS node with the deployment tree.

        Results:
            str, str. management network name and litp path.
            None returned if management network not found.
        """
        # GET NETWORKS
        networks = self.find(ms_node, "/infrastructure", "network")

        for network_url in networks:
            props = self.get_props_from_url(ms_node, network_url)
            if props["litp_management"] == "true":
                return props["name"], network_url

        return None

    def get_arp_dict(self, node, arp_args=''):
        """
        Runs the arp command and returns results as a list
        of dictionary items.

        Args:

          node (str): The node to run the arg command.

       Kwargs:
          arp_args (str): Arguments to pass to the arp command.

       Returns:
          list. A list with each element containing a dict which represents one
          line of arp output.
        """

        cmd = self.net.get_arp_cmd(arp_args)

        stdout, stderr, returnc = \
            self.run_command(node, cmd, arp_args)

        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)

        arp_lines = list()
        for line in stdout:
            line_parts = line.split()

            ##If we have 5 columns we are in the main table.
            ##If we do not have Address then we are not in heading
            if len(line_parts) == 5 \
                    and "Address" not in line:
                arp_dict = dict()
                arp_dict['address'] = line_parts[0]
                arp_dict['type'] = line_parts[1]
                arp_dict['hwaddr'] = line_parts[2]
                arp_dict['flags'] = line_parts[3]
                arp_dict['iface'] = line_parts[4]

                arp_lines.append(arp_dict)

        return arp_lines

    def get_node_net_from_tree(self, ms_node, node_url):
        """Searchs the LITP tree model to find network related
        details for the node specified by the node_url passed.

        Actions:

        1) Set hostname by querying the properties of the node_url.

        2) Set ip addresses from node ip ranges.

        3) Get the system linked to this node.

        4) Get the list of all nic and mac addresses in this system.

        5) Find node_profile linked to this node.

        6) Get interfaces attached to this node profile.

        7) Make a list of all system interface-nic pairs where the interface.
        is defined in the node_profile.

        Args:

            ms_node (str) : The MS containing the LITP tree you wish to search
            for network details.

            node_url (str) : The URL of the node you wish to find network
            related information from.

        Returns:
            dict. Dict of network details
        """
        #We need to examine the litp tree to find the below variables
        node_network_details = dict()

        node_network_details[self.hostname_key] = None
        node_network_details[self.ips_key] = None
        node_network_details[self.interface_mac_key] = None

        # hostname_in_tree = None @todo - not used?
        ips_in_tree = list()
        interface_mac_pairs_ls = list()

        #1) Set hostname from node properties
        node_network_details[self.hostname_key] = \
            self.get_props_from_url(ms_node, node_url,
                                    "hostname")

        if not node_network_details[self.hostname_key]:
            self.log("error", "Could not find hostame")
            return node_network_details

        #2) Set ip addresses from node ip ranges
        #3) Get the list of all mac addresses in this system
        eth_urls = self.find_children_of_collect(ms_node, node_url,
                                                 "network-interface")

        for url in eth_urls:
            ipaddress = self.get_props_from_url(ms_node, url, "ipaddress")
            if ipaddress:
                ips_in_tree.append(ipaddress)

            interface = \
                self.get_props_from_url(ms_node, url, "device_name")
            macaddress = \
                self.get_props_from_url(ms_node, url, "macaddress")
            interface_mac_pairs_ls.append({"interface_name": interface,
                                           "macaddress": macaddress})

        #Add ips to return dict
        node_network_details[self.ips_key] = ips_in_tree

        #add to return dict
        node_network_details[self.interface_mac_key] = interface_mac_pairs_ls

        return node_network_details

    def is_ip_pingable(self, node, ip_addr, args='', timeout_secs=0,
                       ipv4=True):
        """
        Performs a ping command of the ip address passed
        from the selected node. Will return True if ip is pingable
        or False otherwise.

        Optionally will wait a timeout period and only return False if
        ping command fails after timeout has expired.

        Args:
           node (str): The node to perform the ping from.

           ip_addr (str): The ip address or hostname to ping.

        Kwargs:
          args (str): Optional arguments to append to the ping command.
          timeout_secs (str): The length of time to spend retrying the ping.
          By default returns False if the ip cannot be pinged on first attempt.

          ipv4 (bool): Switch between ipv4 and ipv6.

        Returns:
           bool. Returns true if ping is successful or False otherwise.
        """

        if ipv4:
            ping_cmd = self.net.get_ping_cmd(ip_addr, args=args)
        else:
            ip_addr = ip_addr.split("/",)[0]
            ping_cmd = self.net.get_ping6_cmd(ip_addr, args=args)

        counter = 0

        while True:
            _, stderr, returnc = self.run_command(node, ping_cmd)

            self.assertEqual([], stderr)
            if returnc == 0:
                return True

            if counter == timeout_secs:
                return False

            time.sleep(1)
            counter += 1

    def execute_cli_restoremodel_cmd(self, node, args='',
                                username=None,
                                password=None,
                                expect_positive=True,
                                load_json=True):
        """Build + Run a LITP restore_model command.

        Args:
            node (str): Node you want to run command on.

        Kwargs:
            args (str): CLI args, like '--json' and '-h'.

            username (str):  User to run command as if not default.

            password (str):  Password to run command as if not default.

            expect_positive (bool): By default assumes command will run
            without failure.

            load_json (bool): Set to load return values into JSON
            assuming that the -j argument is used.

        Returns:
            list, list, int. std_out, std_err, rc from running upgrade command.

        Will assert success (by default) or failure if the expect_positive
        argument is passed in as False.

        """
        # build and run upgrade command
        upgrade_cmd = self.cli.get_restoremodel_cmd()

        stdout, stderr, returnc = self.run_command(
            node, upgrade_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_upgrade_cmd(self, node, url, args='',
                                username=None,
                                password=None,
                                expect_positive=True,
                                load_json=True):
        """Build + Run a LITP upgrade command.

        Args:
            node (str): Node you want to run command on.

            url (str): LITP path to upgrade.

        Kwargs:
            args (str): CLI args, like '--json' and '-h'.

            username (str):  User to run command as if not default.

            password (str):  Password to run command as if not default.

            expect_positive (bool): By default assumes command will run
            without failure.

            load_json (bool): Set to load return values into JSON
            assuming that the -j argument is used.

        Returns:
            list, list, int. std_out, std_err, rc from running upgrade command.

        Will assert success (by default) or failure if the expect_positive
        argument is passed in as False.

        """
        # build and run upgrade command
        upgrade_cmd = self.cli.get_upgrade_cmd(url, args)
        stdout, stderr, returnc = self.run_command(
            node, upgrade_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_create_cmd(self, node, url, class_type, props='', args='',
                               expect_positive=True, username=None,
                               password=None, add_to_cleanup=True,
                               load_json=True):
        """Build + Run a LITP create command.

        Args:
            node            (str): Node you want to run command on.

            url             (str): LITP path to create.

            class_type      (str): LITP item class type.

        Kwargs:
            props           (str): Create command properties.

            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            add_to_cleanup  (bool): Set to False to turn off auto cleanup.

            load_json       (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running create command.
        """
        # build and run create command
        create_cmd = self.cli.get_create_cmd(url, class_type, props, args)
        stdout, stderr, returnc = self.run_command(
            node, create_cmd, username, password, add_to_cleanup=add_to_cleanup
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_remove_cmd(self, node, url, args='', expect_positive=True,
                               username=None, password=None,
                               add_to_cleanup=True, load_json=True):
        """Build + Run a LITP remove command.

        Args:
            node            (str): Node you want to run command on.

            url             (str): LITP path to remove.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            add_to_cleanup  (bool): Set to False to turn off auto cleanup.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running remove command.
        """

        # build and run remove command
        remove_cmd = self.cli.get_remove_cmd(url, args=args)
        stdout, stderr, returnc = self.run_command(
            node, remove_cmd, username, password, add_to_cleanup=add_to_cleanup
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_update_cmd(self, node, url, props='', args='',
                               expect_positive=True, username=None,
                               password=None, load_json=True,
                               action_del=False):
        """Build + Run a LITP update command.

        Args:
            node            (str): Node you want to run command on.

            url             (str): LITP path to update.

        Kwargs:
            props           (str): Create command properties.

            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.

            action_del     (bool): If set to True will delete the property\
               instead of updating it.
        Returns:
            list, list, int. std_out, std_err, rc from running update command.
        """
        # build and run update command
        update_cmd = self.cli.get_update_cmd(url, props, args,
                                             action_delete=action_del)
        stdout, stderr, returnc = self.run_command(
            node, update_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_createplan_cmd(self, node, args='',
                                   username=None, password=None,
                                   expect_positive=True, load_json=True):
        """Build + Run a LITP create_plan command.

        Args:
            node            (str): Node you want to run command on.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running
            create_plan command.
        """
        # build and run create_plan command
        create_plan_cmd = self.cli.get_create_plan_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, create_plan_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            # show_plan is performed to enable debugging before assertions.
            show_plan_cmd = self.cli.get_show_plan_cmd(args=args)
            # We run as expects as large plan output can lock paramiko when
            # using standard executes
            self.run_expects_command(node, show_plan_cmd, [], timeout_secs=130)

            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def get_plan_data(self, node, logging=False):
        """
        Description:
            Return data structure representing the plan layout and state

            Data structure sample:
            {'state': 'running',
             'phases':
                 '2':
                    {'c1':
                        [
                           {'desc':'Install package "finger" on node "node1"',
                            'url':'http://......',
                            'state': 'Initial'},
                           {'desc':'Install package "firefox" on node "node2"',
                            'url':'http://......',
                            'state': 'Initial'}
                        ]
                    }
             }
        Args:
            node (str): The node to get the plan from
            logging (bool): If set to True plan data is logged
        Return:
            dict, The plan layout and state
        """
        plan_output_file = '/tmp/plan_output.json'
        cmd = 'echo "$(/usr/bin/litp show_plan -j)" > {0}' \
              .format(plan_output_file)
        self.run_command(node,
                         cmd,
                         connection_timeout_secs=30,
                         logging=True)

        self.download_file_from_node(node,
                                     plan_output_file,
                                     plan_output_file)
        plan_output = ''
        with open(plan_output_file) as json_data:
            plan_output = json.load(json_data)

        plan = {}
        plan['state'] = plan_output['properties']['state']

        phases = {}
        for collection_of_phase in plan_output['_embedded'].get('item'):
            for phase in collection_of_phase.get('_embedded').get('item'):
                phase_id = phase.get('id')
                for tasks in phase.get('_embedded').get('item'):
                    if tasks.get('item-type-name') == "collection-of-task":
                        for task in tasks.get('_embedded').get('item'):

                            url = task.get('_links').get('rel').get('href')

                            if 'clusters/' in url:
                                cluster_id = url.split('clusters/')[1] \
                                    .split('/')[0]
                            elif '/ms/' in url:
                                cluster_id = 'ms'
                            elif '/snapshots/' in url:
                                cluster_id = 'snapshots'

                            task_data = {'desc': task.get('description'),
                                         'url': url.split('v1')[1],
                                         'state': task.get('state')}

                            if not phase_id in phases:
                                phases[phase_id] = dict()

                            if not cluster_id in phases[phase_id]:
                                phases[phase_id][cluster_id] = list()

                            phases[phase_id][cluster_id].append(task_data)
        plan['phases'] = phases

        if logging:
            for phase, clusters in sorted(plan['phases'].iteritems()):
                self.log('info', '{0}'.format(phase))
                for cluster, tasks in sorted(clusters.iteritems()):
                    self.log('info', '  {0}'.format(cluster))
                    for task in tasks:
                        self.log('info',
                            '    {0}<8}{1}'
                            .format(task.get('state'), task.get('url')))
                        self.log('info',
                            '    {0}<8}{1}'.format(' ', task.get('desc')))

        return plan

    def get_tasks_by_state(self, node, state='Running', plan_data=None):
        """
        Description:
            Returns a list of task descriptions, associated by cluster name
            and phase number filtered by task state.
        Args:
            node (str) : The node with the running plan
            state (str) : The state to filter by. e.g: Running, Initial etc.
        Returns:
            dict, A plan data structured filtered by task state
        """
        if plan_data is None:
            plan = self.get_plan_data(node)
        else:
            plan = plan_data

        filtered_plan = {}
        for phase, clusters in plan['phases'].iteritems():
            for tasks in clusters.itervalues():
                for task in tasks:
                    if task.get('state') == state:
                        filtered_plan[phase] = clusters

        return filtered_plan

    def execute_cli_createsnapshot_cmd(self, node, args='',
                                       username=None, password=None,
                                       expect_positive=True, load_json=True,
                                       add_to_cleanup=True):
        """Build + Run a LITP create_snapshot command.

        Args:
            node            (str): Node you want to run command on.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
                assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
                Only valid if passing the -j arguments.

            add_to_cleanup  (bool): If False do not add command to autocleanup.
        Returns:
            list, list, int. std_out, std_err, rc from running
            create_snapshot command.
        """
        # build and run create_plan command
        create_snapplan_cmd = self.cli.get_create_snapshot_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, create_snapplan_cmd, username, password,
            add_to_cleanup=add_to_cleanup
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_removesnapshot_cmd(self, node, args='',
                                       username=None, password=None,
                                       expect_positive=True, load_json=True,
                                       add_to_cleanup=True):
        """Build + Run a LITP remove_snapshot command.

        Args:

           node            (str): Node you want to run command on.

        Kwargs:

           args            (str): CLI args, like '--json' and '-h'.

           username        (str):  User to run command as if not default.

           password        (str):  Password to run command as if not default.

           expect_positive (bool): Determines error checking. By default\
              assumes command will run without failure.

           load_json      (bool): Set to load return values into JSON.\
              Only valid if passing the -j arguments.

           add_to_cleanup  (bool): If False do not add command to autocleanup.

        Returns:
            list, list, int. std_out, std_err, rc from running
            remove_snapshot command.
        """
        # build and run remove_snapshot command
        remove_snapshot_cmd = self.cli.get_remove_snapshot_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, remove_snapshot_cmd, username, password,
            add_to_cleanup=add_to_cleanup
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_restoresnapshot_cmd(self, node, args='',
                                        username=None, password=None,
                                        expect_positive=True, load_json=True):
        """Build + Run a LITP restore_snapshot command.

        Args:
            node            (str): Node you want to run command on.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running
            restore_snapshot command.
        """
        # build and run restore_snapshot command
        restore_snapplan_cmd = self.cli.get_restore_snapshot_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, restore_snapplan_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_removeplan_cmd(self, node, args='',
                                   username=None, password=None,
                                   expect_positive=True, load_json=True):
        """Build + Run a LITP remove_plan command.

        Args:
            node            (str):  Node you want to run command on.

        Kwargs:
            args            (str):  CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running
            remove_plan command.
        """
        # build and run create_plan command
        remove_plan_cmd = self.cli.get_remove_plan_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, remove_plan_cmd, username, password
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_runplan_cmd(self, node, args='',
                                username=None, password=None,
                                expect_positive=True, load_json=True,
                                add_to_cleanup=True):
        """Build + Run a LITP run_plan command.

        Args:
            node            (str):  Node you want to run command on.

        Kwargs:
            args            (str):  CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.

            add_to_cleanup (bool): By default will perform standup plan
            cleanup steps in teardown. Set to False to disable this
            behaviour.

        Returns:
            list, list, int. std_out, std_err, rc from running
            run_plan command.
        """
        # build and run create_plan command
        run_plan_cmd = self.cli.get_run_plan_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, run_plan_cmd, username, password,
            add_to_cleanup=add_to_cleanup
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_showplan_cmd(self, node, args='',
                                 username=None, password=None,
                                 expect_positive=True, load_json=True,
                                 expect_large_output=False,
                                 suppress_output=False):
        """Build + Run a LITP show_plan command.

        Args:
            node            (str): Node you want to run command on.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
                Only valid if passing the -j arguments.

            expect_large_output (bool): If we expect a large plan output.\
             (ie if showplan is expected to hang for 10+ secs before returning)
        Returns:
            list, list, int. std_out, std_err, rc from running
            show_plan command.
        """
        # build and run create_plan command
        show_plan_cmd = self.cli.get_show_plan_cmd(args=args)

        ##We run as expects as large plan output can lock paramiko when
        #using standard executes
        if expect_large_output:
            stdout, stderr, returnc = self.run_expects_command(
                node, show_plan_cmd, [], timeout_secs=130,
                suppress_output=suppress_output)
        else:
            stdout, stderr, returnc = self.run_command(
                node, show_plan_cmd, username, password)

        # assert expected values
        if expect_positive:
            self.assertNotEqual([], stdout)

            if "-j" in args and load_json:
                json_data = self.json_u.load_json(stdout)
                self.assertNotEqual(None, json_data,
                                    "JSON could not be loaded")
                stdout = json_data

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def wait_for_ping(self, ip_address, ping_success=True,
                      timeout_mins=15, retry_count=3, node=None):
        """
        Waits for the ip_address to either return a ping or stop returning
        a ping depending on the flag set.

        Args:
           ip_address (str) : Ip address to ping.

        KWargs:
           ping_success (str): By default will return only after ping returns
           success. If set to False will return when ping fails.

           timeout_mins (str): If the ping has not behaved as expected before
           the timeout will return with False.

           retry_count (str): The number of retries before it's known that
                              a ping fails.

           node (str): node on which run the ping command. If node is not
           provided the ping command will be executed by the machine that is
           executing the test.

        Returns:
           bool. True if ping responds in time or False otherwise.
        """
        ping_cmd = self.net.get_ping_cmd(ip_address)

        counter = 0
        timeout_secs = 60 * timeout_mins
        increment_secs = 5

        self.log('info', "Initial Timeout_secs: {0}" \
                 .format(timeout_secs))

        # Need a retry mechanism as sometimes ping responses get lost.
        # In this scenario, we need to have several unsuccessful pings
        # before it's known for 100% sure that ping fails.
        retry = retry_count

        while True:
            if node is None:
                returnc = self.run_command_local(ping_cmd)[2]
            else:
                returnc = self.run_command(node, ping_cmd)[2]

            if ping_success and returnc == 0:
                return True

            if not ping_success and returnc == 1:
                retry -= 1
                # Reduce time to enable faster execution.
                increment_secs = 1
                self.log('info', "ping retry counter: {0}" \
                         .format(retry))
                if retry == 0:
                    return True

            if not ping_success and returnc == 0:
                # Reset to initial values to cover the scenario in which
                # a failed ping is immediately followed by successful one.
                retry = retry_count
                increment_secs = 5
                self.log('info', "reset ping retry counter: {0}" \
                         .format(retry))

            time.sleep(increment_secs)
            counter += increment_secs

            if counter > timeout_secs:
                self.log('info', "Exiting wait_for_ping due to timeout")
                return False

    def wait_for_node_up(self, node, timeout_mins=10, wait_for_litp=False):
        """
        Waits until the node in question is responding to pings and
        can be accessed via ssh.

        Args:

          node (str): The node in question which you wish to wait for.

        Kwargs:

          timeout_mins (int): How long to wait for the node to come up.

          wait_for_litp (bool): Defaults to False. If set to True will
          wait until the LITP version command returns a 0 exit code
          indicating the LITP service is running.

        Returns:
           bool. True if node comes up within timeout or False otherwise.
        """
        node_ip = self.get_node_att(node, 'ipv4')

        if not self.wait_for_ping(node_ip, timeout_mins=timeout_mins):
            return False

        increment_secs = 10
        count = 0
        timeout_secs = 60 * timeout_mins

        while True:
            try:
                #This will force a clean reconnection attempt each time
                self.disconnect_all_nodes()
                self.run_command(node, "hostname")
                self.log('info', "SSH connection is successful")
                break

            except Exception as except_err:
                if 'Authentication' in except_err:
                    self.log('info', "Node is now up")
                    break

                self.log('info', "SSH not yet avalable: {0}"\
                             .format(except_err))
                time.sleep(increment_secs)
                count += increment_secs

                if count > timeout_secs:
                    return False

        if wait_for_litp:
            show_cmd = self.cli.get_show_cmd("/litp/maintenance")
            return self.wait_for_cmd(node,
                                    show_cmd,
                                    0,
                                    timeout_mins=5)

        return True

    def get_node_ilo_ip(self, ms_node, peer_node):
        """
        Determines the ipaddress of the ilo for the provided node.

        Args:
            ms_node (str): The ms node.

            peer_node (str): Filename of peer node for which iLo ipaddress
                             is required.

        Returns:
            str. Returns the ipaddress of the ilo or None if the
                 property cannot be found.
        """
        node_url = self.get_node_url_from_filename(ms_node,
                                                   peer_node)
        system_url = self.deref_inherited_path(ms_node, node_url)

        bmc_url = self.find(ms_node, system_url, "bmc", assert_not_empty=False)

        if bmc_url:
            url = bmc_url[0]
            ilo_ip = self.get_props_from_url(ms_node, url,
                                             filter_prop="ipaddress")
            return ilo_ip

        return None

    def poweroff_peer_node(self, ms_node, peer_node, ilo_ip=None):
        """
        Will perform a hard poweroff of a peer node.

        Args:
           ms_node (str): The ms node.

           peer_node (str): The peer node you wish to poweroff.

        KWargs:
           ilo_ip (str): IP of ILo needed for hardware poweroff on Hardware

        Raises:
          AssertionError. If poweroff command returns an error or if
          node is still pingable after hard power off.
        """
        del ms_node  # unused since change from IPMI to Redfish
        node_ip = self.get_node_att(peer_node, 'ipv4')
        redfish_obj = self.get_redfish_client(node_ip, ilo_ip=ilo_ip)
        try:
            redfish_obj.login()
            body = {"ResetType": "ForceOff"}
            response = redfish_obj.post(test_constants.REDFISH_ACTIONS +
                                        test_constants.REDFISH_RESET,
                                        body=body)
            self.assertEqual(200, response.status)

            self.log('info', "Checking if node is down")
            self.assertTrue(self.wait_for_ping(node_ip, False,
                                               timeout_mins=1))
        finally:
            redfish_obj.logout()

    def poweron_peer_node(self, ms_node, peer_node, wait_poweron=True,
                          poweron_timeout_mins=10, ilo_ip=None):
        """
        Will perform a hard poweron of a peer node.

        Args:
           ms_node (str): The ms node.

           peer_node (str): The peer node you wish to poweron.


        KWargs:
          wait_poweron (bool): By default waits until node has powered back on
          and can be reached via ssh.

          poweron_timeout_mins (int): Length of time to wait for node to
                                      power on before throwing assertion
                                      error.

          ilo_ip (str): IP of ILo needed for hardware poweron on Hardware

        Raises:
          AssertionError. If poweroff command returns an error.
        """
        del ms_node  # unused since change from IPMI to Redfish
        node_ip = self.get_node_att(peer_node, 'ipv4')
        redfish_obj = self.get_redfish_client(node_ip, ilo_ip=ilo_ip)
        try:
            redfish_obj.login()
            body = {"ResetType": "On"}
            response = redfish_obj.post(test_constants.REDFISH_ACTIONS +
                                        test_constants.REDFISH_RESET,
                                        body=body)
            self.assertEqual(200, response.status)

            if wait_poweron:
                self.assertTrue(self.wait_for_node_up(
                    peer_node, poweron_timeout_mins),
                    "Node has not come up before timeout")
        finally:
            redfish_obj.logout()

    @staticmethod
    def get_redfish_client(node_ip, ilo_ip=None):
        """
        Creates a redfish client object for either cloud based
        connections or hardware based connections.
        If an ilo_ip is provided a hardware based client is returned.
        Otherwise a cloud based client is returned.

        Args:
           node_ip (str): IP of node needed to create client
            for cloud poweron

        KWargs:
           ilo_ip (str): IP of ILO, only used when connection is
           hardware based. Default is None

        Returns:
            RedfishClient. Returns a redfish client for either
            cloud or hardware.
        """
        if ilo_ip is None:
            return redfishtool.RedfishClient(
                base_url=node_ip,
                username='no-user',
                password='ignored',
                default_prefix=test_constants.REDFISH_ROOT)

        return redfish.redfish_client(
            base_url='https://{0}'.format(ilo_ip),
            username=test_constants.ILO_USERNAME,
            password=test_constants.ILO_PASSWORD,
            default_prefix=test_constants.REDFISH_ROOT)

    def execute_and_wait_restore_snapshot(self,
                                          ms_node,
                                          args='',
                                          timeout_mins=40,
                                          poweroff_nodes=(),
                                          skip_cmd=False):
        """
        Runs the restore_snapshot command and waits until the
        ms_node has restarted before returning.

        Args:
           ms_node (str): The ms_node you wish to run the restore_snapshot
           command on.

        Kwargs
           args (str): The arguments to pass to the restore_snapshot command.

           reboot_timeout_mins (int): The amount of time to wait for
           restore_snapshot to complete. 30 minutes by default.

           poweroff_nodes (list): When restoring from an expansion you should
           power off expanded nodes. Provide a list of these nodes here.

           skip_cmd (bool): By default runs the restore_snapshot command. Set
           this to True to skip this (assumes command has already been run as
           part of test.)

        Raises:
           AssertionError. If restore_snapshot command fails or node does not
           come up after timeout.
        """
        #0. Poweroff selected nodes before restore. Used when restoring in
        #expansion testcase.
        for node in poweroff_nodes:
            self.poweroff_peer_node(ms_node, node)

        #1. Call restore snapshot and show the plan
        if not skip_cmd:
            self.execute_cli_restoresnapshot_cmd(ms_node, args)
            self.execute_cli_showplan_cmd(ms_node)

        #2. Wait for the MS node to become unreachable
        ms_ip = self.get_node_att(ms_node, 'ipv4')
        self.assertTrue(self.wait_for_ping(ms_ip, False, timeout_mins,
                                           retry_count=2),
                        "Node has not gone down")

        self.log('info', 'Node has gone down')
        #3. Wipe active SSH connections to force a reconnect
        self.disconnect_all_nodes()

        #4. Wait for MS to be reachable again after reboot
        self.assertTrue(self.wait_for_node_up(ms_node,
                                              wait_for_litp=True))

        #6. Wait for snapshot merge
        #Waiting for snapshot to merge
        self.log('info', 'Waiting for snapshot to merge')
        cmd = "/sbin/lvs | /bin/awk '{print $3}' | /bin/grep 'Owi'"
        self.assertTrue(self.wait_for_cmd(ms_node, cmd, 1,
                          timeout_mins=timeout_mins, su_root=True))

        #Sleep to give some final time for merge
        time.sleep(10)
        self.execute_cli_showplan_cmd(ms_node)
        #8. Turn on debug
        self.turn_on_litp_debug(ms_node)

    def execute_and_wait_createsnapshot(self, ms_node, add_to_cleanup=True,
                                        args='', remove_snapshot=True):
        """
        Creates a fresh new snapshot. Does this by first running
        remove_snapshot and then running create_snapshot and waiting until
        completion.
        Does not remove snapshot if remove_snapshot is False.
        In this case only a named snapshot can be created.

        Args:
           ms_node (str): The ms_node you wish to run the createsnapshot
           command on.

        KWargs:
          add_to_cleanup (bool): By default a new snapshot will be taken in
                                 cleanup.
                                 Set this to False to turn off this behaviour.

          args           (str): CLI args for the create_snapshot command.
                                E.G. '-n <name>'.
                                Needs to be set if creating a named snapshot.

          remove_snapshot (bool): If True will remove the deployment snapshot.
                              If False will not remove deployment snapshot.
                              NOTE: Only named snapshots can be created if
                              remove_snapshot=False.
                              Defaults to True.

        Raises:
           AssertionError. If create_snapshot command fails or node does not
           come up after timeout.

        """
        if remove_snapshot:
            _, _, re_c = self.run_command(ms_node,
                                      self.cli.get_remove_snapshot_cmd(),
                                      add_to_cleanup=add_to_cleanup)

            if re_c == 0:
                plan_success = \
                    self.wait_for_plan_state(ms_node,
                                         test_constants.PLAN_COMPLETE)
                self.assertTrue(plan_success)

        self.execute_cli_createsnapshot_cmd(ms_node, args=args,
                                            add_to_cleanup=add_to_cleanup)
        plan_success = \
            self.wait_for_plan_state(ms_node,
                                     test_constants.PLAN_COMPLETE)
        self.assertTrue(plan_success)

    def execute_and_wait_removesnapshot(self, ms_node, args='',
                                        add_to_cleanup=True):
        """
        Removes a snapshot. Does this by running remove_snapshot and waiting
        until completion.

        Args:
           ms_node (str): The ms_node you wish to run the remove_snapshot
           command on.

        Kwargs:
           args           (str): CLI args for the command, like '-n <name>'.

           add_to_cleanup (bool): By default a new snapshot will be taken in
                                 cleanup.
                                 Set this to False to turn off this behaviour.

        Raises:
           AssertionError. If remove_snapshot command fails or plan does not
                           complete within default timeout time.
           come up after timeout.

        """
        self.execute_cli_removesnapshot_cmd(ms_node, args=args,
                                            add_to_cleanup=add_to_cleanup)
        plan_success = \
            self.wait_for_plan_state(ms_node,
                                     test_constants.PLAN_COMPLETE)
        self.assertTrue(plan_success)

    def execute_expand_script(self,
                              ms_node, script_filename,
                              cluster_filename='192.168.0.42_4node.sh',
                              workspace='/home/lciadm100/jenkins/workspace/'):
        """
        Runs specified expansion scripts with specified cluster file.
        Will automatically add expanded node to connection data files.

        Args:
           ms_node (str): The ms node filename.

           script_filename (str): Name of install script.

       Kwargs:

           cluster_filename (str): Name of cluster file.

           workspace (str): The workspace folder which contains the
           stated script as files in child folders.

        Raises:
           AssertionError. If any of the script commands throws an
           error.
        """
        #1. Find path to cluster file on gateway
        cmd = "/bin/find {0} -name '{1}'"\
            .format(workspace,
                    cluster_filename)
        stdout, _, _ = self.run_command_local(cmd)
        self.assertNotEqual([], stdout)
        cluster_file = stdout[0]

        #2. Find path to install script on gateway
        cmd = "/bin/find {0} -name '{1}'"\
            .format(workspace,
                    script_filename)
        stdout, _, _ = self.run_command_local(cmd)
        self.assertNotEqual([], stdout)
        script_file = stdout[0]

        #3. Copy files to MS
        filelist = list()
        filelist.append(self.get_filelist_dict(cluster_file,
                                               '/tmp/cluster.sh'))
        filelist.append(self.get_filelist_dict(script_file,
                                               '/tmp/install.sh'))
        self.copy_filelist_to(ms_node, filelist,
                              root_copy=True)

        #3. Run script to expand cluster
        cmd = "sh /tmp/install.sh /tmp/cluster.sh"
        _, stderr, returnc = self.run_command(ms_node, cmd)
        self.assertNotEqual([], stderr)
        self.assertEqual(0, returnc)

        if 'mn3' in script_filename:
            self.add_node_to_connfile('node3', '192.168.0.235', 'litp-admin',
                                      'p3erS3rv3r', 'managed',
                                      rootpw='@dm1nS3rv3r')

        if 'mn4' in script_filename:
            self.add_node_to_connfile('node4', '192.168.0.241', 'litp-admin',
                                      'p3erS3rv3r', 'managed',
                                      rootpw='@dm1nS3rv3r')

    @staticmethod
    def _translate_task_state(task_state):
        """Method to translate task state id's

        Args:
            task_state   (int): Id of the task to translate

        Returns:
            string, with the task name
        """
        if task_state == 0:
            return "Success"
        if task_state == 1:
            return "Failed"
        if task_state == 2:
            return "Initial"
        if task_state == 3:
            return "Running"
        if task_state == 5:
            return "Stopped"
        return None

    def get_plan_task_states(self, node, task_state,
                                 username=None, password=None,
                                 expect_large_output=False):
        """Build + Run a LITP show_plan command and return specific tasks

        Args:
            node            (str): Node you want to run command on.

            task_state      (int): id of expected task state
                                   i.e. Initial, Failed, Success.
                                   These id's can be found in test_constants

        Kwargs:
            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_large_output (bool): If we expect a large plan output.\
             (ie if showplan is expected to hang for 10+ secs before returning)
        Returns:
            list, returns list of dictionaries, each dict with entry PATH
                  and MESSAGE.
        """
        # build and run create_plan command
        show_plan_cmd = self.cli.get_show_plan_cmd()

        ##We run as expects as large plan output can lock paramiko when
        #using standard executes
        if expect_large_output:
            stdout, stderr, returnc = self.run_expects_command(
                node, show_plan_cmd, [], timeout_secs=130)
        else:
            stdout, stderr, returnc = self.run_command(
                node, show_plan_cmd, username, password)

        task_id = self._translate_task_state(task_state)

        # assert expected values
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)

        plan_dict_list = list()

        plan_dict = self.cli.parse_plan_output(stdout)

        for phase in plan_dict:
            number_tasks = self.cli.get_num_tasks_in_phase(stdout, phase)

            for task in range(1, number_tasks + 1):
                status = plan_dict[phase][task]["STATUS"]
                plan_dict_final = dict()

                if task_id == status:
                    desc_size = len(plan_dict[phase][task]["DESC"])
                    plan_dict_final['PATH'] \
                            = plan_dict[phase][task]["DESC"][0]
                    plan_dict_final['MESSAGE'] \
                        = ' '.join(plan_dict[phase][task]["DESC"][1:desc_size])

                    plan_dict_list.append(plan_dict_final)

        return plan_dict_list

    def execute_cli_prepare_restore_cmd(self, node, args='',
                                          username=None, password=None,
                                          expect_positive=True,
                                          load_json=True):
        """Build + Run a LITP prepare_for_restore command.

        Args:
            node            (str): Node you want to run command on.

        Kwargs:
            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str): Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.

        Returns:
            list, list, int. std_out, std_err, rc from running
            prepare_for_restore command.
        """
        # build and run create_plan command
        prep_cmd = self.cli.get_prepare_restore_cmd(args=args)

        ##We run as expects as large plan output can lock paramiko when
        #using standard executes
        stdout, stderr, returnc = self.run_command(
            node, prep_cmd, username, password)

        # assert expected values
        if expect_positive:
            if "-j" in args and load_json:
                json_data = self.json_u.load_json(stdout)
                self.assertNotEqual(None, json_data,
                                    "JSON could not be loaded")
                stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_stopplan_cmd(self, node, args='',
                                username=None, password=None,
                                expect_positive=True, load_json=True):
        """Build + Run a LITP stop_plan command.

        Args:
            node            (str):  Node you want to run command on.

        Kwargs:
            args            (str):  CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running
            stop_plan command.
        """
        # build and run create_plan command
        stop_plan_cmd = self.cli.get_stop_plan_cmd(args=args)
        stdout, stderr, returnc = self.run_command(
            node, stop_plan_cmd, username, password,
        )

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_inherit_cmd(self, node, url, source_path, props='',
                                args='', expect_positive=True, username=None,
                                password=None, add_to_cleanup=True,
                                load_json=True):
        """Build + Run a LITP inherit command.

        Args:
            node            (str): Node you want to run command on.

            url             (str): LITP path to create.

            source_path     (str): LITP path to inherit from.

        Kwargs:
            props           (str): Inherit command properties.

            args            (str): CLI args, like '--json' and '-h'.

            username        (str): User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            add_to_cleanup  (bool): Set to False to turn off auto cleanup.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running inherit command.
        """

        # build and run inherit command
        inherit_cmd = self.cli.get_inherit_cmd(url, source_path, props, args)
        stdout, stderr, returnc = self.run_command(
            node, inherit_cmd, username, password,
            add_to_cleanup=add_to_cleanup)

        # assert expected values
        if expect_positive:
            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data

            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_show_cmd(self, node, url, args='', expect_positive=True,
                             username=None, password=None, load_json=True):
        """Build + Run a LITP show command.

        Args:
            node            (str):  Node you want to run command on.

        Kwargs:
            args            (str):  CLI args, like '--json' and '-h'.

            username        (str):  User to run command as if not default.

            password        (str):  Password to run command as if not default.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            load_json      (bool): Set to load return values into JSON.\
               Only valid if passing the -j arguments.
        Returns:
            list, list, int. std_out, std_err, rc from running
            stop_plan command.
        """
        # build and run show command
        show_cmd = self.cli.get_show_cmd(url, args)
        stdout, stderr, returnc = self.run_command(
            node, show_cmd, username, password,
        )

        # assert expected values
        if expect_positive:

            if "-j" in args and load_json:
                json_data = self.json_u.load_json(stdout)
                self.assertTrue(json_data, "JSON could not be loaded")
                stdout = json_data

            self.assertNotEqual([], stdout)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_load_cmd(self, node, url, filepath, args='',
                             expect_positive=True, username=None,
                             password=None, load_json=True):
        """
        Build + Run a LITP load command.

        Args:
            node (str): node you want to run command on.

            url (str): LITP URL.

            filepath (str): Filepath to load from.

        Kwargs:
            args (str): CLI args, like '--json' and '-h'.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            username (str): User to run command as if not default.

            password (str): Password to run command as if not default.

            load_json (bool): whether or not to load_json for the user\
               where -j is specified.
        Returns:
            list, list, int. std_out, std_err, return_code from running
            the load command.
        """

        # build and run show command
        load_cmd = self.cli.get_xml_load_cmd(url, filepath, args)
        stdout, stderr, returnc = self.run_command(
            node, load_cmd, username, password,
        )

        # assert expected values
        if expect_positive:

            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertNotEqual(None, json_data,
                                        "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_import_cmd(self, node, source_path, dest_path, args='',
                             expect_positive=True, username=None,
                             password=None, load_json=True):
        """
        Build + Run a LITP import command.

        Args:
            node (str): Node you want to run command on.

            source_path (str): The path of the rpm to import.

            dest_path (str): The path the rpm should be imported to.

        Kwargs:
            args (str): CLI args, like '--json' and '-h'.

            expect_positive (bool): Determines error checking. By default\
               assumes command will run without failure.

            username (str):  User to run command as if not default.

            password (str):  Password to run command as if not default.

            load_json (bool): Whether or not to load_json for the user\
               where -j is specified.
        Returns:
           list, list, int. std_out, std_err and return_code from running
           the import command.
        """

        # build and run show command
        load_cmd = self.cli.get_import_cmd(source_path, dest_path, args)
        stdout, stderr, returnc = self.run_command(
            node, load_cmd, username, password)

        # assert expected values
        if expect_positive:

            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertTrue(json_data, "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_import_iso_cmd(self, node, iso_mount_path, args='',
                             expect_positive=True, username=None,
                             password=None, load_json=True):
        """
        Build + Run a LITP ISO import command.

        Args:
            node (str): Node you want to run command on.

            iso_mount_path (str): The path the iso should be imported to.

        Kwargs:
            args (str): CLI args, like '--json' and '-h'.

            expect_positive (bool): Determines error checking. By default
                                   assumes command will run without failure.

            username (str):  User to run command as if not default.

            password (str):  Password to run command as if not default.

            load_json (bool): Whether or not to load_json for the user
                              where -j is specified.
        Returns:
           list, list, int. std_out, std_err and return_code from running
           the import command.
        """

        # build and run show command
        load_cmd = self.cli.get_import_iso_cmd(iso_mount_path, args)
        stdout, stderr, returnc = self.run_command(
            node, load_cmd, username, password)
        self.iso_import_command_run = True
        # assert expected values
        if expect_positive:

            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertTrue(json_data, "JSON could not be loaded")
                    stdout = json_data
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def execute_cli_export_cmd(self, node, url, filepath='', args='',
                               expect_positive=True, username=None,
                               password=None, load_json=True,
                               add_to_cleanup=True):
        """Build + Run a LITP export command.

        Args:
           node (str): Node you want to run command on.

           url (str): LITP path to export.

        Kwargs:
           filepath (str): Filepath to export to.
                           If not set xml is output to stdout.

           args (str): CLI args, like '--json' and '-h'.

           expect_positive (bool): Determines error checking. By default\
              assumes command will run without failure.

           username (str):  User to run command as if not default.

           password (str):  Password to run command as if not default.

           load_json (bool): Whether or not to load_json for the user\
              where -j is specified.

           add_to_cleanup (bool): By default will restart this service at
           the end of the test in the tearDown if it has not already been
           restarted.

        Returns:
           list, list, int. std_out, std_err and return_code from running
           the import command.
        """
        # build and run show command
        export_cmd = self.cli.get_xml_export_cmd(url, filepath, args)
        stdout, stderr, returnc = self.run_command(
            node, export_cmd, username, password,
            add_to_cleanup=add_to_cleanup)

        # assert expected values
        if expect_positive:

            if "-j" in args:
                self.assertNotEqual([], stdout)

                if load_json:
                    json_data = self.json_u.load_json(stdout)
                    self.assertTrue(json_data, "JSON could not be loaded")
                    stdout = json_data
            #if not filepath specified will return xml to stdout
            elif filepath == '':
                self.assertNotEqual([], stdout)
            else:
                self.assertEqual([], stdout)

            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual([], stderr)
            self.assertNotEqual(0, returnc)

        return stdout, stderr, returnc

    def remove_itemtype_from_model(self, ms_node, itemtype,
                                   path="/", is_collect=False):
        """
        Searches the model for all paths of the specified item type and removes
        them by running a plan.

        Note this is a non-revertible change and is intended for use when items
        in the initial deployment conflicts with a test.

        Args:
           ms_node (str): The ms node.

           itemtype (str): The item type which should be removed.

        KwArgs:

           path (str): The path in the model to look under for the item type.\
              By default searches the whole model.

           is_collect (bool): By default assumes item to delete is a child.\
              Set this to True if you wish to delete a collection.

        Returns:
           bool. True if the item type does not exist in the model or the
           plan to remove the item suceeds.
        """
        rtn_type_children = True

        if is_collect:
            rtn_type_children = False

        item_paths = self.find(ms_node, path, itemtype, rtn_type_children,
                               assert_not_empty=False)

        if item_paths == []:
            return True

        for path in item_paths:
            self.execute_cli_remove_cmd(ms_node, path)

        self.execute_cli_createplan_cmd(ms_node)
        self.execute_cli_runplan_cmd(ms_node)
        self.assertTrue(self.wait_for_plan_state(ms_node,
                                                 test_constants.PLAN_COMPLETE))
        self.execute_cli_removeplan_cmd(ms_node)

        return True

    def get_item_state(self, node, url):
        """
        Gets the state of the given path in the model.

        Args:
           node (str): The node with the deployment tree in question.

           url (str): The path to check the state of.

        Returns:
        str. The state of the item.
        """
        filter_state_cmd = self.cli.get_path_state_cmd(url)

        ##Ignore rc as we are piping commands so rc of not 0 may not be a
        #failure
        stdout, stderr, _ = self.run_command(node, filter_state_cmd)

        self.assertEqual([], stderr)
        self.assertNotEqual([], stdout)

        return stdout[0].strip()

    def execute_show_data_cmd(self, node, url, filter_value,
                              expect_positive=True, assert_value=True):
        """Executes a command to extract a data item.
        (eg a property value or a attribute such as 'links to').

        Args:
           node              (str): Node you want to run command on.

           url               (str): Path with required data item.

           filter_value      (str): The data value you wish to filter by\
              (eg state).

        Kwargs:
           expect_positive   (bool): Determines error checking. By default\
              assumes command will run without failure.

           assert_value      (bool): If set to False will not assert a value\
              is retrurned in std_out.

        Returns:
           str. The value requested.
        """
        value = None
        cmd = self.cli.get_show_data_value_cmd(url, filter_value)

        stdout, stderr, returnc = self.run_command(node, cmd)

        if assert_value:
            if expect_positive:
                self.assertEqual([], stderr)
                self.assertEqual(0, returnc)
                self.assertNotEqual([], stdout)
                value = stdout[0].strip()
            else:
                self.assertEqual([], stderr)
                self.assertEqual([], stdout)
            #NB: we don't assert RC as even without a match rc is 0.

        else:
            if stdout != []:
                value = stdout[0].strip()

        return value

    def deref_inherited_path(self, ms_node, path):
        """
        Dereference an inherited link in the LITP model. This will
        recursively follow all references until a non-reference type is
        found. I.E. The top level source item.

        E.G. If the path passed is:
            /deployments/d1/clusters/c1/nodes/n2/storage_profile,
        Then the return str will be:
            /infrastructure/storage/storage_profiles/profile_1
        as it is of non-reference type storage-profile.

        This can be seen from information below:
        #litp show -p /deployments/d1/clusters/c1/nodes/n2/storage_profile
        /deployments/d1/clusters/c1/nodes/n2/storage_profile
        inherited from: /infrastructure/storage/storage_profiles/profile_1
        type: reference-to-storage-profile

        #litp show -p /infrastructure/storage/storage_profiles/profile_1
        /infrastructure/storage/storage_profiles/profile_1
        type: storage-profile

        Args:

           ms_node (str) : The MS node.

           path (path): The path you wish to deference.

        Returns:

           str. The path to the base item after following all links.
        """

        item_type = self.execute_show_data_cmd(ms_node, path, "type")
        if item_type.startswith("reference-to-"):
            links_to_path = self.execute_show_data_cmd(ms_node, path,
                                                       "inherited from")

            return self.deref_inherited_path(ms_node, links_to_path)

        return path

    # Group 10 - Other
    def join_paths(self, path1, path2):
        """Joins two filepaths together ensuring only one '/'
        is used between them.

        Args:

           path1  (str): The first filepath

           path2  (str): The filepath to append to the first filepath

        Returns:
           str. The two paths joined together.
        """
        return self.g_util.join_paths(path1, path2)

    def is_text_in_list(self, text, list_item):
        """Checks to see if the text passed exists within
        any item in the list.

        Args:

           text      (str): The string to test for.

           list_item (str): The list to check.

        Returns:
           bool. True if the item is found or False otherwise.
        """
        return self.g_util.is_text_in_list(text, list_item)

    def is_text_in_list_regex(self, pattern_obj, list_item):
        """Checks using a Regular Expression or RegexObject to see if the
        pattern exists within any item in the list.

        Args:
           pattern_obj (str)/(RegexObject): The Regular Expression, or compiled
           RegexObject to test for.

           list_item (list): The list to check.

        Returns:
            bool. True if item found or False otherwise.
        """
        return self.g_util.is_text_in_list_regex(pattern_obj, list_item)

    def count_text_in_list(self, text, list_item):
        """Counts the number of lines where text exists
        in the list.

        Args:
           text      (str): The string to test for.

           list_item (str): The list to check.

        Returns:
           int. the number of list items that contain this path
        """

        return self.g_util.count_text_in_list(text, list_item)

    def __parse_json_props(self, stdout, filter_prop):
        """
        Parse the returned stdout from a litp show command
        run with the 'j option and return a dict of all props or
        the value of the one selected property.

        Args:
        stdout (list): Stdout from the show command ran.

        filter_prop (str): The property to filter by or None if no
                           filter should be done.

        Returns:
         dict or str. If filter prop is set returns the value of that
        property or None if the property cannot be found. If no filter
        property is set then all properties are returned as a dict.
        """
        processed_props = None

        processed_props = self.cli.get_properties(stdout)
                ##IF JSON AND FILTER PROP
        if filter_prop:
            filtered_prop = None

            for line in processed_props:
                if filter_prop == line:
                    filtered_prop = str(processed_props[line])
                    break

            return filtered_prop

        # We want to return a dict without unicode 'u' notation
        process_props_str = \
            self.g_util.remove_unicode_from_dict(processed_props)

        return process_props_str

    @staticmethod
    def __parse_std_props(stdout, filter_prop):
        """
        Parse the returned stdout from a litp show command
        and return a dict of all props or the value of the one
        selected property.

        Args:
        stdout (list): Stdout from the show command ran.

        filter_prop (str): The property to filter by or None if no
                           filter should be done.

        Returns:
        dict or str. If filter prop is set returns the value of that
        property or None if the property cannot be found. If no filter
        property is set then all properties are returned as a dict.
        """

        processed_props = None
        ##If we are filtering by a single property
        if filter_prop:
            filtered_prop = None
            startat = False
            for line in stdout:
                ##Start checking for filter prop as we are in prop list
                if "properties" in line and ":" in line:
                    startat = True
                ##Filter prop found in line
                if filter_prop in line and startat:
                    ##We check len to ensure we have the right prop
                    #(ie size vs snap_size)
                    prop_len = len(filter_prop)
                    if len(line.split(":", 1)[0].strip()) != prop_len:
                        continue
                    #Get filter prop value by splitting line on ':'
                    filtered_prop = line.split(":", 1)[-1][1:]
                    break

            ##Return filter prop, set to None if not found
            return filtered_prop

        process_props_str = dict()
        startat = False

        for line in stdout:
            if startat:
                ##Break if we reach children: str, we have
                ##reached line beyond properties
                if "children:" in line:
                    break
                if ":" in line:
                    #split each property on the ':'
                    line1 = line.split(":", 1)
                    ##Name of prop is string before ':'
                    prop_name = str(line1[0].replace(" ", ""))
                    ##Value of prop is string after ':'
                    prop_value = str(line1[1][1:])
                    process_props_str[prop_name] \
                        = prop_value
            if "properties" in line:
                startat = True
        print process_props_str

        processed_props = process_props_str

        return processed_props

    def get_props_from_url(self, node, url, filter_prop=None,
                           show_option="-j", log_output=False):
        """Returns a dict of the properties in the url passed or if filter
        is set returns the value of a single property as a string.

        Args:
           node      (str): The node to run the command on.

           url (str): The litp path to check for properties.

        Kwargs:

           filter_prop (str): If set will return just this property\
           as a string.

           show_option (str): -j chosen by default, but if want to run\
           without -j option then pass show_option=""

           log_output (bool): If set will log the JSON output from show. Note
           this may flood logs.

        Returns:
           dict or str. If filter prop is set returns the value of that
           property or None if the property cannot be found. If no filter
           property is set then all properties are returned as a dict.
        """

        show_prop_cmds = self.cli.get_show_cmd(url)

        # stdout, _, _ = self.run_command(node, show_prop_cmds)
        ##Logging the JSON can flood the test output
        stdout, _, _ = self.run_expects_command(node, show_prop_cmds, [])

        if stdout == [] \
                or not self.is_text_in_list('properties', stdout):
            return None

        ###IF JSON OUTPUT
        if show_option == "-j":
            show_prop_cmds_json = self.cli.get_show_cmd(url, show_option)
            stdout, _, _ = self.run_command(node, show_prop_cmds_json,
                                            logging=log_output)
            return self.__parse_json_props(stdout, filter_prop)
        else:
            return self.__parse_std_props(stdout, filter_prop)

    def restart_litpd_service(self, ms_node, debug_on=True):
        """
        Restarts the litpd service on the selected node.
        After restarting turns on debugging again.

        Args:
           ms_node (str): The node with the LITP service.

           debug_on (bool): If set to False will not turn debug on
                            after restart.

        Results:
           Asserts that the service restarts and debug is set to on
           without error.
        """
        restart_cmd = self.rhc.get_systemctl_restart_cmd("litpd")
        stdout, stderr, rc = self.run_command(ms_node,
                                              restart_cmd, su_root=True,
                                              su_timeout_secs=200)

        self.assertEqual([], stderr)
        self.assertEqual([], stdout)
        self.assertEqual(rc, 0)

        ##If we have started successfully we don't need to start again in
        ##tearDown
        if rc == 0:
            for service in list(self.stopped_service_list):
                if service['NODE'] == ms_node and \
                        service['NAME'] == 'litpd':
                    self.stopped_service_list.remove(service)

        if debug_on:
            self.turn_on_litp_debug(ms_node)

    def systemctl_daemon_reload(self, ms_node, su_root=True):
        """
        Reloads systemctl daemon to avoid warnings on service
        restart

        Args:
            ms_node (str): The node with the LITP service.

        Kwargs:
           assert_success (bool): By default asserts actions
                                  succeeds

           su_root        (bool): Set to True to run command
                                  as root
        """
        cmd = self.rhc.get_systemctl_reload_cmd()

        _, _, _ = self.run_command(ms_node, cmd, su_root=su_root,
                                   default_asserts=True)

    def turn_on_litp_debug(self, ms_node, assert_success=True):
        """
        Runs the command to turn on litp debug.

        Args:
            ms_node (str): The node with the LITP service.

        Kwargs:
           assert_success (bool): By default asserts action
           succeeds.
        """
        turn_on_debug_cmd = self.cli.get_litp_debug_cmd()

        _, stderr, rc = self.run_command(ms_node,
                                    turn_on_debug_cmd)

        if assert_success:
            self.assertEqual(rc, 0)
            self.assertEqual([], stderr)

    def is_litp_debug_enabled(self, ms_node):
        """
        Checks if litp debug logging is enabled

        Args:
            ms_node (str): The node with the LITP service.

        Returns:
            bool. True if enabled or False otherwise.
        """
        url = self.find(ms_node, '/litp', 'logging')[0]
        props = self.get_props_from_url(ms_node, url)

        if props['force_debug'] == 'true':
            return True
        else:
            return False

    def restart_service(self, ms_node, service_name, assert_success=True,
                        su_root=True, su_timeout_secs=120):
        """
        Restarts the a service on the selected node.

        Args:
           ms_node (str): The node with the LITP service.

           service_name (str): Name of service to restart.

           assert_success (bool): By default asserts a service restarts
           successfully. If set to False will not assert this.

           su_root (bool): If set, runs the command as root.

           su_timeout_secs (int): Default timeout for root commands to
           finish running.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        restart_cmd = self.rhc.get_systemctl_restart_cmd(service_name)

        stdout, stderr, rc = self.run_command(ms_node, restart_cmd,
                                              su_root=su_root,
                                              su_timeout_secs=su_timeout_secs)

        if assert_success:

            self.assertEqual([], stderr)
            self.assertEqual([], stdout)
            self.assertEqual(rc, 0)

        return stdout, stderr, rc

    def start_service(self, node, service_name, assert_success=True,
                      su_root=True):
        """
        Starts the service on the selected node.

        Args:
            node (str): The node with the LITP service.

            service_name (str): Name of service to start.

        Kwargs:
            assert_success (bool): By default asserts a service starts
            successfully. If set to False will not assert this.

            su_root (bool): If set, runs the command as root.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        start_cmd = self.rhc.get_systemctl_start_cmd(service_name)

        stdout, stderr, rc = self.run_command(node,
                                              start_cmd, su_root=su_root)

        if assert_success:
            self.assertEqual([], stderr)
            self.assertEqual([], stdout)
            self.assertEqual(rc, 0)

        ##If we have started successfully we don't need to start again in
        ##tearDown
        if rc == 0:
            for service in list(self.stopped_service_list):
                if service['NODE'] == node and service['NAME'] == service_name:
                    self.stopped_service_list.remove(service)

        return stdout, stderr, rc

    def get_service_pid(self, node, service_name, su_root=True):
        """
        Gets the pid of the selected service on the selected node.

        Args:
            node (str): The node with the LITP service.

            service_name (str): Name of service to query.

        Kwargs:
            assert_running (bool): By default asserts a service is
            in state running. If set to False will do no asserting.
            su_root (bool): If set, runs the command as root.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command. Returns list after running the command.
        """
        mainpid_cmd = self.rhc.get_systemctl_mainpid(service_name)

        stdout, stderr, rc = self.run_command(node,
                                              mainpid_cmd, su_root=su_root)
        return stdout, stderr, rc

    def get_service_status_cmd(self, ms_node, service_name,
                               assert_running=True):
        """
        Gets the status of the selected service on the selected node.
        By default asserts it is running.

        Args:
            ms_node (str): The node with the LITP service.

            service_name (str): Name of service to query.

        Kwargs:
            assert_running (bool): By default asserts a service is
            in state running. If set to False will do no asserting.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        return self.get_service_status(ms_node, service_name, assert_running)

    def get_service_status(self, node, service_name,
                         assert_running=True, su_root=True):
        """
        Gets the status of the selected service on the selected node.
        By default asserts it is running.

        Args:
            node (str): The node with the LITP service.

            service_name (str): Name of service to query.

        Kwargs:
            assert_running (bool): By default asserts a service is
            in state running. If set to False will do no asserting.

            su_root (bool): If set, runs the command as root.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        status_cmd = self.rhc.get_systemctl_is_active_cmd(service_name)
        running_status = ['active']

        stdout, stderr, rc = self.run_command(node,
                                              status_cmd, su_root=su_root)

        if assert_running:
            self.assertEqual([], stderr)
            self.assertEqual(running_status, stdout)
            self.assertEqual(rc, 0)

        return stdout, stderr, rc

    def check_mco_puppet_is_enabled(self, ms_node):
        """
        This method checks the status of puppet through mco to test if enabled

        Args:
            ms_node (str): The node with the mco service.

        Returns:
            Boolean. If running returns True, if not False
        """
        status_cmd = "/usr/bin/mco puppet status"
        stdout, stderr, rc = \
                        self.run_command(ms_node, status_cmd, su_root=True)

        self.assertEqual([], stderr)
        self.assertNotEqual([], stdout)
        self.assertEqual(rc, 0)
        start_check = False
        for line in stdout:
            if "disabled = 3" in line and start_check:
                return False
            if "enabled = 3" in line and start_check:
                return True
            if "Summary of Enabled:" in line:
                start_check = True

        return False

    def stop_service(self, node, service_name, assert_success=True,
                     kill_service=False, kill_args='', add_to_cleanup=True,
                     su_root=True, celery_worker='', su_timeout_secs=120,
                     execute_timeout=0.25, connection_timeout_secs=600):
        """
        Stops the service on the selected node.

        Args:
           node (str): The node with the LITP service.

           service_name (str): Name of service to stop.

        Kwargs:
           assert_success (bool): By default asserts a service stops
           successfully. If set to False will not assert this.

           kill_service (bool): By default issues a service stop command to
           stop the service. If this is set will instead kill the service
           pid (simulate unclear shutdown)

           kill_args (str): Can add extra arguments to use in the kill command.

           add_to_cleanup (bool): By default will restart this service at
           the end of the test in the tearDown if it has not already been
           restarted.

           su_root (bool): If set, runs the command as root.

          celery_worker (str): The name of the specific celery worker to kill
          when killing part of celery.

        Returns:
            list, list, int. Returns stdout, stderr and rc after running the
            command.
        """
        if add_to_cleanup:
            stopped_service = dict()
            stopped_service['NODE'] = node
            stopped_service['NAME'] = service_name

            self.stopped_service_list.append(stopped_service)

        if kill_service:
            ##First find the PID
            _, _, _ =  \
                self.get_service_status_cmd(node, service_name)

            stdout, _, _ = \
                            self.get_service_pid(node, service_name)

            if celery_worker:
                pid_num = \
                    self.get_service_pid_from_stdout(stdout, celery_worker)
            else:
                pid_num = \
                    self.get_service_pid_from_stdout(stdout, service_name)

            self.assertTrue(pid_num, "Unable to find PID for process {0}"\
                                .format(service_name))
            ##Now kill the process
            kill_cmd = "/bin/kill {0} {1}".format(kill_args,
                                                  pid_num)

            stdout, stderr, rc = self.run_command(node,
                            kill_cmd, su_root=su_root,
                            su_timeout_secs=su_timeout_secs,
                            execute_timeout=execute_timeout,
                            connection_timeout_secs=connection_timeout_secs)

            if assert_success:
                self.assertEqual([], stderr)
                self.assertEqual([], stdout)
                self.assertEqual(rc, 0)

        else:
            stop_cmd = self.rhc.get_systemctl_stop_cmd(service_name)

            stdout, stderr, rc = self.run_command(node,
                            stop_cmd, su_root=su_root,
                            su_timeout_secs=su_timeout_secs,
                            execute_timeout=execute_timeout,
                            connection_timeout_secs=connection_timeout_secs)

            if assert_success:
                self.assertEqual([], stderr)
                self.assertEqual([], stdout)
                if rc:
                    # Do a check to see if the service is dead
                    # If that check fails (status has 0 return because its up)
                    # need to raise a failure here because
                    # we have been unsuccessful in stopping the service
                    _, _, status_rc = \
                        self.get_service_status(node,
                                                service_name,
                                                assert_running=False)
                    self.assertNotEqual(status_rc, 0)
                else:
                    self.assertEqual(rc, 0)

        return stdout, stderr, rc

    @staticmethod
    def get_service_pid_from_stdout(stdout, service_name):
        """
        Description:
            Processes the output of the get_service_status_cmd function
            and returns the processid for the service.
            Output for rabbitmq-server is different than other services.

        Args:
           stdout (list) : Output from function get_service_status_cmd.

           service_name (str) : Service for which process ID is wanted.

        Returns:
            int. An integer representing the service process id.
        """
        if 'node' in service_name:
            for line in stdout:
                if service_name in line:
                    return line.split('pid')[1].split(')')[0].strip()
        elif 'rabbit' not in service_name:
            pid_str = ''.join(stdout)
            pid_num = pid_str.split("=", 1)[1]
            return pid_num
        else:
            pid = stdout[1].split('pid')
            pid_num = pid[1].split('}')[0].strip().split(',')[1]
            return pid_num

    # Group 11 user related
    @staticmethod
    def __get_usr_del_dict(node, username):
        """Returns a dictionary of node-username.
        Private method used in automated cleanup.

        Args:
           node (str) : The node the user was added to
           username (str) : The username that was added

        Returns:
         dict. A dict containing the node and user passed.
       """
        added_usr = dict()
        added_usr['node'] = node
        added_usr['usr'] = username

        return added_usr

    def create_posix_usr(self, node, username, password, del_usr=True):
        """Creates a new posix user on the passed node with the
        specified username and password.

        Args:
           node (str) : The node to create the user on as determined by the\
              filename.

           username (str) : The username to create.

           password (str) : The password to assign to the new user.

        Kwargs:
           del_usr (bool) : If set to False the user is not deleted at end\
              of the test.

        Returns:
           bool. True if user creation suceeds or false otherwise.
        """
        create_user_cmd = "/usr/sbin/useradd {0}".format(username)

        _, _, rcode = self.run_command(
            node, create_user_cmd, su_root=True
        )

        if rcode != 0:
            return False

        if del_usr:
            self.users_to_delete.append(self.__get_usr_del_dict(node,
                                                                username))

        setps_cmd = "passwd {0}".format(username)

        setpw_cmds = list()
        setpw_cmds.append(self.get_expects_dict("New password",
                                                password))
        setpw_cmds.append(self.get_expects_dict("Retype new password",
                                                password))

        rootpw = self.get_node_att(node, "rootpw")

        if not rootpw:
            self.log("error", "Unable to find root password")
            return False

        _, _, rcode = self.run_expects_command(node, setps_cmd, setpw_cmds,
                                               "root", rootpw)

        if rcode != 0:
            return False

        return True

    def delete_posix_usr(self, node, username):
        """Deletes the specified user on the specified node.

        Args:

         node (str): The node you wish to delete the user from as idenfited by\
            connection data.

         username (str): The username to delete.

        Returns:

           bool. True is user is deleted successfully or False otherwise.
        """

        del_usr_cmd = self.rhc.get_remove_posix_usr_cmd(username)

        _, stderr, returnc = self.run_command(node, del_usr_cmd, su_root=True)

        if returnc != 0:
            self.log("error", "Could not delete user: {0}".format(stderr))
            return False

        return True

    def create_litprc(self, node, username, password):
        """Creates litprc file with the passed user credentials and
        copies it the that users home directory.

        Args:

          node (str) : The node to create the .litprc file in.

          username (str) : The username of the user.

          password (str) : The password of the user.

        Returns:
          bool. True if the file is created successfully or False otherwise.
        """

        litprc_contents = "[session]\nusername = {0}\npassword = {1}" \
            .format(username, password)

        create_litprc_cmd = "echo '{0}' > {1} && chmod 600 {2}".format(
            litprc_contents,
            test_constants.AUTHTICATE_FILENAME,
            test_constants.AUTHTICATE_FILENAME)

        _, stderr, returnc = self.run_command(node,
                                              create_litprc_cmd,
                                              username,
                                              password)

        if returnc != 0:
            self.log(
                "error",
                "Could not create .litprc file: {0}".format(stderr)
            )
            return False

        return True

###SFS RELATED
    def is_filesystem_mounted(self, node, mount_point):
        """
        Runs the mount list command on the specified node
        and retrurns true if passed mount point is found or False otherwise.

        Args:
        node (str): The filename of the node in question

        mount_point (str): The str to search for in the mount list.

        Returns:
        bool. True if mountpoint found or False otherwise.
        """
        mount_cmd = self.sto.get_mount_list_cmd(grep_item=mount_point)

        std_out, std_err, returnc = self.run_command(node, mount_cmd,
                                                     su_root=True)

        #If grep not found or any errors return False
        if std_out == [] or std_err != [] or returnc != 0:
            return False

        return True

    def get_sfs_filesystem_list(self, nas_server):
        """
        Returns list of filesystems on the NAS server. Returns filename and a
        list of other attributes in a dictionary. There are 3 different types
        of NAS servers: VA 7.4, VA 7.2 and SFS. The output of the command
        'storage fs list' is different on each of the NAS Server types.

        Args:
           nas_server (str): Name of the NAS server.

        Returns:
            nas_fs_list (list): List of dictionaries indexed by different
            attributes. The attributes vary based on which server the
            fs command 'storage fs list' is ran on.
            None is returned if no shares are found.
        """
        nas_fs_list = list()

        nas_fs_cmd = "storage fs list"

        server_info = self.get_nas_server_type()
        server_type = server_info[0]
        server_version = server_info[1]

        # Connect to NAS as a master user
        self.assertTrue(self.set_node_connection_data(
            nas_server,
            username=test_constants.SFS_MASTER_USR,
            password=test_constants.SFS_MASTER_PW))

        stdout, stderr, rc = self.run_command(nas_server, nas_fs_cmd)

        if rc != 0 or stderr != []:
            return None

        # Removing the first two lines in stdout so that the correct output
        # is read, in the following commands.
        stdout.remove(stdout[1])
        stdout.remove(stdout[0])

        for fsn in stdout:
            fs_fields = fsn.split()
            fs_entry = dict()

            # These fields are in all NAS Server types
            fs_entry[self.sfs_fs_key] = fs_fields[0]
            fs_entry[self.sfs_fs_status_key] = fs_fields[1]
            fs_entry[self.sfs_fs_size_key] = fs_fields[2]
            fs_entry[self.sfs_fs_layout_key] = fs_fields[3]
            fs_entry[self.sfs_fs_mirror_key] = fs_fields[4]
            fs_entry[self.sfs_fs_column_key] = fs_fields[5]
            fs_entry[self.sfs_fs_use_key] = fs_fields[6]

            if server_type == self.va_full_name and server_version == '7.4':
                # VA 7.4
                fs_entry[self.sfs_fs_used_key] = fs_fields[7]
                fs_entry[self.sfs_fs_shared_key] = fs_fields[8]
                fs_entry[self.sfs_fs_cifsshared_key] = fs_fields[9]
                fs_entry[self.sfs_fs_ftpshared_key] = fs_fields[10]
                fs_entry[self.sfs_fs_sectier_key] = fs_fields[11]
                # The output from "storage fs list" does not contain info on
                # what pool the FS is in - use find_pool_for_fs to obtain this
                fs_entry[self.sfs_fs_pool_key] = \
                    self.find_pool_for_fs(nas_server, fs_fields[0])
                nas_fs_list.append(fs_entry)

            elif server_type == self.va_full_name and server_version == '7.2':
                # VA 7.2
                fs_entry[self.sfs_fs_shared_key] = fs_fields[7]
                fs_entry[self.sfs_fs_cifsshared_key] = fs_fields[8]
                fs_entry[self.sfs_fs_ftpshared_key] = fs_fields[9]
                fs_entry[self.sfs_fs_sectier_key] = fs_fields[10]
                # The output from "storage fs list" does not contain info on
                # what pool the FS is in - use find_pool_for_fs to obtain this
                fs_entry[self.sfs_fs_pool_key] = \
                    self.find_pool_for_fs(nas_server, fs_fields[0])
                nas_fs_list.append(fs_entry)

            elif server_type == self.sfs_full_name:
                # SFS
                fs_entry[self.sfs_fs_shared_key] = fs_fields[7]
                fs_entry[self.sfs_fs_cifsshared_key] = fs_fields[8]
                fs_entry[self.sfs_fs_ftpshared_key] = fs_fields[9]
                fs_entry[self.sfs_fs_sectier_key] = fs_fields[10]
                fs_entry[self.sfs_fs_pool_key] = fs_fields[11]
                nas_fs_list.append(fs_entry)

        return nas_fs_list

    def find_pool_for_fs(self, sfs_node, fs_name):
        """
        Gets the name of the sfs pool the provided fs is contained in.

        Args:
           sfs_node    (str): filename of the sfs.
           fs_name     (str): name of the filesystem

        Returns:
            String. Name of the pool the filesystem is in or None if not found
        """
        cmd = "storage fs list {0}".format(fs_name)
        stdout, _, _ = self.run_command(sfs_node, cmd)
        token = "List of pools:"
        for line in stdout:
            if token in line:
                return line.split(token)[-1].strip()
        return None

    def is_sfs_filesystem_present(self, sfs_node, fs_name,
        status=None, size=None, layout=None, mirror=None,
        column=None, use=None, shared=None, cifsshared=None,
        ftpshared=None, sectier=None, pool=None):
        """
        Tests whether a specific filesystem is present on the passed sfs
        server. Optionally tests whther a specific attribute
        set is also set for the fs item.

        Args:
           node    (str): filename of the sfs.

           fs_name (str): Name of the filesystem to check for.

        Kwargs:
           status (str): If set will only return True if the status as well as
                         any other selected values match.

           size (str): If set will only return True if the size(e.g.100M, 2G)')
                        as well as any other selected values match.

           layout (str): If set will only return True if the layou
                        as well as any other selected values match.

           mirror (str): If set will only return True if the mirror
                        as well as any other selected values match.

           column (str): If set will only return True if the column
                        as well as any other selected values match.

           use (str): If set will only return True if the use
                        as well as any other selected values match.

           shared (str): If set will only return True if the shared
                        as well as any other selected values match.

           cifsshared (str): If set will only return True if the cifsshared
                        as well as any other selected values match.

           ftpshared (str): If set will only return True if the ftpshared
                        as well as any other selected values match.

           sectier (str): If set will only return True if the sectier
                        as well as any other selected values match.

           pool (str): If set will only return True if the pool
                        as well as any other selected values match.

        Returns:
            bool. True if all selected parameters match or False otherwise.
        """
        ###Get a list of all shares
        fs_list = self.get_sfs_filesystem_list(sfs_node)
        ##We always try to match the path parameter
        fs_path = False

        #Initially set to True assuming none are passed in so we ignore these
        #values
        status_v = True
        size_v = True
        layout_v = True
        mirror_v = True
        column_v = True
        use_v = True
        shared_v = True
        cifsshared_v = True
        ftpshared_v = True
        sectier_v = True
        pool_v = True

        for fsn in fs_list:
            #If we find share name set share_path to True
            if fs_name in fsn[self.sfs_fs_key]:
                fs_path = True

                #If an status has been sent in set bool to False unless
                #we find a match
                if status != None:
                    status_v = False
                    if status in fsn[self.sfs_fs_status_key]:
                        status_v = True

                #If an size has been sent in set bool to False unless
                #we find a match
                if size != None:
                    size_v = False
                    if size in fsn[self.sfs_fs_size_key]:
                        size_v = True

                #If an layout has been sent in set bool to False unless
                #we find a match
                if layout != None:
                    layout_v = False
                    if layout in fsn[self.sfs_fs_layout_key]:
                        layout_v = True

                #If an mirror has been sent in set bool to False unless
                #we find a match
                if mirror != None:
                    mirror_v = False
                    if mirror in fsn[self.sfs_fs_mirror_key]:
                        mirror_v = True

                #If an column has been sent in set bool to False unless
                #we find a match
                if column != None:
                    column_v = False
                    if column in fsn[self.sfs_fs_column_key]:
                        column_v = True

                #If an use has been sent in set bool to False unless
                #we find a match
                if use != None:
                    use_v = False
                    if use in fsn[self.sfs_fs_use_key]:
                        use_v = True

                #If an shared has been sent in set bool to False unless
                #we find a match
                if shared != None:
                    shared_v = False
                    if shared in fsn[self.sfs_fs_shared_key]:
                        shared_v = True

                #If an cifsshared has been sent in set bool to False unless
                #we find a match
                if cifsshared != None:
                    cifsshared_v = False
                    if cifsshared in fsn[self.sfs_fs_cifsshared_key]:
                        cifsshared_v = True

                #If an ftpshared has been sent in set bool to False unless
                #we find a match
                if ftpshared != None:
                    ftpshared_v = False
                    if ftpshared in fsn[self.sfs_fs_ftpshared_key]:
                        ftpshared_v = True

                #If an sectier has been sent in set bool to False unless
                #we find a match
                if sectier != None:
                    sectier_v = False
                    if sectier in fsn[self.sfs_fs_sectier_key]:
                        sectier_v = True

                #If an pool has been sent in set bool to False unless
                #we find a match
                if pool != None:
                    pool_v = False
                    if pool in fsn[self.sfs_fs_pool_key]:
                        pool_v = True

                #If we have a match on all required items return True
                if fs_path and status_v and size_v and layout_v and mirror_v \
                        and column_v and use_v and shared_v and cifsshared_v \
                        and ftpshared_v and sectier_v and pool_v:
                    return True

        return False

    def get_sfs_snapshot_list(self, sfs_node):
        """
        Gets all snapshots listed on the sfs node and returns them as a
        list of dicts dictionary.

        Args:
           sfs_node    (str): filename of the sfs.

        Returns:
           list. List of dict indexed by keys, NAME, TYPE, FS, DATE, TIME
           None if no snapshots are found.
        """
        sfs_show_list = list()

        sfs_show_cmd = "storage rollback list"

        stdout, stderr, rc = self.run_command(sfs_node, sfs_show_cmd)

        if rc != 0 or stderr != []:
            return None

        for snapshot in stdout:
            snapshot_fields = snapshot.split()
            if len(snapshot_fields) == 5:
                sfs_entry = dict()
                sfs_entry[self.sfs_snapshot_name_key] = snapshot_fields[0]
                sfs_entry[self.sfs_snapshot_type_key] = snapshot_fields[1]
                sfs_entry[self.sfs_snapshot_fs_key] = snapshot_fields[2]
                sfs_entry[self.sfs_snapshot_date_key] = snapshot_fields[3]
                sfs_entry[self.sfs_snapshot_time_key] = snapshot_fields[4]
                sfs_show_list.append(sfs_entry)

        return sfs_show_list

    def is_sfs_snapshot_present(self, sfs_node, snapshot_name,
                                snapshot_type=None, snapshot_fs=None,
                                 snapshot_date=None, snapshot_time=None):
        """
        Tests whether a specific share is present on the passed sfs
        server. Optionally tests whther a specific IP or permission
        set is also set for the share item.

        Args:
           sfs_node    (str): filename of the sfs.

           snapshot_name (str): Name of the cache to check for.

        Kwargs:
           snapshot_type (str): If set will only return True if the snapshot
                as well as any other selected values match.

           snapshot_fs (str): If set will only return True if the snapshot
            used matches with all other checked values.

           snapshot_date (str): If set will only return True if the snapshot
            used matches with all other checked values.

           snapshot_time (str): If set will only return True if the snapshot
            used matches with all other checked values.

        Returns:
        bool. True if all selected parameters match or False otherwise.
        """
        ###Get a list of all shares
        snapshot_list = self.get_sfs_snapshot_list(sfs_node)
        ##We always try to match the path parameter
        snapshot_path = False

        #Initially set to True assuming none are passed in so we ignore these
        #values

        type_snapshot = True
        fs_snapshot = True
        date_snapshot = True
        time_snapshot = True

        for snapshot in snapshot_list:
            #If we find cache name set share_path to True
            if snapshot_name in snapshot[self.sfs_snapshot_name_key]:
                snapshot_path = True

                #If snapshot type has been sent in set bool to False unless
                #we find a match
                if snapshot_type != None:
                    type_snapshot = False
                    if snapshot_type in snapshot[self.sfs_snapshot_type_key]:
                        type_snapshot = True

                #If snapshot fs has been sent in set bool to False unless
                #we find a match
                if snapshot_fs != None:
                    fs_snapshot = False
                    if snapshot_fs in snapshot[self.sfs_snapshot_fs_key]:
                        fs_snapshot = True

                #If snapshot date has been sent in set bool to False unless
                #we find a match
                if snapshot_date != None:
                    date_snapshot = False
                    if snapshot_date in snapshot[self.sfs_snapshot_date_key]:
                        date_snapshot = True

                #If snapshot type has been sent in set bool to False unless
                #we find a match
                if snapshot_time != None:
                    time_snapshot = False
                    if snapshot_time in snapshot[self.sfs_snapshot_time_key]:
                        time_snapshot = True

                #If we have a match on all required items return True
                if snapshot_path and type_snapshot and fs_snapshot \
                        and date_snapshot and time_snapshot:
                    return True

        return False

    def get_sfs_cache_list(self, sfs_node):
        """
        Gets all cache listed on the sfs node and returns them as a
        list of dicts dictionary.

        Args:
           sfs_node    (str): filename of the sfs.

        Returns:
           list. List of dict indexed by keys, NAME, TOTAL, USED, PERCENT,
           AVAILABLE, PERCENT_AVAIL, SDCNT. None if no snapshots are found.
        """
        sfs_show_list = list()

        sfs_show_cmd = "storage rollback cache list"

        stdout, stderr, rc = self.run_command(sfs_node, sfs_show_cmd)

        if rc != 0 or stderr != []:
            return None

        for cache in stdout:
            cache_fields = cache.split()
            if len(cache_fields) == 7:
                sfs_entry = dict()
                sfs_entry[self.sfs_cache_name_key] = cache_fields[0]
                sfs_entry[self.sfs_cache_total_key] = cache_fields[1]
                sfs_entry[self.sfs_cache_used_key] = cache_fields[2]
                sfs_entry[self.sfs_cache_percent_key] = cache_fields[3]
                sfs_entry[self.sfs_cache_available_key] = cache_fields[4]
                sfs_entry[self.sfs_cache_percent_avail_key] = cache_fields[5]
                sfs_entry[self.sfs_cache_sdcnt_key] = cache_fields[6]
                sfs_show_list.append(sfs_entry)

        return sfs_show_list

    def is_sfs_cache_present(self, sfs_node, cache_name, cache_total=None, \
            cache_used=None, cache_percent=None, cache_available=None, \
            cache_percent_available=None, cache_sdcnt=None):
        """
        Tests whether a specific share is present on the passed sfs
        server. Optionally tests whther a specific IP or permission
        set is also set for the share item.

        Args:
           sfs_node    (str): filename of the sfs.

           cache_name (str): Name of the cache to check for.

        Kwargs:
           cache_total (str): If set will only return True if the cache
                as well as any other selected values match.

           cache_used (str): If set will only return True if the cache
            used matches with all other checked values.

           cache_percent (str): If set will only return True if the cache
            percent matches with all other checked values.

           cache_available (str): If set will only return True if the cache
            available matches with all other checked values.

           cache_percent_available (str): If set will only return True if the\
            cache percent available matches with all other checked values.

           cache_sdcnt (str): If set will only return True if the cache
            sdcnt matches with all other checked values.

        Returns:
        bool. True if all selected parameters match or False otherwise.
        """
        ###Get a list of all shares
        cache_list = self.get_sfs_cache_list(sfs_node)
        ##We always try to match the path parameter
        cache_path = False

        #Initially set to True assuming none are passed in so we ignore these
        #values

        total_cache = True
        used_cache = True
        percent_cache = True
        available_cache = True
        available_percent_cache = True
        sdcnt_cache = True

        for cache in cache_list:
            #If we find cache name set share_path to True
            if cache_name in cache[self.sfs_cache_name_key]:
                cache_path = True

                #If cache total has been sent in set bool to False unless
                #we find a match
                if cache_total != None:
                    total_cache = False
                    if cache_total in cache[self.sfs_cache_total_key]:
                        total_cache = True

                #If cache used has been sent in set bool to False unless
                #we find a match
                if cache_used != None:
                    used_cache = False
                    if cache_used in cache[self.sfs_cache_used_key]:
                        used_cache = True

                #If cache percent has been sent in set bool to False unless
                #we find a match
                if cache_percent != None:
                    percent_cache = False
                    if cache_percent in cache[self.sfs_cache_percent_key]:
                        percent_cache = True

                #If cache available has been sent in set bool to False unless
                #we find a match
                if cache_available != None:
                    available_cache = False
                    if cache_available in cache[self.sfs_cache_available_key]:
                        available_cache = True

                #If cache percent available has been sent in set bool to False
                #unless we find a match
                if cache_percent_available != None:
                    available_percent_cache = False
                    if cache_percent_available in \
                        cache[self.sfs_cache_percent_avail_key]:
                        available_percent_cache = True

                #If cache used has been sent in set bool to False unless
                #we find a match
                if cache_sdcnt != None:
                    sdcnt_cache = False
                    if cache_sdcnt in cache[self.sfs_cache_sdcnt_key]:
                        sdcnt_cache = True

                #If we have a match on all required items return True
                if cache_path and total_cache and used_cache and \
                        percent_cache and available_cache \
                        and available_percent_cache and sdcnt_cache:
                    return True

        return False

    def get_sfs_shares_list(self, sfs_node):
        """
        Gets all nfs shares listed on the sfs node and returns them as a
        list of dicts dictionary.

        Args:
           sfs_node    (str): filename of the sfs.

        Returns:
        list. List of dict indexed by PATH, IP, PERM keys. None if no shares
        are found.
        """

        sfs_show_cmd = "nfs share show"

        stdout, stderr, rc = self.run_command(sfs_node, sfs_show_cmd)

        if rc != 0 or stderr != []:
            return None

        # When 'nfs share show' runs, all three values it expects are found on
        # the same line; Path, IP and NFS options.
        # However some cases that use VA 7.4, nfs_options can not be found on
        # the same line as the other values(Path & IP) OR nfs_options itself is
        # split across two lines.
        # The loop below has been updated to account for all scenarios.

        sfs_show_list = list()
        for share in stdout:
            share_fields = share.split()
            no_of_fields = len(share_fields)

            # Path, IP and Options all on one line
            if no_of_fields == 3 and '(' in share and ')' in share:
                sfs_entry = dict()
                sfs_entry[self.sfs_path_key] = share_fields[0]
                sfs_entry[self.sfs_ip_key] = share_fields[1]
                sfs_entry[self.sfs_perm_key] = share_fields[2]
                sfs_show_list.append(sfs_entry)

            # Path, IP and part of Options on same line
            elif no_of_fields == 3 and '(' in share and ')' not in share:
                temporary_list = list()
                sfs_entry = dict()
                sfs_entry[self.sfs_path_key] = share_fields[0]
                sfs_entry[self.sfs_ip_key] = share_fields[1]
                temporary_list.append(share_fields[2])

            # Only Path & IP on same line
            elif no_of_fields == 2:
                sfs_entry = dict()
                sfs_entry[self.sfs_path_key] = share_fields[0]
                sfs_entry[self.sfs_ip_key] = share_fields[1]

            # All Options on one line
            elif no_of_fields == 1 and '(' in share and ')' in share:
                sfs_entry[self.sfs_perm_key] = share_fields[0]
                sfs_show_list.append(sfs_entry)

            # Other part of Options on one line
            elif no_of_fields == 1 and '(' not in share and ')' in share:
                temporary_list.append(share_fields[0])
                new_item = temporary_list[0] + temporary_list[1]
                sfs_entry[self.sfs_perm_key] = new_item
                sfs_show_list.append(sfs_entry)

        return sfs_show_list

    def is_sfs_share_present(self, sfs_node, share_name, ip_add=None,
                             perm=None):
        """
        Tests whether a specific share is present on the passed sfs
        server. Optionally tests whther a specific IP or permission
        set is also set for the share item.

        Args:
           sfs_node    (str): filename of the sfs.

           share_name (str): Name of the share to check for.

        Kwargs:
           ip_add (str): If set will only return True if the ip as well as\
              any other selected values match.

           perm (str): If set will only return True if the permissions\
              (eg '(rw,root_squash)') as well as any other selected values\
              match.

        Returns:
           bool. True if all selected parameters match or False otherwise.
        """
        ###Get a list of all shares
        share_list = self.get_sfs_shares_list(sfs_node)
        ##We always try to match the path parameter
        share_path = False

        #Initially set to True assuming none are passed in so we ignore these
        #values
        ip_add_path = True
        perm_path = True

        for share in share_list:
            #If we find share name set share_path to True
            if share_name in share[self.sfs_path_key]:
                share_path = True

                #If an ip address has been sent in set bool to False unless
                #we find a match
                if ip_add != None:
                    ip_add_path = False
                    if ip_add in share[self.sfs_ip_key]:
                        ip_add_path = True

                #If a specific permission set has been passed in set to
                #False unless we find a match
                if perm != None:
                    perm_path = False
                    if perm in share[self.sfs_perm_key]:
                        perm_path = True

                #If we have a match on all required items return True
                if share_path and ip_add_path and perm_path:
                    return True

        return False

    def rollback_sfs_filesystem(self, sfs_node, fs_name, rollback_name):
        """

        Runs the restore rollback command on the SFS with given values

        Args:

           sfs_node (str): filename of the sfs.

           fs_name (str): Filesyetem to restore.

           rollback_name (str): Name of the rollback to restore.

        Returns:

           bool. True if all selected rollback succeeded or
                 False if rollback command failed
        """

        cmd = "storage rollback restore {0} {1}".format(fs_name, rollback_name)
        _, stderr, rc = self.run_command(sfs_node, cmd)
        if rc != 0 or stderr != []:
            return False

        return True

    def delete_sfs_shares(self, sfs_node, share_path, ip_add_list=None):
        """
        Deletes all shares using passed share path (eg '/vx/myshare')
        If ip address list parametr is populated will only delete share
        if ip address is in passed list.

        Args:

           sfs_node (str): filename of the sfs.

           share_path (str): Full path of the share to check for.

        Kwargs:

           ip_add_list (list): Optional list of ips. If passed in will only\
              delete shares which have an ip in this list.

        Returns:

           bool. True if all selected share was deleted or
                 False if share was not deleted or not found.
        """
        share_found = False
        share_list = self.get_sfs_shares_list(sfs_node)

        if not share_list:
            return False

        ##Loop through all shares
        for share in share_list:
            if share[self.sfs_path_key] == share_path:
                cmd = "nfs share delete {0} {1}"\
                    .format(share[self.sfs_path_key],
                            share[self.sfs_ip_key])

                ##If we have defined a list of allowed IPs to delete
                ##check share ip matches ip in list
                if ip_add_list:
                    if share[self.sfs_ip_key] in ip_add_list:
                        share_found = True
                        ##We don't care about stdout, we just want to
                        ##ensure delete works
                        _, stderr, rc = self.run_command(sfs_node, cmd)
                        if rc != 0 or stderr != []:
                            return False

                else:
                    share_found = True
                    ##We don't care about stdout, we just want to
                    ##ensure delete works
                    _, stderr, rc = self.run_command(sfs_node, cmd)
                    if rc != 0 or stderr != []:
                        return False

        ##If share found and deleted return True
        return share_found

    def create_sfs_share(self, sfs_node, share_name, share_perm,
                         share_ipaddrs=""):
        """
        Create the given sfs share with permissions on the sfs.

        Args:
           sfs_node    (str): filename of the sfs.

           share_name (str): Name of thre share you wish to create.

           share_permissions (str): Type of permission to be created with share

        Kwargs:

           share_ipaddrs (str): Comma separated ipaddress/subnet for share\
              access

        Returns:
            bool. True if create is successful or False otherwise.
        """

        cmd = "nfs share add {0} {1} {2}".format(share_perm, share_name,
                                                 share_ipaddrs)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def create_sfs_snapshot(self, sfs_node, snapshot_name, fs_name,
                            cache_name):
        """
        Create the given sfs snapshot on the sfs.

        Args:
           sfs_node    (str): filename of the sfs.

           snapshot_name (str): Name of the snapshot you wish to create.

           fs_name (str): The fs name to create snapshot

           cache_name (str): The cache name for snapshot

        Returns:
            bool. True if create is successful or False otherwise.
        """

        cmd = "storage rollback create space-optimized {0} {1} {2}"\
              .format(snapshot_name, fs_name, cache_name)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def create_sfs_cache(self, sfs_node, cache_name, cache_size, cache_pool):
        """
        Create the given sfs cache on the sfs.

        Args:
           sfs_node    (str): filename of the sfs.

           cache_name (str): Name of thre cache you wish to create.

           cache_size (str): Size of the cache to create

           cache_pool (str): Pool to which cache belongs to

        Returns:
            bool. True if create is successful or False otherwise.
        """

        cmd = "storage rollback cache create {0} {1} {2}"\
              .format(cache_name, cache_size, cache_pool)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def create_sfs_fs(self, sfs_node, fs_test, fs_option, fs_size, sfs_pool):
        """
        Create the selected file system.

        Args:
           sfs_node    (str): filename of the sfs.

           fs_test (str): Name of thre file system you wish to create.

           fs_option (str): Type of filesystem to be created

           fs_size (str): Size of the filesystem to be created

           sfs_pool (str): Pool Filesystem will belong to

        Returns:
            bool. True if create is successful or False otherwise.
        """
        cmd = "storage fs create {0} {1} {2} {3}".format(fs_option, \
                    fs_test, fs_size, sfs_pool)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def delete_sfs_fs(self, sfs_node, fs_test):
        """
        Delete the selected file system.

        Ags:

           sfs_node (str): filename of the sfs.

           fs_test (str): Name of thre file system you wish to delete.

        Returns:

           bool. True if delete is successful or False otherwise.
        """
        cmd = "storage fs destroy {0}".format(fs_test)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def delete_sfs_snapshot(self, sfs_node, snapshot_test, fs_test):
        """
        Delete the selected snapshot on SFS.

        Ags:

           sfs_node (str): filename of the sfs.

           snapshot_test (str): Name of the snapshot you wish to delete.

           fs_test (str): Name of the file system you wish to delete snapshot.

        Returns:

           bool. True if delete is successful or False otherwise.
        """
        cmd = "storage rollback destroy {0} {1}".format(snapshot_test, fs_test)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def delete_sfs_cache(self, sfs_node, cache_test):
        """
        Delete the selected cache on SFS.

        Ags:

           sfs_node    (str): filename of the sfs.

           cache_test (str): Name of cache you wish to delete.

        Returns:

           bool. True if delete is successful or False otherwise.
        """
        cmd = "storage rollback cache destroy {0}".format(cache_test)

        ##We don't care about stdout, we just want to
        ##ensure delete works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def increase_sfs_size(self, sfs_node, tier, fs_test, size, pool_name):
        """
        Increase the size of a sfs filesystem.

        Args:
            sfs_node (str): filename of the sfs.

            tier (str): primary|secondary

            fs_test (str): Name of the file system to increase in size.

            size (str): Specified size to which file system will increase.

            pool_name (str): Name of pool to increase in size

        Returns:
            bool. True if increase in size is successful or False otherwise.
        """
        cmd = "storage fs growto {0} {1} {2} {3}".format(tier, fs_test, size,
                                                         pool_name)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def decrease_sfs_size(self, sfs_node, tier, fs_test, size):
        """
        Decrease the size of a sfs filesystem.

        Args:
            sfs_node (str): filename of the sfs.

            tier (str): primary|secondary

            fs_test (str): Name of the file system to decrease in size.

            size (str): Specified size to which file system will decrease.

        Returns:
            bool. True if decrease in size is successful or False otherwise.
        """
        cmd = "storage fs shrinkto {0} {1} {2}".format(tier, fs_test, size)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def mount_sfs_filesystem(self, sfs_node, fs_test):
        """
        Mount (online) a sfs filesystem.

        Args:
            sfs_node (str): filename of the sfs.

            fs_test (str): Name of the file system to mount (take online).

        Returns:
            bool. True if mounting system is successful or False otherwise.
        """
        cmd = "storage fs online {0}".format(fs_test)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def unmount_sfs_filesystem(self, sfs_node, fs_test):
        """
        Unmount (offline) a sfs filesystem.

        Args:
            sfs_node (str): filename of the sfs.

            fs_test (str): Name of the file system to unmount (offline).

        Returns:
            bool. True if unmounting system is successful or False otherwise.
        """
        cmd = "storage fs offline {0}".format(fs_test)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def sfs_rollback_online_snapshot(self, sfs_node, snap_name):
        """
        Make an instant rollback go online

        Args:
            sfs_node (str): filename of the sfs.

            snap_name (str): Name of the rollback to take online.

        Returns:
            bool. True if rollback online is successful or False otherwise.
        """
        cmd = "storage rollback online {0}".format(snap_name)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def sfs_rollback_offline_snapshot(self, sfs_node, snap_name):
        """
        Make an instant rollback go offline

        Args:
            sfs_node (str): filename of the sfs.

            snap_name (str): Name of the rollback to take offline.

        Returns:
            bool. True if rollback offline is successful or False otherwise.
        """
        cmd = "storage rollback offline {0}".format(snap_name)

        ##We don't care about stdout, we just want to
        ##ensure increase works
        _, stderr, rc = self.run_command(sfs_node, cmd)

        if rc != 0 or stderr != []:
            return False

        return True

    def find_nfs_path_by_ip(self, ms_node, ipv4):
        """
        Looks in the model to find any nfs server which matches with the
        passed ip. If found returns the path to that server or returns None
        if the path cannot be found.

        Args:
           ms_node (str): The ms with the model to search.

           ipv4 (str): The nfs ipv4 address to look for.

        Returns:
           str. The path tp the nfs server with matching ip or None
           if no matching path is found.
        """
        nfs_paths = self.find(ms_node, "/infrastructure", "nfs-service",
                              assert_not_empty=False)

        if nfs_paths == []:
            return None

        for path in nfs_paths:

            if self.get_props_from_url(ms_node, path, 'ipv4address').strip() \
                    == ipv4.strip():
                return path

        return None

    ##VCS Related
    def wait_for_vcs_service_group_online(self, node, service_grp_name,
                                          online_count, wait_time_mins=2):
        """
        Check on the selected node if a service group is listed as ONLINE for
        the expected number of times.

        Args:
           node (str): The peer node where you wish to check the service
                        group status.

           service_grp_name (str): The name of the service group under test.

           online_count (int): The number of times you expect this group to be
                               listed as ONLINE on cluster level.

        Kwargs:

          wait_time_mins (int): The maximum time in minutes you will wait for
                                the service group ONLINE count to be correct.

        Returns:
        None. If expected condition is not reached will throw an assertion
        failure.
        """
        hastatus_cmd = self.vcs.get_hastatus_sum_cmd()

        grep_service_group = "{0} | {1} \"{2} \"".format(hastatus_cmd,
                                                    self.rhc.grep_path,
                                                    service_grp_name)

        grep_count_online = "{0} | {1} ' ONLINE ' | wc -l"\
            .format(grep_service_group,
                    self.rhc.grep_path)

        self.assertTrue(self.wait_for_cmd(node, grep_count_online,
                                          0, str(online_count), wait_time_mins,
                                          su_root=True, default_time=2))

    # VCS Related
    def wait_for_vcs_service_group_offline(self, node, service_grp_name,
                                           offline_count, wait_time_mins=2):
        """
        Check on the selected node if a service group is listed as OFFLINE for
        the expected number of times.

        Args:
           node (str): The peer node where you wish to check the service
                        group status.

           service_grp_name (str): The name of the service group under test.

           offline_count (int): The number of times you expect this group to be
                                   listed as OFFLINE on cluster level.

        Kwargs:

          wait_time_mins (int): The maximum time in minutes you will wait for
                                the service group OFFLINE count to be correct.

        Returns:
        None. If expected condition is not reached will throw an assertion
        failure.
        """
        hastatus_cmd = self.vcs.get_hastatus_sum_cmd()

        grep_service_group = '{0} | {1} \"{2} \"'.format(hastatus_cmd,
                                                         self.rhc.grep_path,
                                                         service_grp_name)

        grep_count_offline = "{0} | {1} ' OFFLINE ' | wc -l"\
            .format(grep_service_group,
                    self.rhc.grep_path)

        self.assertTrue(self.wait_for_cmd(node, grep_count_offline,
                                          0, str(offline_count),
                                          wait_time_mins,
                                          su_root=True, default_time=2))

    def wait_for_all_starting_vcs_groups(self, node, timeout_mins=2):

        """
        Check on the selected node that all service groups are listed as
        'ONLINE' or 'OFFLINE'

        Args:
           node (str): The peer node where you wish to check each service
                        group's status.

        Kwargs:
            timeout_mins (int): The maximum time in minutes you will wait for
                                a single service group to reach online status.

        Returns:
        None. If expected condition is not reached will throw an assertion
        failure.
        """

        #Wait for VCS to restart before checking the status of each group
        time.sleep(15)
        faulted_node = False
        hastatus_sum_dict = self.run_vcs_hastatus_sum_command(node)
        hastatus_cmd = self.vcs.get_hastatus_sum_cmd()
        status_cmd = hastatus_cmd + " | grep ^B | grep {0} " \
                     "| grep {1} | tr -s ' ' " \
                     "| cut -d ' ' -f 6"

        for service_grp in hastatus_sum_dict["SERVICE_GROUPS"]:
            if "ONLINE" != service_grp["STATE"] and \
                    "OFFLINE" != service_grp["STATE"]:
                if "FAULTED" in service_grp["STATE"]:
                    faulted_node = True
                    break
                else:
                    node_status_online = self.wait_for_cmd(node,
                                     status_cmd.format(service_grp["GROUP"],
                                                       service_grp["SYSTEM"]),
                                                       0,
                                     expected_stdout='ONLINE',
                                     timeout_mins=timeout_mins,
                                    su_root=True)
                    self.assertTrue(node_status_online)

        self.assertFalse(faulted_node)

    def check_all_vcs_groups_returned_to_online_status(self, conf,
                                                       node, cluster_id):
        """
        Checks that all of the VCS Clustered Services provided
        in the conf dictionary are in the correct amount of
        ONLINE states.

        Args:
            conf (dict): Dictionary of VCS Clustered Service\
               configuration data.

            node (str): Identifies the node on which to contact\
               the VCS console.

            cluster_id (str): Identifies the cluster on which the\
               VCS Clustered Service is expected to be ONLINE.
        """
        group_online_count_dict = {}
        cs_name_list = conf['params_per_cs'].keys()
        # RETRIEVE THE VCS GROUP NAME FOR THE CLUSTERED SERVICE (C-S)
        # AND THE ACTIVE COUNT - NUMBER OF ONLINE NODES FOR THE C-S -
        # AND CREATE A DICTIONARY OF THIS INFORMATION
        for cs_name in cs_name_list:
            cs_grp_name = \
            self.vcs.generate_clustered_service_name(cs_name, cluster_id)
            active_count = conf['params_per_cs'][cs_name]['active']
            group_online_count_dict[cs_grp_name] = active_count

        # USING THE ABOVE CREATED DICTIONARY CYCLE THROUGH EACH
        # CLUSTERED SERVICE AND RETRIEVE ALL INSTANCES OF THE C-S
        # THAT APPEAR IN THE VCS CONSOLE. COUNT HOW MANY OF THESE LINES
        # CONTAINS THE STRING 'ONLINE' AND WAIT FOR UP TO TWO MINUES,
        # WHILE CHECKING EVERY TWO SECONDS, UNTIL THE NUMBER OF
        # 'ONLINE' INSTANCES MATCHES THAT SPECIFIED IN THE DICTIONARY

        for ha_group in group_online_count_dict.keys():
            expected_online_count = group_online_count_dict[ha_group]
            self.wait_for_vcs_service_group_online(node, ha_group,
                                                   expected_online_count)

    def run_vcs_hastatus_sum_command(self, node):
        """
        Run the hastatus -sum command and return the output in a dictionary

        Args:
           node (str): The peer node where you wish to check the hastatus
                       command.

        Returns:
            ha_dict Dictionary of a list of dictionaries with values from the
                    hastatus command output
        """

        ha_dict = {}
        ha_dict["SYSTEM_STATE"] = []
        ha_dict["SERVICE_GROUPS"] = []
        hastatus_cmd = self.vcs.get_hastatus_sum_cmd()
        stdout, stderr, rc = self.run_command(node, hastatus_cmd, su_root=True)
        self.assertEquals([], stderr)
        self.assertEquals(0, rc)
        self.assertNotEquals([], stdout)
        # PARSE THE OUTPUT TO POPULATE THE DICTIONARY
        for line in stdout:
            data1 = line.split()
            if line.startswith("A "):
                add_dict = {}
                add_dict["NODE"] = data1[1]
                add_dict["STATE"] = data1[2]
                add_dict["FROZEN"] = data1[3]
                ha_dict["SYSTEM_STATE"].append(add_dict)
            if line.startswith("B "):
                add_dict = {}
                add_dict["GROUP"] = data1[1]
                add_dict["SYSTEM"] = data1[2]
                add_dict["PROBED"] = data1[3]
                add_dict["AUTODISABLED"] = data1[4]
                add_dict["STATE"] = data1[5]
                ha_dict["SERVICE_GROUPS"].append(add_dict)
        return ha_dict

    def run_vcs_hagrp_display_command(self, node, service_group, attribute=""):
        """
        Run the hagrp command and return output values in a dictionary.
        This also takes into account specific attributes if needed

        Args:
           node (str):  The peer node where you wish to check the hastatus
                       command.
           service_group (str): The Service Group to run command against

        Kwargs:
           attribute (str): If only one attribute is needed check that
                            instead of all

        Returns:
            attr_dict_list, A list dictionary with a list of dictionaries with
                            of all values returned
        """

        attr_dict_list = {}
        hagrp_cmd = None
        if attribute == "":
            hagrp_cmd = self.vcs.get_hagrp_cmd("-display {0}"\
                                                    .format(service_group))
        else:
            hagrp_cmd = self.vcs.get_hagrp_cmd("-display {0} -attribute {1}"\
                                            .format(service_group, attribute))
        stdout, stderr, rc = self.run_command(node, hagrp_cmd, su_root=True)
        self.assertEquals([], stderr)
        self.assertEquals(0, rc)
        self.assertNotEquals([], stdout)
        for line in stdout:
            data1 = line.split()
            add_dict = {}
            if line.startswith("#"):
                continue
            if data1[1] not in attr_dict_list:
                attr_dict_list[data1[1]] = []
            add_dict["SYSTEM"] = data1[2]
            add_dict["VALUE"] = line.split(data1[2])[-1].lstrip()
            attr_dict_list[data1[1]].append(add_dict)
        return attr_dict_list

    def run_vcs_hagrp_resource_command(self, node, service_group):
        """
        Run the hagrp command which returns a list or resources

        Args:
           node (str):  The peer node where you wish to check the hastatus
                       command.
           service_group (str): The Service Group to run command against

        Returns:
            resource_list, A list of any resources returned
        """
        hagrp_cmd = self.vcs.get_hagrp_cmd("-resources {0}"\
                                            .format(service_group))
        resource_list, stderr, rc = self.run_command(node, hagrp_cmd, \
                                                            su_root=True)
        self.assertEquals([], stderr)
        self.assertEquals(0, rc)
        return resource_list

    def run_vcs_hares_display_command(self, node, resource, attribute=""):
        """
        Run the hares command which returns Attributes of a resource

        Args:
           node (str):  The peer node where you wish to check the hastatus
                       command.
           resource (str): The vcs resource to run command against

        Kwargs:
           attribute (str): If only one attribute is needed check that
                            instead of all

        Returns:
            resource_dict, A dictionary containing all resources and values
        """

        attr_dict_list = {}
        hares_cmd = None
        if attribute == "":
            hares_cmd = self.vcs.get_hares_cmd("-display {0}".format(resource))
        else:
            hares_cmd = self.vcs.get_hares_cmd("-display {0} -attribute {1}"\
                                                .format(resource, attribute))
        stdout, stderr, rc = self.run_command(node, hares_cmd, su_root=True)
        self.assertEquals([], stderr)
        self.assertEquals(0, rc)
        self.assertNotEquals([], stdout)
        for line in stdout:
            data1 = line.split()
            add_dict = {}
            if line.startswith("#"):
                continue
            if data1[1] not in attr_dict_list:
                attr_dict_list[data1[1]] = []
            add_dict["SYSTEM"] = data1[2]
            add_dict["VALUE"] = line.split(data1[2])[-1].lstrip()
            attr_dict_list[data1[1]].append(add_dict)

        return attr_dict_list

    def run_vcs_hagrp_dep_command(self, node, service_group, expect_dep=True):
        """
        Run the hagrp command which returns dependencies

        Args:
           node (str):  The peer node where you wish to check the hastatus
                       command.
           service_group (str): The Service Group to run command against

        Returns:
            dict_list, A list of dictionaries with values returned
        """
        dep_dict_list = []
        hagrp_cmd = self.vcs.get_hagrp_cmd("-dep {0}".format(service_group))
        stdout, stderr, rc = self.run_command(node, hagrp_cmd, su_root=True)
        if expect_dep:
            self.assertEquals([], stderr)
            self.assertEquals(0, rc)
            self.assertNotEquals([], stdout)
        else:
            self.assertEquals([], stderr)
            self.assertEquals(1, rc)
            self.assertTrue("No Group dependencies are configured" \
                                in stdout[0])

        for line in stdout:
            data1 = line.split()
            add_dict = {}
            if line.startswith("#"):
                continue
            add_dict["PARENT"] = data1[0]
            add_dict["CHILD"] = data1[1]
            add_dict["RELATIONSHIP"] = line.split(data1[1])[-1].lstrip()
            dep_dict_list.append(add_dict)

        return dep_dict_list

    def run_vcs_hares_dep_command(self, node, resource, expect_dep=True):
        """
        Run the hagrp command which returns dependencies

        Args:
           node (str):  The peer node where you wish to check the hastatus
                       command.
           resource (str): The resource to run command against

        Returns:
            dict_list, A list of dictionaries with values returned
        """
        dep_dict_list = list()
        hares_cmd = self.vcs.get_hares_cmd("-dep {0}".format(resource))
        stdout, stderr, rc = self.run_command(node, hares_cmd, su_root=True)
        if expect_dep:
            self.assertEquals([], stderr)
            self.assertEquals(0, rc)
            self.assertNotEquals([], stdout)
        else:
            self.assertEquals([], stderr)
            self.assertEquals(1, rc)
            self.assertTrue("No Resource dependencies are configured" \
                                        in stdout[0])

        for line in stdout:
            data1 = line.split()
            add_dict = {}
            if line.startswith("#"):
                continue
            add_dict["PARENT"] = data1[0]
            add_dict["CHILD"] = data1[1]
            add_dict["RELATIONSHIP"] = line.split(data1[1])[-1].lstrip()
            dep_dict_list.append(add_dict)

        return dep_dict_list

    ###LIBVIRT RELATED
    def run_libvirt_service_cmd(self, node, service_name,
                                service_cmd, expect_positive=True,
                                timeout=480):
        """
        Function to run commands on a libvirt service.

        Args:
           node (str) : Node on which the service command is to be executed.

           vm_service_name (str): Name of the vm service.

           service_cmd (str): Command to perform on the service.
           (ie stop, start, status etc)

        Kwargs:
          expect_positive (bool): By defaults asserts command success. If set
          to False asserts command failure.

        Returns:
            list, list, int. Returns stdout, stderr and rc of command after
            beingrun.

        """
        cmd = '{0}{1} {2} {3}; exit $?'.format(
                             test_constants.LIBVIRT_MODULE_DIR,
                             test_constants.LIBVIRT_MODULE_NAME,
                             service_name, service_cmd)

        stdout, stderr, returnc = self.run_command(node, cmd,
                                                  su_root=True,
                                                  su_timeout_secs=timeout)

        if expect_positive:
            self.assertNotEquals([], stdout)
            self.assertEquals([], stderr)
            self.assertEquals(0, returnc)
        else:
            #Not making any assertions on stdout or stderr.
            #stdout may not be empty on a failed start. It is empty on timeout
            self.assertNotEquals(0, returnc)

        return stdout, stderr, returnc

    def wget_image_to_node(self, ms_node, node, src_image_name, dest_dir,
                           dest_image_name=None):
        """
        Function to copy the image file from the management server to a
        peer node using the wget command.

        Args:
            ms_node (str): MS node from which to copy file from.

            node (str): Peer node which contains the image file.

            src_image_name (str): Name of the image file on the MS.

            dest_dir (str): Directory on the node to which to transfer the file

            dest_image_name (str): Name to be given to the file when it resides
                                   on the node. If not set name will match
                                   original image name.

        Returns:
        n/a. Asserts success of wget command.
        """
        if dest_image_name == None:
            dest_image_name = src_image_name

        ms_hostname = self.get_node_att(ms_node,
                                        "hostname")
        wget_cmd = \
        "/usr/bin/wget http://{0}/" \
        "images/{1} -O {2}/{3}".format(ms_hostname, src_image_name,
                                       dest_dir, dest_image_name)
        _, _, return_code = \
        self.run_command(node, wget_cmd, su_root=True, su_timeout_secs=180)

        self.assertEqual(0, return_code)

    def create_instance_data_files_in_instance_dir(self, node, sub_dir,
                                                   meta_data_content=None):
        """
        Function to create the user-data and meta-data files in the libvirt
        adaptors instance directory.

        Args:
            node (str): Node on which the files are to be created.

            sub_dir (str): The sub directory within the instance dir where\
               the files are to be created.

            meta_data_content (str): The contents of the meta_data file\
               to be created on the specified node.

        Returns:
            n/a. Assert success for file creation.
        """
        if meta_data_content == None:
            meta_data_content = [""]
        dir_path = \
            self.join_paths(test_constants.LIBVIRT_INSTANCES_DIR, sub_dir)

        meta_data_path = self.join_paths(dir_path, "meta-data")
        network_config_path = self.join_paths(dir_path, "network-config")
        user_data_path = self.join_paths(dir_path, "user-data")

        success = \
            self.create_file_on_node(node, meta_data_path,
                                     meta_data_content,
                                     su_root=True)
        self.assertTrue(success)

        success = \
            self.create_file_on_node(node, network_config_path,
                                     ["version: 1"],
                                     su_root=True)
        self.assertTrue(success)

        success = \
            self.create_file_on_node(node, user_data_path,
                                     ["#cloud-config"],
                                     su_root=True)
        self.assertTrue(success)

    def get_ip_for_vms(self, ms_node, assert_ip_on_vms=True, all_nics=False):
        """
        This will return a the active count number of ips for each vm-service.

        Args:
           ms_node (str): The ms with the LITP tree in.

        Kwargs:
            assert_ip_on_vms (bool): By default will assert at least 1 ip
            exists on all defined vm services. Can be set to False to turn
            off this assertion.

            all_nics (bool): If set to True will get IPs for each
            nic on the VM.

        Returns:
            dict. mapping of service ID to a list containing one IP for
            each VM in the service.

            |      Example:
            |          dictionary of lists.
            |          {
            |               'CS_VM1': ['1.1.1.1'],
            |               'CS_VM2': ['1.1.1.2', '1.1.1.3'],
            |          }
        """
        ##Get all vms
        all_vms = self.find(ms_node, "/deployments", 'vm-service')
        no_ip_on_vm = False
        ips = dict()

        ##Loop through all vm paths
        for path in all_vms:
            clust_service_path = path.rsplit("/", 2)[0]
            # Get how many active VMs are in this service.
            active_count = int(self.get_props_from_url(
                ms_node,
                clust_service_path,
                'active'
            ))

            ##Get nics for each vm
            nic_paths = self.find(ms_node, path,
                                  "vm-network-interface")
            if len(nic_paths) == 0:
                self.log('warning', "No network interfaces defined for VM {0}"\
                             .format(path))
                no_ip_on_vm = True
                continue

            for nic in nic_paths:
            #Get ip address value from example nic
                ip_addresses = self.get_props_from_url(ms_node, nic,
                                                   'ipaddresses')
                if not ip_addresses \
                        or 'dhcp' in ip_addresses:
                    continue

                ip_addresses = [
                    ip.strip()
                    for ip in ip_addresses.split(',')]

                ip_addresses = ip_addresses[:active_count]

                vm_name = path.rsplit("/", 3)[-3]

                ips[vm_name] = list()
                ips[vm_name].extend(ip_addresses)

                if not all_nics:
                    break

        #If assertions are turned off assert for every vm-service an ip has
        #been found.
        if assert_ip_on_vms:
            self.assertFalse(no_ip_on_vm, "Found VM without an ip address")

        return ips

    def get_all_ips_for_vms(self, ms_node, assert_ip_on_vms=True):
        """
        This will return all ips for each vm VM service in the
        deployment model.

        Args:
           ms_node (str): The ms with the LITP tree in.

        Kwargs:
            assert_ip_on_vms (bool): By default will assert at least 1 ip
            exists on all defined vm services. Can be set to False to turn
            off this assertion.

        Returns:
            dict. mapping of service ID to a list containing IPs for
            each VM in the service.

            |      Example:
            |          {
            |               'CS_VM1': ['1.1.1.1'],
            |               'CS_VM2': ['1.1.1.2', '1.1.1.3'],
            |          }
          """
        ##Get all vms
        all_vms = self.find(ms_node, "/deployments", 'vm-service')
        no_ip_on_vm = False
        ips = dict()

        ##Loop through all vm paths
        for path in all_vms:
            ip_list = list()
            ##Get nics for each vm
            nic_paths = self.find(ms_node, path,
                                  "vm-network-interface")
            if len(nic_paths) == 0:
                self.log('warning', "No network interfaces defined for VM {0}"\
                             .format(path))
                no_ip_on_vm = True
                continue

            for nic in nic_paths:
            #Get ip address value from example nic
                ip_addresses = self.get_props_from_url(ms_node, nic,
                                                   'ipaddresses')
                if not ip_addresses \
                        or 'dhcp' in ip_addresses:
                    continue

                #Only pick one ip if multiply are provides
                if "," in ip_addresses:
                    ip_list.extend(ip_addresses.split(','))
                else:
                    ip_list.append(ip_addresses)

                vm_name = path.rsplit("/", 3)[-3]

                ips[vm_name] = ip_list

        #If assertions are turned off assert for every vm-service an ip has
        #been found.
        if assert_ip_on_vms:
            self.assertFalse(no_ip_on_vm, "Found VM without an ip address")

        return ips

    def get_cs_conf_url(self, ms_node, cs_name, vcs_cluster_url):
        """
        Function to retrieve a cs_conf_url using the specified service group.

        Args:
              ms_node (str): The ms node object.

              cs_name (str): CS name from test data.

              vcs_cluster_url (str): Path to VCS cluster.

        Returns:
            str. Deployment path by CS name or None
            if not found.
        """
        cs_conf_urls = self.find(ms_node,
                                 vcs_cluster_url,
                                 'vcs-clustered-service')

        for cs_conf_url in cs_conf_urls:
            ref_service_name = self.get_props_from_url(
                ms_node, cs_conf_url, 'name')
            if ref_service_name == cs_name:
                return cs_conf_url

        return None

    def apply_cs_and_apps_sg(self, ms_node, fixtures, rpm_src_dir):
        """
        Description:
            Copy and import packages to the MS.
            Specify and deploy vcs-clustered-services, packages,
            services, configs and vips in the model.

        Args:
              ms_node (str): The ms node object.

              fixtures (str): Dictionary containing apps
              information.

              rpm_src_dir (str): Local filepath with rpms.

        Actions:
             1. Add dummy lsb-services to repo
             2. Executes CLI to create model
        """
        # It is assumed that any rpms required for this test
        # exist in a repo before the plan is executed
        # This section of the test sets this up
        # List of rpms required for this test
        # Copy RPMs to Management Server
        filelist = [self.get_filelist_dict(rpm_src_dir + rpm, '/tmp/')
                    for rpm in fixtures['packages']]

        self.copy_filelist_to(ms_node, filelist,
                              add_to_cleanup=False, root_copy=True)

        # Use LITP import to add to repo for each RPM
        for rpm in fixtures['packages']:
            self.execute_cli_import_cmd(
                ms_node,
                '/tmp/' + rpm,
                test_constants.PP_PKG_REPO_DIR)

        # Create Clustered-Services in the model
        for vcs in fixtures['vcs-clustered-service']:
            self.execute_cli_create_cmd(ms_node,
                                        vcs['vpath'],
                                        'vcs-clustered-service',
                                        vcs['options_string'],
                                        add_to_cleanup=vcs['add_to_cleanup'])

        # Generate configuration for the plan
        # This configuration will contain the configuration for all
        # clustered-services to be created
        for service in fixtures['service']:
            self.execute_cli_create_cmd(
                ms_node,
                service['vpath'],
                'service',
                service['options_string'],
                add_to_cleanup=service['add_to_cleanup'])

            self.execute_cli_create_cmd(
                ms_node,
                service['package_vpath'],
                'package',
                'name=' + service['package_id'],
                add_to_cleanup=service['add_to_cleanup'])

            self.execute_cli_inherit_cmd(
                ms_node,
                service['destination'],
                service['vpath'],
                add_to_cleanup=service['add_to_cleanup'])

            self.execute_cli_inherit_cmd(
                ms_node,
                service['package_destination'],
                service['package_vpath'],
                add_to_cleanup=service['add_to_cleanup'])

        # CREATE THE HA SERVICE CONFIG ITEM
        for hsc in fixtures['ha-service-config']:
            self.execute_cli_create_cmd(
                ms_node,
                hsc['vpath'],
                'ha-service-config',
                hsc['options_string'],
                add_to_cleanup=hsc['add_to_cleanup'])

        # CREATE THE VIP ITEM
        for vip in fixtures.get('vip', []):
            self.execute_cli_create_cmd(
                ms_node,
                vip['vpath'],
                'vip',
                vip['options_string'],
                add_to_cleanup=vip['add_to_cleanup'])

        # CREATE TRIGGER ITEM
        for vcs_trigger in fixtures.get('vcs_trigger', []):
            self.execute_cli_create_cmd(
                ms_node,
                vcs_trigger['vpath'],
                'vcs-trigger',
                vcs_trigger['options_string'],
                add_to_cleanup=vcs_trigger['add_to_cleanup'])

    def run_and_check_plan(self, ms_node, expected_plan_state,
                           plan_timeout_mins, add_to_cleanup=True):
        """
        Execute create_plan, run_plan and wait for plan to reach expected
        state.

        Args:
            ms_node (str): The ms node object.

            expected_plan_state (str): Expected final state of plan based on
                                       constant file values.

            plan_timeout_mins (int): How long to wait for plan to complete
                                     before failing.

        Kwargs:
            add_to_cleanup (bool): By default will perform standup plan
            cleanup steps in teardown. Set to False to disable this
            behaviour.

        Raises:
            AssertionError any plan command fails or the plan itself fails to
            reach expected state.
        """
        # This section of the test sets up the model and creates the plan
        # Maximum duration of running plan
        self.assertTrue(isinstance(plan_timeout_mins, int))
        # Create and execute plan
        self.execute_cli_createplan_cmd(ms_node)
        self.execute_cli_runplan_cmd(ms_node, add_to_cleanup=add_to_cleanup)

        self.assertTrue(self.wait_for_plan_state(
            ms_node,
            expected_plan_state,
            plan_timeout_mins
        ))

    ##LITP_CI_UTILS
    def get_model_names_and_urls(self):
        """
        Function to get names and urls for model deployments, clusters nodes
        and ms.

        Returns:
            dict. Dictionary containing names and urls of each deployment,
            cluster, ms and node.

        |   Example:
        |   {
        |       'clusters':
        |        [
        |           {
        |               'url': '/deployments/d1/clusters/c1',
        |               'nodes':
        |               [
        |                   {
        |                       'url': '/deployments/d1/clusters/c1/nodes/n1',
        |                       'name': 'node1',
        |                   },
        |                   {
        |                       'url': '/deployments/d1/clusters/c1/nodes/n2',
        |                       'name': 'node2',
        |                   },
        |               ],
        |           },
        |       ],
        |       'nodes':
        |       [
        |           {
        |               'url': '/deployments/d1/clusters/c1/nodes/n1',
        |               'name': 'node1',
        |           },
        |           {
        |               'url': '/deployments/d1/clusters/c1/nodes/n2',
        |               'name': 'node2',
        |           },
        |       ],
        |       'ms':
        |       [
        |           {
        |               'url': '/ms',
        |               'name': 'ms1',
        |           },
        |       ],
        |       'deployments':
        |       [
        |           {
        |               'url': '/deployments/d1',
        |               'names':
        |               [
        |                   'node1',
        |                   'node2',
        |               ],
        |           },
        |       ],
        |   },
        """

        model = {"ms": [],
                 "deployments": [],
                 "clusters": [],
                 "nodes": []}

        model["ms"].append({"url": "/ms", "name":
                                          self.get_management_node_filename()})
        ms_node = model["ms"][0]["name"]

        deployments = self.find(ms_node, "/deployments", "deployment")

        for deployment in deployments:
            nodes = self.find(ms_node, deployment, "node")
            names = []
            for node in nodes:
                names.append(self.get_props_from_url(ms_node, node,
                                                     filter_prop="hostname",
                                                     log_output=True))
            model["deployments"].append({"url": deployment, "names": names})

            clusters = self.find(ms_node, deployment, "vcs-cluster",
                                 assert_not_empty=False)
            clusters.extend(self.find(ms_node, deployment, "cluster",
                                      assert_not_empty=False))
            for cluster in clusters:
                nodes = self.find(ms_node, cluster, "node")
                names = []
                for node in nodes:
                    node_name = self.get_props_from_url(ms_node, node,
                                                        filter_prop="hostname")
                    names.append({"url": node, "name": node_name})
                    model["nodes"].append({"url": node, "name": node_name})
                model["clusters"].append({"url": cluster, "nodes": names})

        self.log("info", "Printing dict from get_model_names_and_urls()")
        self._print_dict(0, model)
        self.log("info", "Finished printing dict")

        return model

    def _print_dict(self, spaces, dct):
        """
        Print method for get_model_names_and_urls()
        """
        print (" " * spaces) + "{"
        for pair in dct:
            if type(pair) == dict:
                self._print_dict(spaces + 4, pair)
                continue
            print (" " * (spaces + 4)) + "'{0}':".format(pair),
            if type(dct[pair]) == list:
                print ""
                self._print_list(spaces + 4, dct[pair])
            elif type(dct[pair]) == dict:
                print " {"
                for vals in dct[pair]:
                    print (" " * (spaces + 8)) + "'{0}': '{1}',".format(
                        vals, dct[pair][vals])
                print (" " * (spaces + 4)) + "}',"
            else:
                print " '{0}',".format(dct[pair])
        print (" " * spaces) + "},"

    def _print_list(self, spaces, lst):
        """
        Print method for get_model_names_and_urls()
        """
        print (" " * spaces) + "["
        for item in lst:
            if type(item) == dict:
                self._print_dict(spaces + 4, item)
            else:
                print (" " * (spaces + 4)) + "'{0}',".format(item)
        print (" " * spaces) + "],"

    def remove_all_snapshots(self, node, remove_only_named_snapshots=False):
        """
        Remove all LITP deployment and named snapshots from the system.

        Args:
            node (str): Node you want to run command on.

            remove_only_named_snapshots (bool): Only remove named snapshots,\
            do not remove the default deployment snapshot.

        Returns:
            N/A. Asserts snapshots removed successfully.
        """
        #1 Find any existing snapshots:
        snaps = self.find(node, "/snapshots", "snapshot-base",
                          assert_not_empty=False)

        def_snap = False
        # Remove all named snapshots
        for snap in snaps:

            name = snap.split("/")[-1]
            name = name.strip()

            if name == "snapshot":
                def_snap = True
                continue

            name_arg = "-n " + name
            self.execute_cli_removesnapshot_cmd(node, args=name_arg,
                                                add_to_cleanup=False)

            # Wait for plan to complete
            self.assertTrue(
                self.wait_for_plan_state(node, test_constants.PLAN_COMPLETE))

        if not remove_only_named_snapshots and def_snap:

            # Remove the default snapshot
            self.execute_cli_removesnapshot_cmd(node)

            # Wait for plan to complete
            self.assertTrue(
                self.wait_for_plan_state(node, test_constants.PLAN_COMPLETE))

    def is_snapshot_item_present(self, ms_node, snapshot_name='snapshot'):
        """
        Description:
            Determine if a snapshot item exists in the model.

        Args:
            ms_node (str): The MS node to check.

        Kwargs:
            snapshot_name (str): Name of snapshot to check. Default 'snapshot'.
                                 I.E. Deployment snapshot.

        Returns:
            bool. True if snapshot item in model, False otherwise.
        """
        snapshot_paths = self.find(ms_node, "/snapshots",
                              "snapshot-base", assert_not_empty=False)

        if len(snapshot_paths) == 0:
            return False

        snapshots = [x.split('/')[-1] for x in snapshot_paths]

        if snapshot_name in snapshots:
            return True
        else:
            return False

    def get_litp_model_information(self):
        """
        NOTE:
            THIS FUNCTION IS FOR USE WITH LIBVIRT TESTING ONLY

        Description:
            Function to return the dictionary from get_model_names_and_urls()
            with additional information relating to libvirt.
            Note: For the purposes of this function it is assumed that this is
            a single cluster deployment.

        Returns:
            dict. Dictionary containing names and urls of each deployment,
            cluster, ms ,node and libvirt information.

        |   Example:
        |   {
        |       'clusters':
        |        [
        |           {
        |               'url': '/deployments/d1/clusters/c1',
        |               'nodes':
        |               [
        |                   {
        |                       'url': '/deployments/d1/clusters/c1/nodes/n1',
        |                       'name': 'node1',
        |                   },
        |                   {
        |                       'url': '/deployments/d1/clusters/c1/nodes/n2',
        |                       'name': 'node2',
        |                   },
        |               ],
        |           },
        |       ],
        |       'nodes':
        |       [
        |           {
        |               'url': '/deployments/d1/clusters/c1/nodes/n1',
        |               'name': 'node1',
        |           },
        |           {
        |               'url': '/deployments/d1/clusters/c1/nodes/n2',
        |               'name': 'node2',
        |           },
        |       ],
        |       'ms':
        |       [
        |           {
        |               'url': '/ms',
        |               'name': 'ms1',
        |           },
        |       ],
        |       'deployments':
        |       [
        |           {
        |               'url': '/deployments/d1',
        |               'names':
        |               [
        |                   'node1',
        |                   'node2',
        |               ],
        |           },
        |       ],
        |       'libvirt':
        |       {
        |           'sfs_service_path': '/infrastructure/storage/storage_prov\
        iders/sfs_service_sp1',
        |           'filesystems_path': '/infrastructure/storage/storage_prov\
        iders/sfs_service_sp1/pools/sfs_pool1/file_systems',
        |           'sfs_virtual_ip': '10.44.86.230',
        |           'software_images_path': '/software/images/',
        |           'software_services_path': '/software/services/',
        |           'cluster_services_path': '/deployments/d1/clusters/c1\
                    /services',
        |           'vcs_node_list': '[n1, n2 ]',
        |       },
        |   },
        """

        model = self.get_model_names_and_urls()
        ms_node = model["ms"][0]["name"]
        sfs_service_path = \
            self.find(ms_node, "/infrastructure/storage/",
                      "sfs-service", exact_match=True)[0]
        filesystems_path = \
            self.find(ms_node, sfs_service_path,
                      "collection-of-sfs-filesystem", exact_match=True)[0]
        sfs_virtual_server_path = \
            self.find(ms_node, sfs_service_path,
                      "sfs-virtual-server", exact_match=True)[0]
        vip_addr = self.get_props_from_url(ms_node, sfs_virtual_server_path,
                                           "ipv4address")
        cluster_services = \
            self.find(ms_node,
                      model["clusters"][0]["url"],
                      "collection-of-clustered-service",
                      exact_match=True)[0]
        vcs_node_list = []
        for line in model["clusters"][0]["nodes"]:
            vcs_node_list.append(line['url'].split("/")[-1])

        model['libvirt'] = {}
        model['libvirt']['sfs_service_path'] = sfs_service_path
        model['libvirt']['filesystems_path'] = filesystems_path
        model['libvirt']['sfs_virtual_ip'] = vip_addr
        model['libvirt']['software_images_path'] = "/software/images/"
        model['libvirt']['software_services_path'] = "/software/services/"
        model['libvirt']['cluster_services_path'] = cluster_services
        model['libvirt']['vcs_node_list'] = vcs_node_list

        self.log("info", "Printing dict from "
                         "get_litp_model_libvirt_information()")
        self._print_dict(0, model)
        self.log("info", "Finished printing dict")

        return model

    def get_litp_network_model_information(self):
        """
        NOTE:
        THIS FUNCTION IS FOR USE WITH LIBVIRT TESTING ONLY

        Function to get the network interfaces and their properties
        under each node in the deployment.

        Returns:
            dict. containing the nodes, the network interfaces and
            their properties

        |   Example:
        |   {
        |       'node1':
        |       [
        |           {
        |               'macaddress':  '98:4B:E1:69:D1:D2',
        |               'name':  'if4',
        |               'device_name':  'eth4',
        |               'network_name':  'traffic1',
        |               'type':  'eth',
        |           },
        |           {
        |               'macaddress':  '98:4B:E1:69:D1:D6',
        |               'name':  'if5',
        |               'ipaddress':  '172.16.200.130',
        |               'device_name':  'eth5',
        |               'network_name':  'traffic2',
        |               'type':  'eth',
        |           },
        |       ]
        |       'node2':
        |       [
        |           {
        |               'macaddress':  '98:4B:E1:68:7C:0A',
        |               'name':  'if4',
        |               'ipaddress':  '172.16.100.3',
        |               'device_name':  'eth4',
        |               'network_name':  'traffic1',
        |               'type':  'eth',
        |           },
        |       ]
        |       'ms1':
        |       [
        |           {
        |               'macaddress':  '80:C1:6E:7A:FA:A8',
        |               'type':  'eth',
        |               'master':  'bondmgmt',
        |               'name':  'if0',
        |               'device_name':  'eth0',
        |           },
        |       ]
        |   }
        """
        network = {}
        net_list = []
        model = self.get_model_names_and_urls()
        management_server = model["ms"][0]["name"]

        ms_net_info_paths = self.find_children_of_collect(management_server,
                                                          "/ms/",
                                                          "network-interface")

        for net in ms_net_info_paths:

            net_props = self.get_props_from_url(management_server, net)
            net_props["name"] = net.split("/")[-1]

            get_type_cmd = self.cli.get_show_data_value_cmd(net, "type")

            stdout = self.run_command(management_server, get_type_cmd)

            net_props['type'] = stdout[0][0]
            net_list.append(net_props)
            net_props = {}

        network["{0}".format(management_server)] = net_list

        net_list = []

        for line in model["clusters"][0]["nodes"]:
            node_net_info_paths = self.find_children_of_collect(
                management_server, line['url'], "network-interface")

            for net in node_net_info_paths:
                net_props = self.get_props_from_url(management_server, net)

                net_props["name"] = net.split("/")[-1]
                get_type_cmd = self.cli.get_show_data_value_cmd(net, "type")
                stdout = self.run_command(management_server, get_type_cmd)
                net_props['type'] = stdout[0][0]
                net_list.append(net_props)
                net_props = {}
            network["{0}".format(line["name"])] = net_list
            net_list = []

        self.log("info", "Printing dict from get_litp_network_"
                         "model_information")
        self._print_dict(0, network)
        self.log("info", "Finished printing dict")
        return network

    def get_locked_vcs_nodes(self):
        """
        Description:
            Get list of locked/frozen VCS nodes.

        Returns:
            list. The list of VCS controlled nodes which are locked.
        """
        # Use first Managed node when issuing ha commands.
        node = self.get_managed_node_filenames()[0]
        ha_dict = self.run_vcs_hastatus_sum_command(node)

        system_dict = ha_dict['SYSTEM_STATE']

        locked_nodes = list()
        for node in system_dict:
            if 'FROZEN' in node:
                if '1' == node['FROZEN']:
                    locked_nodes.append(node['NODE'])

        return locked_nodes

    def manually_unlock_vcs_node(self, node):
        """
        Description:
            Manually unlock/unfreeze a VCS node.

        Args:
            node (str) : The VCS node unlock/unfreeze.

        Returns:
            None. If unlock is not performed successfully function will throw
                  an assertion failure.
        """
        cmd1 = self.vcs.get_haconf_cmd("-makerw")
        cmd2 = self.vcs.get_hasys_cmd("-unfreeze -persistent {0}".format(node))
        cmd3 = self.vcs.get_haconf_cmd("-dump -makero")
        for cmd in [cmd1, cmd2, cmd3]:
            self.run_command(node, cmd, default_asserts=True, su_root=True)

    def manually_lock_vcs_node(self, node):
        """
        Description:
            Manually lock/freeze a VCS node.

        Args:
            node (str) : The VCS node to lock/freeze.

        Returns:
            None. If lock is not performed successfully function will throw
                  an assertion failure.
        """
        cmd1 = self.vcs.get_haconf_cmd("-makerw")
        cmd2 = self.vcs.get_hasys_cmd("-freeze -persistent {0}".format(node))
        cmd3 = self.vcs.get_haconf_cmd("-dump -makero")
        for cmd in [cmd1, cmd2, cmd3]:
            self.run_command(node, cmd, default_asserts=True, su_root=True)

    def get_rhelver_used_on_node(self, node, via_node=None):
        """
        Description:
            Given a node filename, determines the rhel version used on node.
            If rhelver used on node is already known, returns version.
            If not yet known, function calls execute_cli_get_rhelver_from_node
            to contact node and get version.

        Args:
            node (str): Node filename of the node for which the redhat version
                        is required.

        Kwargs:
            via_node (str): In case the node is a VM, need to know the
                          associated host node filename on which the VM is
                          running as there is need to execute commands via
                          the host node.
                          Defaults to None, meaning the node arg is not a VM.

        Returns:
            str. The redhat version.
        """
        real_node_ls = self.get_node_list_by_name([node])

        if not real_node_ls:
            self.log("error", "Node {0} cannot be found".format(node))
            return None

        real_node = real_node_ls[0]

        # If node object does not have this attribute set, need to contact
        # node, get redhat version and store it in node object.
        if not real_node.rhelver:
            real_node.rhelver = \
                self.execute_cli_get_rhelver_from_node(real_node.filename,
                                                       via_node=via_node)

        self.assertNotEqual(None, real_node.rhelver)

        self.log("info", "{0} {1}".format(real_node.filename,
                                          real_node.rhelver))

        return real_node.rhelver

    def execute_cli_get_rhelver_from_node(self, node, via_node=None):
        """
        Description:
            Given a node filename, contacts node and runs command to get the
            the rhel version used on that node.

        Args:
            node (str): Filename of the node for which the redhat version is
                        required.

        Kwargs:
            via_node (str): In case the node is a VM, need to know the
                          associated host node filename on which the VM is
                          running as there is need to execute commands via
                          the host node.
                          Defaults to None, meaning node is not a VM.

        Returns:
            str. The redhat version running on node.
        """
        cmd = "{0}".format('tail ' + test_constants.RH_RELEASE_FILE)

        if via_node:
            # Dealing with a VM, so need to run command via host node.
            stdout, stderr, rc = \
                self.run_command_via_node(via_node,
                                          node,
                                          cmd)
            self.assertEqual(0, rc)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)
        else:
            stdout, stderr, rc = self.run_command(node,
                                            cmd,
                                            add_to_cleanup=False)
            self.assertEqual(0, rc)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)

        return stdout[0]

    def reset_vcs_sg_after_idep(self, story_num, node, deps_present=False):
        """
        Description:

        This method resets and deletes a VCS SG after a litpd restart or
        the plan is stopped. Due to the new core functionality LITPCDS-13137,
        this will need to be run for every idempotency test case

        Args:
                story_num (int): The story number
                node (str): Node to run the commands on
                deps_present (bool): Determines whether to check for
                dependencies between service groups or not

        Returns:
                Nothing
        """
        # Object used to ensure we do not try delete the same resources/service
        # groups running on multiple nodes
        old_name = ''

        # Enable VCS configuration haconf -makerw
        enable_vcs_conf = self.vcs.get_haconf_cmd('-makerw')
        _, _, rc = self.run_command(node, enable_vcs_conf, su_root=True)
        # We dont actually care if the RC is 1 or zero we need to ensure
        # the haconf is rw
        self.assertTrue(rc < 2)

        # Get hagrp command that will display the SG created from the test
        hagrp_cmd = self.vcs.get_hagrp_cmd('-state | grep {0}'
                                           .format(story_num))
        # Run hagrp -state | grep  command on node
        grp_list = self.run_command(node, hagrp_cmd, su_root=True,
                                    default_asserts=True)

        # Clear the Service Group if there is any faults present
        for sg_group_name in grp_list[0]:
            cs_name = (sg_group_name.split("State"))[0]
            if cs_name != old_name:
                ha_clear_cmd = self.vcs.get_hagrp_cs_clear_cmd(cs_name, node)
                self.run_command(node, ha_clear_cmd, su_root=True,
                                 default_asserts=True)
                old_name = cs_name

        # If dependencies exist between SGs we must remove the parent before
        # the child SG accordingly
        if deps_present is True:
            hadep_cmd = self.vcs.get_hagrp_cmd("-dep | grep {0}"
                                               .format(story_num))
            # Run ha command on node to find dependencies
            hadep_list = self.run_command(node, hadep_cmd, su_root=True,
                                          default_asserts=True)
            # Get the first parent dependency between service groups
            if not hadep_list:
                print "Service Group Dependency list is empty"
            else:
                parent = (hadep_list[0][0].split(" "))[0]
                child = (hadep_list[0][0].split(" "))[1]

                # Unlink the first dependency found between SGs
                unlink_cmd = self.vcs.get_hagrp_cmd("-unlink {0} {1}"
                                                    .format(parent, child))
                self.run_command(node, unlink_cmd, su_root=True,
                                 default_asserts=True)

                # Search and remove any parent dependencies before the children
                # dependencies
                for parent_deps in hadep_list[0]:
                    if parent == (parent_deps.split(" "))[1]:
                        child = parent
                        parent = (parent_deps.split(" "))[0]
                        try:
                            # Delete the parent resource and service group
                            hagrp_parent_res = \
                                self.vcs.get_hagrp_resource_list_cmd(parent)
                            stdout = self.run_command(node, hagrp_parent_res,
                                                      su_root=True,
                                                      default_asserts=True)
                            ha_res_del_cmd = \
                                self.vcs.get_hares_del_cmd(stdout[0][0])
                            self.run_command(node, ha_res_del_cmd,
                                             su_root=True,
                                             default_asserts=True)
                            # Delete the child resource and service group
                            # provided no other service relies on it
                            hagrp_child_res = \
                                self.vcs.get_hagrp_resource_list_cmd(child)
                            stdout = self.run_command(node, hagrp_child_res,
                                                      su_root=True,
                                                      default_asserts=True)
                            ha_res_del_cmd = \
                                self.vcs.get_hares_del_cmd(stdout[0][0])
                            self.run_command(node, ha_res_del_cmd,
                                             su_root=True,
                                             default_asserts=True)

                            unlink_cmd = \
                                self.vcs.get_hagrp_cmd("-unlink {0} {1}"
                                                       .format(parent, child))
                            self.run_command(node, unlink_cmd, su_root=True,
                                             default_asserts=True)

                            ha_grp_del_cmd = self.vcs.get_hagrp_del_cmd(parent)
                            self.run_command(node, ha_grp_del_cmd,
                                             su_root=True,
                                             default_asserts=True)

                            ha_grp_del_cmd = self.vcs.get_hagrp_del_cmd(child)
                            self.run_command(node, ha_grp_del_cmd,
                                             su_root=True,
                                             default_asserts=True)
                        except Exception as except_err:
                            self.log('info',
                                     "Unable to check dependecies: {0}"
                                     .format(except_err))
                            raise
        # Check for any remaining cluster services remaining from the test

        # Get hares command that will display the SG resources created from the
        # test
        hares_cmd = self.vcs.get_hares_cmd('-state | grep {0}'
                                               .format(story_num))
        # Run ha command on node
        res_list = self.run_command(node, hares_cmd, su_root=True,
                                    default_asserts=True)

        # Get hagrp command that will display the SG created from the test
        hagrp_cmd = self.vcs.get_hagrp_cmd('-state | grep {0}'
                                           .format(story_num))
        # Run hagrp -state | grep  command on node
        grp_list = self.run_command(node, hagrp_cmd, su_root=True,
                                    default_asserts=True)

        # Delete the resources created from the test case
        for sg_res_name in res_list[0]:
            app_res_name = (sg_res_name.split("State"))[0]
            if app_res_name != old_name:
                ha_res_del_cmd = self.vcs.get_hares_del_cmd(app_res_name)
                self.run_command(node, ha_res_del_cmd, su_root=True,
                                 default_asserts=True)
                old_name = app_res_name

        # Delete the service groups created from the test case
        for sg_group_name in grp_list[0]:
            sg_grp_name = (sg_group_name.split("State"))[0]
            if sg_grp_name != old_name:
                ha_grp_del_cmd = self.vcs.get_hagrp_del_cmd(sg_grp_name)
                self.run_command(node, ha_grp_del_cmd, su_root=True,
                                 default_asserts=True)
                old_name = sg_grp_name

        # Disable VCS configuration haconf -dump -makero
        disable_vcs_conf = self.vcs.get_haconf_cmd('-dump -makero')
        self.run_command(node, disable_vcs_conf, su_root=True,
                         default_asserts=True)

    def get_timezone_on_node(self, node, via_node=None):
        """
        Description:
            Get the timezone of a given node.

        Args:
            node (str): Filename of node from which you want to get time zone.

        Kwargs:
            via_node (str): In case the node is a VM, need to know the
                          associated host node filename on which the VM is
                          running, as there is need to execute commands via
                          the host node.
                          Defaults to None, meaning the node arg is not a VM.

        Returns:
            str. Time Zone
        """
        if self.sles_vm in node:
            os_ver = test_constants.SLES_VERSION_15_4
            vm_password = test_constants.LIBVIRT_SLES_VM_PASSWORD
        else:
            os_ver = self.get_rhelver_used_on_node(node, via_node=via_node)
            vm_password = test_constants.LIBVIRT_VM_PASSWORD

        cmd = self.rhc.get_timedatectl_cmd()
        if via_node != None and test_constants.SLES_VERSION_15_4 == os_ver:
            stdout, stderr, rc = self.run_command_via_node(
                                         via_node,
                                         node,
                                         cmd, password=vm_password)
            self.assertEqual(0, rc)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)
        elif via_node != None:
            stdout, stderr, rc = self.run_command_via_node(
                                           via_node,
                                           node,
                                           cmd)
            self.assertEqual(0, rc)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)
        else:
            stdout, _, _ = self.run_command(node,
                                            cmd,
                                            default_asserts=True,
                                            add_to_cleanup=False,
                                             su_root=True)
            self.assertNotEqual([], stdout)

        for line in stdout:
            if "Time zone:" in line:
                zone = line.split("Time zone:")[1].split("(")[0].strip()
                return zone

    def get_all_volumes(self, ms_node, vol_driver='vxvm'):
        """
        Description:
            Get all filesystems as a list of dictionaries for specified
            vol_driver.
            List of dicts returned has following structure:
                [{'storage_profile': 'storage_profile',
                  'mount_point': '/',
                  'volume_driver': 'lvm',
                  'volume_group_name': 'vg_root',
                  'volume_name': 'root',
                  'snap_size': '100',
                  'path': '/deployments/d1/clusters/c1/nodes/n1/\
                          storage_profile/volume_groups/vg1/file_systems/root',
                  'node_name': "node1" (Or None if path is not on a node),
                  'node_url': "/deployments/d1/clusters/c1/nodes/n1" (Or None
                                if path is not on a node),
                  'type': 'ext4',
                  'size': '16G'},
                 {...},
                 etc...
                ]

        Args:
            ms_node (str): The MS node to check.

        Kwargs:
            vol_driver (str): 'vxvm' or 'lvm'.

        Returns:
            list of dicts. As outlined above in description.
        """
        file_systems = []
        vold = {}
        sps = []

        # Get all storage_profiles paths, but only for required vol_driver.
        sps = self.get_storage_profile_paths(ms_node,
            vol_driver,
            path_url='/deployments')

        self.log("info", "### Storage profiles are {0}".format(str(sps)))

        # For each storage_profile path.
        for stor_prof in sps:
            # Get the storage profile name.
            vold["storage_profile"] = stor_prof.split("/")[-1]

            # Get the volume_driver type
            sp_props = self.get_props_from_url(ms_node, stor_prof)
            vold["volume_driver"] = sp_props["volume_driver"]

            # Get volume group paths
            vgs = self.find(ms_node, stor_prof, 'volume-group')
            self.log("info", "### VGs in {0} are {1}"
                     .format(vold["storage_profile"], str(vgs)))

            # For all volume groups
            for vg_path in vgs:
                # Get volume_group name
                vg_props = self.get_props_from_url(ms_node, vg_path)
                vold["volume_group_name"] = vg_props["volume_group_name"]
                vold["vg_item_id"] = vg_path.split("/")[-1]

                # Get the volume paths
                vols = self.find(ms_node, vg_path, 'file-system')
                self.log("info", "### Vols in {0} are {1}"
                         .format(vold["volume_group_name"], str(vols)))

                # For each volume create a dictionary of attributes
                for vol in vols:
                    vold["path"] = vol

                    vold["node_url"] = None
                    vold["node_name"] = None
                    trail = vold["path"].split("/")
                    if "nodes" in trail:
                        node_child_id_pos = trail.index("nodes") + 1
                        if len(trail) > node_child_id_pos \
                                and trail[node_child_id_pos]:
                            vold["node_url"] = \
                                "/".join(trail[0: node_child_id_pos + 1])
                            vold["node_name"] = \
                                self.get_props_from_url(ms_node,
                                                        vold["node_url"],
                                                        "hostname")

                    vold['volume_name'] = vol.split("/")[-1]
                    # Variable casted to dict to fix pylint issue
                    vol_props = dict(self.get_props_from_url(ms_node, vol))
                    # Update vold with the new properties
                    vold.update(vol_props.copy())
                    # Copy volume dictionary to the list.
                    file_systems.append(vold.copy())

                    # For next usage, remove vol_props values from vold
                    for prop in vol_props:
                        if prop in vold:
                            print "Deleting prop", prop
                            del vold[prop]
                    # Reset vol_props dict for next usage
                    vol_props.clear()

        for filesys in file_systems:
            for key, item in filesys.items():
                self.log("info", "DISK_INFO: {0} - {1}".format(key, item))
            self.log("info", "DISK_INFO")

        return file_systems

    def get_snapshots(self, nodes, grep_args="L_"):
        """
        Description:
            Get the name of any snapshots on the specified nodes.
            Returns a list of snapshots lists. e.g.
            [['ms1', '/dev/vg_root/L_lv_home'],
             ['mn1', '/dev/vg_root/L_root'],
             [etc....]]

        Args:
            nodes (list): A list of nodes

            grep_args (str): If a value is provided, this will be passed to a
                            grep pipe to filter the lvscan.
                            Defaults to "L_"

        Actions:
            1. Grep for snapshots

        Returns:
            list of lists. As outlined above in description.
        """
        cmd = self.sto.get_lvscan_cmd(grep_args=grep_args)
        sshots = []
        for node in nodes:
            out, err, ret_code = self.run_command(node, cmd, su_root=True)
            self.assertEqual([], err)
            self.assertTrue(ret_code < 2)
            if out:
                vol_list = self.sto.parse_lvscan_stdout(out)
                for vol in vol_list:
                    sshots.append([node, vol['origin']])

        return sshots

    def count_vip_ipaddress_type_per_sg(self, ms_node, service_group):
        """
        Description:
            Counts the number ipv4 and ipv6 ipaddress used in vip item
            types for specified VCS clustered service. I.E. VCS Service Group.

        Args:
            ms_node (str): The MS node to check.

            service_group (str): The URL of the VCS service group to check.

        Returns:
            int, int. Number of ipv4 and ipv6 ipaddresses respectively.
        """
        vips = self.find(ms_node, service_group,
                         'vip', assert_not_empty=False)
        ipv4count = 0
        ipv6count = 0
        for vip in vips:
            props = self.get_props_from_url(ms_node, vip)
            if 'ipaddress' in props:
                if self.net.is_ipv4_address(props['ipaddress']):
                    ipv4count += 1
                else:
                    ipv6count += 1
        return ipv4count, ipv6count

    def get_serv_groups_by_num_item(self, ms_node, service_groups, item_type,
                                     num_items):
        """
        Description:
            Get set of VCS Service Groups containing the required number of
            items of specified item_type.
            E.G. get set of VCS SGs with 2 items of item type 'service'.
            self.get_serv_groups_by_num_item(self.ms_node, service_groups, \
                             'service', 2)

        Args:
            ms_node (str): The MS node to check.

            service_groups (list): List of VCS service group URLs to check.

            item_type (str): The LITP Model Item Type.

            num_items (int): Number of items of item_type required.

        Returns:
            set. Returns a set of VCS Service Groups which contain the
            item_type the specified number of times.
        """
        sg_list = list()

        for service_group in service_groups:
            items = self.find(ms_node, service_group,
                                     item_type, assert_not_empty=False)
            if num_items == len(items):
                sg_list.append(service_group)
            else:
                continue

        return set(sg_list)

    def get_servgrps_matching_vip_cfg(self, ms_node, service_groups,
                                      vip_criteria):
        """
        Description:
            Get set of VCS Service Groups matching the vip ipv4 and ipv6
            criteria specified in vip_criteria dict in terms of the number of
            ipv4 and ipv6 vips.

        Args:
            ms_node (str): The MS node to check.

            service_groups (list): List of VCS service group URLs to check.

            vip_criteria (dict): The vip ipv4 and ipv6 criteria to match.
            E.G. {'ipv4': '2', 'ipv6': '2'} means 2 ipv4 and 2 ipv6 vips.

        Returns:
            set. Returns a set of VCS Service Groups matching the vip criteria.
        """
        vip_sgs = list()
        for service_group in service_groups:
            num_ipv4_addrs, num_ipv6_addrs = \
                self.count_vip_ipaddress_type_per_sg(ms_node, service_group)

            if int(vip_criteria["ipv4"]) == num_ipv4_addrs and\
               int(vip_criteria["ipv6"]) == num_ipv6_addrs:
                vip_sgs.append(service_group)
            else:
                continue
        return set(vip_sgs)

    def verify_properties_match(self, ms_node, match_criteria, url):
        """
        Description:
            Check if properties at specified url match those specified
            in match_criteria dict.

        Args:
            ms_node (str): The MS node to check.

            match_criteria (dict): Dictionary of props and values to match.
            E.G. vcs-clustered-service properties.
                 {'active': '1', 'standby': '0', 'node_list': 'n1',\
                    'online_timeout': '60'}

            url       (str): URL to check.
            E.G. url of a vcs-clustered-service item in LITP Model.

        Returns:
            bool. True if properties match. False otherwise.
        """
        if not match_criteria:
            return False

        props_match = True
        props = self.get_props_from_url(ms_node, url)
        for prop in match_criteria:
            if prop in props:
                if match_criteria[prop] != props[prop]:
                    props_match = False
                    continue
            else:
                props_match = False
                continue
        return props_match

    def get_matching_vcs_cs_in_model(self, ms_node, lsb_runtimes=None,
                              apps=None, ha_srv_cfgs=None, pkgs=None,
                              vips_dict=None, cs_props_dict=None,
                              ha_srv_props_dict=None):
        """
        Description:
            Find matching VCS Service Groups in LITP Model based on specified
            parameters.
            NOTE: If no Kwargs are specified, will simply return an empty list.

        Args:
            ms_node (str): The MS node to check.

        Kwargs:
            lsb_runtimes (int): Number of lsb-runtime items to match.
                                Defaults to None which means don't check.

            apps (int): Number of 'service' items to match.
                        Defaults to None which means don't check.

            ha_srv_cfgs (int): Number of ha-service-config items to match.
                               Defaults to None which means don't check.

            pkgs (int): Number of 'package' items to match.
                        Defaults to None which means don't check.

            vips_dict (dict): Dict outlining the required number of
                              ipv4 and ipv6 vips.
                              E.G. {'ipv4': '1', 'ipv6': '1'} means:
                              1 ipv4 and ipv6 based vip.
                              Defaults to None which means don't check.

            cs_props_dict (dict): Dict outlining VSC CS properties to match.
                                  E.G. To match any 2 node PL VCS CS:
                                  {'active': '2',
                                   'standby': '0',
                                   'node_list': 'n1,n2'}
                              Defaults to None which means don't check.

            ha_srv_props_dict (dict): Dict outlining ha-service-config props
                                      to match.
                                      E.G. {'restart_limit': '10',
                                            'startup_retry_limit': '10',
                                            'tolerance_limit': '0'}
                              Defaults to None which means don't check.

        Returns:
            list. Returns a set of VCS Service Groups which match the criteria
                 specified in Kwargs. If no Kwargs are specified, will simply
                 return an empty list.
        """
        matching_criteria = {'lsb_runtimes': lsb_runtimes,
                             'application': apps,
                             'ha_service_config': ha_srv_cfgs,
                             'ha_serv_props': ha_srv_props_dict,
                             'packages': pkgs,
                             'vips': vips_dict,
                             'cs_props': cs_props_dict}

        set_value = False
        ##Test at least one criteria has been set
        for key_item in matching_criteria.keys():
            if matching_criteria[key_item]:
                set_value = True
                break

        if not set_value:
            self.log('info', "No VCS CS matching criteria {0}".\
                                     format(matching_criteria))
            return []

        ha_service_sgs = list()
        cs_props_sgs = list()
        service_groups = list()

        service_groups = self.find(ms_node, '/deployments',
                                     'vcs-clustered-service')
        service_groups[:] = [
            cs_
            for cs_ in service_groups
            if 'CS' in cs_.split('/')[-1]
        ]

        if matching_criteria['lsb_runtimes'] and service_groups:
            service_groups = \
            self.get_serv_groups_by_num_item(ms_node, service_groups, \
                             'lsb-runtime', matching_criteria['lsb_runtimes'])

        if matching_criteria['application'] and service_groups:
            service_groups = \
            self.get_serv_groups_by_num_item(ms_node, service_groups, \
                             'service', matching_criteria['application'])

        if matching_criteria['ha_service_config'] and service_groups:
            for group in service_groups:
                ha_service_configs = self.find(ms_node, group,
                                     'ha-service-config',
                                     assert_not_empty=False)
                if matching_criteria['ha_service_config'] == \
                                                     len(ha_service_configs):
                    if matching_criteria['ha_serv_props']:
                        for ha_serv in ha_service_configs:
                            if self.verify_properties_match(ms_node,
                                           matching_criteria['ha_serv_props'],
                                           ha_serv):
                                ha_service_sgs.append(group)
                    else:
                        ha_service_sgs.append(group)
                else:
                    continue

            service_groups = ha_service_sgs

        if matching_criteria['vips'] and service_groups:
            service_groups = self.get_servgrps_matching_vip_cfg(ms_node,
                                                         service_groups,
                                                     matching_criteria['vips'])

        if matching_criteria['packages'] and service_groups:
            service_groups = \
            self.get_serv_groups_by_num_item(ms_node, service_groups, \
                             'package', matching_criteria['packages'])

        if matching_criteria['cs_props'] and service_groups:
            for group in service_groups:
                if self.verify_properties_match(ms_node,
                                      matching_criteria['cs_props'], group):
                    cs_props_sgs.append(group)
            service_groups = set(cs_props_sgs)

        if not service_groups:
            self.log('info', "No VCS CS matching criteria {0}".\
                                           format(matching_criteria))
        return list(service_groups)

    def get_vx_disk_node(self, ms_node, cluster_id=None, disk_group=None):
        """
        Get Peer Node on which disk group is imported.

        Args:
            ms_node (str): The MS node to check.

        Kwargs:
            cluster_id (str): Identifies the cluster in which to search
                              peer nodes to determine on which node the disk
                              group is expected to be imported.
                              Defaults to None, in which case first
                              vcs-cluster in model is used.

            disk_group (str): Name of disk group. Defaults to None.
                              If None, will use first disk group name
                              found using get_all_volumes function.

        Returns:
            str. Filename of node on which disk group is imported.

        Raises:
            AssertionError if disk group not imported on any node.
        """
        if disk_group == None:
            volumes = self.get_all_volumes(ms_node)
            self.assertTrue(len(volumes) > 0)
            disk_group = volumes[0]["volume_group_name"]

        vx_disk_node = False

        clusters = self.find(ms_node, '/deployments', "vcs-cluster")

        nodes = []
        if cluster_id:
            for cluster in clusters:
                clusterid = cluster.split('/')[-1]
                if cluster_id == clusterid:
                    node_urls = self.find(ms_node, cluster, "node")
                    for url in node_urls:
                        node_filename = \
                            self.get_node_filename_from_url(ms_node, url)
                        nodes.append(node_filename)
        else:
            # Use first vcs-cluster in model.
            node_urls = self.find(ms_node, clusters[0], "node")
            for url in node_urls:
                node_filename = self.get_node_filename_from_url(ms_node, url)
                nodes.append(node_filename)

        for node in nodes:
            out, _, _ = self.run_command(node,
                                         "/sbin/vxdg list",
                                         su_root=True,
                                         default_asserts=True)
            if (self.is_text_in_list('enabled', out) and
                self.is_text_in_list(disk_group, out)):
                vx_disk_node = node
                break
        self.assertTrue(vx_disk_node)
        return vx_disk_node

    def get_running_env(self, ms_node):
        """
        Finds out the environment the test is running on and
        returns the relevant test constant integer.

        Args:
           ms_node (str): The ms node.

        Returns:
           int. ENV_CLOUD, ENV_PHYSICAL or ENV_OTHER test constant.
       """
        cmd_to_check = "/usr/sbin/dmidecode -s system-manufacturer"
        stdout, _, _ = self.run_command(ms_node, cmd_to_check,
                                        su_root=True)

        if self.is_text_in_list('VMware', stdout):
            return test_constants.ENV_CLOUD
        elif self.is_text_in_list('HP', stdout):
            return test_constants.ENV_PHYSICAL

        return test_constants.ENV_OTHER

    def verify_expected_env(self, ms_node, expected_envs, error_msg):
        """
        Will test what environment LITP is installed on and will
        fail the test if this does not match one of the expected values.

        Args:
           ms_node (str): The ms node.

           expected_envs (list): List of ints representing valid environments
                                 for the test as identified by test_constant
                                 values. (ENV_CLOUD, ENV_PHYSICAL, ENV_OTHER)

            error_msg (str): Message which should be displayed if environment
                              doesn't match what is expected.

        Raises:
          AssertionError. If environment does not match one of the
          expected values.
        """
        running_env = self.get_running_env(ms_node)

        if running_env not in expected_envs:
            self.log('error', "Test is running in unexpected environment: {0}"\
                         .format(error_msg))
            self.assertTrue(running_env in expected_envs,
                            "Test is not running in expected environment")

        self.log('info', "Environment test passed")

    def check_cli_errors(self, expected_errors, actual_errors,
                                                    check_extra_error=True):
        """
        Description:
            Compare expected errors with actual errors.
            Litp error messages can be divided into two categories:
                - Validation errors triggered by attempting to perform some
                  illegal action.
                  These are normally made up of two components and one line
                  long:
                      -> Error Type (optional)
                      -> Error message (required)
                - Validation errors triggered by illegal property values,
                  model item inconsistency etc.
                  Normally of three components and span over two lines.
                      -> the URL (required)
                      -> the Error Type (required)
                      -> the Error Message (required)

            This function allows to check both type of errors by verifying
            that all expected errors are found and no extra errors are present.
            In addition, in case of errors of the second type the function
            verifies that the correct URL/ErrorType/ErrorMessage combination
            is present.

        Args:
            expected_errors (dict)   : Data structure that contains expected
                                       error details
            actual_errors (list)     : List of errors posted by LITP
            check_extra_error (bool) : Specify whether to check for extra
                                       error messages.
                                       Defaults to True.
            Note:
            Example of expected_errors data structure:
                expected_errors = [
                    {
                        'url': '/my/path/to/item1',              # Optional
                        'error_type': 'InvalidRequestError',     # Optional
                        'msg': 'Plan already running'            # Required
                    }
                    ...
                ]
        Returns:
            list, list. The first list contains expected error messages that
                        were missing. The second list contains error messages
                        that were not expected.
        """
        missing = []
        extra = []
        for expected in expected_errors:

            self.assertTrue('msg' in expected,
                            '"msg" field is required in expected error data')

            expected_msg = [expected.get('error_type', ''),
                            expected.get('msg')]

            # Removes the relevant entry from actual_error list every time a
            # match is found for an expected error. At the end of this process
            # all actual error are expected to have been removed. If not, it is
            # assumed that remaining error(s) were unexpected and are
            # considered as "extra". In case of error of second type, for each
            # match two lines need to be removed (as each error spans over two
            # lines).
            if 'url' in expected:
                for i, actual in enumerate(actual_errors[:], 0):
                    if expected['url'] == actual and \
                       i < (len(actual_errors) - 1) and \
                       all(
                        [msg in actual_errors[i + 1] for msg in expected_msg]):
                        del actual_errors[i]
                        del actual_errors[i]
                        break
                else:
                    missing.append(expected['url'])
                    missing.append(''.join(expected_msg))
            else:
                for i, actual in enumerate(actual_errors[:], 0):
                    if all(msg in actual for msg in expected_msg):
                        del actual_errors[i]
                        break
                else:
                    missing.append(''.join(expected_msg))

        # We expect actual_error list to be empty at this point
        # any element still in it is to be considered as extra error
        if check_extra_error:
            for error in actual_errors:
                extra.append(error)

        return missing, extra

    def get_full_list_of_tasks(self, node):
        """
        Description:
            Get the full list of tasks in a plan.
            Returns a list of dicts in the format:

            {
                'STATUS': 'Initial',
                'PATH': '/deployments/d1/clusters/c1/services/CS1',
                'MESSAGE': 'Create IPs for VCS service group "Grp_CS_c1_CS1"',
                'ID': 1,
                'PHASE': 1
            }

        Args:
            node (str): The node on which to run the show_plan command

        Returns:
            list. Tasks in plan.
        """
        stdout, stderr, rc = self.execute_cli_showplan_cmd(node)
        self.assertEquals(rc, 0)
        self.assertEquals(stderr, [])

        # Parse the show_plan data into a list of task dictionaries that can
        # easily be searched for duplicates.
        plan_dict = self.cli.parse_plan_output(stdout)
        full_list = []
        for phase, task in plan_dict.iteritems():
            for task_id, task_data in task.iteritems():
                full_task = {}
                desc = task_data.get("DESC")
                if len(desc) > 2:
                    if len(desc) > 3:
                        # Handle task descriptions spread across 3 lines.
                        desc[1] = desc[1] + ' ' + desc[2] + ' ' + desc[3]
                    else:
                        # Handle task descriptions spread across 2 lines.
                        desc[1] = desc[1] + ' ' + desc[2]
                full_task["MESSAGE"] = desc[1]
                full_task["PATH"] = desc[0]
                full_task["STATUS"] = task_data.get("STATUS")
                full_task["ID"] = task_id
                full_task["PHASE"] = phase
                full_list.append(full_task)

        return full_list

    def get_duplicate_tasks(self, node, assert_dups_empty=False):
        """
        Description:
            Assert that there are no duplicate tasks in the plan.
            Tasks are considered duplicates if they contain the same message
            and path.
            If duplicates are present, the assertion error will contain a list
            of duplicate items represented as dictionaries similar to the one
            below:

            {
                'STATUS': 'Initial',
                'PATH': '/deployments/d1/clusters/c1/services/CS1',
                'MESSAGE': 'Create IPs for VCS service group "Grp_CS_c1_CS1"',
                'ID': 1,
                'PHASE': 1
            }

            A task is considered duplicated when both the PATH and the MESSAGE
            above match exactly.

        Args:
            node (str): The node on which to run the show_plan command

            assert_dups_empty (bool): If set will assert their are no duplicate
            tasks.

        Returns:
           list. Duplicate tasks.

        Raises:
          AssertionError. If there are errors running show command or if
          duplicates found and the assert_)dups_empty flag is True.
        """
        full_list = self.get_full_list_of_tasks(node)
        duplicates = []

        count = 0
        for item1 in list(full_list):
            count += 1
            if count >= len(full_list):
                break
            for item2 in list(full_list[count:]):
                if item1["PATH"] == item2["PATH"] and \
                   item1["MESSAGE"] == item2["MESSAGE"]:
                    duplicates.append(item1)

        if assert_dups_empty:
            self.assertEqual([], duplicates)

        return duplicates

    def get_resources_from_hares_list(self, hares_output, res_type):
        """
        Description:
            Based on output passed through from the "hares -list" command,
            this method parses the output and returns all resources matching
            the specified resource type.

        Args:
            hares_output (list): List output returned from running:
                                 "get_hares_cmd('-list')".

            res_type (str): One of 'App'
                                   'IP',
                                   'NIC_Proxy',
                                   'NIC' or
                                   'Phantom_NIC'

        Returns:
            list. A list of resources running in VCS matching specified type.
        """
        res_type_options = ['App', 'IP', 'NIC_Proxy', 'NIC', 'Phantom_NIC']
        self.assertTrue(res_type in res_type_options,
                        "Specified res_type '{0}' invalid".format(res_type))

        # First parse output to get full list of resources
        res_list = []
        for line in hares_output:
            resname = line.split()
            if resname[0] not in res_list:
                res_list.append(resname[0])

        # Now reduce to only Resources of required type
        matched_res_list = []
        for item in res_list:
            if res_type == 'NIC':
                # Need to avoid matching NIC_Proxy and Phantom_NIC resources
                if res_type in item and \
                   'Proxy' not in item and 'Phantom' not in item:
                    matched_res_list.append(item)
            elif res_type in item:
                matched_res_list.append(item)

        return matched_res_list

    def re_order_list(self, original_list):
        """
        Description:
            Take in a list, rotate all elements one place to the right.

        Args:
            original_list (list): List to be rotated.

        Returns:
            list. Updated list if rotate worked. Original list
            if rotate didn't work.
        """
        try:
            return [original_list[-1]] + original_list[:-1]
        except StandardError:
            self.log("error", "List could not be re-ordered")
            return original_list

    def change_cluster_dependency_list(self, ms_node):
        """
        Description:
            Note: Method used in multiple system test testcases.
            Find and update a deployment's clusters' dependency_list property

        Args:
            ms_node (str): The ms node.

        Actions:
            1. Get the existing clusters dependency_list values and add it to
            a list.
            2. Reorder list and update the clusters' dependency_list property.

        Results:
            Updates to the model should be successfully made and
            items should be in updated state.
        """
        # Find clusters' paths
        path_to_clusters = self.find(ms_node,
                                     "/deployments",
                                     'vcs-cluster')
        dependency_list = []
        # Loop through each cluster path
        for cluster_path in path_to_clusters:
            # Get cluster dependency_list contents
            cluster_dependency = \
                self.get_props_from_url(ms_node,
                                        cluster_path,
                                        "dependency_list")
            # Check to see if a cluster has no dependencies set
            if not cluster_dependency:
                self.log("info",
                         "Cluster {0} currently has no "
                         "dependency_list property".format(cluster_path))
            else:
                # Put each cluster dependency into a common list
                dependency_list.extend([cluster_dependency])

        # re-order cluster dependency list
        new_dependency_list = self.re_order_list(dependency_list)
        self.assertTrue(new_dependency_list != dependency_list,
                        "The dependency list could not be re-ordered")

        # for every cluster
        for cluster_path in path_to_clusters:
            self.log("info", "Updating cluster {0} "
                             "dependency_list".format(cluster_path))
            # Condition for when the contents of new dependency list is empty
            # i.e. when its contents have been used and removed to iterate
            # through the list
            if new_dependency_list:
                # as long as new_dependency_list is not empty
                for dependency in new_dependency_list:
                    # Update clusters depdendency_list
                    self.execute_cli_update_cmd(ms_node,
                                                cluster_path,
                                                "dependency_list=" +
                                                dependency)
                    # Remove element from new_dependency_list
                    new_dependency_list.pop(0)
            else:
                # Update the cluster to have no dependency_list
                self.execute_cli_update_cmd(ms_node,
                                            cluster_path,
                                            "dependency_list=")
                self.log("info", "Setting cluster {0} as cluster with no "
                                 "dependency.".format(cluster_path))
        self.log("info", "Cluster dependencies have been re-ordered.")

    def get_local_rpm_path_ls(self, local_rpm_dir, rpm_filter):
        """
        Description:
            Returns a list of RPM file names on a specified path on local
            system path containing the given sub-string filter

        Args:
            local_rpm_dir (str): The path on local system where to search

            rpm_filter (str): Substring to search for in file names

        Return:
            list. The list of RPMs' absolute paths that match the given filter
        """
        rpms = []
        for filename in os.listdir(local_rpm_dir):
            if rpm_filter in filename and filename.endswith('.rpm'):
                rpms.append('{0}/{1}'.format(local_rpm_dir, filename))

        if rpms:
            self.log('info', 'List of RPMs found on "{0}" folder of the local'
                             ' system for this test'.format(local_rpm_dir))
            for rpm in rpms:
                self.log('info', rpm)
        else:
            self.log('info', 'No RPMs were found on "{0}" folder of local'
                             'system matching the "{1}" sub-string'.format(
                local_rpm_dir, rpm_filter))

        return rpms

    def perform_repeated_apd_runs(self, node, task_list, task_state):
        """
        Description:
            Loops through every task in a running plan, waits for the task to
            be successful, restarts the litpd service and then creates and runs
            the plan again. This essentially performs APD testing of an entire
            plan.
            NOTE 1: Will not test duplicated tasks in a plan. This is avoided
            due to difficulty determining which exact task is important.
            NOTE 2: Only use this during Robustness testing. It's not suitable
            for KGB/CDB testing as each test case could last for hours.

            Example Usage:
                 1. Make some updates in LITP Model
                 2. self.execute_cli_createplan_cmd(self.ms_node)
                 3. task_list = self.get_full_list_of_tasks(self.ms_node)
                 4. self.execute_cli_runplan_cmd(self.ms_node)
                 5. self.perform_repeated_apd_runs(
                                          self.ms_node,
                                          task_list,
                                          test_constants.PLAN_TASKS_RUNNING)
                 6. self.wait_for_plan_state(self.ms_node,
                                             test_constants.PLAN_COMPLETE,
                                            ))

        Args:
            node (str): The node on which to run the show_plan command

            task_list (list): list of all tasks in plan created and run
                              immediately before calling this function.

            task_state (str): The state to wait for tasks to achieve before
                              litpd restart. Supported states are
                              test_constants.PLAN_TASKS_RUNNING and
                              test_constants.PLAN_TASKS_SUCCESS only.

        Returns:
            list. Tasks in plan.
        """
        task_state_options = [test_constants.PLAN_TASKS_RUNNING,
                              test_constants.PLAN_TASKS_SUCCESS]
        self.assertTrue(task_state in task_state_options,
                        "Specified task_state '{0}' not supported"\
                                                 .format(task_state))

        tested_tasks = []
        orig_tasklist = task_list[:]
        duplicate_list = self.get_duplicate_tasks(node)
        for item in orig_tasklist:
            taskdesc = item['MESSAGE']
            if taskdesc in tested_tasks:
                self.log("info", "Skip already tested '{0}'".format(taskdesc))
                continue

            # Ensure task is in current plan
            task_found = False
            for task in task_list:
                if taskdesc == task['MESSAGE']:
                    task_found = True
                    break

            if not task_found:
                self.log("info", "Task not in plan '{0}'".format(taskdesc))
                continue

            # Skip duplicate tasks
            dup_task_found = False
            for dup in duplicate_list:
                dupdesc = dup['MESSAGE']
                if taskdesc == dup['MESSAGE']:
                    dup_task_found = True
                    break

            if dup_task_found:
                self.log("info", "Skip duplicate task '{0}'".format(dupdesc))
                continue

            self.assertTrue(self.wait_for_task_state(
                node, taskdesc, task_state, ignore_variables=False,
                timeout_mins=90), 'Task {0} was not successful'.format(
                taskdesc))
            self.restart_litpd_service(node)

            show_pln_cmd = self.cli.get_show_plan_status_cmd()
            stdout, _, _ = self.run_command(node, show_pln_cmd,
                                            default_asserts=True)

            plan_status = stdout[2].split(': ')[1]
            if plan_status == 'Successful':
                self.log("info", "Plan already Successful")
                break

            self.execute_cli_createplan_cmd(node)
            self.execute_cli_runplan_cmd(node)
            task_list = self.get_full_list_of_tasks(node)
            tested_tasks.append(taskdesc)
            duplicate_list = self.get_duplicate_tasks(node)

    def vcs_reboot_and_wait_for_system(
            self, ms_node, active_system, reboot_system,
            system_timeout_mins=5, group_timeout_mins=2):
        """
        Reboot a system and wait for it to rejoin the VCS cluster. Also waits
        for all group instances to start on the system.

        Args:
            ms_node (str): The MS node.
            active_system (str): Active VCS system in the cluster to use
                to check for system states.
            reboot_system (str): System to reboot and wait for SysState=Running
                and any groups on that system to start.
        Kwargs:
            system_timeout_mins (int): Time to wait for the rebooted system
                to get into state Running. Default is 5 minutes.
            group_timeout_mins (int): Time to wait for groups on the
                rebooted system to start. Default is 2 minutes.
        """
        self.log('info', 'Powering off {0}...'.format(reboot_system))
        self.poweroff_peer_node(ms_node, reboot_system)

        self.log('info', '{0} powered off successfully. Attempting to '
                         'power it back on...'.format(reboot_system))
        self.poweron_peer_node(ms_node, reboot_system)

        self.log('info', '{0} powered on successfully. Waiting for VCS and '
                         'groups to start...'.format(reboot_system))
        timeout_seconds = system_timeout_mins * 60

        wait_cmd = self.vcs.get_hasys_cmd(
            '-wait {0} SysState Running -time {1}'.format(
                reboot_system, timeout_seconds))

        self.run_command(active_system, wait_cmd,
                         su_root=True, default_asserts=True)

        self.log('info', 'VCS system started, waiting for groups...')
        self.wait_for_all_starting_vcs_groups(active_system,
                                              group_timeout_mins)
        self.log("info", "Groups started successfully.")

    def get_iptables_configuration(self, node, args='-S', ipv6=False):
        """
        Returns output from running iptables/ip6tables command
        on the specified node with the given args.

        Args:
            node (str): Node to run the iptables/ip6tables command on.
        Kwargs:
            args (str): iptables arguments. Default is '-S'.
            ipv6 (bool): True to check ip6tables instead of iptables.

        Results:
            (lst) Output of iptables/ip6tables command.
        """
        if ipv6:
            ip_version = test_constants.IP6TABLES_PATH
        else:
            ip_version = test_constants.IPTABLES_PATH

        cmd = '{0} {1}'.format(ip_version, args)

        self.log("info", "Running '{0}' on {1}".format(cmd, node))

        # Return std_out of running the command
        return self.run_command(node, cmd, su_root=True,
                                default_asserts=True)[0]

    def check_iptables(self, node, rules, args='-S', ipv6=False,
        expect_present=True, check_file=False, check_list=None):
        """
        Description:
            Check whether specified iptables rules exist on a specified node.
        Args:
            node (str): Node to run command on.
            rules (list): Rules to check if they are in the ip(6)tables or
                that they are not present, if expect_present is False.
                The list consists of sublists, each sublist relates to 1 line
                in the ip(6)tables.
                (e.g. [['INPUT', 'icmp', '100 icmp ipv4', 'ACCEPT'],
                    ['OUTPUT', 'udp', '1995 ntp out']])
        Kwargs:
            args (str): CLI args for ip(6)tables. Default is '-S'.
            ipv6 (bool): Check ip6tables instead of iptables if set to True.
                Default is False
            expect_present (bool): Whether the rules are expected to exist.
                Default is True.
            check_file (bool): Check ip(6)tables file instead of running
                the command. Default is False.
            check_list (list): ip(6)tables results stored in a list instead of
                running command or reading the file.
        """
        if check_file:
            if ipv6:
                iptable_path = test_constants.IPTABLES_V6_PATH
            else:
                iptable_path = test_constants.IPTABLES_V4_PATH

            self.log("info", "Retrieving '{0}' contents.".format(iptable_path))

            iptables_output = self.get_file_contents(
                node, iptable_path, su_root=True)
        elif check_list:
            iptables_output = check_list
        else:
            iptables_output = self.get_iptables_configuration(
                node, args=args, ipv6=ipv6)

        for rule in rules:

            for line in iptables_output:
                rule_present = all(section in line for section in rule)

                if rule_present:
                    break

            if expect_present:
                self.assertTrue(rule_present,
                    "{0} was not found in ip(6)tables results on {1}.".
                        format(rule, node))
            else:
                self.assertFalse(rule_present,
                    "{0} was unexpectedly found in ip(6)tables results "
                    "on {1}".format(rule, node))

    def verify_vm_rules_applied(self, ms_node, vm_fw_rules, expected_rules,
                                vm_ip, vm_service_name, vm_firewall_rule_path,
                                expect_present=True, args='-L'):
        """
        Description: Checks that the vm-firewall-rules are applied in
                     the model and checks they are present in ip(6)tables.
        Args:
            ms_node (str): The MS node to check
            vm_fw_rules (dict): Dictionary containing information about
                                each firewall rule.
            expected_rules (dict): Rules to check if they are in the
                            ip(6)tables for a vm.
                            Each value contains a list of lists with
                            each sublist corresponding to a rule in
                            the ip(6)tables.
                    (e.g.
                        {iptables : [[100 icmp ipv4', 'ACCEPT']],
                         ip6ables : [['OUTPUT', 'udp', '1995 ntp out']]}
                    )
            vm_ip (str): ipaddress of the vm to check.
            vm_service_name (str): The name of the vm to check.
            vm_firewall_rule_path: Path to vm_firewall_rule of a vm.

        KWargs:
            expect_present (bool): Whether you expect the rules to be
                                   present or absent. Default is True.
            args (str): Args to pass to the iptables(6) command.
                            Default is '-L'. Ex. "iptables -L INPUT"
        """
        for rule in vm_fw_rules:
            if expect_present:
                self.assertEqual(self.get_item_state(ms_node,
                            "{0}/{1}".format(vm_firewall_rule_path,
                            rule["item_name"])), "Applied")

        for iptable_type in expected_rules:
            self.check_iptables_on_vm(ms_node, vm_service_name, vm_ip,
            expected_rules[iptable_type], iptable=iptable_type,
            expect_present=expect_present, ipt_args=args)

    def check_iptables_on_vm(self, ms_node, service_name, ipaddr, rules,
                             iptable="iptables", expect_present=True,
                             ipt_args='-L'):
        """
        Description: Checks the ip(6)tables on the selected vm and compares
                     the output with what rules are expected or not expected
                     depending on the 'expect_present' kwarg. It verifies that
                     the accept rules are at the top while the drop rules are
                     added to the bottom of the chain.
        Args:
            ms_node (str): The MS node to check
            service_name (str): The name of the VM.
            ipaddr (str): The ipaddress of the VM.
            rules (list): list containing sublist with each sublist
                          corresponding to a line in the ip(6)tables.
        KWargs:
            iptable (str): Specify whether you want to check iptables or
                           ip6tables. The default is iptables.
            expect_present (bool): Specifies whether you expect the passed
                                    rules to be present in the iptables
                                    or not. Default is True.
            ipt_args (str): Args to pass to the iptables(6) command.
                                Default is '-L'. Ex. "iptables -L INPUT"
        """
        if iptable is "ip6tables":
            if service_name == self.sles_vm:
                ip_version = test_constants.IP6TABLES_SLES_PATH
            else:
                ip_version = test_constants.IP6TABLES_PATH
            ipv6 = True
        else:
            if service_name == self.sles_vm:
                ip_version = test_constants.IPTABLES_SLES_PATH
            else:
                ip_version = test_constants.IPTABLES_PATH
            ipv6 = False

        chains = ['INPUT', 'OUTPUT']

        list_order_err_msg = "The output from the cmd '{0}' on" \
                             " the vm_node '{1}' is not ordered as expected. "\
                             "The rules should be ordered by rule number."

        for chain in chains:
            iptable_cmd = '{0} {1} {2}'.format(ip_version, ipt_args, chain)

            if service_name == self.sles_vm:
                vm_password = test_constants.LIBVIRT_SLES_VM_PASSWORD
            else:
                vm_password = test_constants.LIBVIRT_VM_PASSWORD

            self.add_vm_to_node_list(service_name,
                                 username=test_constants.LIBVIRT_VM_USERNAME,
                                 password=vm_password,
                                 ipv4=ipaddr)

            iptables_output, _, _ = self.run_command(service_name, iptable_cmd,
                                                     username=test_constants.
                                                     LIBVIRT_VM_USERNAME,
                                                     password=vm_password,
                                                     execute_timeout=60,
                                                     default_asserts=True)

            rule_num_list = []

            for line in iptables_output:
                rule_num = []

                rule_num = re.findall(r'(?<=\/\*\W)(.*?)(?=\W)', line)

                if rule_num:
                    rule_num_list.append(int(rule_num[0]))

            self.assertTrue(sorted(rule_num_list) == rule_num_list,
                            list_order_err_msg.format(iptable_cmd,
                                                      service_name))

            self.check_iptables(ms_node, rules, ipv6=ipv6,
                                expect_present=expect_present,
                                check_list=iptables_output)

    # Underscore to avoid pylint error in testset_vcs_setup.py
    def verify_deployments_by_node(self, list_of_cs, cluster_id, conf,
                                   hagrp_output, hares_output, network_dev_map,
                                   list_managed_nodes):
        """
        Description:
              Function which verifies a list of packages are installed on the
              nodes and verifies a given list of clustered-services and all
              their resources are online on the correct nodes.

        Args: list_of_cs (list): Clustered Service names.

              cluster_id (str): id of the cluster in the model.

              conf (dict): Dictionary of the expected configuration

              hagrp_output (str): Output of the VCS hagrp -state command

              hares_output (str): Output of the VCS hares -state command

              network_dev_map (Dict): Dictionary of network names and
                                  their device name

              list_managed_nodes (list): List of the nodes to check for
                                         packages on.
        """

        # ==============================================
        # Determine if all packages have been deployed on
        # the nodes in the cluster
        # ===============================================
        for cs_name in list_of_cs:
            pkgs_per_app = \
                         conf["pkg_per_app"][conf['app_per_cs'][cs_name]]
            for pkg in pkgs_per_app:
                cmd = self.rhc.check_pkg_installed([pkg])
                nr_of_nodes_pkgs = 0
                for node in list_managed_nodes:
                    list_installed_pkgs, _, _ = \
                            self.run_command(node, cmd, su_root=True)

                    for installed_pkg in list_installed_pkgs:
                        if re.search(pkg + '-', installed_pkg):
                            nr_of_nodes_pkgs += 1

                self.assertEqual(len(conf['nodes_per_cs'][cs_name]),
                                 nr_of_nodes_pkgs)

            # ==================================================
            # Verify that the plan has configured VCS correctly
            # ==================================================
            self.assertTrue(self.vcs.verify_vcs_clustered_services(
                                                             cs_name,
                                                             cluster_id,
                                                             conf,
                                                             hagrp_output,
                                                             hares_output,
                                                             network_dev_map))

    def toggle_puppet(self, node, enable=True):
        """
        Enables or disables puppet agent on the specified node.
        Args:
           node (str): Node to run command on.
        KwArgs:
           enable (boolean): This specifies whether to enable/disable the
                             puppet agent. Default value is True.
       """
        cmd = "{0} agent ".format(test_constants.PUPPET_PATH)
        if enable:
            self.log('info', 'Enabling puppet agent on {0}.'.format(node))
            cmd += "--enable"
        else:
            self.log('info', 'Disabling puppet agent on {0}.'.format(node))
            cmd += "--disable"

        self.run_command(node, cmd, su_root=True)

        self.log('info', 'Check if file created by puppet exists -'
                         ' agent_disabled.lock.')

        check_file = " [ -f {0} ]".format(
            test_constants.PUPPET_AGENT_DISABLED_FILE)
        _, _, rc = self.run_command(node, check_file, su_root=True)

        self.log('info', 'Asserting whether agent_disabled.lock exists based'
                         ' on whether puppet agent was enabled/disabled.')
        if enable:
            self.assertEqual(rc, 1, "Unexpectedly found agent_disabled.lock"
                                    "on {0} after enabling puppet.".format(
                                     node))
        else:
            self.assertEqual(rc, 0, 'Expected to find agent_disabled.lock on '
                                    '{0} after disabling puppet but was not '
                                    'found'.format(node))

    def kill_puppet_agent(self, ms_node, node):
        """
        Kills puppet runs on specified node
            Args:
                ms_node (str): MS node to run the command on

                node (str): Node on which to kill the puppet runs
        """
        self.log("info", "Killing puppet runs on {0}".format(node))
        cmd = \
            "{0} rpc -agent puppetagentkill -action kill_puppet_agent -I {1}"\
            .format(test_constants.MCO_EXECUTABLE, node)

        self.run_command(ms_node, cmd, su_root=True, default_asserts=True)

    def get_nas_server_type(self, concat_ver=True):
        """
        Establish the type of NAS Server

        Kwargs:
            concat_ver(bool): Concatenates the returned version to first
                              decimal point

        Returns:
            nas_info (list): NAS name and NAS version from server banner
        """
        # Get the NAS Server
        nas_server = self.get_sfs_node_filenames()[0]
        nas_info = None

        banner_path = None

        # Connect to NAS as a support user
        self.assertTrue(self.set_node_connection_data(
            nas_server,
            username=test_constants.SFS_SUPPORT_USR,
            password=test_constants.SFS_SUPPORT_PW))

        for path in self.nas_server_banners:
            rc = self.run_command(nas_server,
                                  '[ -f {0} ]'.format(path))[2]
            if rc == 0:
                banner_path = path
                break

        self.assertNotEqual(banner_path, None, 'Unable to identify location '
                                               'of banner')

        banner_output, std_err, rc = self.run_command(nas_server,
                                                      '{0} {1}'.format(
                                                       test_constants.CAT_PATH,
                                                       banner_path))
        self.assertEqual(std_err, [],
                         'Error executing run command \'{0}\''.format(std_err))
        self.assertEqual(rc, 0)

        nas_line = ''
        for line in banner_output:
            for nas_type in self.nas_type_list:
                if nas_type in line:
                    nas_line = line
        self.assertNotEqual(nas_line, '', 'Could not find an expected NAS '
                                          'type in the banner')

        matching_string = re.match(r'\*\s+(.+)\s+\*', nas_line)
        self.assertNotEqual(matching_string, None, 'Could not match expected '
                                                   'regex in string')

        matching_string = matching_string.group(1).strip()

        for nas_type in self.nas_type_list:
            if matching_string.startswith(nas_type):
                # Split string into words
                banner_string_array = matching_string.split(' ')

                version = banner_string_array[len(banner_string_array) - 1]

                if concat_ver:
                    version = version.split('.')
                    version = '{0}.{1}'.format(version[0], version[1])

                nas_info = [nas_type, version]

        self.assertNotEqual(nas_info, None, 'Unable to determine NAS for '
                                            'server: {0}'.format(nas_server))

        return nas_info
