#include "../../includes/irc_server.hpp"
#include <string>
#include <cctype>

// Fonction katchouf wesh l7erf mn les caractères spéciaux li msmou7 bihom f IRC
bool checkSpecailChar(char c) {
    // RFC 2812 kaysem7 b had caractères spéciaux f nickname dyal IRC.
    std::string s = "[]\\`_^{}|";
    for (size_t i = 0; i < s.length(); i++) {
        if (c == s[i])
            return true;
    }
    return false;
}

// Fonction katchouf wesh nickname kamel valid 3la 7sab RFC 2812
bool checkNickValid(const std::string& nick) {
    // Kant2ekdo mn qanon dyal awal caractère w mn caractères lbaqyin f nickname.
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

// L'Handler dyal l'commande NICK
void nickHundler(Client &c, Message &M, Server &s) {
    // Khass client ydir PASS b nja7 qbel ma ykhtar nickname.
    if (!c.passIsRecived()) {
        // kaw : 451 client matregistrash
        s.sending_queue(c, replyCmd(451, c, "NICK :You have not registered"));
        return;
    }
    
    if (M.params.empty()) {
        // kaw : 431 makaynsh nickname
        s.sending_queue(c, replyCmd(431, c, ":No nickname given"));
        return;
    }
    
    std::string newNick = M.params[0];
    if (!checkNickValid(newNick)) {
        // kaw : fixit duplicated relpy
        // kaw : 432 nickname ghalet
        s.sending_queue(c, replyCmd(432, c, newNick + ""));
        return;
    }

    // Client yqder ybqa b nafs nickname dyalo, walakin mayqderch yakhed dyal client akhor.
    std::vector<Client> &clients = s.getClients();
    for (size_t i = 0; i < clients.size(); ++i) {
        if (clients[i].getNickname() == newNick && clients[i].getFd() != c.getFd()) {
            // kaw : 433 nick deja in use
            s.sending_queue(c, replyCmd(433, c, newNick));
            return;
        }
    }

    c.setNickname(newNick);
    c.setNicknameIsReceived(true);

    // Ila USER deja t3ammar, NICK howa akher 7aja naqsa bach ykml registration.
    if (c.userIsRecived() && !c.isRegistered())
    {
        // kaw
        // in case l user bgha ybedel nick maytle3sh lih welcome msg
        c.setRegistered(true);
        s.sending_queue(c, replyCmd(1, c, ""));
    }
}



