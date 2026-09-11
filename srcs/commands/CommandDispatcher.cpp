#include "../../includes/LogicCore.hpp"
#include "../../includes/irc_server.hpp"
#include "../../includes/Server.hpp"
#include "../../includes/Channel.hpp"
#include <cctype>

void dispatchCommand(Client &client, const std::string &line, Server &server)
{
    Message message = Parser::parse(line);
    std::string command = message.cmd;

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
    else if (command == "MODE")
        modes(client, message, server);
    else if (!command.empty())
        server.sending_queue(client, replyCmd(421, client, command)); 
}
