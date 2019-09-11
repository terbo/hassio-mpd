ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Install pre-requsites
RUN apk update

RUN apk add --no-cache openssh-server openssh-client python3 py3-pip
RUN apk add --no-cache cifs-utils alsa-utils alsa-plugins alsaconf
RUN apk add --no-cache mpd mpc ncmpc ympd espeak vim less bash egrep 
RUN apk add --no-cache less strace 
RUN apk add --no-cache --allow-untrusted apk/*apk

RUN pip3 install paho-mqtt python-mpd2 pyaml youtube-dl

#RUN apk add --no-cache pulseaudio pulseaudio-bash-completion
#RUN apk add --no-cache pulseaudio-utils pulseaudio-alsa alsa-plugins-pulse

# Copy data for add-on
COPY run.sh /
COPY etc/mpd.conf /etc
COPY mqtt.py /bin
COPY etc/server.yaml /etc
COPY bin/play* /bin

# Make executable
RUN chmod a+x /run.sh /bin/mqtt.py /bin/play*

# Let her rip...
CMD [ "/run.sh" ]
