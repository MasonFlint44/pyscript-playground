from sitewinder import Component, Signal, Router, bootstrap
from pyhtml5 import (
    Division,
    Header,
    Main,
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
)

# ------------------------ Reusable Components ------------------------------------


class Card(Component):
    """
    Simple reusable card with title + body content.
    Use via: self.portal(Card, title="...", body=lambda: <Node>)
    Pass body as a callable that returns a Node so it renders fresh each time.
    """

    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(
                ".card",
                padding="16px",
                border="1px solid #e5e7eb",
                border_radius="12px",
                background="white",
                box_shadow="0 1px 2px rgba(0,0,0,.05)",
            )
            css.rule(".title", font_weight="600", margin_bottom="8px")
        return css

    def template(self):
        title = self.props.get("title", "")
        body = self.props.get("body")
        root = Division().classes("card")
        with root:
            if title:
                Span(title).classes("title")
            if callable(body):
                # ⚠️ Do NOT panel.add(...). Since we're inside `with root:`,
                # calling body() here will auto-append anything it creates.
                body()
        return root


# ----------------------------- Pages ---------------------------------------------


class Home(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(
                ".hero",
                display="grid",
                gap="16px",
                grid_template_columns="repeat(3, minmax(0, 1fr))",
            )
            css.rule(".grid", display="grid", gap="16px")
            with css.media("(max-width: 900px)"):
                css.rule(".hero", grid_template_columns="1fr")
        return css

    def template(self):
        root = Division().classes("home").style(padding="20px")
        with root:
            with Header():
                Heading1("Welcome to SiteWinder ⚡")
                Paragraph(
                    "Angular-like components in pure Python with PyScript + pyhtml5."
                )
            with Main():
                with Section().classes("hero"):
                    self.portal(
                        Card,
                        title="Counters",
                        body=lambda: Paragraph(
                            "Visit “#/counter” for signals, events, and computed views."
                        ),
                    )
                    self.portal(
                        Card,
                        title="Forms & Binding",
                        body=lambda: Paragraph(
                            "See two-way binding (text, checkbox, select) on “#/form”."
                        ),
                    )
                    self.portal(
                        Card,
                        title="Todos & Modal",
                        body=lambda: Paragraph(
                            "Inline editing with stable focus, plus a modal on “#/todos”."
                        ),
                    )
        return root


class Counter(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(".wrap", padding="20px")
            css.rule(".row", display="flex", gap="8px", align_items="center")
            css.rule(
                ".btn",
                width="36px",
                height="36px",
                border_radius="12px",
                border="1px solid #ddd",
                background="white",
                cursor="pointer",
                font_size="18px",
                line_height="34px",
                text_align="center",
            )
            css.rule(
                ".pill",
                display="inline-block",
                padding="4px 10px",
                border_radius="999px",
                background="#111827",
                color="white",
                font_size="12px",
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
            Heading1("Counter Playground")
            Paragraph("Demonstrates Signals, events, and a computed total.")
            with Division().classes("row"):
                Paragraph("Step:")
                step_in = Input(type="number", min="1", value=str(self.step()))
                self.bind_value(step_in, self.step, event="input", prop="value")
            HorizontalRule().style(margin="12px 0")
            # ⚠️ Don't call root.add(...) while inside `with root:`—just create the rows.
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
                ".wrap", padding="20px", display="grid", gap="14px", max_width="520px"
            )
            css.rule(".row", display="grid", gap="6px")
            css.rule(
                "input, select",
                border="1px solid #d1d5db",
                padding="10px",
                border_radius="10px",
                font_size="14px",
            )
            css.rule(
                ".preview",
                padding="12px",
                background="#f9fafb",
                border_radius="10px",
                border="1px dashed #d1d5db",
            )
        return css

    def on_init(self):
        self.name = Signal("Ada Lovelace")
        self.is_admin = Signal(False)
        self.color = Signal("violet")

    def template(self):
        root = Division().classes("wrap")
        with root:
            Heading1("Form Binding")
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
                Paragraph(f"Hello, {self.name()}!")
                Paragraph(f"Admin: {self.is_admin()}")
                Paragraph(f"Favorite color: {self.color()}")
        return root


class Todos(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(".wrap", padding="20px", display="grid", gap="12px")
            css.rule(
                ".todo",
                display="grid",
                grid_template_columns="auto 1fr auto",
                gap="8px",
                align_items="center",
                padding="8px",
                border="1px solid #eee",
                border_radius="10px",
                background="white",
            )
            css.rule(".controls", display="flex", gap="8px")
            css.rule(
                ".btn",
                border="1px solid #ddd",
                border_radius="10px",
                padding="6px 10px",
                background="white",
                cursor="pointer",
            )
            css.rule(".empty", color="#6b7280")
        return css

    def on_init(self):
        def make_todo(text: str) -> dict:
            return {"text": Signal(text), "done": Signal(False)}

        self.todos: list[dict] = [
            make_todo("Learn PyScript"),
            make_todo("Ship SiteWinder demo"),
        ]
        self.new_text = Signal("")
        self.show_modal = Signal(False)

    def _add_todo(self):
        t = self.new_text().strip()
        if t:
            self.todos.append({"text": Signal(t), "done": Signal(False)})
            self.new_text.set("")

    def _del_todo(self, idx: int):
        if 0 <= idx < len(self.todos):
            del self.todos[idx]

    def template(self):
        root = Division().classes("wrap")
        with root:
            Heading1("Todos + Modal")
            with Division().classes("controls"):
                inp = Input(type="text", placeholder="What’s next?")
                self.bind_value(inp, self.new_text, event="input", prop="value")
                add_btn = Button("Add").classes("btn")
                self.on(add_btn, "click", lambda e: self._add_todo())
                self.on(
                    inp,
                    "keydown",
                    lambda ev: (
                        self._add_todo() if getattr(ev, "key", "") == "Enter" else None
                    ),
                )

            HorizontalRule().style(margin="6px 0")

            if not self.todos:
                Paragraph("No todos yet. Add one above!").classes("empty")
            else:
                for i, item in enumerate(self.todos):
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

            # Modal controlled by self.show_modal
            from sitewinder import (
                Component as _C,
            )  # avoid top-level circular import in some loaders

            class Modal(_C):
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
                            background="white",
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
                            border="1px solid #ddd",
                            border_radius="10px",
                            padding="8px 12px",
                            background="white",
                            cursor="pointer",
                        )
                        css.rule(
                            ".btn.primary",
                            background="#111827",
                            color="white",
                            border_color="#111827",
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
                            Heading2("Hello from Modal")
                            Paragraph("This modal is controlled by a Signal.")
                            with Division().classes("actions"):
                                cancel = Button("Close").classes("btn primary")
                                self.on(
                                    cancel,
                                    "click",
                                    lambda e: self.open_signal.set(False),
                                )
                    return root

            btn_modal = Button("Open modal").classes("btn")
            self.on(btn_modal, "click", lambda e: self.show_modal.set(True))
            # Placeholder for modal
            self.portal(Modal, open_signal=self.show_modal)
        return root


class App(Component):
    def template(self):
        return Division(id="outlet")


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
