import ConfigParser
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.exceptions import ModbusIOException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.pdu import ExceptionResponse

import meter_registers

SCRIPT_WORK_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))
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
        filename=os.path.join(SCRIPT_WORK_DIR, 'logs', 'sync_runtime.log')
        , when='midnight', interval=1, backupCount=3,
        encoding='utf-8',
        delay=False)

    console_logger = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_logger.setFormatter(console_formatter)
    logging.basicConfig(
        filename=os.path.join(SCRIPT_WORK_DIR, "logs", datetime.today().strftime('%Y-%m-%d') + ".log")
        , format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s'
        , datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.getLogger('meter').addHandler(file_handler)
    logging.getLogger('meter').addHandler(console_logger)
    logging.getLogger('meter').setLevel(logging_level)


def get_meter_values():
    meter_registers_values = meter_registers.wattson_registers_map.copy()
    start_register_address = min(meter_registers_values["HOLDING"])
    registers_count = max(meter_registers_values["HOLDING"]) - start_register_address + 1

    meter_config = read_setup()
    assert isinstance(meter_config, ConfigParser.RawConfigParser)

    try:
        client = ModbusClient(method="rtu"
                              , port=meter_config.get("METER", "port")
                              , stopbits=meter_config.getint("METER", "stopbits")
                              , bytesize=meter_config.getint("METER", "bytesize")
                              , parity=meter_config.get("METER", "parity")
                              , baudrate=meter_config.getint("METER", "baudrate"))

        response = client.read_holding_registers(start_register_address - 1, registers_count,
                                                 unit=1)
        print(len(response.registers))

        if isinstance(response, ExceptionResponse) or isinstance(response, ModbusIOException):
            logger.error("Read modbus data error{}".format(response))
            return None

        decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=Endian.Big)

        for current_register in range(start_register_address, start_register_address + registers_count - 1, 2):

            if current_register in meter_registers_values['HOLDING'].keys():
                meter_registers_values['HOLDING'][current_register].value = decoder.decode_32bit_float()

    except BaseException as ex:
        logger.error("Process data error modbus data error{}".format(ex))
        return None

    finally:
        if client:
            client.close()

    return meter_registers_values


if __name__ == '__main__':
    data_from_meter = get_meter_values()
    for data in data_from_meter["HOLDING"].values():
        print(data)
