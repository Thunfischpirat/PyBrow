import unittest

from lexing import lex, Text, Tag

class TestLexing(unittest.TestCase):
   """Test processing of response bodies.""" 
   def test_plain_text(self):
      body = "Hello world!"
      self.assertEqual(lex(body), [Text(body)])

   def test_tags(self):
      body = "<b>Hello world!</b>"
      expected_list = [Tag(tag='b'), Text(text='Hello world!'), Tag(tag='/b')]
      self.assertEqual(lex(body), expected_list)

   def test_entities(self):
      body = "Hello &lt;world&gt;"
      self.assertEqual(lex(body), [Text("Hello <world>")])

   def test_view_source(self):
      body = "<b>Hello world!</b>"
      self.assertEqual(lex(body, True), [Text(body)])
