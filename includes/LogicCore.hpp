#ifndef LOGIC_CORE_HPP
#define LOGIC_CORE_HPP

#include <string>

class Client;
class Server;

void dispatchCommand(Client &client, const std::string &line, Server &server);

#endif
