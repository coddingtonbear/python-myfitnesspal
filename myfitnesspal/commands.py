import argparse
import logging
from datetime import datetime
from getpass import getpass
from typing import Dict

from dateutil.parser import parse as dateparse
from rich import print

from . import Client
from .keyring_utils import (
    delete_password_in_keyring,
    get_password_from_keyring_or_interactive,
    store_password_in_keyring,
)
from .types import CommandDefinition

COMMANDS: Dict[str, CommandDefinition] = {}

logger = logging.getLogger(__name__)


def get_command_list():
    command_lines = []
    for name, info in COMMANDS.items():
        if info["is_alias"]:
            continue
        message = "{}: {}".format(name, info["description"])
        if info["aliases"]:
            message = message + "; aliases: {}".format(", ".join(info["aliases"]))
        command_lines.append(message)
    prolog = "available commands:\n"
    return prolog + "\n".join(["  " + cmd for cmd in command_lines])


def command(desc, name=None, aliases=None):
    if aliases is None:
        aliases = []

    def decorator(fn):
        main_name = name if name else fn.__name__
        command_details: CommandDefinition = {
            "function": fn,
            "description": desc,
            "is_alias": False,
            "aliases": [],
        }

        COMMANDS[main_name] = command_details
        for alias in aliases:
            COMMANDS[alias] = command_details.copy()
            COMMANDS[alias]["is_alias"] = True
            COMMANDS[main_name]["aliases"].append(alias)
        return fn

    return decorator


@command(
    "Store a MyFitnessPal password in your system keychain.",
    aliases=["store-password"],
)
def store_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "username", help="The MyFitnessPal username for which to store this password."
    )
    args = parser.parse_args(extra)

    password = getpass(f"MyFitnessPal Password for {args.username}: ")

    store_password_in_keyring(args.username, password)


@command(
    "Delete a MyFitnessPal password from your system keychain.",
    aliases=["delete-password"],
)
def delete_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "username",
        help="The MyFitnessPal username for which to delete a stored password.",
    )
    args = parser.parse_args(extra)

    delete_password_in_keyring(args.username)


@command(
    "Display MyFitnessPal data for a given date.",
)
def day(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "username",
        help="The MyFitnessPal username for which to delete a stored password.",
    )
    parser.add_argument(
        "date",
        nargs="?",
        default=datetime.now().strftime("%Y-%m-%d"),
        type=lambda datestr: dateparse(datestr).date(),
        help="The date for which to display information.",
    )
    args = parser.parse_args(extra)

    password = get_password_from_keyring_or_interactive(args.username)
    client = Client(args.username, password)
    day = client.get_date(args.date)

    date_str = args.date.strftime("%Y-%m-%d")
    print(f"[blue]{date_str}[/blue]")
    for meal in day.meals:
        print(f"[bold]{meal.name.title()}[/bold]")
        for entry in meal.entries:
            print(f"* {entry.name}")
            print(
                f"  [italic bright_black]{entry.nutrition_information}"
                f"[/italic bright_black]"
            )
        print("")

    print("[bold]Totals[/bold]")
    for key, value in day.totals.items():
        print(
            "{key}: {value}".format(
                key=key.title(),
                value=value,
            )
        )
    print(f"Water: {day.water}")
    if day.notes:
        print(f"[italic]{day.notes}[/italic]")
