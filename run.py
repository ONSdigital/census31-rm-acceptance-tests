import argparse
import logging

from behave import __main__ as behave_executable

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_BEHAVE_FORMAT = 'pretty'
DEFAULT_FEATURE_DIRECTORY = 'acceptance_tests/features'


def parse_arguments():
    """
    Parses commandline arguments
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser('Run behave scenarios')
    parser.add_argument('--log_level', '-l', help='Logging level', default=DEFAULT_LOG_LEVEL)
    parser.add_argument('--format', '-f', help='Behave format', default=DEFAULT_BEHAVE_FORMAT)
    parser.add_argument('--feature_directory', '-fd', help='Feature directory', default=DEFAULT_FEATURE_DIRECTORY)
    parser.add_argument('--tags', '-t', help='Tags')
    parser.add_argument('--show_skipped', help='Show skipped tests', action='store_true')

    return parser.parse_args()


def main():
    """
    Runner
    """
    args = parse_arguments()

    logging.basicConfig(level=args.log_level)

    show_skipped = '--show-skipped' if args.show_skipped else '--no-skipped'

    tags_arg = parse_tags(args.tags)

    args = f'--logging-level {args.log_level} --format {args.format} {args.feature_directory} {tags_arg} {show_skipped}'

    return behave_executable.main(args)


# --tags=~@tag1,~@tag2 doesn't work.  Needs to be --tags @tag1 --tags ~@tag2
def parse_tags(tags_arg):
    new_tag_arg = ''

    if tags_arg is None:
        return new_tag_arg

    for tag in tags_arg.split(","):
        new_tag_arg += f' --tags {tag}'

    print(new_tag_arg)
    return new_tag_arg


if __name__ == '__main__':
    exit(main())
