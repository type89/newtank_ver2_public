import webiopi
import serial
import time
import RPi.GPIO as GPIO
import statistics
import os
import glob
from time import sleep
import subprocess
import datetime
from slack_sdk.webhook import WebhookClient
from slack_sdk import WebClient

webiopi.setDebug()

#ser = serial.Serial('/dev/arduino_uno', 9600)
#ser = serial.Serial('/dev/ttyAMA0', 9600)
ser = serial.Serial('/dev/ttyUSB0',9600)
#ser = serial.Serial('/dev/arduino_mega', 9600)
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# TRIGとECHOのGPIO番号
GPIO_TRIG = 2
GPIO_ECHO = 3
# ピン番号をGPIOで指定
GPIO.setmode(GPIO.BCM)
# TRIG_PINを出力, ECHO_PINを入力
GPIO.setup(GPIO_TRIG,GPIO.OUT)
GPIO.setup(GPIO_ECHO,GPIO.IN)
GPIO.setwarnings(False)

# 生の温度データを取得する関数
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# 温度データのみを取り出して返す関数
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def pulse_in(pin, value=GPIO.HIGH, timeout=0.5):
    start_time = time.time()
    not_value = (not value)

    # 前のパルスが終了するのを待つ
    while GPIO.input(pin) == value:
        if time.time() - start_time > timeout:
            return 0
    # パルスが始まるのを待つ
    while GPIO.input(pin) == not_value:
        if time.time() - start_time > timeout:
            return 0
    # パルス開始時刻を記録
    start = time.time()
    # パルスが終了するのを待つ
    while GPIO.input(pin) == value:
        if time.time() - start_time > timeout:
            return 0
    # パルス終了時刻を記録
    end = time.time()
    return end - start


def get_distance(trig, echo, temp):
    # 出力を初期化
    GPIO.output(trig, GPIO.LOW)
    time.sleep(0.3)
    # 出力(10us以上待つ)
    GPIO.output(trig, GPIO.HIGH)
    time.sleep(0.000011)
    # 出力停止
    GPIO.output(trig, GPIO.LOW)
    # echo からパルスを取得
    dur = pulse_in(echo, GPIO.HIGH, 0.5)
    # ( パルス時間 x 331.50 + 0.61 * 温度 ) x (単位をcmに変換) x 往復
    # return dur * (331.50 + 0.61 * temp) * 100 / 2
    return dur * (331.50 + 0.61 * temp) * 50


def range_find():
  #print("calc...")
  temp = read_temp()
  temp_fm = '{:.1f}'.format(temp)
  #print("Temprature = " + str('{:.1f}'.format(temp)) + 'C')
  dislist = []
  i=0
  while(i<5):
      distance = get_distance(GPIO_TRIG, GPIO_ECHO,temp)
      dislist.append(distance)
      i+=1
  #for dis in dislist:
  #  print(dis)
  median = statistics.median(dislist)
  #print("Distance = " + str('{:.1f}'.format(median)) + 'cm')
  dist_fm = '{:.1f}'.format(median)
  url="WebhookのURL"
  webhook = WebhookClient(url)
  webhook.send(text="Newtank Range Finder\nDistance = " + dist_fm + "cm\nTemprature = " + temp_fm + "C")

  return

def Get_photo():
  filepath = '/home/pi/work/webiopi/jpg/'
  args = 'rm -f ' + filepath + '*.jpg'
  subprocess.Popen(args, shell=True)

  url="WebhookのURL"
  webhook = WebhookClient(url)
  webhook.send(text="Newtank Camera\nNow shooting...")
  now = datetime.datetime.now()
  now = "{0:%Y-%m-%d-%H:%M:%S}".format(now)
  filename = now + '.jpg'
  streamurl = ' http://localhost:8080/?action=snapshot'
  args = 'wget -O ' + filepath + filename + streamurl
  subprocess.Popen(args, shell=True)
  sleep(2)
  SLACK_BOT_TOKEN='トークン'
  client = WebClient(SLACK_BOT_TOKEN)

  client.files_upload(
  	channels = 'チャンネルID',
        title = now,
        file = filepath + filename,
        initial_comment = now + " file uploaded from Recon Tank",
  )
  sleep(2)
  return

def room_lighton():
  args = 'python3 /home/pi/work/webiopi/irrp.py -p -g17 -f /home/pi/work/webiopi/codes light:on'
  subprocess.Popen(args, shell=True)
  return

def room_lightoff():
  args = 'python3 /home/pi/work/webiopi/irrp.py -p -g17 -f /home/pi/work/webiopi/codes light:off'
  subprocess.Popen(args, shell=True)
  return

@webiopi.macro
def serial_send(arg):
    arg_byte=arg.encode('utf-8')
    ser.write(arg_byte)
    return

@webiopi.macro
def range_finder():
    range_find()
    return

@webiopi.macro
def shoot():
    Get_photo()
    return

@webiopi.macro
def room_lon():
    room_lighton()
    return

@webiopi.macro
def room_loff():
    room_lightoff()
    return  
