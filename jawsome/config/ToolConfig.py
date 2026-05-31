
__version__ = "1.0.0"

class Tool_Config:

    version: str = __version__

    SAFE_MODE = ["can_", "check_", "checkout_", "claim_", "compare_", "contains_", "decode_", "decrypt_", "derive_", "describe_", "detect_", "discover_", "download_", "estimate_", "evaluate_", "export_", "filter_", "get_", "group_", "head_", "import_", "is_", "list_", "poll_", "predict_", "query_", "re_", "read_", "receive_", "refresh_", "resolve_", "restore_", "retrieve_", "return_", "sample_", "scan_", "search_", "select_", "synthesize_", "validate_", "verify_", "view_"]
    BILLING_HEAVY_PREFIXES = ["analyze_", "scan_", "query_", "search_", "predict_", "synthesize_", "export_", "import_",
                              "download_", "evaluate_", "estimate_", "sample_"]
    AVOID_PATTERN = ["pagina", "delete", "get_waiter"]
