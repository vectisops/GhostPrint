import unittest


class GuiImportTests(unittest.TestCase):
    def test_gui_module_imports_without_starting_window_or_network_requests(self):
        import gui

        self.assertTrue(callable(gui.main))


if __name__ == "__main__":
    unittest.main()
