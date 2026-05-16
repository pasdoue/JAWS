import importlib
import inspect
import json
import pkgutil
from enum import Enum
from pathlib import Path
from typing import List, Dict, Union, Any, Tuple, Optional

import pickle

from R2Log import logger

import boto3, botocore

from rich.emoji import Emoji

import meta_aws
from libs.Services import Services, Service, Function
from settings import Config


def get_unique_keys(obj, result=None):
    """
        Allow to retrieve all "keys" recursively in a JSON.
        Usefull for guessing parameters that are required
    """
    if result is None:
        result = set()

    if isinstance(obj, dict):
        for k, v in obj.items():
            result.add(k)
            get_unique_keys(v, result)

    elif isinstance(obj, list):
        for item in obj:
            get_unique_keys(item, result)

    return result

def find_parent(obj, target_key, parent=None):
    if isinstance(obj, dict):
        for key, value in obj.items():

            # clé trouvée -> retourner le parent
            if key == target_key:
                return parent

            # continuer récursivement
            result = find_parent(value, target_key, obj)
            if result is not None:
                return result

    elif isinstance(obj, list):
        for item in obj:
            result = find_parent(item, target_key, parent)
            if result is not None:
                return result

    return None


def search_adequate_module(module: str, method: str, arn: str, boto_func: Any) -> Optional[Any]:
    """
    Search for a specific method within a module within the meta_aws package.

    Args:
        module (str): The name of the AWS SDK service to check.
        method (str): The name of the method to execute within the service.
    """
    for _, module_name, _ in pkgutil.iter_modules(meta_aws.__path__):
        if module_name == module:
            loaded_module = importlib.import_module(f"{meta_aws.__name__}.{module_name}")
            for _, obj in inspect.getmembers(loaded_module, inspect.isclass):
                # ensure class is defined in this module (not imported)
                if obj.__name__ != "MetaAWS":
                    if hasattr(obj, method):
                        loaded_class = obj(arn=arn, boto_func=boto_func)
                        return getattr(loaded_class, method)()
    return None


class EntityTypeEnum(Enum):
    user = "user"
    role = "role"

class AWS_profile:

    def __init__(self, creds: Dict, metadata: bool = True) -> None:
        """
            Init object according to input settings
            :param kwargs: creds used
        """
        self.boto_session = boto3.session.Session(**creds)
        self.__safe_mode = True
        self.arn = self.boto_session.client('sts').get_caller_identity().get('Arn')
        self.entity_type, self.entity_name = self.get_entity_type_and_name(arn=self.arn)
        logger.success(f"Arn : {self.arn}\n"
                       f"Entity_type : {self.entity_type} {Emoji('boom')}{Emoji('sweat_drops')}\n"
                       f"Entity_name : {self.entity_name} {Emoji('speech_balloon')}")
        self.output_folder_name = AWS_profile.get_arn_safe_linux(arn=self.arn) # Get end of Arn which is human-readable and remove '/' inside
        self.services: Services = Services()
        self.metadata = metadata

        if self.services.FILE_MAP.exists():
            self.load_from_filemap()
        else:
            # avoid calling IAM role function if we are user and vice versa
            self.update_dynamically_services_functions()

    @staticmethod
    def get_entity_type_and_name(arn: str) -> Tuple[EntityTypeEnum, str]:
        if "assumed-role" in arn:
            entity_type = EntityTypeEnum.role
            entity_name = arn.split("/")[-2]
        else:
            entity_type = EntityTypeEnum.user
            entity_name = arn.split("/")[-1]
        return entity_type, entity_name

    @staticmethod
    def get_arn_safe_linux(arn: str) -> str:
        return arn.split(':')[-1].replace('/','_')

    def set_unsafe_mode(self):
        self.__safe_mode = False
        self.services.set_unsafe_mode()

    def launch_discovery(self, services: List[Service], progress, task_progress_ids):
        all_res = list()
        for service in services:
            try:
                client = self.boto_session.client(service.name)
            except botocore.exceptions.UnknownServiceError:
                progress.remove_task(task_progress_ids[service.name])
                continue
            if client is not None:
                service_rights = self.check_rights(service=service, session_obj=client, progress=progress, progress_id=task_progress_ids[service.name])
                all_res.append(service_rights)
        return all_res

    def check_rights(self, service: Service, session_obj: boto3.session.Session, progress, progress_id) -> dict:
        """
            Perform actual SDK call to AWS to check rights of calling
        """
        res = dict()
        res[service.name] = {}
        artifacts_only = {}

        #start collecting possible artifacts by interrogating endpoints without params needed
        for function in service.get_functions(active_only=True, no_params_required=True):
            if any(function.name.startswith(safe_mode) for safe_mode in Config.SAFE_MODE) and \
                    not any(function.name.startswith(billing) for billing in Config.BILLING_HEAVY_PREFIXES) and \
                    not any(pattern in function.name for pattern in Config.AVOID_PATTERN):
                service_function = getattr(session_obj, function.name)
                # check if the function is available in the current zone
                if service_function is None:
                    ret = "unavailable"
                else:
                    try:
                        ret = search_adequate_module(module=service.name, method=function.name, arn=self.arn, boto_func=service_function)
                        if ret is None:
                            if function.hash_ownerid_param():
                                ret = service_function(OwnerIds=["self"])
                            else:
                                ret = service_function()
                            if ret is not None:
                                logger.success(f"{service.name}:{function.name} is available")
                                if not self.metadata: AWS_profile.remove_response_metadata(resp=ret)
                                artifacts_only[service.name] = { function.name : ret }
                    except Exception as e:
                        ret = self._handle_boto_error(error=e)
                    if ret is None:
                        ret = "empty"
                res[service.name][function.name] = ret
                progress.update(progress_id, advance=1)

        unique_keys_artifacts = get_unique_keys(obj=artifacts_only)
        if artifacts_only == {}:
            #no items found so not possible to inject args ???
            logger.debug(f"No artifacts retrieved for {service.name}")
            progress.update(progress_id, advance=len([f for f in service.functions if f.activated and not f.has_no_required_params()]))
        else:
            # iterate a second round only for functions with params so we can try to inject some previous artifacts
            for function in [f for f in service.functions if f.activated and not f.has_no_required_params()]:
                if any(function.name.startswith(safe_mode) for safe_mode in Config.SAFE_MODE) and \
                        not any(function.name.startswith(billing) for billing in Config.BILLING_HEAVY_PREFIXES) and \
                        not any(pattern in function.name for pattern in Config.AVOID_PATTERN):
                    service_function = getattr(session_obj, function.name)
                    # check if the function is available in the current zone
                    if service_function is None:
                        res[service.name][function.name] = "unavailable"
                    else:
                        params_names = function.get_params(required_params_only=True)
                        if [uniq_key in params_names for uniq_key in unique_keys_artifacts].count(True) == len(params_names):
                            logger.success(f"All parameters are injectable for {service.name}:{function.name}({','.join(params_names)})")
                            res[service.name][function.name] = []
                            if len(params_names) == 1:
                                # simple case to handle has we have only one possibility
                                param_name = params_names[0]
                                possibilities = find_parent(obj=artifacts_only, target_key=param_name)
                                if isinstance(possibilities, dict):
                                    logger.info(f"Test injecting : {len(list(possibilities.values())[0])} possibilities")
                                    for p in list(possibilities.values())[0]:
                                        try:
                                            ret = search_adequate_module(module=service.name, method=function.name, arn=self.arn,
                                                                     boto_func=service_function)
                                            if ret is None:
                                                ret = service_function(**{param_name: p[param_name]})
                                                if ret is not None:
                                                    logger.success(f"{service.name}:{function.name} is available")
                                                    if not self.metadata: AWS_profile.remove_response_metadata(resp=ret)
                                        except Exception as e:
                                            ret = self._handle_boto_error(error=e)
                                        res[service.name][function.name].append({p[param_name]: ret})
                            else:
                                logger.warning(f"Not implemented for multiple args...")
                                res[service.name][function.name] = f"Not implemented for multiple args..."
                        else:
                            res[service.name][function.name] = f"Unable to guess all required params. Avoiding call."
                    progress.update(progress_id, advance=1)

        self.write_rights_to_file(service=service, res=res)
        progress.remove_task(progress_id)
        return res

    @staticmethod
    def _handle_boto_error(error: Exception) -> str :
        str_err = str(error)
        if any(x in str_err for x in ["UnauthorizedOperation", "AccessDenied", "ForbiddenException"]):
            return "Access Denied"
        elif "Missing required parameter" in str_err:
            return "Missing required parameter"
        elif "not available in this region" in str_err:
            return "Not available in this region." #TODO : maybe possible to check via boto functions ??
        else:
            return f"Unknown Exception : {str_err}"


    def write_rights_to_file(self, service: Service, res: dict):
        """
            Write to output file the result of batch
            :param service:
            :param res:
            :return:
        """
        output_folder = Path(__file__).parent / self.output_folder_name / self.boto_session.region_name
        output_file = output_folder / f"{service.name}.json"

        if not output_folder.exists():
            output_folder.mkdir(parents=True)

        output_file.write_text(json.dumps(res, indent=4, sort_keys=True, default=str))

    def update_dynamically_services_functions(self):
        """
            Retrieve boto3 available services and then retrieve all associated functions.
            Results are saved in a file.
        """
        logger.info("Updating dynamically list of AWS services and associated functions")
        # if we are user then remove IAM "role" calls, and vice versa
        iam_entity_to_remove = self.get_iam_entity_to_remove()

        available_services = self.boto_session.get_available_services()
        for service in available_services:
            curr_service = Service(name=service)
            try:
                boto_service: boto3.session.Session = self.boto_session.client(service_name=curr_service.name)
            except Exception as e:
                logger.error(f"Impossible to connect to AWS service : {service}\n{str(e)}")
                continue
            for function in dir(boto_service):
                if not function.startswith("_"):
                    # remove user or role API in IAM according to current entity type
                    if not (curr_service.name == "iam" and iam_entity_to_remove.value in function):
                        func = getattr(boto_service, function)
                        try:
                            func_doc = func.__doc__ if hasattr(func, "__doc__") else None
                            if func_doc is not None:
                                params = Function.parse_boto_docstring(docstr=str(func_doc))
                                curr_service.add_function(function=Function(name=function, activated=True, parameters=params))
                        except TypeError:
                            pass
            self.services.add_service(service=curr_service)

        self.save_to_filemap()
        logger.success("Update finished !")
        return

    def save_to_filemap(self, output_file: Path = None):
        out_file = output_file if output_file is not None else self.services.FILE_MAP
        if self.services is None:
            raise ValueError("Services are not provided")
        with open(out_file, 'wb') as f:
            #f.write(json.dumps(self.services, indent=4, sort_keys=True, default=str))
            pickle.dump(self.services, f, pickle.HIGHEST_PROTOCOL)
        logger.success(f"Successfully exported services to filemap : {out_file}")

    def load_from_filemap(self, output_file: Path = None):
        out_file = output_file if output_file is not None else self.services.FILE_MAP
        with out_file.open('rb') as f:
            self.services = pickle.load(f)

    ####################################################################################
    ###### Handling IAM specific routes (according to entity type : user or role)
    ####################################################################################

    @staticmethod
    def remove_response_metadata(resp: dict) -> None:
        """
            Every call to an endpoint generate metadata. 
            By default remove them as they have nothing interesting
        """
        if isinstance(resp, dict) and "ResponseMetadata" in resp.keys():
            resp.pop("ResponseMetadata")

    def iam_enum(self) -> dict:

        res = {}
        logger.info(f"Trying to gain some IAM information before brute force.")
        logger.info(f"Knowing that we are of type : {self.entity_type} {Emoji('sweat_drops')}")
        iam_client = self.boto_session.client("iam")

        res["get_account_authorization_details"] = self.iam_enum_get_account_authorization_details(iam_client=iam_client)

        if self.entity_type == EntityTypeEnum.user:
            res["get_user"] = self.iam_enum_get_user(iam_client=iam_client, metadata=self.metadata)
            res["list_attached_user_policies"] = self.iam_enum_list_attached_user_policies(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)
            res["list_user_policies"] = self.iam_enum_list_user_policies(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)
            res["list_groups_for_user"] = user_groups = self.iam_enum_list_groups_for_user(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)

            # verify that user_groups is dict so last call returned something and not an error
            if user_groups is not None and isinstance(user_groups, dict):
                self.iam_enum_list_group_policies(iam_client=iam_client, user_groups=user_groups)
        else:
            res["get_role"] = self.iam_enum_get_role(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)
            res["list_attached_role_policies"] = self.iam_enum_list_attached_role_policies(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)
            res["list_role_policies"] = self.iam_enum_list_role_policies(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)

        self._deactivate_iam_user_or_role()
        logger.success(f"IAM discovery finished {Emoji('popcorn')}")
        return res

    @staticmethod
    def iam_enum_get_account_authorization_details(iam_client, no_metadata: bool = False) -> str:
        try:
            everything = iam_client.get_account_authorization_details()
            logger.success(f"IAM get_account_authorization_details worked!")
            if no_metadata : AWS_profile.remove_response_metadata(resp=everything)
            #TODO: handle when size too big
            #logger.success(json.dumps(everything, indent=4, default=str))
            return everything
        except Exception as e:
            logger.error(f"Failed to interrogate IAM get_account_authorization_details() : \n{str(e)}")
            return str(e)

    def get_iam_entity_to_remove(self) -> EntityTypeEnum:
        """
            Return the entity type to remove from IAM to avoid unnecessary call
        """
        return EntityTypeEnum.user if self.entity_type == EntityTypeEnum.role else EntityTypeEnum.role

    def _deactivate_iam_user_or_role(self):
        """
            According to detected type for entity, we deactivate IAM functions for user if we are role and vice versa
        """
        entity_to_remove = self.get_iam_entity_to_remove()
        logger.info(f"Deactivating IAM functions for entity type : {entity_to_remove}")
        self.services.deactivate_service_function(service_name="iam",
                                                  search_type="str",
                                                  is_substring=True,
                                                  pattern=entity_to_remove.value)
        # As all calls are already performed before BF, exclude those functions for future BF
        self.services.deactivate_service_function(service_name="iam",
                                                  search_type="str",
                                                  is_substring=True,
                                                  pattern=self.entity_type.value)

    def write_iam_results_at_the_end(self, iam_results: dict):
        """
            As BF creates all files at the end, it will erase IAM scan of the beginning.
            So we handled the results and paste them after BF finished.
        """
        output_folder = Path(__file__).parent / self.output_folder_name / self.boto_session.region_name
        filename = output_folder / f"iam.json"

        if not output_folder.exists():
            output_folder.mkdir(parents=True)
        
        if not filename.exists():
            filename.write_text(json.dumps(iam_results, indent=4, sort_keys=True, default=str))
        else:
            with filename.open('r') as f:
                file_content = json.loads(f.read())
            for key in iam_results.keys():
                file_content["iam"][key] = iam_results[key]
            filename.write_text(json.dumps(file_content, indent=4, sort_keys=True, default=str))

    ##########################################
    ###### ROLE FUNCTIONS
    ##########################################
    @staticmethod
    def iam_enum_get_role(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            #TODO : find a role that can do this to test
            #TODO : Handle if response too long ???
            role = iam_client.get_role(RoleName=role_name)
            if not metadata : AWS_profile.remove_response_metadata(resp=role)
            logger.success(f"get_role() worked!")
            # logger.success(f"{json.dumps(role, indent=4, default=str)}")
            return role
        except Exception as e:
            logger.error(f"Failed to interrogate IAM get_role() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_attached_role_policies(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            # TODO : find a role that can do this to test
            role_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            if not metadata : AWS_profile.remove_response_metadata(resp=role_policies)
            for policy in role_policies["AttachedPolicies"]:
                logger.success(f"Policy Name & ARN [{policy['PolicyName']}] : {policy['PolicyArn']}")
            return role_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_attached_role_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_role_policies(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            role_policies = iam_client.list_role_policies(RoleName=role_name)
            if not metadata : AWS_profile.remove_response_metadata(resp=role_policies)
            logger.success(f"IAM list_role_policies worked!")
            logger.info(f"Role {role_name} has {len(role_policies['PolicyNames'])} inline policies")
            # List all policies, if present.
            for policy in role_policies['PolicyNames']:
                logger.success(f"Policy : {policy}")
            return role_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_role_policies() : \n{str(e)}")
            return str(e)

    ##########################################
    ###### USER FUNCTIONS
    ##########################################
    @staticmethod
    def iam_enum_get_user(iam_client, metadata: bool = False) -> Union[str, dict]:
        try:
            user = iam_client.get_user()
            if not metadata : AWS_profile.remove_response_metadata(resp=user)
            logger.success(f"IAM get_user worked!")
            logger.success(json.dumps(user, indent=4, default=str))
            if 'UserName' not in user['User']:
                if user['User']['Arn'].endswith(':root'):
                    logger.success(f"Found root credentials {Emoji('1st_place_medal')}! \n{user['User']['Arn']}")
                else:
                    logger.error("Unexpected iam.get_user() response: %s" % user)
            # else: return user['User']['UserName']
            return user
        except Exception as e:
            logger.error(f"Failed to interrogate IAM get_user() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_attached_user_policies(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_policies = iam_client.list_attached_user_policies(UserName=username)
            if not metadata : AWS_profile.remove_response_metadata(resp=user_policies)
            logger.success(f"IAM list_attached_user_policies worked!")
            logger.info(f"User {username} has {len(user_policies['AttachedPolicies'])} policies")
            for policy in user_policies['AttachedPolicies']:
                logger.success(f"Policy Name & ARN : {policy['PolicyName']} [{policy['PolicyArn']}]")
            return user_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_attached_user_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_user_policies(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_policies = iam_client.list_user_policies(UserName=username)
            if not metadata : AWS_profile.remove_response_metadata(resp=user_policies)
            logger.success(f"IAM list_user_policies worked!")
            logger.info(f"User {username} has {len(user_policies['PolicyNames'])} inline policies")
            # List all policies, if present.
            for policy in user_policies['PolicyNames']:
                logger.success(f"Policy : {policy}")
            return user_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_user_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_groups_for_user(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_groups = iam_client.list_groups_for_user(UserName=username)
            if not metadata : AWS_profile.remove_response_metadata(resp=user_groups)
            logger.success(f"IAM list_groups_for_user worked!")
            logger.info(f"User {username} has {len(user_groups['Groups'])} groups associated")
            return user_groups
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_groups_for_user() : \n{str(e)}")
            return str(e)

    @staticmethod
    def iam_enum_list_group_policies(iam_client, user_groups: dict, metadata: bool = False) -> dict:
        res = {}
        for group in user_groups['Groups']:
            group_name = group['GroupName']
            try:
                group_policies = iam_client.list_group_policies(GroupName=group_name)
                if not metadata : AWS_profile.remove_response_metadata(resp=group_policies)
                logger.success(f"IAM Group {group_name} has {len(group_policies['PolicyNames'])} inline policies : ")
                for policy in group_policies['PolicyNames']:
                    logger.info(f"---> {policy}")
                res[group_name] = group_policies
            except Exception as e:
                logger.error(f"Failed to interrogate IAM list_group_policies() : \n{str(e)}")
                res[group_name] = str(e)
        return res
