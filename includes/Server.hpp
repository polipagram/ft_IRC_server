#ifndef SERVER_HPP
#define SERVER_HPP

#include <string>
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
#include "Channel.hpp"
#include <csignal>

class Server
{
    private:
        int         fd;
        int         port;
        std::string passwd;
        bool loaded;

        std::vector<struct pollfd> fds;
        std::vector<Client> clients;
        std::vector<Channel> channels;

        void open_socket();
        void binding();
        void listening();
        void poll_setup();
        void connect();
        bool handle_user(size_t i);
        void extract_msg(size_t i);
        void disconnect(size_t i);
        void leave_chanels(int fd);

    public:
        Server(int port, const std::string& passwd);
        ~Server();
        void launch();
        std::vector<Client> &getClients();
        std::vector<Channel> &getChannels();
        std::string get_passwd() const;
        void shutdown();
        void sending_queue(Client &client, const std::string &message);
        bool handle_send(size_t i);




};

void sig_handler(int sig);

#endif
