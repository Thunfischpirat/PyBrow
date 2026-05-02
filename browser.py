import ssl
import socket
from urllib.parse import unquote

class URL:
   def __init__(self, url: str) -> None:
        if url.startswith("data:"):
           self.scheme , url = url.split(":", 1) 
           self.mime, self.data = url.split(",", 1)
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

   def request_http(self) -> str:
       s = socket.socket(
	     family=socket.AF_INET,
	     type=socket.SOCK_STREAM,
	     proto=socket.IPPROTO_TCP,
	   )         
       s.connect((self.host, self.port))

       if self.scheme == "https":
          ctx = ssl.create_default_context()
          s = ctx.wrap_socket(s, server_hostname=self.host)
        
       headers = [
                  f"GET {self.path} HTTP/1.1",
		  f"Host: {self.host}",
		  f"Connection: close",
		  f"User-Agent: PyBrow",
       ]

       request = "\r\n".join(headers) + "\r\n\r\n"

       s.sendall(request.encode("utf8"))

       response = s.makefile("r", encoding="utf8", newline="\r\n")
       statusline = response.readline()
       version, status, explanation = statusline.split(" ", 2)
  
       response_headers = {}
       while True:
          line = response.readline()
          if line == "\r\n":
             break
          header, value = line.split(":", 1)
          response_headers[header.casefold()] = value.strip()

       assert "transfer-encoding" not in response_headers
       assert "content-encoding" not in response_headers

       content = response.read()
       s.close()
  
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
      
      
def show(body: str) -> None:
   in_tag = False
   i = 0
   while i < len(body):
      c = body[i]
      if c == "<":
         in_tag = True
      elif c == ">":
         in_tag = False
      elif c == "&":
         entity = body[i:i+4]
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
      i += 1

def load(url: URL) -> None:
   if url.scheme in ["http", "https"]:
      body = url.request_http()
   elif url.scheme == "file":
      body = url.request_file()
   else:
      body = url.request_data()
            
   show(body)

if __name__ == "__main__":
   import sys
   load(URL(sys.argv[1]))
