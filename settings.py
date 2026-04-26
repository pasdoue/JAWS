from pathlib import Path
from typing import List
import os


class Config:
    SESSION_TOKEN_DURATION: int = os.environ.get('SESSION_TOKEN_DURATION', 3600) # from 900 sec to 129600 sec (36 hours)
    SERVICES_FILE_MAPPING: Path = os.environ.get('SERVICES_FILE_MAPPING', Path(__file__).parent / "services.json")
    REGIONS_FILE_MAPPING: Path = os.environ.get('REGIONS_FILE_MAPPING', Path(__file__).parent / "regions.json")
    SAFE_MODE: List[str] = ["can_", "check_", "checkout_", "claim_", "compare_", "contains_", "decode_", "decrypt_", "derive_", "describe_", "detect_", "discover_", "download_", "estimate_", "evaluate_", "export_", "filter_", "get_", "group_", "head_", "import_", "is_", "list_", "poll_", "predict_", "query_", "re_", "read_", "receive_", "refresh_", "resolve_", "restore_", "retrieve_", "return_", "sample_", "scan_", "search_", "select_", "synthesize_", "validate_", "verify_", "view_"]
    BILLING_HEAVY_PREFIXES = ["analyze_", "scan_", "query_", "search_", "predict_", "synthesize_", "export_", "import_",
                              "download_", "evaluate_", "estimate_", "sample_"]
    AVOID_PATTERN = ["pagina", "delete"]