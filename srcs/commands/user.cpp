#include "../../includes/irc_server.hpp"


void userHandler(Client &client, Message &message, Server &server)
{
    (void)server;

    if (client.isRegistered())
    {
        server.sending_queue(client, replyCmd(462, client, "USER"));
        return;
    }

    if (!client.passIsRecived())
    {
        server.sending_queue(client, replyCmd(451, client, "USER :You have not registered"));
        return;
    }

    if (message.params.size() < 4)
    {
        server.sending_queue(client, replyCmd(461, client, "USER"));
        return;
    }

    client.setUsername(message.params[0]);
    client.setUserIsRecived(true);

    if (client.nicknameIsReceived())
    {
        client.setRegistered(true);
        server.sending_queue(client, replyCmd(1, client, ""));
    }
}
