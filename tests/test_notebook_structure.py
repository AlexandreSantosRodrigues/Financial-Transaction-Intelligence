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
        tree = ast.parse(source)

        # Check the actual CSV read allowlist; diagnostics may mention banned fields.
        column_definitions = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "cols" for target in node.targets)
        ]
        self.assertEqual(len(column_definitions), 1)
        loaded_columns = set(ast.literal_eval(column_definitions[0]))
        self.assertEqual(loaded_columns, {"step", "type", "amount", "isFraud", "isFlaggedFraud"})

        csv_reads = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "read_csv"
        ]
        self.assertTrue(csv_reads)
        for call in csv_reads:
            usecols = next((kw.value for kw in call.keywords if kw.arg == "usecols"), None)
            self.assertIsInstance(usecols, ast.Name)
            self.assertEqual(usecols.id, "cols")

        # Verify feature engineering does not access targets, flags or balances.
        feature_functions = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "transformar"
        ]
        self.assertEqual(len(feature_functions), 1)
        data_fields = {
            node.slice.value
            for node in ast.walk(feature_functions[0])
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "parte"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        }
        self.assertEqual(data_fields, {"step", "type", "amount"})
        for forbidden in ("oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest", "isFraud", "isFlaggedFraud"):
            self.assertNotIn(forbidden, data_fields)
        self.assertIn("raw_train", source)
        self.assertIn("raw_val", source)
        self.assertIn("raw_test", source)


if __name__ == "__main__":
    unittest.main()
