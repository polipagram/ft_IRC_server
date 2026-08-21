#include "../../includes/irc_server.hpp"

void inviteHandler(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        client.sendMessgToClient(replyCmd(451, client, "INVITE"));
        return;
    }
    if (message.params.size() < 2)
    {
        client.sendMessgToClient(replyCmd(461, client, "INVITE"));
        return;
    }

    const std::string &targetNick = message.params[0];
    const std::string &channelName = message.params[1];
    std::vector<Client> &clients = server.getClients();
    std::vector<Channel> &channels = server.getChannels();
    Client *target = NULL;
    Channel *channel = NULL;

    for (size_t i = 0; i < clients.size(); ++i)
    {
        if (clients[i].getNickname() == targetNick)
            target = &clients[i];
    }
    if (target == NULL)
    {
        client.sendMessgToClient(replyCmd(401, client, targetNick));
        return;
    }

    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channelName)
            channel = &channels[i];
    }
    if (channel == NULL)
    {
        client.sendMessgToClient(replyCmd(403, client, channelName));
        return;
    }
    if (!channel->isOperator(client.getFd()))
    {
        client.sendMessgToClient(replyCmd(482, client, channelName));
        return;
    }
    if (channel->hasMember(target->getFd()))
    {
        client.sendMessgToClient(replyCmd(443, client, targetNick + " " + channelName));
        return;
    }

    // Kan7fed invitation bach MODE +i ymken l-target ydkhol mn ba3d.
    channel->addInvite(target->getFd());
    target->sendMessgToClient(":" + client.getNickname() + " INVITE " + targetNick +
                              " :" + channelName + "\r\n");
    client.sendMessgToClient(replyCmd(341, client, targetNick + " " + channelName));
}
