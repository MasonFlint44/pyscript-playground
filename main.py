import pyhtml5 as html


def example_build() -> tuple[html.Element, html.Stylesheet]:
    """
    Example showing non-abbreviated class names.
    """
    with html.Stylesheet() as css:
        css.rule("*,*::before,*::after", box_sizing="border-box")
        css.rule(
            "body",
            margin=0,
            font_family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
            line_height=1.5,
        )
        css.rule("#root", padding="24px")
        with css.keyframes("spin") as kf:
            kf.frame("0%").decl("transform", "rotate(0deg)")
            kf.frame("100%").decl("transform", "rotate(360deg)")
        with css.media("(max-width: 640px)"):
            css.rule(".cards", grid_template_columns="1fr")

    with html.Division(id="root") as root:
        with html.Header().classes("site-header"):
            html.Heading1("Non‑abbreviated HTML classes")
            html.Paragraph("Build HTML and CSS using readable Python class names.")
        with html.Main():
            with html.Section().classes("cards").style(
                display="grid",
                gap="16px",
                grid_template_columns="repeat(2, minmax(0,1fr))",
            ):
                with html.Article().classes("card"):
                    html.Heading2("Horizontal Rule + List")
                    html.Paragraph("Below is an HR and an unordered list:")
                    html.HorizontalRule()
                    with html.UnorderedList():
                        for i in range(3):
                            html.ListItem(f"Item {i+1}")
                with html.Article().classes("card"):
                    html.Heading2("Table example")
                    with html.Table().add_class("table"):
                        with html.TableHead():
                            with html.TableRow():
                                html.TableHeaderCell("Name")
                                html.TableHeaderCell("Role")
                        with html.TableBody():
                            with html.TableRow():
                                html.TableDataCell("Ada")
                                html.TableDataCell("Engineer")
                            with html.TableRow():
                                html.TableDataCell("Grace")
                                html.TableDataCell("Scientist")
                    with html.Button("Click me").style(
                        animation="spin 8s linear infinite"
                    ):
                        pass
    return root, css


root, css = example_build()
css.mount()
root.mount()
