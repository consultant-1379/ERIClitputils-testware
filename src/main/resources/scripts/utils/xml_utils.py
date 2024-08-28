"""
XML pp Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""

from lxml import etree


class XMLUtils(object):
    """
    XML command related utilities.
    """

    def __init__(self):
        """
        Initialise LITP path variables.
        """
        self.xmllint_path = "/usr/bin/xmllint"

    def get_validate_xml_file_cmd(self, filepath):
        """Returns an xmllint command which reports success (exit code 0)
        if run on a file with valid xml. xmllint is installed on Red Hat
        as a default package.

        Args:
            filepath (str): The filepath of the XML file to test.

        Returns:
            str. An xmllint cmd.
        """
        return "{0} {1}".format(self.xmllint_path, filepath)

    @staticmethod
    def load_xml_dataobject(xml_data):
        """
        Loads the passed XML data to an XML element tree.

        Args:
            xml_data (list): The contents of an XML file as a list. This list\
                can be generated by calling the get_file_contents method.

        Returns:
            xml.etree. Tree representing the XML object.
        """
        ##1. Convert to string and parse.

        tree = etree.fromstring("\n".join(xml_data))

        return tree

    @staticmethod
    def output_xml_dataobject(xml_data):
        """
        Converts the passed element tree object to XML data.

        Args:
            xml_data (elementtree): An XML tree object created from\
                calling load_xml_dataobject.

        Returns:
            str. The dataobject converted to XML.
        """
        xmlstr = etree.tostring(xml_data, encoding='utf-8')

        return xmlstr
