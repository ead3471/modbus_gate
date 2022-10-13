# Modbus Gate project

ModbusGate is a module designed for requesting and auto load data from Modbus RTU devices to the remote MySql database.

## Features

- Read data from Modbus RTU devices
- Store data in the local sqlite database
- Synchronize local database with remote MySQL database
- Read each connected device data manually via http requests
## Installation
 - install Python 2.7
 - init and activate virtual environment
 - run pip install -r requirements.txt
 - create folders logs/server and logs/sync
 - create tables in remote database(see resources/remote_tables_create.txt)
 - create file resources/meter_data.sqlite
 - create tables in local database(see resources/local_tables_create.txt)
