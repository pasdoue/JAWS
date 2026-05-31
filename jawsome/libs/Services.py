from re import search as regex_search
from itertools import zip_longest
from typing import List, Optional

from R2Log import logger, console
from rich.emoji import Emoji

from jawsome.config.ToolConfig import Tool_Config


class Parameter:
    """
        Class to retrieve each potential parameter of the boto3 current function
        Will allow to use functions like describe_ / get_ and so on

        Also no types are returned from signature introspection... So we can just assume
    """
    def __init__(self, name: str, required: bool = False):
        self.name = name
        self.required = required

class Function:
    """
        A representation of a function avalaible in an AWS service
        for example : list-policies (inside iam service)
    """

    def __init__(self, name: str, parameters: List[Parameter], activated: bool = True):
        self.name = name
        self.activated = activated
        self.parameters = parameters

    def get_params(self, required_params_only: bool = False) -> List[str]:
        if not self.parameters:
            return []
        else:
            if required_params_only:
                return [p.name for p in self.parameters if p.required]
            else:
                return [p.name for p in self.parameters]

    def has_no_required_params(self) -> bool:
        if not self.parameters:
            return True
        if any([p.required for p in self.parameters]):
            return False
        return True

    def hash_ownerid_param(self) -> bool:
        return any([p.name == "OwnerIds" for p in self.parameters])



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

    def update_functions_stats(self) -> None:
        self.nb_functions = len(self.functions)
        self.nb_activated_functions = 0
        for f in self.functions:
            if f.activated:
                self.nb_activated_functions += 1
        self.nb_not_activated_functions = self.nb_functions - self.nb_activated_functions

    def get_functions(self, active_only: bool = True,
                      no_params_required: bool = False,
                      only_begin: Optional[List[str]] = None,
                      exclude_begin: Optional[List[str]] = None) -> List[Function]:
        """
            Return functions according to multiple possible criterias
            :param active_only: retrieve only active functions
            :param no_params_required: allow to retrieve function that do not require params
            :param only_begin: Filter result by giving a list of begin function pattern (ex: list_, get_...)
            :param exclude_begin: Same as above but exclude pattern
        """
        funcs = self.functions
        # Filter by activation
        if active_only:
            if no_params_required:
                funcs = [f for f in funcs if f.activated and f.has_no_required_params()]
            else:
                funcs = [f for f in funcs if f.activated]

        # Normalize patterns (lowercase once)
        only_begin = [p.lower() for p in only_begin] if only_begin else None
        exclude_begin = [p.lower() for p in exclude_begin] if exclude_begin else None

        # Apply whitelist (only_begin)
        if only_begin:
            if no_params_required:
                funcs = [ f for f in funcs if any(f.name.lower().startswith(p) for p in only_begin) and f.has_no_required_params() ]
            else:
                funcs = [f for f in funcs if any(f.name.lower().startswith(p) for p in only_begin)]

        # Apply blacklist (exclude_begin)
        if exclude_begin:
            if no_params_required:
                funcs = [ f for f in funcs if not any(f.name.lower().startswith(p) for p in exclude_begin) and f.has_no_required_params() ]
            else:
                funcs = [ f for f in funcs if not any(f.name.lower().startswith(p) for p in exclude_begin) ]
        return funcs

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

    def get_services_names(self, active_only: bool = True) -> Optional[List[str]]:
        """
            Return only list of services names
        """
        if active_only:
            return [service.name for service in self.get_services()] if len(self.get_services()) > 0 else None
        else:
            return [service.name for service in self.get_services(active_only=False)] if len(self.get_services(active_only=False)) > 0 else None

    def deactivate_service_function(self, service_name: str,
                                    search_type: str = "str",
                                    pattern: str="",
                                    is_substring: bool = False):
        """
            Function to deactivate specific(s) function(s) by pattern (can be strict / light comparison or regex)
            :param service_name: name of service to scan
            :param search_type: can be "str" or "regex"
            :param pattern: pattern to search
            :param is_substring: In case we are in "str" search, allow "light" comparison". If not set, strict comparison is performed
        """
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
                        if regex_search(pattern, function.name):
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
                    if any(function.name.startswith(safe_mode) for safe_mode in Tool_Config.SAFE_MODE):
                       function.activated = True
                    else:
                        function.activated = False
            service.update_functions_stats()


def print_services(services: Services) -> None:
    """
        Print services and their associated number of functions.
        Will display only selected services to estimate the number of calls to perform.
        (allow estimating if furtivity is in place or not)
    """
    call_to_perform = 0
    not_activated_function_in_activated_services = 0

    repr_array = []
    activated_services = services.get_services(active_only=True)
    all_services = services.get_services(active_only=False)

    total_api_calls = sum([len(service.get_functions(active_only=False)) for service in all_services])

    logger.info(f"{Emoji('hamster')} Every service are listed below with it's associated number of functions : ")
    for service in activated_services:
        functions_activated = service.get_functions(active_only=True)
        all_functions = service.get_functions(active_only=False)
        diff_functions = set(all_functions) - set(functions_activated)

        not_activated_function_in_activated_services += len(diff_functions)

        call_to_perform += len(functions_activated)
        repr_array.append((service.name, len(functions_activated)))

    PAIRS_PER_ROW = min(len(repr_array),5)  # change to 3, 4, etc.

    # compute column widths
    name_width = max(len(name) for name, _ in repr_array)
    num_width = max(len(str(num)) for _, num in repr_array)

    it = iter(repr_array)
    for group in zip_longest(*[it] * PAIRS_PER_ROW, fillvalue=("", "")):
        console.print("   ".join(
            f"{name:<{name_width}} [{num:>{num_width}}]"
            for name, num in group
        ), highlight=True)

    logger.info(f"Total number of activated services : [{len(activated_services)}/{len(all_services)}]")
    logger.info(f"Total number of call to perform : [{call_to_perform}/{total_api_calls}]")
    logger.info(f"Total number of functions avoided inside active service : {not_activated_function_in_activated_services}")
    if len(activated_services) == len(all_services):
        logger.warning(f"+------------------------------------------------------------------+")
        logger.warning(f"| /!\\    You're about to launch discovery on ALL services      /!\\ |")
        logger.warning(f"+------------------------------------------------------------------+")
