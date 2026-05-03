import re
from typing import List, Union

from settings import Config


class Function:
    """
        A representation of a function avalaible in an AWS service
        for example : list-policies (inside iam service)
    """

    def __init__(self, name: str, activated: bool = True):
        self.name = name
        self.activated = activated


class Service:
    """
        A representation of an AWS services (iam, ssm...)
    """

    def __init__(self, name: str, functions: List[Function] = None, activated: bool = True) -> None:
        self.name = name
        self.functions = list() if functions is None else functions
        self.activated = activated
        self.nb_functions = 0
        self.nb_activated_functions = 0
        self.nb_not_activated_functions = 0

    def add_function(self, function: Function):
        self.functions.append(function)

    def update_stats(self) -> None:
        self.nb_functions = len(self.functions)
        self.nb_activated_functions = 0
        for f in self.functions:
            if f.activated:
                self.nb_activated_functions += 1
        self.nb_not_activated_functions = self.nb_functions - self.nb_activated_functions

    def get_functions(self, active_only: bool = True) -> List[Function]:
        """
            Return only functions that are activated
        """
        if active_only:
            return [function for function in self.functions if function.activated]
        else:
            return [function for function in self.functions]


class Services:

    def __init__(self, safe_mode: bool = True) -> None:
        self.safe_mode = safe_mode # by default is True to avoid wrong behaviors
        self.__whitelist: List[str] = []
        self.__blacklist: List[str] = []
        self.nb_services = 0
        self.nb_activated_services = 0
        self.services: List[Service] = list()

    def set_unsafe_mode(self):
        self.safe_mode = False

    def add_service(self, service: Service):
        self.services.append(service)

    def get_services(self, active_only: bool = True) -> List[Service]:
        if active_only:
            return [service for service in self.services if service.activated]
        else:
            return [service for service in self.services]

    def get_services_names(self, active_only: bool = True) -> Union[None|List[str]]:
        """
            Return only list of services names
        """
        if active_only:
            return [service.name for service in self.get_services()] if len(self.get_services()) > 0 else None
        else:
            return [service.name for service in self.get_services(active_only=False)] if len(self.get_services(active_only=False)) > 0 else None

    def deactivate_service_function(self, service_name: str, search_type: str = "str", pattern="", is_substring: bool = False):
        for service in self.get_services(active_only=True):
            if service.name == service_name:
                for function in service.get_functions(active_only=True):
                    if search_type == "str":
                        if is_substring:
                            if pattern in function.name:
                                function.activated = False
                                self.nb_activated_services -= 1
                        else:
                            if pattern == function.name:
                                function.activated = False
                                self.nb_activated_services -= 1

                    elif search_type == "regex":
                        if re.search(pattern, function.name):
                            function.activated = False
                            self.nb_activated_services -= 1

    def calculate_white_and_black_list(self, white_list: List[str], black_list: List[str]):
        """
            Return list of AWS services to bruteforce first including white list if exists and then always exclude black list.
            :param white_list: list of services to scan
            :param black_list: list of services to avoid
        """
        self.__blacklist = black_list
        self.__whitelist = white_list
        self.nb_services = len(self.services)

        if isinstance(self.__blacklist, str):
            self.__blacklist = self.__blacklist.strip().split(",")
        if isinstance(self.__whitelist, str):
            self.__whitelist = self.__whitelist.strip().split(",")

        for service in self.services:
            if self.__whitelist:
                service.activated = True if service.name in self.__whitelist else False
            if self.__blacklist:
                service.activated = False if service.name in self.__blacklist else service.activated

            if service.activated:
                self.nb_activated_services += 1

    def calculate_safe_mode(self):
        """
            Deactivate some functions if we are in safe mode.
        """
        if not self.safe_mode:
            return
        for service in self.services:
            if service.activated:
                for function in service.functions:
                    if any(function.name.startswith(safe_mode) for safe_mode in Config.SAFE_MODE):
                       function.activated = True
                    else:
                        function.activated = False
            service.update_stats()
