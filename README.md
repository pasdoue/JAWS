## General

This project has been released because, impossible to find robust library for brute forcing AWS rights.  
They have different flaws : too much running time / does not test everything

Tested projects :  
- https://github.com/andresriancho/enumerate-iam  
- https://github.com/carlospolop/bf-aws-permissions  
- https://github.com/peass-ng/CloudPEASS

## Important Information

> This tool is developed on my free time by myself only.  
It's possible that you encounter issues even if I try to test as much as possible all possible configurations...  
Feel free to report an issue or suggest a PR 🍻

This code is using official **boto3** library and load **dynamically** all services (ie : iam,ec2...) and all associated functions (ie : ec2.list_images_in_recycle_bin and so on) of boto3  
**So even if boto3 is updated, this tool remains up to date !! 😉**  

### When first launch it may takes around 4min30 because needs to map all boto functions !!   
### After that it runs up to **7min for total BF** with fiber connection (**still twice faster than other tools 🏎😉**)

At the end, when you see this message : "Please wait for threads to exit properly..." you can kill prog if you want (just verify output folder is well populated).  
Something get stuck while finishing and I couldn't identify why or what is the real bottleneck... 

## Setup

1. Set your creds & config inside files : https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html

> The script can support multiple profiles. So feel free to create plenty of them if needed ! :D
> Simple & minimalist example below : 

~/.aws/credentials : 
```bash
[default]
 aws_access_key_id = ASIA...NSQ
 aws_secret_access_key = WihcB......PiMeFULn
 aws_session_token = IQoJb3JpZ2luX2VjEDcaCXVzLWVhc3QtMiJ.....Hm25smvGxg=
```

~/.aws/config : 
```bash
[default]
 region = us-east-2
```

2. Create a safe execution code environment and launch it

If you run this script the first time with or without params, it will perform an update of sessions and functions available by boto first.
```bash
python3 -m venv venv && souce venv/bin/activate
python3 -m pip install -e .
```

3. Start gathering info

> python3 -h

```bash
[*]
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

usage: main.py [-h] [--credentials-file CREDENTIALS_FILE] [--config-file CONFIG_FILE] [-t THREADS] [--thread-timeout THREAD_TIMEOUT] [--update-services]
               [-r [{af-south-1,ap-east-1,ap-east-2,ap-northeast-1,ap-northeast-2,ap-northeast-3,ap-south-1,ap-south-2,ap-southeast-1,ap-southeast-2,ap-southeast-3,ap-southeast-4,ap-southeast-5,ap-southeast-6,ap-southeast-7,ca-central-1,ca-west-1,eu-central-1,eu-central-2,eu-north-1,eu-south-1,eu-south-2,eu-west-1,eu-west-2,eu-west-3,il-central-1,me-central-1,me-south-1,mx-central-1,sa-east-1,us-east-1,us-east-2,us-west-1,us-west-2,cn-north-1,cn-northwest-1,us-gov-east-1,us-gov-west-1,us-iso-east-1,us-iso-west-1,us-isob-east-1,us-isob-west-1,eu-isoe-west-1,us-isof-east-1,us-isof-south-1,eusc-de-east-1,all} ...]]
               [-b [SERVICES ...]] [-w [SERVICES ...]] [--metadata] [-p] [--list-partitions] [--unsafe-mode] [-v]

Bruteforce AWS rights with boto3

options:
  -h, --help            show this help message and exit
  --credentials-file CREDENTIALS_FILE
                        AWS credentials file
  --config-file CONFIG_FILE
                        AWS config file
  -t, --threads THREADS
                        Number of threads to use
  --thread-timeout THREAD_TIMEOUT
                        Timeout consumed before killing thread
  --update-services     Force to update list of services and associated functions. This file saves time to avoid reparsing all services/functions/functions_args...
  -r, --regions [{af-south-1,ap-east-1,ap-east-2,ap-northeast-1,ap-northeast-2,ap-northeast-3,ap-south-1,ap-south-2,ap-southeast-1,ap-southeast-2,ap-southeast-3,ap-southeast-4,ap-southeast-5,ap-southeast-6,ap-southeast-7,ca-central-1,ca-west-1,eu-central-1,eu-central-2,eu-north-1,eu-south-1,eu-south-2,eu-west-1,eu-west-2,eu-west-3,il-central-1,me-central-1,me-south-1,mx-central-1,sa-east-1,us-east-1,us-east-2,us-west-1,us-west-2,cn-north-1,cn-northwest-1,us-gov-east-1,us-gov-west-1,us-iso-east-1,us-iso-west-1,us-isob-east-1,us-isob-west-1,eu-isoe-west-1,us-isof-east-1,us-isof-south-1,eusc-de-east-1,all} ...]
                        Specify regions to scan
  -b, --black-list [SERVICES ...]
                        List of services to remove separated by comma. Launch script with -p to see services
  -w, --white-list [SERVICES ...]
                        List of services to whitelist/scan separated by comma. Launch script with -p to see services
  --metadata            Retrieve metadata of all AWS SDK functions calls
  -p, --dont-print-services
                        List of all available services
  --list-partitions     Partition to use (upper level of regions - which is not documented but found by reversing SDK)
  --unsafe-mode         Perform potentially destructive functions. Disabled by default.
  -v, --verbose         Verbosity level (-v for verbose, -vv for advanced, -vvv for debug)
```

## How does it works ? 

> Disclaimer : Part described bellow came from a session where I decided to reverse python SDK to understand how to stay up to date about AWS regions.

Everyone knows about AWS regions, but I discovered that only half true...  
According to SDK code, there is an upper level than regions which is called "partition".  
So every "partition" get a list of "regions" and each regions has a bundle of available "services" which have also it's own a bundle of available "functions".    

In summary : partition > regions > services > functions

The well known "regions" that everybody knows is part of a partition called "aws"  
All those information can be seen inside : .venv/lib/python3.14/site-packages/botocore/data/endpoints.json  

1. To stay up to date according to declared "partitions" and "regions" of SDK, the script read those information from "endpoints.json" (complete path just upper). 

2. Script begin always by loading all services and functions available in SDK. So it is always up to date (take about 4min30).

3. Perform equivalent of `aws sts get_caller_identity` to retrieve ARN (identity of the token)
Examples : 
arn:aws:sts::718896642544:assumed-role/web01/i-0d925034be5d2f45b
arn:aws:iam::718896642544:user/lucifer

4. From ARN we can know if we are a "user" or a "role".
So we will call the following IAM function :  

If we are User :  
- get_account_authorization_details
- get_user
- list_attached_user_policies
- list_user_policies
- list_groups_for_user
- list_group_policies
  
If we are Role :  
- get_role
- list_attached_role_policies
- list_role_policies

5. Once those information retrieved, it performs brute force on whatever endpoint you tell it to

A. Performs call to endpoints that **do not require** some **parameters** to works.  
Doing so, we hope to **retrieve some artifacts** by performing som list_ or get_ functions (**loot** is life !!).

B. If we **loot some artifacts** we try to call every functions with required parameters.  
We check **all "keys"** of loot and compare them to functions parameters.  
**Only if all params can be "injected"** :
- easy to handle on one param
- not coded yet for multiple ones :/

6. Find your loot inside generated directory : \<role>/\<region>/\<service>.json  
Path is indicated on terminal/logs at the end of scan, you may have to scroll up a little

## Commands cheat sheet

Launch scan on all services : 
```bash
python3 main.py
```

Launch scan on all services and retrieve metadata (deactivated by default) : 
```bash
python3 main.py --metadata
```

Force an update of all boto3 services/functions/functions_params mapping (can be slow) : 
```bash
python3 main.py --update-services
```

List partitions : 
```bash
python3 main.py --list-partitions
```

Spawn script without banner (bye bye sharky :/) : 
```bash
python3 main.py --no-banner
```

Dont print list of available services : 
```bash
python3 main.py -p
```

Scan using services white-list : 
```bash
python3 main.py -w ec2 sts pricing dynamodb
```

Show number of calls that will be performed using only some services : 
Asks you if you want to perform scan now ;)
```bash
python3 main.py -p -w ec2 sts dynamodb
```

Scan using black-list : 
```bash
python3 main.py -b cloudhsm cloudhsmv2 sms dynamodb
```

Scan using black-list & white-list (will perform scan on white list without "dynamodb" service): 
```bash
python3 main.py -w ec2 sts pricing dynamodb -b cloudhsm cloudhsmv2 sms dynamodb
```

Update region file list :  
```bash
python3 main.py --update-regions
```

Perform scan on multiple regions :  
```bash
python3 main.py -w ec2 sts -r us-east-1 us-east-2 eu-west-1
```

Perform scan on ALL regions (carefull should take a looong time friendo) :  
```bash
python3 main.py -w ec2 sts -r all
```

Total BF (unsafe mode, not recommended if you don't know what you do)
```bash
python3 main.py --unsafe-mode
```

## Done : 

- [X] Handle profile like aws cli and allow user to use any file config
- [X] Support multiple regions to scan
- [X] Allow specific service/function hooking
- [X] Performs some IAM checks before and avoid some useless calls (that can also trigger alerts)
- [X] Remove metadata from SDK response (better clarity & less storage used)
- [X] Put first IAM checks & results after BF performed (also check why those calls are performed as they should be deactivated for BF phase)
- [X] Check if function as "OwnerIds" in params and then replace it with "self" to avoid false positive
- [X] Detect all params of a function (by parsing __doc__ strings, couldn't find another way to do it)
- [X] First call functions with no required params and then those with params (and try to replace params with previous collected artefacts)

## TBD : 

- [ ] Some parameters of some particular functions are not well retrieved (WTF ><) : lucifer elasticbeanstalk describe_environment_managed_action_history 
- [ ] Handle multiple args replacement
- [ ] Detect if some results will be erased and trigger a warning if different from previous run
- [ ] Maybe chunk output json files that are too big (but make it optional)

## Bonus

All functions prefix i could find (255). This is helping to determine which function can be called without "damages"

```text
abort_
accept_
acknowledge_
activate_
add_
admin_
advertise_
allocate_
allow_
analyze_
apply_
approve_
archive_
assign_
associate_
assume_
attach_
authorize_
back_
backtrack_
batch_
begin_
build_
bulk_
bundle_
calculate_
can_
cancel_
change_
channel_
chat_
check_
checkout_
claim_
classify_
clear_
clone_
close_
commit_
compare_
complete_
compose_
configure_
confirm_
connect_
contains_
continue_
converse_
convert_
copy_
count_
create_
deactivate_
deauthorize_
decline_
decode_
decrease_
decrypt_
define_
deliver_
deny_
deploy_
deprecate_
deprovision_
deregister_
derive_
describe_
detach_
detect_
disable_
disassociate_
discard_
disconnect_
discover_
dismiss_
dispose_
dissociate_
distribute_
domain_
download_
enable_
encrypt_
enter_
estimate_
evaluate_
exchange_
execute_
exit_
expire_
export_
extend_
failover_
filter_
finalize_
flush_
forecast_
forget_
forgot_
generate_
get_
global_
grant_
group_
head_
import_
increase_
index_
infer_
ingest_
initialize_
initiate_
install_
instantiate_
invalidate_
invite_
invoke_
is_
issue_
join_
label_
list_
lock_
logout_
lookup_
manage_
mark_
merge_
meter_
migrate_
modify_
monitor_
move_
notify_
open_
opt_
optimize_
override_
pause_
peer_
phone_
poll_
populate_
post_
predict_
prepare_
preview_
promote_
provide_
provision_
publish_
purchase_
purge_
push_
put_
query_
re_
read_
rebalance_
reboot_
rebuild_
receive_
recognize_
record_
redact_
redrive_
refresh_
regenerate_
register_
reimport_
reject_
release_
reload_
remove_
rename_
render_
renew_
reorder_
replace_
replicate_
report_
request_
resend_
reserve_
reset_
resize_
resolve_
respond_
restart_
restore_
resume_
resync_
retire_
retrieve_
retry_
return_
reverse_
revoke_
rollback_
rotate_
run_
sample_
scan_
schedule_
search_
select_
send_
set_
setup_
share_
shutdown_
sign_
signal_
simulate_
skip_
snap_
split_
start_
stop_
stream_
submit_
subscribe_
suspend_
swap_
switchover_
sync_
synthesize_
tag_
terminate_
test_
transact_
transfer_
translate_
unarchive_
unassign_
undeploy_
undeprecate_
ungroup_
unlabel_
unlink_
unlock_
unmonitor_
unpeer_
unregister_
unshare_
unsubscribe_
untag_
update_
upgrade_
upload_
validate_
verify_
view_
vote_
withdraw_
write_
```
