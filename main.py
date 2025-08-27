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
            css.rule(
                ".card",
                padding="16px",
                border="1px solid #e5e7eb",
                border_radius="14px",
                background="var(--card-bg)",
                box_shadow="0 1px 2px rgba(0,0,0,.06)",
            )
            css.rule(
                ".title",
                font_weight="600",
                margin_bottom="8px",
                color="var(--text-strong)",
            )
        return css

    def template(self):
        title = self.props.get("title", "")
        body = self.props.get("body")
        root = Division().classes("card")
        with root:
            if title:
                Span(title).classes("title")
            if callable(body):
                # Render body content; context manager will append.
                body()
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
            css.rule(".lead", color="var(--text-muted)")
            with css.media("(max-width: 900px)"):
                css.rule(".hero", grid_template_columns="1fr")
        return css

    def template(self):
        root = Division().classes("home")
        with root:
            Heading1("💨 SiteWinder")
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
            css.rule(
                ".btn",
                width="38px",
                height="38px",
                border_radius="12px",
                border="1px solid var(--line)",
                background="var(--btn-bg)",
                cursor="pointer",
                font_size="18px",
                line_height="36px",
                text_align="center",
                color="var(--text)",
            )
            css.rule(
                ".pill",
                display="inline-block",
                padding="4px 10px",
                border_radius="999px",
                background="var(--accent)",
                color="white",
                font_size="12px",
            )
            css.rule(
                "input[type=number]",
                border="1px solid var(--line)",
                background="var(--field-bg)",
                color="var(--text)",
                border_radius="10px",
                padding="8px 10px",
                width="82px",
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
                )  # coerce → int via sitewinder
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
            css.rule(
                "input, select",
                border="1px solid var(--line)",
                background="var(--field-bg)",
                color="var(--text)",
                padding="10px",
                border_radius="10px",
                font_size="14px",
            )
            css.rule(
                ".preview",
                padding="12px",
                background="var(--card-bg)",
                border_radius="12px",
                border="1px dashed var(--line)",
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
            css.rule(
                ".todo",
                display="grid",
                grid_template_columns="auto 1fr auto",
                gap="8px",
                align_items="center",
                padding="8px",
                border="1px solid var(--line)",
                border_radius="10px",
                background="var(--card-bg)",
            )
            css.rule(".controls", display="flex", gap="8px")
            css.rule(
                ".btn",
                border="1px solid var(--line)",
                border_radius="10px",
                padding="6px 10px",
                background="var(--btn-bg)",
                cursor="pointer",
                color="var(--text)",
            )
            css.rule(".empty", color="var(--text-muted)")
            css.rule(
                "input[type=text]",
                border="1px solid var(--line)",
                background="var(--field-bg)",
                color="var(--text)",
                border_radius="10px",
                padding="8px 10px",
            )
        return css

    def on_init(self):
        def make_todo(text: str) -> dict:
            return {"text": Signal(text), "done": Signal(False)}

        # List wrapped in a Signal so deletions/additions trigger render
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

            # Simple modal using a quick inner class to avoid extra file
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
                            background="var(--card-bg)",
                            border_radius="16px",
                            padding="20px",
                            box_shadow="0 10px 30px rgba(0,0,0,.2)",
                            color="var(--text)",
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
                            border="1px solid var(--line)",
                            border_radius="10px",
                            padding="8px 12px",
                            background="var(--btn-bg)",
                            cursor="pointer",
                            color="var(--text)",
                        )
                        css.rule(
                            ".btn.primary",
                            background="var(--accent)",
                            color="white",
                            border_color="var(--accent)",
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
                                close = Button("Close").classes("btn primary")
                                self.on(
                                    close,
                                    "click",
                                    lambda e: self.open_signal.set(False),
                                )
                    return root

            # Trigger modal
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
            css.rule(
                ".bar",
                position="sticky",
                top="0",
                z_index="500",
                backdrop_filter="saturate(180%) blur(8px)",
                background="var(--nav-bg)",
                border_bottom="1px solid var(--line)",
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
            css.rule(".brand", font_weight="700", color="var(--text-strong)")
            css.rule(".nav", display="flex", gap="12px", align_items="center")
            css.rule(".link", text_decoration="none", color="var(--text)")
            css.rule(".link.active", color="var(--accent)")
            css.rule(
                ".toggle",
                border="1px solid var(--line)",
                border_radius="12px",
                padding="6px 10px",
                background="var(--btn-bg)",
                cursor="pointer",
                color="var(--text)",
            )
        return css

    def on_init(self):
        # theme signal is passed from App
        self.theme: Signal = self.props["theme"]
        # track location for active link highlight
        from js import window

        self.current_hash = Signal(str(window.location.hash or "#/"))
        # cache listener so we can remove it
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
                Span("💨 SiteWinder").classes("brand")
                with Division().classes("nav"):
                    self._link("#/", "Home")
                    self._link("#/counter", "Counter")
                    self._link("#/form", "Form")
                    self._link("#/todos", "Todos")
                    # theme toggle
                    btn = Button("🌙" if self.theme() == "light" else "☀️").classes(
                        "toggle"
                    )

                    def _toggle(_):
                        self.theme.set("dark" if self.theme() == "light" else "light")

                    self.on(btn, "click", _toggle)
        return root


class App(Component):
    """App shell: global styles, font loader, theme handling, navbar + outlet."""

    def styles(self):
        css = Stylesheet()
        with css:
            # Base theme tokens (no CSS variables to keep builder simple)
            css.rule(
                "body",
                margin="0",
                background="#f7fafc",
                color="#0f172a",
                font_family="'Inter', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji'",
            )
            css.rule("[data-theme='dark'] body", background="#0b1220", color="#e5e7eb")
            # Semantic tokens using selectors (light vs dark)
            css.rule(
                ":root",
                **{
                    "/*": "light theme tokens (ignored by browser; comment placeholder)"
                },
            )
            # Light
            css.rule("body", **{"--noop": "0"})  # placeholder so block isn't empty
            # Component token aliases (light)
            css.rule(
                ":root body",
                **{
                    # surfaces
                    "/*card-bg*/ color": "inherit"
                },
            )
            # We'll use explicit values inside components via these names:
            # -- we can't set CSS custom props with the builder, so bake values:
            css.rule(":root", **{})  # no-op
            # Link styles
            css.rule("a", color="#2563eb")
            css.rule("[data-theme='dark'] a", color="#93c5fd")
            # App-level “design tokens” via selectors
            # We’ll reference these in components as concrete values:
            # Light:
            css.rule(":root body", **{"/*text*/ outline-color": "#0f172a"})
            # Basic utility classes
            css.rule(
                ".container", max_width="1200px", margin="0 auto", padding="0 16px"
            )
            # Non-variable aliases used by components:
            css.rule(":root", **{})  # no-op to satisfy builder
        return css

    def on_init(self):
        self.theme = Signal("light")
        self._theme_unsub = None

    def on_mount(self):
        # Load Inter font into <head> once
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
        # Apply immediately
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
            # Header + nav
            self.portal(Navbar, theme=self.theme)
            # Page outlet (router mounts here)
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
