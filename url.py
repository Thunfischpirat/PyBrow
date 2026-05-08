import ssl
import sys
import socket
import gzip

from urllib.parse import unquote
from typing import BinaryIO

OPEN_SOCKETS = {}


class URL:
    """Hold URL parts and make requests based on different schemes."""

    def __init__(self, url: str) -> None:
        self._setup(url)

    def request_http(self, redirect_count: int = 0) -> str:
        """Request and decode content from a server via HTTP(S)."""
        s = self._setup_socket()
        request = self._create_request()

        s.sendall(request.encode("utf8"))

        response = s.makefile("rb", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        _, status, _ = statusline.decode("utf-8").split(" ", 2)

        response_headers = self._get_response_headers(response)

        if 300 <= int(status) < 400:
            redirect_count += 1
            if redirect_count > 5:
                raise RuntimeError("Maximum number of 5 redirects exceeded")

            url = response_headers.get("location")
            if url is None:
                raise KeyError("location")

            self._read_response(response_headers, response)
            self._setup(url)
            return self.request_http(redirect_count)

        raw = self._read_response(response_headers, response)

        if response_headers.get("content-encoding") == "gzip":
            raw = gzip.decompress(raw)

        content = raw.decode("utf-8")

        return content

    def _setup_socket(self) -> socket.SocketType:
        """
        Set up a reusable socket for repeated requests to the same server.
        """
        s = OPEN_SOCKETS.get(f"{self.scheme}-{self.host}-{self.port}")

        if s is None:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            OPEN_SOCKETS[f"{self.scheme}-{self.host}-{self.port}"] = s

        return s

    def _create_request(self) -> str:
        """Build the raw HTTP GET request."""
        headers = [
            f"GET {self.path} HTTP/1.1",
            f"Host: {self.host}",
            "Connection: keep-alive",
            "User-Agent: PyBrow",
            "Accept-Encoding: gzip",
        ]

        return "\r\n".join(headers) + "\r\n\r\n"

    def _get_response_headers(self, response: BinaryIO) -> dict[str, str]:
        """Parse headers of server response."""
        response_headers = {}
        while True:
            line = response.readline().decode("utf-8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        return response_headers

    def _read_response(
        self,
        response_headers: dict[str, str],
        response: BinaryIO,
    ) -> bytes:
        """Read server response as raw bytes."""
        if "content-length" in response_headers:
            num_bytes = int(response_headers["content-length"])
            raw = response.read(num_bytes)
        elif "transfer-encoding" in response_headers:
            num_bytes = int(response.readline(), 16)
            raw = b""
            while num_bytes > 0:
                raw += response.read(num_bytes)
                response.readline()
                num_bytes = int(response.readline(), 16)
            while True:
                line = response.readline()
                if line == b"\r\n":
                    break
        else:
            raw = response.read()

        return raw


    def request_file(self) -> str:
        """Return content from locally stored file."""
        assert self.scheme == "file"
        content = ""
        path = unquote(self.path)
        with open(path, encoding="utf-8") as f:
            for line in f:
                content += line
        content += "\n"
        return content


    def request_data(self) -> str:
        """Return the inline HTML content of the url."""
        assert self.scheme == "data"
        return unquote(self.data) + "\n"


    def _setup(self, url: str) -> None:
        """From url get relevant parts such as host, port, path and scheme."""
        self.view_source = False
        if url.startswith("view-source:"):
            _, url = url.split(":", 1)
            self.view_source = True
        if url.startswith("data:"):
            self.scheme, url = url.split(":", 1)
            _, self.data = url.split(",", 1)
            return
        elif url.startswith("/"):
            self.path = url
            return
        else:
            self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file", "data"]

        if "/" not in url:
            url = url + "/"

        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        else:
            self.port = None

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)


def show(body: str, view_source: bool = False) -> None:
    """
    Skip HTML tags and show the text of the body.
    If view_source is True show body as is.
    """
    in_tag = False
    i = 0
    while i < len(body):
        c = body[i]
        if not view_source:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif c == "&":
                entity = body[i:i + 4]
                if entity == "&lt;":
                    print("<", end="")
                    i += 4
                    continue
                elif entity == "&gt;":
                    print(">", end="")
                    i += 4
                    continue
            elif not in_tag:
                print(c, end="")
        else:
            print(c, end="")
        i += 1


def load(url: URL) -> None:
    """Depending on the scheme process URL accordingly and show the response body."""
    if url.scheme in ["http", "https"]:
        body = url.request_http()
    elif url.scheme == "file":
        body = url.request_file()
    else:
        body = url.request_data()

    show(body, url.view_source)


if __name__ == "__main__":
    load(URL(sys.argv[1]))
