#ifndef SERVER_HPP
#define SERVER_HPP

#include <string>
#include <fstream>
#include <unistd.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <iostream>
#include <netinet/in.h>   
#include <cstring> 

class Server
{
    private:
        int         fd;
        int         port;
        std::string passwd;

        void open_socket();
        void binding();
        void listening();
        
    public:
        Server(int port, const std::string& passwd);
        ~Server();
};

#endif