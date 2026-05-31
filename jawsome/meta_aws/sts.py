import json

from R2Log import logger

from jawsome.AWS_profile import AWS_profile
from jawsome.meta_aws.meta_aws import MetaAWS
from jawsome.config.UserConfig import User_Config


class MetaSTS(MetaAWS):

    async def get_session_token(self):
        token_duration = User_Config.SESSION_TOKEN_DURATION
        res = await self.boto_func(DurationSeconds=token_duration)
        AWS_profile.remove_response_metadata(resp=res)
        if isinstance(res, dict) and "Credentials" in res:
            pprint_creds = json.dumps(res['Credentials'], default=str, indent=4)
            logger.success(f"Session token successfully retrieved : duration {token_duration/60} minutes / {int(token_duration/3600)} hours\n{pprint_creds}")
        return res

