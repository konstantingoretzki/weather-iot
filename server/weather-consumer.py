#!/usr/bin/env python3
import pika, sys, os
import json
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData

db_username = "user"
db_password = "pass"
db_ip_port  = "1.2.3.4:31433"
db_database = "master"
db_connection_string = f'mssql+pyodbc://{db_username}:{db_password}@{db_ip_port}/{db_database}?driver=SQL+Server' # 'sqlite:///weather_iot.db'

rabbitmq_server_ip = "1.2.3.4"
rabbitmq_server_port = 5672
rabbitmq_server_user = "user"
rabbitmq_server_pass = "pass"

def create_database(engine):
    metadata = MetaData()
    users = Table('weather_iot', metadata,
        Column('id', Integer, primary_key=True),
        Column('device_id', String),
        Column('timestamp', Integer),
        Column('temperature', Float),
        Column('pressure', Float),
        Column('humidity', Float)
        ) 
    # Creating the database table if it does not exists
    metadata.create_all(engine)

def reset_database(engine):
    print("Deleting table...")
    with engine.connect() as conn:
            conn.execute(f"DROP TABLE IF EXISTS weather_iot;")

    print("Createing table...")
    create_database(engine)

    print("Done!")

def main():
    # Creating to the database
    print("[*] Connecting to the database...")
    engine = create_engine(db_connection_string) 
    create_database(engine)
    print(" [+] Connected to the database.")

    # Connecting to the RabbitMQ server
    print("\n[*] Connecting to the RabbitMQ server...")
    credentials = pika.PlainCredentials(rabbitmq_server_user, rabbitmq_server_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_server_ip, rabbitmq_server_port,
                                        '/',
                                        credentials))

    print(" [+] Connected to the RabbitMQ server.")
    channel = connection.channel()
    channel.queue_declare(queue='weather')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body) 
        data = json.loads(body)

        # Write the dataset to the database
        with engine.connect() as conn:
            conn.execute(f"INSERT INTO weather_iot (device_id, timestamp, temperature, pressure, humidity) VALUES (?, ?, ?, ?, ?);", (data['device_id'], data['timestamp'], data['temperature'], data['pressure'], data['humidity']))

    channel.basic_consume(queue='weather', on_message_callback=callback, auto_ack=True)

    print('\n[*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)