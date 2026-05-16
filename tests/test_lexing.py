import unittest

from lexing import lex, Text, Tag

class TestLexing(unittest.TestCase):
   """Test processing of response bodies.""" 
   def test_plain_text(self):
      body = "Hello world!"
      self.assertEqual(lex(body), [Text(body)])

   def test_tags(self):
      body = "<b>Hello world!</b>"
      expected_list = [Tag('b', dict()), Text(text='Hello world!'), Tag('/b', dict())]
      self.assertEqual(lex(body), expected_list)

   def test_tag_attributes(self):
      body = '<h1 class="title"> and </h1>'
      expected_list = [Tag("h1", {"class": '"title"'}),
                       Text(text=" and "), 
                       Tag("/h1", dict())]
      self.assertEqual(lex(body), expected_list)

   def test_entities(self):
      body = "Hello &lt;world&gt;"
      self.assertEqual(lex(body), [Text("Hello <world>")])

   def test_view_source(self):
      body = "<b>Hello world!</b>"
      self.assertEqual(lex(body, True), [Text(body)])
