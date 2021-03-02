'''
    File name: client.py
    Author: Amit Nikam
    Version: 1.0.0
    Python Version: 3.8
'''

### MODULES
import socket
from socket import timeout
import argparse
import pickle
import os
import hashlib
import concurrent.futures
import time

### Pass Arguments to script via. Terminal
parser = argparse.ArgumentParser(description = "This is the client for the multi threaded socket server!")
parser.add_argument('--ip', metavar = 'ip', type = str, nargs = '?', default = socket.gethostbyname(socket.gethostname()))
parser.add_argument('--port', metavar = 'port', type = int, nargs = '?', default = 9000)
parser.add_argument('--dir', metavar = 'dir', type = str, nargs = '?', default = './downloads')
args = parser.parse_args()

### PROTOCOL
TIMEOUT_SECONDS = 10        # Timeout connection after defined seconds of inactivity
HEADER = 64                 # Size of header
PACKET = 2048               # Size of a packet, multiple packets are sent if message is larger than packet size.
FORMAT = 'utf-8'            # Message format
ADDR = (args.ip, args.port)  # Address socket server will bind to  

### MESSAGES
FILE_LIST_MESSAGE = "!GET_FILE_LIST"
FILE_DOWNLOAD_MESSAGE = "!DOWNLOAD "
DISCONNECT_MESSAGE = "!DISCONNECT"

### DOWNLOAD DIRECTORY (MAKE ONE IF NOT EXISTING. CAN BE CHANGED WITH ARGUMENT)
if not os.path.exists(args.dir):
    os.makedirs(args.dir)
    print(f'\n{args.dir} folder created. Files will be downloaded here.')

### ESTABLISH SOCKET CONNECTION TO SERVER ON DEMAND
def createSocket():
    # define socket as a IPv4 and TCP type
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # set timeout to connections
    client.settimeout(TIMEOUT_SECONDS)
    # create a non-blocking socket connection and return it
    client.connect_ex(ADDR)
    return client

### SEND SERIALIZED MESSAGES TO THE SERVER ENCODED IN FORMAT
def send(msg,client):
    # message pickled into bytes and HEADER added to message
    msg = pickle.dumps(msg)
    msg = bytes(f'{len(msg):<{HEADER}}', FORMAT) + msg
    client.send(msg)

### RECEIVED MESSAGE FROM THE SERVER
def getMessage(client):
    full_msg = b''
    new_msg = True
    ## Loop to download full message body
    while True:
        # receive message packets or teminate if packets lost
        try:
            msg = client.recv(PACKET)
        except timeout:
            full_msg = "TIMEOUT"
            break
        
        # get length of message from HEADER
        if new_msg:
            msg_len = int(msg[:HEADER])
            new_msg = False
        
        full_msg += msg

        # decode and break out of loop if full message is received
        if len(full_msg)-HEADER == msg_len:
            full_msg = pickle.loads(full_msg[HEADER:])
            break
    
    ## Return the full message or terminated status to caller
    return full_msg

### USER INTERRACTION TO SELECT FILES FOR DOWNLOAD FROM THE HOST LIST
def selectFilesFromList(file_list):
    ## Display list in console
    print("\nSelect files to download by index number. For multiple files seperate the index number with comma:\n")
    print(f'{"Index":<8}{"File Name":<20}')
    for f in file_list:
        print(f'{file_list.index(f):<8}{f:<20}')
    ## Save user input
    li = list(map(int, input('\n').split(',')))
    dl = []
    
    ## Check input for valid files
    for i in li:
        try:
            if i == file_list.index(file_list[i]):
                dl.append(file_list[i])
        # Inform of invalid inputs
        except IndexError:
            print(f'\nIndex no {i} not found!')
    
    ## Show the list of valid files which will be downloaded
    print(f'\nDownloading {dl}\n')
    return dl

### HANDLER FOR SERIAL AND PARALLEL DOWNLOADS   
def download(file_list, mode, client):
    ## takes list of files to download, mode and client
    fail_list = []
    
    ## SERIALLY DOWNLOAD
    if mode == 0:
        for f in file_list:
            # function to download and return success/fail
            fail = downloadSerial(f, client)
            # make a list of failed downloads
            if fail:
                fail_list.append(f)
        return fail_list
    ## PARALLELY DOWNLOAD
    elif mode == 1:
        # assign a thread for the download process and add it to list
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(downloadParallel,file_list.index(f),f) for f in file_list]
            # as sson as any download ends, take action
            for f in concurrent.futures.as_completed(threads):
                fail = f.result() 
                if fail:
                    fail_list.append(fail)
        return fail_list
    ## case for wrong mode selected
    else:
        print("Invalid Input")
        return file_list

### SERIAL DOWNLOADER
def downloadSerial(f, client):
    down_file_time = time.time()
    ## send message for download containing file name
    send(FILE_DOWNLOAD_MESSAGE+f,client)
    ## receive md5 and file data 
    md5_original = getMessage(client)
    file_data = getMessage(client)
    ## if the connection timesout due to packet loss, return file name to re-download
    if (md5_original=="TIMEOUT" or file_data=="TIMEOUT"):
        print(f'\n{f} failed to download due to time out, trying again!')
        return f
    ## generate md5 of the file data received
    md5_mirror = hashlib.md5(file_data).hexdigest()
    ## INTEGRITY CHECK - Save if success, else return file name for re-download
    if md5_original == md5_mirror:
        file_mirror = open(os.path.join(args.dir,f), 'wb')
        file_mirror.write(file_data)
        file_mirror.close()
        print(f'\n{f}\nmd5: {md5_mirror}\nIntegrity check pass, downloaded successfully!')
        print(f'Downloaded in {time.time()-down_file_time} seconds')
    else:
        print(f'\n{f}\nFile integrity failures. trying again')
        return f

### PARALLEL DOWNLOADER (Each file is assigned one connection thread)
def downloadParallel(c,f):
    ## make a new connection to the server
    c = createSocket()
    ## send message for download containing file name
    down_file_time = time.time()
    send(FILE_DOWNLOAD_MESSAGE+f, c)
    ## receive md5 and file data
    md5_original = getMessage(c)
    file_data = getMessage(c)
    ## if the connection timesout due to packet loss,
    ## close connection thread and try again
    if (md5_original=="TIMEOUT" or file_data=="TIMEOUT"):
        print(f'\n{f} failed to download due to time out, trying again!')
        send(DISCONNECT_MESSAGE,c)
        c.close()
        return f
    ## generate md5 of the file data received
    md5_mirror = hashlib.md5(file_data).hexdigest()
    ## INTEGRITY CHECK - Save if success and disconnect
    if md5_original == md5_mirror:
        file_mirror = open(os.path.join(args.dir,f), 'wb')
        file_mirror.write(file_data)
        file_mirror.close()
        print(f'\n{f}\nmd5: {md5_mirror}\nIntegrity check passed, downloaded successfully!')
        print(f'Downloaded in {time.time()-down_file_time} seconds')
        send(DISCONNECT_MESSAGE,c)
        c.close()
    ## IF FAILED INTEGRITY CHECK - Close connection thread and try again
    else:
        print(f'\n{f}\nFile integrity failures. trying again')
        send(DISCONNECT_MESSAGE,c)
        c.close()
        return f

### RUN CLIENT (ACTIVE STATUS)
def run():
    client = createSocket()
    print(f"[CONNECTED] Client connected to {args.ip}")
    active = True
    try:
        while active: 
            ## SEND REQUEST TO GET FILE LIST ON DEMAND
            send(FILE_LIST_MESSAGE, client)
            file_list = getMessage(client)
            if file_list == "TIMEOUT":
                continue
            
            ## LET USER SELECT FILES TO DOWNLOAD FROM THE LIST
            file_list = selectFilesFromList(file_list)
            
            ## LET USER SELECT MODE
            comm = int(input("Enter\n0 - Serially download\n1 - Parallely download\n"))
            download_time = time.time()
            fail_list = download(file_list, comm, client)
            
            ## LOOP TO TRY AND DOWNLOAD FAILED FILES AGAIN
            if fail_list:
                retry = 3
                while retry:
                    if (comm != 0 and comm != 1):
                        break
                    print(f'\n{fail_list} failed to download, tries left {retry}')
                    retry = retry - 1
                    fail_list = download(fail_list, comm, client)
                    if not fail_list:
                        break
            
            ### IF STILL ANY DOWNLOADS LEFT, INFORM USER
            if fail_list:
                print(f'{fail_list} could not be downloaded')
            
            download_time = time.time()-download_time
            print(f'\nDownload Completed in: {download_time} seconds')
            
            ## END CONNECTION
            send(DISCONNECT_MESSAGE, client)
            client.close()
            
            ## DEACTIVATE PROGRAM
            print(f'\n-\n--\n---\n[CLOSING PROGRAM]\n---\n--\n-\n')
            active = False

    except KeyboardInterrupt:
        send(DISCONNECT_MESSAGE, client)
        print("\n[KEYBOARD INTERRUPT]")

### START
if __name__ == "__main__":
   run()