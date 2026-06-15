# Screenshots do LangSmith

Coloque aqui os prints do dashboard que comprovam o resultado. A evidência principal
(e sempre atualizada) são os **links públicos** no [README principal](../../README.md#dashboard-público-do-langsmith);
os screenshots são um complemento estático exigido pelo enunciado.

Sugestão de arquivos:

| Arquivo | O que capturar | Como chegar |
|---|---|---|
| `01-metricas-aprovadas.png` | As 5 métricas ≥ 0.8 e o status APROVADO | Saída do terminal de `python src/evaluate.py` |
| `02-prompt-publico-hub.png` | O prompt `kauemsc/bug_to_user_story_v2` com o badge **Public** | https://smith.langchain.com/hub/kauemsc/bug_to_user_story_v2 |
| `03-tracing-exemplo.png` | O trace de uma execução (System prompt + relato de bug + User Story gerada) | Projeto `prompt-optimization-challenge-resolved` → aba **Tracing** → clicar em um `RunnableSequence` |
| `04-dataset-15-exemplos.png` | O dataset de avaliação com 15 exemplos | **Datasets & Experiments** → `prompt-optimization-challenge-resolved-eval` |

No macOS, use `Cmd+Shift+4` para recortar a tela e salve os arquivos nesta pasta.
