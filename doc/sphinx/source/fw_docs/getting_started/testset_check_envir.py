from litp_generic_test import GenericTest, attr


class Story100(GenericTest):
    """An example test to validate environment is set up as expected"""

    def setUp(self):
        """Run before every test"""
        super(Story100, self).setUp()

        #Get references to run commands on each node
        self.test_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()

    def tearDown(self):
        """Run after every test"""
        #do some of our own cleanup actions
        super(Story100, self).tearDown()

    @attr('all', 'example')
    def test_01_p_test_environ(self):
        """
        Description: See section on test case description standards

        Runs some simple tests fetching hostnames from
        nodes and checking it matches what is in the connection data
        file.

        If this test fails it indicates that the hostname is not set in
        the connection data file correctly or some connection issue exists
        with the environment. (check you can ping all nodes)
        """

        #Check MS hostname
        cmd_to_run = 'hostname'
        ms_hostname = self.get_node_att(self.test_node, 'hostname')
        stdout, stderr, returnc = self.run_command(self.test_node,
                                                       cmd_to_run)

        self.assertTrue(self.is_text_in_list(ms_hostname, stdout),
                        "MS is not setup correctly")
        self.assertEquals([], stderr)
        self.assertEquals(0, returnc)

        self.log("info", "MS Environment appears correct")

        ##Output warning if no nodes setup on environment
        if len(self.peer_nodes) == 0:
            self.log("warn",\
                         "You have no nodes configured in your" +
                     "connection data file")

        #Test hostname for each node
        for node in self.peer_nodes:
            node_hostname = self.get_node_att(node, 'hostname')
            stdout, stderr, returnc = self.run_command(node,
                                                           cmd_to_run)

            self.assertTrue(self.is_text_in_list(node_hostname, stdout),
                                "Node {0} is not setup correctly".format(node))
            self.assertEquals([], stderr)
            self.assertEquals(0, returnc)

            self.log("info", "Node {0} Environment appears correct"\
                         .format(node))
