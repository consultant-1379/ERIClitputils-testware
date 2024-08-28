Simple Framework Examples
===========================

Basic Method Structure
--------------------------

The below code illustrates the basic structure of a test story.

Note particularly:

- The syntax to inherit GenericTest in the test story.

- The calling of the parent tearDown and setUp methods.

- That all test functions must contain unit test style assertions.

- The classes should be named StoryXX where XX corresponds to the story number you are testing. We do not use the notation LITPCDS, as this can cause confusion as bugs and stories share this prefix.


**Example 1 = Framework Method Structure**

.. code-block:: python

    from litp_generic_test import GenericTest, attr

    class Story100(GenericTest):
        """The story string"""

        def setUp(self):
            """Run before every test"""
            super(Story100, self).setUp()
            #Set up some variables for our test

        def tearDown(self):
            """Run after every test"""
            #do some of our own cleanup actions
            super(Story100, self).tearDown()

        def method1(self, arg1, arg2):
            """Method description, actions, args and returns"""
            pass 
 
        @attr('all', 'example')
        def test_01_n_test_boolean(self):
            """Test case description"""
            self.assertTrue(False, "False is not True")


A more complete example, in two parts
----------------------------------------

Part one below shows example code from a real test with comments explaining the framework in more detail.

**Example 2 - Framework Code Use**

.. code-block:: python

    #Import Generic Test and the required area class
    from litp_generic_test import GenericTest, attr
    from rest_utils import RestUtils
 
    #Create a story class that inherits GenericTest
    class Story232(GenericTest):
        """Story string"""
 
        #Create a setup method. This is run at the beginning of every test.
        def setUp(self):
            #Call the generic test setup first
            super(Story232, self).setUp()
            #Get the ms name without hardcoding (eg 'ms1') using the helper function
            self.test_node = self.get_management_node_filename()
         
            #Init the required area classes
            self.ms_ip_address = self.get_node_att(self.test_node, 'ipv4')
            self.restutils = RestUtils(self.ms_ip_address)
            self.cli = CLIUtils()
 
        #Create a teardown method. This is run at the end of every test.
        def tearDown(self):
            #Call the generic test teardown
            super(Story232, self).tearDown()

        #Create methods to aid your tests, this will prevent code duplication
        def method1(self, arg1, arg2):
             #Try to use as many methods from GenericTest as possible
             pass
 
        @attr('all', 'example')
        def test_01_p_read_json_output(self):
            """
            Test case description
            """
            #Use the find command to get all node urls. Using find avoids hardcoding.
            node_url = self.find(self.test_node, "/deployments", "node", True)
 
            for item in node_url:
                #Use area class functions
                stdout, errors, status = self.restutils.get(item)
                self.assertEqual(200, status)
                self.assertEqual("", errors)
                self.assertNotEqual("", stdout)



The second part below shows a 'final version' with the level of comments expected for a TC.


**Example 3 - Final solution (with expected comments)**

.. code-block:: python

    from litp_generic_test import GenericTest, attr
    from rest_utils import RestUtils
    class Story232(GenericTest):
        '''
        As a REST Client developer I want to CRUD on execution manager so I can
        create, review and execute a plan through the REST API
        '''
 
        def setUp(self):
            """
            Description:
                Runs before every single test
            """
            super(Story232, self).setUp()
 
            self.test_node = self.get_management_node_filename()
            self.ms_ip_address = self.get_node_att(self.test_node, 'ipv4')
            self.restutils = RestUtils(self.ms_ip_address)
            self.cli = CLIUtils()
 
        def tearDown(self):
            """
            Description:
                Runs after every single test
            """
            super(Story232, self).tearDown()

        def method1(self, arg1, arg2):
            """
            Description:
                Short explanation of what the method does
            Actions:
                1. Only define actions for complex methods
            Args:
                arg1 (str): short description of arg1
 
                arg2 (list): short description of arg2
            Returns:
                item(type): description of returned item
            """
            pass
 
        @attr('all', 'example')
        def test_01_p_read_json_output(self):
            """
            Description: See section on test case description
            """
            self.log('info', '1. Perform find to get the litp path for all nodes')
            node_urls = self.find(self.test_node, "/deployments", "node")
  
            for node_url in node_urls:
                self.log('info', '2. Run a get on each node url.)
                stdout, errors, status = self.restutils.get(node_url)
 
                self.log('info', '3. Assert get succeeds without errors')
                self.assertEqual(200, status)
                self.assertEquals("", errors)
                self.assertNotEquals("", stdout)
