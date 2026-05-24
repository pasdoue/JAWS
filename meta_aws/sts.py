import json

from R2Log import logger

from AWS_profile import AWS_profile
from meta_aws.meta_aws import MetaAWS
from settings import Config


class MetaSTS(MetaAWS):

    async def get_session_token(self):
        res = await self.boto_func(DurationSeconds=Config.SESSION_TOKEN_DURATION)
        AWS_profile.remove_response_metadata(resp=res)
        if isinstance(res, dict) and "Credentials" in res:
            pprint_creds = json.dumps(res['Credentials'], default=str, indent=4)
            logger.success(f"Session token successfully retrieved : duration {Config.SESSION_TOKEN_DURATION/60} minutes / {int(Config.SESSION_TOKEN_DURATION/3600)} hours\n{pprint_creds}")
        return res

