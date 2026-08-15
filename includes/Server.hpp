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
#include <fcntl.h>
#include <vector>
#include <poll.h>

class Server
{
    private:
        int         fd;
        int         port;
        std::string passwd;
        std::vector<struct pollfd>  fds;

        void open_socket();
        void binding();
        void listening();
        void poll_setup();
        
        public:
            Server(int port, const std::string& passwd);
            ~Server();
            void launch();

};

#endif