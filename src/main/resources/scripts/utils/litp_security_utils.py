"""
LITP Security Utils
"""
import re


class SecurityUtils(object):
    """
    Security related utilities.
    """

    def __init__(self):
        """Initialise LITP path variables.
        """
        self.litp_crypt = "/usr/bin/litpcrypt"

    def get_litpcrypt_set_cmd(self, service, user, password):
        """
        Creates a litpcrypt set command.

        Args:
           service  (str): The name of the service to set password on.

           user     (str): The username to access the service.

           password (str): The username password to encrypt.

        Returns:
           str. A litpcrypt set command.
        """
        cmd = "{0} set {1} {2} {3}".format(self.litp_crypt,
                                           service, user, password)

        return cmd

    def get_litpcrypt_delete_cmd(self, service, user):
        """
        Creates a litpcrypt delete command.

        Args:
           service  (str): The name of the service to remove user from.

           user     (str): The username to remove from the shadow file.

        Returns:
           str. Litpcrypt delete command.
        """
        cmd = "{0} delete {1} {2}".format(self.litp_crypt, service, user)

        return cmd

    @staticmethod
    def get_litpshadow_dict(shadow_file_contents):
        """
        Loads the contents of the litpshadow file into a dict.

        Args:
           shadow_file_contents (list): The shadow file contents as a list.
              NB: This can be generated from calling get_file_contents.

        Return:
           dict. Shadow file contents with service names as keys and
           the list of allowed users for that service values.
        """
        shadow_file_dict = dict()
        current_key = None

        for line in shadow_file_contents:
            if re.match(r"\[(.+?)\]", line):
                # Remove surrounding square brackets
                service_name = line.replace("[", "").replace("]", "").strip()

                current_key = service_name
                shadow_file_dict[current_key] = list()
            elif "=" in line:
                # Extract username for the service
                shadow_file_dict[current_key].\
                    append(line.split("=")[0].strip())

        return shadow_file_dict
