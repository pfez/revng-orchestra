import os

from loguru import logger

from . import SubCommandParser
from ..model.configuration import Configuration
from ..model.install_metadata import load_file_list, is_installed


def install_subcommand(sub_argparser: SubCommandParser):
    cmd_parser = sub_argparser.add_subcmd(
        "inspect",
        help="Inspect orchestra status",
    )
    install_config_subcommand(cmd_parser)
    install_component_subcommand(cmd_parser)


def install_config_subcommand(sub_argparser: SubCommandParser):
    sub_argparser.add_subcmd(
        "config",
        handler=handle_config,
        help="Dump yaml configuration generated by ytt",
    )


def install_component_subcommand(sub_argparser: SubCommandParser):
    component_parser = sub_argparser.add_subcmd(
        "component",
        help="Inspect component status",
    )
    all_subparsers = set()

    installed_files_parser = component_parser.add_subcmd(
        "installed-files",
        handler=handle_installed_files,
        help="List installed files",
    )
    all_subparsers.add(installed_files_parser)

    hash_material_parser = component_parser.add_subcmd(
        "hash-material",
        handler=handle_hash_material,
        help="Print material used for computing recursive hash",
    )
    all_subparsers.add(hash_material_parser)

    # Add component parameter to all subcmds
    for subparser in all_subparsers:
        subparser.add_argument("component", help="Name of the component to act on")


def handle_installed_files(args):
    config = Configuration(use_config_cache=args.config_cache)
    build = config.get_build(args.component)

    if build is None:
        suggested_component_name = config.get_suggested_component_name(args.component)
        logger.error(f"Component {args.component} not found! Did you mean {suggested_component_name}?")
        return 1

    if not is_installed(config, build.component.name):
        logger.error(f"Component {args.component} is not installed")
        return 2

    file_list = load_file_list(build.component.name, config)
    for f in file_list:
        print(f)

    return 0


def handle_hash_material(args):
    config = Configuration(use_config_cache=args.config_cache)
    build = config.get_build(args.component)

    if build is None:
        suggested_component_name = config.get_suggested_component_name(args.component)
        logger.error(f"Component {args.component} not found! Did you mean {suggested_component_name}?")
        return 1

    print(build.component.recursive_hash_material())

    return 0


def handle_config(args):
    config = Configuration(use_config_cache=args.config_cache)
    with open(os.path.join(config.orchestra_dotdir, "config_cache.yml")) as f:
        print(f.read())

    return 0
