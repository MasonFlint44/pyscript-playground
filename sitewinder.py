"""
sitewinder.py — Angular-like component framework for PyScript + pyhtml5

Features:
- Component base class with template(), optional styles, and lifecycle hooks.
- Signals (reactive state), automatic change detection (per component).
- Event binding helpers and basic two-way binding for form elements.
- Child component mounting via portal().
- Hash router and simple bootstrap().
- Optional per-instance style scoping (opt-in).

Requires: pyhtml5.py in the same directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import itertools

# --------- PyScript / JS interop --------------------------------------------------

HAS_JS = False
_document = None
_window = None
_console = None
_create_proxy = None

try:
    from js import document as _document, window as _window, console as _console  # type: ignore

    # pyodide proxy helper: try modern API, fall back to legacy
    try:
        from pyodide.ffi import create_proxy as _create_proxy  # type: ignore
    except Exception:
        import pyodide  # type: ignore

        _create_proxy = pyodide.create_proxy  # type: ignore
    HAS_JS = True
except Exception:
    HAS_JS = False


def _schedule_microtask(fn: Callable[[], None]) -> None:
    """Run `fn` soon (batch multiple state changes)."""
    if HAS_JS:
        _window.setTimeout(_create_proxy(lambda *_: fn()), 0)
    else:
        fn()


def _is_dom_node(obj) -> bool:
    """
    True if obj is a real DOM node/element (not JsNull/undefined/None).
    Works with Pyodide JsProxy wrappers.
    """
    if obj is None:
        return False
    try:
        return hasattr(obj, "addEventListener") or hasattr(obj, "nodeType")
    except Exception:
        return False


# --------- pyhtml5 integration ----------------------------------------------------

from pyhtml5 import (
    Node,
    Element,
    Fragment,
    Stylesheet,
    Division,  # used for portals / host wrappers
)

# --------- Reactive core ----------------------------------------------------------

_current_collector_stack: List["DependencyCollector"] = []


class DependencyCollector:
    def __init__(self):
        self.signals: Set["Signal[Any]"] = set()

    def __enter__(self):
        _current_collector_stack.append(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _current_collector_stack.pop()
        return False


def _register_signal_read(sig: "Signal[Any]"):
    if _current_collector_stack:
        _current_collector_stack[-1].signals.add(sig)


class Signal:
    """A simple observable value with dependency tracking."""

    __slots__ = ("_value", "_subs", "_name")

    def __init__(self, value: Any, name: Optional[str] = None):
        self._value = value
        self._subs: Set[Callable[[Any, Any], None]] = set()
        self._name = name

    def __call__(self) -> Any:
        return self.get()

    @property
    def value(self) -> Any:
        return self.get()

    @value.setter
    def value(self, v: Any) -> None:
        self.set(v)

    def get(self) -> Any:
        _register_signal_read(self)
        return self._value

    def set(self, v: Any) -> None:
        old = self._value
        if old is v or old == v:
            return
        self._value = v
        for cb in list(self._subs):
            try:
                cb(old, v)
            except Exception as e:
                if HAS_JS:
                    _console.error(f"Signal subscriber error: {e}")

    def subscribe(self, cb: Callable[[Any, Any], None]) -> Callable[[], None]:
        self._subs.add(cb)

        def _unsub():
            self._subs.discard(cb)

        return _unsub


class EventEmitter:
    """Minimal event emitter for component outputs."""

    def __init__(self):
        self._subs: Set[Callable[..., None]] = set()

    def subscribe(self, cb: Callable[..., None]) -> Callable[[], None]:
        self._subs.add(cb)

        def _un():
            self._subs.discard(cb)

        return _un

    def emit(self, *args, **kwargs):
        for cb in list(self._subs):
            cb(*args, **kwargs)


# --------- Component base ---------------------------------------------------------

_portal_id_iter = (f"swp-{i}" for i in itertools.count(1))
_event_id_iter = (f"swe-{i}" for i in itertools.count(1))
_comp_instance_iter = (i for i in itertools.count(1))


@dataclass
class _EventBinding:
    elem_id: str
    event: str
    handler: Callable[..., None]
    proxy: Any = None  # JS proxy
    attached_to: Any = None  # JS element


@dataclass
class _ValueBinding:
    elem_id: str
    signal: Signal
    prop: str = "value"
    event: str = "input"
    proxy: Any = None
    attached_to: Any = None


class Component:
    """
    Base class for SiteWinder components.

    Subclass and implement:
      - template(self) -> Node  (Element/Fragment built with pyhtml5)
      - optionally styles(self) -> Stylesheet | str | None

    Lifecycle hooks:
      - on_init(self)
      - on_mount(self)
      - on_update(self)
      - on_destroy(self)

    Helpers inside template():
      - self.on(element, 'click', handler)
      - self.bind_value(input_element, signal, event='input'|'change', prop='value'|'checked')
      - self.portal(ChildComponentClass, **props)
    """

    selector: Optional[str] = None

    def __init__(self, **props):
        self.props = props
        self._instance_id = next(_comp_instance_iter)
        self._scoped_attr = f'data-sw-cid="{self._instance_id}"'
        self._host_js = None
        self._root_js = None
        self._mounted = False
        self._destroyed = False

        self._event_bindings: List[_EventBinding] = []
        self._value_bindings: List[_ValueBinding] = []
        self._portal_children: List[Tuple[str, type, Dict[str, Any]]] = []

        self._signal_unsubs: List[Callable[[], None]] = []
        self._pending_render = False

        self._style_el = None
        self._use_scoped_styles = True

        # Stable id registry for objects (e.g., Signals) across renders
        self._stable_ids: Dict[int, str] = {}
        self._stable_ids_counter: int = 0

        self.on_init()

    # ----- override points --------------------------------------------------------
    def template(self) -> Node:
        raise NotImplementedError

    def styles(self) -> Optional[Union[Stylesheet, str]]:
        return None

    # ----- lifecycle --------------------------------------------------------------
    def on_init(self):
        pass

    def on_mount(self):
        pass

    def on_update(self):
        pass

    def on_destroy(self):
        pass

    # ----- public API -------------------------------------------------------------
    def mount(self, host: Union[str, Any]):
        if not HAS_JS:
            raise RuntimeError("Component.mount() requires a browser environment.")
        if isinstance(host, str):
            el = _document.querySelector(host)
            if not _is_dom_node(el):
                raise ValueError(f"SiteWinder: mount host not found: {host}")
            self._host_js = el
        else:
            if not _is_dom_node(host):
                raise ValueError(
                    "SiteWinder: mount host must be a DOM element or selector."
                )
            self._host_js = host

        self._render_and_mount(first_mount=True)
        return self

    def destroy(self):
        if self._destroyed:
            return
        self._cleanup_bindings()
        self._unsubscribe_signals()
        if self._root_js and self._host_js:
            try:
                self._host_js.removeChild(self._root_js)
            except Exception:
                pass
        if self._style_el and self._style_el.parentNode:
            try:
                self._style_el.parentNode.removeChild(self._style_el)
            except Exception:
                pass
        self._destroyed = True
        try:
            self.on_destroy()
        except Exception as e:
            if HAS_JS:
                _console.error(f"on_destroy error: {e}")

    # ----- event + value bindings -------------------------------------------------
    def on(self, element: Element, event: str, handler: Callable[..., None]) -> Element:
        elem_id = self._ensure_elem_marker(element)
        self._event_bindings.append(_EventBinding(elem_id, event, handler))
        return element

    def bind_value(
        self,
        element: Element,
        signal: Signal,
        *,
        event: str = "input",
        prop: str = "value",
    ) -> Element:
        # Use a STABLE id based on the Signal object so we can restore focus after re-renders
        stable_id = self._stable_id_for(signal, prefix="sv")
        elem_id = self._ensure_elem_marker(element, preferred_id=stable_id)
        self._value_bindings.append(
            _ValueBinding(elem_id, signal, prop=prop, event=event)
        )
        try:
            if prop == "checked":
                element.set_attr(checked=bool(signal.get()))
            else:
                element.set_attr(value=str(signal.get()))
        except Exception:
            pass
        return element

    # ----- child components (portals) --------------------------------------------
    def portal(self, child_component_cls: type, **child_props) -> Element:
        portal_id = next(_portal_id_iter)
        placeholder = Division()
        placeholder.set_attr(**{"data-sw-portal": portal_id})
        self._portal_children.append((portal_id, child_component_cls, child_props))
        return placeholder

    def use(self, child_component_cls: type, **props) -> Element:
        return self.portal(child_component_cls, **props)

    # ----- stable id helpers ------------------------------------------------------
    def _stable_id_for(self, obj: Any, *, prefix: str = "k") -> str:
        key = id(obj)
        sid = self._stable_ids.get(key)
        if sid is not None:
            return sid
        self._stable_ids_counter += 1
        sid = f"{prefix}-{self._stable_ids_counter}"
        self._stable_ids[key] = sid
        return sid

    # ----- focus capture/restore --------------------------------------------------
    def _is_within_root(self, el) -> bool:
        try:
            return (
                _is_dom_node(el)
                and _is_dom_node(self._root_js)
                and self._root_js.contains(el)
            )
        except Exception:
            return False

    def _capture_focus_state(self) -> Optional[Dict[str, Any]]:
        """
        Capture active element id and selection (for text controls) so we can restore after re-render.
        Only works for elements that carry a data-sw-id (from on()/bind_value()).
        """
        if not HAS_JS or not _is_dom_node(self._root_js):
            return None
        try:
            active = _document.activeElement
        except Exception:
            return None
        if not self._is_within_root(active):
            return None

        try:
            elem_id = active.getAttribute("data-sw-id")
        except Exception:
            elem_id = None
        if not elem_id:
            return None

        sel_start = sel_end = None
        sel_dir = None
        try:
            sel_start = getattr(active, "selectionStart", None)
            sel_end = getattr(active, "selectionEnd", None)
            sel_dir = getattr(active, "selectionDirection", None)
        except Exception:
            pass

        return {
            "elem_id": elem_id,
            "sel_start": sel_start,
            "sel_end": sel_end,
            "sel_dir": sel_dir,
        }

    def _restore_focus_state(self, state: Optional[Dict[str, Any]]) -> None:
        if not state or not HAS_JS or not _is_dom_node(self._root_js):
            return
        elem_id = state.get("elem_id")
        if not elem_id:
            return
        try:
            el = self._root_js.querySelector(f'[data-sw-id="{elem_id}"]')
        except Exception:
            el = None
        if not _is_dom_node(el):
            return
        try:
            el.focus()
        except Exception:
            pass

        sel_start = state.get("sel_start")
        sel_end = state.get("sel_end")
        sel_dir = state.get("sel_dir") or "none"
        if sel_start is not None and sel_end is not None:
            try:
                if hasattr(el, "setSelectionRange"):
                    el.setSelectionRange(sel_start, sel_end, sel_dir)
                else:
                    setattr(el, "selectionStart", sel_start)
                    setattr(el, "selectionEnd", sel_end)
            except Exception:
                pass

    # ----- internal: rendering + binding -----------------------------------------
    def _ensure_elem_marker(
        self, element: Element, preferred_id: Optional[str] = None
    ) -> str:
        data_attr = element.attrs.get("data-sw-id")
        if data_attr:
            return data_attr
        new_id = preferred_id or next(_event_id_iter)
        element.set_attr(**{"data-sw-id": new_id})
        return new_id

    def _scope_css(self, css_text: str, scope_selector: str) -> str:
        scoped_lines: List[str] = []
        for line in css_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("@"):
                scoped_lines.append(line)
                continue
            if "{" in line:
                before, after = line.split("{", 1)
                selectors = [s.strip() for s in before.split(",")]
                prefixed = ", ".join(f"{scope_selector} {s}" for s in selectors if s)
                scoped_lines.append(f"{prefixed} {{{after}")
            else:
                scoped_lines.append(line)
        return "\n".join(scoped_lines)

    def _mount_styles_if_any(self, first_mount: bool):
        styles = self.styles()
        if not styles:
            return
        if isinstance(styles, Stylesheet):
            css_text = styles.to_css()
        else:
            css_text = str(styles)
        if self._use_scoped_styles:
            scope_selector = f'[data-sw-cid="{self._instance_id}"]'
            css_text = self._scope_css(css_text, scope_selector)

        if HAS_JS:
            if self._style_el is None:
                self._style_el = _document.createElement("style")
                self._style_el.setAttribute("type", "text/css")
                _document.head.appendChild(self._style_el)
            self._style_el.textContent = css_text

    def _render_and_mount(self, first_mount: bool = False):
        if not _is_dom_node(self._host_js):
            raise RuntimeError(
                "No host element resolved; call mount(selector_or_element) first."
            )

        # CLEANUP & RESET PER-RENDER
        self._cleanup_bindings()
        self._event_bindings.clear()
        self._value_bindings.clear()
        self._portal_children.clear()

        for unsub in self._signal_unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._signal_unsubs.clear()

        # CAPTURE FOCUS BEFORE WE NUKE THE DOM
        focus_state = self._capture_focus_state()

        # BUILD TEMPLATE & COLLECT SIGNALS
        with DependencyCollector() as dep:
            try:
                node = self.template()
                if not isinstance(node, Node):
                    node = Fragment(str(node))
            except Exception as e:
                if HAS_JS:
                    _console.error(f"template() error: {e}")
                node = Fragment(f"SiteWinder template error: {e}")

        def _on_sig_change(old, new):
            self._schedule_rerender()

        for sig in dep.signals:
            self._signal_unsubs.append(sig.subscribe(_on_sig_change))

        # CREATE ROOT CONTAINER (FIRST MOUNT)
        container_attr_name = "data-sw-root"
        container_attr_val = f"root-{self._instance_id}"
        if first_mount:
            self._host_js.innerHTML = ""
            root = _document.createElement("div")
            root.setAttribute(container_attr_name, container_attr_val)
            root.setAttribute(
                "data-sw-cid", str(self._instance_id)
            )  # for style scoping
            self._host_js.appendChild(root)
            self._root_js = root

        # (RE)MOUNT STYLES
        self._mount_styles_if_any(first_mount)

        # (RE)RENDER DOM
        if _is_dom_node(self._root_js):
            self._root_js.innerHTML = ""
            node.to_dom(self._root_js)

        # BINDINGS
        self._apply_event_bindings()
        self._apply_value_bindings()
        self._mount_portal_children()

        # RESTORE FOCUS AFTER DOM & BINDINGS
        self._restore_focus_state(focus_state)

        # LIFECYCLE
        if not self._mounted:
            self._mounted = True
            try:
                self.on_mount()
            except Exception as e:
                if HAS_JS:
                    _console.error(f"on_mount error: {e}")
        else:
            try:
                self.on_update()
            except Exception as e:
                if HAS_JS:
                    _console.error(f"on_update error: {e}")

    def _schedule_rerender(self):
        if self._pending_render or self._destroyed:
            return
        self._pending_render = True

        def run():
            self._pending_render = False
            self._render_and_mount(first_mount=False)

        _schedule_microtask(run)

    def _apply_event_bindings(self):
        for eb in self._event_bindings:
            if eb.attached_to and eb.proxy:
                try:
                    eb.attached_to.removeEventListener(eb.event, eb.proxy)
                except Exception:
                    pass
            eb.attached_to = None
            eb.proxy = None

        for eb in self._event_bindings:
            el = self._root_js.querySelector(f'[data-sw-id="{eb.elem_id}"]')
            if not _is_dom_node(el):
                continue
            proxy = _create_proxy(lambda ev, _h=eb.handler: _h(ev))
            el.addEventListener(eb.event, proxy)
            eb.attached_to = el
            eb.proxy = proxy

    def _apply_value_bindings(self):
        for vb in self._value_bindings:
            if vb.attached_to and vb.proxy:
                try:
                    vb.attached_to.removeEventListener(vb.event, vb.proxy)
                except Exception:
                    pass
            vb.attached_to = None
            vb.proxy = None

        for vb in self._value_bindings:
            el = self._root_js.querySelector(f'[data-sw-id="{vb.elem_id}"]')
            if not _is_dom_node(el):
                continue

            # Only set if different to avoid caret jumps during typing
            try:
                current = getattr(el, vb.prop)
                new_val = vb.signal.get()
                if current != new_val:
                    setattr(el, vb.prop, new_val)
            except Exception:
                pass

            def _handler(ev, _vb=vb):
                try:
                    val = getattr(ev.target, _vb.prop)
                except Exception:
                    val = None
                _vb.signal.set(val)

            proxy = _create_proxy(_handler)
            el.addEventListener(vb.event, proxy)

            def _update_dom(_old, _new, _el=el, _vb=vb):
                if _is_dom_node(_el):
                    try:
                        if getattr(_el, _vb.prop) != _new:
                            setattr(_el, _vb.prop, _new)
                    except Exception:
                        pass

            unsub = vb.signal.subscribe(_update_dom)

            vb.attached_to = el
            vb.proxy = proxy
            self._signal_unsubs.append(unsub)

    def _mount_portal_children(self):
        for portal_id, cls, props in self._portal_children:
            slot = self._root_js.querySelector(f'[data-sw-portal="{portal_id}"]')
            if not _is_dom_node(slot):
                continue
            try:
                child = cls(**props)
                child.mount(slot)
            except Exception as e:
                if HAS_JS:
                    _console.error(f"Child component mount error: {e}")
                try:
                    slot.textContent = f"[SiteWinder] failed to mount child: {e}"
                except Exception:
                    pass

    def _cleanup_bindings(self):
        for eb in self._event_bindings:
            if eb.attached_to and eb.proxy:
                try:
                    eb.attached_to.removeEventListener(eb.event, eb.proxy)
                except Exception:
                    pass
            eb.attached_to = None
            eb.proxy = None

        for vb in self._value_bindings:
            if vb.attached_to and vb.proxy:
                try:
                    vb.attached_to.removeEventListener(vb.event, vb.proxy)
                except Exception:
                    pass
            vb.attached_to = None
            vb.proxy = None

    def _unsubscribe_signals(self):
        for unsub in self._signal_unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._signal_unsubs.clear()


# --------- Router -----------------------------------------------------------------


class Router:
    """
    Very small hash-based router.
    Usage:
        router = Router("#outlet", {
            "#/": lambda: HomeComponent(),
            "#/counter": lambda: CounterComponent(),
        })
        router.start()
    """

    def __init__(
        self,
        outlet: Union[str, Any],
        routes: Dict[str, Callable[[], Component]],
        *,
        not_found: Optional[Callable[[], Component]] = None,
    ):
        self.outlet = outlet
        self.routes = routes
        self.not_found_factory = not_found
        self._current: Optional[Component] = None
        self._hash_proxy = None

    def start(self):
        if not HAS_JS:
            raise RuntimeError("Router requires a browser environment.")
        self._hash_proxy = _create_proxy(lambda *_: self._on_hash_change())
        _window.addEventListener("hashchange", self._hash_proxy)
        self._on_hash_change()

    def stop(self):
        if not HAS_JS:
            return
        if self._hash_proxy:
            _window.removeEventListener("hashchange", self._hash_proxy)
            self._hash_proxy = None

    def _on_hash_change(self):
        h = str(_window.location.hash or "#/")
        factory = self.routes.get(h)
        if factory is None and self.not_found_factory is not None:
            factory = self.not_found_factory
        if factory is None:
            if h.endswith("/") and (h[:-1] in self.routes):
                factory = self.routes[h[:-1]]
        if factory is None and "#/" in self.routes:
            factory = self.routes["#/"]

        if factory is None:
            if self._current:
                self._current.destroy()
                self._current = None
            return

        if self._current:
            self._current.destroy()
            self._current = None

        comp = factory()
        comp.mount(self.outlet)
        self._current = comp


# --------- Bootstrap ---------------------------------------------------------------


def bootstrap(root_component_cls: type[Component], host: Union[str, Any], **props):
    """
    Construct and mount a root component into host (selector or element).
    """
    app = root_component_cls(**props)
    app.mount(host)
    return app
