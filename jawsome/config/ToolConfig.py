
__version__ = "1.2.0"

class Tool_Config:

    version: str = __version__

    SAFE_MODE = [ #not sorted (TBD)
                 "advertise_",
                 "clear_",
                 "check_",
                 "checkout_",
                 "compare_",
                 "contains_",
                 "decrypt_",
                 "decode_",
                 "derive_",
                 "synthesize_",
                 "validate_",
                 "view_",
                 # avoid interruption of services
                 "build_",
                 "cancel_",
                 "create_",
                 "clear_",
                 "close_",
                 "detect_",
                 "enable_",
                 "estimate_",
                 "evaluate_",
                 "restore_",
                 "poll_",
                 "predict_",
                 "sample_",
                 "select_",
                 "update_",
                 # remove attributes methods
                 "unarchive_",
                 "unassign_",
                 "undeploy_",
                 "undeprecate_",
                 "ungroup_",
                 "unlabel_",
                 "unlink_",
                 "unlock_",
                 "unmonitor_",
                 "unpeer_",
                 "unregister_",
                 "unshare_",
                 "unsubscribe_",
                 "untag_",
                 ]
    BILLING_HEAVY_PREFIXES = ["analyze_", "scan_", "query_", "search_", "predict_", "synthesize_", "export_", "import_",
                              "download_", "evaluate_", "estimate_", "sample_"]
    AVOID_PATTERN = ["pagina", "delete", "get_waiter"]

    HANDLE_BOTO_ERROR_ACCESS_DENIED = ["UnauthorizedOperation", "AccessDenied", "ForbiddenException", "Access Denied"]

    AVOID_SERVICE_LOOT = ["MaxItems", "NextToken"]
    PARSING_FINAL_RESULT_AVOID_LIST = ["Access Denied","Unknown Exception","Unable to guess","An error occurred", "Not available in this region", "Missing required parameter"]

