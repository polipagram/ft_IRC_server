#include "../../includes/irc_server.hpp"

bool let_s_change_the_topic(Client &c, Message &m, Channel &chan, std::vector<Client> &cs,
                            Server &s)
{
    const std::string &mode = m.params[1];

    if (mode != "+t" && mode != "-t")
        return false;

    if (mode == "+t")
        chan.set_change_topic(true);
    else
        chan.set_change_topic(false);

    print_modes(mode, chan.getName(), "");

    std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " " + mode + "\r\n";

    notification(chan, cs, s, msg);

    return true;
}