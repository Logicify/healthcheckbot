#!/usr/bin/env python3

#    Healthcheck Bot
#    Copyright (C) 2018 Dmitry Berezovsky
#    
#    HealthcheckBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    HealthcheckBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging

import gc
import os

from healthcheckbot import app
from healthcheckbot.common import bootstrap
from healthcheckbot.common.model import CliExtension
from healthcheckbot.common.utils import CLI

DEFAULT_CONFIG_LOCATIONS = [
    './config.yaml',
    './config.yml',
]

supplementary_parser = argparse.ArgumentParser(add_help=False)
supplementary_parser.add_argument("-c", "--config", dest='config', type=argparse.FileType('r'), required=False,
                                  help="File containing HealthcheckBot configuration in yaml or JSON format")
supplementary_parser.add_argument("-v", "--verbose", dest="verbose", action='store_true', required=False,
                                  help="If set more verbose output will used",
                                  default=False)

parser = argparse.ArgumentParser(prog='healthcheckbot', add_help=True,
                                 description='Advanced health and status checks for your software',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
--------------------------------------------------------------
Healthcheck Bot Copyright (C) 2019 Dmitry Berezovsky
This program comes with ABSOLUTELY NO WARRANTY;
This is free software, and you are welcome to redistribute it
under certain conditions;
--------------------------------------------------------------
"""
                                 )

parser.add_argument("-c", "--config", dest='config', type=argparse.FileType('r'), required=False,
                    help="File containing HealthcheckBot configuration in yaml or JSON format")

parser.add_argument("-v", "--verbose", dest="verbose", action='store_true', required=False,
                    help="If set more verbose output will used",
                    default=False)

module_parser = parser.add_subparsers(title="module",
                                      dest="module",
                                      description='Use \"<MODULE_NAME> -h\" to get information '
                                                  'about command available for particular module')

_config = None
namespace_parsers = {}


class ApplicationRunCLIExtension(CliExtension):
    COMMAND_NAME = 'run'
    COMMAND_DESCRIPTION = 'Run Healthcheck Bot in foreground'

    def handle(self, args):
        global _config
        bootstrapped_app = bootstrap.bootstrap_from_cli(_config, self.get_application_manager())
        app.run_application(_config, bootstrapped_app)


class VerifyConfigCLIExtension(CliExtension):
    COMMAND_NAME = 'verify'
    COMMAND_DESCRIPTION = 'Verify configuration file end exit'

    def handle(self, args):
        global _config
        try:
            bootstrapped_app = bootstrap.bootstrap_from_cli(_config, self.get_application_manager())
            CLI.print_info("Config file is valid")
        except Exception as e:
            CLI.print_error("Config file is invalid")
            CLI.print_error(e)
            exit(1)


def get_default_config_path():
    for config_path in DEFAULT_CONFIG_LOCATIONS:
        if os.path.isfile(config_path):
            return config_path
    return None


def read_config_from_arguments() -> dict:
    known, unknown = supplementary_parser.parse_known_args()
    CLI.verbose_mode = known.verbose
    if known.config is None:
        config_path = get_default_config_path()
    else:
        config_path = known.config.name
        known.config.close()
    if config_path:
        CLI.print_info("Loaded config: " + os.path.realpath(config_path))
        CLI.print_info("")
        return bootstrap.read_config(config_path)
    else:
        CLI.print_error('Unable to load config file. Check -c/--config option.')
        exit(1)


def configure_subparser_for_cli_extension(ext, parser, application):
    ext.setup_parser(parser)
    ext_instance = ext(parser, application)
    parser.set_defaults(handler=ext_instance)


def main():
    global _config
    logging.basicConfig(level=logging.DEBUG)
    _config = read_config_from_arguments()
    application = bootstrap.bootstrap_cli(_config)
    # Register root commands
    root_commands = (ApplicationRunCLIExtension, VerifyConfigCLIExtension)
    # Process root commands
    for cmd in root_commands:
        cmd_subparser = module_parser.add_parser(cmd.COMMAND_NAME, help=cmd.COMMAND_DESCRIPTION)
        configure_subparser_for_cli_extension(cmd, cmd_subparser, application)

    # Process CLI extensions
    for namespace, ext in application.cli_extensions:
        if namespace not in namespace_parsers.keys():
            p = module_parser.add_parser(namespace)
            namespace_parsers[namespace] = p.add_subparsers(title='module_cmd', dest='module_cmd')
        ext_parser = namespace_parsers[namespace]
        if ext.COMMAND_NAME is None:
            raise Exception(
                "Invalid CLI Extension: {}. COMMAND_NAME needs to be defined".format(ext.__class__.__name__))
        ext_subparser = ext_parser.add_parser(ext.COMMAND_NAME,
                                              help=ext.COMMAND_DESCRIPTION)
        configure_subparser_for_cli_extension(ext, ext_subparser, application)

    args = parser.parse_args()
    gc.collect()
    if hasattr(args, "handler"):
        args.handler.handle(args)


if __name__ == '__main__':
    main()
