#!/usr/bin/expect -f

set timeout -1
set password [lindex $argv 0]

log_user 1
spawn rpk update -y

expect {
    -re "(?i)password.*:" {
        send "$password\r"
        exp_continue
    }
    eof
}
