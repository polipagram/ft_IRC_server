#include "../includes/Server.hpp"
#include "../includes/LogicCore.hpp"
#include <cerrno>

volatile sig_atomic_t _shutdown = 0;

void sig_handler(int sig)
{
    if (sig == SIGINT)
        _shutdown = 1;
}

Server::Server(int port, const std::string &passwd) : fd(-1), port(port), passwd(passwd), loaded(true)
{
    if (this->port < 1 || this->port > 65535)
        throw std::runtime_error("invalid port!");
    std::signal(SIGINT, sig_handler);
    open_socket();
    binding();
    listening();
    poll_setup();
}

Server::~Server()
{
    for (size_t i = 1; i < fds.size(); i++)
        close(fds[i].fd);
    if (this->fd != -1)
        close(fd);
}

void Server::open_socket()
{
    this->fd = socket(AF_INET, SOCK_STREAM, 0);

    if (this->fd == -1)
        throw std::runtime_error("failed to open socket!");

    int opt = 1;

    if(setsockopt(this->fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1)
    {
        close(this->fd);
        this->fd = -1;
        throw std::runtime_error("socket option failed!");
    }

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

void Server::disconnect(size_t i)
{
    int fd_client = this->fds[i].fd;

    std::cout << "Client " << fd_client << " disconnected" << std::endl;

    leave_chanels(fd_client);

    close(fd_client);

    this->fds.erase(this->fds.begin() + i);
    this->clients.erase(this->clients.begin() + (i - 1));
}

void Server::extract_msg(size_t i)
{
    std::string& buffer = this->clients[i - 1].get_buff();

    size_t pos;

    while ((pos = buffer.find('\n')) != std::string::npos)
    {
        std::string msg = buffer.substr(0, pos);
        buffer.erase(0, pos + 1);
        if (!msg.empty() && msg[msg.size() - 1] == '\r')
            msg.erase(msg.size() - 1);
        dispatchCommand(this->clients[i - 1], msg, *this);
    }
}

bool  Server::handle_send(size_t i)
{
    Client &client = this->clients[i - 1];
    std::string &buffer = client.get_send_buff();

    if (!client.send_data())
    {
        this->fds[i].events &= ~POLLOUT;
        return false;
    }

    int bytes = send(this->fds[i].fd, buffer.c_str(), buffer.size(), MSG_NOSIGNAL);

    if (bytes > 0)
    {
        buffer.erase(0, bytes);
        if (!client.send_data())
            this->fds[i].events &= ~POLLOUT;
        return false;
    }
    if (bytes == -1 && (errno == EAGAIN || errno == EWOULDBLOCK))
            return false;
    disconnect(i);
    return true;
}

void Server::sending_queue(Client &client, const std::string &message)
{
    if (message.empty())
        return;

    client.append_send_buff(message);

    for (size_t i = 1; i < fds.size(); i++)
    {
        if (&clients[i - 1] == &client)
        {
            fds[i].events |= POLLOUT;
            break;
        }
    }
}

bool Server::handle_user(size_t i)
{
    char buffer[4006];

    int bytes = recv(this->fds[i].fd, buffer, sizeof(buffer) - 1,0);

    if (bytes > 0)
    {
        this->clients[i - 1].append_buff(std::string(buffer, bytes));
        extract_msg(i);
        return false;
    }

    if (bytes == 0)
    {
        disconnect(i);
        return true;
    }

    if (errno == EAGAIN || errno == EWOULDBLOCK)
    return false;
    
    std::cerr << "recv failed on " << this->fds[i].fd << std::endl;
    disconnect(i);
    return true;
}

void Server::shutdown()
{
    std::string msg = " -_- Server shutting down\r\n";

    for (size_t i = 1; i < this->fds.size(); ++i)
    {
        int fd_c = this->fds[i].fd;
        send(fd_c, msg.c_str(), msg.size(), MSG_NOSIGNAL);
        std::cout << "Closing client fd: " << fd_c << std::endl;

        if (close(fd_c) == -1)
            std::cerr << "close failed: " << strerror(errno) << std::endl;
        else
            std::cout << "Client fd " << fd_c << " closed successfully" << std::endl;
    }

    while (this->fds.size() > 1)
        disconnect(1);

    this->channels.clear();
    this->clients.clear();
    this->fds.clear();

    if (this->fd != -1)
    {
        close(this->fd);
        this->fd = -1;
    }

    std::cout << " -_- Server shutting down..." << std::endl;
}

void Server::launch()
{
    while (!_shutdown)
    {
        int polling = poll(&this->fds[0], this->fds.size(), -1);
        if (polling == -1)
        {
            if (errno == EINTR)
                continue;

            throw std::runtime_error("poll failed!");
        }
        for (size_t i = 0; i < this->fds.size();)
        {
            if (this->fds[i].revents == 0)
            {
                i++;
                continue;
            }

            if (this->fds[i].fd == this->fd)
            {
                if (this->fds[i].revents & POLLIN)
                    connect();
                i++;
                continue;
            }

            if (this->fds[i].revents & POLLIN)
            {
                if (handle_user(i))
                    continue;
            }

            if (this->fds[i].revents & (POLLERR | POLLHUP | POLLNVAL))
            {
                disconnect(i);
                continue;
            }

            if (this->fds[i].revents & POLLOUT)
            {
                if (handle_send(i))
                    continue;
            }
            i++;
        }
    }
    shutdown();
}

std::vector<Client> &Server::getClients()
{
    return clients;
}

std::vector<Channel> &Server::getChannels()
{
    return channels;
}

std::string Server::get_passwd() const
{
    return passwd;
}

void Server::leave_chanels(int fd)
{
    for (size_t i = 0; i < channels.size();)
    {
        channels[i].removeMember(fd);
        channels[i].remove_invite(fd);
        channels[i].remove_operator(fd);

        if (channels[i].isEmpty())
            channels.erase(channels.begin() + i);
        else
            i++;
    }
}