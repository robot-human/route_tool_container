import os
import time
from sys import getsizeof
import paho.mqtt.client as paho
from paho import mqtt
import paho.mqtt.publish as publish
from time import sleep

SERVER = 0
topic = "fevvf/fevbii"
clientID = "clientId-xMODDl314VwR-pedro-p"
file_path = f'./config.ini'
QOS = 2
KEEPALIVE=60

if(SERVER == 0):
    host ="broker.mqttdashboard.com"
    port=1883
elif(SERVER == 1):
    host = "fcf1be1bbd2a44cf9bb7bd7c50f89a7d.s1.eu.hivemq.cloud"
    port = 8883    
    userName = "testuser2022"
    password = "Testuser123"
elif(SERVER == 2):
    host = "34.130.9.249"
    userName = "beth"
    password = "~m8Y[CgKnB"
    port = 1883
elif(SERVER == 3):
    host = "e6238d8846024198be84bfb8255304bd.s1.eu.hivemq.cloud"
    userName = "fev_vf"
    port = 8883
    password = "~m8Y[CgKnB"

output_files_path = f'./gpx/'
output_files = os.listdir(output_files_path)

def on_connect(client, userdata, flags, rc, properties=None):
    print("on connect %s." % rc)
def on_disconnect(client, userdata, flags, rc):
    print("client disconnected")
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))


if __name__ == '__main__':
    print("start sending files")
    client = paho.Client(client_id=clientID, userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect
    if(SERVER != 0):
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(userName, password)
    client.connect(host, port, keepalive=KEEPALIVE)
    client.on_subscribe = on_subscribe
    client.subscribe(topic, qos=QOS)
    client.on_publish = on_publish
    
    n_files = 0
    for file_path in output_files:
        n_files += 1
    
    print(f"Number of files {n_files}")
    #client.publish(topic, payload=f"Hello GUI am sending {n_files} files", qos=QOS)
    publish.single(topic, payload=f"Hello GUI am sending {n_files} files", qos=QOS, retain=False, hostname=host,port=port, client_id=clientID, keepalive=KEEPALIVE, will=None, auth=None, tls=None,protocol=paho.MQTTv5, transport="tcp")
    for name in output_files:
        print(name)
        file_name_path = output_files_path+name
        #client.publish(topic, payload=f"{name}", qos=QOS)
        publish.single(topic, payload=f"{name}", qos=QOS, retain=False, hostname=host,port=port, client_id=clientID, keepalive=KEEPALIVE, will=None, auth=None, tls=None,protocol=paho.MQTTv5, transport="tcp")
        sleep(0.2)
        f = open(file_name_path, "r")
        content = f.read()
        print(getsizeof(content)/1000, " kbts")
        #client.publish(topic, payload=content, qos=QOS)
        publish.single(topic, payload=content, qos=QOS, retain=False, hostname=host,port=port, client_id=clientID, keepalive=KEEPALIVE, will=None, auth=None, tls=None,protocol=paho.MQTTv5, transport="tcp")
        sleep(0.2)
        f.close()
        print(f"{name} closed")     
    
    client.on_disconnect = on_disconnect
    client.disconnect()
    