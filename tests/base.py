import os
import unittest
import json

import lxml.html


class MFPTestCase(unittest.TestCase):
    def get_html_document(self, file_name):
        file_path = os.path.join(os.path.dirname(__file__), "html", file_name)
        content = None
        with open(file_path, "r", encoding="utf-8") as in_:
            content = in_.read()
        return lxml.html.document_fromstring(content)

    def get_json_data(self, file_name):
        file_path = os.path.join(os.path.dirname(__file__), "json", file_name)
        with open(file_path, "r", encoding="utf-8") as in_:
            content = in_.read()
        return json.loads(content)
