import unittest
import tempfile

from url import URL

class TestURL(unittest.TestCase):
   """Test that the supported request schemes for URLs work."""
   def test_about_blank(self):
      url = URL("about:blank")
      self.assertEqual(url.scheme, "about-blank")

   def test_malformed_url(self):
      url = URL("http:/example.org")
      self.assertEqual(url.scheme, "about-blank")

   def test_data_request(self):
      url = URL("data:text/html,Hello world!")
      self.assertEqual(url.request_data(), "Hello world!\n")

   def test_http_status(self):
      url = URL("http://httpbin.org/status/404")
      url.request_http()
      self.assertEqual(url.status, "404")

   def test_redirect(self):
      url = URL("http://httpbin.org/redirect/2")
      url.request_http()
      self.assertEqual(url.status, "200")

   def test_https_request(self):
      url = URL("https://httpbin.org/robots.txt")
      body = url.request_http()
      self.assertEqual(body, "User-agent: *\nDisallow: /deny\n")
     
   def test_http_gzip(self):
      url = URL("http://httpbin.org/gzip")
      url.request_http() 
      self.assertEqual(url.status, "200")

   def test_file_request(self):
      with tempfile.NamedTemporaryFile("w") as f:
         f.write("Hello world!")
         f.flush()

         url = URL(f"file:///{f.name}")
         body = url.request_file()

      self.assertEqual(body, "Hello world!\n")
    
