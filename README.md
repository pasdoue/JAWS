## General

This project has been released because, impossible to find robust library for brute forcing AWS IAM rights.

Tested those two projects but does not output same results... :  
https://github.com/andresriancho/enumerate-iam  
https://github.com/carlospolop/bf-aws-permissions  

## Information

**This code can take a while (up to 6min for total BF).**

This code is using official boto library and load dynamically all subfunctions of every services of boto (ie : iam,ec2...)

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

usage: main.py [-h] [--credentials-file CREDENTIALS_FILE] [--config-file CONFIG_FILE] [-t THREADS] [--thread-timeout THREAD_TIMEOUT] [--export-services] [--update-regions] [-r [PARAMETER ...]] [-b [PARAMETER ...]] [-w [PARAMETER ...]]
               [--no-banner] [-p] [--unsafe-mode] [-v]

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
  --export-services     Export all boto3 services and associated functions to file
  --update-regions      Update remotely list of AWS regions (official web doc of AWS)
  -r, --regions [PARAMETER ...]
                        Specify regions to scan
  -b, --black-list [PARAMETER ...]
                        List of services to remove separated by comma. Launch script with -p to see services
  -w, --white-list [PARAMETER ...]
                        List of services to whitelist/scan separated by comma. Launch script with -p to see services
  --no-banner           Do not print banner
  -p, --print-services  List of all available services
  --unsafe-mode         Perform potentially destructive functions. Disabled by default.
  -v, --verbose         Verbosity level (-v for verbose, -vv for advanced, -vvv for debug)
```

## How does it works ? 

1. Take up to date list of availables regions inside AWS according to : https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html
Feel free to add some regions of your own after script created the file "regions.json". If not you wont be able to scan those regions as script wont let you

2. Script begin always by loading all services and functions available in SDK. So ti is always up to date (does not slow down tool either).

3. Perform equivalent of `aws sts get_caller_identity` to retrieve ARN (identity of the token)
Examples : 
arn:aws:sts::718896642544:assumed-role/web01/i-0d925034be5d2f45b
arn:aws:iam::718896642544:user/lucifer

4. From ARN we can know if we are a "user" or a "role".
So we will call the following function : 
User : 
get_account_authorization_details
get_user
list_attached_user_policies
list_user_policies
list_groups_for_user
list_group_policies

Role : 
get_role
list_attached_role_policies
list_role_policies

5. Once those information retrieved, it performs brute force on whatever endpoint you tell it to

## Commands cheat sheet

Launch scan on all services : 
```bash
python3 main.py
```

Spawn script without banner (bye bye sharky :/) : 
```bash
python3 main.py --no-banner
```

Show list of available services : 
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

## TBD : 

- [ ] Perform list_ before get_ or describe_
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
