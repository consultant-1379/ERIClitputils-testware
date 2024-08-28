# Copy update_peer_password.py (this script) to /opt/ericsson/enminst/lib
# cd /opt/ericsson/enminst/lib
# python update_peer_password.py

from argparse import ArgumentParser
from base64 import decodestring
import pexpect

from h_litp.litp_rest_client import LitpRestClient

INFRA_SYSTEMS = '/infrastructure/systems'
SSH = '/usr/bin/ssh -oStrictHostKeyChecking=no {0}@{1}'
TIMEOUT = 4


def _get_sys_names():
    litp = LitpRestClient()
    items = litp.get_children(INFRA_SYSTEMS)
    sys_list = []
    for item in items:
        if item['path'].split('/')[3] != 'management_server':
            sys_name = item['data']['properties']['system_name']
            sys_list.append(sys_name)
    return sys_list


def _update_litp_password(systems, old_pass='cGFzc3cwcmQ=\n',
                          new_pass='MTJzaHJvb3Q=\n'):
    print '\n>>> Update default litp-admin password >>>'
    for system in systems:
        try:
            print '-------------------------------'
            ssh = SSH.format('litp-admin', system)
            px = pexpect.spawn(ssh)
            px.expect('password:')
            px.sendline(decodestring(old_pass))
            rc = px.expect(['Permission denied',
                            '\(current\) UNIX password:',
                           '\[litp-admin@.+\]\$'], TIMEOUT)
            if rc == 0:
                print 'Cannot login to {0} with litp-admin and default ' \
                    'password. Permission denied'.format(system)
                continue
            if rc == 2:
                print 'The default litp-admin password on {0} is current ' \
                      'password'.format(system)
                px.sendline('exit')
                px.expect('closed', TIMEOUT)
                continue
            print 'Changing the default litp-admin password on {0}'.format(
                system)
            px.sendline(decodestring(old_pass))
            px.expect('New password:', TIMEOUT)
            px.sendline(decodestring(new_pass))
            px.expect('Retype new password:', TIMEOUT)
            px.sendline(decodestring(new_pass))
            px.expect('passwd: all authentication tokens updated successfully',
                      TIMEOUT)
            print 'Password successfully changed for litp-admin on {0}'.format(
                system)
        except pexpect.TIMEOUT:
            print 'Password NOT changed for litp-admin on {0}'.format(system)
            print 'Possible reason:'
            print px.before
            print px.after
        except pexpect.EOF:
            print 'Password NOT changed for litp-admin on {0}'.format(system)
            print 'Possible reason:'
            print px.before
            print px.after


def _update_root_password(systems, old_pass='bGl0cGMwYjZsRXI=\n',
                          new_pass='MTJzaHJvb3Q=\n'):
    print '\n>>> Update default root password >>>'
    for system in systems:
        try:
            print '-------------------------------'
            ssh = SSH.format('litp-admin', system)
            px = pexpect.spawn(ssh)
            px.expect('password:')
            px.sendline(decodestring(new_pass))
            px.expect('\[litp-admin@.+\]\$', TIMEOUT)
            print 'Changing the default root password on {0}'.format(system)
            px.sendline('su -')
            px.expect('Password:', TIMEOUT)
            px.sendline(decodestring(old_pass))
            rc = px.expect(['su: incorrect password',
                            '\(current\) UNIX password:',
                           '\[root@.+\]\#'], TIMEOUT)
            if rc == 0:
                print 'The default root password on {0} is incorrect or ' \
                        'already updated'.format(system)
                continue
            if rc == 2:
                print 'The default root password on {0} is current ' \
                    'password'.format(system)
                px.sendline('exit')
                px.expect('logout', TIMEOUT)
                continue
            px.sendline(decodestring(old_pass))
            px.expect('New password:', TIMEOUT)
            px.sendline(decodestring(new_pass))
            px.expect('Retype new password:', TIMEOUT)
            px.sendline(decodestring(new_pass))
            px.expect('\[root@.+\]\#', TIMEOUT)
            print 'Password successfully changed for root on {0}'.format(
                system)
        except pexpect.TIMEOUT:
            print 'Password NOT changed for root on {0}'.format(system)
            print 'Possible reason:'
            print px.before
            print px.after
        except pexpect.EOF:
            print 'Password NOT changed for root on {0}'.format(system)
            print 'Possible reason:'
            print px.before
            print px.after


def main():
    parser = ArgumentParser(description='Script to update litp-admin and '
                            'root default passwords on the peer nodes')
    parser.add_argument('-s', required=False,
                        help='Single system or list of systems separated by '
                             'comma. No space allowed between names. Default '
                             'value is list of all systems.')
    args = parser.parse_args()
    if args.s:
        systems = [system.strip() for system in args.s.split(',')]
        _update_litp_password(systems)
        _update_root_password(systems)
    else:
        systems = _get_sys_names()
        _update_litp_password(systems)
        _update_root_password(systems)

if __name__ == '__main__':
    main()
