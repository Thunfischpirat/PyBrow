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

      self.line = []
      
      for token in tokens:
         self._process_token(token)
      self._flush()

   def _process_token(self, token: Union[Text, Tag]) -> None: 
      """Either process each word of a Text token or modify layout based on tag types."""
      if isinstance(token, Text):
         for word in token.text.split():
            self._process_word(word)
      elif token.tag == "i":
         self.style = "italic"
      elif token.tag == "/i":
         self.style = "roman"
      elif token.tag == "b":
         self.weight = "bold"
      elif token.tag == "/b":
         self.weight = "normal"
      elif token.tag == "small":
         self.size -= 2
      elif token.tag == "/small":
         self.size += 2
      elif token.tag == "big":
         self.size += 4
      elif token.tag == "/big":
         self.size -= 4
      elif token.tag == "br":
         self._flush()
      elif token.tag == "/p":
         self._flush()
         self.cursor_y += VSTEP

   def _process_word(self, word: Text) -> None:
      """Add word to a line at correct horizontal position."""
      font = get_font(self.size, self.weight, self.style)
      w = font.measure(word)
      if self.cursor_x + w > self.width - HSTEP:
         self._flush()
      else:
          self.line.append((self.cursor_x, word, font))
          self.cursor_x += w + font.measure(" ")

   def _flush(self) -> None:
      """Determine the baseline of a line and the correct y-coordinates of its words."""
      if not self.line:
         return

      metrics = [font.metrics() for _, _, font in self.line]
      max_ascent = max([m["ascent"] for m in metrics])

      baseline = self.cursor_y + 1.25 * max_ascent

      for x, word, font in self.line:
         y = baseline - font.metrics("ascent")
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
