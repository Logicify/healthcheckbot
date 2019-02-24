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

import logging

import gc

from healthcheckbot import cli
from healthcheckbot.common.core import ApplicationManager

from healthcheckbot.common.bootstrap import bootstrap
from healthcheckbot.common.utils import CLI

logger = logging.getLogger('App')


def run_application(config: dict, application: ApplicationManager = None):
    if application is None:
        # Do bootstrap
        application = bootstrap(config)
    try:
        logger.info("Started main application loop")
        application.main_loop()
    except KeyboardInterrupt:
        application.shutdown()
        logger.info("Bye")
        exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        config = cli.read_config_from_arguments()
        gc.collect()
        run_application(config)
    except Exception as e:
        CLI.print_error(e)
        exit(1)
