#include "../../includes/irc_server.hpp"
#include <string>
#include <cctype>

bool checkSpecailChar(char c) {
    std::string s = "[]\\`_^{}|";
    for (size_t i = 0; i < s.length(); i++) {
        if (c == s[i])
            return true;
    }
    return false;
}

bool checkNickValid(const std::string& nick) {
    if (nick.empty())
        return false;

    if (!std::isalpha(static_cast<unsigned char>(nick[0])) && !checkSpecailChar(nick[0]))
        return false;

    if (nick.length() > 9)
        return false;

    for (size_t i = 1; i < nick.length(); i++) {
        if (!std::isalnum(static_cast<unsigned char>(nick[i])) && !checkSpecailChar(nick[i]) && nick[i] != '-')
            return false;
    }
    return true;
}

void nickHundler(Client &c, Message &M, Server &s) {
    if (!c.passIsRecived()) {
        s.sending_queue(c, replyCmd(451, c, "NICK :You have not registered"));
        return;
    }
    
    if (M.params.empty()) {
        s.sending_queue(c, replyCmd(431, c, ":No nickname given"));
        return;
    }
    
    std::string newNick = M.params[0];
    if (!checkNickValid(newNick)) {
        s.sending_queue(c, replyCmd(432, c, newNick + ""));
        return;
    }

    std::vector<Client> &clients = s.getClients();
    for (size_t i = 0; i < clients.size(); ++i) {
        if (clients[i].getNickname() == newNick && clients[i].getFd() != c.getFd()) {
            // kaw : 433 nick deja in use
            s.sending_queue(c, replyCmd(433, c, newNick));
            return;
        }
    }

    c.setNickname(newNick);
    if(c.isRegistered())
        s.sending_queue(c, "NICK :" + newNick);
    c.setNicknameIsReceived(true);

    if (c.userIsRecived() && !c.isRegistered())
    {
        c.setRegistered(true);
        s.sending_queue(c, replyCmd(1, c, ""));
    }
}



