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

import sys
from typing import Callable, List

import os
import yaml

from healthcheckbot.common.core import ApplicationManager
from healthcheckbot.common.error import ConfigValidationError
from healthcheckbot.common.evaluator import simple_env_evaluator
from healthcheckbot.common.model import Module, WatcherModule
from healthcheckbot.common.utils import EvaluatingConfigWrapper

logger = logging.getLogger('Bootstrap')

__all__ = ['read_config', 'bootstrap', 'bootstrap_from_cli']


def read_config(config_file) -> dict:
    if isinstance(config_file, str):
        config_file = open(config_file, mode='r')
    try:
        return yaml.load(config_file)
    finally:
        if hasattr(config_file, 'close'):
            config_file.close()


def bootstrap(config: dict) -> ApplicationManager:
    application = bootstrap_environment(config)
    return bootstrap_from_cli(config, application)


def bootstrap_from_cli(config: dict, application: ApplicationManager) -> ApplicationManager:
    # Instantiate components
    instantiate_outputs(config, application)
    return application


def bootstrap_cli(config: dict) -> ApplicationManager:
    return bootstrap_environment(config, True)


def bootstrap_environment(config: dict, enable_cli=False) -> ApplicationManager:
    application = new_application()
    logger.info('Reading config file')
    config = add_expression_evaluator(config)
    save_instance_config(config, application)
    load_context_path(application)
    return application


def new_application(enable_cli=False):
    application = ApplicationManager()
    application.get_instance_settings().enable_cli = enable_cli
    return application


def add_expression_evaluator(config_section: dict) -> EvaluatingConfigWrapper:
    return EvaluatingConfigWrapper(config_section, simple_env_evaluator)


def save_instance_config(config: dict, application: ApplicationManager):
    if 'app' in config:
        app_config = add_expression_evaluator(config.get('app', {}))
        settings = application.get_instance_settings()
        settings.id = app_config.get('id', 'healthcheckbot0')
        # Context Path
        for path in app_config.get('classpath', []):
            if isinstance(path, str):
                if not os.path.exists(path):
                    raise ConfigValidationError('app/classpath', 'path ' + path + ' doesn\'t exist')
                settings.context_path.append(path)
            else:
                raise ConfigValidationError('app/classpath', 'Context path must be the list of strings')


def load_context_path(application: ApplicationManager):
    context_path = application.get_instance_settings().context_path
    for p in context_path:
        sys.path.append(p)


def instantiate_modules_for_section(section_name: str, section_config: dict, application: ApplicationManager,
                                    cb: Callable[[ApplicationManager, Module, dict], None] = None,
                                    instance_name_prefix='') -> List[Module]:
    result = []
    for name, module_def in section_config.items():
        if not (isinstance(module_def, dict) and 'provider' in module_def):
            raise ConfigValidationError('/'.join((section_name, name)),
                                        'Should be dictionary containing mandatory key "provider"')
        module_def = add_expression_evaluator(module_def)
        instance = application.register_module_instance(instance_name_prefix + name, module_def.get('provider'))
        try:
            # Parse and set parameters
            for param_def in instance.PARAMS:
                if param_def.name in module_def:
                    val = module_def.get(param_def.name)
                    if param_def.parser is not None:
                        val = param_def.parser.parse(val, application, '/'.join((section_name, name, param_def.name)))
                    val = param_def.sanitize(val)
                    param_def.validate(val)
                    setattr(instance, param_def.name, val)
                elif param_def.is_required:
                    raise ConfigValidationError('/'.join((section_name, name, param_def.name)),
                                                'Parameter {} is required'.format(param_def.name))
            # Run validation of the module device
            instance.validate()
            if cb is not None:
                cb(application, instance, module_def)
            instance.on_configured()
            logger.info('Configured module {}({}))'.format(name, instance.__class__.__name__))
            result.append(instance)
        except Exception as e:
            raise ConfigValidationError('/'.join((section_name, name)), "Invalid module configuration: " + str(e), e)
    return result


def _register_watcher_module(application: ApplicationManager, watcher: WatcherModule, module_def: dict):
    for trigger_name in module_def.get('triggers', tuple()):
        trigger = application.get_trigger_by_name(trigger_name)
        if trigger is None:
            raise ConfigValidationError('triggers', "Trigger \'{}\' doesn't exist".format(trigger_name))
        trigger.register_watcher(watcher)
    assertions = instantiate_modules_for_section('watchers/{}/custom_assertions'.format(watcher.name),
                                                 module_def.get('custom_assertions', dict()), application,
                                                 instance_name_prefix=watcher.name + '__')
    watcher.custom_assertions = assertions


def instantiate_outputs(config: dict, application: ApplicationManager):
    section_config = config.get('outputs', {})
    instantiate_modules_for_section('outputs', section_config, application)
    section_config = config.get('triggers', {})
    instantiate_modules_for_section('triggers', section_config, application)
    section_config = config.get('watchers', {})
    instantiate_modules_for_section('watchers', section_config, application, _register_watcher_module)
