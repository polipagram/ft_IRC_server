#include "../../includes/irc_server.hpp"


void userHandler(Client &client, Message &message, Server &server)
{
    (void)server;

    // Ila client deja registered, ma y9derch ybdel USER.
    if (client.isRegistered())
    {
        server.sending_queue(client, replyCmd(462, client, "USER"));
        return;
    }

    // 2. Khasso ydir PASS qbel USER (7sab logic dyal project dyalk).
    if (!client.passIsRecived())
    {
        server.sending_queue(client, replyCmd(451, client, "USER :You have not registered"));
        return;
    }

    // 3. USER khaso 4 parameters:
    // username, mode (0), unused (*), realname.
    if (message.params.size() < 4)
    {
        server.sending_queue(client, replyCmd(461, client, "USER"));
        return;
    }

    // 4. Kan7fdo username.
    client.setUsername(message.params[0]);
    client.setUserIsRecived(true);

    // Ila NICK deja tدار, USER howa akher 7aja naqsa bach ykml registration.
    if (client.nicknameIsReceived())
    {
        client.setRegistered(true);
        server.sending_queue(client, replyCmd(1, client, ""));
    }
}
