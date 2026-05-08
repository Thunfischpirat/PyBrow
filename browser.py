import tkinter
import sys

from url import URL

DEFAULT_WIDTH, DEFAULT_HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

PARAGRAPH_BREAK = 1.3


def lex(body: str, view_source: bool = False) -> str:
    in_tag = False
    i = 0
    text = ""
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
                    text += c
                    i += 4
                    continue
                elif entity == "&gt;":
                    text += c
                    i += 4
                    continue
            elif not in_tag:
               text += c
        else:
               text += c
        i += 1
    return text


def layout(text: str, width: int) -> list[tuple[int, int, str]]:
   display_list = []
   cursor_x, cursor_y = HSTEP, VSTEP
   for c in text:
      if c == "\n":
          cursor_y += PARAGRAPH_BREAK * VSTEP
          cursor_x = HSTEP
      else:
          display_list.append((cursor_x, cursor_y, c))
          cursor_x += HSTEP

          if cursor_x >= width - HSTEP:
             cursor_y += VSTEP
             cursor_x = HSTEP

   return display_list


class Browser:
   def __init__(self):

      self.text = ""
      self.display_list = []

      self.width = DEFAULT_WIDTH
      self.height = DEFAULT_HEIGHT

      self.window = tkinter.Tk()
      self.window.title("PyBrow")
      self.canvas = tkinter.Canvas(
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
      if url.scheme in ["http", "https"]:
          body = url.request_http()
      elif url.scheme == "file":
          body = url.request_file()
      else:
          body = url.request_data()

      self.text = lex(body, url.view_source)
      self.display_list = layout(self.text, self.width)
      self._draw()

   def _draw(self) -> None:
      self.canvas.delete("all")
      for x, y, c in self.display_list:
         if y - self.height <= self.scroll <= y + VSTEP:
            self.canvas.create_text(x, y - self.scroll, text=c)

   def _scrolldown(self, e: tkinter.EventType) -> None:
      self.scroll += SCROLL_STEP
      self._draw()

   def _scrollup(self, e: tkinter.EventType) -> None:
      if self.scroll >= SCROLL_STEP:
         self.scroll -= SCROLL_STEP
      self._draw()

   def _resize(self, e: tkinter.EventType) -> None:
     self.width = e.width
     self.height = e.height

     if self.text and self.display_list:
         self.display_list = layout(self.text, self.width)
         self._draw()

if __name__ == "__main__":
   Browser().load(URL(sys.argv[1]))
   tkinter.mainloop()
