"""
JSON Utils

Note: :synopsis: for this file is located in source_code_docs.rst
"""

import json
from litp_generic_utils import GenericUtils
import traceback


class JSONUtils(object):
    """JSON related utilities.
    """

    def __init__(self):
        """Initialise LITP path variables.
        """
        self.gen_utils = GenericUtils()

    def load_json(self, json_data):
        """Attempts to load the passed string into JSON.

        Args:
            json_data (str): The JSON data to load.

        Returns:
            The data parsed to JSON or None if the JSON.loads fails.
        """
        # If structure is a list, we need to convert to text before loading.
        if isinstance(json_data, list):
            json_data = "".join(json_data)

        try:
            return json.loads(json_data)

        except Exception, exp:
            traceback.print_exc()
            self.gen_utils.log("error", "JSON is corrupt {0}".format(exp))
            return None

    def dump_json(self, json_data):
        """
        Attempts to dump the passed string into JSON format. This allows for
        strings formatted in unicode to a format that can be loaded by JSON.

        Args:
            json_data (str): The JSON data to load.

        Returns:
            The data converted to JSON friendly format or None if
            conversion fails.
        """
        # If structure is a list, we need to convert to text before loading
        if isinstance(json_data, list):
            json_data = "".join(json_data)

        try:
            return json.dumps(json_data)

        except Exception, exp:
            traceback.print_exc()
            self.gen_utils.log("error", "JSON is corrupt {0}".format(exp))
            return None

    def is_json_hal_complient(self, json_output, has_children, has_props):
        """Performs a simple HAL compliant test.

        Args:
            json_output (list): The output from running a JSON command.

            has_children (bool): Set to True if JSON item should have child
                            paths. If True, method asserts for embedded key.

            has_props (bool): Set to True if JSON item should have
                            properties. If True, asserts for properties key.

        Checks the following HAL rules:

        a) _links is in the top level with a self href.
        b) If has_children is set, _embedded key exists in the top level.
        c) If has_props is set, the properties key exists in the top level.
        d) If there are children and properties, check
            properties are not within embedded.
        e) If there are no children, embedded tag should not exist.
        f) If has_props is not set, the properties are not the top level.

        Returns:
            bool. True if structure is compliant or False otherwise.
        """
        json_element = json_output

        # If structure is a list, we need to convert to string
        if isinstance(json_element, list):
            # 1. Convert object to string
            json_element = "".join(json_output)

        json_element = self.gen_utils.load_json(json_element)

        expected_top_level_keys = ['_links']

        if has_children:
            expected_top_level_keys.append('_embedded')

        if has_props:
            expected_top_level_keys.append('properties')

        # a) _links is in the top level with a self href
        # b) If has_children is set, _embedded key exists in the top level
        # c) If has_props is set, the properties key exists in the top level

        if not set(expected_top_level_keys).issubset(set(json_element.keys())):
            return False

        # a) _links is in the top level with a self href
        if not 'self' in json_element['_links'].keys():
            return False

        if not 'href' in json_element['_links']['self'].keys():
            return False

        # d) If there are children and properties, check properties not within
        #       embedded top level
        if has_props and has_children:
            if 'properties' in json_element['_embedded']:
                return False

        # e) If there are no children, embedded tag should not exist
        if not has_children:
            if '_embedded' in json_element.keys():
                return False

        # f) If has_props is not set the properties are not the top level
        if not has_props:
            if 'properties' in json_element.keys():
                return False

        return True
