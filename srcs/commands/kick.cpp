#include "../../includes/irc_server.hpp"

void kickHandler(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "KICK"));
        return;
    }
    if (message.params.size() < 2)
    {
        server.sending_queue(client, replyCmd(461, client, "KICK"));
        return;
    }

    const std::string &channelName = message.params[0];
    const std::string &targetNick = message.params[1];
    std::vector<Channel> &channels = server.getChannels();
    std::vector<Client> &clients = server.getClients();
    Channel *channel = NULL;
    size_t channelIndex = 0;

    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channelName)
        {
            channel = &channels[i];
            channelIndex = i;
        }
    }
    if (channel == NULL)
    {
        server.sending_queue(client, replyCmd(403, client, channelName));
        return;
    }
    if (!channel->isOperator(client.getFd()))
    {
        server.sending_queue(client, replyCmd(482, client, channelName));
        return;
    }

    Client *target = NULL;
    for (size_t i = 0; i < clients.size(); ++i)
    {
        if (clients[i].getNickname() == targetNick)
            target = &clients[i];
    }
    if (target == NULL)
    {
        server.sending_queue(client, replyCmd(401, client, targetNick));
        return;
    }
    if (!channel->hasMember(target->getFd()))
    {
        server.sending_queue(client, replyCmd(441, client, targetNick + " " + channelName));
        return;
    }

    const std::string reason = message.params.size() > 2 ? message.params[2] : client.getNickname();
    const std::string wireMessage = ":" + client.getNickname() + " KICK " + channelName +
                                    " " + targetNick + " :" + reason + "\r\n";
    const std::vector<int> members = channel->getMemberFds();
    // Kan3lmo target w ga3 members qbel ma n7iydoh mn channel.
    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i])
                server.sending_queue(clients[j], wireMessage);
        }
    }

    channel->removeMember(target->getFd());
    if (channel->isEmpty())
        channels.erase(channels.begin() + channelIndex);
}
