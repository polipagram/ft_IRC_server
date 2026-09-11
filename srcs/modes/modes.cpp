#include "../../includes/irc_server.hpp"

void print_modes(const std::string &mode,const std::string &channel_name, const std::string &Nick)
{
    std::cout << "[MODE] " << channel_name << " " << mode;

    if (!Nick.empty())
        std::cout << " " << Nick;

    std::cout << std::endl;
}

void notification(Channel &channel, std::vector<Client> &clients, Server &server, std::string &msg)
{
    const std::vector<int> &members = channel.getMemberFds();

    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i])
            {
                server.sending_queue(clients[j], msg);
                break;
            }
        }
    }
}

void modes(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "MODE"));
        return;
    }

    if (message.params.size() < 2)
    {
        server.sending_queue(client, replyCmd(461, client, "MODE"));
        return;
    }

    const std::string &channel_name = message.params[0];

    std::vector<Channel> &channels = server.getChannels();
    std::vector<Client> &clients = server.getClients();

    Channel *channel = NULL;

    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channel_name)
        {
            channel = &channels[i];
            break;
        }
    }

    if (channel == NULL)
    {
        server.sending_queue(client, replyCmd(403, client, channel_name));
        return;
    }
    if (!channel->isOperator(client.getFd()))
    {
        server.sending_queue(client, replyCmd(482, client, channel_name));
        return;
    }
    if (invite_only(client, message, *channel, clients, server))
        return;
    if (let_s_change_the_topic(client, message, *channel, clients, server))
        return;
    if (secret_key(client, message, *channel, clients, server))
        return;
    if (limited_usage(client, message, *channel, clients, server))
        return;
    if (operators(client, message, *channel, clients, server))
        return;
    server.sending_queue(client, replyCmd(472, client, message.params[1]));
}
