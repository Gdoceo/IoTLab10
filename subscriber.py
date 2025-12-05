import time
import network
from machine import Pin
from umqtt.robust import MQTTClient

import temperature_upb2 as pb   

# -----------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------

BROKER_IP = "172.20.10.2"      # Raspberry Pi IP
TOPIC = b"temp/pico"           # Topic to listen to
PUB_IDENT = None               # MUST be None for subscriber
OUTPUT_PIN = "LED"             # Built-in LED on Pico W

# -----------------------------------------------------
# VALIDATION
# -----------------------------------------------------
def config_valid():
    # Subscriber must NOT have PUB_IDENT
    if PUB_IDENT is not None:
        return False
    return True

# -----------------------------------------------------
# WIFI CONNECT
# -----------------------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("Moes iPhone", "moe2drizzy")

    print("Connecting to WiFi...")
    for _ in range(20):
        if wlan.isconnected():
            print("Connected to WiFi")
            print("IP:", wlan.ifconfig()[0])
            return
        time.sleep(1)

    raise RuntimeError("WiFi failed to connect")

# -----------------------------------------------------
# GLOBAL STORAGE
# -----------------------------------------------------
latest = {}   # { publisher_id : (temperature, timestamp) }

def current_seconds():
    t = time.localtime()
    return t[3]*3600 + t[4]*60 + t[5]

# -----------------------------------------------------
# MQTT CALLBACK (NOW USING PROTOBUF)
# -----------------------------------------------------
def mqtt_callback(topic, msg_bytes):
    global latest

    try:
        # msg_bytes is the raw protobuf payload from MQTT
        m = pb.TemperaturemessageMessage()
        # depending on your uprotobuf version, it's either parse(...) or ParseFromString(...)
        m.parse(msg_bytes)   # <-- if this throws, try: m.ParseFromString(msg_bytes)

        # use _value according to the lab sheet
        pub_id = m.id._value
        temp   = m.temp._value

        # either use sender's time, or just local time
        # ts = m.time._value        # if you store seconds in the message
        ts = current_seconds()      # simpler: timestamp when we received it

        latest[pub_id] = (temp, ts)

        print("Received → {}: {:.2f}°C".format(pub_id, temp))

    except Exception as e:
        print("Error parsing protobuf:", e)

# -----------------------------------------------------
# SUBSCRIBER LOOP
# -----------------------------------------------------
def run_subscriber():
    led = Pin(OUTPUT_PIN, Pin.OUT)

    mqtt = MQTTClient("subscriber", BROKER_IP)
    mqtt.set_callback(mqtt_callback)
    mqtt.connect()
    mqtt.subscribe(TOPIC)

    print("Listening for messages on:", TOPIC)

    while True:
        mqtt.check_msg()        # receive messages

        now = current_seconds()
        temps = []

        # Keep only publishers from last 10 minutes
        for pid, (temp, ts) in list(latest.items()):
            if now - ts <= 600:
                temps.append(temp)
            else:
                del latest[pid]

        # Compute average temperature
        if temps:
            avg = sum(temps) / len(temps)
            print("Average temperature:", avg)

            if avg > 25:
                led.value(1)
            else:
                led.value(0)

        time.sleep(1)

# -----------------------------------------------------
# MAIN
# -----------------------------------------------------
def main():
    if not config_valid():
        print("❌ Invalid config! Subscriber cannot have PUB_IDENT set.")
        return

    connect_wifi()
    run_subscriber()

main()
