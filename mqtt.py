#!/usr/bin/env python3

version     = '0.11.5'
__version__ = tuple(map(int, version.split('.')))
CONFIG_FILE='/etc/server.yaml'

import os, sys, logging, socket
from logging import info, error, debug
logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(funcName)s %(threadName)s(%(lineno)d) -%(levelno)s: %(message)s')

import time, re, tempfile
import json, yaml
import paho.mqtt.client as mqtt
from subprocess import run

from mpd.base import MPDClient as MPD
from types import SimpleNamespace

user_opts = {}

def mqtt_on_message(client, userdata, msg):
  global user_opts
  topic = msg.topic
  payload = str(msg.payload.decode())
 
  try:
    user_opts = json.loads(payload)
    if not 'msg' in user_opts:
      client.publish(cfg.mqtt.status, "ERROR in JSON", qos=cfg.mqtt.qos, retain=cfg.mqtt.retain)
      return
    msg = user_opts['msg']
    del user_opts['msg']

    debug("TOPIC: '%s' MSG: '%s' OPTIONS: '%s'" % (topic, msg, user_opts))
  except:
    debug("TOPIC: '%s' MSG: '%s'" % (topic, payload))
    msg = payload 
  
  try:
    if topic == 'tts/say':
      speak(msg)
    elif topic.startswith('sms/in/'):
      phone = topic.split('/')[2]
      debug('SMS from phone %s' % phone)
      speak(txtmsg(phone,msg))
    elif topic.startswith('mpd/cmd/'):
      cmd = topic.split('/')[2]
      debug('cmd: %s' % cmd)
      mpd_cmd(cmd, payload)
    elif topic == 'tts/play':
      playsnd(msg)
    elif topic == 'vlc/play':
      playvlc(msg)
    elif topic == 'vlc/stop':
      stopvlc()
  except Exception as e:
      debug('Error parsing topic "%s" for message "%s": %s' % (topic, payload, e))

def stopvlc(voice=True):
  os.system('killall -9 youtube-dl vlc')
  if voice: speak('stopping vlc')

def playvlc(uri):
  stopvlc(0)

  speak('playing video')
  if mpd_connect()['state'] == 'play':
    mpd.pause()

  run('%s %s' % ('/bin/play', uri))

def mpd_connect():
  status = False
  try:
    status = mpd.status()
  except:
    mpd.connect(cfg.mpd.host,cfg.mpd.port,timeout=cfg.mpd.timeout)
    status = mpd.status()
  finally:
    if status:
      debug('MPD Status: %s' % (status['state']))
      return status
    else:
      return []

def mpd_cmd(cmd, args=''):
  mpd_connect()
  
  if cmd not in mpd.commands():
    debug('Invalid command: %s' % cmd)
    return

  debug("Executing mpd.%s(%s)" % (cmd, args))

  ret = eval('mpd.%s(%s)' % (cmd, args))

  if ret:
    debug('Return: %s' % ret)

def txtmsg(phone, msg):
  res = re.match(r'^([^-]*)-([^\d]*)(\d*)(.*)',msg)
   
  if(res):
    out = res.groups()
    sender = out[0].strip()
    msg = out[1].strip()
    num = out[2].strip()
     
    msg = 'SMS from %s: %s' % (phone, msg)
    
    info(msg) #"SMS on %s: '%s' (%s): %s" % (phone, sender, num, msg))
  else:
    # need to parse last part or something, so its not just a bunch of gunk
    mesg = ' '.join(msg.split(' ')[1:])
    msg = "Text Message on %s: %s" % (phone, mesg)
    info(msg)
  
  return msg

def speak(msg):
  info("Speaking '%s'" % msg)
  playing = 0

  # make numbers easier to understand
  msg = re.sub(r'([0-9])',r'\1 ',msg)

  try:
    status = mpd_connect()
   
    if status['state'] == 'play':
      playing = 1   
      mpd.pause()
      vol = int(status['volume'])
      nvol = int(vol * cfg.mpd.reduce)
      info(nvol)
      mpd.setvol(nvol)
      time.sleep(.8)
  except:
    pass
  
  tmpfile = tempfile.NamedTemporaryFile('w', dir='/tmp')
  
  debug('Using %s tempfile' % tmpfile.name)
  
  with open(tmpfile.name,'w') as out:
    out.write(msg)

  espeak(tmpfile.name)

  if playing:
    time.sleep(.5)
    mpd.play()
    mpd.setvol(vol)
    mpd.disconnect()
    debug('Disconnected from MPD')

def espeak(tmpfile):
  global user_opts
  
  opts = ''
  
  for key in _cfg['espeak'].keys():
    opts += ' -%s %s ' % (key, _cfg['espeak'][key])
  if len(user_opts):
    for key in user_opts.keys():
      if key in _cfg['espeak']:
        opts += ' -%s %s ' % (key, user_opts[key])
    user_opts={}

  debug('Espeak Options: "%s"' % opts)
  
  os.system('espeak %s -f %s --stdout | aplay -D sysdefault:CARD=Audio' % (opts, tmpfile))

def mqtt_on_connect(client, userdata, flags, rc):
  if rc == 0:
    info("mqtt connected")

    for topic in cfg.mqtt.topics:
      client.subscribe(topic, qos=cfg.mqtt.qos)

    client.publish(cfg.mqtt.status, "MQTT MPD/TTS Server %s Initializing" % version, qos=cfg.mqtt.qos, retain=cfg.mqtt.retain)
  else:
    info("mqtt connection failed")

def mqtt_init():
  protocol = mqtt.MQTTv311

  client = mqtt.Client(client_id=version, clean_session=True, protocol=protocol)

  client.on_connect = mqtt_on_connect
  client.on_message = mqtt_on_message

  return client

def main():
  try:
    client.connect(cfg.mqtt.host, cfg.mqtt.port, cfg.mqtt.keepalive)
  except socket.error as err:
    error(err)

  debug("Connected to MQTT, initiating main loop")
  client.loop_start()

  try:
    while True:
      time.sleep(10)
  except KeyboardInterrupt:
    debug("KeyboardInterrupt")
  finally:
    client.publish(cfg.mqtt.status, "MQTT MPD/TTS Server Exiting", qos=cfg.mqtt.qos, retain=cfg.mqtt.retain)
    time.sleep(1)
    client.disconnect()

if __name__ == "__main__":
  try:
    _cfg = yaml.load(open(CONFIG_FILE,'r').read())
    
    cfg = SimpleNamespace(**_cfg)
    cfg.mpd = SimpleNamespace(**_cfg['mpd'])
    cfg.mqtt = SimpleNamespace(**_cfg['mqtt'])
    cfg.espeak = SimpleNamespace(**_cfg['espeak'])
  
  except Exception as e:
    error('Unable to load configuration - %s' % e)
    sys.exit(1)
  
  while True:
    try:
      mpd = MPD(use_unicode=True)
      client = mqtt_init()
      main()
    except Exception as e:
      debug(e)
      error('Restarting in 10 seconds...')
    
    time.sleep(10)
