CC = c++

FLAGS = -Wall -Wextra -Werror -std=c++98

# Khass parser w les handlers dyal commandes ytkombilaw m3a server.
SRCS = srcs/Server.cpp srcs/Channel.cpp main.cpp srcs/Client.cpp srcs/parsser/Parser.cpp \
	srcs/commands/CommandDispatcher.cpp \
	srcs/commands/pass.cpp srcs/commands/nick.cpp srcs/commands/join.cpp \
	srcs/commands/user.cpp srcs/commands/privmsg.cpp srcs/commands/topic.cpp \
	srcs/commands/kick.cpp srcs/commands/invite.cpp srcs/commands/replayCmd.cpp srcs/modes/operator.cpp 

OBJS = $(SRCS:.cpp=.o)

NAME = irc

all: $(NAME)

$(NAME):$(OBJS)
	$(CC) $(FLAGS) $(OBJS) -o $(NAME)

%.o: %.cpp
	$(CC) $(FLAGS) -c $< -o $@

clean:
	rm -f $(OBJS)

fclean: clean
	rm -f $(NAME)

re : fclean all

.PHONY: all clean fclean re
