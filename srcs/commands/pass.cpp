#include "../../includes/irc_server.hpp"

void passHundler(Client &c, Message &M, Server &s){
    if(c.isRegistered())
        s.sending_queue(c, replyCmd(462, c, "PASS"));
    else if(M.params.empty())
        s.sending_queue(c, replyCmd(461, c, "PASS"));
    else if(s.get_passwd() == M.params[0])
        c.setPassIsRecived(true);
    else
        s.sending_queue(c, replyCmd(464, c, "PASS"));
}
