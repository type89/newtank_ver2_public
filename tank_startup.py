from slack_sdk.webhook import WebhookClient
import subprocess
import time
import re

ip = ''
maxretry = 10
i = 0
while len(ip) == 0 and i < maxretry:
    i = i +1
    ip = subprocess.check_output('ip a show wlan0 | grep "inet " | cut -f6 -d " " | cut -d "/" -f1', shell=True)
    #print(type(ip))
    print('Try ==> ' + str(i) )
    time.sleep(2)

ip = ip.decode().rstrip() 
print(ip)


file_name = "/home/pi/work/webiopi/rctank.html"

with open(file_name, encoding="utf-8") as f:
    data_lines = f.read()


data_lines = re.sub(r'192.168.*:8080', str(ip) + ":8080", data_lines)
print(data_lines)
# 同じファイル名で保存
with open(file_name, mode="w", encoding="utf-8") as f:
    f.write(data_lines)

subprocess.Popen("sudo systemctl start webiopi", shell=True)
time.sleep(20)

if len(ip) != 0 :
    arg = "New Tank console\n" + "http://" + ip + ":8000"
else:
    arg = "IP address is unknown"

url="WebhookのURL"
webhook = WebhookClient(url)
webhook.send(text=arg)
