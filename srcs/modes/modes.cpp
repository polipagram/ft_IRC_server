#include "../../includes/irc_server.hpp"

void print_modes(const std::string &mode,const std::string &channel_name, const std::string &Nick)
{
    std::cout << "[MODE] " << channel_name << " " << mode;

    if (!Nick.empty())
        std::cout << " " << Nick;

    std::cout << std::endl;
}

void modes(Client &client, Message &message, Server &server)
{
    if (!client.isRegistered())
    {
        server.sending_queue(client, replyCmd(451, client, "MODE"));
        return;
    }

    if (message.params.size() < 2)
    {
        server.sending_queue(client, replyCmd(461, client, "MODE"));
        return;
    }

    const std::string &channel_name = message.params[0];
    const std::string &mode = message.params[1];

    std::vector<Channel> &channels = server.getChannels();
    std::vector<Client> &clients = server.getClients();

    Channel *channel = NULL;

    for (size_t i = 0; i < channels.size(); ++i)
    {
        if (channels[i].getName() == channel_name)
        {
            channel = &channels[i];
            break;
        }
    }

    if (channel == NULL)
    {
        server.sending_queue(client, replyCmd(403, client, channel_name));
        return;
    }

    if (!channel->isOperator(client.getFd()))
    {
        server.sending_queue(client, replyCmd(482, client, channel_name));
        return;
    }

    if (mode == "+i" || mode == "-i")
    {
        if (mode == "+i")
            channel->setInvite_only(true);
        else
            channel->setInvite_only(false);

        print_modes(mode, channel_name, "");

        const std::string msg = ":" + client.getNickname() + " MODE " + channel_name + " " + mode + "\r\n";

        const std::vector<int> &members = channel->getMemberFds();

        for (size_t i = 0; i < members.size(); ++i)
        {
            for (size_t j = 0; j < clients.size(); ++j)
            {
                if (clients[j].getFd() == members[i])
                {
                    server.sending_queue(clients[j], msg);
                    break;
                }
            }
        }

        return;
    }

    if (mode != "+o" && mode != "-o")
    {
        server.sending_queue(client, replyCmd(472, client, mode));
        return;
    }

    if (message.params.size() < 3)
    {
        server.sending_queue(client, replyCmd(461, client, "MODE"));
        return;
    }

    const std::string &user_nick = message.params[2];

    Client *target = NULL;

    for (size_t i = 0; i < clients.size(); ++i)
    {
        if (clients[i].getNickname() == user_nick)
        {
            target = &clients[i];
            break;
        }
    }

    if (target == NULL)
    {
        server.sending_queue(client, replyCmd(401, client, user_nick));
        return;
    }

    if (!channel->hasMember(target->getFd()))
    {
        server.sending_queue(client, replyCmd(441, client, user_nick + " " + channel_name));
        return;
    }

    if (mode == "+o")
        channel->addOperator(target->getFd());
    else
        channel->remove_operator(target->getFd());

    print_modes(mode, channel_name, user_nick);

    const std::string msg = ":" + client.getNickname() + " MODE " + channel_name + " " + mode + " " + user_nick + "\r\n";

    const std::vector<int> &members = channel->getMemberFds();

    for (size_t i = 0; i < members.size(); ++i)
    {
        for (size_t j = 0; j < clients.size(); ++j)
        {
            if (clients[j].getFd() == members[i])
            {
                server.sending_queue(clients[j], msg);
                break;
            }
        }
    }
}