import json
from typing import List, Union, Any

import requests
from R2Log import logger
from rich.emoji import Emoji
from bs4 import BeautifulSoup

from settings import Config


class Regions:

    """
        Class to handle regions name. Based on this official web page :
        https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html

        Careful : a boto3 session object may not be authorized to list regions it can access...
        An error occurred (AccessDeniedException) when calling the ListRegions operation: User: arn:aws:iam::ID:user/... is not authorized to perform: account:ListRegions on resource: arn:aws:account::ID:account because no identity-based policy allows the account:ListRegions action

        So we need to handle it manually
    """
    REGION_FILEMAP = Config.REGIONS_FILE_MAPPING

    @staticmethod
    def get_regions_from_web() -> List[str]:
        """
            Retrieves regions information from web official web page of AWS :
            https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html
        """
        res = []
        url = "https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html"

        logger.info(f"{Emoji('pirate_flag')} Retrieving regions information from official web page of AWS")
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        elems = soup.find('div', {"class": "table-container"}).find("table").find_all("tr")[1:] #skip header row
        if elems:
            for elem in elems:
                region_name = elem.find_all("td")[0].text.strip()
                res.append(region_name)
        else:
            logger.critical("Unable to retrieve regions information from official web page of AWS")
        return res

    @classmethod
    def save_filemap(cls, regions: List[str]):
        try:
            with cls.REGION_FILEMAP.open('w+') as f:
                f.write(json.dumps(regions))
        except Exception as e:
            logger.critical(f"{Emoji('no_entry_sign')} Unable to save regions filemap : {e}")

    @classmethod
    def update_filemap(cls, force: bool = False):
        if not force and cls.REGION_FILEMAP.exists():
            return
        remote_regions = cls.get_regions_from_web()
        cls.save_filemap(remote_regions)

    @classmethod
    def load_filemap(cls) -> Any | None:
        try:
            with cls.REGION_FILEMAP.open('r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            logger.critical("Region filemap not found")

    @classmethod
    def verify_region_exists(cls, input_region: Union[str|List[str]]) -> List[str]:
        """
            Verify if the input region exists in the list of regions
            return only valid regions and raise error if no one exists
        """
        if isinstance(input_region, str):
            # in case we want to interrogate all regions
            if input_region.lower() == "all":
                return cls.load_filemap()
            else:
                input_region = [input_region]

        # lowercase all regions
        input_region = [region.lower() for region in input_region]
        data = cls.load_filemap()
        array_intersect = list(set(input_region) & set(data))
        if not array_intersect:
            raise ValueError("No valid regions found")
        return array_intersect

