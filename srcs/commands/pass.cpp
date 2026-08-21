#include "../../includes/irc_server.hpp"

void passHundler(Client &c, Message &M, Server &s){
    // PASS katqbel ghir mra, khasha parameter, w khasso yqabel password dyal server.
    if(c.passIsRecived())
        c.sendMessgToClient(replyCmd(462, c, "PASS"));
    else if(M.params.empty())
        c.sendMessgToClient(replyCmd(461, c, "PASS"));
    else if(s.get_passwd() == M.params[0])
        c.setPassIsRecived(true);
    else
        c.sendMessgToClient(replyCmd(464, c, "PASS"));
}
