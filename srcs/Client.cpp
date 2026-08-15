#include "../includes/Client.hpp"

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

void Client::setRegistered(bool registered){
    registered = true;
}

void Client::setPassIsRecived(bool registered){
    registered = true;
}

bool Client::passIsRecived(){
    return passRecived;
}

bool Client::isRegistered(){
    return registered;
}

void sendMessgToClient(std::string messg){
    (void)messg;
}

Client::~Client(){}