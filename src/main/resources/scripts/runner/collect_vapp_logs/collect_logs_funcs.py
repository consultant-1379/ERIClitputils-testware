"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes
"""
import os
import shutil
import errno
import pexpect


def mkdir_parent(path):
    """
    Takes path of directory to create.
    Creates any parent directories, if needed.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def copy_file(source, dest):
    """
    Blah
    """
    try:
        shutil.copy(source, dest)
    except:
        print "File {0} does not exist.".format(source)


def copy_dir(source, dest):
    """
    Blah
    """
    try:
        shutil.copytree(source, dest)
    except:
        print "Directory {0} does not exist.".format(source)


def expect_cmd(command, password):
    """
    Bluh
    """
    print command
    child = pexpect.spawn(command)
    child.expect(["password:", pexpect.EOF])
    child.sendline(password)
    child.wait()
    child.expect(pexpect.EOF)
    # Print the output
    print child.before


def copy_file_bash(source, dest, directory=False):
    """
    NOT USED
    """
    # If a directory is to be copied, use recursive
    if directory:
        return "cp {0} {1} -r".format(source, dest)

    return "cp {0} {1}".format(source, dest)
