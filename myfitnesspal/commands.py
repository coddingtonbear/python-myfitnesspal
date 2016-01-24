import argparse
from getpass import getpass
import logging

from .keyring_utils import (
    delete_password_in_keyring,
    store_password_in_keyring,
)


COMMANDS = {}

logger = logging.getLogger(__name__)


def get_command_list():
    command_lines = []
    for name, info in COMMANDS.items():
        if info['is_alias']:
            continue
        message = "{0}: {1}".format(name, info['description'])
        if info['aliases']:
            message = message + '; aliases: {0}'.format(
                ', '.join(info['aliases'])
            )
        command_lines.append(message)
    prolog = 'available commands:\n'
    return prolog + '\n'.join(['  ' + cmd for cmd in command_lines])


def command(desc, name=None, aliases=None):
    if aliases is None:
        aliases = []

    def decorator(fn):
        main_name = name if name else fn.__name__
        command_details = {
            'function': fn,
            'description': desc,
            'is_alias': False,
            'aliases': [],
        }

        COMMANDS[main_name] = command_details
        for alias in aliases:
            COMMANDS[alias] = command_details.copy()
            COMMANDS[alias]['is_alias'] = True
            COMMANDS[main_name]['aliases'].append(alias)
        return fn
    return decorator


@command(
    "Store a MyFitnessPal password in your system keychain.",
    aliases=['store-password'],
)
def store_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'username',
        help='The MyFitnessPal username for which to store this password.'
    )
    args = parser.parse_args(extra)

    password = getpass(
        "MyFitnessPal Password for {username}: ".format(
            username=args.username
        )
    )

    store_password_in_keyring(args.username, password)


@command(
    "Delete a MyFitnessPal password from your system keychain.",
    aliases=['delete-password'],
)
def delete_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'username',
        help='The MyFitnessPal username for which to delete a stored password.'
    )
    args = parser.parse_args(extra)

    delete_password_in_keyring(args.username)
