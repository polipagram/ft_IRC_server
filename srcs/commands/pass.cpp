#include "irc_server.hpp"



// src/commands/Pass.cpp
// └── void handlePass(Client& client, IRCMessage& msg, Server& server)
//     ├── check: client.getAuthenticated()  → 462//
//     ├── check: msg.params.empty()         → 461
//     ├── check: params[0] == password      → 464
//     └── client.setAuthenticated(true)



void passHundler(Client &c, Message &M, Server s){
    if(c.passIsRecived())
        c.sendMessgToClient(replyCmd(462, c, "PASS"));
    else if(M.params.empty())
        c.sendMessgToClient(replyCmd(461, c, "PASS"));
    else if(s.getPass() == M.params[0])
        c.setPassIsRecived(true);
    else
        c.sendMessgToClient(replyCmd(464, c, "PASS"));
}

void nickHundler(){
    
}