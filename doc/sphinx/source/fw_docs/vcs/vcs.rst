VCS Test Framework
====================

This document outlines the procedure for creating IT tests for the ERIClitpvcs-testware repo. Please follow the steps outlined below along with reading the content description at each stage, explaining whats going on. 

Reason behind using this VCS Test Framework
---------------------------------------------

Due to the nature of the VCS testware repo issues met in the past highlighted that the repo has a lot of dependencies between test sets/cases. Meaning the test suite was highly prone to bugs. This inevitably lead to complex test suites which we all should avoid. In the past any basic refactoring job that took place with intial tests cases caused a spiral of increasingly difficult solutions needed to be found with associated tests, which was time costly. 

 The Solution to the problem
 ----------------------------
 What was found in the VCS testware repo was a baseline was needed as part of every test set. Meaning that many of the test cases use the same initial structure with the setup() method supplied by unit test framework. This is essentially what allows the design of the IT's for the VCS testware repo to be a lot easier, as if every test case uses the same VCS clustered service to be created, then each test case will independently set the parameters that is associated with the test case scenario, saving a lot of time with creating and teardown, as well as not having test cases depend on one another for values and parameter changes;

** For Example **
**The Test cases below highlight how test cases could potentially be dependent on one another. The major issue with this methodology is if Test Case 1 fails, Test Case 2 will never get run which is not what we want to happen. As testers we want to keep each test case as isolated as possible**
  ==============================================  =====================================================
  Test Case 1                                     Test Case 2 
  ==============================================  =====================================================
  Creates One Fail Over VCS Clustered Service     Takes Parallel VCS Clustered Service created from TC1 
  Expand VCS Clustered Service to be Parallel     Add Virtual Machine on Nodes
  Validate the Cluster is now running two nodes   Add Virtual IPs 
  in Parallel                                     Validate VMs are running
  ==============================================  =====================================================

**Note:** Currently there is no libvirt support the vcs fixtures generator but will be added for future stories 


How to use the VCS Test Framework
----------------------------------
The first thing a tester must ensure when working with the VCS testware repo is that they have imported vcs_utils, fixtures generator and set the constant 'STORY' which corresponds to the story of the test cases being developed for. The code snippet for these imports can be found below:


Imports Needed to use the VCS Framework
----------------------------------------

.. code-block:: python
  
  from vcs_utils import VCSUtils
  from generate import load_fixtures, generate_json, apply_item_changes, \
      apply_options_changes
 
  STORY = '9600'

Essentially, these imports should be all a tester should require for creating test cases for the VCS testware repo. Examples and notes on the imported methods being used can be found in the segments below.


Methods Needed to create an applied VCS configuration
------------------------------------------------------

- vcs_utils.py module contains vcs command related utilities.
- generate.py module contains a few helper methods for the generation of test cases. Each imported method description and illustration are as follows.

**Step 1:**

**Generate_JSON**

- generate_json is a method that creates the json schema for usage with the fixtures object later on in the code. 

**NOTE** The json method below will optionally write a json schema to a file if they wish, sets the story to the corresponding value that was set during the imports. Creates one VCS clustered service, application, HA-service-configuration. Then sets the optional on/offline timeout values along with the HA-service-config options. The last option add_to_cleanup is either set to True/False, which basically sets the baseline fixtures back to what they were prior to any test case completing. 

.. code-block:: python

  _json = generate_json(to_file=False, story=STORY,
                                vcs_length=1,
                                app_length=1,
                                hsc_length=1,
                                vcs_options='online_timeout="180"' 'offline_timeout="180"',
                                hsc_options='fault_on_monitor_timeouts="280"'
                                'tolerance_limit="300"',
                                add_to_cleanup=False)

The parameters seen above for vcs and hsc_options can be declared as part of the json schema **OPTIONALLY**. They can be declared later in test code as part of independent test cases if needed. However these parameters for vcs and hsc are completely optional, and are not mandatory fields comapred to the others. Please reference Step 4. 

**Step 2:**

**Load_fixtures**

- load_fixtures is a method that loads and modifies fixture values from variables. It also inspects the state of the deployment systems during runtime and appends node information where necessary.

**NOTE** The dictionary self.fixtures is generated from the load_fixtures method that takes the story number the vcs-cluster-url, node-urls and setting a flag equal to json to highlight the input is of json format. 

.. code-block:: python

  self.management_server = self.get_management_node_filename()
  self.vcs_cluster_url = self.find(self.management_server, '/deployments', 'vcs-cluster')[0]
  nodes_urls = self.find(self.management_server, self.vcs_cluster_url, 'node')
  
  self.fixtures = load_fixtures(STORY, self.vcs_cluster_url, nodes_urls, input_data=_json)

**Step 3:**

**Apply_item_changes**

- apply_item_changes is a method that works similarly to apply_options_changes method found below, except the dictionary that it uses does not change the optional parameters in litp, instead the apply_item_changes method changes the whole item structure of a declared item in litp. This is where specific test cases requirements are met. 

.. code-block:: python

  apply_item_changes(self.fixtures, 'service', 0,
                       {'parent': "CS_9600_1",
                        'destination': self.vcs_cluster_url +
                        '/services/CS_9600_1/applications/APP_9600_1'})

**Step 4:**

**Apply_options_changes**

- apply_options_changes function accepts a generated fixture (self.fixtures), a string with the item type (in the example below we use 'vcs-clustered-service'), an index of the item that needs to be changed (in this case there is normally one vcs cs so the index is 0), and a dictionary of custom options that are going to update the generated one at runtime. The last parameter is a boolean which can change the behaviour of the method, making it overwrite the options instead of updating them (This is noramally set to True)

.. code-block:: python

    apply_options_changes(
        self.fixtures,
        'vcs-clustered-service', 1, {'active': '1', 'standby': '0',
                                     'offline_timeout': '401',
                                     'name': 'CS_9600_2',
                                     'node_list': 'n1'},
        overwrite=True)

**NOTE: These method imports and declarations ideally should be at the beginning of the python file in setup, although if there are numerous test cases with varying implementations the apply_options_changes can be added as part of a specific test rather than in setup, which can speed up test execution even further. 

Lastly to note if a VCS configuration already exists in the model and a tester tries to create the same item, the test will fail.**

**Please find full worked example below** 

Example 1:
==========

**Story which creates the following**

===================== ============ =========================
Item Type              Quantity    Applied Options                
===================== ============ =========================
VCS-clustered-service   1           active=2, name=CS_5169_1
App resource            1           None
HA-service-config       1           None
===================== ============ =========================

.. code-block:: python

  import os
  from litp_generic_test import GenericTest, attr
  import test_constants
  from vcs_utils import VCSUtils
  from generate import load_fixtures, generate_json, apply_options_changes, \
      apply_item_changes

  STORY = '5169'

  def setUp(self):
        super(Story5169, self).setUp()
        # specify test data constants
        self.management_server = self.get_management_node_filename()
        self.vcs = VCSUtils()
        # Location where RPMs to be used are stored
        self.rpm_src_dir = (os.path.dirname(
            os.path.realpath(__file__)) + '/rpm-out/dist/')

        # Current assumption is that only 1 VCS cluster will exist
        self.vcs_cluster_url = self.find(self.management_server,
                                         '/deployments', 'vcs-cluster')[0]
        self.cluster_id = self.vcs_cluster_url.split('/')[-1]
        self.node_flnmes = self.get_managed_node_filenames()
        nodes_urls = self.find(self.management_server,
                               self.vcs_cluster_url,
                               'node')

        _json = generate_json(to_file=False, story=STORY,
                              vcs_length=1,
                              app_length=1,
                              hsc_length=1
                              )
        self.fixtures = load_fixtures(
            STORY, self.vcs_cluster_url, nodes_urls, input_data=_json)
        apply_options_changes(
            self.fixtures,
            'vcs-clustered-service', 0, {'active': '2', 'standby': '0',
                                         'name': 'CS_5169_1',
                                         'node_list': 'n1,n2'},
            overwrite=True)

Example 2:
==========

**A Little more complex Example which creates the following**

**Test Case 01**

===================== ============ ====================================
Item Type              Quantity    Applied Options                
===================== ============ ====================================
VCS-clustered-service   2           active=2, name=CS_5168_1, CS_5168_2
App resource            2           None
HA-service-config       2           None
===================== ============ ====================================

**Test Case 02**

===================== ============ ====================================
Item Type              Quantity    Applied Options                
===================== ============ ====================================
VCS-clustered-service   1           active=2, name=CS_5168_1
App resource            1           None
HA-service-config       1           None
===================== ============ ====================================
**Note: **In this example each test case implements its litp model changes in the test case itself. This is due to the test cases meeting specific edge case scenarios, hence it could be a useful source if ever faced with needing to create another litp item after the initial fixtures dictionary (mentioned above) has been generated. 

.. code-block:: python
  
  import os
  from litp_generic_test import GenericTest, attr
  import test_constants
  from vcs_utils import VCSUtils
  from generate import load_fixtures, generate_json, apply_options_changes, \
      apply_item_changes

  STORY = '5168'


  class Story5168(GenericTest):
      """
      LITPCDS-5168:
      As a LITP user i want to contract my parallel VCS Service Group so that an
      application can run on less nodes if required
      The user should be able to perform the following:
          -A user can remove a node from the node_list property of a vcs-
           clustered-service which will result in a contraction of the associated
           Service Group
          -I should see that any node removed from the node_list should no longer
           have its inherited packages installed on that node
          -If I attempt to change the node_list property such that the "new-node-
           list" is not a subset of the "old node_list" property then I should
           see a validation error
          -If I attempt to reduce the node_list property and the vcs-clustered-
           service contains vip items then i should see a validation error
          -If I attempt to contract a vcs-clustered-service which has properties
           active=1 and standby=1 then i should see a validation error

           Generator command:
           Test Case 1
          python generate.py --s 5168 --a 2 --vcs 2 --hsc 2 \
          --vcso 'active="2"' 'standby="0"'
           Test Case 2
           python generate.py --s 5168 --a 1 --vcs 1 --hsc 1 \
          --vcso 'active="2"' 'standby="0"'
      """

      def setUp(self):
          super(Story5168, self).setUp()
          # specify test data constants
          self.management_server = self.get_management_node_filename()
          self.vcs = VCSUtils()
          # Location where RPMs to be used are stored
          self.rpm_src_dir = (os.path.dirname(
              os.path.realpath(__file__)) + '/rpm-out/dist/')

          self.vcs_cluster_url = self.find(self.management_server,
                                           '/deployments', 'vcs-cluster')[-1]
          self.vcs_cluster_url_dep = self.find(self.management_server,
                                               '/deployments', 'vcs-cluster')[0]
          self.cluster_id = self.vcs_cluster_url.split('/')[-1]
          self.node_flnmes = self.get_managed_node_filenames()
          self.nodes_urls = self.find(self.management_server,
                                      self.vcs_cluster_url,
                                      'node')
          self.node_ids = [node.split('/')[-1] for node in self.nodes_urls]

      def tearDown(self):
          """
          Description:
              Runs after every single test
          Actions:
              -
          Results:
              The super class prints out diagnostics and variables
          """
          super(Story5168, self).tearDown()

      def baseline(self, vcs_len, app_len, hsc_len, cleanup=False):
          """
          Description:
              Runs initially with every test case to set up litp model
              with vcs/app and ha service parameters
          Parameters:
              vcs_len: (int) Number of VCS CS
              app_len: (int) Number of applications
              hsc_len: (int) Number of HA Service Configs
              cleanup: (bool) Add
          Actions:
              Declares fixtures dictionary for litp model generation
          Returns:
              fixtures dictionary
          """
          _json = generate_json(to_file=False, story=STORY,
                                vcs_length=vcs_len,
                                app_length=app_len,
                                hsc_length=hsc_len,
                                add_to_cleanup=cleanup)
          return load_fixtures(
              STORY, self.vcs_cluster_url, self.nodes_urls, input_data=_json)

      @attr('all', 'revert',
            'story5168', 'story5168_tc01', 'cdb_priority1')
      def test_01_p_rmve_node_frm_node_lst(self):
          """
          Test to validate that a user is capable of removing a node from a node
          list with a VCS parallel clustered service, without any validation
          errors, and verify that any inherited packages that were previously on
          the removed node, are deleted.

           Steps:
                  1. Create two, two node parallel VCS CSs
                  2. Create dependency between CSs and contract the CS that is
                   dependent upon
                  3. Remove a node from the node_list property per VCS CS
                  4. Validate the service group has been contracted through VCS
                  5. Verify any inherited packages previously on the removed node
                   is not longer inherited
          """
          fixtures = self.baseline(2, 2, 2, cleanup=True)
          # Properties to update VCS CS with
          node_props = 'node_list={0} active=1'.format(self.node_ids[0])
          # Step 1 and 2

          cs_url = self.get_cs_conf_url(self.management_server,
                                        fixtures['service'][0]['parent'],
                                        self.vcs_cluster_url)

          # Execute initial plan creation if test data if is not applied already
          if cs_url is None:
              apply_options_changes(fixtures, 'vcs-clustered-service', 0,
                                    {'active': '2', 'standby': '0',
                                               'name': 'CS_5168_1',
                                               'node_list': '{0}'
                                               .format(','.join(self.node_ids))},
                                    overwrite=True)

              apply_options_changes(fixtures, 'vcs-clustered-service', 1,
                                    {'active': '2', 'standby': '0',
                                               'name': 'CS_5168_2',
                                               'node_list': '{0}'.
                                               format(','.join(self.node_ids)),
                                               'dependency_list': 'CS_5168_1'},
                                    overwrite=True)
              # Create application and HA Service Config for VCS CS_5168_2
              apply_item_changes(fixtures, 'service', 1,
                                 {'parent': "CS_5168_2", 'destination':
                                  self.vcs_cluster_url_dep +
                                  '/services/CS_5168_2/applications/' +
                                  'APP_5168_2'})
              apply_item_changes(fixtures, 'ha-service-config', 1,
                                 {'vpath': self.vcs_cluster_url +
                                  '/services/CS_5168_2/ha_configs/' +
                                  'HSC_5168_2'})
              self.apply_cs_and_apps_sg(self.management_server,
                                        fixtures,
                                        self.rpm_src_dir)

              # This section of the test sets up the model and creates the plan
              self.run_and_check_plan(self.management_server,
                                      test_constants.PLAN_COMPLETE, 5)

              # Get CS_URL for CS_5168_2
              first_cs_url = self.get_cs_conf_url(self.management_server,
                                                  fixtures['service']
                                                  [0]['parent'],
                                                  self.vcs_cluster_url)
              second_cs_url = self.get_cs_conf_url(self.management_server,
                                                   fixtures['service']
                                                   [1]['parent'],
                                                   self.vcs_cluster_url)
          # Step 3
          self.execute_cli_update_cmd(self.management_server,
                                      first_cs_url, node_props)

          self.execute_cli_update_cmd(self.management_server,
                                      second_cs_url, node_props)

          self.run_and_check_plan(self.management_server,
                                  test_constants.PLAN_COMPLETE, 10)
          # Step 4 and 5
          cs_group_name = self.vcs.generate_clustered_service_name(
              fixtures['service'][1]['parent'], self.cluster_id)

          grp_status_cmd = \
              self.vcs.get_hagrp_cmd('-state {0} -sys {1}'.
                                     format(cs_group_name, self.node_flnmes[0])
                                     )
          stdout, _, _ = self.run_command(self.node_flnmes[0], grp_status_cmd,
                                          su_root=True, default_asserts=True)

          self.assertEqual('ONLINE', stdout[0])
          # Verify the dependency still exists
          second_cs_group_name = \
              self.vcs.generate_clustered_service_name(fixtures['service']
                                                       [1]['parent'],
                                                       self.cluster_id)
          cmd = self.vcs.get_hagrp_dep_cmd(second_cs_group_name)

          stdout, _, _ = self.run_command(self.node_flnmes[0], cmd, su_root=True,
                                          default_asserts=True)
          self.assertEqual('{0} {1} online local'
                           ' soft'.format(second_cs_group_name, cs_group_name),
                           stdout[1])

      @attr('pre-reg', 'non-revert', 'story5168', 'story5168_tc02')
      def test_02_p_verify_cs_contraction_apps_can_be_reused(self):
          """
          Test to validate when a two node parallel clustered service is
          contracted that has an inherited service, and subsequently in a new
          plan add an additional clustered service which inherits the same
          service, there should not be an error

           Steps:
                  1. Create one, two node parallel VCS CSs
                  2. Contract the parallel VCS CS to be a one node parallel CS
                      and create/run plan
                  3. Create new one node parallel VCS CS
                  4. Inherit same service onto new CS that was previously used
                   on the parallel CS
                  5. Validate successful plan
          """
          # Properties the VCS CS are updated with
          cs_update_props = \
              'node_list={0} active=1'.format(self.node_ids[0])

          cs_create_props = ('name=CS_5168_2 standby=0 node_list={0} active=1'.
                             format(self.node_ids[1]))

          # Step 1
          fixtures = self.baseline(1, 1, 1)

          apply_options_changes(
              fixtures,
              'vcs-clustered-service', 0, {'active': '2', 'standby': '0',
                                           'name': 'CS_5168_1',
                                           'node_list': '{0}'.
                                           format(','.join(self.node_ids))},
              overwrite=True)

          cs_url = self.get_cs_conf_url(self.management_server,
                                        fixtures['service'][0]['parent'],
                                        self.vcs_cluster_url)

          # Execute initial plan creation if test data if is not applied already
          if cs_url is None:
              self.apply_cs_and_apps_sg(self.management_server,
                                        fixtures,
                                        self.rpm_src_dir)
              # This section of the test sets up the model and creates the plan
              self.run_and_check_plan(self.management_server,
                                      test_constants.PLAN_COMPLETE, 5)
              cs_url = self.get_cs_conf_url(self.management_server,
                                            fixtures['service'][0]['parent'],
                                            self.vcs_cluster_url)
          # Step 2
          self.execute_cli_update_cmd(self.management_server,
                                      cs_url, cs_update_props)
          self.run_and_check_plan(self.management_server,
                                  test_constants.PLAN_COMPLETE, 5)
          # Step 3 and 4
          self.execute_cli_create_cmd(self.management_server,
                                      self.vcs_cluster_url + '/services/' +
                                      'CS_5168_2',
                                      'vcs-clustered-service',
                                      cs_create_props,
                                      add_to_cleanup=False)

          self.execute_cli_create_cmd(self.management_server,
                                      self.vcs_cluster_url +
                                      '/services/CS_5168_2/ha_configs/' +
                                      'service_config',
                                      'ha-service-config',
                                      add_to_cleanup=False)

          self.execute_cli_inherit_cmd(self.management_server,
                                       self.vcs_cluster_url +
                                       '/services/CS_5168_2/applications/' +
                                       'APP_5168_2',
                                       '/software/services/APP_5168_1',
                                       add_to_cleanup=False)
          # Step 5
          self.run_and_check_plan(self.management_server,
                                  test_constants.PLAN_COMPLETE, 5)


**Follow up**

From the example stories above, the code snippets seen above generate vcs-clustered services along with applicationa and ha-service-configuration. The stages after this setup, is to create test methods that either set/validate specific cases outlined from a testers test case design as they would normally. Please remember that edge cases can be met as well like what is seen in the second example.   
