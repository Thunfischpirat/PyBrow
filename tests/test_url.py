import unittest

import io
import tempfile
import http.server

from url import URL

class TestURL(unittest.TestCase):
   """Test that the supported request schemes for URLs work."""
   def test_about_blank(self):
      url = URL("about:blank")
      url.about_blank()
      self.assertEqual(url.scheme, "about-blank")

   def test_malformed_url(self):
      url = URL("http:/example.org")
      self.assertEqual(url.scheme, "about-blank")

   def test_malformed_scheme(self):
      url = URL("htto://example.org")
      self.assertEqual(url.scheme, "about-blank")

   def test_data_request(self):
      url = URL("data:text/html,Hello world!")
      self.assertEqual(url.request_data(), "Hello world!\n")

   def test_simple_http_request(self):
      url = URL("http://example.org")
      url.request_http()
      self.assertEqual(url.status, "200")

   def test_http_status(self):
      url = URL("http://httpbin.org/status/404")
      url.request_http()
      self.assertEqual(url.status, "404")

   def test_view_source(self):
      url = URL("view-source:http://httpbin.org/html")
      body = url.request_http()
      self.assertTrue(body.startswith("<!DOCTYPE html>"))
      self.assertTrue(body.endswith("</html>"))

   def test_http_custom_port(self):
      port = 8080
      url = URL(f"http://localhost:{port}/")
      self.assertEqual(url.port, port)

   def test_malformed_port(self):
      url = URL("http://localhost:not-a-port/")
      self.assertEqual(url.scheme, "about-blank")

   def test_redirect(self):
      url = URL("http://httpbin.org/redirect/2")
      url.request_http()
      self.assertEqual(url.status, "200")

   def test_too_many_redirect(self):
      url = URL("http://httpbin.org/redirect/6")
      with self.assertRaises(RuntimeError):
         url.request_http()

   def test_read_response_without_length_or_transfer_encoding(self):
      url = URL("http://example.org/")
      response = io.BytesIO(b"Hello world!")
      body = url._read_response({}, response)
      self.assertEqual(body, b"Hello world!")

   def test_https_request(self):
      url = URL("https://httpbin.org/robots.txt")
      body = url.request_http()
      self.assertEqual(body, "User-agent: *\nDisallow: /deny\n")

   def test_http_gzip(self):
      url = URL("http://httpbin.org/gzip")
      url.request_http() 
      self.assertEqual(url.status, "200")

   def test_http_transfer_encoding(self):
      url = URL("http://httpbin.org/stream/20")
      url.request_http()
      self.assertEqual(url.status, "200")

   def test_file_request(self):
      with tempfile.NamedTemporaryFile("w") as f:
         f.write("Hello world!")
         f.flush()

         url = URL(f"file:///{f.name}")
         body = url.request_file()

      self.assertEqual(body, "Hello world!\n")
    
