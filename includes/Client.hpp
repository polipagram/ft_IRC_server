#ifndef CLIENT_HPP
#define CLIENT_HPP

#include <string>

class Client
{
private:
    int fd;
    std::string pass; //password
    std::string nickname; //nickname
    std::string username; //username
    bool passRecived; //pass
    bool nicknameReceived; //nickname is recived
    bool registered; //user done
    // kaw : i need a buffer to store the line 
    // sent by the user in it
    std::string buffer; // client to server
    // I think I removed this f lmerge redito :)
    bool userRecived; // kaw
    std::string send_buffer; // server to client

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
    // Katsift reply IRC l-socket dyal had client.
    // void sendMessgToClient(const std::string &message);
    
    int getFd() const;
    const std::string &getNickname() const;
    const std::string &getUsername() const;
    const std::string &getPass() const;
    bool isRegistered() const;
    bool nicknameIsReceived() const;
    bool userIsRecived() const;
    void append_buff(const std::string &data);  //kaw
    std::string &get_buff(); //kaw
    void append_send_buff(const std::string &data); //kaw
    std::string &get_send_buff(); //kaw
    //kantchecki beha wash clent endo maysifet mashi empty buffer
    bool send_data() const; //kaw
};


#endif
