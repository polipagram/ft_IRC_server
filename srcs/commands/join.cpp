#include "../../includes/irc_server.hpp"

static bool validChannelName(const std::string &channelName)
{
    if (channelName.size() < 2 || channelName[0] != '#')
        return false;

    for (size_t i = 1; i < channelName.size(); ++i)
    {
        if (channelName[i] == ' ' || channelName[i] == ',' || channelName[i] == ':' ||
            channelName[i] == '\r' || channelName[i] == '\n')
            return false;
    }
    return true;
}

void joinHandler(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "JOIN"));
        return;
    }

    if (message.params.empty())
    {
        server.sending_queue(client, replyCmd(461, client, "JOIN"));
        return;
    }

    const std::string &channelName = message.params[0];
    if (!validChannelName(channelName))
    {
        server.sending_queue(client, replyCmd(403, client, channelName));
        return;
    }

    std::vector<Channel> &channels = server.getChannels();
    Channel *channel = NULL;
    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channelName)
            channel = &channels[i];
    }

    if (channel == NULL)
    {
        channels.push_back(Channel(channelName));
        channel = &channels.back();
    }
    if (channel->hasMember(client.getFd()))
    {
        server.sending_queue(client, replyCmd(443, client, channelName));
        return;
    }
    if (channel->isInvite_only() && !channel->isInvited(client.getFd()))
    {
        server.sending_queue(client, replyCmd(473, client, channelName));
        return;
    }

    if (channel->has_key())
    {
        if (message.params.size() < 2 || message.params[1] != channel->get_key())
        {
            server.sending_queue(client, replyCmd(475, client, channelName));
            return;
        }
    }
    if (channel->has_limit() && static_cast<int>(channel->getMemberFds().size()) >= channel->get_limit())
    {
        server.sending_queue(client, replyCmd(471, client, channelName));
        return;
    }
    const bool firstMember = channel->isEmpty();
    channel->addMember(client.getFd());
    if (firstMember)
        channel->addOperator(client.getFd());

    const std::string joinMessage = ":" + client.getNickname() + " JOIN :" + channelName + "\r\n";
    const std::vector<int> &members = channel->getMemberFds();
    std::vector<Client> &clients = server.getClients();
    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i])
                server.sending_queue(clients[j], joinMessage);
        }
    }

    std::string names;
    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i])
            {
                if (!names.empty())
                    names += " ";
                if (channel->isOperator(members[i]))
                    names += "@";
                names += clients[j].getNickname();
            }
        }
    }

    server.sending_queue(client, ":ircserv 353 " + client.getNickname() + " = " +
                              channelName + " :" + names + "\r\n");
    server.sending_queue(client, ":ircserv 366 " + client.getNickname() + " " +
                              channelName + " :End of /NAMES list\r\n");
}
