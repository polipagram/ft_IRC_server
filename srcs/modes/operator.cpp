#include "../../includes/irc_server.hpp"

bool operators(Client &c, Message &m, Channel &chan, std::vector<Client> &cs, Server &s)
{
    const std::string &mode = m.params[1];

    if (mode != "+o" && mode != "-o")
        return false;

    if (m.params.size() < 3)
    {
        s.sending_queue(c, replyCmd(461, c, "MODE"));
        return true;
    }

    const std::string &user_nick = m.params[2];

    Client *target = NULL;

    for (size_t i = 0; i < cs.size(); ++i)
    {
        if (cs[i].getNickname() == user_nick)
        {
            target = &cs[i];
            break;
        }
    }

    if (target == NULL)
    {
        s.sending_queue(c, replyCmd(401, c, user_nick));
        return true;
    }

    if (!chan.hasMember(target->getFd()))
    {
        s.sending_queue(c,replyCmd(441, c, user_nick + " " + chan.getName()));
        return true;
    }

    if (mode == "+o")
    {
        if (chan.isOperator(target->getFd()))
            return true;
        chan.addOperator(target->getFd());
    }
    else
    {
        if (!chan.isOperator(target->getFd()))
            return true;

        if (chan.getOperatorFds().size() == 1)
        {
            std::string msg = ":ircserv NOTICE " + c.getNickname() + " :You cannot remove the last channel operator\r\n";

            s.sending_queue(c, msg);
            return true;
        }

        chan.remove_operator(target->getFd());
    }

    print_modes(mode, chan.getName(), user_nick);

    std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " " + mode + " " + user_nick + "\r\n";

    notification(chan, cs, s, msg);

    return true;
}