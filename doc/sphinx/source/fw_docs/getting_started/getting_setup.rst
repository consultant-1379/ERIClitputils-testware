.. _getting_started-label:

Test Environment Setup
===========================

Supported Operating System
----------------------------

The test framework has been designed to work on Scientific Linux Release 6. Although the framework should work in other Linux distributions, configuration steps may be different to those stated below.

As of 26/03/2019 the typical machine will be installed with CentOS7. The docs have been updated to reflect this.

Installing Git
-----------------

Check if git is installed:

.. code-block:: bash

    git --version

If git isn't installed, it can be installed following the steps here: http://git-scm.com/book/en/Getting-Started-Installing-Git .

It should be possible to perform the install using the following command in a console window:

.. code-block:: bash

    sudo yum install git

Setup your SSH Keys for Git
------------------------------

Once you have your XID, setup your SSH keys on https://gerrit.ericsson.se.

Create an SSH key:

.. code-block:: bash

    > ssh-keygen -t rsa -C "your_email@example.com"
    > xclip -sel clip < ~/.ssh/id_rsa.pub  # copies public key to clipboard


You may need to install xclip:

.. code-block:: bash

    sudo yum install xclip

Log onto Gerrit https://gerrit.ericsson.se/#/settings/ssh-keys and add your SSH key by pasting it in and hitting 'Add'.

Setup your gitconfig to match your credentials by creating a ~/.gitconfig file and put the following lines into it:

.. code-block:: bash

    [user]
        name = < REPLACE WITH YOUR USERNAME HERE >
        email = < REPLACE WITH YOUR EMAIL ACCOUNT >
    [core]
        autocrlf = false
        safecrlf = true

You should now be able to authenticate successfully when you make your first ``git clone``.

**Restart your computer** if you have issues cloning a repo after changing keys. The SSH service can get in a confused state or be caching the wrong key.

.. _getting_started_repo-label:

Clone Git Repositories to your Local Machine
-------------------------------------------------------

Firstly get the repo containing the utilities(utils/ERIClitputils-testware) to begin local testing.

Clone it to a directory e.g. /home/<USERNAME>/litprepos/

.. code-block:: bash

    [user@localhost ~]$ git clone ssh://<your_xid>@gerritmirror.lmera.ericsson.se:29418/LITP/ERIClitputils-testware

'<your_xid>': Your XID/ZID

Try **lower** and **upper** case if there are issues with this.

LITP is made up of lots of different LITP modules examples include: networking, vcs, core etc.

Each of these modules have their own repository containing Integration Tests(ITs).

They can be found here : `LITP/ERIClitp <https://gerrit.ericsson.se/#/admin/projects/?filter=LITP%252FERIClitp>`_

Below is an example of how to clone a repo(core/ERIClitpcore-testware) to your local machine.

.. code-block:: bash

    [user@localhost ~]$ git clone ssh://<your_xid>@gerritmirror.lmera.ericsson.se:29418/LITP/ERIClitpcore-testware

Ensuring pushing/pulling from correct repo

.. code-block:: bash

    git remote -v

More details can be found here:
`Continuous Integration(CI) Test Framework <https://confluence-nam.lmera.ericsson.se/display/ELITP/Continuous+Integration+Test+Framework>`_


Setting your Python Path
----------------------------

Python 2.7 should already be installed on your machine. If not please refer to "Installing Python" in the "Legacy" section below.

The system needs to know where to find all the utility functions and classes. This is done by updating PYTHONPATH to include 'ERIClitputils-testware/src/main/resources/scripts/utils'

To do this edit the ~/.bashrc file.

Use the below and edit it based on where ERIClitputils-testware has been cloned (step above).

.. code-block:: bash

    Example 1
    export PYTHONPATH="${PYTHONPATH}:/home/<USERNAME>/**litprepos**/ERIClitputils-testware/src/main/resources/scripts/utils"
    Example 2
    export PYTHONPATH="${PYTHONPATH}:/home/<USERNAME>/**git**/ERIClitputils-testware/src/main/resources/scripts/utils"


Install Pip
------------------

Pip is a utility to install Python packages.

Check if pip is installed:

.. code-block:: bash

   pip --version

If pip is not already installed, you can find install instructions at: https://pypi.python.org/pypi/pip

Installing Additional Python Packages
-------------------------------------

There are several Python packages which may not be installed by default which the framework requires.
These are: pexpect, paramiko, netaddr

All these packages can be installed with the pip utility as shown below.

**Note if using VirtualEnv you need to be in python 2.6.6 mode and should not use sudo**

.. code-block:: bash

    [user@localhost ~] sudo pip install pexpect
    [user@localhost ~] sudo pip install paramiko
    [user@localhost ~] sudo pip install netaddr

    ##If running in Virtualenv
    [user@localhost ~] pip install pexpect
    [user@localhost ~] pip install paramiko
    [user@localhost ~] pip install netaddr

Providing you are using the correct version of Python (2.6.6 as stated above), the default version pip installs will be compatible with the framework.

If you are on python 2.7 and are encountering issues with these packages, try installing the following specific versions.

.. code-block:: bash

    [user@localhost ~] sudo pip install pexpect==3.3
    [user@localhost ~] sudo pip install paramiko==1.12.0
    [user@localhost ~] sudo pip install netaddr==0.7.10

    ##If packages already installed use the upgrade flag
    [user@localhost ~] sudo pip install pexpect==3.3 --upgrade
    [user@localhost ~] sudo pip install paramiko==1.12.0 --upgrade
    [user@localhost ~] sudo pip install netaddr==0.7.10 --upgrade


.. _test-env-setup-label:

Code Checker Tools
--------------------

In the test framework, pylint and pep8 are used for checking that code quality meets Python standards and reduces risk of bad / broken code in the test environment. Ensure the following versions of both tools are installed:


Install Pylint
~~~~~~~~~~~~~~~~~

Install pylint version 1.1.0 and ensure it's installed correctly by checking its version.

.. code-block:: bash

    [user@localhost ~]$ sudo pip install pylint==1.1.0

.. code-block:: bash

    [user@localhost ~]$ pylint --version
    No config file found, using default configuration
    pylint 0.21.1,
    astng 0.20.1, common 0.50.3
    Python 2.6.6 (r266:84292, Jun 18 2012, 09:57:52)
    [GCC 4.4.6 20110731 (Red Hat 4.4.6-3)]
    
If pylint is already installed but is not version 1.1.0 use

.. code-block:: bash

    [user@localhost ~]$ sudo pip install pylint==1.1.0 --upgrade

If errors still exist, it may be because you need to upgrade other packages.

Install Astroid
~~~~~~~~~~~~~~~~~

Install astroid with version 1.2.1

.. code-block:: bash

    [user@localhost ~]$ sudo pip install astroid==1.2.1

If problems persist see the documentation here: https://pypi.python.org/pypi/pylint

Link to the Pylint Config File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests use some customised pylint rules which are defined in a configuration file.
This file is present in repo ERIClitputils-testware and rules are found under path 'ERIClitputils-testware/src/main/resources/scripts/pylint/pylintrc_test_2_1'

Run pylint using this file as shown in example below:

.. code-block:: bash

    [user@localhost ~]$pylint --rcfile=~/git/ERIClitputils-testware/src/main/resources/scripts/pylint/pylintrc_test_2_1 test_story100.py

However, it is advisable to set up an alias in your .bashrc file to save you having to type the above line each time, for example:

.. code-block:: bash

    alias pylint_test="pylint --rcfile=~/git/ERIClitputils-testware/src/main/resources/scripts/pylint/pylintrc_test_2_1"


Install Pep8
~~~~~~~~~~~~~~~~~

pep8 version should be set to 0.6.1. It may be necessary to downgrade if a later version is installed.

.. code-block:: bash

    > Use the below if you need to downgrade from a newer installed version
    [user@localhost ~]$ sudo pip install pep8==0.6.1 --upgrade
    > Use the below if you do not have pep8 installed
    [user@localhost ~]$ sudo pip install pep8==0.6.1

**This is the last required step.**
If you will need to run tests on your local machine you will have to follow the steps to install nosetests and set up VMs.





Setup the Desired Development Environment
------------------------------------------

Each developer/coder will like to use a specific tool to write code, you may use whichever is your preference whether listed here or not. The following are a number of examples of ones in use within the test community:

Vi / Vim
~~~~~~~~~~~~~~~~~

By default vi is installed on every Scientific Linux. vim can be downloaded to add colour and a few extra features not available in vi. To install vim, try the following:

.. code-block:: bash

    [user@localhost ~] sudo yum install vim

When this is installed you can configure your ~/.vimrc file to modify the settings of vi/vim to control the behaviour of vim when modifying a Python file, i.e. tabs, spaces, indenting...

.. The "*" below cannot be escaped so it causes the code to be highlighted, regardless of this it still successfully creates a sphinx document

.. code-block:: bash

    [user@localhost ~]$ cat ~/.vimrc
    autocmd BufNewFile,BufRead *.py set ts=4 | set shiftwidth=4 | set expandtab | set autoindent | set showmatch


Emacs
~~~~~~~~~~~~~~~~~

Install as shown below.

.. code-block:: bash

    [user@localhost ~]$ sudo yum install emacs

You can save the following Emacs config file as .emacs in your home directory which adds useful shortcuts and highlighting.

.. code-block:: bash

    (custom-set-variables
      ;; custom-set-variables was added by Custom.
      ;; If you edit it by hand, you could mess it up, so be careful.
      ;; Your init file should contain only one such instance.
      ;; If there is more than one, they won't work right.
     '(inhibit-startup-screen t))
    (custom-set-faces
      ;; custom-set-faces was added by Custom.
      ;; If you edit it by hand, you could mess it up, so be careful.
      ;; Your init file should contain only one such instance.
      ;; If there is more than one, they won't work right.
     )
    (global-linum-mode 1) ; display line numbers in margin. Emacs 23 only.
    (column-number-mode 1)

    (setq x-select-enable-clipboard t)
    (global-set-key (kbd "C-c") 'clipboard-kill-ring-save) ; CTRL+c - for copy
    (global-set-key (kbd "C-v") 'clipboard-yank) ; CTRL+v - for paste
    (global-set-key (kbd "C-r") 'clipboard-kill-region) ; CTRL+r - for cut
    (global-set-key (kbd "C-z") 'undo) ; CTRL+z - undo
    (global-set-key (kbd "C-2") 'split-window-horizontally) ; CTRL+2 - split vertically
    (global-set-key (kbd "C-1") 'delete-other-windows) ; CTRL+1 - kill other windows

    ; This splits my emacs window vertically when I open two files at once instead of horizontal
    (defun 2-windows-vertical-to-horizontal ()
      (let ((buffers (mapcar 'window-buffer (window-list))))
        (when (= 2 (length buffers))
          (delete-other-windows)
          (set-window-buffer (split-window-horizontally) (cadr buffers)))))
     (add-hook 'emacs-startup-hook '2-windows-vertical-to-horizontal)
     (setq frame-title-format
      '((buffer-file-name "%f")))
     ;Below causing hang?
    (require 'whitespace)
     (setq whitespace-style '(face empty tabs lines-tail trailing))
    (global-whitespace-mode t)


Gedit
~~~~~~~~~~~~~~~~~

This is installed by default on all Scientific Linux machines.

Eclipse
~~~~~~~~~~~~~~~~~

Eclipse Standard can be downloaded from: http://www.eclipse.org/downloads/

When installed go to "Help -> Install New Software" and add http://pydev.org/updates which will install the PyDev plugin needed for Eclipse.

Install Nosetests
~~~~~~~~~~~~~~~~~~~

Install nosetests with version 1.3.0:

.. code-block:: bash

    [user@localhost ~]$ sudo pip install nose==1.3.0

If nosetests is already installed with the wrong version uninstall and reinstall using the below commands:

.. code-block:: bash

    [user@localhost ~]$ sudo pip uninstall nose
    [user@localhost ~]$ sudo pip install nose==1.3.0


Setup your Connection Data Files
------------------------------------

All server connection information is defined in a single file. Create the file using the details below and create an environment variable which points to its location as shown below:

.. code-block:: bash

    export LITP_CONN_DATA_FILE="/home/david.appleton/host.properties"


NB: You can create the file anywhere on your machine, the above is just an example path.

Below are the example contents of the file:

**file - host.properties:**

.. code-block:: bash

       #Define my MS with hostname ms1
       host.ms1.type=MS
       host.ms1.ip=10.10.10.10
       #Define root user with password dummy1
       host.ms1.user.root.pass=dummy1
       #Define litp-admin user with password dummy2
       host.ms1.user.litp-admin.pass=dummy2
       host.ms1.port.ssh=22

       host.SC-1.ip=10.10.10.11
       host.SC-1.user.root.pass=dummy1
       host.SC-1.user.litp-admin.pass=dummy1
       host.SC-1.port.ssh=22
       host.SC-1.type=managed

       host.SC-2.ip=10.10.10.12
       host.SC-2.user.root.pass=dummy1
       host.SC-2.user.litp-admin.pass=dummy1
       host.SC-2.port.ssh=22
       host.SC-2.type=managed


When you create your file you will need to update all the fields (ip, passwords, hostnames) to match the machine (such as the VM) you are connecting to.

Note the following:

- The second part of each line is the hostname.
- You should define two users for each node, root and litp-admin, and ensure the passwords in the file match what is actually on your node.
- The type value should be either MS (management server), MN (managed node), SFS or NFS.

In the below example we define a management server with hostname hostname1:

.. code-block:: bash

       host.hostname1.type=MS
       host.hostname1.ip=10.10.10.10
       host.hostname1.user.root.pass=dummy1
       host.hostname1.user.litp-admin.pass=dummy2
       host.hostname1.port.ssh=22


**Note: Before running any tests make sure you have set your connection data files to point to the nodes in your test environment. You should never connect to an IP without permission to do so.**


Legacy Instructions
====================

The following instructions **are no longer used** but are being kept for legacy purposes


Install Python
---------------------

LITP and the test utilities are designed to run under python 2.6.6. This should be the installed version if running Scientific Linux:

.. code-block:: bash

    [user@localhost ~] python --version
    Python 2.6.6

**If running CENTOS 7** python 2.7 will be installed by default so you should look at setting up python 2.6.6 using VirtualEnv by following the below steps:

   1. Use yum to install the below packages

   .. code-block:: bash

      [user@localhost ~] sudo yum install python-devel openssl-devel zlib-devel sqlite-devel readline-devel ncurses-devel

   2. Download the tar.gz file of python 2.6.6 from here: https://www.python.org/download/releases/2.6.6/

   3. Extract the tarball using **tar -xvf #FILENAME#** and run the below commands from the extracted directory:

   .. code-block:: bash

      [user@localhost ~] ./configure
      [user@localhost ~] make
      [user@localhost ~] sudo make altinstall

   4. Install pip (see section below)

   5. Install virtualenv using the command **sudo pip install virtualenvwrapper**

   6. Add the following to your .bashrc file

   .. code-block:: bash

      export WORKON_HOME=$HOME/.virtualenvs
      source /usr/bin/virtualenvwrapper.sh


After this has been installed you will need to run the below command to start working in python 2.6:

   .. code-block:: bash

       [user@localhost ~] mkvirtualenv -p /usr/local/bin/python2.6 py26
       [user@localhost ~] workon py26


More details can be found here: http://docs.python-guide.org/en/latest/dev/virtualenvs/

**NB Do not try and change the native version of python in CENTOS 7 to python 2.6.6. This will break OS components** Instead VirtualEnv should be used as above.

Installing VMs
-----------------

In order to run your tests locally without the need of Ammeon hardware, it is required that you need to setup some virtual machines. This guide should get you started:

https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/content/sites/litp2/litp-training/latest/fw_docs/install_vm/installing_vm.html

Example Test to Verify Environment
-----------------------------------

When you have configured your VMs, you can download an example testfile :download:`here <testset_check_envir.py>`.

Run it with 'nosetests -s testset_check_envir.py'. If the test passes, it proves your connection data is set up correctly and all your configured nodes can be reached.
