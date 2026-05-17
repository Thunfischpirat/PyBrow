from dataclasses import dataclass

from typing import Union

@dataclass
class Text:
   text: str

@dataclass
class Tag:
   """A tag has a name and attributes with values."""
   tagname: str
   attributes: dict[str, str] 

def parse_tag(buffer: str) -> Tag:
   """Return tag with name and attributes from buffer string."""
   entries = buffer.split()
   tagname = entries.pop(0) 
   attributes = dict()

   if tagname == "!DOCTYPE":
      return Tag(tagname, attributes)
   elif tagname == "!--":
      return Tag(tagname, {"comment": entries.pop(0) })

   for e in entries:
      if "=" in e:
         name, value = e.split("=", 1)
         attributes[name] = value

   return Tag(tagname, attributes)
   

def lex(body: str, view_source: bool = False) -> list[Union[Text, Tag]]:
    """Tokenize a response body into Text and Tag elements."""
    in_tag = False
    out = []
    i = 0
    buffer = ""

    if view_source:
       out.append(Text(body))
       return out

    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
            if buffer:
               out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(parse_tag(buffer)) 
            buffer = ""
        elif c == "&":
            if body[i:i+4] == "&lt;":
                buffer += "<"
                i += 4
                continue
            elif body[i:i+4] == "&gt;":
                buffer += ">"
                i += 4
                continue
            elif body[i:i+5] == "&shy;":
                buffer += "\N{soft hyphen}"
                i += 5
                continue
        else:
           buffer += c
        i += 1
    
    if not in_tag and buffer:
       out.append(Text(buffer))

    return out

