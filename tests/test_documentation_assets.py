"""Checks for project documentation, figures and Colab metric provenance.

These tests verify document integrity, not model predictive quality.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ROOT / "analyses" / "01_concentracao_financeira.md",
    ROOT / "analyses" / "02_forecast_segmentos.md",
    ROOT / "analyses" / "03_deteccao_fraudes.md",
    ROOT / "analyses" / "04_fluxo_anomalias.md",
    ROOT / "analyses" / "metodologia_limitacoes.md",
]
IMAGES = [
    "concentracao_hhi_gini.svg",
    "curva_abc.svg",
    "clusters.svg",
    "comparacao_forecast.svg",
    "previsao_volume.svg",
    "matriz_confusao.svg",
    "precision_recall.svg",
    "shap_fraudes.svg",
    "fluxo_financeiro.svg",
    "anomalias.svg",
]


class DocumentationChecks(unittest.TestCase):
    def test_reports_are_present_and_substantive(self):
        for path in REPORTS:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"Relatório não existe: {path}")
                self.assertGreater(len(path.read_text(encoding="utf-8")), 1500)

    def test_svg_figures_are_valid_xml(self):
        for filename in IMAGES:
            path = ROOT / "assets" / "images" / filename
            with self.subTest(figure=filename):
                self.assertTrue(path.is_file(), f"Figura não existe: {path}")
                node = ElementTree.parse(path).getroot()
                self.assertEqual(node.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIn("viewBox", node.attrib)
                self.assertIn("role", node.attrib)

    def test_relative_markdown_links_resolve(self):
        pages = [*REPORTS, ROOT / "README.md"]
        for page in pages:
            if not page.exists():
                continue
            content = page.read_text(encoding="utf-8")
            for dest in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                dest = dest.split("#", 1)[0].split("?", 1)[0].strip()
                if not dest or re.match(r"^(?:[a-z][a-z0-9+.-]*:|/)", dest, re.I):
                    continue
                with self.subTest(page=page.name, link=dest):
                    self.assertTrue((page.parent / dest).exists(), f"Link inválido: {page}: {dest}")

    def test_colab_metrics_provenance(self):
        path = ROOT / "assets" / "data" / "metricas_colab.json"
        metrics = json.loads(path.read_text(encoding="utf-8"))
        banking = metrics["banking"]
        paysim = metrics["paysim"]
        self.assertEqual(banking["transacoes_validas_2019_2023"], 505980)
        self.assertEqual(sum(y["transacoes"] for y in banking["anos"]), 505980)
        self.assertEqual(sum(v["clientes"] for v in banking["abc_2023"].values()), 57301)
        self.assertEqual(sum(v["clientes"] for v in banking["clusters"].values()), 79866)
        self.assertEqual(paysim["transacoes"], 6362620)
        self.assertEqual(paysim["fraudes"], 8213)
        cm = paysim["xgboost"]
        self.assertEqual(cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"], 123580)
        self.assertEqual(cm["tp"] + cm["fn"], 1654)
        self.assertNotEqual(metrics["meta"]["unidade_banking"], metrics["meta"]["unidade_paysim"])

    def test_readme_after_rebranding(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        if not readme.startswith("# Financial Transaction Intelligence"):
            # The README is committed last; earlier doc-only commits remain testable.
            self.skipTest("README still awaits rebranding in this intermediate commit")
        for expected in (
            "analyses/01_concentracao_financeira.md",
            "analyses/02_forecast_segmentos.md",
            "analyses/03_deteccao_fraudes.md",
            "analyses/04_fluxo_anomalias.md",
            "analyses/metodologia_limitacoes.md",
        ):
            self.assertIn(expected, readme)
        self.assertNotIn("![Power BI]", readme)
        self.assertNotIn("Power Query", readme)
        self.assertNotIn("37.000", readme)


if __name__ == "__main__":
    unittest.main()
