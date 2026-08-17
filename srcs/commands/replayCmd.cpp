#include "irc_server.hpp"

std::string replyCmd(int code, const Client& c, const std::string& cmd)
{
    switch (code)
    {
        case 1:
            return ":ircserv 001 " + c.getNickname() +
                   " :Welcome to the Internet Relay Network " +
                   c.getNickname() + "\r\n";

        case 331:
            return ":ircserv 331 " + c.getNickname() +
                   " " + cmd + " :No topic is set\r\n";

        case 332:
            return ":ircserv 332 " + c.getNickname() +
                   " " + cmd + " :Topic\r\n";

        case 341:
            return ":ircserv 341 " + c.getNickname() +
                   " " + cmd + " :Inviting\r\n";

        case 353:
            return ":ircserv 353 " + c.getNickname() +
                   " " + cmd + " :Names\r\n";

        case 366:
            return ":ircserv 366 " + c.getNickname() +
                   " " + cmd + " :End of /NAMES list\r\n";

        case 324:
            return ":ircserv 324 " + c.getNickname() +
                   " " + cmd + " :Channel mode\r\n";

        case 401:
            return ":ircserv 401 " + c.getNickname() +
                   " " + cmd + " :No such nick/channel\r\n";

        case 403:
            return ":ircserv 403 " + c.getNickname() +
                   " " + cmd + " :No such channel\r\n";

        case 404:
            return ":ircserv 404 " + c.getNickname() +
                   " " + cmd + " :Cannot send to channel\r\n";

        case 421:
            return ":ircserv 421 " + c.getNickname() +
                   " " + cmd + " :Unknown command\r\n";

        case 431:
            return ":ircserv 431 " + c.getNickname() +
                   " :No nickname given\r\n";

        case 432:
            return ":ircserv 432 " + c.getNickname() +
                   " " + cmd + " :Erroneous nickname\r\n";

        case 433:
            return ":ircserv 433 " + c.getNickname() +
                   " " + cmd + " :Nickname is already in use\r\n";

        case 441:
            return ":ircserv 441 " + c.getNickname() +
                   " " + cmd + " :They aren't on that channel\r\n";

        case 442:
            return ":ircserv 442 " + c.getNickname() +
                   " " + cmd + " :You're not on that channel\r\n";

        case 443:
            return ":ircserv 443 " + c.getNickname() +
                   " " + cmd + " :is already on channel\r\n";

        case 451:
            return ":ircserv 451 " + c.getNickname() +
                   " :You have not registered\r\n";

        case 461:
            return ":ircserv 461 " + c.getNickname() +
                   " " + cmd + " :Not enough cmdeters\r\n";

        case 462:
            return ":ircserv 462 " + c.getNickname() +
                   " :Unauthorized command (already registered)\r\n";

        case 464:
            return ":ircserv 464 " + c.getNickname() +
                   " :Password incorrect\r\n";

        case 471:
            return ":ircserv 471 " + c.getNickname() +
                   " " + cmd + " :Cannot join channel (+l)\r\n";

        case 472:
            return ":ircserv 472 " + c.getNickname() +
                   " " + cmd + " :is unknown mode char to me\r\n";

        case 473:
            return ":ircserv 473 " + c.getNickname() +
                   " " + cmd + " :Cannot join channel (+i)\r\n";

        case 475:
            return ":ircserv 475 " + c.getNickname() +
                   " " + cmd + " :Cannot join channel (+k)\r\n";

        case 482:
            return ":ircserv 482 " + c.getNickname() +
                   " " + cmd + " :You're not channel operator\r\n";

        default:
            return "";
    }
}