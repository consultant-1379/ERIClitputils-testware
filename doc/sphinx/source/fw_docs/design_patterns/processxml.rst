.. _xmlprocess-env-label:

Processing XML in the IT Test Framework
============================================

Any part of the LITP tree can be exported or imported using XML format. The framework provides some basic methods for manipulating XML data as is shown in the below example.


Manipulating XML in Tests
-------------------------------------------

In the below code example, we export from the tree to XML, modify it, load it back into LITP and then assert the expected changes have occurred in the model.

**Manipulating XML**

.. code-block:: python

    from xml_utils import XMLUtils
    from litp_generic_test import GenericTest, attr

    class Story100(GenericTest):

       def setUp():
           self.xml_utils = XMLUtils()
           self.ms_node = self.get_management_node_filename()

        def test_01_p_check_xml(self):
            ##1. Using the find method we get the node path and backup it props
            node_path = self.find(self.ms_node, "/deployments", "node")[0]
            self.backup_path_props(self.ms_node, node_path)

            ##2. As we have not specified a file calling the export command will output the xml to stdout
            stdout, _, _ = self.execute_cli_export_cmd(self.test_node, node_path)

            ##3. Using the xml utilities we can load the xml to an object
            xml_object = self.xml_utils.load_xml_dataobject(stdout)

            ##4. We will now loop through the item properties and update the hostname property
            new_hostname = "nodestory100"
            hostname_found = False
            for child in xml_object:
                if child.tag == 'hostname':
                    child.text = new_hostname
                    hostname_found = True
                    break

            ##5. Assert we have found the hostname
            self.assertTrue(hostname_found, "Hostname was not found")

            ##6. Convert the object back to XML
            xml_string = self.xml_utils.output_xml_dataobject(xml_object)

            ##7. Output to a xml file on the ms
            filename = "/tmp/test1.xml"
            self.assertTrue(self.create_file_on_node(self.ms_node, filename, xml_string.split("\n")), "Output to {0} was unsuccessful".format(filename))

            ##8. Load the edited XML file back into the model
            parent_path = self.get_parent_path(node_path)
            self.execute_cli_load_cmd(self.ms_node, parent_path, filename, "--replace")

            ##9. Assert model is updated with changed hostname
            self.assertEqual(new_hostname, self.get_props_from_url(self.ms_node, node_path, 'hostname'))


The XML utilities make use of the Python etree library. More details and examples of processing XML data within this object type can be found here:

http://lxml.de/tutorial.html
