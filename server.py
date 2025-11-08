import numbers
import sys

import api
import argparse
import socket
import threading

CACHE_POLICY = True  # whether to cache responses or not
# the maximum time that the response can be cached for (in seconds)
CACHE_CONTROL = 2 ** 16 - 1

global flag_quit  # Made to make the termination of the program easier. Not required for this exercise.

BUFFSIZE = api.BUFFER_SIZE  # using the API buffer size to ensure consistency in data handling across all socket operations


def calculate(expression: api.Expr, steps: list[str] = []) -> tuple[numbers.Real, list[api.Expression]]:
    '''    
    Function which calculates the result of an expression and returns the result and the steps taken to calculate it.
    The function recursively descends into the expression tree and calculates the result of the expression.
    Each expression wraps the result of its subexpressions in parentheses and adds the result to the steps list.
    '''
    expr = api.type_fallback(expression)
    const = None
    if isinstance(expr, api.Constant) or isinstance(expr, api.NamedConstant):
        const = expr
    elif isinstance(expr, api.BinaryExpr):
        left_steps, right_steps = [], []
        left, left_steps = calculate(expr.left_operand, left_steps)
        for step in left_steps[:-1]:
            steps.append(api.BinaryExpr(
                step, expr.operator, expr.right_operand))
        right, left_steps = calculate(expr.right_operand, right_steps)
        for step in right_steps[:-1]:
            steps.append(api.BinaryExpr(left, expr.operator, step))
        steps.append(api.BinaryExpr(left, expr.operator, right))
        const = api.Constant(expr.operator.function(left, right))
        steps.append(const)
    elif isinstance(expr, api.UnaryExpr):
        operand_steps = []
        operand, operand_steps = calculate(expr.operand, operand_steps)
        for step in operand_steps[:-1]:
            steps.append(api.UnaryExpr(expr.operator, step))
        steps.append(api.UnaryExpr(expr.operator, operand))
        const = api.Constant(expr.operator.function(operand))
        steps.append(const)
    elif isinstance(expr, api.FunctionCallExpr):
        args = []
        for arg in expr.args:
            arg_steps = []
            arg, arg_steps = calculate(arg, arg_steps)
            for step in arg_steps[:-1]:
                steps.append(api.FunctionCallExpr(expr.function, *
                (args + [step] + expr.args[len(args) + 1:])))
            args.append(arg)
        steps.append(api.FunctionCallExpr(expr.function, *args))
        const = api.Constant(expr.function.function(*args))
        steps.append(const)
    else:
        raise TypeError(f"Unknown expression type: {type(expr)}")
    return const.value, steps


def process_request(request: api.CalculatorHeader) -> api.CalculatorHeader:
    '''
    Function which processes a CalculatorRequest and builds a CalculatorResponse.
    '''
    result, steps = None, []
    try:
        if request.is_request:
            expr = api.data_to_expression(request)
            result, steps = calculate(expr, steps)
        else:
            raise TypeError("Received a response instead of a request")
    except Exception as e:
        return api.CalculatorHeader.from_error(e, api.CalculatorHeader.STATUS_CLIENT_ERROR, CACHE_POLICY, CACHE_CONTROL)

    if request.show_steps:
        steps = [api.stringify(step, add_brackets=True) for step in steps]
    else:
        steps = []

    return api.CalculatorHeader.from_result(result, steps, CACHE_POLICY, CACHE_CONTROL)


def server(host: str, port: int) -> None:
    # socket(socket.AF_INET, socket.SOCK_STREAM)
    # (1) AF_INET is the address family for IPv4 (Address Family)
    # (2) SOCK_STREAM is the socket type for TCP (Socket Type) - [SOCK_DGRAM is the socket type for UDP]
    # Note: context manager ('with' keyword) closes the socket when the block is exited
    global flag_quit
    flag_quit = False  # used for terminating the program when gets a message to do so
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # SO_REUSEADDR is a socket option that allows the socket to be bound to an address that is already in use.
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Prepare the server socket
        # * Fill in start (1)
        server_socket.bind((host, port))
        """
        explanation-
            connecting the socket to the host ip and port. 
            bind method prepares the server socket to listen for connection
            on the specific port and address (ip address) and allow clients to connect to the socket.   
        """
        server_socket.listen(1)
        """
            explanation-
                listen method tells the server to wait for incoming connections. 
                the numeric param tells the socket the max number of client connections 
                he'll handle simultaneously. in this exercise the server will be handling 
                one client at max, so we set the param to 1.

        """
        server_socket.settimeout(1)  # setting a timeout for to accept method. if quit was received,
        # timeout will make sure new thread will not open
        # * Fill in end (1)

        threads = []
        print(f"Listening on {host}:{port}")

        while True:
            try:
                # Establish connection with client.
                # * Fill in start (2)

                client_socket, address = server_socket.accept()

                """
                    explanation-
                        client-
                            client sends a SYN packet to the server to request a connection.
                        server-
                            since we applied the listen method, the server socket is now waiting for incoming connections.
                            if a client send a SYN packet while the server socket is listening, the server will receive
                            the packet and replay with SYN-ACK (ack is a packet that confirm that the socket received
                            the client request). 
                            if the client received the SYN-ACK successfully, it will send another ACK to the server.
                        after this process- 
                            the handshake between the client and the server is complete.
                        the accept method waits until the handshake complete, and then returns the socket and client address.
                           (client address is a tuple that contain both the ip and the port that's being used by the client)
                        after receiving the data from the client (via accept method) we know that the connection between
                        the server and the client has been established and redy to exchange data.

                """
                # * Fill in end (2)
                # Create a new thread to handle the client request
                thread = threading.Thread(target=client_handler, args=(
                    client_socket, address))
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                print("Shutting down...")
                break
            # added lines-for quit option
            except socket.timeout:
                # accept() timed out, check if we should stop
                if flag_quit:
                    # QUIT was signaled by a handler thread
                    break
                # If not quitting, just continue waiting for connections.
                pass
            # end of added lines

        for thread in threads:  # Wait for all threads to finish
            thread.join()
        # added lines-for terminating the program
        try:
            print("closing socket...")
            server_socket.close()  # Close the proxi socket
            print("terminating server.py...")
            sys.exit(0)
        except Exception as e:
            print(f"Error while closing server socket: {e}")
        # end of added lines


def client_handler(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    '''
    Function which handles client requests
    '''
    global flag_quit
    client_addr = f"{client_address[0]}:{client_address[1]}"
    client_prefix = f"{{{client_addr}}}"
    with client_socket:  # closes the socket when the block is exited
        print(f"Conection established with {client_addr}")
        while True:
            # * Fill in start (3)
            data = client_socket.recv(BUFFSIZE)
            """
                explanation - 
                    after a connection id established (accept method returned the client socket and address successfully)
                    a new thread is open in order to handel the communication with this specific client.
                    the recv method is waiting to receive data from the client. 
                    reads up to BUFFSIZE bytes of data from the client socket, if the client closed the connection- the recv
                    method will return an empty bytes object.

            """
            try:  # checking if QUIT message was received.
                if len(data) == 4:  # implemented in this scope since request is never shorter than 12 bytes,
                    # a 4 bytes data cant be a request.
                    is_quiting = data.decode("utf-8")  # decoding bytes to string
                    print(is_quiting)
                    if "QUIT" in is_quiting:
                        flag_quit = True
                        client_socket.close()  # making sure client soket is closed
                    break
            except Exception as e:
                print(e)
            # * Fill in end (3)
            if not data:  # * Change in start (1)
                # exit loop when receiving no data (means that client closed the connection).
                # no need to close client socket since the with method handles this automatically
                break
                # * Change in end (1)
            try:

                try:
                    request = api.CalculatorHeader.unpack(data)
                except Exception as e:
                    raise api.CalculatorClientError(
                        f'Error while unpacking request: {e}') from e

                print(f"{client_prefix} Got request of length {len(data)} bytes")

                response = process_request(request)

                response = response.pack()
                print(
                    f"{client_prefix} Sending response of length {len(response)} bytes")

                # * Fill in start (4)
                client_socket.sendall(response)
                """
                    explanation - 
                        there's two method we can choose from in order to send data to the client while using
                        TCP protocol:
                            send()- sends data up to some buffer size. it may not send all the data in one
                                call, so it will require us to handle the sending of the remaining data.
                            sendall- ensure the sending of the all the data, by internally loops, and handling the
                                buffer limitation automatically.
                        we chose to use sendall method in order to make sure all the data is send to the client.
                """
            # * Fill in end (4)
            except Exception as e:
                print(f"Unexpected server error: {e}")
                client_socket.sendall(api.CalculatorHeader.from_error(
                    e, api.CalculatorHeader.STATUS_SERVER_ERROR, CACHE_POLICY, CACHE_CONTROL).pack())

    # * Change in start (2)
    print(f"{client_prefix} Connection closed")
    client_socket.close()  # same as line 254
    return
    # * Change in end (2)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='A Calculator Server.')

    arg_parser.add_argument('-p', '--port', type=int,
                            default=api.DEFAULT_SERVER_PORT, help='The port to listen on.')
    arg_parser.add_argument('-H', '--host', type=str,
                            default=api.DEFAULT_SERVER_HOST, help='The host to listen on.')

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    server(host, port)
