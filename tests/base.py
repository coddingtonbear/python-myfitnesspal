import os
import unittest

import lxml.html


class MFPTestCase(unittest.TestCase):
    def get_html_document(self, file_name):
        file_path = os.path.join(os.path.dirname(__file__), "html", file_name)
        content = None
        with open(file_path, "r") as in_:
            content = in_.read()
        return lxml.html.document_fromstring(content)
