#ifndef SERVER_HPP
#define SERVER_HPP

#include <string>
#include <fstream>
#include <unistd>
#include <sys/socket.h>

class Server
{
    private:
        int         fd;
        int         port;
        std::string passwd;

        void open_socket();
    public:
        Server(int port, const std::string& passwd);
        ~Server();
};

#endif