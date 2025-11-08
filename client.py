import socket
import api
import argparse
import api

# region Predefined

# The following are for convenience. You can use them to build expressions.
pi_c = api.NAMED_CONSTANTS.PI
tau_c = api.NAMED_CONSTANTS.TAU
e_c = api.NAMED_CONSTANTS.E

add_b = api.BINARY_OPERATORS.ADD
sub_b = api.BINARY_OPERATORS.SUB
mul_b = api.BINARY_OPERATORS.MUL
div_b = api.BINARY_OPERATORS.DIV
mod_b = api.BINARY_OPERATORS.MOD
pow_b = api.BINARY_OPERATORS.POW

neg_u = api.UNARY_OPERATORS.NEG
pos_u = api.UNARY_OPERATORS.POS

sin_f = api.FUNCTIONS.SIN
cos_f = api.FUNCTIONS.COS
tan_f = api.FUNCTIONS.TAN
sqrt_f = api.FUNCTIONS.SQRT
log_f = api.FUNCTIONS.LOG
max_f = api.FUNCTIONS.MAX
min_f = api.FUNCTIONS.MIN
pow_f = api.FUNCTIONS.POW
rand_f = api.FUNCTIONS.RAND

flag_quit = False


# endregion


def process_response(response: api.CalculatorHeader) -> None:
    if response.is_request:
        raise api.CalculatorClientError("Got a request instead of a response")
    if response.status_code == api.CalculatorHeader.STATUS_OK:
        result, steps = api.data_to_result(response)
        print("Result:", result)
        if steps:
            print("Steps:")
            expr, first, *rest = steps
            print(f"{expr} = {first}", end="\n" * (not bool(rest)))
            if rest:
                print(
                    "".join(map(lambda v: f"\n{' ' * len(expr)} = {v}", rest)))
    elif response.status_code == api.CalculatorHeader.STATUS_CLIENT_ERROR:
        err = api.data_to_error(response)
        raise api.CalculatorClientError(err)
    elif response.status_code == api.CalculatorHeader.STATUS_SERVER_ERROR:
        err = api.data_to_error(response)
        raise api.CalculatorServerError(err)
    else:
        raise api.CalculatorClientError(
            f"Unknown status code: {response.status_code}")


def client(server_address: tuple[str, int], expressions_list: list[api.Expression], show_steps: bool = False,
           cache_result: bool = False, cache_control: int = api.CalculatorHeader.MAX_CACHE_CONTROL) -> None:
    server_prefix = f"{{{server_address[0]}:{server_address[1]}}}"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        print(f"{server_prefix} Connection established")
        for expression in expressions_list:
            try:
                request = api.CalculatorHeader.from_expression(
                    expression, show_steps, cache_result, cache_control)

                request = request.pack()
                print(f"{server_prefix} Sending request of length {len(request)} bytes")
                client_socket.sendall(request)

                response = client_socket.recv(api.BUFFER_SIZE)
                print(f"{server_prefix} Got response of length {len(response)} bytes")
                response = api.CalculatorHeader.unpack(response)
                process_response(response)

            except api.CalculatorError as e:
                print(f"{server_prefix} Got error: {str(e)}")
            except Exception as e:
                print(f"{server_prefix} Unexpected error: {str(e)}")
    print(f"{server_prefix} Connection closed")


# Added lines: message to close proxy and server.
def closing_message(server_address: tuple[str, int]):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        try:
            message = "QUIT"
            print("Sending request to close server")
            client_socket.sendall(message.encode("utf-8"))
        except Exception as exception:
            print(exception)


# and of added lines


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="A Calculator Client.")

    arg_parser.add_argument("-p", "--port", type=int,
                            default=api.DEFAULT_PROXY_PORT, help="The port to connect to.")
    arg_parser.add_argument("-H", "--host", type=str,
                            default=api.DEFAULT_PROXY_PORT, help="The host to connect to.")

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    # * Change in start (1)
    # Example expressions: (uncomment one of them for your needs)
    # (1) '(sin(max(2, 3 * 4, 5, 6 * ((7 * 8) / 9), 10 / 11)) / 12) * 13' = -0.38748277824137206
    # expr = mul_b(div_b(sin_f(max_f(2, mul_b(3, 4), 5, mul_b(
    #    6, div_b(mul_b(7, 8), 9)), div_b(10, 11))), 12), 13)  # (1)

    # (2) '(max(2, 3) + 3)' = 6
    # expr = add_b(max_f(2, 3), 3) # (2)

    # (3) '3 + ((4 * 2) / ((1 - 5) ** (2 ** 3)))' = 3.0001220703125
    # expr = add_b(3, div_b(mul_b(4, 2), pow_b(sub_b(1, 5), pow_b(2, 3)))) # (3)

    # (4) '((1 + 2) ** (3 * 4)) / (5 * 6)' = 17714.7
    # expr = div_b(pow_b(add_b(1, 2), mul_b(3, 4)), mul_b(5, 6)) # (4)

    # (5) '-(-((1 + (2 + 3)) ** -(4 + 5)))' = 9.92290301275212e-08
    # expr = neg_u(neg_u(pow_b(add_b(1, add_b(2, 3)), neg_u(add_b(4, 5))))) # (5)

    # (6) 'max(2, (3 * 4), log(e), (6 * 7), (9 / 8))' = 42
    # expr = max_f(2, mul_b(3, 4), log_f(e_c), mul_b(6, 7), div_b(9, 8)) # (6)
    # * Change in end (1)

    # Change the following values according to your needs:

    show_steps = True  # Request the steps of the calculation
    cache_result = True  # Request to cache the result of the calculation
    # If the result is cached, this is the maximum age of the cached response
    # that the client is willing to accept (in seconds)
    cache_control = 2 ** 16 - 1

    # * Change in start (2)
    """
        List of expressions to choose from. 
    """
    exprList = [
        # mul_b(div_b(sin_f(max_f(2, mul_b(3, 4), 5, mul_b(div_b(mul_b(7, 8), 9)), div_b(10, 11))), 12), 13),
        add_b(max_f(2, 3), 3),
        add_b(3, div_b(mul_b(4, 2), pow_b(sub_b(1, 5), pow_b(2, 3)))),
        div_b(pow_b(add_b(1, 2), mul_b(3, 4)), mul_b(5, 6)),
        neg_u(neg_u(pow_b(add_b(1, add_b(2, 3)), neg_u(add_b(4, 5))))),
        max_f(2, mul_b(3, 4), log_f(e_c), mul_b(6, 7), div_b(9, 8))
    ]

    """
        making an expressions list to send to the server.
        the quit option was implemented to make the termination of the program easier for the programmer,
        and reducing the number of files that needs too be manually closed after each run.
    """

    exit = ""

    while exit != "-1":
        expToSend = []
        print("Enter expression numbers from list to calculate, enter -1 to finish:")
        expr = input("EXP: ")
        while expr != "-1":
            try:
                expToSend.append(exprList[int(expr)])
            except Exception as e:
                print("illegal value")
                print(e)
            expr = input("EXP: ")

        try:
            client((api.DEFAULT_PROXY_HOST, api.DEFAULT_PROXY_PORT), expToSend, show_steps, cache_result,
                    cache_control)
        except Exception as e:
            print("illegal value")
            print(e)

        print("\nInstructions: "
              "\nType -1 to close the connection, press ENTER to send a new request")
        exit = input("")

    terminate = input("Type -1 to terminate proxy.py, server.py, client.py: ")
    if terminate == "-1":
        closing_message((api.DEFAULT_PROXY_HOST, api.DEFAULT_PROXY_PORT))
    # * Change in end (2)
