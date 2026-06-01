from django.test import TestCase

from bookmarker.templatetags.markdown_filter import markdownify


class TestMarkdownify(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_smart_emphasis(self):
        text=""""_Both_" comes off as sloppy characterization, muddy filmmaking, lack of focus. [...] But I submit that that the real reason we criticized and disliked Lynch's Laura's muddy *both*ness"""
        expected="""<p>"<em>Both</em>" comes off as sloppy characterization, muddy filmmaking, lack of focus. [...] But I submit that that the real reason we criticized and disliked Lynch's Laura's muddy <em>both</em>ness</p>"""
        self.assertMultiLineEqual(
            expected,
            markdownify(text)
        )
