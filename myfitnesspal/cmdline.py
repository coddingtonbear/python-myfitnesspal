import argparse
import logging
import sys


from .commands import COMMANDS, get_command_list


logger = logging.getLogger(__name__)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        epilog=get_command_list(),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'command',
        type=str,
        nargs=1,
        choices=COMMANDS.keys()
    )
    parser.add_argument(
        '--loglevel',
        type=str,
        default='INFO'
    )
    args, extra = parser.parse_known_args()

    # Set up a simple console logger
    logging.basicConfig(level=args.loglevel)
    logging.addLevelName(
        logging.WARNING,
        "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING)
    )
    logging.addLevelName(
        logging.ERROR,
        "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR)
    )

    try:
        if args.command[0] in COMMANDS:
            COMMANDS[args.command[0]]['function'](args, *extra)
    except Exception as e:
        logger.exception(e)
        raise
