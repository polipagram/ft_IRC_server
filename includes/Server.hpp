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
#include "Client.hpp"

class Server
{
    private:
        int         fd;
        int         port;
        std::string passwd;
        std::vector<struct pollfd>  fds;
        std::vector<Client>         clients;

        void open_socket();
        void binding();
        void listening();
        void poll_setup();
        void new_user();
        bool    handle_user(size_t i);
        void   extract_msg(size_t i);



        public:
            Server(int port, const std::string& passwd);
            ~Server();
            void launch();
            bool existing_nick(const std::string& nickname) const;
            Client& get_client(size_t i);
            
};

#endif