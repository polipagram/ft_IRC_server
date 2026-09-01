#include "../../includes/Parser.hpp"

Message Parser::parse(const std::string& raw_line)
{
    Message msg;

    size_t i = 0;
    while (i < raw_line.size() && (raw_line[i] == ' ' || raw_line[i] == '\t'))
        i++;

    if (i < raw_line.size() && raw_line[i] == ':')
    {
        i++;
        while (i < raw_line.size() && raw_line[i] != ' ' && raw_line[i] != '\t')
            msg.prefix += raw_line[i++];
    }

    while (i < raw_line.size() && (raw_line[i] == ' ' || raw_line[i] == '\t'))
        i++;

    while (i < raw_line.size() && raw_line[i] != ' ' && raw_line[i] != '\t')
        msg.cmd += raw_line[i++];

    std::string token;
    while (i < raw_line.size())
    {
        while (i < raw_line.size() && (raw_line[i] == ' ' || raw_line[i] == '\t'))
            i++;

        if (i == raw_line.size())
            break;

        if (raw_line[i] == ':')
        {
            i++;
            msg.params.push_back(raw_line.substr(i));
            break;
        }

        token.clear();
        while (i < raw_line.size() && raw_line[i] != ' ' && raw_line[i] != '\t')
            token += raw_line[i++];
        msg.params.push_back(token);
    }

    return msg;
}