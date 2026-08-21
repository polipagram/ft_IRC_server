#include "../includes/irc_server.hpp"

Client::Client(int fd): fd(fd), passRecived(false), nicknameReceived(false), registered(false), userRecived(false){}

void Client::setPass(const std::string& p){
    pass = p;
}

void Client::setNickname(const std::string &nickname){
    this->nickname = nickname;
}

void Client::setUsername(const std::string &username){
    this->username = username;
}

int Client::getFd() const{
    return fd;
}

const std::string &Client::getNickname() const{
    return nickname;
}

const std::string &Client::getUsername() const{
    return username;
}

const std::string& Client::getPass() const{
    return pass;
}

/*
 kaw : hna kan tale3 error i fixed it I assigned dok
 l vars li endek konty dayr registered = true
 idk i may be wrong
 */
void Client::setRegistered(bool registered){
    this->registered = registered;
}

// same here
void Client::setPassIsRecived(bool registered){
    this->passRecived = registered;
}

void Client::setNicknameIsReceived(bool received){
    this->nicknameReceived = received;
}

void Client::setUserIsRecived(bool received){
    this->userRecived = received;
}

bool Client::passIsRecived(){
    return passRecived;
}

bool Client::isRegistered(){
    return registered;
}

void Client::sendMessgToClient(const std::string &message){
    // MSG_NOSIGNAL kaymna3 server ytsed b SIGPIPE ila client qta3 connexion.
    if (!message.empty())
        send(fd, message.c_str(), message.size(), MSG_NOSIGNAL);
}

Client::~Client(){}


void Client::append_buff(const std::string &data) // kaw
{
    this->buffer += data;
}

std::string &Client::get_buff() // kaw
{
    return this->buffer;
}

bool Client::nicknameIsReceived() const
{
    return nicknameReceived;
}

bool Client::userIsRecived() const
{
    return userRecived;
}
