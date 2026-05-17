import random
import sys
import argparse
import time

import logging
from typing import List

from R2Log import logger, console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.emoji import Emoji
from rich.prompt import Confirm

import threading
import queue
import numpy as np
from itertools import zip_longest

from AWS_profile import AWS_profile
from libs.Partitions import Partition_Manager
from libs.User import User_config
from libs.Services import Services, Service

partitions_mngr = Partition_Manager()

def print_banner() -> None:
    banners = []
    banners.append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢠⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⡿⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⡌⠉⠉⠉⠉⠉⠉⣹⣿⣦⡄
⠀⠀⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠀⠀⢀⣴⣯⣴⣿⣿⣿⣿⠁
⠀⠀⠸⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣴⣿⣿⣿⣿⣿⣿⡿⠃⠀
⠀⠀⠀⢻⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠞⠛⠋⠉⠙⠛⠻⢿⡟⣿⣿⣿⣿⠻⠁⠀⠀        ██╗ █████╗ ██╗    ██╗███████╗
⠀⠀⠀⠘⣿⣿⣿⣿⣦⠀⠀⠀⠀⠀⡸⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣆⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢉⣷⣶⣶⣤⣄⢸⡿⠙⠁⠀⠀⠀⠀        ██║██╔══██╗██║    ██║██╔════╝
⠀⠀⠀⠀⣿⣿⣭⣬⣤⣤⣤⣄⣀⣀⣀⣀⣀⣀⢤⠤⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⠎⠀⠀⠀⠀⠀⠀⠀        ██║███████║██║ █╗ ██║███████╗
⠀⠀⠀⣸⣿⣿⣿⣿⠻⠛⠛⠿⡿⣿⣿⣿⣿⣾⣤⣀⣀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣾⣿⣿⣿⣷⣦⣄⣀⣀⣠⣤⣶⣿⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀        ██║██╔══██║██║███╗██║╚════██║
⠀⠀⣴⣿⣿⣿⠻⠈⠀⠀⠀⠀⠀⠈⠉⠛⠟⡿⢿⠿⡛⣘⣤⣤⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ╚█████╔╝██║  ██║╚███╔███╔╝███████║
⠀⢠⣿⣿⠻⠈⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣦⣶⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝
⠐⠛⠙⠈⠀⠀⠀⠀⠀⢀⣄⣦⣶⠿⠿⠿⠛⠛⠛⠉⠉⠉⠀⠀⠀⠘⠛⠻⠿⠿⠿⠿⠟⠛⠛⠙⠉⠁⠀⠈⠉⠛⠿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠿⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
""")
    banners.append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣠⣤⣤⠶⠶⠶⠶⠾⠛⠛⠛⠛⠛⠛⠛⢿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣿⣛⠛⠛⠛⠓⠢⢄⡀⠀⠤⠟⠂⠀⠀⠀⠀⠀⠀⢀⡿        ██╗ █████╗ ██╗    ██╗███████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⠾⠛⠉⠑⠤⣙⢮⡉⠓⣦⣄⡀⠀⣹⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠃        ██║██╔══██╗██║    ██║██╔════╝
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⡶⠞⠋⠉⠀⠀⠀⠀⠀⠀⠒⠛⠛⠛⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⢰⡟⠀        ██║███████║██║ █╗ ██║███████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠾⠛⠉⣡⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⢺⢿⢉⡽⡟⢓⣶⠦⢤⣀⡀⠈⠳⣿⠁⠀        ██║██╔══██║██║███╗██║╚════██║
⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠟⠁⠀⠀⣀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠚⠁⠀⢛⠛⠛⠻⢷⡧⣾⡴⣛⣏⣹⡇⣀⣿⠀⠀    █████╔╝██║  ██║╚███╔███╔╝███████║
⠀⠀⠀⠀⠀⠀⣠⠞⠋⠀⣀⠤⠒⢉⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠔⠋⠀⣀⠴⠚⠛⠛⠯⡑⠂⠀⠀⡏⢹⣿⡾⠟⠋⠁⠀⠀    ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝
⠀⠀⠀⠀⣠⠞⠁⠀⠐⠊⠀⠀⢠⡿⠁⠀⢰⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⣤⡿⠋⠀⠀⠀⠀⠀⠀⡹⠀⠀⠀⣠⡾⠋⠀⠀⠀⠀⠀⠀
⠀⠀⣠⡞⠁⠀⠀⠀⠀⠀⠀⢠⡿⠁⢀⢸⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⡞⠋⠉⠉⠓⠒⠢⢤⣴⣥⣆⣠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
⠀⣼⠋⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀⠀⢸⠀⡆⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⢽⣦⠀⠀⠀⠀⠀⠀⣟⡿⣽⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣇⣤⣤⣤⣤⣄⡀⠀⢀⡾⠁⠀⠀⢘⡆⠱⡈⢆⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⢻⡚⡆⣀⠀⠀⠀⢸⡽⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠙⢷⣾⠃⠀⠀⠀⠈⠾⣦⣙⠪⢷⠄⠀⠀⠀⠀⠀⠀⠀⠈⠻⣭⣟⣹⢦⣀⣀⣟⣹⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⣤⠶⠖⠊⠉⠀⠉⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠦⣼⣞⣹⣯⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """)
    logger.info(random.choice(banners))

def worker(task_queue, aws_profile: AWS_profile, progress, task_progress_ids) -> None:
    """Worker thread function to process tasks from the queue."""
    while True:
        try:
            service_list: List[Service] = task_queue.get(timeout=60)  # Wait for a task
        except queue.Empty:
            break  # Exit if the queue is empty
        try:
            aws_profile.launch_discovery(service_list, progress, task_progress_ids)
        except Exception as e:
            for service in service_list:
                progress.remove_task(task_progress_ids[service.name])
            # logger.error(f"Task ["+",".join(services)+f"] failed with exception: {e}")
            logger.error(f"Error occurred : {e}")
            console.print_exception(show_locals=True)
        finally:
            task_queue.task_done()  # Mark the task as done

def verify_unsafe(unsafe: bool, aws_profile: AWS_profile) -> None:
    if unsafe:
        resp = Confirm.ask("Are you sure you want to run this script in unsafe mode ?", show_choices=True, console=console)
        if not resp:
            sys.exit(0)
        else:
            logger.warning("Running in unsafe mode.")
            aws_profile.set_unsafe_mode()

def print_elapsed_time(start: time.time) -> None:
    end = time.time()
    logger.info(f"Script took : {str(end - start)} seconds")

def set_logger(level: int) -> None:
    logger.setVerbosity(level)
    file_handler = logging.FileHandler("logs.txt")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setLevel(logger.level)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

def print_services(services: Services) -> None:
    """
        Print services and their associated number of functions.
        Will display only selected services to estimate the number of calls to perform.
        (allow estimating if furtivity is in place or not)
    """
    call_to_perform = 0
    not_activated_function_in_activated_services = 0

    repr_array = []
    activated_services = services.get_services(active_only=True)
    all_services = services.get_services(active_only=False)

    total_api_calls = sum([len(service.get_functions(active_only=False)) for service in all_services])

    logger.info(f"{Emoji('hamster')} Every service are listed below with it's associated number of functions : ")
    for service in activated_services:
        functions_activated = service.get_functions(active_only=True)
        all_functions = service.get_functions(active_only=False)
        diff_functions = set(all_functions) - set(functions_activated)

        not_activated_function_in_activated_services += len(diff_functions)

        call_to_perform += len(functions_activated)
        repr_array.append((service.name, len(functions_activated)))

    PAIRS_PER_ROW = min(len(repr_array),5)  # change to 3, 4, etc.

    # compute column widths
    name_width = max(len(name) for name, _ in repr_array)
    num_width = max(len(str(num)) for _, num in repr_array)

    it = iter(repr_array)
    for group in zip_longest(*[it] * PAIRS_PER_ROW, fillvalue=("", "")):
        console.print("   ".join(
            f"{name:<{name_width}} [{num:>{num_width}}]"
            for name, num in group
        ), highlight=True)

    logger.info(f"Total number of activated services : [{len(activated_services)}/{len(all_services)}]")
    logger.info(f"Total number of call to perform : [{call_to_perform}/{total_api_calls}]")
    logger.info(f"Total number of functions avoided inside active service : {not_activated_function_in_activated_services}")
    if len(activated_services) == len(all_services):
        logger.warning(f"+------------------------------------------------------------------+")
        logger.warning(f"| /!\\    You're about to launch discovery on ALL services      /!\\ |")
        logger.warning(f"+------------------------------------------------------------------+")

def parse_args() -> argparse.Namespace:
    global partitions_mngr

    all_regions = partitions_mngr.list_regions(get_all=True)
    regions_choices = [r.name for r in all_regions] + ["all"]

    parser = argparse.ArgumentParser(description='Bruteforce AWS rights with boto3', epilog=print_banner()) #little hack to print banner on help menu. Do not return str because if so, the rest of help message wont print...
    parser.add_argument('--credentials-file', default=User_config.default_credentials_file_path,
                        help='AWS credentials file')
    parser.add_argument('--config-file', default=User_config.default_config_file_path, help='AWS config file')
    parser.add_argument('-t', '--threads', type=int, default=75, help='Number of threads to use')
    parser.add_argument('--thread-timeout', type=int, default=30, help='Timeout consumed before killing thread')
    parser.add_argument('--update-services', action="store_true", default=False,
                        help='Force to update list of services and associated functions. This file saves time to avoid reparsing all services/functions/functions_args...')
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
    #TODO: FIXME
    #parser.add_argument('--no-banner', action="store_true", default=False, help='Do not print banner')
    parser.add_argument('-p', '--dont-print-services', action="store_true",
                        help='List of all available services')
    parser.add_argument('--list-partitions', action="store_true",
                        help='Partition to use (upper level of regions - which is not documented but found by reversing SDK)')
    parser.add_argument('--unsafe-mode', action="store_true",
                        help='Perform potentially destructive functions. Disabled by default.')
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Verbosity level (-v for verbose, -vv for advanced, -vvv for debug)")
    return parser.parse_args()

if __name__ == "__main__":

    start = time.time()

    args = parse_args()
    set_logger(level=args.verbose)

    # TODO: FIXME
    # if not args.no_banner:
    #     print_banner()

    if args.list_partitions:
        partitions_mngr.pprint_partitions()

    if args.regions:
        regions_to_scan = partitions_mngr.verify_region_exists(input_region=args.regions)

        settings_list = [ User_config.load(config_file_path=args.config_file,
                                           credentials_file_path=args.credentials_file,
                                           region_name=region)
                          for region in regions_to_scan ]
    else:
        settings_list = [ User_config.load(config_file_path=args.config_file, credentials_file_path=args.credentials_file) ]

    for curr_settings in settings_list:

        aws_profile = AWS_profile(creds=curr_settings, metadata=args.metadata)

        if args.update_services:
            aws_profile.update_dynamically_services_functions()
            print_elapsed_time(start=start)
            start = time.time()

        iam_res = aws_profile.iam_enum()

        verify_unsafe(unsafe=args.unsafe_mode, aws_profile=aws_profile)
        aws_profile.services.calculate_white_and_black_list(white_list=args.white_list, black_list=args.black_list)
        aws_profile.services.calculate_safe_mode()

        if not args.dont_print_services:
            print_services(services=aws_profile.services)
            print_elapsed_time(start=start)
            start = time.time()

            resp = Confirm.ask(f"Would you like to run script with this config ?", show_choices=True, console=console)
            if not resp:
                logger.info("Exiting")
                sys.exit(0)

        logger.info(f"Be patient, script can take up to 6min to BF. {Emoji('pray')}")

        services_to_bf = aws_profile.services.get_services(active_only=True)
        NUMBER_OF_THREADS = len(services_to_bf) if len(services_to_bf) < args.threads else args.threads

        services_chunks = np.array_split(services_to_bf, NUMBER_OF_THREADS)
        services_chunks = [list(chunk) for chunk in services_chunks]

        task_queue = queue.Queue()
        for chunk in services_chunks:
            task_queue.put(chunk)

        with Progress(
                SpinnerColumn(),
                "[bold blue]{task.description}",
                BarColumn(),
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
                for service in aws_profile.services.get_services(active_only=True)
            }

            # Start worker threads
            threads = []
            for _ in range(NUMBER_OF_THREADS):  # Adjust the number of threads as needed
                thread = threading.Thread(target=worker, args=(task_queue, aws_profile, progress, task_progress_ids))
                thread.start()
                threads.append(thread)

            # Wait for all threads to finish
            for thread in threads:
                thread.join(timeout=args.thread_timeout)

        aws_profile.write_iam_results_at_the_end(iam_results=iam_res)

        logger.success(f"{Emoji('partying_face')} All results have been written to this folder : {aws_profile.get_arn_safe_linux(aws_profile.arn)}/{aws_profile.boto_session.region_name}")
        print_elapsed_time(start=start)
        logger.info(f"Please wait for threads to exit properly (even if Ctrl+C should not cause damages to results) {Emoji('hamster')}")
