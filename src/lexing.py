from dataclasses import dataclass

from typing import Union

@dataclass
class Text:
   text: str

@dataclass
class Tag:
   tag: str

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
            out.append(Tag(buffer)) 
            buffer = ""
        elif c == "&":
            entity = body[i:i + 4]
            if entity == "&lt;":
                buffer += "<"
                i += 4
                continue
            elif entity == "&gt;":
                buffer += ">"
                i += 4
                continue
        else:
           buffer += c
        i += 1
    
    if not in_tag and buffer:
       out.append(Text(buffer))

    return out

