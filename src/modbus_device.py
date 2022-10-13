import meter_registers
from meter_registers import *
import sqlite3 as sqlite
from sqlite3 import Row
import time
import os
from datetime import timedelta, datetime
import logging
from modbus_registers import ModbusRequest
from meter_registers import wattson_registers_map

SCRIPT_WORK_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

controllers_db = os.path.join(SCRIPT_WORK_DIR, "resources", "meter_data.sqlite")
store_values_table = "realtime_values"
controllers_table = "controllers"

logger = logging.getLogger("boilers")


def remove_old_records(store_deep, remove_logger=logger):
    now_timestamp = time.mktime(datetime.now().timetuple())
    oldest_record_timestamp = int(now_timestamp - store_deep)
    try:
        con = sqlite.connect(controllers_db)
        cursor = con.cursor()
        sql = "DELETE FROM {} WHERE timestamp < {}".format(
            store_values_table, oldest_record_timestamp
        )

        remove_logger.debug(
            "Remove local store records older when {}".format(
                datetime.fromtimestamp(oldest_record_timestamp)
            )
        )
        cursor.execute(sql)
        removed_rows_count = cursor.rowcount
        con.commit()
        remove_logger.debug("Removed {} rows".format(removed_rows_count))
    except BaseException as ex:
        remove_logger.error("Remove old records error {}".format(ex))
    finally:
        if con:
            con.close()


def store_controllers_memory(controllers_list):
    # (List[ProlonController]):->None
    try:
        con = sqlite.connect(controllers_db)
        cursor = con.cursor()
        sql = (
            "INSERT OR IGNORE INTO "
            + store_values_table
            + "(controller_id,register_address,timestamp,value,register_type) VALUES (?,?,?,?,?) "
        )

        for controller in controllers_list:
            assert isinstance(controller, ModbusDevice)
            for (
                reg_type,
                controller_values,
            ) in controller.operative_values_memory.items():
                for register_address, controller_value in controller_values.items():
                    assert isinstance(controller_value, ControllerValue)
                    cursor.execute(
                        sql,
                        (
                            controller.internal_id,
                            register_address,
                            time.mktime(controller_value.timestamp.timetuple()),
                            controller_value.value,
                            ModbusDevice.register_types[reg_type],
                        ),
                    )

        con.commit()
    finally:
        if con:
            con.close()


def get_controllers_in_system():
    controllers = {
        1: ModbusDevice(
            name="WattsOn meter", uid=1, modbus_map=wattson_registers_map, internal_id=1
        )
    }

    meter_registers_map = meter_registers.wattson_registers_map
    start_register_address = min(meter_registers_map["HOLDING"])
    registers_count = max(meter_registers_map["HOLDING"]) - start_register_address + 2

    print(start_register_address, registers_count)
    for controller in controllers.values():
        controller.add_read_data_request(
            start_register_address, registers_count, "HOLDING"
        )

    return controllers


def get_data_stored_after(controllers_update_info, config, logger=logger):
    con = sqlite.connect(controllers_db)
    con.row_factory = Row
    cursor = con.cursor()

    result = {}
    for controller_id, timestamp in controllers_update_info.items():
        assert isinstance(timestamp, datetime)
        try:
            logger.debug(
                "Get data for controller {} after {}".format(controller_id, timestamp)
            )
            sql = (
                "SELECT * FROM "
                + store_values_table
                + " WHERE controller_id = "
                + str(controller_id)
                + " AND timestamp>"
                + str(time.mktime(timestamp.timetuple()))
                + " ORDER BY timestamp ASC LIMIT 10000"
            )
            cursor.execute(sql)
            records = cursor.fetchall()

            result[controller_id] = []
            for record in records:
                result[controller_id].append(
                    {
                        "timestamp": timestamp.fromtimestamp(record["timestamp"]),
                        "register_number": record["register_address"],
                        "register_type": record["register_type"],
                        "value": record["value"],
                    }
                )
        except BaseException as ex:
            logger.error(
                "Error at get data stored after {} for controller {}:{}".format(
                    timestamp, controller_id, ex
                )
            )
    cursor.close()
    con.close()
    return result


class ModbusDevice:
    register_types = {"HOLDING": 3, "INPUT": 4}

    def __init__(self, name, uid, modbus_map, internal_id=1):
        self.name = name  # type:str
        self.uid = uid  # type:int
        self.modbus_map = modbus_map
        self.operative_values_memory = {
            "HOLDING": {},
            "INPUT": {},
        }  # map of regular updated values
        self.last_update = datetime.now()
        self.last_update_status = "OK"
        self.operative_memory_requests = (
            []
        )  # list of requests for operative_values_memory
        self.internal_id = internal_id
        if len(self.modbus_map["INPUT"].keys()) > 0:
            self.max_input_register_number = max(self.modbus_map["INPUT"].keys())
        else:
            self.max_input_register_number = 0

        if len(self.modbus_map["HOLDING"].keys()) > 0:
            self.max_holding_register_number = max(self.modbus_map["HOLDING"].keys())
        else:
            self.max_holding_register_number = 0

    def decode_modbus_responce_to_json(self, request, responce_registers):
        request_type = "HOLDING"
        if request.fc == 4:
            request_type = "INPUT"

        result = {}
        register_number = request.start
        for register in responce_registers:
            if register_number in self.modbus_map[request_type]:
                result[register_number] = (
                    self.modbus_map[request_type][register_number]
                    .get_value_from_register(register)
                    .to_json()
                )
            register_number += 1

        return result

    # def add_read_holding_regs_request(self, start_register, registers_count):
    # if stop_register - start_register > 125:
    # raise ValueError('Stop-start difference is to big!(>125)')
    # else:
    # self.operative_memory_requests.append(
    #     ModbusRequest.create_read_hold_regs_req(start_register, registers_count, self.uid))
    # for register in range(start_register, start_register + registers_count - 1):
    #     if register in self.modbus_map["HOLDING"]:
    #         modbus_register = self.modbus_map["HOLDING"][register]  # type: ProlonRegister
    #         self.operative_values_memory["HOLDING"][modbus_register.register_number] = modbus_register.value

    def add_read_data_request(self, start_register, count, reg_type):
        # if stop_register - start_register > 125:
        # raise ValueError('Stop-start difference is to big!(>125)')
        # else:
        if reg_type == "INPUT":
            self.operative_memory_requests.append(
                ModbusRequest.create_read_input_regs_req(
                    start_register, count, self.uid
                )
            )
        else:
            self.operative_memory_requests.append(
                ModbusRequest.create_read_hold_regs_req(start_register, count, self.uid)
            )
        for register in range(start_register, count + start_register):
            if register in self.modbus_map[reg_type]:
                modbus_register = self.modbus_map[reg_type][register]
                assert isinstance(modbus_register, ModbusDeviceFloat32Value)
                default_value = ControllerValue.from_modbus_device_value(
                    modbus_register
                )
                self.operative_values_memory[reg_type][
                    modbus_register.address
                ] = default_value

    def update_memory_from_response(
        self, responce_registers, start_register, responce_fnc
    ):
        reg_types = "INPUT"
        if responce_fnc == 3:
            reg_types = "HOLDING"

        self.last_update = datetime.now()

        for response_register_number in range(len(responce_registers)):
            register_address_in_map = start_register + response_register_number
            if register_address_in_map in self.modbus_map[reg_types].keys():
                # print("Decode register:{}".format(register_address_in_map))
                slice_for_decoder = responce_registers[response_register_number:]
                modbus_value = self.modbus_map[reg_types][register_address_in_map]
                assert isinstance(modbus_value, ModbusDeviceValue)
                value_from_controller = modbus_value.get_value_from_modbus_registers(
                    slice_for_decoder
                )

                current_memory_value = self.operative_values_memory[reg_types][
                    modbus_value.address
                ]
                assert isinstance(current_memory_value, ControllerValue)
                current_memory_value.update_value(value_from_controller)

    def print_memory(self):

        print("=====HOLDING====")
        for value in self.operative_values_memory["HOLDING"].values():
            print(str(value))

        print("====INPUT===")
        for value in self.operative_values_memory["INPUT"].values():
            print(str(value))

        print(
            "total registers = "
            + str(
                len(self.operative_values_memory["HOLDING"])
                + len(self.operative_values_memory["INPUT"])
            )
        )
