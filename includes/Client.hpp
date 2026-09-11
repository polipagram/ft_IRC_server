#ifndef CLIENT_HPP
#define CLIENT_HPP

#include <string>

class Client
{
private:
    int fd;
    std::string pass;
    std::string nickname;
    std::string username;
    bool passRecived;
    bool nicknameReceived;
    bool registered; 
    std::string buffer;
    bool userRecived;
    std::string send_buffer;

public:
    Client(int fd);
    ~Client();
    void setNickname(const std::string& nickname);
    void setUsername(const std::string& username);
    void setPass(const std::string &password);
    void setRegistered(bool registered);
    bool passIsRecived();
    bool isRegistered();
    void setPassIsRecived(bool registered);
    void setNicknameIsReceived(bool received);
    void setUserIsRecived(bool received);
   
    
    int getFd() const;
    const std::string &getNickname() const;
    const std::string &getUsername() const;
    const std::string &getPass() const;
    bool isRegistered() const;
    bool nicknameIsReceived() const;
    bool userIsRecived() const;
    void append_buff(const std::string &data); 
    std::string &get_buff(); 
    void append_send_buff(const std::string &data); 
    std::string &get_send_buff(); 
    bool send_data() const;
};


#endif
