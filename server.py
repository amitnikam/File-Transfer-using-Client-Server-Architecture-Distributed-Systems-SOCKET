'''
    File name: server.py
    Author: Amit Nikam
    Version: 1.0.0
    Python Version: 3.8
'''

### MODULES
import socket
import threading
import pickle
import os
from os.path import isfile, join
import argparse
import hashlib
import logging
import time

### Pass Arguments to script via. Terminal
parser = argparse.ArgumentParser(description = "This is the Multi Threaded Socket Server!")
parser.add_argument('--ip', metavar = 'ip', type = str, nargs = '?', default = socket.gethostbyname(socket.gethostname()))
parser.add_argument('--port', metavar = 'port', type = int, nargs = '?', default = 9000)
parser.add_argument('--dir', metavar = 'dir', type = str, nargs = '?', default = './host_dir')
args = parser.parse_args()

### LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(message)s')
file_handler = logging.FileHandler('server.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

### PROTOCOL
HEADER = 64                 # Size of header
PACKET = 2048               # Size of a packet, multiple packets are sent if message is larger than packet size. 
FORMAT = 'utf-8'            # Message format
ADDR = (args.ip, args.port)  # Address socket server will bind to  

### MESSAGES
FILE_LIST_MESSAGE = "!GET_FILE_LIST"
FILE_DOWNLOAD_MESSAGE = "!DOWNLOAD "
DISCONNECT_MESSAGE = "!DISCONNECT"


### BIND SOCKET TO PORT
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
except Exception as e:
    raise SystemExit(f"Failed to bind to host: {args.ip} and port: {args.port}, because {e}")

### DIRECTORY TO HOST FILES (MAKE ONE IF NOT MADE. CAN BE CHANGED WITH ARGUMENT)
if not os.path.exists(args.dir):
    os.makedirs(args.dir)
    logger.info(f'{"[FILE DIRECTORY]":<26}{args.dir} directory created. Keep files which you want clients to download here.')

### GENERATE FILE LIST FROM HOST DIRECTORY
def getFileList():
    return [f for f in os.listdir(args.dir) if isfile(join(args.dir, f))]


### SOCKET CONNECTION HANDLER
def handle_client(conn, addr):
    logger.info(f'{"[NEW CONNECTION]":<26}{addr} connected.')

    ## SEND MESSAGES ENCODED IN FORMAT
    def send(msg):
        # message pickled into bytes and HEADER added to message
        msg = pickle.dumps(msg)
        msg = bytes(f'{len(msg):<{HEADER}}', FORMAT) + msg
        if len(msg) > PACKET:    
            for i in range(0, len(msg), PACKET):
                conn.send(msg[i:i+PACKET])
            return len(msg)
        conn.send(msg)
        return len(msg)

    ## RECORD STATS
    conn_time = time.time()
    conn_download = 0

    ## MESSAGE RECEIVER 
    connected = True
    while connected:

        # RECEIVE MESSAGE HEADER > GET LENGTH OF MESSAGE > SAVE AND DECODE FULL MESSAGE
        msg_length = conn.recv(HEADER)
        if msg_length:
            # Start the process only for a valid header 
            full_msg = b''
            new_msg = True
            # loop to download full message body
            while True:
                # receive message packets
                msg = conn.recv(PACKET)
                
                # get length from header
                if new_msg:
                    msg_len = int(msg_length)
                    full_msg = msg_length
                    new_msg = False
                
                full_msg += msg

                # decode and break out of loop if full message is received
                if len(full_msg)-HEADER == msg_len:
                    msg = pickle.loads(full_msg[HEADER:])
                    break
        
        # CASE FOR DOWNLOAD MESSAGE
        if msg[:len(FILE_DOWNLOAD_MESSAGE)] == FILE_DOWNLOAD_MESSAGE:
            # open requested file in binary and read data
            file_name = join(args.dir, msg[len(FILE_DOWNLOAD_MESSAGE):])
            up_start = time.time()
            file_open = open(file_name,'rb')
            file_data = file_open.read()
            # md5 HASH the opened file
            md5 = hashlib.md5(file_data).hexdigest()
            # send md5 and then opened file data
            file_size = send(md5)
            file_size += send(file_data)
            file_open.close()

            # log stats
            conn_download += file_size
            logger.info(f'{"[DOWNLOAD FILE]":<26}{addr} -> is downloading {msg[len(FILE_DOWNLOAD_MESSAGE):]}.')
            logger.info(f'{"[UPLOAD STAT]":<26}{addr} <- sent:{file_size:^12}Bytes in time:{time.time()-up_start:<24}')
            msg=''
            
        # CASE FOR FILE LIST MESSAGE - RETURNS LIST OF FILES
        if msg == FILE_LIST_MESSAGE:
            file_size = send(getFileList())
            conn_download += file_size
            logger.info(f'{"[FETCH FILE LIST]":<26}{addr}')
            msg=''
        
        # CASE FOR DISCONNECT MESSAGE
        if msg == DISCONNECT_MESSAGE:
            connected = False
            logger.info(f'{"[DISCONNECTED]":<26}{addr} -> Total Download:{conn_download} Bytes | Time Connected:{time.time()-conn_time}')
    
    ## CLOSE CONNECTION
    conn.close()


### MAIN SERVER THAT IS LISTENING FOR CONNECTIONS ON BINDED PORT,
### ACCEPTS CONNECTIONS AND ASSIGNS A THREAD TO HANDLE CONNECTION.
def start():
    server.listen()
    logger.info(f'{"[LISTENING]":<26}Server is listening on host:{args.ip} and Port:{args.port}')
    while True:

        ## MULTI THREADING CONNECTIONS
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn,addr))
            thread.start()
            logger.info(f'{"[ACTIVE CONNECTIONS]":<26}{threading.activeCount() - 1}')
        
        ## HANDLE KEYBOARD INTERRUPTS
        except KeyboardInterrupt:
            logger.info(f'{"[KEYBOARD INTERRUPT]":<26}Server stopped accepting new connections')
            logger.info(f'{"[CHECK]":<26}{threading.activeCount() - 1} client thread(s) still active')
            break

        ## HANDLE ANY OTHER ERRORS
        except Exception as e:
            logger.info(f'Connection error: {e}')

### RUN SERVER
def run():
    logger.info(f'{"[STARTING]":<26}Server is starting...')
    start()
    logger.info('[SERVER SHUTDOWN]')

### START
if __name__ == "__main__":
   run()
