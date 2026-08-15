#include "Server.hpp"

int main(int ac, char **av)
{
    if (ac != 3)
    {
        std::cerr << "Please specify port && passwd" << std::endl;
        return 1;
    }

    try
    {
        int port = std::atoi(av[1]);
        std::string passwd = av[2];

        Server server(port, passwd);
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}