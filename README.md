This is just an MPD music server container for Home Assistant running on Hassbian.
It mounts my media collection over samba/cifs, but any other method could be used.

It also includes a python MQTT client that can interface with MPD, or for my uses
use espeak for different notifications until I find another TTS solution, and also
interface with a custom compiled headless VLC server. I got the idea for the VLC
server from another addon, but it failed to include GnuTLS in the build, and I wanted
to be able to forward the audio from youtube videos to other systems.

to be continued... 
