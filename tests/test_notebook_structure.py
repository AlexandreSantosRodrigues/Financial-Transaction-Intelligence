"""Static quality gates; do not claim dataset validation from these checks."""
import ast
from pathlib import Path
import unittest
import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


class NotebookStructureTests(unittest.TestCase):
    def test_four_notebooks_present(self):
        self.assertEqual(len(NOTEBOOKS), 4)

    def test_only_initial_title_and_code(self):
        for path in NOTEBOOKS:
            with self.subTest(notebook=path.name):
                notebook = nbformat.read(path, as_version=4)
                nbformat.validate(notebook)
                self.assertEqual(notebook.cells[0].cell_type, "markdown")
                self.assertEqual(sum(c.cell_type == "markdown" for c in notebook.cells), 1)
                self.assertTrue(notebook.cells[0].source.startswith("# "))
                self.assertTrue(all(c.cell_type == "code" for c in notebook.cells[1:]))
                for cell in notebook.cells[1:]:
                    ast.parse(cell.source)

    def test_no_training_on_post_transaction_balances(self):
        path = ROOT / "notebooks" / "03_fraudes_picos_movimentacao.ipynb"
        notebook = nbformat.read(path, as_version=4)
        source = "\n".join(c.source for c in notebook.cells if c.cell_type == "code")
        for name in ("oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"):
            self.assertNotIn(name, source)
        self.assertIn("raw_train", source)
        self.assertIn("raw_val", source)
        self.assertIn("raw_test", source)


if __name__ == "__main__":
    unittest.main()
