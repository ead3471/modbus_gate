import ConfigParser
import logging
import os
from datetime import datetime, time
from logging.handlers import TimedRotatingFileHandler
import meter_registers
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from modbus_device import ModbusDevice, store_controllers_memory
from time import sleep

SCRIPT_ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))

setup_file = os.path.join(SCRIPT_ROOT_DIR, 'resources', 'config.ini')

logger = logging.getLogger("meter")


def read_setup():
    try:
        config_parser = ConfigParser.RawConfigParser()
        config_parser.readfp(open(setup_file))
        return config_parser
    except BaseException as ex:
        logging.error("Error read config file {}:{}".format(setup_file, ex))
        raise ex


def init_logger(logging_level=logging.DEBUG):
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(SCRIPT_ROOT_DIR, 'logs', 'sync_runtime.log')
        , when='midnight', interval=1, backupCount=3,
        encoding='utf-8',
        delay=False)

    console_logger = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_logger.setFormatter(console_formatter)
    logging.basicConfig(
        filename=os.path.join(SCRIPT_ROOT_DIR, "logs", datetime.today().strftime('%Y-%m-%d') + ".log")
        , format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s'
        , datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.getLogger('meter').addHandler(file_handler)
    logging.getLogger('meter').addHandler(console_logger)
    logging.getLogger('meter').setLevel(logging_level)

if __name__ == '__main__':
    meter_registers_map = meter_registers.wattson_registers_map
    start_register_address = min(meter_registers_map["HOLDING"])
    registers_count = max(meter_registers_map["HOLDING"]) - start_register_address + 2

    print(start_register_address, registers_count)

    meter_config = read_setup()
    assert isinstance(meter_config, ConfigParser.RawConfigParser)

    client = ModbusClient(method="rtu"
                              , port=meter_config.get("METER", "port")
                              , stopbits=meter_config.getint("METER", "stopbits")
                              , bytesize=meter_config.getint("METER", "bytesize")
                              , parity=meter_config.get("METER", "parity")
                              , baudrate=meter_config.getint("METER", "baudrate"))

    modbus_device = ModbusDevice("Wattson", 1, meter_registers_map, 1)
    modbus_device.add_read_data_request(start_register_address, registers_count, "HOLDING")
    while True:
        read_registers = modbus_device.operative_memory_requests[0].execute(client)
        modbus_device.update_memory_from_response(read_registers,start_register_address,3)
        store_controllers_memory([modbus_device])
        modbus_device.print_memory()
        sleep(3)