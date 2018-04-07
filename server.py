# -*- coding: utf-8 -*-
"""
Christina Hernández Wunsch <hernandezwunschc@gmail.com>
"""
import re
import math
import socket
import sys
import json
from qgram_index import QgramIndex


def hexa2int(hexa):
    """
    Returns an int that represents 4 bits.

    >>> hexa2int('E')
    14
    >>> hexa2int('1')
    1
    """
    if hexa == 'F':
        return 15
    elif hexa == 'E':
        return 14
    elif hexa == 'D':
        return 13
    elif hexa == 'C':
        return 12
    elif hexa == 'B':
        return 11
    elif hexa == 'A':
        return 10
    else:
        return int(hexa)


def urlDecode(encoded):
    """
    >>> urlDecode("z%C3%BCrich")
    'zürich'

    >>> urlDecode("L%C3%B8kken")
    'Løkken'

    >>> urlDecode("a+o")
    'a+o'

    >>> urlDecode("%C3%A1+%C3%A9")
    'á+é'

    >>> urlDecode("%C3%A1%20%C3%A9")
    'á é'
    """
    ascii_bytes = bytes(encoded, encoding='utf-8')
    index = 0
    while True:
        index = encoded.find("%", index)
        if index == -1:
            return ascii_bytes.decode('utf-8')
        else:
            ascii_bytes = ascii_bytes[:index] +\
                bytes([(hexa2int(encoded[index + 1]) << 4) +
                      hexa2int(encoded[index + 2])]) + \
                ascii_bytes[index + 3:]
            encoded = encoded[:index] + encoded[index + 2:]
    return encoded


def server(input_file, port):
    qggram = QgramIndex(3)
    qggram.read_from_file(input_file)
    # Create communication socket and listen on port 80.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((socket.gethostname(), port))
    print("Started server: %s:%s" % (socket.gethostname(), port))
    server.listen(3)
    # Server loop.
    while True:
        print("\x1b[1mWaiting for requests on port %d ... \x1b[0m" % port)
        (client, address) = server.accept()
        message = client.recv(1 << 31)
        message = message.decode("ascii")
        # Consider only HTTP GET requests.
        match = re.match("^GET /(.*) HTTP", message)
        if not match:
            continue
        query = match.group(1)
        print("HTTP GET request received: \"%s\"" % query)
        content_type = "text/plain"
        # Deal with queries starting with ?.
        match = re.match("get_cities\?term=(.*)", query)
        if match:
            prefix = match.group(1)
            prefix = urlDecode(prefix)
            print("Answering prefix query for: \"%s\"" % prefix)
            # Normalize prefix.
            prefix = re.sub("[ \W+\n]", "", prefix).lower()
            delta = int(math.floor(len(prefix) / 4))
            # Send results with proper HTTP headers.
            matches, comps = qggram.find_matches(prefix, delta, 10)
            matches = [{"label": qggram.city_names[x[0] - 1],
                        "rating": x[1]}
                       for x in matches]
            content_type = "application/json"
            content = json.dumps(matches)
            print("Returning:\n %s" % content)
        # Otherwise consider query as file name and serve the corresponding
        else:
            try:
                # You can only have access to certain files
                # default search.html
                if query == "":
                    query = "search.html"
                if query in ["search.html", "search.css", "search.js"]:
                    with open(query) as file:
                        content = file.read()
                        if query.endswith(".html"):
                            content_type = "text/html"
                        if query.endswith(".css"):
                            content_type = "text/css"
                        if query.endswith(".js"):
                            content_type = "application/javascript"
                        if query.endswith(".png"):
                            content_type = "image/png"
                else:
                    content = ""
            except:
                content = ""
        # Send result with proper HTTP headers.
        if content == "":
            result = ("HTTP/1.1 404 Not found\r\n")
        else:
            result = ("HTTP/1.1 200 OK\r\n"
                      "Content-type: %s\r\n"
                      "Content-length: %s\r\n\r\n%s") % (content_type,
                                                         len(content),
                                                         content)
        client.send(result.encode())
        client.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 server.py <file> <port>")
        exit(1)
    input_file = sys.argv[1]
    port = int(sys.argv[2])
    server(input_file, port)
