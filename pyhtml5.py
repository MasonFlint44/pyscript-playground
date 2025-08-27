"""
pyhtml5.py — A tiny HTML5 + CSS DSL for PyScript (non‑abbreviated class names)

- Classes are generated from a TAG->ClassName mapping you can tweak.
- All elements are context managers (Gradio-like nested `with`).
- Works in PyScript (mounts into the DOM) or renders to strings.
- Generic CSS builder for rules and common at‑rules.

NOTE: Lower-case tag aliases like `div()` are intentionally not exported,
so class names are never abbreviated (e.g., use `Division()` not `Div()`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import html

# ---- PyScript / browser detection -------------------------------------------------

HAS_JS = False
_document = None
try:
    from js import document as _document  # type: ignore
    HAS_JS = True
except Exception:
    HAS_JS = False

# ---- Utilities -------------------------------------------------------------------

def _hyphenate(name: str) -> str:
    """Map pythonic identifiers to HTML/CSS attribute/property names."""
    if name.endswith("_"):
        name = name[:-1]
    name = name.replace("__", "-")
    name = name.replace("_", "-")
    return name

def _stringify(value: Any) -> str:
    if value is True:
        return ""
    if value is False or value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(map(str, value))
    return str(value)

def _normalize_attrs(attrs: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in attrs.items():
        if v is None or v is False:
            continue
        name = _hyphenate(k)
        out[name] = _stringify(v)
    return out

def _normalize_style(style: Union[str, Dict[str, Any], None]) -> str:
    if style is None:
        return ""
    if isinstance(style, str):
        return style
    parts = []
    for k, v in style.items():
        if v is None or v is False:
            continue
        parts.append(f"{_hyphenate(k)}:{v}")
    return ";".join(parts)

# ---- Build stacks ----------------------------------------------------------------

class _BuildStacks:
    element_stack: List["Element"] = []
    css_stack: List["CSSContainer"] = []

    @classmethod
    def current_element_parent(cls) -> Optional["Element"]:
        return cls.element_stack[-1] if cls.element_stack else None

    @classmethod
    def push_element(cls, el: "Element") -> None:
        cls.element_stack.append(el)

    @classmethod
    def pop_element(cls) -> None:
        if cls.element_stack:
            cls.element_stack.pop()

    @classmethod
    def current_css_container(cls) -> Optional["CSSContainer"]:
        return cls.css_stack[-1] if cls.css_stack else None

    @classmethod
    def push_css(cls, c: "CSSContainer") -> None:
        cls.css_stack.append(c)

    @classmethod
    def pop_css(cls) -> None:
        if cls.css_stack:
            cls.css_stack.pop()

# ---- Nodes -----------------------------------------------------------------------

class Node:
    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        raise NotImplementedError

    def to_dom(self, parent_js=None):
        raise NotImplementedError

    def mount(self, target: Optional[Union[str, Any]] = None):
        if not HAS_JS:
            raise RuntimeError("mount() requires PyScript / a browser (js.document).")
        if target is None:
            parent = _document.body
        elif isinstance(target, str):
            parent = _document.querySelector(target)
            if parent is None:
                raise ValueError(f"mount target not found: {target}")
        else:
            parent = target
        return self.to_dom(parent)

class Text(Node):
    def __init__(self, text: str):
        self.text = str(text)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return (self.text if _in_raw_text else html.escape(self.text))

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        tn = _document.createTextNode(self.text)
        if parent_js is not None:
            parent_js.appendChild(tn)
        return tn

class Comment(Node):
    def __init__(self, text: str):
        self.text = str(text)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return f"<!-- {html.escape(self.text)} -->"

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        cn = _document.createComment(self.text)
        if parent_js is not None:
            parent_js.appendChild(cn)
        return cn

class Fragment(Node):
    def __init__(self, *children: Union[Node, str]):
        self.children: List[Node] = []
        for c in children:
            self.add(c)

    def __enter__(self):
        _BuildStacks.push_element(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_element()
        return False

    def add(self, child: Union["Node", str, None]) -> Optional["Node"]:
        if child is None:
            return None
        if isinstance(child, str):
            child = Text(child)
        self.children.append(child)
        return child

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        return "".join(ch.to_html(indent, _in_raw_text=_in_raw_text) for ch in self.children)

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        frag = _document.createDocumentFragment()
        for ch in self.children:
            ch.to_dom(frag)
        if parent_js is not None:
            parent_js.appendChild(frag)
        return frag

# ---- Element ---------------------------------------------------------------------

VOID_TAGS = {
    "area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"
}
RAW_TEXT_TAGS = {"script", "style"}

class Element(Node):
    _tag: str = "div"
    _void: bool = False

    def __init__(self, *children: Union[Node, str], **attrs):
        self.tag = getattr(self, "_tag", "div")
        self.void = self.tag in VOID_TAGS
        self.attrs: Dict[str, str] = {}
        self.children: List[Node] = []

        style = attrs.pop("style", None)
        classes = attrs.pop("class_", None) or attrs.pop("class", None)

        self.attrs.update(_normalize_attrs(attrs))
        if classes:
            self.add_class(classes)
        if style:
            self.set_style(style)

        parent = _BuildStacks.current_element_parent()
        if parent is not None:
            parent.add(self)

        for c in children:
            self.add(c)

    def __enter__(self):
        _BuildStacks.push_element(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_element()
        return False

    def add(self, child: Union["Node", str, None]) -> Optional["Node"]:
        if child is None:
            return None
        if self.void:
            raise TypeError(f"<{self.tag}> is a void element and cannot have children.")
        if isinstance(child, str):
            child = Text(child)
        self.children.append(child)
        return child

    def __call__(self, *children: Union["Node", str], **attrs) -> "Element":
        for c in children:
            self.add(c)
        if attrs:
            self.attrs.update(_normalize_attrs(attrs))
        return self

    def set_attr(self, **attrs) -> "Element":
        self.attrs.update(_normalize_attrs(attrs))
        return self

    def add_class(self, *classes) -> "Element":
        tokens: List[str] = []
        for cls in classes:
            if cls is None or cls is False:
                continue
            if isinstance(cls, (list, tuple, set)):
                for t in cls:
                    if t:
                        tokens.extend(str(t).split())
            else:
                tokens.extend(str(cls).split())
        if not tokens:
            return self
        existing = self.attrs.get("class", "")
        merged = (existing + " " + " ".join(tokens)).strip() if existing else " ".join(tokens)
        self.attrs["class"] = merged
        return self

    def classes(self, *classes) -> "Element":
        return self.add_class(*classes)

    def set_style(self, style: Union[str, Dict[str, Any]]) -> "Element":
        style_str = _normalize_style(style) if isinstance(style, dict) else style
        existing = self.attrs.get("style", "")
        if existing and style_str:
            self.attrs["style"] = existing.rstrip(";") + ";" + style_str
        elif style_str:
            self.attrs["style"] = style_str
        return self

    def style(self, **props) -> "Element":
        return self.set_style(props)

    def data(self, **ds) -> "Element":
        for k, v in ds.items():
            self.attrs[f"data-{_hyphenate(k)}"] = _stringify(v)
        return self

    def aria(self, **props) -> "Element":
        for k, v in props.items():
            self.attrs[f"aria-{_hyphenate(k)}"] = _stringify(v)
        return self

    def _attrs_to_html(self) -> str:
        if not self.attrs:
            return ""
        parts = []
        for k, v in self.attrs.items():
            if v == "" and k not in {"value"} and k not in {"style","class"} and not k.startswith(("aria-","data-")):
                parts.append(f" {k}")  # boolean or valueless attribute
            else:
                v_escaped = html.escape(v, quote=True)
                parts.append(f' {k}="{v_escaped}"')
        return "".join(parts)

    def to_html(self, indent: int = 0, _in_raw_text: bool = False) -> str:
        pad = "  " * indent if indent else ""
        open_tag = f"<{self.tag}{self._attrs_to_html()}>"
        if self.void:
            return pad + open_tag
        if not self.children:
            return pad + open_tag + f"</{self.tag}>"
        in_raw = self.tag in RAW_TEXT_TAGS
        has_block = any(isinstance(ch, Element) and not ch.void for ch in self.children)
        if has_block:
            inner = []
            for ch in self.children:
                if isinstance(ch, Element):
                    inner.append("\n" + ch.to_html(indent + 1, _in_raw_text=in_raw))
                else:
                    inner.append("\n" + ("  " * (indent + 1)) + ch.to_html(indent + 1, _in_raw_text=in_raw))
            inner_str = "".join(inner) + "\n" + pad
            return pad + open_tag + inner_str + f"</{self.tag}>"
        else:
            inner = "".join(ch.to_html(indent, _in_raw_text=in_raw) for ch in self.children)
            return pad + open_tag + inner + f"</{self.tag}>"

    def to_dom(self, parent_js=None):
        if not HAS_JS:
            return None
        el = _document.createElement(self.tag)
        for k, v in self.attrs.items():
            if v == "" and k not in {"value"} and k not in {"style","class"} and not k.startswith(("aria-","data-")):
                el.setAttribute(k, "")
            else:
                el.setAttribute(k, v)
        if not self.void:
            for ch in self.children:
                ch.to_dom(el)
        if parent_js is not None:
            parent_js.appendChild(el)
        return el

# ---- HTML5 tag mapping -> non-abbreviated class names -----------------------------

# Full element set (same as previous version)
_HTML5_TAGS = [
    # Document metadata
    "html","head","title","base","link","meta","style",
    # Sections
    "body","address","article","aside","footer","header","h1","h2","h3","h4","h5","h6","hgroup","main","nav","section",
    # Grouping
    "blockquote","dd","div","dl","dt","figcaption","figure","hr","li","menu","ol","p","pre","ul",
    # Text-level
    "a","abbr","b","bdi","bdo","br","cite","code","data","dfn","em","i","kbd","mark","q","rp","rt","ruby","s","samp","small","span","strong","sub","sup","time","u","var","wbr",
    # Edits
    "del","ins",
    # Embedded
    "area","audio","img","map","track","video","embed","iframe","object","param","picture","source",
    # Scripting
    "canvas","noscript","script","slot","template",
    # Table
    "caption","col","colgroup","table","tbody","td","tfoot","th","thead","tr",
    # Forms
    "button","datalist","fieldset","form","input","label","legend","meter","optgroup","option","output","progress","select","textarea",
    # Interactive
    "details","dialog","summary",
    # Non-standard but handy
    "portal"
]

# Non-abbreviated class names (tweak here)
TAG_TO_CLASSNAME: Dict[str, str] = {
    # Document metadata
    "html": "Html",
    "head": "Head",
    "title": "Title",
    "base": "Base",
    "link": "Link",
    "meta": "Meta",
    "style": "Style",
    # Sections
    "body": "Body",
    "address": "Address",
    "article": "Article",
    "aside": "Aside",
    "footer": "Footer",
    "header": "Header",
    "h1": "Heading1",
    "h2": "Heading2",
    "h3": "Heading3",
    "h4": "Heading4",
    "h5": "Heading5",
    "h6": "Heading6",
    "hgroup": "HeadingGroup",
    "main": "Main",
    "nav": "Navigation",
    "section": "Section",
    # Grouping
    "blockquote": "BlockQuote",
    "dd": "DescriptionDetails",
    "div": "Division",
    "dl": "DescriptionList",
    "dt": "DescriptionTerm",
    "figcaption": "FigureCaption",
    "figure": "Figure",
    "hr": "HorizontalRule",
    "li": "ListItem",
    "menu": "Menu",
    "ol": "OrderedList",
    "p": "Paragraph",
    "pre": "PreformattedText",
    "ul": "UnorderedList",
    # Text-level
    "a": "Anchor",
    "abbr": "Abbreviation",
    "b": "Bold",
    "bdi": "BidirectionalIsolation",
    "bdo": "BidirectionalOverride",
    "br": "LineBreak",
    "cite": "Citation",
    "code": "Code",
    "data": "Data",
    "dfn": "Definition",
    "em": "Emphasis",
    "i": "Italic",
    "kbd": "KeyboardInput",
    "mark": "Mark",
    "q": "Quotation",
    "rp": "RubyParenthesis",
    "rt": "RubyText",
    "ruby": "RubyAnnotation",
    "s": "Strikethrough",
    "samp": "SampleOutput",
    "small": "Small",
    "span": "Span",
    "strong": "Strong",
    "sub": "Subscript",
    "sup": "Superscript",
    "time": "Time",
    "u": "Underline",
    "var": "Variable",
    "wbr": "WordBreakOpportunity",
    # Edits
    "del": "Deletion",
    "ins": "Insertion",
    # Embedded
    "area": "MapArea",
    "audio": "Audio",
    "img": "Image",
    "map": "ImageMap",
    "track": "Track",
    "video": "Video",
    "embed": "Embed",
    "iframe": "InlineFrame",
    "object": "Object",
    "param": "Parameter",
    "picture": "Picture",
    "source": "Source",
    # Scripting
    "canvas": "Canvas",
    "noscript": "NoScript",
    "script": "Script",
    "slot": "Slot",
    "template": "Template",
    # Table
    "caption": "TableCaption",
    "col": "TableColumn",
    "colgroup": "TableColumnGroup",
    "table": "Table",
    "tbody": "TableBody",
    "td": "TableDataCell",
    "tfoot": "TableFooter",
    "th": "TableHeaderCell",
    "thead": "TableHead",
    "tr": "TableRow",
    # Forms
    "button": "Button",
    "datalist": "DataList",
    "fieldset": "FieldSet",
    "form": "Form",
    "input": "Input",
    "label": "Label",
    "legend": "Legend",
    "meter": "Meter",
    "optgroup": "OptionGroup",
    "option": "Option",
    "output": "Output",
    "progress": "Progress",
    "select": "Select",
    "textarea": "TextArea",
    # Interactive
    "details": "Details",
    "dialog": "Dialog",
    "summary": "Summary",
    # Non-standard
    "portal": "Portal",
}

# Validate we covered the full list
_missing = [t for t in _HTML5_TAGS if t not in TAG_TO_CLASSNAME]
if _missing:
    raise RuntimeError(f"TAG_TO_CLASSNAME missing entries: {_missing}")

CLASSNAME_TO_TAG: Dict[str, str] = {v: k for k, v in TAG_TO_CLASSNAME.items()}
TAG_TO_CLASS: Dict[str, type] = {}
CLASSNAME_TO_CLASS: Dict[str, type] = {}

def rebuild_html_classes(overrides: Optional[Dict[str, str]] = None) -> None:
    """
    Rebuild the HTML element classes from TAG_TO_CLASSNAME.
    Optionally pass `overrides` to adjust names on the fly:
        rebuild_html_classes({"hr": "HorizontalRuleLine"})
    """
    global TAG_TO_CLASSNAME, CLASSNAME_TO_TAG, TAG_TO_CLASS, CLASSNAME_TO_CLASS
    if overrides:
        TAG_TO_CLASSNAME = {**TAG_TO_CLASSNAME, **overrides}
        CLASSNAME_TO_TAG = {v: k for k, v in TAG_TO_CLASSNAME.items()}

    # Remove existing generated classes from globals (in case we're rebuilding)
    for name in list(CLASSNAME_TO_CLASS.keys()):
        if name in globals():
            try:
                del globals()[name]
            except Exception:
                pass

    TAG_TO_CLASS.clear()
    CLASSNAME_TO_CLASS.clear()

    for tag, class_name in TAG_TO_CLASSNAME.items():
        cls = type(class_name, (Element,), {"_tag": tag})
        globals()[class_name] = cls
        TAG_TO_CLASS[tag] = cls
        CLASSNAME_TO_CLASS[class_name] = cls

def element_class_for_tag(tag: str) -> type:
    return TAG_TO_CLASS[tag]

def tag_for_element_class_name(class_name: str) -> str:
    return CLASSNAME_TO_TAG[class_name]

def create(tag: str, *children, **attrs) -> Element:
    """Instantiate by tag string using the current mapping."""
    return element_class_for_tag(tag)(*children, **attrs)

def custom(tag_name: str, *children, **attrs) -> Element:
    """Create a custom element with an arbitrary tag name (e.g., web components)."""
    cls = type("Custom_" + "".join(p.capitalize() for p in tag_name.split("-")), (Element,), {"_tag": tag_name})
    return cls(*children, **attrs)

# Build classes on import
rebuild_html_classes()

# ---- CSS Builder (unchanged) -----------------------------------------------------

def _css_prop_name(name: str) -> str:
    return _hyphenate(name)

@dataclass
class CSSDeclaration:
    prop: str
    value: str
    def to_css(self) -> str:
        return f"{self.prop}:{self.value};"

class CSSContainer:
    def __init__(self):
        self.children: List[Union["CSSStyleRule","AtRule","KeyframesRule","PageRule","FontFaceRule"]] = []

    def __enter__(self):
        _BuildStacks.push_css(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_css()
        return False

    def add(self, child):
        self.children.append(child)
        return child

    def rule(self, selector: str, **props) -> "CSSStyleRule":
        rule = CSSStyleRule(selector, props)
        container = _BuildStacks.current_css_container() or self
        container.add(rule)
        return rule

    def media(self, query: str) -> "AtRule":
        ar = AtRule("media", query)
        ( _BuildStacks.current_css_container() or self ).add(ar)
        return ar

    def supports(self, condition: str) -> "AtRule":
        ar = AtRule("supports", condition)
        ( _BuildStacks.current_css_container() or self ).add(ar)
        return ar

    def layer(self, name: Optional[str] = None) -> "AtRule":
        ar = AtRule("layer", name or "")
        ( _BuildStacks.current_css_container() or self ).add(ar)
        return ar

    def container(self, query: str) -> "AtRule":
        ar = AtRule("container", query)
        ( _BuildStacks.current_css_container() or self ).add(ar)
        return ar

    def page(self, selector: Optional[str] = None) -> "PageRule":
        pr = PageRule(selector)
        ( _BuildStacks.current_css_container() or self ).add(pr)
        return pr

    def keyframes(self, name: str) -> "KeyframesRule":
        kf = KeyframesRule(name)
        ( _BuildStacks.current_css_container() or self ).add(kf)
        return kf

    def font_face(self, **props) -> "FontFaceRule":
        ff = FontFaceRule(props)
        ( _BuildStacks.current_css_container() or self ).add(ff)
        return ff

    def to_css(self, indent: int = 0) -> str:
        return "".join(ch.to_css(indent) for ch in self.children)

    def mount(self, target: Optional[Union[str, Any]] = None):
        css_text = self.to_css()
        if not HAS_JS:
            raise RuntimeError("Stylesheet.mount() requires PyScript / a browser (js.document).")
        style_el = _document.createElement("style")
        style_el.setAttribute("type", "text/css")
        style_el.textContent = css_text
        if target is None:
            _document.head.appendChild(style_el)
        elif isinstance(target, str):
            parent = _document.querySelector(target)
            if parent is None:
                raise ValueError(f"mount target not found: {target}")
            parent.appendChild(style_el)
        else:
            target.appendChild(style_el)
        return style_el

class Stylesheet(CSSContainer):
    pass

class CSSStyleRule:
    def __init__(self, selector: str, props: Optional[Dict[str, Any]] = None):
        self.selector = selector
        self.decls: List[CSSDeclaration] = []
        if props:
            for k, v in props.items():
                if v is None or v is False:
                    continue
                self.decls.append(CSSDeclaration(_css_prop_name(k), str(v)))

    def __enter__(self):
        _BuildStacks.push_css(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_css()
        return False

    def decl(self, prop: str, value: Any) -> "CSSStyleRule":
        self.decls.append(CSSDeclaration(_css_prop_name(prop), str(value)))
        return self

    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  "*(indent+1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}{self.selector} {{\n{inner}{pad}}}\n"

class AtRule(CSSContainer):
    def __init__(self, name: str, prelude: str):
        super().__init__()
        self.name = name
        self.prelude = prelude
    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}@{self.name} {self.prelude} {{\n{inner}{pad}}}\n"

class KeyframesRule(CSSContainer):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def frame(self, selector: str, **props) -> "CSSStyleRule":
        rule = CSSStyleRule(selector, props)
        ( _BuildStacks.current_css_container() or self ).add(rule)
        return rule
    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}@keyframes {self.name} {{\n{inner}{pad}}}\n"

class PageRule(CSSContainer):
    def __init__(self, selector: Optional[str] = None):
        super().__init__()
        self.selector = selector
    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        head = "@page" + (f" {self.selector}" if self.selector else "")
        inner = "".join(ch.to_css(indent + 1) for ch in self.children)
        return f"{pad}{head} {{\n{inner}{pad}}}\n"

class FontFaceRule:
    def __init__(self, props: Optional[Dict[str, Any]] = None):
        self.decls: List[CSSDeclaration] = []
        if props:
            for k, v in props.items():
                if v is None or v is False:
                    continue
                self.decls.append(CSSDeclaration(_css_prop_name(k), str(v)))
    def __enter__(self):
        _BuildStacks.push_css(self); return self
    def __exit__(self, exc_type, exc, tb):
        _BuildStacks.pop_css(); return False
    def decl(self, prop: str, value: Any) -> "FontFaceRule":
        self.decls.append(CSSDeclaration(_css_prop_name(prop), str(value))); return self
    def to_css(self, indent: int = 0) -> str:
        pad = "  " * indent if indent else ""
        inner = "".join("  "*(indent+1) + d.to_css() + "\n" for d in self.decls)
        return f"{pad}@font-face {{\n{inner}{pad}}}\n"

# ---- Convenience API --------------------------------------------------------------

def html_string(node: Node) -> str:
    return node.to_html()

def css_string(sheet: Stylesheet) -> str:
    return sheet.to_css()
