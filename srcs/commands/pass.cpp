#include "../../includes/irc_server.hpp"

void passHundler(Client &c, Message &M, Server &s){
    // PASS katqbel ghir mra, khasha parameter, w khasso yqabel password dyal server.
    // if(c.passIsRecived())
    // kaw : fixit lmesage dyal registered l client hta ysali nick o user
    if(c.isRegistered())
    // kaw : 462 is for  re registering error
        s.sending_queue(c, replyCmd(462, c, "PASS"));
    else if(M.params.empty())
    // kaw : 461 is for not enough or missing params
        s.sending_queue(c, replyCmd(461, c, "PASS"));
    else if(s.get_passwd() == M.params[0])
        c.setPassIsRecived(true);
    else
        // kaw : 464 is for wrong passwd or passwd mismatch
        s.sending_queue(c, replyCmd(464, c, "PASS"));
}
