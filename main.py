from sitewinder import Component, Signal, Router, bootstrap
from pyhtml5 import (
    Division,
    Header,
    Navigation,
    Section,
    Article,
    Paragraph,
    Heading1,
    Heading2,
    Button,
    Input,
    Label,
    UnorderedList,
    ListItem,
    HorizontalRule,
    Stylesheet,
    Select,
    Option,
    Span,
    Anchor,
)

# ------------------------ Reusable Components ------------------------------------


class Card(Component):
    """Reusable card with title + body content (callable)."""

    def styles(self):
        css = Stylesheet()
        with css:
            # Light defaults
            css.rule(
                ".card",
                padding="16px",
                border="1px solid #e5e7eb",
                border_radius="14px",
                background="#ffffff",
                box_shadow="0 1px 2px rgba(0,0,0,.06)",
                color="#0f172a",
            )
            css.rule(".title", font_weight="600", margin_bottom="8px", color="#0b1220")
            # Dark overrides
            css.rule(
                "html[data-theme='dark'] .card",
                background="#111827",
                border="1px solid #334155",
                color="#e5e7eb",
            )
            css.rule("html[data-theme='dark'] .card .title", color="#f3f4f6")
        return css

    def template(self):
        title = self.props.get("title", "")
        body = self.props.get("body")
        root = Division().classes("card")
        with root:
            if title:
                Span(title).classes("title")
            if callable(body):
                body()  # context manager appends
        return root


# ----------------------------- Pages ---------------------------------------------


class Home(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(".home", padding="24px")
            css.rule(
                ".hero",
                display="grid",
                gap="16px",
                grid_template_columns="repeat(3, minmax(0, 1fr))",
            )
            css.rule(".lead", color="#334155")
            with css.media("(max-width: 900px)"):
                css.rule(".hero", grid_template_columns="1fr")
            css.rule("html[data-theme='dark'] .home .lead", color="#94a3b8")
        return css

    def template(self):
        root = Division().classes("home")
        with root:
            Heading1("SiteWinder")
            Paragraph(
                "Angular-like components in pure Python with PyScript + pyhtml5."
            ).classes("lead")
            HorizontalRule().style(margin="12px 0")
            with Section().classes("hero"):
                self.portal(
                    Card,
                    title="🔢 Counters",
                    body=lambda: Paragraph(
                        "Visit “#/counter” for signals, events, and computed totals."
                    ),
                )
                self.portal(
                    Card,
                    title="📝 Forms & Binding",
                    body=lambda: Paragraph(
                        "See text/checkbox/select bindings on “#/form”."
                    ),
                )
                self.portal(
                    Card,
                    title="✅ Todos & Modal",
                    body=lambda: Paragraph(
                        "Inline editing with stable focus and a modal on “#/todos”."
                    ),
                )
        return root


class Counter(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(".wrap", padding="24px")
            css.rule(".row", display="flex", gap="8px", align_items="center")
            # Inputs & buttons (light)
            css.rule(
                ".btn",
                width="38px",
                height="38px",
                border_radius="12px",
                border="1px solid #e5e7eb",
                background="#ffffff",
                cursor="pointer",
                font_size="18px",
                line_height="36px",
                text_align="center",
                color="#0f172a",
            )
            css.rule(
                "input[type=number]",
                border="1px solid #e5e7eb",
                background="#ffffff",
                color="#0f172a",
                border_radius="10px",
                padding="8px 10px",
                width="82px",
            )
            css.rule(
                ".pill",
                display="inline-block",
                padding="4px 10px",
                border_radius="999px",
                background="#7c3aed",
                color="white",
                font_size="12px",
            )
            # Dark overrides
            css.rule(
                "html[data-theme='dark'] .btn",
                border="1px solid #334155",
                background="#0b1220",
                color="#e5e7eb",
            )
            css.rule(
                "html[data-theme='dark'] input[type=number]",
                border="1px solid #334155",
                background="#0b1220",
                color="#e5e7eb",
            )
        return css

    def on_init(self):
        self.count_a = Signal(0)
        self.count_b = Signal(10)
        self.step = Signal(1)

    def _controls(self, label: str, sig: Signal):
        row = Division().classes("row")
        with row:
            Paragraph(label)
            dec = Button("−").classes("btn")
            self.on(dec, "click", lambda e, s=sig: s.set(s() - self.step()))
            inc = Button("+").classes("btn")
            self.on(inc, "click", lambda e, s=sig: s.set(s() + self.step()))
        return row

    def template(self):
        total = self.count_a() + self.count_b()
        root = Division().classes("wrap")
        with root:
            Heading1("🔢 Counter Playground")
            Paragraph("Signals, events, two counters, and a computed total.")
            with Division().classes("row"):
                Paragraph("Step:")
                step_in = Input(type="number", min="1", value=str(self.step()))
                self.bind_value(
                    step_in, self.step, event="input", prop="value"
                )  # coerces to int
            HorizontalRule().style(margin="12px 0")
            self._controls("Counter A:", self.count_a)
            self._controls("Counter B:", self.count_b)
            HorizontalRule().style(margin="12px 0")
            p = Paragraph()
            with p:
                Span("Total: ").classes("pill")
                Span(str(total))
        return root


class FormDemo(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(
                ".wrap", padding="24px", display="grid", gap="14px", max_width="560px"
            )
            css.rule(".row", display="grid", gap="6px")
            # Light
            css.rule(
                "input, select",
                border="1px solid #e5e7eb",
                background="#ffffff",
                color="#0f172a",
                padding="10px",
                border_radius="10px",
                font_size="14px",
            )
            css.rule(
                ".preview",
                padding="12px",
                background="#f1f5f9",
                border_radius="12px",
                border="1px dashed #94a3b8",
                color="#0f172a",
            )
            # Dark
            css.rule(
                "html[data-theme='dark'] input, html[data-theme='dark'] select",
                border="1px solid #334155",
                background="#0b1220",
                color="#e5e7eb",
            )
            css.rule(
                "html[data-theme='dark'] .preview",
                background="#111827",
                border="1px dashed #334155",
                color="#e5e7eb",
            )
        return css

    def on_init(self):
        self.name = Signal("Ada Lovelace")
        self.is_admin = Signal(False)
        self.color = Signal("violet")

    def template(self):
        root = Division().classes("wrap")
        with root:
            Heading1("📝 Form Binding")
            with Division().classes("row"):
                Label("Name")
                name_inp = Input(type="text", placeholder="Your name")
                self.bind_value(name_inp, self.name, event="input", prop="value")
            with Division().classes("row"):
                Label("Admin?")
                admin_inp = Input(type="checkbox")
                self.bind_value(
                    admin_inp, self.is_admin, event="change", prop="checked"
                )
            with Division().classes("row"):
                Label("Favorite color")
                sel = Select()
                with sel:
                    for c in ["slate", "violet", "rose", "emerald", "amber"]:
                        Option(c, value=c)
                self.bind_value(sel, self.color, event="change", prop="value")

            HorizontalRule().style(margin="8px 0")
            with Division().classes("preview"):
                Paragraph(f"Hello, {self.name()}! 👋")
                Paragraph(f"Admin: {'✅' if self.is_admin() else '❌'}")
                Paragraph(f"Favorite color: 🎨 {self.color()}")
        return root


class Todos(Component):
    """Todos list where structure mutations cause re-renders (list wrapped in a Signal)."""

    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(
                ".wrap", padding="24px", display="grid", gap="12px", max_width="720px"
            )
            # Light
            css.rule(
                ".todo",
                display="grid",
                grid_template_columns="auto 1fr auto",
                gap="8px",
                align_items="center",
                padding="8px",
                border="1px solid #e5e7eb",
                border_radius="10px",
                background="#ffffff",
                color="#0f172a",
            )
            css.rule(".controls", display="flex", gap="8px")
            css.rule(
                ".btn",
                border="1px solid #e5e7eb",
                border_radius="10px",
                padding="6px 10px",
                background="#ffffff",
                cursor="pointer",
                color="#0f172a",
            )
            css.rule(".empty", color="#6b7280")
            css.rule(
                "input[type=text]",
                border="1px solid #e5e7eb",
                background="#ffffff",
                color="#0f172a",
                border_radius="10px",
                padding="8px 10px",
            )
            # Dark overrides
            css.rule(
                "html[data-theme='dark'] .todo",
                border="1px solid #334155",
                background="#111827",
                color="#e5e7eb",
            )
            css.rule(
                "html[data-theme='dark'] .btn",
                border="1px solid #334155",
                background="#0b1220",
                color="#e5e7eb",
            )
            css.rule("html[data-theme='dark'] .empty", color="#94a3b8")
            css.rule(
                "html[data-theme='dark'] input[type=text]",
                border="1px solid #334155",
                background="#0b1220",
                color="#e5e7eb",
            )
        return css

    def on_init(self):
        def make_todo(text: str) -> dict:
            return {"text": Signal(text), "done": Signal(False)}

        self.todos = Signal(
            [make_todo("Learn PyScript"), make_todo("Ship SiteWinder demo")]
        )
        self.new_text = Signal("")
        self.show_modal = Signal(False)

    def _add_todo(self):
        t = self.new_text().strip()
        if t:
            self.todos.set(self.todos() + [{"text": Signal(t), "done": Signal(False)}])
            self.new_text.set("")

    def _del_todo(self, idx: int):
        items = self.todos()
        if 0 <= idx < len(items):
            self.todos.set(items[:idx] + items[idx + 1 :])

    def template(self):
        items = self.todos()
        root = Division().classes("wrap")
        with root:
            Heading1("✅ Todos & Modal")
            with Division().classes("controls"):
                inp = Input(type="text", placeholder="What’s next?")
                self.bind_value(inp, self.new_text, event="input", prop="value")
                add_btn = Button("Add").classes("btn")
                self.on(add_btn, "click", lambda e: self._add_todo())

            HorizontalRule().style(margin="6px 0")

            if not items:
                Paragraph("No todos yet. Add one above! ✨").classes("empty")
            else:
                for i, item in enumerate(items):
                    row = Division().classes("todo")
                    with row:
                        chk = Input(type="checkbox")
                        self.bind_value(
                            chk, item["done"], event="change", prop="checked"
                        )
                        txt = Input(type="text")
                        self.bind_value(txt, item["text"], event="input", prop="value")
                        del_btn = Button("✕").classes("btn")
                        self.on(del_btn, "click", lambda e, idx=i: self._del_todo(idx))

            # Inline modal (simple)
            class Modal(Component):
                def styles(self):
                    css = Stylesheet()
                    with css:
                        css.rule(
                            ".backdrop",
                            position="fixed",
                            inset="0",
                            background="rgba(0,0,0,.35)",
                            display="grid",
                            place_items="center",
                            z_index="1000",
                        )
                        css.rule(
                            ".panel",
                            width="min(560px, 92vw)",
                            background="#ffffff",
                            color="#0f172a",
                            border_radius="16px",
                            padding="20px",
                            box_shadow="0 10px 30px rgba(0,0,0,.2)",
                        )
                        css.rule(
                            ".actions",
                            display="flex",
                            gap="8px",
                            justify_content="flex-end",
                            margin_top="12px",
                        )
                        css.rule(
                            ".btn",
                            border="1px solid #e5e7eb",
                            border_radius="10px",
                            padding="8px 12px",
                            background="#ffffff",
                            cursor="pointer",
                            color="#0f172a",
                        )
                        css.rule(
                            "html[data-theme='dark'] .panel",
                            background="#111827",
                            color="#e5e7eb",
                        )
                        css.rule(
                            "html[data-theme='dark'] .btn",
                            border="1px solid #334155",
                            background="#0b1220",
                            color="#e5e7eb",
                        )
                    return css

                def on_init(self):
                    self.open_signal = self.props["open_signal"]

                def template(self):
                    if not self.open_signal():
                        return Division()
                    root = Division().classes("backdrop")
                    self.on(
                        root,
                        "click",
                        lambda ev: (
                            self.open_signal.set(False) if ev.target is root else None
                        ),
                    )
                    self.on(
                        root,
                        "keydown",
                        lambda ev: (
                            self.open_signal.set(False)
                            if getattr(ev, "key", "") == "Escape"
                            else None
                        ),
                    )
                    root.set_attr(tabindex="0")
                    with root:
                        panel = Division().classes("panel")
                        with panel:
                            Heading2("🎉 Hello from Modal")
                            Paragraph("This modal is controlled by a Signal.")
                            with Division().classes("actions"):
                                close = Button("Close").classes("btn")
                                self.on(
                                    close,
                                    "click",
                                    lambda e: self.open_signal.set(False),
                                )
                    return root

            open_modal = Button("Open modal").classes("btn")
            self.on(open_modal, "click", lambda e: self.show_modal.set(True))
            self.portal(Modal, open_signal=self.show_modal)
        return root


# ----------------------------- App Shell -----------------------------------------


class Navbar(Component):
    """Sticky top bar with links + light/dark toggle (persists in localStorage)."""

    def styles(self):
        css = Stylesheet()
        with css:
            # Gradient header (light)
            css.rule(
                ".bar",
                position="sticky",
                top="0",
                z_index="500",
                backdrop_filter="saturate(180%) blur(6px)",
                background="linear-gradient(90deg, #7c3aed 0%, #06b6d4 100%)",
                border_bottom="1px solid rgba(0,0,0,.08)",
            )
            # Dark header gradient
            css.rule(
                "html[data-theme='dark'] .bar",
                background="linear-gradient(90deg, #0ea5e9 0%, #7c3aed 100%)",
                border_bottom="1px solid rgba(255,255,255,.08)",
            )
            css.rule(
                ".inner",
                display="flex",
                align_items="center",
                justify_content="space-between",
                padding="10px 16px",
                max_width="1200px",
                margin="0 auto",
            )
            css.rule(".brand", font_weight="700", color="white")
            css.rule(".nav", display="flex", gap="14px", align_items="center")
            css.rule(".link", text_decoration="none", color="white", opacity="0.9")
            css.rule(".link.active", opacity="1.0", text_decoration="underline")
            css.rule(
                ".toggle",
                border="1px solid rgba(255,255,255,.35)",
                border_radius="12px",
                padding="6px 10px",
                background="rgba(255,255,255,.15)",
                cursor="pointer",
                color="white",
            )
        return css

    def on_init(self):
        self.theme: Signal = self.props["theme"]
        from js import window

        self.current_hash = Signal(str(window.location.hash or "#/"))
        self._hash_proxy = None

    def on_mount(self):
        from js import window
        from pyodide.ffi import create_proxy

        self._hash_proxy = create_proxy(
            lambda *_: self.current_hash.set(str(window.location.hash or "#/"))
        )
        window.addEventListener("hashchange", self._hash_proxy)

    def on_destroy(self):
        try:
            from js import window

            if self._hash_proxy:
                window.removeEventListener("hashchange", self._hash_proxy)
                self._hash_proxy = None
        except Exception:
            pass

    def _link(self, href: str, label: str):
        is_active = (self.current_hash() == href) or (
            href == "#/" and self.current_hash() in ("", "#")
        )
        a = Anchor(label, href=href).classes("link" + (" active" if is_active else ""))
        return a

    def template(self):
        root = Division().classes("bar")
        with root:
            inner = Division().classes("inner")
            with inner:
                # Brand: 🐍 snake emoji as requested
                Span("🐍 SiteWinder").classes("brand")
                with Division().classes("nav"):
                    self._link("#/", "Home")
                    self._link("#/counter", "Counter")
                    self._link("#/form", "Form")
                    self._link("#/todos", "Todos")
                    btn = Button("🌙" if self.theme() == "light" else "☀️").classes(
                        "toggle"
                    )

                    def _toggle(_):
                        self.theme.set("dark" if self.theme() == "light" else "light")

                    self.on(btn, "click", _toggle)
        return root


class App(Component):
    """App shell: global styles, Inter font loader, theme handling, navbar + outlet."""

    def styles(self):
        css = Stylesheet()
        with css:
            # Inter font applied broadly
            css.rule(
                "html, body, input, button, select, textarea",
                font_family="'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial",
                line_height="1.5",
            )
            # Base light/dark page colors
            css.rule(
                "html[data-theme='light'] body",
                margin="0",
                background="#f7fafc",
                color="#0f172a",
            )
            css.rule(
                "html[data-theme='dark'] body",
                margin="0",
                background="#0b1220",
                color="#e5e7eb",
            )
            # Links
            css.rule("a", color="#2563eb")
            css.rule("html[data-theme='dark'] a", color="#93c5fd")
            # Page container spacing
            css.rule(
                ".container", max_width="1200px", margin="0 auto", padding="0 16px"
            )
        return css

    def on_init(self):
        self.theme = Signal("light")
        self._theme_unsub = None

    def on_mount(self):
        # Load Inter font once
        from js import document, window

        link_id = "sw-font-inter"
        try:
            if not document.getElementById(link_id):
                ln = document.createElement("link")
                ln.id = link_id
                ln.rel = "stylesheet"
                ln.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
                document.head.appendChild(ln)
        except Exception:
            pass

        # Read persisted theme
        try:
            saved = window.localStorage.getItem("sw-theme")
            if saved in ("light", "dark"):
                self.theme.set(saved)
        except Exception:
            pass

        # Apply + persist theme on changes
        def apply_theme(_old, new):
            try:
                document.documentElement.setAttribute("data-theme", new)
                window.localStorage.setItem("sw-theme", new)
            except Exception:
                pass

        self._theme_unsub = self.theme.subscribe(apply_theme)
        apply_theme(None, self.theme())

    def on_destroy(self):
        if self._theme_unsub:
            try:
                self._theme_unsub()
            except Exception:
                pass
            self._theme_unsub = None

    def template(self):
        root = Division()
        with root:
            self.portal(Navbar, theme=self.theme)
            Division(id="outlet").classes("container").style(
                padding_top="16px", padding_bottom="24px"
            )
        return root


# ----------------------------- Router + Bootstrap --------------------------------

router = Router(
    "#outlet",
    {
        "#/": lambda: Home(),
        "#/counter": lambda: Counter(),
        "#/form": lambda: FormDemo(),
        "#/todos": lambda: Todos(),
    },
)

bootstrap(App, "#app")
router.start()
