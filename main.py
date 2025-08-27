from sitewinder import Component, Signal, Router, bootstrap
from pyhtml5 import (
    Division, Header, Main, Section, Article, Paragraph, Heading1, Heading2,
    Button, Input, Label, UnorderedList, ListItem, HorizontalRule, Stylesheet
)

# ----- Components ----------------------------------------------------------------

class Home(Component):
    def styles(self):
        css = Stylesheet()
        with css:
            css.rule(".hero", display="grid", gap="12px", grid_template_columns="repeat(2, minmax(0,1fr))")
            css.rule(".card", padding="12px", border="1px solid #ddd", border_radius="8px", background="white")
        return css

    def template(self):
        root = Division().classes("home")
        with root:
            with Header():
                Heading1("Welcome to SiteWinder 👋")
                Paragraph("Angular-like components in pure Python with PyScript + pyhtml5.")
            with Main():
                with Section().classes("hero"):
                    with Article().classes("card"):
                        Heading2("Counter")
                        Paragraph("Try the Counter page via router.")
                    with Article().classes("card"):
                        Heading2("Form Binding")
                        Paragraph("Two-way binding demo on the Form page.")
        return root

class Counter(Component):
    def on_init(self):
        self.count = Signal(0)

    def template(self):
        root = Division().classes("counter").style(padding="16px")
        with root:
            Heading1(f"Count: {self.count()}")
            with Division().classes("controls").style(display="flex", gap="8px", margin_top="8px"):
                btn_dec = Button("−").classes("btn")
                self.on(btn_dec, "click", lambda ev: self.count.set(self.count()-1))
                btn_inc = Button("+").classes("btn")
                self.on(btn_inc, "click", lambda ev: self.count.set(self.count()+1))
        return root

class FormDemo(Component):
    def on_init(self):
        self.name = Signal("Ada")
        self.is_admin = Signal(False)

    def template(self):
        root = Division().classes("form").style(padding="16px")
        with root:
            Heading1("Form binding")
            with Division().style(display="grid", gap="8px", max_width="320px"):
                # Text input (two-way)
                with Division():
                    Label("Name:")
                    inp = Input(type="text", placeholder="Your name")
                    self.bind_value(inp, self.name, event="input", prop="value")
                # Checkbox (two-way)
                with Division():
                    Label("Admin?")
                    chk = Input(type="checkbox")
                    self.bind_value(chk, self.is_admin, event="change", prop="checked")
            HorizontalRule().style(margin="12px 0")
            Paragraph(f"Hello, {self.name()}! Admin: {self.is_admin()}")
        return root

class App(Component):
    def template(self):
        # The router will mount different components into this outlet.
        return Division(id="outlet")

# ----- Router + bootstrap ---------------------------------------------------------

router = Router("#outlet", {
    "#/": lambda: Home(),
    "#/counter": lambda: Counter(),
    "#/form": lambda: FormDemo(),
})

# Mount the App shell, then start the router.
bootstrap(App, "#app")
router.start()
