import unittest

from browser import parse_css, parse_html, text_wrap


class BrowserTests(unittest.TestCase):
    def test_parse_html_basic_tree(self):
        dom = parse_html("<html><body><h1>Hello</h1><p>World</p></body></html>")
        html = dom.children[0]
        body = html.children[0]
        self.assertEqual(html.tag, "html")
        self.assertEqual(body.tag, "body")

    def test_parse_css(self):
        rules = parse_css("h1 { color: red; font-size: 20px; } .x { display: block; }")
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0].selector, "h1")
        self.assertEqual(rules[0].declarations["color"], "red")

    def test_text_wrap(self):
        lines = text_wrap("a bb ccc dddd", width=6)
        self.assertEqual(lines, ["a bb", "ccc", "dddd"])


if __name__ == "__main__":
    unittest.main()
