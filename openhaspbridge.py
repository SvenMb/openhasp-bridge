#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import paho.mqtt.client as mqtt
import time
import json
import colorsys

global lp

def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code "+str(rc))
    client.subscribe("hasp/#")
    for m in cfg["mqtt_pre"]:
        logging.info("subscribe: "+m+"/#")
        client.subscribe(m+"/#")
    client.subscribe(cfg["tuya_pre"]+"/#")
    client.subscribe("stat/#")
    client.subscribe("tele/#")

def on_message(client, userdata, message):
    pass # print("received message: " ,str(message.topic),str(message.payload.decode("utf-8")))

def on_haspLWT(mosq,obj,msg):
    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    logging.info("on_haspLWT: "+panel+" "+stat)
    if (stat!='online'):
        return
    logging.info(panel+" is online")
    # print status on panel
    client.publish(hasp_pre+"/"+panel+"/command/json",
                   '["page": 1,"id": 33,"w": 320,"x": 0,"y": 112,"obj": "label"]')
    client.publish(hasp_pre+"/"+panel+"/command/json",
                   '["page": 1,"id": 33,"text": "Server verbunden, es geht los..."]')
    # switch to page 2
    client.publish(hasp_pre+"/"+panel+"/command/page","2")
    # trigger tuya devices to send status
    for d in cfg["dev"].keys():
        if cfg["dev"][d]["type"] in ["tuya","tuyaw","tuyargb","tuyargbw"]:
            client.publish(tuya_pre+"/"+d+"/command","get-states")
            logging.info(tuya_pre+"/"+d+"/command->"+"get-states")
        elif cfg["dev"][d]["type"] == "sp1":
            client.publish("cmnd/"+d+'/POWER','')
            client.publish("cmnd/"+d+'/STATUS','8')
            client.publish("cmnd/"+d+'/TelePeriod','30')


def on_haspIDLE(mosq,obj,msg):
    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    logging.info("IDLE: "+panel+" "+stat)
    if (stat=='short'):
        # print(panel,"is short idle")
        client.publish("hasp/"+panel+"/command/backlight",'80')
    elif (stat=='long'):
        #  print(panel,"is long idle")
        client.publish("hasp/"+panel+"/command/backlight",'off')
    else:
        # print(panel," ",stat)
        client.publish("hasp/"+panel+"/command/backlight",'255')

def on_haspPAGE(mosq,obj,msg):
    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    logging.info("PAGE: "+panel+" "+stat)
    # remove this panel from lp (long_press)
    if stat!=cfg["hasp_details"][panel]["page"] and panel in lp.keys():
        logging.info("Details off: "+panel+" "+stat)
        lp.pop(panel,"")

def on_haspButton(mosq,obj,msg):
    global lp

    panel=msg.topic.split("/")[1]
    event=msg.topic.split("/")[3]
    stat=str(msg.payload.decode("utf-8"))
    logging.info("on_haspButton: "+panel+" "+event+" "+stat)
    j=json.loads(stat)
    if "event" in j.keys() and j["event"]=="down":
        button[panel+event]=time.time()
        return
    p=time.time()-button[panel+event]
    t=hasp_thing[panel][event]
    if p>0.8 and p<5 and json.loads(stat)["val"]==0:
        devtype=cfg["dev"][cfg["thing"][t]["dev"][0]]["type"]
        logging.info("long press "+str(p)+" "+t+" "+devtype)
        if devtype in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            lp[panel]=t
            # restore state
            client.publish(hasp_pre+"/"+panel+"/command/"+event+".val",1)
            # put thing name on details page
            client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["text"],t)
            # switch details for specific device
            if devtype=="tuyargbw":
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["rgb"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation_s"]+".hidden","false")
            elif devtype=="tuyargb":
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness_s"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp_s"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["rgb"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation_s"]+".hidden","false")
            elif devtype=="tuyaw":
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["brightness_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["color_temp_s"]+".hidden","false")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["rgb"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["cbrightness_s"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation"]+".hidden","true")
                client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp_details"][panel]["saturation_s"]+".hidden","true")

            # switch to details page
            client.publish(hasp_pre+"/"+panel+"/command/page",cfg["hasp_details"][panel]["page"])
            haspShow(t)
        return
    logging.info("short press "+str(p))
    # take care of special buttons, to get 'immediate' feedback
    #if cfg["hasp"][panel][event]["type"]=="sp1button":
    #    client.publish(hasp_pre+"/"+panel+"/command/"+cfg["hasp"][panel][event]["color"],cfg["hasp_color"][json.loads(stat)["val"]])
        # print("SP1: ",hasp_pre+"/"+panel+"/command/"+cfg["hasp"][panel][event]["color"],cfg["hasp_color"][json.loads(stat)["val"]])
    # tuya device
    val=json.loads(stat)["val"]
    if val==1:
        m="ON"
    else:
        m="OFF"
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("Tuya: "+d+" "+m)
            client.publish(tuya_pre+"/"+d+"/command",m)
    # Steckdose
        elif cfg["dev"][d]["type"] in ["sp1"]:
            logging.info("SP1: "+d+" "+str(json.loads(stat)["val"]))
            client.publish("cmnd/"+d+"/POWER",m)
        elif cfg["dev"][d]["type"] in ["slave"]:
            logging.info("Slave: "+d+" "+cfg["dev"][d]["mqtt"]+" "+str(json.loads(stat)["val"]))
            client.publish(cfg["dev"][d]["mqtt"],m)
        else:
            logging.info("unknown device type for: "+t)

def on_haspBright(mosq,obj,msg):
    global lp
    global things

    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    ev=json.loads(stat)["event"]
    if ev=="down":
        return
    t=lp[panel]
    logging.info("on_haspBright: "+panel+" "+t+" "+stat)

    # update things
    things[t]["brightness"]=str(json.loads(stat)["val"])
    # tuya device
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("change Brightness: "+d+" "+things[t]["brightness"])
            client.publish(tuya_pre+"/"+d+"/white_brightness_command",things[t]["brightness"])
        else:
            logging.info("unknown device type for: "+t)

def on_haspCTemp(mosq,obj,msg):
    global lp
    global things

    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    ev=json.loads(stat)["event"]
    if ev=="down":
        return
    t=lp[panel]
    logging.info("on_haspCTemp: "+panel+" "+t+" "+stat)

    # update things
    ctemp=int(int(json.loads(stat)["val"])/100*(things[t]["max_ctemp"]-things[t]["min_ctemp"])+things[t]["min_ctemp"])
    things[t]["color_temp"]=str(ctemp)
    # tuya device
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("change Color_Temp: "+d+" "+things[t]["color_temp"])
            client.publish(tuya_pre+"/"+d+"/color_temp_command",things[t]["color_temp"])
        else:
            logging.info("unknown device type for: "+t)

def on_haspRGB(mosq,obj,msg):
    global lp
    global things

    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    ev=json.loads(stat)["event"]
    if ev=="down":
        return
    t=lp[panel]
    logging.info("on_haspRGB: "+panel+" "+t+" "+stat)

    val=json.loads(stat)

    # update things
    (h,s,v)=colorsys.rgb_to_hsv(int(val["r"])/255,int(val["g"])/255,int(val["b"])/255)
    things[t]["hue"]=str(int(h*359))
    things[t]["cbrightness"]=str(int(s*100))
    things[t]["saturation"]=str(int(v*100))
    hsv=things[t]["hue"]+","+things[t]["saturation"]+","+things[t]["cbrightness"]
    # tuya device
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("change Color: "+d+" "+hsv)
            client.publish(tuya_pre+"/"+d+"/hsb_command",hsv)
        else:
            logging.info("unknown device type for: "+t)


def on_haspCBright(mosq,obj,msg):
    global lp
    global things

    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    ev=json.loads(stat)["event"]
    if ev=="down":
        return
    t=lp[panel]
    logging.info("on_haspCBright: "+panel+" "+t+" "+stat)

    # update things
    things[t]["cbrightness"]=str(json.loads(stat)["val"])
    hsv=things[t]["hue"]+","+things[t]["saturation"]+","+things[t]["cbrightness"]
    # tuya device
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("change CBrightness: "+d+" "+hsv)
            client.publish(tuya_pre+"/"+d+"/hsb_command",hsv)
        else:
            logging.info("unknown device type for: "+" "+t)

def on_haspSat(mosq,obj,msg):
    global lp
    global things

    panel=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    ev=json.loads(stat)["event"]
    if ev=="down":
        return
    t=lp[panel]
    logging.info("on_haspSat: "+panel+" "+t+" "+stat)

    # update things
    things[t]["saturation"]=str(json.loads(stat)["val"])
    hsv=things[t]["hue"]+","+things[t]["saturation"]+","+things[t]["cbrightness"]
    # tuya device
    for d in cfg["thing"][t]["dev"]:
        if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
            logging.info("change CBrightness: "+d+" "+hsv)
            client.publish(tuya_pre+"/"+d+"/hsb_command",hsv)
        else:
            logging.info("unknown device type for: "+t)




def haspShow(thing):
    global lp
    global things

    for p in lp.keys():
        if thing==lp[p]:
            logging.info("yes show "+p+"->"+thing+"!")
            client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["brightness"]+".val",things[thing]["brightness"])
            logging.info(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["brightness"]+".val"+" "+things[thing]["brightness"])
            ctemp=int((int(things[thing]["color_temp"])-things[thing]["min_ctemp"])/(things[thing]["max_ctemp"]-things[thing]["min_ctemp"])*100)
            client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["color_temp"]+".val",str(ctemp))

            # calculate rgb color
            (r,g,b)=colorsys.hsv_to_rgb(int(things[thing]["hue"])/360,int(things[thing]["saturation"])/100,int(things[thing]["cbrightness"])/100)
            logging.info('#{:02x}'.format(int(r*255))+'{:02x}'.format(int(g*255))+'{:02x}'.format(int(b*255)))
            client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["rgb"]+".color",'#{:02X}'.format(int(r*255))+'{:02X}'.format(int(g*255))+'{:02X}'.format(int(b*255)))
            client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["cbrightness"]+".val",things[thing]["cbrightness"])
            client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp_details"][p]["saturation"]+".val",things[thing]["saturation"])


    for p in cfg["thing"][thing]["panel"].keys():
        for b in cfg["thing"][thing]["panel"][p]:
            logging.info("show: "+thing+" "+cfg["hasp"][p][b]["type"])
            if cfg["hasp"][p][b]["type"] == "tuyabutton":
                if things[thing]["state"]=="ON":
                    client.publish(hasp_pre+"/"+p+"/command/"+b+".val","1")
                    if things[thing]["mode"]=="white":
                        client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],things[thing]["brightness"]+"%")
                    else:
                        client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],things[thing]["cbrightness"]+"%")
                elif things[thing]["state"]=="OFF":
                    client.publish(hasp_pre+"/"+p+"/command/"+b+".val","0")
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"]," ")
                else:
                    client.publish(hasp_pre+"/"+p+"/command/"+b+".val","0")
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],things[thing]["state"])
            elif cfg["hasp"][p][b]["type"] == "sp1button":
                if things[thing]["state"]=="ON":
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["color"],cfg["hasp_color"][1])
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],str(things[thing]["sp1"]["Power"])+" W")
                elif things[thing]["state"]=="OFF":
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["color"],cfg["hasp_color"][0])
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"]," ")
                else:
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["color"],cfg["hasp_color"][0])
                    client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],things[thing]["state"])
            elif cfg["hasp"][p][b]["type"] == "text":
                if "json" in cfg["hasp"][p][b]:
                    text=str(things[thing]["sp1"][cfg["hasp"][p][b]["json"]])
                else:
                    text=str(things[thing]["sp1"])
                # text=str(things[thing]["sp1"][cfg["hasp"][p][b]["json"]]   ["power_curr"])
                client.publish(hasp_pre+"/"+p+"/command/"+cfg["hasp"][p][b]["text"],cfg["hasp"][p][b]["pre"]+text+cfg["hasp"][p][b]["post"])



def on_TUYAstate(mosq,obj,msg):
    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYAstate: "+t+"->"+stat)
    if stat in ["ON","OFF","offline"]:
        things[t]["state"]=stat
    else:
        logging.info("E stat unknown: "+msg.topic+" "+stat)
        things[t]["state"]="unknown"
    haspShow(t)

def on_TUYAmode(mosq,obj,msg):
    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYAmode: "+t+"->"+stat)
    things[t]["mode"]=stat
    haspShow(t)

def on_TUYAbright(mosq,obj,msg):
    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYAbright: "+t+"->"+stat)
    things[t]["brightness"]=stat
    haspShow(t)

def on_TUYActemp(mosq,obj,msg):
    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYActemp: "+t+"->"+stat)
    things[t]["color_temp"]=stat
    haspShow(t)

def on_TUYAcbright(mosq,obj,msg):
    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYAcbright: "+t+"->"+stat)
    things[t]["cbrightness"]=stat
    haspShow(t)

def on_TUYAhsb(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("TUYAcbright: "+t+"->"+stat)
    hsb=stat.split(",")
    if len(hsb)>2:
        things[t]["cbrightness"]=hsb[2]
    things[t]["saturation"]=hsb[1]
    things[t]["hue"]=hsb[0]
    haspShow(t)

def on_SP1Power(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SP1Power: "+t+"->"+stat)
    if stat in ["ON","OFF","offline"]:
        things[t]["state"]=stat
    else:
        logging.info("stat unknown: "+msg.topic++stat)
        things[t]["state"]="unknown"
    haspShow(t)

def on_SP1Status8(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SP1Status8: "+t+"->"+stat)

    things[t]["sp1"]=json.loads(stat)["StatusSNS"]["ENERGY"]

    haspShow(t)


def on_SP1State(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SP1State: "+t+"->"+stat)

    j=json.loads(stat)
    if "POWER" in j.keys(): power=j["POWER"]
    elif "POWER1" in j.keys(): power=j["POWER1"]
    else: return
    if power in ["ON","OFF"]:
        things[t]["state"]=power
    else:
        logging.info("stat unknown: ",msg.topic,stat)
        things[t]["state"]="unknown"
    haspShow(t)


def on_SP1Sensor(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SP1Sensor: "+t+"->"+stat)

    things[t]["sp1"]=json.loads(stat)["ENERGY"]

    haspShow(t)


def on_SP1LWT(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SP1LWT: "+t+"->"+stat)

    if stat=="Offline":
        things[t]["state"]="offline"
        haspShow(t)

def on_Sensor(mosq,obj,msg):
    global things

    t=msg.topic.split("/")
    if t[0] == "tele":
        d=t[1]
    else:
        d=t[0]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_Sensor: "+t+"->"+stat)
    if "json" in cfg["dev"][cfg["thing"][t]["dev"][0]]:
        things[t]["sp1"]=json.loads(stat)[cfg["dev"][cfg["thing"][t]["dev"][0]]["json"]]
    else:
        things[t]["sp1"]=stat
    haspShow(t)

def on_SensorLWT(mosq,obj,msg):
    global things

    d=msg.topic.split("/")[1]
    stat=str(msg.payload.decode("utf-8"))
    t=dev_thing[d]
    logging.info("on_SensorLWT: "+t+"->"+stat)

    if stat=="Offline":
        things[t]["state"]="offline"
        haspShow(t)

def on_Connect(mosq,obj,msg):
    global connect

    c=connect[msg.topic]
    stat=str(msg.payload.decode("utf-8"))

    logging.info("Slave: "+cfg["connect"][c]["slave"]+" "+json.loads(stat)["state"])
    if cfg["connect"][c]["type"]=="hasp":
        client.publish(cfg["connect"][c]["slave"],json.loads(stat)["state"])



# --------------------------------
# Start
# --------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', required=False, default="openhasp_bridge.json")
parser.add_argument('-l', '--loglevel', required=False, default=None)
parser.add_argument('-f', '--logfile', required=False, default=None)
args, unknown = parser.parse_known_args()


with open(args.config) as cfg_file:
  cfg=json.load(cfg_file)


# logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
loglevel=args.loglevel
if loglevel is None:
    loglevel=cfg["debug"]["loglevel"]
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logfile=args.logfile
if logfile is None:
    if "logfile" in cfg["debug"].keys():
        logfile=cfg["debug"]["logfile"]
if logfile is None:
    logging.basicConfig(encoding='utf-8', level=numeric_level)
else:
    logging.basicConfig(filename=logfile,encoding='utf-8', level=numeric_level)

# print ("config:",cfg)

mqttBroker = cfg["mqtt_srv"]
mqttUser   = cfg["mqtt_user"]
mqttPass   = cfg["mqtt_pass"]
mqttName   = cfg["mqtt_name"]

tuya_pre   = cfg["tuya_pre"]
hasp_pre   = cfg["hasp_pre"]

things={}

for t in cfg["thing"].keys():
    logging.info("INIT: "+t)
    things[t]={}
    things[t]["state"]="offline"
    things[t]["mode"]="white"
    things[t]["brightness"]="100"
    things[t]["color_temp"]="300"
    things[t]["min_ctemp"]=154
    things[t]["max_ctemp"]=400
    things[t]["cbrightness"]="100"
    things[t]["saturation"]="100"
    things[t]["hue"]="0"
    things[t]["sp1"]={"Power":"0"}

logging.info("----")
logging.info("T: ",things)
logging.info("~~~~")

hasp_thing={}

for t in cfg["thing"].keys():
    for p in cfg["thing"][t]["panel"].keys():
        if p not in hasp_thing:
            hasp_thing[p]={}
        for b in cfg["thing"][t]["panel"][p]:
            hasp_thing[p][b]=t

logging.info("----")
logging.info("HD: ",hasp_thing)
logging.info("~~~~")

dev_thing={}

for t in cfg["thing"].keys():
    for d in cfg["thing"][t]["dev"]:
        if d not in dev_thing:
            dev_thing[d]={}
        dev_thing[d]=t

logging.info("----")
logging.info("DH: ",dev_thing)
logging.info("~~~~")

button={}

lp={}

# add parse command line !!!!

client = mqtt.Client(mqttName)

logger = logging.getLogger(__name__)
client.enable_logger(logger)

client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(username=mqttUser,password=mqttPass)

# register openHASP Panels LWT, Idle and page
for p in cfg["hasp"]:
    logging.info("on_haspLWT: "+hasp_pre+"/"+p+"/LWT")
    client.message_callback_add(hasp_pre+"/"+p+"/LWT", on_haspLWT)
    logging.info("on_haspIDLE: "+hasp_pre+"/"+p+"/state/idle")
    client.message_callback_add(hasp_pre+"/"+p+"/state/idle", on_haspIDLE)
    logging.info("on_haspPAGE: "+hasp_pre+"/"+p+"/state/idle")
    client.message_callback_add(hasp_pre+"/"+p+"/state/page", on_haspPAGE)

# register openHASP Panels details page
for p in cfg["hasp_details"]:
    client.message_callback_add(hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["brightness"], on_haspBright)
    logging.info("on_haspBright: "+hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["brightness"])
    client.message_callback_add(hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["color_temp"],on_haspCTemp)
    logging.info("on_haspCTemp: "+hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["color_temp"])
    client.message_callback_add(hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["rgb"],on_haspRGB)
    logging.info("on_haspRGB: "+hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["rgb"])
    client.message_callback_add(hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["cbrightness"],on_haspCBright)
    logging.info("on_haspCBright: "+hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["cbrightness"])
    client.message_callback_add(hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["saturation"],on_haspSat)
    logging.info("on_haspSat: "+hasp_pre+"/"+p+"/state/"+cfg["hasp_details"][p]["saturation"])


# register Panel Events for Buttons
for p in cfg["hasp"].keys():
    for e in cfg["hasp"][p].keys():
        logging.info("on_haspButton: "+hasp_pre+"/"+p+"/state/"+e)
        client.message_callback_add(hasp_pre+"/"+p+"/state/"+e, on_haspButton)

# register Device Events
# for d in cfg["dev"].keys():
for t in cfg["thing"].keys():
    d=cfg["thing"][t]["dev"][0]
    if cfg["dev"][d]["type"] in ["tuya","tuyargb","tuyargbw","tuyaw"]:
        logging.info("on_TUYAstate: "+tuya_pre+"/"+d+"/state")
        client.message_callback_add(tuya_pre+"/"+d+"/state", on_TUYAstate)
        client.message_callback_add(tuya_pre+"/"+d+"/status", on_TUYAstate)
        client.message_callback_add(tuya_pre+"/"+d+"/mode_state", on_TUYAmode)
        client.message_callback_add(tuya_pre+"/"+d+"/white_brightness_state", on_TUYAbright)
        client.message_callback_add(tuya_pre+"/"+d+"/color_temp_state", on_TUYActemp)
        client.message_callback_add(tuya_pre+"/"+d+"/color_brightness_state", on_TUYAcbright)
        client.message_callback_add(tuya_pre+"/"+d+"/hsb_state", on_TUYAhsb)
        client.message_callback_add(tuya_pre+"/"+d+"/hs_brightness_state", on_TUYAhsb)

    elif cfg["dev"][d]["type"] in ["sp1"]:
        logging.info("on_SP1state cmnd/"+d+"/state")
        client.message_callback_add("stat/"+d+"/POWER", on_SP1Power)
        client.message_callback_add("stat/"+d+"/POWER1", on_SP1Power)
        client.message_callback_add("stat/"+d+"/STATUS8", on_SP1Status8)
        client.message_callback_add("tele/"+d+"/STATE", on_SP1State)
        client.message_callback_add("tele/"+d+"/SENSOR", on_SP1Sensor)
        client.message_callback_add("tele/"+d+"/LWT", on_SP1LWT) # Offline/Online

    elif cfg["dev"][d]["type"] in ["sensor"]:
        if "mqtt" in cfg["dev"][d]:
            logging.info("on_SENSOR> "+cfg["dev"][d]["mqtt"])
            client.message_callback_add(cfg["dev"][d]["mqtt"], on_Sensor)
        else:
            logging.info("on_SENSOR> tele/"+d+"/SENSOR")
            client.message_callback_add("tele/"+d+"/SENSOR", on_Sensor)
            client.message_callback_add("tele/"+d+"/LWT", on_SensorLWT) # Offline/Online

    else:
        logging.info("unkown device type to register: "+cfg["dev"][d]["type"])


connect={}
for c in cfg["connect"].keys():
    client.message_callback_add(cfg["connect"][c]["master"], on_Connect)
    connect[cfg["connect"][c]["master"]]=c

logging.info("+++++++++++++++++++++++++++++++++++++++++")
logging.info(connect)

client.connect(mqttBroker) #
client.loop_forever()

# client.loop_start()
# time.sleep(30)
# client.loop_stop()
