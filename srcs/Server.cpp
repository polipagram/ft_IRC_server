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

void   Server::launch()
{
    while(true)
    {
        int polling = poll(&this->fds[0], this->fds.size(), -1);
        if(polling == -1)
            throw std::runtime_error("poll fialed!");
        for(size_t i = 0; i < this->fds.size() ; i++)
        {
            if(this->fds[i].revents == 0)
                continue;
            if(this->fds[i].fd == this->fd)
            {
                int fd_client = accept(this->fd, NULL, NULL);
                if(fd_client == -1)
                    continue;
                    
                struct pollfd client_poll;

                client_poll.fd = fd_client;
                client_poll.events = POLLIN;
                client_poll.revents = 0;

                this->fds.push_back(client_poll);
                
            }
        }
    }
}