"""
Testes automatizados para validação do prompt otimizado (v2).

Executar com:
    pytest tests/test_prompts.py -v
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure  # noqa: F401 (disponível para uso/extensão)

# Caminho e chave do prompt otimizado
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Carrega o conteúdo do prompt v2 (dicionário sob a chave principal)."""
    data = load_prompts(str(PROMPT_PATH))
    assert data is not None, f"Não foi possível carregar {PROMPT_PATH}"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        system_prompt = prompt["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser string"
        assert system_prompt.strip() != "", "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt.get("system_prompt", "").lower()
        # Procura por marcadores de Role Prompting
        role_markers = ["você é", "voce e", "atue como", "persona"]
        assert any(marker in system_prompt for marker in role_markers), (
            "O system_prompt deve definir uma persona/role "
            "(ex: 'Você é um Product Manager...')"
        )
        # Reforça que a persona é de Product Manager (contexto do desafio)
        assert "product manager" in system_prompt, (
            "A persona esperada é de Product Manager"
        )

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        # Considera todos os campos de texto do prompt
        text = " ".join(
            str(prompt.get(field, ""))
            for field in ("system_prompt", "user_prompt", "description")
        ).lower()

        mentions_markdown = "markdown" in text
        # Template padrão de User Story: "Como um... eu quero... para que..."
        mentions_user_story_format = (
            "como um" in text and "eu quero" in text and "para que" in text
        )
        assert mentions_markdown or mentions_user_story_format, (
            "O prompt deve exigir formato Markdown ou o template padrão de "
            "User Story ('Como um... eu quero... para que...')"
        )

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt.get("system_prompt", "").lower()

        # Sinais de Few-shot: palavra "exemplo" + pares de entrada/saída
        has_example_keyword = "exemplo" in system_prompt
        has_input_marker = "relato de bug" in system_prompt
        has_output_marker = "user story gerada" in system_prompt

        # Deve haver mais de um exemplo (few-shot, não one-shot)
        example_count = system_prompt.count("user story gerada")

        assert has_example_keyword, "O prompt deve conter exemplos (palavra 'exemplo')"
        assert has_input_marker and has_output_marker, (
            "Os exemplos devem ter pares de entrada (relato de bug) e saída (user story)"
        )
        assert example_count >= 2, (
            f"Few-shot requer pelo menos 2 exemplos; encontrados: {example_count}"
        )

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` ou `TODO` no texto.

        Usa fronteira de palavra para não dar falso-positivo em palavras
        legítimas que contêm a substring 'todo' (ex.: 'metodologias', 'todos').
        """
        # Casa o placeholder [TODO] (qualquer caixa) ou o token TODO/TODOS em
        # CAIXA ALTA isolado. Não casa a palavra portuguesa "todos" (minúscula).
        todo_pattern = re.compile(r"(?i:\[TODO\])|\bTODOs?\b")
        for field in ("system_prompt", "user_prompt", "description"):
            text = str(prompt.get(field, ""))
            match = todo_pattern.search(text)
            assert match is None, (
                f"O campo '{field}' ainda contém um TODO pendente: '{match.group()}'"
            )

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), (
            "'techniques_applied' deve ser uma lista nos metadados do YAML"
        )
        assert len(techniques) >= 2, (
            f"Pelo menos 2 técnicas devem ser listadas; encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
