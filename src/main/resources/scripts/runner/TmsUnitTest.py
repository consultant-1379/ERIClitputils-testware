import json
import pprint
import unittest
from test_runner import TmsResponse
from test_runner import Tms
class TestTMS(unittest.TestCase):

    def get_sample(self):
        return [
            'def test_01_p_cs_deploy_and_set_props(self):'
                '"""'
                '@tms_id: litpcds_10167_tc01a',
                '@tms_requirements_id: LITPCDS-10167',
                '@tms_title:',
                'Critical Service deploy and set properties',
                '@tms_description:',
                 'To ensure that it is possible to create, a vcs-cluster(sfha) with',
                 '"critical_service" property and a "vcs-clustered-service" as part',
                 'from the cluster. Update the model with task which can cause node lock',
                 '(change kernel parameter). Create plan and fail over the service',
                 'before create plan. Run the plan and check critical service',
                 'online status during all of lock phases. After successful plan',
                 'check critical service is still online on the same node',
                 'as before create plan..',
                '@tms_test_steps:',
                '@step: Run a plan which creates a service object and a',
                        '"clustered-service" as part from',
                        'present "vcs-cluster", and adds "critical_service" property',
                        'which is pointing to the service.',
                '@result: Plan executes successfully',
                '@step: Create a plan which updates the model with a task which',
                        'can cause node lock.',
                '@result: The first lock should be in the standby node of the plan',
                '@step: Remove the plan',
                '@result: Removal command executes successfully',
                '@step: Switch the service to the standby node and wait for it to',
                    'come online',
                '@result: Service has now been switched to the standby node',
                '@step: Run create plan command',
                '@result: Check lock order',
                '@step: Run Plan',
                '@result: During first node lock the service is not running in the',
                    'standby node and is running in the active node.',
                '@step: Restart the litp service while plan is running',
                '@result: Restarts and healthcheck passes',
                '@step: Create and run the plan',
                '@result: First lock applied phase is not present in initial state.',
                '@result: During second node lock the service is running in the standby',
                    'node and is not running in the active node.',
                '@result: Plan completes successfully',
                '@tms_test_precondition: NA',
                '@tms_execution_type: Automated',
                '"""'
                ]
    def get_sample_after_desc_changed(self):
        return [
            'def test_01_p_cs_deploy_and_set_props(self):'
                '"""'
                '@tms_id: litpcds_10167_tc01a',
                '@tms_requirements_id: LITPCDS-10167',
                '@tms_title:',
                'Critical Service deploy and set properties',
                '@tms_description:',
                 'To ensure that it is possible to create, a vcs-cluster(sfha) with',
                 '"critical_service" property and a "vcs-clustered-service" as part',
                 'from the cluster. Update the model with task which can cause node lock',
                 '(change kernel parameter). Create plan and fail over the service',
                 'before create plan. Run the plan and check critical service',
                 'online status during all of lock phases. After successful plan',
                 'check critical service is still online on the same node',
                 'as before create plan.!',
                '@tms_test_steps:',
                '@step: Run a plan which creates a service object and a',
                        '"clustered-service" as part from',
                        'present "vcs-cluster", and adds "critical_service" property',
                        'which is pointing to the service.',
                '@result: Plan executes successfully',
                '@step: Create a plan which updates the model with a task which',
                        'can cause node lock.',
                '@result: The first lock should be in the standby node of the plan',
                '@step: Remove the plan',
                '@result: Removal command executes successfully',
                '@step: Switch the service to the standby node and wait for it to',
                    'come online',
                '@result: Service has now been switched to the standby node',
                '@step: Run create plan command',
                '@result: Check lock order',
                '@step: Run Plan',
                '@result: During first node lock the service is not running in the',
                    'standby node and is running in the active node.',
                '@step: Restart the litp service while plan is running',
                '@result: Restarts and healthcheck passes',
                '@step: Create and run the plan',
                '@result: First lock applied phase is not present in initial state.',
                '@result: During second node lock the service is running in the standby',
                    'node and is not running in the active node.',
                '@result: Plan completes successfully',
                '@tms_test_precondition: NA',
                '@tms_execution_type: Automated',
                '"""'
                ]

    def get_sample_after_step_change(self):
        return [
            'def test_01_p_cs_deploy_and_set_props(self):'
                '"""'
                '@tms_id: litpcds_10167_tc01a',
                '@tms_requirements_id: LITPCDS-10167',
                '@tms_title:',
                'Critical Service deploy and set properties',
                '@tms_description:',
                 'To ensure that it is possible to create, a vcs-cluster(sfha) with',
                 '"critical_service" property and a "vcs-clustered-service" as part',
                 'from the cluster. Update the model with task which can cause node lock',
                 '(change kernel parameter). Create plan and fail over the service',
                 'before create plan. Run the plan and check critical service',
                 'online status during all of lock phases. After successful plan',
                 'check critical service is still online on the same node',
                 'as before create plan..',
                '@tms_test_steps:',
                '@step: Run a plan which creates a service object and a',
                        '"clustered-service" as part from',
                        'present "vcs-cluster", and adds "critical_service" property',
                        'which is pointing to the service.',
                '@result: Plan executes successfully',
                '@step: Create a plan which updates the model with a task which',
                        'can cause node lock.',
                '@result: The first lock should be in the standby node of the plan',
                '@step: Remove the plan',
                '@result: Removal command executes successfully',
                '@step: Switch the service to the standby node and wait for it to',
                    'come online',
                '@result: Service has now been switched to the standby node',
                '@step: Run create plan command',
                '@result: Check lock order',
                '@step: Run Plan',
                '@result: During first node lock the service is not running in the',
                    'standby node and is running in the active node.',
                '@step: Restart the litp service while plan is running',
                '@result: Something',
                '@step: Create and run the plan',
                '@result: First lock applied phase is not present in initial state.',
                '@result: During second node lock the service is running in the standby',
                    'node and is not running in the active node.',
                '@result: Plan completes successfully',
                '@tms_test_precondition: NA',
                '@tms_execution_type: Automated',
                '"""'
                ]

    def get_sample_after_step_added(self):
        return [
            'def test_01_p_cs_deploy_and_set_props(self):'
                '"""'
                '@tms_id: litpcds_10167_tc01a',
                '@tms_requirements_id: LITPCDS-10167',
                '@tms_title:',
                'Critical Service deploy and set properties',
                '@tms_description:',
                 'To ensure that it is possible to create, a vcs-cluster(sfha) with',
                 '"critical_service" property and a "vcs-clustered-service" as part',
                 'from the cluster. Update the model with task which can cause node lock',
                 '(change kernel parameter). Create plan and fail over the service',
                 'before create plan. Run the plan and check critical service',
                 'online status during all of lock phases. After successful plan',
                 'check critical service is still online on the same node',
                 'as before create plan..',
                '@tms_test_steps:',
                '@step: Run a plan which creates a service object and a',
                        '"clustered-service" as part from',
                        'present "vcs-cluster", and adds "critical_service" property',
                        'which is pointing to the service.',
                '@result: Plan executes successfully',
                '@step: Create a plan which updates the model with a task which',
                        'can cause node lock.',
                '@result: The first lock should be in the standby node of the plan',
                '@step: Remove the plan',
                '@result: Removal command executes successfully',
                '@step: Switch the service to the standby node and wait for it to',
                    'come online',
                '@result: Service has now been switched to the standby node',
                '@step: Run create plan command',
                '@result: Check lock order',
                '@step: Do something',
                '@result: Something happened',
                '@step: Run Plan',
                '@result: During first node lock the service is not running in the',
                    'standby node and is running in the active node.',
                '@step: Restart the litp service while plan is running',
                '@result: Restarts and healthcheck passes',
                '@step: Create and run the plan',
                '@result: First lock applied phase is not present in initial state.',
                '@result: During second node lock the service is running in the standby',
                    'node and is not running in the active node.',
                '@result: Plan completes successfully',
                '@tms_test_precondition: NA',
                '@tms_execution_type: Automated',
                '"""'
                ]

    def get_sample_after_step_removed(self):
        return [
            'def test_01_p_cs_deploy_and_set_props(self):'
                '"""'
                '@tms_id: litpcds_10167_tc01a',
                '@tms_requirements_id: LITPCDS-10167',
                '@tms_title:',
                'Critical Service deploy and set properties',
                '@tms_description:',
                 'To ensure that it is possible to create, a vcs-cluster(sfha) with',
                 '"critical_service" property and a "vcs-clustered-service" as part',
                 'from the cluster. Update the model with task which can cause node lock',
                 '(change kernel parameter). Create plan and fail over the service',
                 'before create plan. Run the plan and check critical service',
                 'online status during all of lock phases. After successful plan',
                 'check critical service is still online on the same node',
                 'as before create plan..',
                '@tms_test_steps:',
                '@step: Run a plan which creates a service object and a',
                        '"clustered-service" as part from',
                        'present "vcs-cluster", and adds "critical_service" property',
                        'which is pointing to the service.',
                '@result: Plan executes successfully',
                '@step: Create a plan which updates the model with a task which',
                        'can cause node lock.',
                '@result: The first lock should be in the standby node of the plan',
                '@step: Remove the plan',
                '@result: Removal command executes successfully',
                '@step: Switch the service to the standby node and wait for it to',
                    'come online',
                '@result: Service has now been switched to the standby node',
                '@step: Run create plan command',
                '@result: Check lock order',
                '@step: Restart the litp service while plan is running',
                '@result: Restarts and healthcheck passes',
                '@step: Create and run the plan',
                '@result: First lock applied phase is not present in initial state.',
                '@result: During second node lock the service is running in the standby',
                    'node and is not running in the active node.',
                '@result: Plan completes successfully',
                '@tms_test_precondition: NA',
                '@tms_execution_type: Automated',
                '"""'
                ]

    def get_tms_session(self):
        # tms.username
        # tms.password can be manually set after Tms() call for any tests
        tms = Tms()
        tms.login_tms_session()
        return tms

    def test_parse(self):
        dato = self.get_sample()
        tms = Tms()
        res = tms.parse_tms(dato,"test_01_p_cs_deploy_and_set_props")
        tc = res["tms_id"]
        tms_thing = tms.get_test(tc).response
        import pprint
        print tms.logger
        pprint.pprint(tms_thing)

    def test_compare_safe(self):
        met = "test_01_p_cs_deploy_and_set_props"
        d1 = self.get_sample()
        dx = self.get_sample()
        d2 = self.get_sample_after_desc_changed()
        d3 = self.get_sample_after_step_added()
        d4 = self.get_sample_after_step_removed()
        d5 = self.get_sample_after_step_change()

        tms = Tms()
        r1 = tms.build_tms_request(tms.parse_tms(d1, met))
        rx = tms.build_tms_request(tms.parse_tms(dx, met))
        r2 = tms.build_tms_request(tms.parse_tms(d2, met))
        r3 = tms.build_tms_request(tms.parse_tms(d3, met))
        r4 = tms.build_tms_request(tms.parse_tms(d4, met))
        r5 = tms.build_tms_request(tms.parse_tms(d5, met))

        self.assertTrue(tms.compare_tms_records(r1, rx))
        self.assertFalse(tms.compare_tms_records(r1, r2))
        self.assertFalse(tms.compare_tms_records(r1, r3))
        self.assertFalse(tms.compare_tms_records(r1, r4))
        self.assertFalse(tms.compare_tms_records(r1, r5))

        real = tms.get_test(tms.parse_tms(d1, met)["tms_id"]).response
        self.assertTrue(tms.compare_tms_records(real, rx))
        self.assertFalse(tms.compare_tms_records(real, r2))
        self.assertFalse(tms.compare_tms_records(real, r3))
        self.assertFalse(tms.compare_tms_records(real, r4))
        self.assertFalse(tms.compare_tms_records(real, r5))


    def test_put(self):
        tms = self.get_tms_session()

        data = self.get_sample_after_step_added()
        test_method_name = "test_01_p_cs_deploy_and_set_props"
        tms_data = tms.parse_tms(data,test_method_name)

        tms.upload_to_tms(tms_data)

        pprint.pprint(tms.logger)
        pprint.pprint(tms_data)

    def test_reqs(self):
        tms = Tms()
        ret = TmsResponse()
        ret.response=dict()
        dat = dict()

        dat["tms_requirements_id"]=None
        ret.response["requirements"]=None
        requires = tms.get_requirements_data(ret, dat)
        self.assertEqual(requires,[])

        dat["tms_requirements_id"]="a,b,c"
        ret=None
        requires = tms.get_requirements_data(ret, dat)
        self.assertEqual(requires,["a","b","c"])


        dat["tms_requirements_id"]=None
        ret = TmsResponse()
        ret.response=None
        requires = tms.get_requirements_data(ret, dat)
        self.assertEqual(requires,[])

        dat["tms_requirements_id"]=None
        ret=None
        requires = tms.get_requirements_data(ret, dat)
        self.assertEqual(requires,[])

