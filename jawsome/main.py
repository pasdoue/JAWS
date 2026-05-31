import asyncio
import sys
import argparse
import time
from pathlib import Path

try:
    import aiobotocore
    import botocore
    import boto3
    import requests

    from R2Log import logger, console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.emoji import Emoji
    from rich.prompt import Confirm

    from jawsome.AWS_profile import AWS_profile
    from jawsome.libs.Partitions import Partition_Manager
    from jawsome.libs.User import User_config
    from jawsome.libs.Services import print_services

    from jawsome.utils import print_banner, print_elapsed_time, set_logger, SharkBarColumn
    from jawsome.config.ToolConfig import __version__

except ModuleNotFoundError as e:
    print("Mandatory dependencies are missing:", e)
    print("Please install them with python3 -m pip install --upgrade -r requirements.txt")
    exit(1)
except ImportError as e:
    print("An error occurred while loading the dependencies!\nDetails:")
    print(e)
    exit(1)
except KeyboardInterrupt:
    exit(1)

partitions_mngr = Partition_Manager()

async def worker(service, aws_profile: AWS_profile, progress, task_progress_ids) -> None:
    try:
        await aws_profile.launch_discovery(service, progress, task_progress_ids)
    except Exception as e:
        progress.remove_task(task_progress_ids[service.name])
        logger.error(f"Error occurred : {e}")
        console.print_exception(show_locals=True)

def verify_unsafe(unsafe: bool, aws_profile: AWS_profile) -> None:
    if unsafe:
        resp = Confirm.ask("Are you sure you want to run this script in unsafe mode ?", show_choices=True, console=console)
        if not resp:
            sys.exit(0)
        else:
            logger.warning("Running in unsafe mode.")
            aws_profile.set_unsafe_mode()

def parse_args() -> argparse.Namespace:
    global partitions_mngr

    all_regions = partitions_mngr.list_regions(get_all=True)
    regions_choices = [r.name for r in all_regions] + ["all"]

    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument('--no-banner', action="store_true", default=False, help='Do not print banner')

    # Parse only known args first
    pre_args, remaining = pre_parser.parse_known_args()
    if not pre_args.no_banner:
        print_banner()

    parser = argparse.ArgumentParser(description='Bruteforce AWS rights with boto3', parents=[pre_parser]) #little hack to print banner on help menu. Do not return str because if so, the rest of help message wont print...
    parser.add_argument('--credentials-file', default=User_config.default_credentials_file_path, help='AWS credentials file')
    parser.add_argument('--config-file', default=User_config.default_config_file_path, help='AWS config file')
    parser.add_argument('--log-file', action="store_true", help='Log inside file the current run')
    parser.add_argument('-o','--output-dir', default=Path.cwd(), help='Custom output directory to store results')
    parser.add_argument('-t', '--threads', type=int, default=75, help='Number of threads to use')
    parser.add_argument('--thread-timeout', type=int, default=30, help='Timeout consumed before killing thread')
    parser.add_argument('-r', '--regions',
                        nargs='*',
                        choices=regions_choices,
                        help='Specify regions to scan')
    parser.add_argument('-b', '--black-list', nargs='*',
                        default="cloudhsm cloudhsmv2 sms sms-voice.pinpoint",
                        help='List of services to remove separated by comma. Launch script with -p to see services',
                        metavar='SERVICES')
    parser.add_argument('-w', '--white-list', nargs='*',
                        default=[],
                        help='List of services to whitelist/scan separated by comma. Launch script with -p to see services',
                        metavar='SERVICES')
    parser.add_argument('--metadata', action="store_true", help='Retrieve metadata of all AWS SDK functions calls')
    parser.add_argument('-p', '--dont-print-services', action="store_true", help='Don\'t print stats of number of calls it will perform and execute discovery asap (without prompt)')
    parser.add_argument('-s', '--skip-iam', action="store_true", help='Don\'t perform IAM check')
    parser.add_argument('--list-partitions', action="store_true", help='List partitions (upper level of regions - found by reversing SDK)')
    parser.add_argument('--unsafe-mode', action="store_true", help='Perform potentially destructive functions. Disabled by default.')
    parser.add_argument('--no-fancy-bar', action="store_true", help='Remove fancy advancement bar with shark and boat (due to calculation it add ~1min runtime for total BF)')
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level (-v for verbose, -vv for advanced, -vvv for debug)")
    parser.add_argument("--version", action="store_true", help="Print tool version")
    parser.parse_known_args()
    return parser.parse_args()

async def entry_point():
    start = time.time()

    args = parse_args()
    set_logger(level=args.verbose, logfile=args.log_file)

    if args.version:
        logger.info(f"Version : {__version__}")
        exit(0)

    if args.list_partitions:
        partitions_mngr.pprint_partitions()

    if args.regions:
        regions_to_scan = partitions_mngr.verify_region_exists(input_region=args.regions)

        settings_list = [User_config.load(config_file_path=args.config_file,
                                          credentials_file_path=args.credentials_file,
                                          region_name=region)
                         for region in regions_to_scan]
    else:
        settings_list = [
            User_config.load(config_file_path=args.config_file, credentials_file_path=args.credentials_file)]

    for curr_settings in settings_list:

        aws_profile = AWS_profile(creds=curr_settings, metadata=args.metadata, output_dir=args.output_dir)
        await aws_profile.init_class()

        iam_res = {}
        if not args.skip_iam:
            iam_res = await aws_profile.iam_enum()

        verify_unsafe(unsafe=args.unsafe_mode, aws_profile=aws_profile)
        aws_profile.services.calculate_white_and_black_list(white_list=args.white_list, black_list=args.black_list)
        aws_profile.services.calculate_safe_mode()

        if not args.dont_print_services:
            print_services(services=aws_profile.services)
            print_elapsed_time(start_time=start)
            start = time.time()

            resp = Confirm.ask(f"Would you like to run script with this config ?", show_choices=True, console=console)
            if not resp:
                logger.info("Exiting")
                sys.exit(0)

        logger.info(f"Be patient, script can take up to 6min to BF. {Emoji('pray')}")

        services_to_bf = aws_profile.services.get_services(active_only=True)

        bar_column = BarColumn() if args.no_fancy_bar else SharkBarColumn()
        with Progress(
                SpinnerColumn(),
                "[bold blue]{task.description}",
                bar_column,
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TextColumn("[cyan]{task.completed}/{task.total}"),
                transient=True,
                refresh_per_second=2,
                console=console
        ) as progress:
            # Add tasks to the progress bar
            task_progress_ids = {
                service.name: progress.add_task(f"[green]Processing {service.name}...", total=len(service.get_functions()))
                for service in services_to_bf
            }
            workers = [
                asyncio.create_task(worker(service, aws_profile, progress, task_progress_ids))
                for service in services_to_bf
            ]
            await asyncio.gather(*workers)

        if not args.skip_iam:
            aws_profile.write_iam_results_at_the_end(iam_results=iam_res)

        logger.success(f"{Emoji('partying_face')} All results have been written to this folder : {aws_profile.get_arn_safe_linux(aws_profile.arn)}/{aws_profile.get_region()}")
        print_elapsed_time(start_time=start)

def main():
    try:
        return asyncio.run(entry_point())
    except (KeyboardInterrupt, asyncio.CancelledError, EOFError):
        return 2
    except SystemExit as e:
        if e.code is not None:
            return int(e.code)
    except Exception:
        logger.error("It seems that something unexpected happened ...")
        console.print_exception(show_locals=True, suppress=[asyncio, botocore, boto3, requests, aiobotocore])
    return 1