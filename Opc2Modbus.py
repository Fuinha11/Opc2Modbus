header = '''
###########################################################################     
#                                                          
#   _____  _____  _____    ___    _____         _  _             
#  |     ||  _  ||     |  |_  |  |     | ___  _| || |_  _ _  ___ 
#  |  |  ||   __||   --|  |  _|  | | | || . || . || . || | ||_ -|
#  |_____||__|   |_____|  |___|  |_|_|_||___||___||___||___||___|
#             
#                                                    
# OPC to Modbus for Python Script
#
# Created by Marcos Marques @ 2020 (https://github.com/Fuinha11)
#
###########################################################################
'''

from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from twisted.internet.task import LoopingCall
from opcua import Client
import logging


# ----------------------------------------------------------------------- #
# Configuration
# ----------------------------------------------------------------------- #

logging.basicConfig()
log = logging.getLogger("OpcToModbus")
log.setLevel(logging.INFO)  # You may change this for production depoy

# Host address of the OPC Server
opc_host = "opc.tcp://localhost:4840/freeopcua/server/"

# Host adress for the Modbus Server
modbus_host = "localhost"
modbus_port = 5020

# Modbus server information
identity = ModbusDeviceIdentification()
identity.VendorName = 'Fuinha11'
identity.ProductCode = 'POTM'
identity.VendorUrl = 'https://github.com/Fuinha11'
identity.ProductName = 'OPC to Modbus'
identity.ModelName = 'O2M0.1'
identity.MajorMinorRevision = '0.0.1'

# Time between updates in sec
update_inteval = 1.5

# ----------------------------------------------------------------------- #
# End of Configuration
# ----------------------------------------------------------------------- #

opc_client: Client


def initiate_client():
    global opc_client
    opc_client = Client(opc_host)
    opc_client.connect()
    return opc_client


def shutdown_client():
    global opc_client
    opc_client.disconnect()


def updating_writer(context):
    """ 
    A worker process that runs every so often and
    updates live values to the context.
    """

    root = opc_client.get_root_node()

    # Gather data from OPC Client
    myvar = root.get_child(["0:Objects", "2:MyObject", "2:MyVariable"])
    
    # Update Modbus context data
    register = 3
    slave_id = 0x00  # If in single mode the only slave_id is 0x00
    address = 0x00
    value = myvar.get_value()
    context[slave_id].setValues(register, address, [int(value)])


def initiate_server(identity, inteval, host, port):
    """
    Start a Modbus server using the information on
    the configuration block above, and set a recurring 
    call to a function in order to update the values.
    """

    # initialize your data store
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock.create(),
        co=ModbusSequentialDataBlock.create(),
        hr=ModbusSequentialDataBlock.create(),
        ir=ModbusSequentialDataBlock.create(),)

    context = ModbusServerContext(slaves=store, single=True)

    # Start the Looping callback
    loop = LoopingCall(f=updating_writer, context=context)
    loop.start(inteval, now=False)

    # Start the Modbus server
    print("Modbus Server started. Press Cntl + C to stop...")
    StartTcpServer(context, identity=identity, address=(host, port))


if __name__ == "__main__":
    try:
        print(header)
        print("Initializing...")
        print("Starting OPC Client.")
        initiate_client()
        print(f"Client listening at: {opc_host}")
        print("-"*70 + "\n")
        print("Starting Modbus server.")
        print(f"Server hosted at: {modbus_host}:{modbus_port}")
        initiate_server(identity, update_inteval, modbus_host, modbus_port)
    finally:
        print("Sutting down...")
        shutdown_client()