#!/bin/sh
 
set -e
 
pull=0 # on/off guix pull
base_dir=/var/tmp/dima12101/sbn_wsgi
sbn_profile=$base_dir/sbn
guix_profile=$base_dir/guix
tmp_out_dir=/tmp/wsgi/out
sbn_wsgi_server=~/subordination_project/WEB-SBN-Python/wsgi_sbn/main.py                   
wsgi_app=examples.simple_app:app
nodes="g1
g2
g3
g4
g5
g6"
 
check_all() {
    # Access to all exe files
    for i in $nodes
    do
        echo -n $i
        ssh dima12101@$i \
            'GUIX_PROFILE='$sbn_profile'
             . $GUIX_PROFILE/etc/profile
             realpath $(which sbnd)'
    done
}
 
build_all() {
    root="~/subordination_project/subordination"
    rsync -acv --exclude=.git --exclude=build --exclude='*~' --delete $PWD/ dima12101@g1:$root/
    
    # Installing dependencies and building the project
    for i in $nodes
    do
        ssh dima12101@$i \
            "set -ex
             if test $pull = 1 || ! test -e $guix_profile/bin/guix
             then
                 mkdir -p $base_dir
                 guix pull --channels=$root/guix/channels.scm --profile=$guix_profile
             fi
             sed 's/@name@/subordination/g;s/@version@/0.0.0/g;s|@source_root@|$root|g' < $root/guix/package.scm.in > /tmp/sbn.scm
             mkdir -p $base_dir
             $guix_profile/bin/guix package -f /tmp/sbn.scm -i openmpi tcpdump --profile=$sbn_profile --substitute-urls='http://g1:55555 https://guix.cmmshq.ru'" &
        test "$i" = "g1" && wait
    done
    wait
    check_all
}

sbnd_kill() {
    i="$1"
    echo "Kill sbnd on $i"
    set +e
    ssh -n dima12101@$i 'pkill -9 sbnd; pkill -9 sbnc; pkill -9 sbn-python3'
    set -e
}

run() {  
    output_dir=out
    mkdir -p $output_dir

    # Kill all processes on each node
    for i in $nodes
    do
        sbnd_kill $i
    done

    # Running sbnd on each node
    for i in $nodes
    do
        echo "Start sbnd on $i"
        ssh -n dima12101@$i \
            'GUIX_PROFILE='$sbn_profile'
            . $GUIX_PROFILE/etc/profile
            rm -f '$base_dir'/transactions '$base_dir'/10.2.* '$base_dir'/sbnd.log
            cat > sbnd.properties << EOF
#remote.min-input-buffer-size=1703936
#remote.min-output-buffer-size=1703936
#process.min-input-buffer-size=13631488
#process.min-output-buffer-size=13631488
#unix.min-input-buffer-size=65536
#unix.min-output-buffer-size=65536
discoverer.fanout=99999
network.allowed-interface-addresses=10.2.0.0/24
process.allow-root=1
remote.connection-timeout=7s
remote.max-connection-attempts=1
discoverer.scan-interval=30s
network.interface-update-interval=1h
transactions.directory='$base_dir'
discoverer.profile=0
discoverer.max-attempts=10
discoverer.cache-directory='$base_dir' 
EOF
            nohup sbnd config=sbnd.properties < /dev/null > '$base_dir'/sbnd.log 2>&1 &
            '
    done
    sleep 1

    # Creating a folder for out on each node
    for i in $nodes
    do
        ssh -n dima12101@$i 'mkdir -p '$tmp_out_dir'; rm -rf '$tmp_out_dir'/*'
    done
 
            
    ssh dima12101@g1 '
        GUIX_PROFILE='$sbn_profile'
        . $GUIX_PROFILE/etc/profile
        sbnc select -t node -o rec
        cd /tmp/out
        cat > /home/dima12101/sbnc.properties << EOF
local.num-upstream-threads=1
local.num-downstream-threads=0
#remote.min-input-buffer-size=8388608
#remote.min-output-buffer-size=8388608
EOF
        export SBN_CONFIG=/home/dima12101/sbnc.properties
        export SBN_TEST_SLEEP_FOR=10
        sbnc sbn-python3 '$sbn_wsgi_server' '$wsgi_app'
        ' &

    set -e
    echo "Press ENTER to stop!"
    read answer

    # Kill all processes on each node
    for i in $nodes
    do
        sbnd_kill $i &
    done
    wait
 
    # Uploading outs
    echo "rsync"
    for i in $nodes
    do
        ssh -n dima12101@$i 'cp '$base_dir'/sbnd.log '$tmp_out_dir'/sbnd-'$(hostname)'.log'
        rsync -a dima12101@$i:$tmp_out_dir/ $output_dir/
    done
}
 
# Pipeline
build_all
run
