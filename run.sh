#!/usr/bin/env bashio
set -e

bashio::log.info "MPD Server Starting..."

# SSH
#echo "Port 2222 >> /etc/ssh/sshd_config"

#/bin/mkdir -p /root/.ssh
#/bin/chmod -R 700 /root/.ssh

passwd -u root

#bashio::log.info "Copying SSH Configuration..."

#cp etc/ssh* /etc
#cp etc/moduli /etc
#cp etc/.bash* /root
#cp etc/.vimrc /root
#cp etc/.inputrc /root

#chmod 0600 /etc/ssh/ssh*

#/usr/sbin/sshd -p 2222

# MPD
mkdir -p /data/mp3
mkdir -p /data/video

# why do i have to do this?
chown root:audio /dev/snd/*

#bashio::log.info "Mounting CIFS filesystems..."

#mount //ftp/data/mp3   /data/mp3 -o username=data,password=pass
#mount //ftp/data/video /data/video -o username=data,password=pass
#mount //ftp//mpd /var/lib/mpd -o username=root,password=no

# can also have this as jq, but i like... files

cd /

(sleep 30 && nohup ympd & ) &

bashio::log.info "MPD Daemon starting .."

python3 /bin/mqtt.py &

mpd --no-daemon
