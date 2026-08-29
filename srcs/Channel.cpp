#include "../includes/Channel.hpp"

Channel::Channel(const std::string &channelName) : name(channelName) , invite_only(false) ,
 change_topic(false) , limit(0)
{
}

const std::string &Channel::getName() const
{
    return name;
}

bool Channel::hasMember(int fd) const
{
    for (size_t i = 0; i < memberFds.size(); ++i)
    {
        if (memberFds[i] == fd)
            return true;
    }
    return false;
}

void Channel::addMember(int fd)
{
    if (!hasMember(fd))
        memberFds.push_back(fd);
}

void Channel::removeMember(int fd)
{
    for (size_t i = 0; i < memberFds.size(); ++i)
    {
        if (memberFds[i] == fd)
        {
            memberFds.erase(memberFds.begin() + i);
            break;
        }
    }
    for (size_t i = 0; i < operatorFds.size(); ++i)
    {
        if (operatorFds[i] == fd)
        {
            operatorFds.erase(operatorFds.begin() + i);
            break;
        }
    }
}

const std::vector<int> &Channel::getMemberFds() const
{
    return memberFds;
}

bool Channel::isEmpty() const
{
    return memberFds.empty();
}

bool Channel::isOperator(int fd) const
{
    for (size_t i = 0; i < operatorFds.size(); ++i)
    {
        if (operatorFds[i] == fd)
            return true;
    }
    return false;
}

void Channel::addOperator(int fd)
{
    if (!isOperator(fd))
        operatorFds.push_back(fd);
}

bool Channel::isInvited(int fd) const
{
    for (size_t i = 0; i < invitedFds.size(); ++i)
    {
        if (invitedFds[i] == fd)
            return true;
    }
    return false;
}

void Channel::addInvite(int fd)
{
    if (!isInvited(fd))
        invitedFds.push_back(fd);
}

const std::string &Channel::getTopic() const
{
    return topic;
}

void Channel::setTopic(const std::string &newTopic)
{
    topic = newTopic;
}

// kaw
void Channel::remove_invite(int fd)
{
    for (size_t i = 0; i < invitedFds.size(); i++)
    {
        if (invitedFds[i] == fd)
        {
            invitedFds.erase(invitedFds.begin() + i);
            return;
        }
    }
}

//kaw

void Channel::remove_operator(int fd)
{
    for (size_t i = 0; i < operatorFds.size(); i++)
    {
        if (operatorFds[i] == fd)
        {
            operatorFds.erase(operatorFds.begin() + i);
            return;
        }
    }
}

bool Channel::isInvite_only() const
{
    return invite_only;
}

void Channel::setInvite_only(bool val)
{
    invite_only = val;
}

bool Channel::is_change_topic() const
{
    return change_topic;
}

void Channel::set_change_topic(bool val)
{
    change_topic = val;
}

bool Channel::has_key() const
{
    return !key.empty();
}

std::string Channel::get_key() const
{
    return key;
}

void Channel::set_key(std::string new_key)
{
    key = new_key;
}

void Channel::remove_key()
{
    key.clear();
}

bool Channel::has_limit() const
{
    return limit > 0;
}

int Channel::get_limit() const
{
    return limit;
}

void Channel::set_limit(int user_limit)
{
    limit = user_limit;
}

void Channel::remove_limit()
{
    limit = 0;
}

const std::vector<int> Channel::getOperatorFds() const
{
    return operatorFds;
}


