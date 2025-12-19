import unittest

from src.html_formatter import HTMLFormatter


class TestHTMLFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = HTMLFormatter(title="Test Pulse")

    def test_format_pulse_includes_core_sections(self):
        overall_md = (
            "# Headline\n"
            "Intro paragraph with *italics* and **bold**.\n"
            "- key insight A\n"
            "- key insight B\n"
            "1. ordered item\n"
            "2. second item\n"
            "> blockquote insight\n"
            "`inline code`\n"
        )
        html = self.formatter.format_pulse(
            overall_md,
            [
                {
                    "name": "source1",
                    "summary": (
                        "## Source headline\n"
                        "- bullet one\n"
                        "- bullet two\n"
                        "Paragraph with a [link](http://example.com).\n"
                    ),
                    "banner_url": "assets/banners/source1.jpg",
                    "items": [
                        {
                            "title": "Post Title",
                            "link": "http://example.com",
                            "date": "2024-01-01",
                            "summary": "Short summary",
                        }
                    ],
                }
            ],
        )

        self.assertIn("Test Pulse", html)
        self.assertIn("Headline", html)
        self.assertIn("Intro paragraph", html)
        self.assertIn("key insight A", html)
        self.assertIn("ordered item", html)
        self.assertIn("blockquote", html)
        self.assertIn("inline code", html)
        self.assertIn("source1", html)
        self.assertIn("bullet one", html)
        self.assertIn("bullet two", html)
        self.assertIn("Source headline", html)
        self.assertIn("Post Title", html)
        self.assertIn("http://example.com", html)
        self.assertIn("2024-01-01", html)
        self.assertIn("card-banner", html)
        self.assertIn("assets/banners/source1.jpg", html)


if __name__ == "__main__":
    unittest.main()
