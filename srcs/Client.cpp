#include "../includes/Client.hpp"

Client::Client(int fd): fd(fd), auth(false), nicknameReceived(false), registered(false){}

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
    auth = registered;
}

bool Client::isRegistered() const{
    return auth;
}

Client::~Client(){}