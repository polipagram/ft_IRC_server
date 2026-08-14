#include "Server.hpp"



Server::Server(int port, const std::string &passwd) : fd(-1), port(port) , passwd(passwd)
{

}

Server::~Server()
{
    if(this->fd != -1)
        close(fd);
}

void Server::open_socket()
{
    this->fd = socket(AF_INET, SOCK_STREAM, 0);

    if (this->fd == -1)
        throw std::runtime_error("socket() failed");
}
