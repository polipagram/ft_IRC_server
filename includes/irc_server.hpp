#ifndef IRC_SERVER_HPP
#define IRC_SERVER_HPP

#include "Channel.hpp"
#include "Client.hpp"
#include "Parser.hpp"
#include "Server.hpp"

std::string replyCmd(int code, const Client& c, const std::string& cmd);
// Hado homa les fonctions dyal commandes li process_command kay3ayt lihom mn ba3d parse.
void passHundler(Client &client, Message &message, Server &server);
void nickHundler(Client &client, Message &message, Server &server);
void joinHandler(Client &client, Message &message, Server &server);
void userHandler(Client &client, Message &message, Server &server);
void privmsgHandler(Client &client, Message &message, Server &server);
void topicHandler(Client &client, Message &message, Server &server);
void kickHandler(Client &client, Message &message, Server &server);
void inviteHandler(Client &client, Message &message, Server &server);
void modes(Client &client, Message &message, Server &server); // kaw
void notification(Channel &channel, std::vector<Client> &clients, Server &server, std::string &msg);



#endif
