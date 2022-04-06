import time
import paho.mqtt.client as paho
from paho import mqtt

SERVER = 3

if(SERVER == 0):
    host ="broker.mqttdashboard.com"
    port=1883
    userName = "testuser2022"
    password = "Testuser123"
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
    topic = "fevvf_route_tool"
    port = 8883
    password = "~m8Y[CgKnB"
topic = "fevvf_route_tool"
clientID = "clientId-xLODDl4VwO"
file_path = f"./request_input.txt"

def on_connect(client, userdata, flags, rc, properties=None):
    print("on connect %s." % rc)
def on_disconnect(client, userdata, flags, rc):
    print("client disconnected")
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    return None
def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    #print(message)
    f = open(file_path, "w")
    f.write(message)
    f.close()
    client.on_disconnect = on_disconnect
    client.disconnect()
    client.loop_stop()

if __name__ == '__main__':
    print("subscribe file")
    client = paho.Client(client_id=clientID, userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect
    if(SERVER != 0):
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(userName, password)
    client.connect(host, port)

    client.on_subscribe = on_subscribe
    client.subscribe(topic, qos=0)
    client.on_message = on_message
    client.loop_forever()
