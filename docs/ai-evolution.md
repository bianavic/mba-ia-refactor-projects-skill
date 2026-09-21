# Evolução do Uso de IA

[← README](../README.md) · [Análise Manual](manual-analysis.md) · [Design da Skill](skill-design.md) · [Resultados](results.md) · [Estrutura do Projeto](project-structure.md) · [Enunciado Original](challenge-original.md)

> Registro do que já foi aplicado para sustentar "funciona em qualquer stack" e do que ficou mapeado como próximo passo — não é um requisito obrigatório do enunciado, é contexto de engenharia sobre como o projeto evoluiu.

---

O enunciado pede uma skill que funcione em qualquer projeto de backend. Esta seção registra o que foi feito para sustentar essa afirmação, e o que ficou mapeado como próximo passo — separando explicitamente as duas coisas, para que nada aqui seja lido como implementado quando não está.

O princípio que organiza tudo abaixo: **separar o que é da skill do que é do repositório**. Tudo que a skill precisa para rodar tem que viajar com ela; tudo que é específico de um projeto fica no projeto. Foi a violação desse princípio que gerou o trabalho da seção 7.1.

## 7.1 O Que Já Foi Aplicado

**A verificação estrutural passou a ser propriedade da skill.** O `SKILL.md` exigia, no passo 6 da Fase 3, uma verificação mecânica do AP-16 — e apontava para `./arch-check.sh`, um script que existia em triplicata neste repositório e em nenhum outro lugar. Em qualquer projeto externo, o único passo que a skill não consegue provar por teste de endpoint simplesmente não tinha o que executar. A skill agora empacota `scripts/arch-check.sh` (agnóstico de stack) e `references/verification-recipes.md` (sinais por linguagem e o procedimento para derivar padrões numa stack não listada); o passo 6 prefere uma verificação que o projeto auditado já tenha e cai para a empacotada quando não existe.

## 7.2 Hooks — Mover Regras do Prompt para o Harness

Três das regras inegociáveis do `SKILL.md` hoje dependem de o modelo obedecer a uma instrução em texto. Hooks as tornariam garantias do harness:

| Hook | Regra que passa a ser imposta |
|---|---|
| `PreToolUse` em `Edit`/`Write` | "Nunca modificar arquivo antes da confirmação da Fase 2" — bloqueia a escrita enquanto a fase corrente for 1 ou 2, em vez de confiar na instrução |
| `PostToolUse` em `Edit`/`Write` | Roda a verificação de AP-16 assim que um arquivo de rota é alterado — a regressão aparece no instante em que é introduzida |
| `Stop` | Recusa encerrar o turno se a verificação estrutural falhar, ou se a Fase 2 rodou sem o relatório ter sido salvo em `reports/` |
| `PreToolUse` em `Bash(git commit *)` | Aborta se o staged tocar `.env`, `*.db` ou `instance/` — hoje isso é só `.gitignore` |

Detalhe de projeto importante: **hooks não pertencem à skill**. Eles vivem no `.claude/settings.json` do projeto auditado, e colocá-los dentro da skill a amarraria a uma configuração de host — exatamente o erro corrigido na seção 7.1. O caminho correto é a Fase 3 *emitir* uma configuração sugerida como entregável, que o projeto adota ou não.

O mesmo raciocínio se aplica ao *plan mode*: rodar as Fases 1 e 2 nele faz do gate de confirmação uma impossibilidade técnica em vez de uma promessa, sem que a skill precise saber nada sobre isso.

## 7.3 Modo Headless e CI

A Fase 2 é read-only por definição — o que a torna o candidato natural para automação:

- **Auditoria como gate de PR.** `claude -p` com as ferramentas restritas a leitura transforma "a Fase 2 nunca modifica arquivos" numa garantia do processo, não do modelo. Falhar o PR quando aparece um CRITICAL/HIGH ausente do baseline converte os relatórios de `reports/` — hoje evidência estática do estado "antes" — em baseline executável.
- **Saída estruturada.** Se a Fase 2 emitisse `audit.json` junto com o markdown, o diff entre auditorias seria mecânico. É exatamente o trabalho que hoje é feito à mão nos relatórios `-part2`, cuja seção `## Resolved since ...` é redigida manualmente.
- **Execução em lote multi-repo.** Nesta entrega, a evidência de que a skill é agnóstica de stack vem dos 3 projetos deste repositório — duas stacks, três arquiteturas de partida. Rodar as Fases 1 e 2 em lote sobre N repositórios públicos, com as ferramentas restritas a leitura, produziria uma medida de genericidade em vez de um argumento: em quantos a skill dispara, em quantos os achados citam arquivo:linha real, em quantos o detector de AP-16 encontra a camada de rotas. É também como uma lacuna de padrão numa stack ainda não coberta apareceria por processo, antes de alguém tropeçar nela.

## 7.4 Decomposição da Skill e Evals

- **Três skills em vez de três fases.** `arch-audit` (read-only), `arch-refactor` e `arch-verify`. O gate entre Fase 2 e Fase 3 viraria uma fronteira real, e `arch-verify` ficaria reutilizável em CI sem arrastar o resto do fluxo.
- **Testes de caracterização antes da Fase 3.** "Preservar o comportamento existente" hoje é verificado por um `manual-tests.sh` escrito à mão, depois do fato. A Fase 1 já monta a tabela de rotas: gerar os testes *antes* de tocar no código transforma a preservação de comportamento em medida, não em afirmação.
- **Evals da skill.** Rodar a skill contra repositórios não vistos e medir se ela dispara, se atinge a distribuição mínima de achados e se todo achado cita arquivo:linha real. É a forma de substituir "a skill é agnóstica de tecnologia" por um número — hoje é uma afirmação sustentada por duas stacks.
- **Distribuição como plugin.** A triplicata da skill é exigência do enunciado ([seção 9.4.3](challenge-original.md#94-requisitos)), não uma escolha de design. Fora deste contexto, empacotar como plugin instalável resolveria a duplicação sem copiar diretórios.

## 7.5 Limites Conhecidos

- O `arch-check.sh` empacotado é baseado em regex sobre arquivos de rota. Ele não substitui análise de AST: uma chamada de persistência atrás de um alias, de reflexão ou de um wrapper genérico escapa. Ele erra para o lado de sinalizar demais (um falso positivo vira revisão humana; um falso negativo vira selo de aprovação indevido), e por isso trata "não achei a camada de rotas" como INCONCLUSIVE.
- Os padrões cobrem 7 famílias de linguagem, e só duas delas foram exercitadas de verdade aqui. Uma oitava stack provavelmente expõe uma lacuna de formato — persistência alcançada de um jeito que o padrão escrito não prevê — e o modo de falha perigoso é o PASS silencioso, não o erro. É o que `verification-recipes.md` tenta antecipar ao exigir que todo padrão novo seja validado contra uma violação conhecida antes de se confiar num PASS.
- A Fase 3 nunca foi executada num projeto externo. A evidência de que a refatoração preserva comportamento vem dos 3 projetos deste repositório, todos com suíte de validação escrita à mão.

---
