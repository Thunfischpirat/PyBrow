import ssl
import sys
import socket
import gzip

from urllib.parse import unquote

OPEN_SOCKETS = {}


class URL:
    def __init__(self, url: str) -> None:
       self._setup(url)

    def request_http(self, redirect_count: int = 0) -> str:
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

        headers = [
            f"GET {self.path} HTTP/1.1",
            f"Host: {self.host}",
             "Connection: keep-alive",
             "User-Agent: PyBrow",
             "Accept-Encoding: gzip"
        ]

        request = "\r\n".join(headers) + "\r\n\r\n"

        s.sendall(request.encode("utf8"))

        response = s.makefile("rb", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.decode("utf-8").split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline().decode("utf-8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        if int(status) >= 300 and int(status) < 400:
           redirect_count += 1
           if redirect_count > 5:
              raise RuntimeError(f"Maximum number of 5 redirects exceeded")

           url = response_headers.get("location")
           if url is None:
              raise KeyError("location")
           
           if "content-length" in response_headers:  
              num_bytes = int(response_headers["content-length"])
              response.read(num_bytes)
           elif "transfer-encoding" in response_headers:
              num_bytes = int(response.readline(), 16) 
              while num_bytes > 0:
                 response.read(num_bytes)
                 response.readline()
                 num_bytes = int(response.readline(), 16)
              while True:
                 line = response.readline()
                 if line == b"\r\n":
                    break
           else:
              response.read()
              

           self._setup(url)
           return self.request_http(redirect_count)
        
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

        if response_headers.get("content-encoding") == "gzip": 
           raw = gzip.decompress(raw)

        content = raw.decode("utf-8")

        return content

    def request_file(self) -> str:
        assert self.scheme == "file"
        content = ""
        path = unquote(self.path)
        with open(path, encoding="utf-8") as f:
            for line in f:
                content += line
        content += "\n"
        return content

    def request_data(self) -> str:
        assert self.scheme == "data"
        return unquote(self.data) + "\n"

    def _setup(self, url: str) -> None:
        self.view_source = False
        if url.startswith("view-source:"):
            _, url = url.split(":", 1)
            self.view_source = True
        if url.startswith("data:"):
            self.scheme, url = url.split(":", 1)
            self.mime, self.data = url.split(",", 1)
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


def show(body: str, view_source: bool) -> None:
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
    if url.scheme in ["http", "https"]:
        body = url.request_http()
    elif url.scheme == "file":
        body = url.request_file()
    else:
        body = url.request_data()

    show(body, url.view_source)

if __name__ == "__main__":
    load(URL(sys.argv[1]))
