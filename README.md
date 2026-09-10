# ft_irc

A custom Internet Relay Chat server written in C++98.

This project recreates the core functionality of an IRC server using TCP sockets and a single non blocking event loop based on `poll()`.
The server supports multiple clients, authentication, nickname management, channels, private messages, channel operators, invitations, topics and channel modes.

## Table of Contents

1. [IRC](#irc)
2. [Networking Concepts](#networking-concepts)
3. [Sockets](#sockets)
4. [Creating a TCP Server](#creating-a-tcp-server)
5. [TCP Connection Flow](#tcp-connection-flow)
6. [Non Blocking I/O](#non-blocking-io)
7. [poll()](#poll)
8. [Receiving IRC Messages](#receiving-irc-messages)
9. [Sending IRC Messages](#sending-irc-messages)
10. [Server Architecture](#server-architecture)
11. [Client Lifecycle](#client-lifecycle)
12. [IRC Registration](#irc-registration)
13. [IRC Commands](#irc-commands)
14. [Channels](#channels)
15. [Channel Modes](#channel-modes)
16. [Topics](#topics)
17. [Private Messages](#private-messages)
18. [Project Structure](#project-structure)
19. [Project Communication Flow](#project-communication-flow)
20. [Clean Shutdown](#clean-shutdown)
21. [Build](#build)
22. [Usage](#usage)
23. [Testing](#testing)

## IRC

IRC, or Internet Relay Chat, is a protocol that allows users to communicate through a server.

An IRC client connects to the server using TCP. After connecting, the client registers with a nickname and username, then it can join channels and communicate with other users.

A simple IRC server can be represented like this:

```text
                         IRC SERVER
                              |
              +---------------+---------------+
              |               |               |
           Client A        Client B        Client C
              |               |               |
              +---------------+---------------+
                              |
                           #channel
```

The server is responsible for managing connections and deciding where messages should go.

For example, if `kaw` sends a message to a channel:

```text
kaw
 |
 | PRIVMSG #42 :Hello everyone
 v
IRC Server
 |
 +------> akira
 |
 +------> another client
 |
 +------> another client
```

The server keeps track of connected clients, channels, channel members, operators, invitations, topics and channel modes.

## Networking Concepts

### TCP

TCP stands for Transmission Control Protocol.

It provides a reliable and ordered byte stream between two endpoints.

In this project, the endpoints are sockets belonging to the IRC client and the IRC server.

TCP provides:

* reliable delivery
* ordered data
* retransmission of lost data
* connection management
* a continuous stream of bytes

One important thing to understand is that TCP does not understand IRC commands.

If a client sends:

```text
NICK kaw\r\n
```

TCP only sees a sequence of bytes.

It does not know that:

```text
NICK kaw\r\n
```

is one IRC command.

This responsibility belongs to the application layer, which in this project is handled by the parser.

### Socket

A socket is a communication endpoint used by a program to communicate with another process.

The application asks the operating system to create the socket:

```cpp
int fd = socket(AF_INET, SOCK_STREAM, 0);
```

If successful, the operating system returns a file descriptor.

For example:

```text
fd = 3
```

The file descriptor is the handle used by the program to work with that socket.

### IP Address

An IP address identifies a machine or network interface.

For local testing, this project uses:

```text
127.0.0.1
```

This is the loopback address and refers to the local machine.

When the server uses:

```cpp
INADDR_ANY
```

it means that it can listen on the available local IPv4 interfaces.

Conceptually:

```text
0.0.0.0:6667
```

means:

```text
all local IPv4 interfaces
          +
       port 6667
```

### Port

A port identifies a service on a machine.

TCP and UDP ports range from:

```text
0 to 65535
```

The traditional ranges are:

```text
0       1023       49151                 65535
|---------|-----------|---------------------|
 System    Registered   Dynamic / Private
 Ports     Ports        Ports
```

For this project, the port is provided when starting the server:

```bash
./irc 6667 00
```

Here:

```text
6667
 |
 + IRC server port

00
 |
 + server password
```

## Sockets

The `socket()` function is:

```cpp
int socket(int domain, int type, int protocol);
```

It takes three arguments.

### Domain

The domain defines the address family.

Common examples:

```text
AF_INET
    |
    + IPv4

AF_INET6
    |
    + IPv6

AF_UNIX
    |
    + communication between processes
      on the same machine
```

This project uses:

```cpp
AF_INET
```

because the server communicates using IPv4.

### Type

The type defines how communication behaves.

The two important types are:

```text
SOCK_STREAM
    |
    + stream oriented communication
    + normally TCP

SOCK_DGRAM
    |
    + datagram oriented communication
    + normally UDP
```

This project uses:

```cpp
SOCK_STREAM
```

because IRC communication uses TCP.

### Protocol

The third argument selects the specific protocol.

Using:

```cpp
0
```

asks the operating system to use the default protocol for the selected domain and type.

Therefore:

```cpp
socket(AF_INET, SOCK_STREAM, 0);
```

means:

```text
AF_INET
    |
    + IPv4

SOCK_STREAM
    |
    + stream communication

0
    |
    + default protocol
    |
    + TCP
```

This creates an IPv4 TCP socket.

## Creating a TCP Server

A TCP server is created through a sequence of steps:

```text
socket()
    |
    v
bind()
    |
    v
listen()
    |
    v
accept()
    |
    v
client socket
```

Each function has a different responsibility.

### socket()

Creates the socket:

```cpp
fd = socket(AF_INET, SOCK_STREAM, 0);
```

At this point, the server has a socket but it is not listening on a port yet.

### bind()

Associates the socket with an IP address and port.

The server prepares an IPv4 address:

```cpp
sockaddr_in adr;

adr.sin_family = AF_INET;
adr.sin_addr.s_addr = htonl(INADDR_ANY);
adr.sin_port = htons(port);
```

Then:

```cpp
bind(fd, reinterpret_cast<sockaddr *>(&adr), sizeof(adr));
```

The result is conceptually:

```text
Server socket
      |
      v
0.0.0.0:6667
```

`htons()` converts a 16 bit value from host byte order to network byte order.

It is used for the port.

`htonl()` converts a 32 bit value from host byte order to network byte order.

It is used for IPv4 address values such as `INADDR_ANY`.

```text
htons()
    |
    + host to network
    + 16 bit
    + port

htonl()
    |
    + host to network
    + 32 bit
    + IPv4 address
```

### listen()

`listen()` changes the socket into a passive listening socket:

```cpp
listen(fd, SOMAXCONN);
```

The server is now waiting for incoming TCP connections.

The listening socket does not normally communicate with a client.

Its job is to wait for new connections.

### accept()

When a client connects, the server calls:

```cpp
int client_fd = accept(fd, NULL, NULL);
```

`accept()` returns a new file descriptor representing the connected client.

The original listening socket remains open.

```text
                 Server

          Listening socket
                 fd
                 |
                 | accept()
                 |
       +---------+---------+
       |         |         |
       v         v         v
    client A  client B  client C
      fd 4      fd 5      fd 6
```

The important distinction is:

```text
Listening socket
    |
    + waits for connections

Connected socket
    |
    + communicates with one client
```

## TCP Connection Flow

Before the server receives a connection through `accept()`, TCP establishes the connection using the three way handshake.

```text
Client                         Server

   |                              |
   | -------- SYN --------------> |
   |                              |
   | <----- SYN + ACK ----------- |
   |                              |
   | -------- ACK --------------> |
   |                              |
   |     TCP connection ready     |
   |                              |
   |                        accept()
   |                              |
   |                        client_fd
   |                              |
   | <-------- data ------------> |
```

The operating system kernel handles the TCP handshake.

The IRC server does not manually implement SYN, SYN ACK or ACK packets.

Once the connection is established, the connection waits in the kernel's accept queue until the server calls `accept()`.

The complete server side flow is:

```text
socket()
   |
   v
bind()
   |
   v
listen()
   |
   v
Client connects
   |
   v
TCP handshake
   |
   v
Accept queue
   |
   v
accept()
   |
   v
New client socket
```

The listening socket stays open so other clients can connect through the same port.

## Non Blocking I/O

This server uses non blocking sockets.

A socket can be changed to non blocking mode using:

```cpp
fcntl(fd_client, F_SETFL, O_NONBLOCK);
```

In simple terms:

```text
fd_client
    |
    + which file descriptor?

F_SETFL
    |
    + change file status flags

O_NONBLOCK
    |
    + enable non blocking mode
```

### Why non blocking?

With blocking I/O, a call such as `recv()` can wait until data becomes available.

For a server handling multiple clients, this can cause one client to block the whole event loop.

With non blocking I/O:

```text
Client A
   |
   | no data
   v
recv() returns
   |
   v
continue

Client B
   |
   v
check

Client C
   |
   v
check
```

The server can continue processing other clients.

When a non blocking operation cannot currently proceed, the system may return:

```text
EAGAIN
```

or:

```text
EWOULDBLOCK
```

These do not automatically mean that the client disconnected.

They generally mean:

```text
The operation cannot be completed right now.
Try again later.
```

## poll()

The server needs to handle multiple sockets.

Instead of continuously blocking on one client, it uses `poll()` to monitor all relevant file descriptors.

Each entry contains:

```cpp
struct pollfd
{
    int   fd;
    short events;
    short revents;
};
```

The important fields are:

```text
fd
 |
 + which socket?

events
 |
 + what do I want to monitor?

revents
 |
 + what actually happened?
```

For example:

```cpp
fds[i].events = POLLIN;
```

means:

```text
Tell me when this socket is ready to be read.
```

After `poll()` returns, the kernel fills:

```cpp
fds[i].revents
```

with the events that actually happened.

### POLLIN

The socket is ready for reading.

For the listening socket:

```text
POLLIN
   |
   + new connection
   |
   + accept()
```

For a client socket:

```text
POLLIN
   |
   + client sent data
   |
   + recv()
```

### POLLOUT

The socket is ready for writing.

This server uses it when a client's send buffer contains data waiting to be transmitted.

### POLLHUP

Indicates that the connection has been hung up.

The server treats this as a condition that needs to be handled and cleaned up.

For example:

```text
Client closes connection
        |
        v
      POLLHUP
        |
        v
   disconnect()
        |
        v
 close client socket
```

### POLLERR

Indicates an error condition on the file descriptor.

### POLLNVAL

Indicates that the file descriptor is invalid.

The server checks these conditions and disconnects the affected client when necessary.

### Poll bit flags

Poll events are bit flags.

This is why code such as:

```cpp
if (events & POLLOUT)
```

is used.

The three operations to remember are:

```cpp
// CHECK
if (events & POLLOUT)

// ADD
events |= POLLOUT;

// REMOVE
events &= ~POLLOUT;
```

A simple way to remember them:

```text
&       CHECK
|=      ADD
&= ~    REMOVE
```

For example:

```cpp
clientPollfd.events |= POLLOUT;
```

enables `POLLOUT`.

And:

```cpp
clientPollfd.events &= ~POLLOUT;
```

removes `POLLOUT`.

## The Main Server Loop

The server is built around one main event loop.

Conceptually:

```text
                    launch()
                       |
                       v
                    poll()
                       |
          +------------+------------+
          |            |            |
          v            v            v
      listener       client       client
       POLLIN        POLLIN       POLLOUT
          |            |            |
          v            v            v
       accept()      recv()       send()
          |            |            |
          v            v            v
     new client      parser      send buffer
```

The same loop can also detect:

```text
POLLERR
POLLHUP
POLLNVAL
```

and clean up the affected connection.

This allows one server process to manage many clients.

## Receiving IRC Messages

When `poll()` reports `POLLIN` for a client, the server reads data using `recv()`.

There are three important cases.

### recv() > 0

Data was received.

The returned value represents the number of bytes received.

Those bytes are appended to the client's receive buffer.

### recv() == 0

The remote side closed the connection.

The server must clean up the client.

```text
recv() == 0
      |
      v
client disconnected
      |
      v
leave channels
      |
      v
close socket
      |
      v
remove from poll list
      |
      v
remove client state
```

### recv() == -1

An error occurred.

Because the socket is non blocking, the server checks `errno`.

If it is:

```text
EAGAIN
EWOULDBLOCK
```

the connection is normally still valid.

## TCP Message Fragmentation

TCP gives the server a continuous stream of bytes, not complete IRC commands.

For example, the client `kaw` might send:

```text
NICK kaw\r\n
```

The server is not guaranteed to receive the complete command in one `recv()`.

It could receive:

```text
NICK k
```

and later:

```text
aw\r\n
```

The server therefore stores received data in the client's buffer until a complete IRC line is available.

```text
Client
   |
   | TCP data
   v
 recv()
   |
   v
Client buffer
   |
   | search for \r\n
   |
   +---- not found
   |       |
   |       +---- keep the data
   |
   +---- found
           |
           v
     complete IRC command
           |
           v
         Parser
```

For example:

```text
First recv():

NICK k

Client buffer:

NICK k
```

There is no `\r\n` yet, so the server waits for more data.

Later:

```text
Second recv():

aw\r\n
```

The buffer becomes:

```text
NICK kaw\r\n
```

Now the server has a complete IRC command and can pass it to the parser.

### Several commands in one recv()

The opposite can also happen.

A client may send several commands very quickly:

```text
PASS 00\r\nNICK kaw\r\nUSER Kawtar 0 * :Kawtar\r\n
```

A single `recv()` may return all of these bytes at once.

The server therefore has to extract every complete command.

```text
recv()
   |
   v
Client buffer
   |
   +---- PASS 00\r\n
   |
   +---- NICK kaw\r\n
   |
   +---- USER Kawtar 0 * :Kawtar\r\n
```

Each command is processed separately:

```text
PASS 00
   |
   v
PASS handler

NICK kaw
   |
   v
NICK handler

USER Kawtar 0 * :Kawtar
   |
   v
USER handler
```

This is why the receive buffer belongs to each client.

Every client has its own TCP stream and therefore its own buffer.

```text
Server
 |
 +── Client kaw
 |      |
 |      +── nickname
 |      +── username
 |      +── buffer
 |
 +── Client akira
        |
        +── nickname
        +── username
        +── buffer
```

TCP does not know anything about `PASS`, `NICK`, `USER`, `JOIN` or `PRIVMSG`.

TCP provides the reliable byte stream.

The IRC parser creates logical IRC commands from that byte stream.

## Sending IRC Messages

Receiving data is only half of the communication.

The server also needs to send IRC messages back to clients.

For example, `kaw` can send:

```text
PRIVMSG akira :Hello Adam
```

The server receives:

```text
PRIVMSG akira :Hello Adam\r\n
```

The parser extracts the command and the `PRIVMSG` handler determines that `akira` is the destination.

The server can then prepare:

```text
:kaw PRIVMSG akira :Hello Adam\r\n
```

and place it into `akira`'s send buffer.

### Why a send buffer?

A non blocking `send()` is not guaranteed to transmit the entire message in one call.

For example:

```text
send buffer:

:kaw PRIVMSG akira :Hello Adam\r\n
```

The first call to `send()` might transmit only part of the data.

The remaining bytes must stay in the send buffer.

```text
Client
 |
 +── buffer
 |     incoming data
 |
 +── send_buffer
       outgoing data
```

The sending flow is:

```text
Command handler
      |
      v
sending_queue()
      |
      v
Client send_buffer
      |
      v
enable POLLOUT
      |
      v
poll()
      |
      v
POLLOUT
      |
      v
send()
      |
      v
remove bytes that were sent
      |
      v
send_buffer empty?
      |
      +---- yes
              |
              v
       disable POLLOUT
```

This prevents the server from blocking while waiting for a client to accept outgoing data.

### Channel message example

Suppose `akira` is in `#42` with `kaw` and another client.

Akira sends:

```text
PRIVMSG #42 :Hello everyone
```

The server determines the channel members:

```text
#42
 |
 +── akira
 +── kaw
 +── another client
```

The message is then queued for the appropriate clients.

```text
akira
  |
  | PRIVMSG #42
  v
Server
  |
  v
Channel #42
  |
  +------> kaw
  |
  +------> another client
```

## Server Architecture

The server can be represented as:

```text
Server
 |
 +── fd
 |     listening socket
 |
 +── fds
 |     poll descriptors
 |
 +── clients
 |     Client objects
 |       |
 |       +── fd
 |       +── nickname
 |       +── username
 |       +── registration state
 |       +── buffer
 |       +── send_buffer
 |
 +── channels
       Channel objects
         |
         +── memberFds
         +── operatorFds
         +── invitedFds
         +── topic
         +── channel modes
```

### Server fd

The server's listening socket.

```text
fd
 |
 + listens for new connections
```

It is created with `socket()`, associated with an address using `bind()`, placed into listening mode using `listen()`, and used with `accept()`.

### fds

The vector containing the descriptors monitored by `poll()`.

Conceptually:

```text
fds
 |
 +── [0] server listening fd
 +── [1] client kaw fd
 +── [2] client akira fd
 +── [3] another client fd
```

### clients

Contains the state of connected clients.

A client stores information such as:

```text
file descriptor
nickname
username
registration state
receive buffer
send buffer
```

### channels

Contains the channels created on the server.

A channel stores information such as:

```text
members
operators
invited clients
topic
channel modes
```

The responsibilities are separated:

```text
Server
  |
  + connection management
  + polling
  + client management
  + channel management

Client
  |
  + user state
  + incoming data
  + outgoing data

Channel
  |
  + members
  + operators
  + invitations
  + topic
  + modes
```

## Client Lifecycle

A client follows roughly this lifecycle:

```text
Client starts
     |
     v
TCP connect
     |
     v
Server accept()
     |
     v
Client object created
     |
     v
PASS
     |
     v
NICK
     |
     v
USER
     |
     v
Registered
     |
     +-------- JOIN --------+
     |                      |
     v                      v
  Channel              PRIVMSG
     |                      |
     v                      v
 channel state         message routing
```

When the client disconnects:

```text
disconnect
    |
    v
leave channels
    |
    v
close socket
    |
    v
remove from poll list
    |
    v
remove client state
```

Cleaning up all references is important.

A disconnected client should not remain in the server's client list or inside channel membership lists.

## IRC Registration

A basic IRC registration sequence is:

```text
PASS <password>
NICK <nickname>
USER <username> 0 * :real name
```

For example, `kaw` can register as:

```text
PASS 00
NICK kaw
USER Kawtar 0 * :Kawtar
```

Another client can register as:

```text
PASS 00
NICK akira
USER Adam 0 * :Adam
```

Here:

```text
kaw
 |
 + nickname

Kawtar
 |
 + username
```

and:

```text
akira
 |
 + nickname

Adam
 |
 + username
```

After the required information has been received and validated, the client becomes registered.

The server then sends the appropriate welcome response.

The `001` numeric reply indicates successful registration.

## Nicknames

Each client has a nickname.

For example:

```text
NICK kaw
```

The server validates the nickname and checks that it is not already in use.

If another client already uses the nickname, the server returns the appropriate IRC error.

A successful nickname change does not normally use a dedicated numeric success reply.

Instead, the server sends a `NICK` command.

For example:

```text
:kaw NICK :kaw2
```

This informs the other clients that the nickname has changed.

## IRC Commands

The project implements the main IRC commands required by the server:

```text
PASS
NICK
USER
JOIN
PRIVMSG
TOPIC
KICK
INVITE
MODE
```

### PASS

Authenticates the client using the server password.

```text
PASS 00
```

### NICK

Sets or changes the client's nickname.

```text
NICK kaw
```

### USER

Provides the username and user information.

```text
USER Kawtar 0 * :Kawtar
```

### JOIN

Joins a channel.

```text
JOIN #42
```

### PRIVMSG

Sends a message to another user:

```text
PRIVMSG akira :Hello Adam
```

or to a channel:

```text
PRIVMSG #42 :Hello everyone
```

### TOPIC

Queries a channel topic:

```text
TOPIC #42
```

or sets a topic:

```text
TOPIC #42 :Welcome to #42
```

### KICK

Removes a user from a channel.

```text
KICK #42 akira
```

### INVITE

Invites a user to a channel.

```text
INVITE akira #42
```

### MODE

Changes channel modes.

```text
MODE #42 +i
MODE #42 -i
```

## Channels

Channels allow multiple clients to communicate together.

A channel name in this project starts with `#`.

For example:

```text
JOIN #42
```

When the first client joins a new channel, that client becomes an operator.

For example, if `kaw` creates the channel:

```text
#42

operator
   |
   +── kaw

members
   |
   +── kaw
```

When `akira` joins:

```text
#42

operator
   |
   +── kaw

members
   |
   +── kaw
   +── akira
```

The server keeps channel membership and operator information separately.

When a client joins, the server sends the appropriate IRC join and names replies.

The names list marks channel operators with `@`.

For example:

```text
@kaw akira
```

## Channel Modes

The server implements the following channel modes:

```text
+i
-i

+t
-t

+k
-k

+o
-o

+l
-l
```

### Invite Only

Enable:

```text
MODE #42 +i
```

Only invited clients can join the channel.

Disable:

```text
MODE #42 -i
```

Normal channel joining is allowed again.

### Topic Restriction

Enable:

```text
MODE #42 +t
```

Only channel operators can change the topic.

Disable:

```text
MODE #42 -t
```

Normal members can change the topic again.

### Channel Key

Set a key:

```text
MODE #42 +k secret
```

Clients must provide the correct key when joining:

```text
JOIN #42 secret
```

Remove the key:

```text
MODE #42 -k
```

### Channel Operator

Give operator privileges:

```text
MODE #42 +o akira
```

Remove operator privileges:

```text
MODE #42 -o akira
```

Operators can perform privileged channel operations such as changing restricted modes and kicking users.

### User Limit

Set a channel member limit:

```text
MODE #42 +l 5
```

Remove the limit:

```text
MODE #42 -l
```

## Topics

A channel can have a topic.

Querying the topic:

```text
TOPIC #42
```

If no topic exists, the server returns the appropriate `331` response.

If a topic exists, the server returns `332` with the topic.

Setting a topic:

```text
TOPIC #42 :Welcome to ft_irc
```

The server broadcasts a `TOPIC` command to the channel members:

```text
:kaw TOPIC #42 :Welcome to ft_irc
```

When `+t` is enabled, only channel operators can change the topic.

## Private Messages

IRC messages can be sent directly to another user.

For example, `kaw` can send a private message to `akira`:

```text
PRIVMSG akira :Hello Adam
```

The server finds `akira` and queues the message for the corresponding socket.

The flow is:

```text
kaw
  |
  | PRIVMSG akira :Hello Adam
  v
Server
  |
  | find akira
  v
akira.send_buffer
  |
  v
poll()
  |
  | POLLOUT
  v
send()
  |
  v
akira
```

Messages can also be sent to channels:

```text
PRIVMSG #42 :Hello everyone
```

The server finds the channel members and broadcasts the message to the appropriate clients.

## Project Structure

The project is organized as follows:

```text
ft_IRC_server/
|
├── includes/
│   ├── Channel.hpp
│   ├── Client.hpp
│   ├── irc_server.hpp
│   ├── LogicCore.hpp
│   ├── Parser.hpp
│   └── Server.hpp
│
├── srcs/
│   ├── Channel.cpp
│   ├── Client.cpp
│   ├── Server.cpp
│   │
│   ├── commands/
│   │   ├── CommandDispatcher.cpp
│   │   ├── invite.cpp
│   │   ├── join.cpp
│   │   ├── kick.cpp
│   │   ├── nick.cpp
│   │   ├── pass.cpp
│   │   ├── privmsg.cpp
│   │   ├── replayCmd.cpp
│   │   ├── topic.cpp
│   │   └── user.cpp
│   │
│   ├── modes/
│   │   ├── change_topic.cpp
│   │   ├── invite_only.cpp
│   │   ├── limited_usage.cpp
│   │   ├── modes.cpp
│   │   ├── operator.cpp
│   │   └── secret_key.cpp
│   │
│   └── parsser/
│       └── Parser.cpp
│
├── main.cpp
├── Makefile
└── README.md
```

### includes/

Contains the declarations used by the project.

The main classes are:

```text
Server
    |
    + manages connections, clients and channels

Client
    |
    + represents one connected IRC client

Channel
    |
    + represents one IRC channel

Parser
    |
    + parses complete IRC commands
```

### Server.cpp

Contains the main server and networking logic:

```text
socket
bind
listen
accept
poll
client connections
disconnects
shutdown
```

### Client.cpp

Represents one connected client.

It stores:

```text
file descriptor
nickname
username
registration state
receive buffer
send buffer
```

### Channel.cpp

Represents a channel and manages:

```text
members
operators
invited clients
topic
channel modes
```

### commands/

Contains the IRC command handlers.

```text
CommandDispatcher.cpp
    |
    + selects the correct command handler

pass.cpp
    |
    + PASS

nick.cpp
    |
    + NICK

user.cpp
    |
    + USER

join.cpp
    |
    + JOIN

privmsg.cpp
    |
    + PRIVMSG

topic.cpp
    |
    + TOPIC

kick.cpp
    |
    + KICK

invite.cpp
    |
    + INVITE
```

`replayCmd.cpp` contains the logic used to build IRC numeric replies.

### modes/

Contains the individual channel mode implementations.

```text
modes.cpp
    |
    + MODE entry point

invite_only.cpp
    |
    + +i / -i

change_topic.cpp
    |
    + +t / -t

secret_key.cpp
    |
    + +k / -k

limited_usage.cpp
    |
    + +l / -l

operator.cpp
    |
    + +o / -o
```

### parsser/

Contains the IRC parser.

Its responsibility is to convert a complete IRC line into a structured message.

The flow is:

```text
TCP bytes
   |
   v
Client buffer
   |
   v
complete IRC line
   |
   v
Parser
   |
   v
Message
   |
   v
CommandDispatcher
   |
   v
Command handler
```

## Project Communication Flow

The most important flow in the project is:

```text
                         CLIENT
                           |
                           | TCP
                           v
                    Server::accept()
                           |
                           v
                         Client
                           |
                           v
                         poll()
                           |
                         POLLIN
                           |
                           v
                         recv()
                           |
                           v
                    Client::buffer
                           |
                           v
                       Parser.cpp
                           |
                           v
                 CommandDispatcher.cpp
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
         nick.cpp       join.cpp      privmsg.cpp
            |              |              |
            |              v              |
            |          Channel.cpp        |
            |              |              |
            +--------------+--------------+
                           |
                           v
                  sending_queue()
                           |
                           v
                  Client::send_buffer
                           |
                           v
                         poll()
                           |
                         POLLOUT
                           |
                           v
                         send()
                           |
                           v
                         CLIENT
```

This is the main path to keep in mind when reading the code.

The networking layer receives bytes.

The client stores them.

The parser creates an IRC message.

The dispatcher selects the appropriate handler.

The handler modifies the client or channel state.

The resulting reply is placed into a send buffer.

`poll()` eventually tells the server that the socket is ready for writing.

The server sends the remaining data to the client.


## Build

The project is written in C++98.

Build the server with:

```bash
make
```

To rebuild everything:

```bash
make re
```


## Usage

Start the server with:

```bash
./irc <port> <password>
```

Example:

```bash
./irc 6667 00
```

The server will listen on port `6667` and use `00` as the password.

### Connecting with netcat

For a simple manual test:

```bash
nc -C 127.0.0.1 6667
```

The `-C` option makes netcat use CRLF line endings.

This is useful for IRC because IRC commands are terminated with:

```text
\r\n
```

Register a client as `kaw`:

```text
PASS 00
NICK kaw
USER Kawtar 0 * :Kawtar
```

Register another client as `akira`:

```text
PASS 00
NICK akira
USER Adam 0 * :Adam
```

Then join a channel:

```text
JOIN #42
```

Set a topic:

```text
TOPIC #42 :Testing ft_irc
```

Send a channel message:

```text
PRIVMSG #42 :Hello everyone
```

Send a private message:

```text
PRIVMSG akira :Hello Adam
```

Change a channel mode:

```text
MODE #42 +t
```

You can open another terminal and connect a second client to test communication between users.

## Basic Manual Test

Start the server:

```bash
./irc 6667 00
```

Open a second terminal:

```bash
nc -C 127.0.0.1 6667
```

Register `kaw`:

```text
PASS 00
NICK kaw
USER Kawtar 0 * :Kawtar
```

Join:

```text
JOIN #42
```

Set the topic:

```text
TOPIC #42 :Welcome to ft_irc
```

Send a message:

```text
PRIVMSG #42 :Hello from kaw
```

Open another terminal and connect:

```bash
nc -C 127.0.0.1 6667
```

Register `akira`:

```text
PASS 00
NICK akira
USER Adam 0 * :Adam
```

Join the same channel:

```text
JOIN #42
```

Now test a private message:

```text
PRIVMSG kaw :Hello Kawtar
```

### Running the tester

Start the server:

```bash
./irc 6667 00
```

Then run:

```bash
python3 testing.py
```

The default connection is:

```text
127.0.0.1:6667
```

with password:

```text
00
```

### Valgrind

Valgrind can be used to check memory management:

```bash
valgrind --leak-check=full --show-leak-kinds=all ./irc 6667 00
```
