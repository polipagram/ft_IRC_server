#include "Server.hpp"



Server::Server(int port, const std::string &passwd) : fd(-1), port(port) , passwd(passwd)
{
    open_socket();
    binding();
    std::cout << "socket ready to go !\n"; 
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
        throw std::runtime_error("failed to open socket");
}

void Server::binding()
{
    sockaddr_in adr;
    std::memset(&adr, 0, sizeof(adr));

    adr.sin_family = AF_INET;
    adr.sin_addr.s_addr = htonl(INADDR_ANY);
    adr.sin_port = htons(this->port);

    if (bind(this->fd, reinterpret_cast<sockaddr *>(&adr), sizeof(adr)) == -1)
    {
        close(this->fd);
            this->fd = -1;
        throw std::runtime_error("bind() failed");
    }
}
