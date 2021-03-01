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
import time
from typing import List, Tuple, Type, NamedTuple, Dict

from healthcheckbot.common.error import InvalidModuleError, WatcherRuntimeError, OutputRuntimeError
from healthcheckbot.common.model import CliExtension, Module, TriggerModule, OutputModule, WatcherModule, \
    ValidationReporter, WatcherResult, LoopModuleMixin, WatcherAssert


class ModuleType(NamedTuple):
    bucket: dict
    name: str
    base_class: Type


class InstanceSettings:
    def __init__(self):
        self.id = None
        self.enable_cli = False
        self.context_path = []


class ApplicationManager:

    def __init__(self) -> None:
        self.__instance_settings = InstanceSettings()
        self.__terminating = False
        self.cli_extensions = []  # type: List[Tuple[str, CliExtension]]
        self.__logger = logging.getLogger('ApplicationManager')
        self.__triggers = {}  # type: Dict[TriggerModule]
        self.__outputs = {}  # type: Dict[OutputModule]
        self.__watchers = {}  # type: Dict[WatcherModule]
        self.__watcher_asserts = {}  # type: Dict[WatcherAssert]
        self.__main_loop = []  # type: List[LoopModuleMixin]

    def __module_by_class_or_class_name(self, class_name):
        if isinstance(class_name, str):
            try:
                module_name, class_name = class_name.rsplit('.', 1)
                module = __import__(module_name, globals(), locals(), [class_name], 0)
                clazz = getattr(module, class_name)
            except ImportError as e:
                raise InvalidModuleError("Class doesn't exist: " + str(class_name), e)
            except AttributeError as e:
                raise InvalidModuleError("Class doesn't exist: " + str(class_name), e)
        else:
            clazz = class_name
        # Validations
        assert clazz is not None, "module instance shouldn't be None"
        if not issubclass(clazz, Module):
            raise InvalidModuleError('Module must implement healthcheckbot.common.model.Module class')
        return clazz

    def __bucket_for_module_instance(self, clazz: Type) -> ModuleType:
        if issubclass(clazz, TriggerModule):
            return ModuleType(self.__triggers, 'trigger', TriggerModule)
        elif issubclass(clazz, OutputModule):
            return ModuleType(self.__outputs, 'output', OutputModule)
        elif issubclass(clazz, WatcherModule):
            return ModuleType(self.__watchers, 'watcher', WatcherModule)
        elif issubclass(clazz, WatcherAssert):
            return ModuleType(self.__watcher_asserts, 'assert', WatcherAssert)
        else:
            raise InvalidModuleError('Unknown module type: ' + clazz.__name__)

    def get_trigger_by_name(self, name) -> TriggerModule:
        return self.__triggers.get(name)

    def get_output_by_name(self, name):
        return self.__triggers.get(name)

    def register_module_instance(self, instance_name, class_name) -> Module:
        try:
            module_class = self.__module_by_class_or_class_name(class_name)
            module_type = self.__bucket_for_module_instance(module_class)
            module_inst = module_class(self)
            try:
                module_inst.on_initialized()
            except Exception as e:
                raise InvalidModuleError("Error during initialization", e)
            module_type.bucket[instance_name] = module_inst
            self.__logger.info(
                'Instantiated {} "{}"({})'.format(module_type.name, instance_name, module_class.__name__))
            if isinstance(module_inst, LoopModuleMixin):
                self.__main_loop.append(module_inst)
                self.__logger.info(
                    'Module "{}"({}) registered in application loop'.format(instance_name, module_class.__name__))
            module_inst.name = instance_name
            return module_inst
        except InvalidModuleError as e:
            raise InvalidModuleError('Unable to register module {}: '.format(class_name) + e.message, e)

    def get_instance_settings(self) -> InstanceSettings:
        return self.__instance_settings

    def main_loop(self):
        while not self.__terminating:
            for module in self.__main_loop:
                try:
                    module.step()
                except Exception as e:
                    self.__logger.error("Error in during main loop execution: " + str(e))
            time.sleep(0.01)

    def run_watcher(self, watcher: WatcherModule, trigger: TriggerModule) -> WatcherResult:
        reporter = ValidationReporter(watcher, trigger)
        try:
            state = watcher.obtain_state(trigger)
        except Exception as e:
            raise WatcherRuntimeError(
                'Watcher "{}" was unable to finish obtain state cycle: {}'.format(watcher.name, str(e)), e)
        if watcher.enable_assertions:
            try:
                watcher.do_assertions(state, reporter)
                for assertion in watcher.custom_assertions:
                    try:
                        assertion.do_assert(state, reporter, assertion.name)
                    except Exception as e:
                        reporter.error(assertion.name, 'Unexpected error: ' + str(e))

            except Exception as e:
                raise WatcherRuntimeError(
                    'Watcher "{}" was unable to run assertions check: {}'.format(watcher.name, str(e)), e)
        try:
            serialized_state = watcher.serialize_state(state)
            watcher_result = WatcherResult(serialized_state, reporter.errors, reporter.extra_data)
        except Exception as e:
            raise WatcherRuntimeError(
                'Watcher "{}" was unable serialize state: {}'.format(watcher.name, str(e)), e)
        self.deliver_watcher_result(watcher, watcher_result)
        return watcher_result

    def deliver_watcher_result(self, watcher: WatcherModule, watcher_result: WatcherResult):
        for output_name, output in self.__outputs.items():
            try:
                output.output(watcher, watcher_result)
            except Exception as e:
                raise OutputRuntimeError(
                    'Unable to deliver watcher result via output "{}": {}'.format(output.name, str(e)), e)

    def shutdown(self):
        self.__logger.info("Initiating shutdown process")
        self.__terminating = True
        for bucket in (self.__watchers, self.__triggers, self.__outputs, self.__watcher_asserts):
            for name, module in bucket.items():
                try:
                    module.on_before_destroyed()
                    del module
                except Exception as e:
                    self.__logger.error(
                        "Error while destroying module {}({}): {}".format(name, module.__class__.__name__, e))
        self.__logger.info("Destroyed modules")
