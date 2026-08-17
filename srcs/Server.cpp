#include "../includes/Server.hpp"

Server::Server(int port, const std::string &passwd) : fd(-1), port(port), passwd(passwd)
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
    if (this->fd != -1)
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
         std::cerr << "bind failed: "
              << std::strerror(errno)
              << std::endl;
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

void Server::connect()
{
    int fd_client = accept(this->fd, NULL, NULL);

    if (fd_client == -1)
        return;

    if (fcntl(fd_client, F_SETFL, O_NONBLOCK) == -1)
    {
        close(fd_client);
        return;
    }

    struct pollfd client_poll;

    client_poll.fd = fd_client;
    client_poll.events = POLLIN;
    client_poll.revents = 0;

    this->fds.push_back(client_poll);
    this->clients.push_back(Client(fd_client));

    std::cout << "New client connected: " << fd_client << std::endl;
}

void Server::extract_msg(size_t i)
{
    std::string& buffer = this->clients[i].get_buff();

    size_t pos;

    while ((pos = buffer.find("\r\n")) != std::string::npos)
    {
        std::string msg = buffer.substr(0, pos);
        buffer.erase(0, pos + 1);
        // hna khassna nparsiw lmsg to separate nick from text
        std::cout << "MSG from Client " << this->fds[i].fd << " : " << msg << std::endl;
    }
}

bool Server::handle_user(size_t i)
{
    char buffer[1024];

    int bytes = recv(this->fds[i].fd, buffer, sizeof(buffer) - 1,0);

    if (bytes > 0)
    {
        this->clients[i].append_buff(std::string(buffer, bytes));
        extract_msg(i);
        return false;
    }

    if (bytes == 0)
    {
        disconnect(i);
        return true;
    }

    std::cerr << "recv failed on !" << this->fds[i].fd << std::endl;
    close(this->fds[i].fd);
    this->fds.erase(this->fds.begin() + i);
    this->clients.erase(this->clients.begin() + i);

    return true;
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
                connect();
            }
            else
            {
                if (handle_user(i))
                    i--;
            }
        }
    }
}

// this function is the fnction li katcheki nicknames

bool Server::existing_nick(const std::string& nickname) const
{
    for (size_t i = 0; i < clients.size(); ++i)
    {
        if (clients[i].getNickname() == nickname)
            return true;
    }

    return false;
}

Client& Server::get_client(size_t i)
{
    return this->clients[i];
}

// added this it was removed by merge

std::string Server::get_passwd() const
{
    return this->passwd;
}

void Server::disconnect(size_t i)
{
    int fd_client = this->fds[i].fd;

    std::cout << "Client " << fd_client << " disconnected" << std::endl;

    close(fd_client);

    this->fds.erase(this->fds.begin() + i);
    this->clients.erase(this->clients.begin() + i);
}

