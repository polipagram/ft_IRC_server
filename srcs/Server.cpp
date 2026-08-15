#include "../includes/Server.hpp"

Server::Server(int port, const std::string &passwd) : fd(-1), port(port) , passwd(passwd)
{
    if (this->port < 1 || this->port > 65535)
        throw std::runtime_error("invalid port!");
    open_socket();
    binding();
    listening();
    poll_setup();
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
        throw std::runtime_error("failed to open socket!");
    
    if (fcntl(this->fd, F_SETFL, O_NONBLOCK) == -1)
    {
        close(this->fd);
        this->fd = -1;
        throw std::runtime_error("fcntl failed!");
    }
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
        throw std::runtime_error("binding failed!");
    }
}

void Server::listening()
{
    if (listen(this->fd, SOMAXCONN) == -1)
    {
        close(this->fd);
        this->fd = -1;
        throw std::runtime_error("listening failed!");
    }
}

void Server::poll_setup()
{
    struct pollfd listen_socket;

    listen_socket.fd = this->fd;
    listen_socket.events = POLLIN;
    listen_socket.revents = 0;

    this->fds.push_back(listen_socket);
}