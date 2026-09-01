#include "../../includes/irc_server.hpp"

bool limited_usage(Client &c, Message &m, Channel &chan, std::vector<Client> &cs, Server &s)
{
    const std::string &mode = m.params[1];

    if (mode != "+l" && mode != "-l")
        return false;

    if (mode == "-l")
    {
        chan.remove_limit();

        print_modes(mode, chan.getName(), "");

        std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " -l\r\n";

        notification(chan, cs, s, msg);

        return true;
    }

    if (m.params.size() < 3)
    {
        s.sending_queue(c, replyCmd(461, c, "MODE"));
        return true;
    }

    const std::string &limit_str = m.params[2];

    bool valid = !limit_str.empty();

    for (size_t i = 0; i < limit_str.size() && valid; ++i)
    {
        if (!std::isdigit(static_cast<unsigned char>(limit_str[i])))
            valid = false;
    }

    if (!valid)
    {
        s.sending_queue(c, replyCmd(461, c, "MODE"));
        return true;
    }

    int limit = std::atoi(limit_str.c_str());

    if (limit <= 0)
    {
        s.sending_queue(c, replyCmd(461, c, "MODE"));
        return true;
    }

    chan.set_limit(limit);

    print_modes(mode, chan.getName(), limit_str);

    std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " +l " + limit_str + "\r\n";

    notification(chan, cs, s, msg);

    return true;
}