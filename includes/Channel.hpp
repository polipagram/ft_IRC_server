#ifndef CHANNEL_HPP
#define CHANNEL_HPP

#include <string>
#include <vector>

class Channel
{
private:
    std::string name;
    std::string topic;
    // Kan7fdo fd machi pointer dyal Client, bach zyada dyal clients ma tbdelch l-members.
    std::vector<int> memberFds;
    std::vector<int> operatorFds;
    std::vector<int> invitedFds;

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
};

#endif
