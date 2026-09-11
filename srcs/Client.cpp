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


Client::~Client(){}


void Client::append_buff(const std::string &data)
{
    this->buffer += data;
}

std::string &Client::get_buff()
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

void Client::append_send_buff(const std::string &data) 
{
    this->send_buffer += data;
}

bool Client::send_data() const 
{
    return !this->send_buffer.empty();
}

std::string &Client::get_send_buff() 
{
    return this->send_buffer;
}

