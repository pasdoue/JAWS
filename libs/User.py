from configparser import ConfigParser
from pathlib import Path
from typing import Union
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
    def _load_credentials_file(cls, credentials_file_path: Path = default_credentials_file_path, region_name: Union[str, None] = None) -> Union[dict, None]:
        res = {}
        credentials = ConfigParser()

        if credentials_file_path.exists():
            credentials.read(credentials_file_path)
            cred_section = ""
            if len(credentials.sections()) > 1:
                prompt = f"Choose credentials to use : " if region_name is None else f"Choose credentials to use for region ({region_name}) : "
                cred_section = Prompt.ask(prompt=prompt, choices=credentials.sections(), show_choices=True)
            elif len(credentials.sections()) == 1:
                cred_section = credentials.sections()[0]
            else:
                logger.critical(f"{Emoji('hamster')} AWS credentials file detected but no section found.")

            if cred_section:
                tmp = dict(credentials.items(cred_section))
                res["profile_name"] = cred_section

                # Because AWS Boto library Session only accept those params and no other ones... We need to remove all other params... GG AWS
                for k, v in tmp.items():
                    # verify this param exists in boto3.session.Session
                    if k in inspect.signature(boto3.session.Session).parameters.keys():
                        res[k] = v
            return res
        else:
            logger.critical(f"{Emoji('no_entry_sign')} AWS credentials file does not exists. Configure it to launch script")

    @classmethod
    def _load_config_file(cls, config_file_path: Path = default_config_file_path, region_name: Union[str, None] = None) -> Union[dict, None]:
        config = ConfigParser()

        if region_name is not None:
            return {"region_name": region_name}

        if config_file_path.exists():
            config.read(config_file_path)
            config_section = ""
            if len(config.sections()) > 1:
                config_section = Prompt.ask(prompt="Choose config to use : ", choices=config.sections(), show_choices=True)
            elif len(config.sections()) == 1:
                config_section = config.sections()[0]
            else:
                logger.critical(f"{Emoji('hamster')} AWS config file detected but no section found.")

            # Because AWS Boto library Session only accept those params and no other ones... We need to remove all other params... GG AWS
            return {"region_name": config.get(config_section, "region")}
        else:
            logger.critical(f"{Emoji('no_entry_sign')} AWS config file does not exist. Using environment variables. Configure it to launch script")

    @staticmethod
    def load(credentials_file_path: Union[Path|str] = default_credentials_file_path,
             config_file_path: Union[Path|str] = default_config_file_path,
             region_name: str = None) -> dict:

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
