"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts (system_prompt, persona, formato, few-shot, técnicas, sem TODOs)
3. Constrói um ChatPromptTemplate (system + human) com a variável {bug_report}
4. Faz push PÚBLICO para o LangSmith Hub: {USERNAME}/bug_to_user_story_v2
5. Adiciona metadados (tags, descrição/readme, técnicas utilizadas)

Usa o langsmith.Client.push_prompt, que suporta is_public, description, tags e readme.
"""

import os
import re
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Mapeia o arquivo YAML local -> nome (sem username) publicado no Hub.
PROMPTS_TO_PUSH = [
    {
        "yaml_path": "prompts/bug_to_user_story_v2.yml",
        "yaml_key": "bug_to_user_story_v2",
        "hub_name": "bug_to_user_story_v2",
    },
]


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt otimizado.

    Args:
        prompt_data: Dados do prompt (conteúdo sob a chave do YAML)

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    # Campo system_prompt obrigatório e não vazio
    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    if not system_prompt:
        errors.append("system_prompt está vazio ou ausente")

    # Sem TODOs pendentes. Casa o placeholder [TODO] (qualquer caixa) ou o token
    # TODO/TODOS em CAIXA ALTA isolado; não casa palavras como "metodologias"/"todos".
    todo_pattern = re.compile(r"(?i:\[TODO\])|\bTODOs?\b")
    for field in ("system_prompt", "user_prompt", "description"):
        text = prompt_data.get(field) or ""
        if todo_pattern.search(text):
            errors.append(f"campo '{field}' ainda contém TODO")

    # Persona / Role Prompting presente
    if "você é" not in system_prompt.lower():
        errors.append("system_prompt não define uma persona (Role Prompting)")

    # Mínimo de 2 técnicas declaradas nos metadados
    techniques = prompt_data.get("techniques_applied", []) or []
    if len(techniques) < 2:
        errors.append(
            f"mínimo de 2 técnicas requeridas em 'techniques_applied', "
            f"encontradas: {len(techniques)}"
        )

    return (len(errors) == 0, errors)


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """
    Constrói um ChatPromptTemplate (system + human) a partir dos dados do YAML.
    A variável de entrada é {bug_report}, consumida durante a avaliação.
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = (prompt_data.get("user_prompt") or "{bug_report}").strip()

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt no Hub (com username, ex.: 'user/bug_to_user_story_v2')
        prompt_data: Dados do prompt (conteúdo sob a chave do YAML)

    Returns:
        True se sucesso, False caso contrário
    """
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print(f"   ❌ Prompt inválido:")
        for err in errors:
            print(f"      - {err}")
        return False

    chat_prompt = build_chat_prompt(prompt_data)

    techniques = prompt_data.get("techniques_applied", [])
    tags = prompt_data.get("tags", [])
    description = prompt_data.get("description", "Prompt otimizado: Bug to User Story")

    readme = (
        f"{description}\n\n"
        f"**Técnicas aplicadas:** {', '.join(techniques)}\n\n"
        f"Converte relatos de bugs em User Stories ágeis (formato "
        f"'Como um... eu quero... para que...') com critérios de aceitação em Gherkin, "
        f"adaptando a profundidade à complexidade do bug."
    )

    try:
        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=chat_prompt,
            is_public=True,
            description=description,
            readme=readme,
            tags=tags,
        )
        print(f"   ✓ Push PÚBLICO concluído")
        print(f"   🔗 URL: {url}")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao fazer push de '{prompt_name}': {e}")
        return False


def main():
    """Função principal."""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    all_ok = True
    pushed = 0

    for config in PROMPTS_TO_PUSH:
        yaml_path = config["yaml_path"]
        yaml_key = config["yaml_key"]
        prompt_name = f"{username}/{config['hub_name']}"

        print(f"\n📤 Preparando push de: {prompt_name}")
        print(f"   Lendo: {yaml_path}")

        data = load_yaml(yaml_path)
        if not data:
            print(f"   ❌ Não foi possível carregar {yaml_path}")
            all_ok = False
            continue

        prompt_data = data.get(yaml_key)
        if not prompt_data:
            print(f"   ❌ Chave '{yaml_key}' não encontrada em {yaml_path}")
            all_ok = False
            continue

        if push_prompt_to_langsmith(prompt_name, prompt_data):
            pushed += 1
        else:
            all_ok = False

    print("\n" + "=" * 50)
    if all_ok and pushed > 0:
        print(f"✅ Push concluído! {pushed} prompt(s) publicado(s).")
        print("\nPróximos passos:")
        print("1. Verifique o prompt no dashboard: https://smith.langchain.com/prompts")
        print("2. Confirme que está PÚBLICO (ícone de cadeado aberto)")
        print("3. Execute a avaliação: python src/evaluate.py")
        return 0
    else:
        print("❌ Push concluído com erros. Verifique as mensagens acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
