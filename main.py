from pyscript_html import *

# Styles with at-rules
with StyleSheet() as styles:
    styles.import_url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap")
    with styles.font_face(font_family="'Inter'", font_style="normal", font_weight="400", src="local('Inter'), url('/fonts/Inter.woff2') format('woff2')"):
        pass
    styles.property("--card-radius", syntax="<length>", inherits="false", initial_value="16px")

    with styles.rule("body") as r:
        r.set(margin="2rem", font_family="Inter, system-ui, sans-serif", background="#fafafa")
    with styles.rule(".card") as r:
        r.set(background="#fff", padding="1.25rem", border_radius="var(--card-radius)", box_shadow="0 10px 25px rgba(0,0,0,0.08)", max_width="880px", margin="0 auto")
    with styles.rule("header, footer") as r:
        r.set(padding="0.75rem 0")
    with styles.rule("nav ul") as r:
        r.set(display="flex", gap="1rem", list_style="none", padding_left="0")
    with styles.rule(".muted") as r:
        r.set(color="#666")
    with styles.rule("table") as r:
        r.set(border_collapse="collapse", width="100%")
    with styles.rule("th, td") as r:
        r.set(border="1px solid #e5e5e5", padding="8px", text_align="left")
    with styles.rule(".btn") as r:
        r.set(display="inline-block", padding="0.6rem 0.9rem", border_radius="10px", background="#111", color="white", text_decoration="none")
    with styles.rule(".btn:hover") as r:
        r.set(filter="brightness(1.06)")

    with styles.keyframes("fadeIn") as kf:
        kf.step("from", opacity=0)
        kf.step("to", opacity=1)
    with styles.rule(".fade-in") as r:
        r.set(animation="fadeIn 500ms ease-out both")

    with styles.media("(max-width: 700px)") as m:
        with m.rule("body") as r:
            r.set(margin="1rem")
        with m.rule("nav ul") as r:
            r.set(flex_direction="column")

    with styles.supports("(backdrop-filter: blur(4px))") as s:
        with s.rule(".card") as r:
            r.set(background="rgba(255,255,255,0.85)", backdrop_filter="blur(6px)")

    with styles.container("(min-width: 600px)") as c:
        with c.rule(".two-col") as r:
            r.set(display="grid", grid_template_columns="1fr 1fr", gap="1rem")

    with styles.layer("components") as layer:
        with layer.rule(".btn") as r:
            r.set(font_weight="600")

with App(stylesheet=styles) as app:
    with Header():
        with Navigation():
            with List(unordered=True):
                with ListItem(): Anchor("Home", href="#")
                with ListItem(): Anchor("Docs", href="#")
                with ListItem(): Anchor("GitHub", href="#")
    with Main():
        with Division(cls="card"):
            with Article():
                with Heading("Welcome", size=2): pass
                with Paragraph(cls="muted"): text("This DSL mirrors HTML5 with clean names. Styles use the same with-syntax.")
                with Figure():
                    with Image(src="/logo.png", alt="Logo"): pass
                    with FigureCaption(): text("Our logo.")
                with InlineFrame(src="https://example.com", title="Example", width="100%", height="200", loading="lazy", referrerpolicy="no-referrer"): pass
                with Canvas(width="200", height="80", id="chart"): pass
                with Division(cls="two-col fade-in"):
                    with Paragraph(): text("This column stacks under 700px (@media).")
                    with Paragraph(): text("Button uses @layer + @keyframes.")
                with Table():
                    with TableHead():
                        with TableRow():
                            with TableHeaderCell("Key"): pass
                            with TableHeaderCell("Value"): pass
                    with TableBody():
                        with TableRow():
                            with TableDataCell("Language"): pass
                            with TableDataCell("Python"): pass
                with Paragraph():
                    with Anchor("Primary Action", href="#", cls="btn"): pass
        with Aside():
            with Paragraph(): text("Sidebar content")
            with Meter(value="0.6", min="0", max="1"): pass
            with Progress(value="40", max="100"): pass
            with Paragraph(): InlineQuote("Inline quote example")
            with Paragraph(): Bold("B"); Italic("I"); Underline("U"); Strikethrough("S")
    with Footer():
        with Paragraph(): text("© 2025 MySite")
    mount(app)
