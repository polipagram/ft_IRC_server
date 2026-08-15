#ifndef IRC_SERVER_HPP
#define IRC_SERVER_HPP

#include "Channel.hpp"
#include "Client.hpp"
#include "Parser.hpp"
#include "Server.hpp"

std::string replyCmd(int code, const Client& c, const std::string& cmd);




#endif