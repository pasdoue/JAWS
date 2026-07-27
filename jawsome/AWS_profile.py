import asyncio
import importlib
import inspect
import json
import pkgutil
import re
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Union, Any, Tuple, Optional, List

from R2Log import logger, console
from rich.emoji import Emoji
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from aiobotocore.session import get_session, AioSession

from jawsome import meta_aws
from jawsome.libs.Services import Services, Service, Function, Parameter
from jawsome.config.ToolConfig import Tool_Config
from jawsome.utils import print_elapsed_time, get_unique_keys, find_parent

reg_boto_shitty_async = re.compile("|".join(["EC2", "PHI", "SNOMEDCT", "HIT", "MFA", "ID", "ACLS", "ACL", "WhatsApp", "OTel"]))
reg_boto_services1 = re.compile(r'([A-Z]+)([A-Z][a-z])')
reg_boto_services2 = re.compile(r'([a-z0-9])([A-Z])')

async def search_adequate_module(module: str, method: str, arn: str, boto_func: Any) -> Optional[Any]:
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
                        ret = await getattr(loaded_class, method)()
                        return ret
    return None


class EntityTypeEnum(Enum):
    user = "user"
    role = "role"

class AWS_profile:

    def __init__(self, creds: Dict, metadata: bool = True, output_dir: Path = Path.cwd()) -> None:
        """
            Init object according to input settings
            :param kwargs: creds used
        """
        self.boto_session: AioSession = get_session()
        self.__safe_mode = True
        self.__creds = creds
        self.__profile_name = creds["profile_name"]
        self.__creds.pop("profile_name") #create error on client init of aiobotocore if present
        self.arn = ""
        self.entity_type, self.entity_name = None, None
        self.output_dir = Path(output_dir).expanduser() # custom user output dir (from args)
        self.output_folder_name = "" # will be under output_dir and calculated according to ARN retrieved
        self.services: Services = Services()
        self.metadata = metadata

        if not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.critical(f"Unknwon error while creating output dir. Exiting script. Error details : {str(e)}")


    def get_region(self):
        return self.__creds["region_name"]

    async def init_class(self) -> None:
        """
            Performs async calls to boto and set all attributes from class.
            As __init__() function cannot be async
        """
        async with self.boto_session.create_client('sts', **self.__creds) as session:
            res = await session.get_caller_identity()
            logger.info(f"UserId : {res.get('UserId')}")
            logger.info(f"Account : {res.get('Account')}")
            self.arn = res.get('Arn')

        self.entity_type, self.entity_name = self.get_entity_type_and_name(arn=self.arn)
        logger.success(f"Arn : {self.arn}\n"
                       f"Entity_type : {self.entity_type} {Emoji('boom')}{Emoji('sweat_drops')}\n"
                       f"Entity_name : {self.entity_name} {Emoji('speech_balloon')}")
        self.output_folder_name = AWS_profile.get_arn_safe_linux(arn=self.arn)  # Get end of Arn which is human-readable and remove '/' inside

        await self.update_dynamically_services()

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

    ####################################################################################
    ###### Calling boto functions to see which ones responds
    ####################################################################################

    def set_unsafe_mode(self):
        self.__safe_mode = False
        self.services.set_unsafe_mode()

    async def launch_discovery(self, service: Service, progress, task_progress_ids):
        all_res = list()
        async with self.boto_session.create_client(service.name, **self.__creds) as client:
            service_rights = await self.check_rights(service=service, session_obj=client, progress=progress, progress_id=task_progress_ids[service.name])
            all_res.append(service_rights)
        return all_res

    @staticmethod
    def remove_functions_additional_filters(functions: List[Function]) -> List[Function]:
        res = []
        for function in functions:
            if any(function.name.startswith(safe_mode) for safe_mode in Tool_Config.SAFE_MODE) and \
                    not any(function.name.startswith(billing) for billing in Tool_Config.BILLING_HEAVY_PREFIXES) and \
                    not any(pattern in function.name for pattern in Tool_Config.AVOID_PATTERN):
                res.append(function)
        return res

    async def check_rights(self, service: Service, session_obj, progress, progress_id) -> dict:
        """
            Perform actual SDK call to AWS to check rights of calling
        """
        res = dict()
        res[service.name] = {}
        artifacts_only = {}

        func_with_no_params = service.get_functions(active_only=True, no_params_required=True)
        func_with_no_params = AWS_profile.remove_functions_additional_filters(func_with_no_params)

        progress.update(progress_id, total=len(func_with_no_params))
        #start collecting possible artifacts by interrogating endpoints without params needed
        for function in func_with_no_params:
            service_function = getattr(session_obj, function.name)
            # check if the function is available in the current zone
            if service_function is None:
                ret = "unavailable"
            else:
                try:
                    ret = await search_adequate_module(module=service.name, method=function.name, arn=self.arn, boto_func=service_function)
                    if ret is None:
                        if function.hash_ownerid_param():
                            ret = await service_function(OwnerIds=["self"])
                        else:
                            ret = await service_function()
                        if not self._handle_boto_error(ret, check=True):
                            logger.success(f"{service.name}:{function.name} is available")
                            if not self.metadata:
                                AWS_profile.remove_response_metadata(resp=ret)
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
        else:
            func_with_params = [f for f in service.functions if f.activated and not f.has_no_required_params()]
            func_with_params = AWS_profile.remove_functions_additional_filters(func_with_params)
            progress.update(progress_id, total=len(func_with_params))
            # iterate a second round only for functions with params so we can try to inject some previous artifacts
            for function in func_with_params:
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
                                        ret = await search_adequate_module(module=service.name, method=function.name, arn=self.arn,
                                                                 boto_func=service_function)
                                        if ret is None:
                                            ret = await service_function(**{param_name: p[param_name]})
                                            if not self._handle_boto_error(ret, check=True):
                                                logger.success(f"{service.name}:{function.name} is available")
                                                if not self.metadata:
                                                    AWS_profile.remove_response_metadata(resp=ret)
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
    def _handle_boto_error(error: Union[Exception|str], check=False) -> Union[str|bool] :
        str_err = str(error)
        final_error = ""
        if any(x in str_err for x in ["UnauthorizedOperation", "AccessDenied", "ForbiddenException"]):
            final_error = f"Access Denied."
        #should not happened but stay there even if normally handled
        elif "Missing required parameter" in str_err:
            final_error = "Missing required parameter"
        elif "MissingParameter" in str_err:
            final_error = f"Multiple optional parameters but required : {str_err.split(':')[-1]}"
        elif "not available in this region" in str_err:
            final_error = "Not available in this region." #TODO : maybe possible to check via boto functions ??

        if check:
            return True if final_error else False
        else:
            if not final_error:
                return f"Unknown Exception : {str_err}"
            else:
                return final_error

    def write_rights_to_file(self, service: Service, res: dict) -> None:
        """
            Write to output file the result of batch
            :param service:
            :param res:
            :return:
        """
        output_folder = self.output_dir / self.output_folder_name / self.get_region()
        output_file = output_folder / f"{service.name}.json"

        if not output_folder.exists():
            output_folder.mkdir(parents=True)

        output_file.write_text(json.dumps(res, indent=4, sort_keys=True, default=str))

    ####################################################################################
    ###### Dynamic updates of boto services & functions & params
    ####################################################################################

    async def update_dynamically_services(self) -> None:
        """
            Retrieve boto3 available services and then retrieve all associated functions.
            Results are saved in a pickl export file to load fast on next run.
        """
        start = time.time()
        logger.info(f"Updating list of boto3 services and associated functions! Be patient, can take a while {Emoji('pray')}")
        #iam_entity_to_remove = self.get_iam_entity_to_remove()
        available_services = self.boto_session.get_available_services()
        logger.info(f"Scanning {len(available_services)} services {Emoji('eyes')}")

        with Progress(
                SpinnerColumn(),
                "[bold blue]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TextColumn("[cyan]{task.completed}/{task.total}"),
                transient=True,
                refresh_per_second=2,
                console=console
        ) as progress:
            task_progress_ids = {
                "Boto_services": progress.add_task(f"[green]Processing boto3 Services local mapping...", total=len(available_services))
            }
            tasks = [
                asyncio.create_task(self.__update_dynamically_services_functions(s_name, task_progress_ids, progress))
                for s_name in available_services
            ]
            await asyncio.gather(*tasks)

            progress.remove_task(task_progress_ids["Boto_services"])

        logger.success("Update finished !")
        print_elapsed_time(start_time=start)
        return

    @staticmethod
    def __convert_async_boto_obj_to_boto(input_param: str) -> str:
        """
            As aiobotocore stores functions and params names, we can parse it to scan boto lib
            BUT aiobotocore stores functions & params in uppercase where boto in lower... :face_palm: again
        """
        input_param = reg_boto_shitty_async.sub(lambda m: "_"+m.group(0).lower(), input_param)
        input_param = reg_boto_services1.sub(r'\1_\2', input_param)
        input_param = reg_boto_services2.sub(r'\1_\2', input_param)
        return input_param.lower()

    async def __update_dynamically_services_functions(self, service_name: str, task_progress_ids, progress) -> None:
        """
            As parsing function.__doc__ of boto is not asyncio compliant.
            Changed strategy of dumping boto functions and dump aiobotocore instead of boto.
            But all function are in upper case... Really annoying shit but should be well handled (tested on almost every endpoints)
        """
        curr_service = Service(name=service_name)
        s_obj = await self.boto_session.get_service_model(service_name)

        boto_functions = [function for function in s_obj.operation_names]
        boto_functions_lower = [self.__convert_async_boto_obj_to_boto(input_param=function) for function in boto_functions]
        for i in range(len(boto_functions)):
            function = boto_functions[i]
            params = []
            try:
                if s_obj.operation_model(function).input_shape is not None:
                    str_params = list(s_obj.operation_model(function).input_shape.members.keys())
                    for p in str_params:
                        is_required = False
                        if p in s_obj.operation_model(function).input_shape.required_members:
                            is_required = True
                        params.append(Parameter(name=p, required=is_required))
                curr_service.add_function(function=Function(name=boto_functions_lower[i], activated=True, parameters=params))
            except Exception as e:
                logger.error(f"Unknown error occurred while parsing : {service_name}.{function}() :\n{str(e)}")
                continue
        progress.update(task_progress_ids["Boto_services"], advance=1)

        self.services.add_service(service=curr_service)

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

    async def iam_enum(self) -> dict:

        res = {}
        logger.info(f"Trying to gain some IAM information before brute force.")
        logger.info(f"Knowing that we are of type : {self.entity_type} {Emoji('sweat_drops')}")
        async with self.boto_session.create_client("iam", **self.__creds) as iam_client:
            res["get_account_authorization_details"] = await self.iam_enum_get_account_authorization_details(iam_client=iam_client)

            if self.entity_type == EntityTypeEnum.user:
                res["get_user"] = await self.iam_enum_get_user(iam_client=iam_client, metadata=self.metadata)
                res["list_attached_user_policies"] = await self.iam_enum_list_attached_user_policies(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)
                res["list_user_policies"] = await self.iam_enum_list_user_policies(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)
                res["list_groups_for_user"] = user_groups = await self.iam_enum_list_groups_for_user(iam_client=iam_client, username=self.entity_name, metadata=self.metadata)

                # verify that user_groups is dict so last call returned something and not an error
                if user_groups is not None and isinstance(user_groups, dict):
                    await self.iam_enum_list_group_policies(iam_client=iam_client, user_groups=user_groups)
            else:
                res["get_role"] = await self.iam_enum_get_role(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)
                res["list_attached_role_policies"] = await self.iam_enum_list_attached_role_policies(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)
                res["list_role_policies"] = await self.iam_enum_list_role_policies(iam_client=iam_client, role_name=self.entity_name, metadata=self.metadata)

            self._deactivate_iam_user_or_role()
            logger.success(f"IAM discovery finished {Emoji('popcorn')}")
        return res

    @staticmethod
    async def iam_enum_get_account_authorization_details(iam_client, no_metadata: bool = False) -> str:
        try:
            everything = await iam_client.get_account_authorization_details()
            logger.success(f"IAM get_account_authorization_details worked!")
            if no_metadata :
                AWS_profile.remove_response_metadata(resp=everything)
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

    def _deactivate_iam_user_or_role(self) -> None:
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

    def write_iam_results_at_the_end(self, iam_results: dict) -> None:
        """
            As BF creates all files at the end, it will erase IAM scan of the beginning.
            So we handled the results and paste them after BF finished.
        """
        if not iam_results:
            return
        output_folder = self.output_dir / self.output_folder_name / self.get_region()
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
    ###### IAM ROLE FUNCTIONS
    ##########################################
    @staticmethod
    async def iam_enum_get_role(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            #TODO : find a role that can do this to test
            #TODO : Handle if response too long ???
            role = await iam_client.get_role(RoleName=role_name)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=role)
            logger.success(f"get_role() worked!")
            # logger.success(f"{json.dumps(role, indent=4, default=str)}")
            return role
        except Exception as e:
            logger.error(f"Failed to interrogate IAM get_role() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_attached_role_policies(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            # TODO : find a role that can do this to test
            role_policies = await iam_client.list_attached_role_policies(RoleName=role_name)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=role_policies)
            for policy in role_policies.get("AttachedPolicies", []):
                logger.success(f"Policy Name & ARN [{policy.get('PolicyName')}] : {policy.get('PolicyArn')}")
            return role_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_attached_role_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_role_policies(iam_client, role_name: str, metadata: bool = False) -> Union[str, dict]:
        try:
            role_policies = await iam_client.list_role_policies(RoleName=role_name)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=role_policies)
            logger.success(f"IAM list_role_policies worked!")
            logger.info(f"Role {role_name} has {len(role_policies.get('PolicyNames',[]))} inline policies")
            # List all policies, if present.
            for policy in role_policies.get('PolicyNames',[]):
                logger.success(f"Policy : {policy}")
            return role_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_role_policies() : \n{str(e)}")
            return str(e)

    ##########################################
    ###### IAM USER FUNCTIONS
    ##########################################
    @staticmethod
    async def iam_enum_get_user(iam_client, metadata: bool = False) -> Union[str, dict]:
        try:
            user = await iam_client.get_user()
            if not metadata :
                AWS_profile.remove_response_metadata(resp=user)
            logger.success(f"IAM get_user worked!")
            logger.success(json.dumps(user, indent=4, default=str))
            if user.get('User', '') and 'UserName' not in user.get('User', ''):
                if user.get('User').get('Arn','').endswith(':root'):
                    logger.success(f"Found root credentials {Emoji('1st_place_medal')}! \n{user.get('User').get('Arn','')}")
                else:
                    logger.error("Unexpected iam.get_user() response: %s" % user)
            # else: return user['User']['UserName']
            return user
        except Exception as e:
            logger.error(f"Failed to interrogate IAM get_user() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_attached_user_policies(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_policies = await iam_client.list_attached_user_policies(UserName=username)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=user_policies)
            logger.success(f"IAM list_attached_user_policies worked!")
            logger.info(f"User {username} has {len(user_policies.get('AttachedPolicies',[]))} policies")
            for policy in user_policies.get('AttachedPolicies',[]):
                logger.success(f"Policy Name & ARN : {policy.get('PolicyName')} [{policy.get('PolicyArn')}]")
            return user_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_attached_user_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_user_policies(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_policies = await iam_client.list_user_policies(UserName=username)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=user_policies)
            logger.success(f"IAM list_user_policies worked!")
            logger.info(f"User {username} has {len(user_policies.get('PolicyNames',[]))} inline policies")
            # List all policies, if present.
            for policy in user_policies.get('PolicyNames',[]):
                logger.success(f"Policy : {policy}")
            return user_policies
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_user_policies() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_groups_for_user(iam_client, username: str, metadata: bool = False) -> Union[str, dict]:
        try:
            user_groups = await iam_client.list_groups_for_user(UserName=username)
            if not metadata :
                AWS_profile.remove_response_metadata(resp=user_groups)
            logger.success(f"IAM list_groups_for_user worked!")
            logger.info(f"User {username} has {len(user_groups.get('Groups',[]))} groups associated")
            return user_groups
        except Exception as e:
            logger.error(f"Failed to interrogate IAM list_groups_for_user() : \n{str(e)}")
            return str(e)

    @staticmethod
    async def iam_enum_list_group_policies(iam_client, user_groups: dict, metadata: bool = False) -> dict:
        res = {}
        for group in user_groups.get('Groups',[]):
            group_name = group.get('GroupName','')
            try:
                group_policies = await iam_client.list_group_policies(GroupName=group_name)
                if not metadata :
                    AWS_profile.remove_response_metadata(resp=group_policies)
                logger.success(f"IAM Group {group_name} has {len(group_policies.get('PolicyNames',[]))} inline policies : ")
                for policy in group_policies.get('PolicyNames',[]):
                    logger.info(f"---> {policy}")
                res[group_name] = group_policies
            except Exception as e:
                logger.error(f"Failed to interrogate IAM list_group_policies() : \n{str(e)}")
                res[group_name] = str(e)
        return res

    ##########################################
    ###### Parse all results to CLI
    ##########################################

    def parse_results(self):
        """
            Analyse saved results to show a resume of all retrieved info inside CLI.
            Avoid to parse all files by hand.
        """
        output_folder = self.output_dir / self.output_folder_name / self.get_region()
        if not output_folder.exists():
            logger.warning(f"Output folder {output_folder} does not exists. Please perform scan before")
            return

        for p in output_folder.rglob("*"):
            curr_service = p.stem
            service_res = []
            json_content = {}
            with p.open('r') as f:
                json_content = json.loads(f.read())

            all_func = json_content.get(curr_service)
            if all_func is not None:
                for func, res in all_func.items():
                    if isinstance(res, str) and any(res.startswith(x) for x in ["Access Denied","Unknown Exception","Unable to guess","An error occurred", "Not available in this region", "Missing required parameter"]):
                        continue
                    else:
                        service_res.append({func:res})

            if service_res:
                logger.success(f"Found results for : {curr_service} \n{json.dumps(service_res, indent=4, default=str)}")


