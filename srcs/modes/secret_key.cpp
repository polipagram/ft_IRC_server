#include "../../includes/irc_server.hpp"

bool secret_key(Client &c, Message &m, Channel &chan, std::vector<Client> &cs, Server &s)
{
    const std::string &mode = m.params[1];

    if (mode != "+k" && mode != "-k")
        return false;

    if (m.params.size() < 3)
    {
        s.sending_queue(c, replyCmd(461, c, "MODE"));
        return true;
    }

    const std::string &key = m.params[2];

    if (mode == "+k")
    {
        chan.set_key(key);

        print_modes(mode, chan.getName(), key);

        std::string msg = ":" + c.getNickname() + " MODE " +
                          chan.getName() + " +k " + key + "\r\n";

        notification(chan, cs, s, msg);
    }
    else
    {
        chan.remove_key();

        print_modes(mode, chan.getName(), "");

        std::string msg = ":" + c.getNickname() + " MODE " + chan.getName() + " -k\r\n";

        notification(chan, cs, s, msg);
    }

    return true;
}