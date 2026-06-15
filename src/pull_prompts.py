"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt de baixa qualidade do Hub (leonanluppi/bug_to_user_story_v1)
3. Salva localmente em prompts/bug_to_user_story_v1.yml

A serialização lê as mensagens do ChatPromptTemplate retornado pelo Hub e
reconstrói uma estrutura YAML legível (system_prompt / user_prompt + metadados).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt(s) de baixa qualidade publicados no Hub do desafio.
PROMPTS_TO_PULL = [
    {
        "hub_name": "leonanluppi/bug_to_user_story_v1",
        "output_path": "prompts/bug_to_user_story_v1.yml",
        "yaml_key": "bug_to_user_story_v1",
        "version": "v1",
    },
]


def extract_messages(prompt_template) -> dict:
    """
    Extrai as mensagens (system / human) de um ChatPromptTemplate retornado
    pelo Hub e devolve um dicionário com system_prompt e user_prompt.

    Funciona tanto para ChatPromptTemplate quanto para PromptTemplate simples.
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_template, "messages", None)

    if messages:
        for message in messages:
            # Cada item é um MessagePromptTemplate; o texto fica em .prompt.template
            inner = getattr(message, "prompt", None)
            template_text = getattr(inner, "template", None)

            # Alguns templates (ex.: MessagesPlaceholder) não têm .prompt
            if template_text is None:
                continue

            role = type(message).__name__.lower()

            if "system" in role:
                system_prompt += template_text
            elif "human" in role or "user" in role:
                user_prompt += template_text
            else:
                # Fallback: trata mensagens desconhecidas como contexto de sistema
                system_prompt += template_text
    else:
        # PromptTemplate simples (sem múltiplas mensagens)
        template_text = getattr(prompt_template, "template", "")
        system_prompt = template_text

    return {
        "system_prompt": system_prompt.strip(),
        "user_prompt": user_prompt.strip(),
    }


def pull_single_prompt(config: dict) -> bool:
    """Faz pull de um único prompt do Hub e salva localmente em YAML."""
    hub_name = config["hub_name"]
    output_path = config["output_path"]

    print(f"\n📥 Fazendo pull de: {hub_name}")

    try:
        prompt_template = hub.pull(hub_name)
        print(f"   ✓ Prompt carregado do Hub")
    except Exception as e:
        print(f"   ❌ Erro ao fazer pull de '{hub_name}': {e}")
        return False

    extracted = extract_messages(prompt_template)

    if not extracted["system_prompt"] and not extracted["user_prompt"]:
        print(f"   ⚠️  Não foi possível extrair conteúdo do prompt.")
        return False

    # Reconstrói a estrutura YAML legível (mesmo formato do v1 do desafio).
    yaml_data = {
        config["yaml_key"]: {
            "description": "Prompt (pull do LangSmith Hub) para converter relatos de bugs em User Stories",
            "system_prompt": extracted["system_prompt"],
            "user_prompt": extracted["user_prompt"] or "{bug_report}",
            "version": config["version"],
            "source": hub_name,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if save_yaml(yaml_data, output_path):
        print(f"   ✓ Prompt salvo em: {output_path}")
        return True

    print(f"   ❌ Falha ao salvar prompt em: {output_path}")
    return False


def pull_prompts_from_langsmith() -> bool:
    """Faz pull de todos os prompts configurados e salva localmente."""
    all_ok = True

    for config in PROMPTS_TO_PULL:
        if not pull_single_prompt(config):
            all_ok = False

    return all_ok


def main():
    """Função principal."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    print("\n" + "=" * 50)
    if success:
        print("✅ Pull concluído com sucesso!")
        print("\nPróximo passo: analise o prompt v1 e crie sua versão otimizada em")
        print("  prompts/bug_to_user_story_v2.yml")
        return 0
    else:
        print("❌ Pull concluído com erros. Verifique as mensagens acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
