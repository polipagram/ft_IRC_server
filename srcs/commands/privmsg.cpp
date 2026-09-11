#include "../../includes/irc_server.hpp"

void privmsgHandler(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "PRIVMSG"));
        return;
    }
    if (message.params.empty())
    {
        server.sending_queue(client, replyCmd(411, client, ""));
        return;
    }
    if (message.params.size() < 2 || message.params[1].empty())
    {
        server.sending_queue(client, replyCmd(412, client, ""));
        return;
    }

    const std::string &target = message.params[0];
    const std::string &text = message.params[1];
    const std::string wireMessage = ":" + client.getNickname() + " PRIVMSG " +
                                    target + " :" + text + "\r\n";

    std::vector<Channel> &channels = server.getChannels();
    std::vector<Client> &clients = server.getClients();

    if (target[0] == '#')
    {
        Channel *channel = NULL;
        for (size_t i = 0; i < channels.size(); ++i)
        {
            if (channels[i].getName() == target)
                channel = &channels[i];
        }
        if (channel == NULL)
        {
            server.sending_queue(client, replyCmd(403, client, target));
            return;
        }
        if (!channel->hasMember(client.getFd()))
        {
            server.sending_queue(client, replyCmd(404, client, target));
            return;
        }
        const std::vector<int> &members = channel->getMemberFds();
        for (size_t i = 0; i < members.size(); ++i)
        {
            for (size_t j = 0; j < clients.size(); ++j)
            {
                if (clients[j].getFd() == members[i] && clients[j].getFd() != client.getFd())
                    server.sending_queue(clients[j], wireMessage);
            }
        }
        return;
    }

    Client *recipient = NULL;
    for (size_t i = 0; i < clients.size(); ++i)
    {
        if (clients[i].getNickname() == target)
            recipient = &clients[i];
    }
    if (recipient == NULL)
    {
         server.sending_queue(client, replyCmd(401, client, target));
        return;
    }

    server.sending_queue(*recipient, wireMessage);
}
