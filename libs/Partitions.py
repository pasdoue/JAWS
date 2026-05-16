import json
from pathlib import Path
from typing import List, Union, Optional

from R2Log import logger
from botocore.loaders import Loader


ENDPOINTS_FILE = Path(Loader.BUILTIN_DATA_PATH) / "endpoints.json"


class Region:

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


class Partition:

    def __init__(self, shortname: str, name: str, dns_suffix: str, regex: str, regions: List[Region]):
        self.shortname = shortname
        self.name = name
        self.dns_suffix = dns_suffix
        self.regex = regex
        self.regions = regions


class Partition_Manager:

    """
        Class to handle partition.
        According to Python SDK code, there is a file which contains "the architecture" of AWS.
        You can inspect the file ./.venv/lib/python3.14/site-packages/botocore/data/endpoints.json

        So there are "partitions" and each of thos partitions have regions.
        The most known one is aws with regions us-east-1
    """

    def __init__(self):
        self.data = {}
        with ENDPOINTS_FILE.open('r') as f:
            self.data = json.loads(f.read())
        self.partitions: List[Partition] = []

        self._construct_partitions()

    def _construct_partitions(self) -> None:
        for partition in self.data["partitions"]:
            regions = []
            for name, descr in partition["regions"].items():
                regions.append(Region(name=name, description=descr["description"]))
            self.partitions.append(Partition(shortname=partition["partition"],
                      name=partition["partitionName"],
                      dns_suffix=partition["dnsSuffix"],
                      regex=partition["regionRegex"],
                      regions=regions))
        logger.success(f"Finished to parse boto conf")

    def pprint_partitions(self):
        for p in self.partitions:
            logger.info(f"==================================")
            logger.info(f"dnsSuffix : {p.dns_suffix}")
            logger.info(f"partition : {p.shortname}")
            logger.info(f"partitionName : {p.name}")
            logger.info(f"regionRegex : {p.regex}")
            var = ' '.join([r.name for r in p.regions])
            logger.info(f"regions : {var}")
            logger.info(f"==================================")
        logger.success(f"There are {len(self.partitions)} partitions")


    def list_regions(self, partition_shortname: Optional[str] = None, get_all: bool = False) -> List[Region]:
        res = []
        if get_all:
            for p in self.partitions:
                res += p.regions
            return res
        elif partition_shortname is not None:
            for p in self.partitions:
                if p.shortname == partition_shortname:
                    return p.regions
        else:
            logger.critical(f"You must provide at least a short partition name or retrieve ALL functions")
        return res


    def verify_region_exists(self, input_region: Union[str|List[str]]) -> List[str]:
        """
            Verify if the input region exists in the list of regions
            return only valid regions and raise error if no one exists
        """
        all_regions = self.list_regions(get_all=True)
        all_regions_str = [r.name for r in all_regions]

        if isinstance(input_region, str):
            # in case we want to interrogate all regions
            if input_region.lower() == "all":
                return all_regions_str
            else:
                input_region = [input_region]
        elif isinstance(input_region, list):
            if len(input_region) == 1 and input_region[0].lower() == "all":
                return all_regions_str

        # lowercase all regions
        input_region = [region.lower() for region in input_region]
        array_intersect = list(set(input_region) & set(all_regions_str))
        if not array_intersect:
            # raise ValueError("No valid regions found")
            logger.critical(
                f"Region '{input_region}' is not valid for partition {self.partition}"
                f"Allowed values: {" ".join(all_regions_str)}"
            )
        return array_intersect

