# File Transfer using Client-Server Architecture Distributed Systems (SOCKETS)

This program is a basic implementation of a widely used client-server based communication architecture between different Distributed Systems. Connections are established through [Sockets](https://www.tutorialspoint.com/unix_sockets/what_is_socket.htm). Server can handle multiple clients simultaneously using multi-threading. Clients can download multiple files parallely using multiple threaded connections.

___
<br>

## Implementation

<br>

> Run the server.py python script before client.py (else the client would throw a connection error and close).

### Server
The server.py can be executed simply using:
    
    python server.py

If required, arguments can be passed to the Server during the time of
execution as follows:

    python server.py --ip <Host Address> --port <PORT> --dir <Host File Location>

`--port` is used to pass port number as argument (default:9000)

`--dir` is used to declare the host file directory (default: ./host_dir)

`--ip` is used to pass IP Address manually (default: Self Host)

### Client
To start the client, run client.py

    python client.py

If required, arguments can be passed to the Client during the time of
execution as follows:

    python client.py --ip <Address> --port <PORT> --dir <Download Location>

`--port` is used to pass server's PORT number as argument (default:9000)

`--dir` is used to declare the download file directory (default: ./downloads)

`--ip` is used to pass Server's IP Address manually (default: Self Host)

>> It is advised to not use --ip if running the server.py and client.py on local machine. 
>
>> To shutdown an active server, Keyboard Interrupt the server by
pressing ‘ctrl’ + ’F’ keys.
>
>> If any active clients are connected, the server will print the same in console. It is advised to close the clients before closing the server to avoid temporary PORT blocking.

___
<br>

## Features

<br>

__Server Features (Version 1.0.0)__
- Server logs every major action in a log file.
- The server binds to a socket which is listening for conntections on a port.
- Clients can connect to the server using the system's address and port number.
- Server can handle multiple connections simultaneously using Multi-Threading.
- The server (program) hosts a few files in it's specified host directory.
- The server sends the list of files it has in it's hosted directory to the client on demand.
- Server sends the requested download file to the client from it's host directory.
- Host Address, Port Number and File host directory can be updated as passed arguements while running the program.

__Client Features (Version 1.0.0)__
- Client is an terminal based user interractive program.
- Client establishes connection to the server using the server system's address and port number.
- Client requests the server to send the list of files it has.
- Client creates a directory to download files to (if not created).
- Client takes files selected for download by the user and proceeds to download using either of the two methods:
    - Parallel Download: Downloads files parallely by establishing new connection for each file download.
    - Serial Download: Downloads files one after another in the same connection as the client.  
- Client closes connection and shutdowns if user quits the program.

___
<br>

## About
<br>

__Version:__ 1.0.0

__Reporitory:__ <https://github.com/amitnikam/File-Transfer-using-Client-Server-Architecture-Distributed-Systems-SOCKETS->

__Author:__ [Amit Nikam](https://github.com/amitnikam)

__Mail:__ <mail@amitnikam.com>

___
