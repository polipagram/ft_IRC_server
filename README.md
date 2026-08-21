# ft_irc

`ft_irc` is a custom Internet Relay Chat (IRC) server developed in C++98 . The project aims to recreate the core functionality of an IRC server while adhering to the IRC protocol, enabling multiple clients to communicate in real time through channels and private messages.

The server is designed to be compatible with standard IRC clients, handling client connections, authentication, channel management, user commands, and message broadcasting while emphasizing socket programming, network communication, and object-oriented design.

## Recent integration changes

The following changes were made to make the parser, command handlers, and the
server work together.

| Change | Why it was needed |
| --- | --- |
| Added parser and command `.cpp` files to `Makefile` | They were not compiled or linked, so `PASS`, `NICK`, and parsing could never run in the server. |
| Fixed include paths in `Parser.cpp` and `srcs/commands/` | Those files are two directories below `includes/`; the previous paths prevented compilation. |
| Restored the `Server.hpp` declarations used by `Server.cpp` | The header did not declare `launch`, poll helpers, client handling, or the poll/client vectors, causing build errors. |
| Kept `fds` and `clients` as vectors | `Server.cpp` already uses indexing and `push_back`; its previous header declared a map, which was incompatible. |
| Added `Client::sendMessgToClient()` | Command handlers need a real member function to send IRC replies to the specific client. The old free function discarded the message. |
| Added shared declarations for `PASS`, `NICK`, `JOIN`, and replies | `Server.cpp` needs those declarations to dispatch parsed commands safely. |
| Added command dispatch in `Server::process_command()` | After a complete `\r\n` line is received, the server now parses it and routes `PASS` and `NICK`; unknown commands return `421`. |
| Added `Server::getPass()` and `Server::isNicknameInUse()` | These names are used by the existing command handlers; they now delegate to the server's existing password and nickname logic. |
| Fixed the client index offset | `fds[0]` is the listening socket but `clients[0]` is the first client. Using `clients[i]` caused an out-of-bounds access and a crash; client socket `fds[i]` now uses `clients[i - 1]`. |
| Improved `NICK` validation | Character checks now safely use `unsigned char`, and nickname length is limited to 9 characters. |
| Corrected the `461` reply text | Changed `Not enough cmdeters` to `Not enough parameters`. |

Verification performed: `make re` succeeds with `-Wall -Wextra -Werror -std=c++98`.
A local socket test also verified that `PASS secret`, `NICK akira`, and an unknown
command return the expected replies without crashing the server.


# TCP Listening Socket

A **TCP listening socket** is a passive socket used by a server to wait for incoming client connections.

## Server Socket Setup

```mermaid
flowchart LR
    A["1. socket()<br/><br/>Create socket<br/><br/>fd = socket(AF_INET, SOCK_STREAM, 0)"]
    B["2. bind()<br/><br/>Bind to IP + port<br/><br/>0.0.0.0:8080"]
    C["3. listen()<br/><br/>Mark as passive<br/><br/>LISTEN state"]
    D["4. accept()<br/><br/>Accept connection<br/><br/>new_fd = accept(fd, ...)"]
    E["5. Communicate<br/><br/>read() / write()<br/><br/>new_fd"]

    A --> B --> C --> D --> E
```

---

# What Happens When a Client Connects?

The important thing to understand is that **the listening socket does not communicate with the client**.

It only waits for connections.

```mermaid
sequenceDiagram
    participant C as Client
    participant K as Kernel
    participant S as Server

    C->>K: SYN
    K-->>C: SYN + ACK
    C->>K: ACK

    Note over K: TCP connection established

    K->>K: Put connection into accept queue

    S->>K: accept(listening_fd)
    K-->>S: new_fd

    Note over S: new_fd is dedicated to this client

    S->>C: read() / write()
```

---

# Listening Socket vs Connected Socket

This distinction is **very important**.

```mermaid
flowchart TB
    L["Listening Socket<br/><br/>fd<br/>State: LISTEN<br/><br/>0.0.0.0:8080"]

    Q["Kernel<br/><br/>Accept Queue<br/><br/>Completed connections waiting<br/>to be accepted"]

    C1["Connected Socket<br/><br/>new_fd #1<br/>Client A"]
    C2["Connected Socket<br/><br/>new_fd #2<br/>Client B"]
    C3["Connected Socket<br/><br/>new_fd #3<br/>Client C"]

    L -->|"Incoming connections"| Q
    Q -->|"accept()"| C1
    Q -->|"accept()"| C2
    Q -->|"accept()"| C3

    L -.->|"Remains open"| L
```

The key idea is:

```text
                 SERVER

        ┌─────────────────────┐
        │  Listening Socket   │
        │         fd          │
        │      LISTEN         │
        │     port 8080       │
        └──────────┬──────────┘
                   │
                   │ incoming connections
                   ▼
        ┌─────────────────────┐
        │     Accept Queue    │
        │                     │
        │  [client A]         │
        │  [client B]         │
        │  [client C]         │
        └──────────┬──────────┘
                   │
                 accept()
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       new_fd1  new_fd2  new_fd3
          │        │        │
       Client A Client B Client C
```

---

# TCP Three-Way Handshake

The handshake happens **before the server receives the connection through `accept()`**.

```text
Client                         Server

   │                              │
   │────────── SYN ──────────────>│
   │                              │
   │<────── SYN + ACK ────────────│
   │                              │
   │────────── ACK ──────────────>│
   │                              │
   │       Connection established │
   │                              │
   │                              │
   │                    Accept Queue
   │                         │
   │                         ▼
   │                      accept()
   │                         │
   │                         ▼
   │                       new_fd
   │                              │
   │<─────── data ───────────────>│
```

The **kernel handles the TCP handshake**.

Your server application normally does not manually send the SYN/SYN-ACK/ACK.

---

# Typical Socket States

```mermaid
stateDiagram-v2
    [*] --> LISTEN: listen()

    LISTEN --> SYN_RCVD: Client sends SYN

    SYN_RCVD --> ESTABLISHED_QUEUE: Handshake completed

    ESTABLISHED_QUEUE --> ESTABLISHED: accept()

    ESTABLISHED --> [*]: close(new_fd)
```


# Key Characteristics

| Characteristic                  | Meaning                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| **Passive**                     | The listening socket waits for incoming connections.             |
| **LISTEN state**                | `listen()` puts the socket into listening mode.                  |
| **Accept queue**                | Completed connections wait here until `accept()` retrieves them. |
| **New socket per client**       | Every successful `accept()` returns a new connected socket.      |
| **Listening socket stays open** | The original socket continues accepting new clients.             |
| **Same port, many clients**     | Multiple clients can connect through the same listening port.    |
| **Kernel handles handshake**    | TCP's three-way handshake is handled by the OS kernel.           |

---
