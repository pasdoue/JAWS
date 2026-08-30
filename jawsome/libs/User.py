from configparser import ConfigParser
from pathlib import Path
from typing import Union, Optional
import inspect

import boto3
from rich.emoji import Emoji

from rich.prompt import Prompt
from R2Log import logger


class User_config:
    """
        This class will parse config file of user and return a dict with all params to use in boto3.session.Session.
        Because boto3.session.Session params differs from config files (thanks AWS... grrr) we need to reformat them
    """
    default_credentials_file_path: Path = Path.home() / ".aws" / "credentials"
    default_config_file_path: Path = Path.home() / ".aws" / "config"

    @classmethod
    def _load_credentials_file(cls, credentials_file_path: Path, region_name: Optional[str]) -> dict:
        """
            Method to parse credentials config file (default : ~/.aws/credentials) which is Yaml format
        """
        profile_to_use = ""
        res = {}
        credentials = ConfigParser()

        if credentials_file_path.exists():
            credentials.read(credentials_file_path)
            cred_sections = credentials.sections()
            if len(cred_sections) > 1:
                prompt = f"Choose credentials to use : " if region_name is None else f"Choose credentials to use for region ({region_name}) : "
                profile_to_use = Prompt.ask(prompt=prompt, choices=cred_sections, show_choices=True)
            elif len(cred_sections) == 1:
                profile_to_use = cred_sections[0]
                logger.info(f"Chose default creds in {credentials_file_path} which is : [{cred_sections[0]}]")
            else:
                raise ValueError(f"{Emoji('hamster')} AWS credentials file detected but no section found : {credentials_file_path}")

            tmp = dict(credentials.items(profile_to_use))
            for k, v in tmp.items():
                logger.info(f"{k} : {v[:4]}...{v[-4:]}")

            res["profile_name"] = profile_to_use
            # Because AWS Boto library Session only accept those params and no other ones... We need to remove all other params... GG AWS
            for k, v in tmp.items():
                # verify this param exists in boto3.session.Session
                if k in inspect.signature(boto3.session.Session).parameters.keys():
                    res[k] = v
        else:
            raise FileNotFoundError(f"{Emoji('no_entry_sign')} AWS credentials file does not exists : {credentials_file_path}")
        return res

    @classmethod
    def _load_config_file(cls, config_file_path: Path) -> dict:
        """
            Method to parse config file (default : ~/.aws/config) which is Yaml format
        """
        config = ConfigParser()

        if config_file_path.exists():
            config.read(config_file_path)
            config_section = ""
            if len(config.sections()) > 1:
                config_section = Prompt.ask(prompt="Choose config to use : ", choices=config.sections(), show_choices=True)
            elif len(config.sections()) == 1:
                config_section = config.sections()[0]
                logger.info(f"Chose default region in {config_file_path} which is : {config.get(config_section, 'region')}")
            else:
                raise ValueError(f"{Emoji('hamster')} AWS config file detected but no section found : {config_file_path}")

            # Because AWS Boto library Session only accept those params and no other ones... We need to remove all other params... GG AWS
            return {"region_name": config.get(config_section, "region")}
        else:
            raise FileNotFoundError(f"{Emoji('no_entry_sign')} AWS config file does not exist : {config_file_path}")

    @staticmethod
    def load(credentials_file_path: Union[Path|str] = default_credentials_file_path,
             config_file_path: Union[Path|str] = default_config_file_path,
             region_name: Optional[str] = None) -> dict:
        """
            Handle the loading of credentials and config files
        """

        creds_file_path = Path(credentials_file_path).expanduser() if isinstance(credentials_file_path, str) else credentials_file_path.expanduser()
        conf_file_path = Path(config_file_path).expanduser() if isinstance(config_file_path, str) else config_file_path.expanduser()

        settings = User_config._load_credentials_file(credentials_file_path=creds_file_path, region_name=region_name)

        if region_name is not None:
            settings["region_name"] = region_name
        else:
            settings.update(User_config._load_config_file(config_file_path=conf_file_path))

        if not settings["aws_access_key_id"]:
            logger.critical("AWS access key ID not found.")
        if not settings["aws_secret_access_key"]:
            logger.critical("AWS secret access key not found.")

        return settings
