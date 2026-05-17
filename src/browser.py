import sys
import tkinter as tk

import tkinter.font

from url import URL
from lexing import lex, Text, Tag

from typing import Union

DEFAULT_WIDTH, DEFAULT_HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

FONTS = {}


def get_font(size: 12, weight: str, style: str) -> tkinter.font.Font:
   """Return a cached font of given size, weight and style."""
   key = (size, weight, style)
   if key not in FONTS:
      font = tkinter.font.Font(size=size, weight=weight, slant=style)
      label = tkinter.Label(font=font)
      FONTS[key] = (font, label)
   return FONTS[key][0]

class Layout:
   """Determine how to display and position a list of Text tokens."""
   def __init__(self, tokens: list[Union[Text, Tag]], width: int):
      self.display_list = []
      self.width = width
 
      self.cursor_x = HSTEP
      self.cursor_y = VSTEP
      self.weight = "normal"
      self.style = "roman"
      self.size = 12

      self.center = False
      self.sup = False

      self.line = []
      
      for token in tokens:
         self._process_token(token)
      self._flush()

   def _process_token(self, token: Union[Text, Tag]) -> None: 
      """Either process each word of a Text token or modify layout based on tag types."""
      if isinstance(token, Text):
         for word in token.text.split():
            self._process_word(word)
      elif token.tagname == "i":
         self.style = "italic"
      elif token.tagname == "/i":
         self.style = "roman"
      elif token.tagname == "b":
         self.weight = "bold"
      elif token.tagname == "/b":
         self.weight = "normal"
      elif token.tagname == "small":
         self.size -= 2
      elif token.tagname == "/small":
         self.size += 2
      elif token.tagname == "big":
         self.size += 4
      elif token.tagname == "/big":
         self.size -= 4
      elif token.tagname == "br":
         self._flush()
      elif token.tagname == "/p":
         self._flush()
         self.cursor_y += VSTEP
      elif token.tagname == "h1" and token.attributes.get("class") == '"title"':
         self.center = True
      elif token.tagname == "/h1":
         self._flush()
         self.center = False
      elif token.tagname == "sup":
         self.sup = True
         self.size = int(self.size * 0.5)
      elif token.tagname == "/sup":
         self.sup = False
         self.size *= 2

   def _process_word(self, word: str) -> None:
      """Add word to a line at correct horizontal position."""
      font = get_font(self.size, self.weight, self.style)

      modifiers = []
      if self.sup:
         modifiers.append("sup")
      
      if self._check_linebreak(word.replace("\N{soft hyphen}", ""), font):
         if "\N{soft hyphen}" in word:
            w_front, w_back = self._find_longest_subword(word, font)
 
            if w_front:
               self.line.append((self.cursor_x, w_front + "-", font, modifiers))
               self._flush()
               self._process_word(w_back)
               return
   
            if self.line:
               self._flush()
               self._process_word(w_back)
               return

         self._flush()

      word = word.replace("\N{soft hyphen}", "")

      self.line.append((self.cursor_x, word, font, modifiers))
      self.cursor_x += font.measure(word) + font.measure(" ")

   def _find_longest_subword(self, word: str, font: tkinter.font.Font) -> tuple[str,str]:
      """Find the longest part of a hyphenated word that still fits in the line."""
      word_parts = word.split("\N{soft hyphen}")

      w_front = ""
      while word_parts and not self._check_linebreak(w_front + word_parts[0] + "-", font):
         w_front += word_parts.pop(0)
      w_back = "\N{soft hyphen}".join(word_parts)
   
      return w_front, w_back

   def _check_linebreak(self, word: str, font: tkinter.font.Font) -> bool:
      """Check whether the given word fits in the current line."""
      return self.cursor_x + font.measure(word) > self.width - HSTEP

   def _flush(self) -> None:
      """Determine the baseline of a line and the correct y-coordinates of its words."""
      if not self.line:
         return

      metrics = [font.metrics() for _, _, font, _ in self.line]
      max_ascent = max([m["ascent"] for m in metrics])
  
      if self.center:
         x_last, w_last, font_last = self.line[-1]
         line_end = x_last + font_last.measure(w_last)
         offset_center = (self.width - line_end - HSTEP) / 2

      baseline = self.cursor_y + 1.25 * max_ascent

      for i, (x, word, font, modifiers) in enumerate(self.line):
         y = baseline - font.metrics("ascent")

         if self.center:
            x += offset_center

         if "sup" in modifiers:
            y = baseline - max_ascent

         self.display_list.append((x, y, word, font))

      max_descent = max([m["descent"] for m in metrics])
      self.cursor_y = baseline + 1.25 * max_descent
  
      self.cursor_x = HSTEP
      self.line = []
  

class Browser:
   """GUI to display and interact with content from URL queries."""
   def __init__(self):

      self.text = ""
      self.display_list = []

      self.width = DEFAULT_WIDTH
      self.height = DEFAULT_HEIGHT

      self.window = tk.Tk()
      self.window.title("PyBrow")

      self.canvas = tk.Canvas(
         self.window,
         width=DEFAULT_WIDTH,
         height=DEFAULT_HEIGHT
      )
 
      self.canvas.pack(fill="both", expand=True)

      self.scroll = 0

      self.window.bind("<Down>", self._scrolldown)
      self.window.bind("<Up>", self._scrollup)
      self.window.bind("<Button-4>", self._scrollup)
      self.window.bind("<Button-5>", self._scrolldown)

      self.window.bind("<Configure>", self._resize)

   def load(self, url: URL) -> None:
      """Request data from URL based on various schemes."""
      if url.scheme in ["http", "https"]:
          body = url.request_http()
      elif url.scheme == "file":
          body = url.request_file()
      elif url.scheme == "data":
          body = url.request_data()
      else:
          body = url.about_blank()

      self.text = lex(body, url.view_source)
      self.display_list = Layout(self.text, self.width).display_list
      self._draw()

   def _draw(self) -> None:
      """Draw visible words to the Canvas."""
      self.canvas.delete("all")
      for x, y, w, f in self.display_list:
         if y - self.height <= self.scroll <= y + VSTEP:
            self.canvas.create_text(x, y - self.scroll, text=w, font=f, anchor="nw")

   def _scrolldown(self, e: tk.EventType) -> None:
      self.scroll += SCROLL_STEP
      self._draw()

   def _scrollup(self, e: tk.EventType) -> None:
      if self.scroll >= SCROLL_STEP:
         self.scroll -= SCROLL_STEP
      self._draw()

   def _resize(self, e: tk.EventType) -> None:
     self.width = e.width
     self.height = e.height

     if self.text and self.display_list:
         self.display_list = Layout(self.text, self.width).display_list
         self._draw()


if __name__ == "__main__":
   Browser().load(URL(sys.argv[1]))
   tk.mainloop()
