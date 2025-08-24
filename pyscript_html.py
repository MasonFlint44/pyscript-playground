# pyscript_ui_app_cm.py
# App-scoped, context-managed declarative UI DSL that mirrors HTML5 tags
# with clear, unabbreviated Python class names (no redundant *Element suffixes).

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence, Union, Optional, List
import contextvars

# --------------------------------------------------------------------------------------
# App-scoped context
# --------------------------------------------------------------------------------------
_CURRENT_APP: contextvars.ContextVar["App | None"] = contextvars.ContextVar(
    "_CURRENT_APP", default=None
)

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------

def _escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

def _normalize_class(cls: Union[str, Sequence[str], None]) -> Optional[str]:
    if cls is None:
        return None
    if isinstance(cls, str):
        return cls.strip() or None
    return " ".join([c for c in cls if c]).strip() or None

def _attr_key(k: str) -> str:
    if k.endswith("_"):
        k = k[:-1]
    if k.startswith("data_"):
        return "data-" + k[5:].replace("_", "-")
    if k.startswith("aria_"):
        return "aria-" + k[5:].replace("_", "-")
    return k

def _attr_value(v: Any) -> str:
    if isinstance(v, bool):
        return ""
    return _escape_html(v)

# --------------------------------------------------------------------------------------
# CSS (at-rules and rules)
# --------------------------------------------------------------------------------------

class CssNode:
    def to_css(self) -> str:
        raise NotImplementedError

@dataclass
class StyleRule(CssNode):
    selector: str
    props: Mapping[str, Any]

    def __post_init__(self):
        if not isinstance(self.props, dict):
            self.props = dict(self.props)

    def __enter__(self) -> "StyleRule":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def set(self, **props: Any) -> "StyleRule":
        self.props.update(props)
        return self

    def to_css(self) -> str:
        body = "\n".join(
            f"  {k.replace('_','-')}: {v};" for k, v in self.props.items()
        )
        return f"{self.selector} {{\n{body}\n}}"

@dataclass
class RuleBlock(CssNode):
    header: str
    children: list[CssNode] = field(default_factory=list)

    def __enter__(self) -> "RuleBlock":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def rule(self, selector: str, **props: Any) -> StyleRule:
        r = StyleRule(selector, dict(props))
        self.children.append(r)
        return r

    def add(self, *nodes: CssNode) -> "RuleBlock":
        self.children.extend(nodes)
        return self

    def to_css(self) -> str:
        inner = "\n\n".join(n.to_css() for n in self.children)
        return f"{self.header} {{\n{inner}\n}}"

@dataclass
class Keyframes(CssNode):
    name: str
    steps: list[StyleRule] = field(default_factory=list)

    def __enter__(self) -> "Keyframes":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def step(self, selector: str, **props: Any) -> StyleRule:
        r = StyleRule(selector, dict(props))
        self.steps.append(r)
        return r

    def to_css(self) -> str:
        inner = "\n\n".join(r.to_css() for r in self.steps)
        inner = inner.replace(" {\n", " {\n  ").replace("\n}", "\n  }")
        return f"@keyframes {self.name} {{\n{inner}\n}}"

@dataclass
class FontFace(CssNode):
    props: Mapping[str, Any]

    def __enter__(self) -> "FontFace":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def set(self, **props: Any) -> "FontFace":
        self.props = {**self.props, **props}
        return self

    def to_css(self) -> str:
        body = "\n".join(f"  {k.replace('_','-')}: {v};" for k, v in self.props.items())
        return f"@font-face {{\n{body}\n}}"

@dataclass
class ImportRule(CssNode):
    url: str
    media: Optional[str] = None
    def to_css(self) -> str:
        if self.media:
            return f"@import url('{self.url}') {self.media};"
        return f"@import url('{self.url}');"

@dataclass
class PropertyRule(CssNode):
    name: str
    syntax: str = "*"
    inherits: str = "false"
    initial_value: Optional[str] = None
    def to_css(self) -> str:
        lines = [
            f"@property {self.name} {{",
            f"  syntax: '{self.syntax}';",
            f"  inherits: {self.inherits};",
        ]
        if self.initial_value is not None:
            lines.append(f"  initial-value: {self.initial_value};")
        lines.append("}")
        return "\n".join(lines)

@dataclass
class StyleSheet:
    nodes: list[CssNode] = field(default_factory=list)

    def add(self, selector: str, **props: Any) -> "StyleSheet":
        self.nodes.append(StyleRule(selector, props))
        return self

    def rule(self, selector: str, **props: Any) -> StyleRule:
        r = StyleRule(selector, dict(props))
        self.nodes.append(r)
        return r

    def media(self, query: str) -> RuleBlock:
        rb = RuleBlock(f"@media {query}")
        self.nodes.append(rb)
        return rb

    def supports(self, condition: str) -> RuleBlock:
        rb = RuleBlock(f"@supports {condition}")
        self.nodes.append(rb)
        return rb

    def container(self, query: str) -> RuleBlock:
        rb = RuleBlock(f"@container {query}")
        self.nodes.append(rb)
        return rb

    def layer(self, name: Optional[str] = None) -> RuleBlock:
        header = "@layer" if name is None else f"@layer {name}"
        rb = RuleBlock(header)
        self.nodes.append(rb)
        return rb

    def keyframes(self, name: str) -> Keyframes:
        kf = Keyframes(name)
        self.nodes.append(kf)
        return kf

    def font_face(self, **props: Any) -> FontFace:
        ff = FontFace(props)
        self.nodes.append(ff)
        return ff

    def import_url(self, url: str, media: Optional[str] = None) -> ImportRule:
        ir = ImportRule(url, media)
        self.nodes.insert(0, ir)
        return ir

    def property(
        self,
        name: str,
        *,
        syntax: str = "*",
        inherits: str = "false",
        initial_value: Optional[str] = None,
    ) -> PropertyRule:
        pr = PropertyRule(name, syntax, inherits, initial_value)
        self.nodes.append(pr)
        return pr

    def __enter__(self) -> "StyleSheet":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def to_css(self) -> str:
        return "\n\n".join(n.to_css() for n in self.nodes)

    def to_style_tag(self) -> str:
        return f"<style>\n{self.to_css()}\n</style>"

# --------------------------------------------------------------------------------------
# Elements (context-managed, app-aware)
# --------------------------------------------------------------------------------------

Child = Union["Element", str]

@dataclass
class Element:
    tag: str
    children: list[Child] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        tag: str,
        children: Optional[Iterable[Child]] = None,
        *,
        cls: Union[str, Sequence[str], None] = None,
        **attrs: Any,
    ) -> None:
        self.tag = tag
        self.children = list(children or [])
        self.attrs = dict(attrs)
        if (c := _normalize_class(cls)) is not None:
            existing = self.attrs.get("class", None) or self.attrs.get("class_", None)
            if existing:
                c = f"{existing} {c}"
            self.attrs["class"] = c

    def __enter__(self) -> "Element":
        app = App.current()
        if app is None:
            raise RuntimeError("Create elements inside an App: with App() as app: ...")
        if app._stack:
            app._stack[-1].children.append(self)
        else:
            app._root_children.append(self)
        app._stack.append(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        app = App.current()
        if app is None or not app._stack or app._stack[-1] is not self:
            raise RuntimeError("Mismatched UI context: element stack out of sync")
        app._stack.pop()
        return None

    def add(self, *children: Child) -> "Element":
        self.children.extend(children)
        return self

    def _render_attrs(self) -> str:
        parts: list[str] = []
        for k, v in self.attrs.items():
            key = _attr_key(k)
            if isinstance(v, bool):
                if v:
                    parts.append(key)
                continue
            parts.append(f'{key}="{_attr_value(v)}"')
        return (" " + " ".join(parts)) if parts else ""

    def _render_children(self) -> str:
        out: list[str] = []
        for ch in self.children:
            if isinstance(ch, Element):
                out.append(ch.render())
            else:
                out.append(_escape_html(ch))
        return "".join(out)

    def render(self) -> str:
        voids = {
            "area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr",
        }
        attrs = self._render_attrs()
        if self.tag in voids:
            return f"<{self.tag}{attrs}>"
        return f"<{self.tag}{attrs}>{self._render_children()}</{self.tag}>"

    def __str__(self) -> str:
        return self.render()

# --------------------------------------------------------------------------------------
# HTML5 vocabulary (unabbreviated class names)
# --------------------------------------------------------------------------------------

# Tables (unabbreviated)
class Table(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("table", children, **kw)

class TableCaption(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("caption", children, **kw)

class TableColumnGroup(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("colgroup", children, **kw)

class TableColumn(Element):
    def __init__(self, **kw: Any):
        super().__init__("col", None, **kw)

class TableHead(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("thead", children, **kw)

class TableBody(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("tbody", children, **kw)

class TableFoot(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("tfoot", children, **kw)

class TableRow(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("tr", children, **kw)

class TableHeaderCell(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("th", children, **kw)

class TableDataCell(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("td", children, **kw)

# Basic flow/phrasing
class Division(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("div", children, **kw)

class Paragraph(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        if isinstance(children, str):
            children = [children]
        super().__init__("p", children, **kw)

class Span(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("span", children, **kw)

class Anchor(Element):
    def __init__(self, text_: str, href: str, **kw: Any):
        kw.setdefault("href", href)
        super().__init__("a", [text_], **kw)

class Image(Element):
    def __init__(self, **kw: Any):
        super().__init__("img", None, **kw)

class Emphasis(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("em", children, **kw)

class Strong(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("strong", children, **kw)

class Small(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("small", children, **kw)

class Mark(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("mark", children, **kw)

class Code(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("code", children, **kw)

class Preformatted(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("pre", children, **kw)

class Blockquote(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("blockquote", children, **kw)

class Citation(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("cite", children, **kw)

class Time(Element):
    def __init__(
        self,
        datetime: Optional[str] = None,
        children: Optional[Iterable[Child]] = None,
        **kw: Any,
    ):
        if datetime is not None:
            kw.setdefault("datetime", datetime)
        super().__init__("time", children, **kw)

class Data(Element):
    def __init__(
        self, value: str, children: Optional[Iterable[Child]] = None, **kw: Any
    ):
        kw.setdefault("value", value)
        super().__init__("data", children, **kw)

class Variable(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("var", children, **kw)

class KeyboardInput(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("kbd", children, **kw)

class SampleOutput(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("samp", children, **kw)

class Subscript(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("sub", children, **kw)

class Superscript(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("sup", children, **kw)

# Headings (distinct from <header>)
class Heading(Element):
    def __init__(
        self,
        text: str,
        size: int = 1,
        *,
        cls: Union[str, Sequence[str], None] = None,
        **attrs: Any,
    ):
        if not (1 <= size <= 6):
            raise ValueError("Heading size must be 1..6")
        super().__init__(f"h{size}", [text], cls=cls, **attrs)

# Sections / landmarks
class Section(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("section", children, **kw)

class Article(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("article", children, **kw)

class Navigation(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("nav", children, **kw)

class Header(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("header", children, **kw)

class Footer(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("footer", children, **kw)

class Main(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("main", children, **kw)

class Aside(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("aside", children, **kw)

class Figure(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("figure", children, **kw)

class FigureCaption(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("figcaption", children, **kw)

# Lists
class List(Element):
    def __init__(
        self, unordered: bool = True, items: Iterable[Child] | None = None, **kw: Any
    ):
        tag = "ul" if unordered else "ol"
        children: list[Child] = []
        if items:
            for it in items:
                children.append(ListItem([it]) if not isinstance(it, Element) else it)
        super().__init__(tag, children, **kw)

class ListItem(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        if isinstance(children, str):
            children = [children]
        super().__init__("li", children, **kw)

class DescriptionList(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("dl", children, **kw)

class DescriptionTerm(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("dt", children, **kw)

class DescriptionDetails(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("dd", children, **kw)

# Forms
class Form(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("form", children, **kw)

class Label(Element):
    def __init__(
        self,
        for_id: Optional[str] = None,
        children: Optional[Iterable[Child]] = None,
        **kw: Any,
    ):
        if for_id is not None:
            kw.setdefault("for", for_id)
        super().__init__("label", children, **kw)

class Input(Element):
    def __init__(self, **kw: Any):
        super().__init__("input", None, **kw)

class Textarea(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("textarea", children, **kw)

class Select(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("select", children, **kw)

class OptGroup(Element):
    def __init__(self, label: str, children: Optional[Iterable[Child]] = None, **kw: Any):
        kw.setdefault("label", label)
        super().__init__("optgroup", children, **kw)

class Option(Element):
    def __init__(self, text_: str, value: Optional[str] = None, **kw: Any):
        if value is not None:
            kw.setdefault("value", value)
        super().__init__("option", [text_], **kw)

class Fieldset(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("fieldset", children, **kw)

class Legend(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("legend", children, **kw)

class Datalist(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("datalist", children, **kw)

class Output(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("output", children, **kw)

class Button(Element):
    def __init__(self, label: str, **kw: Any):
        super().__init__("button", [label], **kw)

class Meter(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("meter", children, **kw)

class Progress(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("progress", children, **kw)

# Media
class Audio(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("audio", children, **kw)

class Video(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("video", children, **kw)

class Source(Element):
    def __init__(self, **kw: Any):
        super().__init__("source", None, **kw)

class Track(Element):
    def __init__(self, **kw: Any):
        super().__init__("track", None, **kw)

class Picture(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("picture", children, **kw)

# Embeds / graphics
class InlineFrame(Element):  # <iframe>
    def __init__(self, **kw: Any):
        super().__init__("iframe", None, **kw)

class Canvas(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("canvas", children, **kw)

class Embed(Element):
    def __init__(self, **kw: Any):
        super().__init__("embed", None, **kw)

class ObjectEmbed(Element):  # <object>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("object", children, **kw)

class Param(Element):
    def __init__(self, **kw: Any):
        super().__init__("param", None, **kw)

class ImageMap(Element):  # <map>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("map", children, **kw)

class Area(Element):
    def __init__(self, **kw: Any):
        super().__init__("area", None, **kw)

# Scripting / templates
class Script(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        # For inline script: pass JS string in children
        super().__init__("script", children, **kw)

class Noscript(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("noscript", children, **kw)

class Template(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("template", children, **kw)

class Slot(Element):
    def __init__(self, name: Optional[str] = None, children: Optional[Iterable[Child]] = None, **kw: Any):
        if name is not None:
            kw.setdefault("name", name)
        super().__init__("slot", children, **kw)

# Inline phrasing extras
class InlineQuote(Element):  # <q>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("q", children, **kw)

class Bold(Element):  # <b>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("b", children, **kw)

class Italic(Element):  # <i>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("i", children, **kw)

class Underline(Element):  # <u>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("u", children, **kw)

class Strikethrough(Element):  # <s>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("s", children, **kw)

class Definition(Element):  # <dfn>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("dfn", children, **kw)

class LineBreak(Element):  # <br>
    def __init__(self, **kw: Any):
        super().__init__("br", None, **kw)

class HorizontalRule(Element):  # <hr>
    def __init__(self, **kw: Any):
        super().__init__("hr", None, **kw)

class Insertion(Element):  # <ins>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("ins", children, **kw)

class Deletion(Element):  # <del>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("del", children, **kw)

# Ruby + misc
class Address(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("address", children, **kw)

class Abbreviation(Element):
    def __init__(
        self,
        title: Optional[str] = None,
        children: Optional[Iterable[Child]] = None,
        **kw: Any,
    ):
        if title is not None:
            kw.setdefault("title", title)
        super().__init__("abbr", children, **kw)

class BidirectionalIsolate(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("bdi", children, **kw)

class BidirectionalOverride(Element):
    def __init__(
        self, dir_: Optional[str] = None, children: Optional[Iterable[Child]] = None, **kw: Any
    ):
        if dir_ is not None:
            kw.setdefault("dir", dir_)
        super().__init__("bdo", children, **kw)

class Ruby(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("ruby", children, **kw)

class RubyBase(Element):  # <rb>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("rb", children, **kw)

class RubyText(Element):  # <rt>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("rt", children, **kw)

class RubyParenthesis(Element):  # <rp>
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("rp", children, **kw)

class WordBreakOpportunity(Element):  # <wbr>
    def __init__(self, **kw: Any):
        super().__init__("wbr", None, **kw)

# Document metadata (optional, if you ever want to emit full documents)
class Html(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("html", children, **kw)

class Head(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("head", children, **kw)

class Body(Element):
    def __init__(self, children: Optional[Iterable[Child]] = None, **kw: Any):
        super().__init__("body", children, **kw)

class Title(Element):
    def __init__(self, text_: str, **kw: Any):
        super().__init__("title", [text_], **kw)

class Base(Element):
    def __init__(self, **kw: Any):
        super().__init__("base", None, **kw)

class Link(Element):
    def __init__(self, **kw: Any):
        super().__init__("link", None, **kw)

class Meta(Element):
    def __init__(self, **kw: Any):
        super().__init__("meta", None, **kw)

class StyleTag(Element):  # inline <style>
    def __init__(self, css_text: str, **kw: Any):
        super().__init__("style", [css_text], **kw)

# --------------------------------------------------------------------------------------
# App + helpers
# --------------------------------------------------------------------------------------

@dataclass
class App:
    stylesheet: Optional[StyleSheet] = None
    _root_children: list[Element] = field(default_factory=list)
    _stack: list[Element] = field(default_factory=list)
    _token: Any = field(default=None, init=False, repr=False)

    def __enter__(self) -> "App":
        self._token = _CURRENT_APP.set(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _CURRENT_APP.reset(self._token)
        self._token = None
        self._stack.clear()
        return None

    @staticmethod
    def current() -> "App | None":
        return _CURRENT_APP.get()

    def text(self, value: str) -> None:
        if not self._stack:
            raise RuntimeError("No active element context for text().")
        self._stack[-1].children.append(value)

    def html(self) -> str:
        css = self.stylesheet.to_style_tag() if self.stylesheet else ""
        body = "".join(child.render() for child in self._root_children)
        return f"{css}\n{body}"

# module-level sugar

def text(value: str) -> None:
    app = App.current()
    if app is None:
        raise RuntimeError("text() must be called inside an App context")
    app.text(value)

def mount(app: App, root_selector: str = "body") -> None:
    html = app.html()
    try:
        from pyscript import document  # type: ignore
        el = document.querySelector(root_selector)
        if el is None:
            raise RuntimeError(f"No element found for selector '{root_selector}'")
        el.innerHTML = html
    except Exception:
        print(html)
