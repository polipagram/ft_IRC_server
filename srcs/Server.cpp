#include "../includes/Server.hpp"
#include "../includes/LogicCore.hpp"
#include <cerrno>

bool _shutdown= false;

void sig_handler(int sig)
{
    if (sig == SIGINT)
        _shutdown = true;
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
    // Listening socket kaykoun f fds[0], donc client li kayqablo howa clients[i - 1].
    std::string& buffer = this->clients[i - 1].get_buff();

    size_t pos;

    // Kayqbel IRC standard (\r\n) w 7ta nc li kayseft ghir \n.
    while ((pos = buffer.find('\n')) != std::string::npos)
    {
        std::string msg = buffer.substr(0, pos);
        buffer.erase(0, pos + 1);
        // Kan7iydo \r ila line jat b CRLF qbel ma nwslo l-parser.
        if (!msg.empty() && msg[msg.size() - 1] == '\r')
            msg.erase(msg.size() - 1);
        // Ghir messages kamlin b line ending li kaywslou l-parser.
        // std::cout << "RAW COMMAND: [" << msg << "]" << std::endl;
        dispatchCommand(this->clients[i - 1], msg, *this);
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

    // Socket non-blocking t9der matlqach data mn ba3d poll, hadchi machi error.
    if (errno == EAGAIN || errno == EWOULDBLOCK)
        return false;

    std::cerr << "recv failed on " << this->fds[i].fd << std::endl;
    disconnect(i);
    return true;
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
        for (size_t i = 0; i < this->fds.size(); i++)
        {
            if (this->fds[i].revents == 0)
                continue;

            if (this->fds[i].fd == this->fd)
            {
                if (this->fds[i].revents & POLLIN)
                    connect();
                continue;
            }

            if (this->fds[i].revents & POLLIN)
            {
                if (handle_user(i))
                {
                    i--;
                    continue;
                }
            }

            // Kan7iydo socket ila lqina error, hang-up, wla descriptor maṣaliḥch.
            if (this->fds[i].revents & (POLLERR | POLLHUP | POLLNVAL))
            {
                disconnect(i);
                i--;
                continue;
            }

            if (this->fds[i].revents & POLLOUT)
            {
                if (handle_send(i))
                {
                    i--;
                    continue;
                }
            }
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

void Server::disconnect(size_t i)
{
    int fd_client = this->fds[i].fd;

    std::cout << "Client " << fd_client << " disconnected" << std::endl;

    leave_chanels(fd_client);

    close(fd_client);

    this->fds.erase(this->fds.begin() + i);
    // 3la 7sab l-offset bin fds w clients li mchar7 f Server.hpp.
    this->clients.erase(this->clients.begin() + (i - 1));
}


void Server::shutdown()
{
    std::string msg = " -_- Server shutting down\r\n";

    while (this->fds.size() > 1)
    {
        send(this->fds[1].fd, msg.c_str(), msg.size(), 0);
        disconnect(1);
    }

    this->fds.clear();
    this->clients.clear();

    if (this->fd != -1)
    {
        close(this->fd);
        this->fd = -1;
    }

    std::cout << " -_- Server shutting down..." << std::endl;
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

void Server::leave_chanels(int fd)
{
    for (size_t i = 0; i < channels.size();)
    {
        channels[i].removeMember(fd);
        channels[i].remove_invite(fd);

        if (channels[i].isEmpty())
            channels.erase(channels.begin() + i);
        else
            i++;
    }
}