#ifndef CHANNEL_HPP
#define CHANNEL_HPP

#include <string>
#include <vector>
#include <cstdlib>

class Channel
{
private:
    std::string name;
    std::string topic;
    // Kan7fdo fd machi pointer dyal Client, bach zyada dyal clients ma tbdelch l-members.
    std::vector<int> memberFds;
    std::vector<int> operatorFds;
    std::vector<int> invitedFds;
    bool invite_only; // kaw
    bool change_topic; // kaw
    std::string key; // kaw
    int limit; // kaw
    
    public:
    Channel(const std::string &name);
    const std::string &getName() const;
    bool hasMember(int fd) const;
    void addMember(int fd);
    void removeMember(int fd);
    const std::vector<int> &getMemberFds() const;
    bool isEmpty() const;
    bool isOperator(int fd) const;
    void addOperator(int fd);
    bool isInvited(int fd) const;
    void addInvite(int fd);
    const std::string &getTopic() const;
    void setTopic(const std::string &newTopic);
    void remove_invite(int fd); // kaw
    void remove_operator(int fd); // kaw
    bool isInvite_only() const;
    void setInvite_only(bool value);
    bool is_change_topic() const;
    void set_change_topic(bool val);
    bool has_key() const;
    std::string  get_key() const;
    void set_key(std::string new_key);
    void  remove_key();
    bool has_limit() const;
    int get_limit() const;
    void set_limit(int limit);
    void remove_limit();
    const std::vector<int> &getOperatorFds() const;


};

#endif
