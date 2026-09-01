#include "../../includes/irc_server.hpp"

bool invite_only(Client &c, Message &m, Channel &chan, std::vector<Client> &cs, Server &s)
{
    const std::string &mode = m.params[1];

    if (mode != "+i" && mode != "-i")
        return false;

    if (mode == "+i")
        chan.setInvite_only(true);
    else
        chan.setInvite_only(false);

    print_modes(mode, chan.getName(), "");

    std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " " + mode + "\r\n";

    notification(chan, cs, s, msg);

    return true;
}