#!/usr/bin/env python3

from sys import argv
import time
import pika
import json

## change me
# general
device_id = "<fill-me>"
loop_interval_seconds = 5
temperature_offset = -8 # adjust or set to zero if not needed
# RabbitMQ
rabbit_mq_user = "<fill-me>"
rabbit_mq_password = "<fill-me>"
rabbit_mq_server = "XXX.XXX.XXX.XXX"
# Airrohr Webserver
web_server = "http://XXX.XXX.XXX.XXX"
web_auth_token = "<fill-me>"

# sensor read inspired by
# https://github.com/pimoroni/bme680-python/blob/master/examples/read-all.py

def init_i2c():
    global sensor
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # These oversampling settings can be tweaked to
    # change the balance between accuracy and noise in
    # the data.

    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)

    # calibrate temperature offset
    # https://github.com/pimoroni/bme680-python/pull/13/files
    sensor.set_temp_offset(temperature_offset)


def read_i2c():
    if sensor.get_sensor_data():
        temperature = "{0:.2f}".format(sensor.data.temperature)
        pressure = "{0:.2f}".format(sensor.data.pressure)
        humidity = "{0:.2f}".format(sensor.data.humidity)
        return temperature, pressure, humidity


def send_rabbit(msg):
    credentials = pika.PlainCredentials(rabbit_mq_user, rabbit_mq_password)
    parameters = pika.ConnectionParameters(rabbit_mq_server, 5672, "/", credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue="weather")
    channel.basic_publish(exchange="", routing_key="weather", body=msg)
    connection.close()


def read_web():
    response = requests.get(web_server + '/data.json', headers=headers)
    json_response = response.json()

    temperature = pressure = humidity = None
    for sensor in json_response["sensordatavalues"]:
        if sensor["value_type"] == "BME280_temperature":
            temperature = sensor["value"]
        elif sensor["value_type"] == "BME280_pressure":
            pressure = sensor["value"]
        elif sensor["value_type"] == "BME280_humidity":
            humidity = sensor["value"]

    return temperature, pressure, humidity


if __name__ == "__main__":
    print("weather-producer.py - display and send temperature, pressure and humidity to RabbitMQ.\n")

    # check if parameter is passed
    if len(argv) != 2:
        print("Please specify which method should be used for reaching the sensors.")
        print("Available solutions are 'airrohr' for using the airrohr data from the")
        print("webinterface and 'i2c' for directly reading from the sensors (bme680).")
        exit()

    # configure function calls depending on the passed argument 
    if argv[1] == "airrohr":
        import requests
        global headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'DNT': '1',
            'Authorization': web_auth_token,
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        get_data = read_web
    elif argv[1] == "i2c":
        import bme680
        init_i2c()
        get_data = read_i2c

    # fetch and send data in loop
    try:
        while True:
            temperature = pressure = humidity = None
            temperature, pressure, humidity = get_data()

            if (temperature != None) and (pressure != None) and (humidity != None):
                json_str = json.dumps(
                    {
                        "timestamp": int(time.time()),
                        "device_id": device_id,
                        "temperature": temperature,
                        "pressure": pressure,
                        "humidity": humidity,
                    }
                )
                print(json_str)
                send_rabbit(json_str)
            time.sleep(loop_interval_seconds)

    except KeyboardInterrupt:
        pass
