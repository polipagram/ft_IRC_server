#include "includes/Server.hpp"

int main(int ac, char **av)
{
    if (ac != 3)
    {
        std::cerr << "Please specify port && passwd" << std::endl;
        return 1;
    }

    try
    {
        Server server(std::atoi(av[1]), av[2]);

        server.launch();
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}