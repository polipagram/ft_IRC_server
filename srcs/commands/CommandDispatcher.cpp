#include "../../includes/LogicCore.hpp"
#include "../../includes/irc_server.hpp"
#include "../../includes/Server.hpp"
#include <cctype>

void dispatchCommand(Client &client, const std::string &line, Server &server)
{
    Message message = Parser::parse(line);
    std::string command = message.cmd;

    // Commandes IRC ma kayferr9och bin majuscule w minuscule.
    for (size_t i = 0; i < command.size(); ++i)
        command[i] = static_cast<char>(std::toupper(static_cast<unsigned char>(command[i])));

    if (command == "PASS")
        passHundler(client, message, server);
    else if (command == "NICK")
        nickHundler(client, message, server);
    else if (command == "USER")
        userHandler(client, message, server);
    else if (command == "JOIN")
        joinHandler(client, message, server);
    else if (command == "PRIVMSG")
        privmsgHandler(client, message, server);
    else if (command == "TOPIC")
        topicHandler(client, message, server);
    else if (command == "KICK")
        kickHandler(client, message, server);
    else if (command == "INVITE")
        inviteHandler(client, message, server);
    else if (!command.empty())
        // client.sendMessgToClient(replyCmd(421, client, command));
        // kaw : bedelt logic dyal send finma kayna sendMessgtoClient 
        // li kenty dayer feha had function 
        server.sending_queue(client, replyCmd(421, client, command)); 
}
