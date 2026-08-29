#include "../../includes/irc_server.hpp"

void topicHandler(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "TOPIC"));
        return;
    }

    if (message.params.empty())
    {
        server.sending_queue(client, replyCmd(461, client, "TOPIC"));
        return;
    }

    const std::string &channelName = message.params[0];
    std::vector<Channel> &channels = server.getChannels();
    std::vector<Client> &clients = server.getClients();
    Channel *channel = NULL;
    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channelName)
            channel = &channels[i];
    }
    if (channel == NULL)
    {
        server.sending_queue(client, replyCmd(403, client, channelName));
        return;
    }

    // TOPIC #channel bla text katsift ghir topic li kayna daba.
    if (message.params.size() == 1)
    {
        if (channel->getTopic().empty())
            server.sending_queue(client, replyCmd(331, client, channelName));
        else
            server.sending_queue(client, ":ircserv 332 " + client.getNickname() + " " +
                                     channelName + " :" + channel->getTopic() + "\r\n");
        return;
    }

    if (!channel->hasMember(client.getFd()))
    {
        server.sending_queue(client, replyCmd(442, client, channelName));
        return;
    }
    
    // kaw

    if (channel->is_change_topic() && !channel->isOperator(client.getFd()))
    {
        server.sending_queue(client, replyCmd(482, client, channelName));
        return;
    }

    const std::string &newTopic = message.params[1];
    // Topic katb9a f Channel; restriction dyal operator ghadi tzad m3a MODE +t.
    channel->setTopic(newTopic);

    const std::string wireMessage = ":" + client.getNickname() + " TOPIC " +
                                    channelName + " :" + newTopic + "\r\n";
    // Kanbroadcastew l-members l-okhrin, w kan2ekdo l-sender b nafs message.
    const std::vector<int> &members = channel->getMemberFds();
    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i] && clients[j].getFd() != client.getFd())
                server.sending_queue(clients[j], wireMessage);
        }
    }
    server.sending_queue(client, wireMessage);
}
