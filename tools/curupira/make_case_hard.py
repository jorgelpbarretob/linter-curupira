#!/usr/bin/env python3
"""Gera casos difíceis (tokens + legibilidade) para o estudo Hermes × Curupira.

Todos os insumos são sintéticos (nenhum conteúdo confidencial). Cada caso
carrega residual alto de CURUPIRA-PT-PONT-001 no input, para que o braço
controle deixe resíduo esperado. O objetivo de produto é baixar tokens de
entrada/saída e aumentar legibilidade; residual 0 no tratamento é gate,
não o único KPI.

Convenção do hash do pacote (documentada aqui para reprodução):
  package_sha256 = sha256( concatenação, ordenada por caminho relativo,
                           de "relpath\\x00bytes\\x00" de todos os arquivos
                           do diretório do caso, EXCETO manifest.json )

Uso:
  python3 tools/curupira/make_case_hard.py            # gera todos abaixo
  python3 tools/curupira/make_case_hard.py case-011   # gera um caso
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CASES = REPO / "cases"
RULE = "CURUPIRA-PT-PONT-001"
CREATED = "2026-08-17"

CASES_DEF: dict[str, dict] = {
    "case-011": {
        "type": "criacao-dificil",
        "title": "Criar procedimento CIP a partir de notas cruas de passagem de turno",
        "artifact_name": "procedimento-cip.md",
        "input_rel": "inputs/notas-turno.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-011 — criação com insumo cru e denso

## Objetivo de produto
Produzir um procedimento novo, enxuto e legível para o operador, baixando
tokens de leitura e de saída. Não é só passar no lint.

## Entrada
`notas-turno.md` (notas cruas de passagem de turno, densas).

## Entregar
Procedimento novo em `procedimento-cip.md`.

## Pronto quando
1. Tags preservadas: CIP-3, XV-210, P-301, TI-77.
2. Ordem lógica: preparação, circulação alcalina, enxágue, verificação.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Texto final com menos caracteres de prosa que o equivalente reescrito
   literalmente das notas.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente concentrações, temperaturas ou tempos fora das notas.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-011

- [ ] Tags CIP-3, XV-210, P-301, TI-77 presentes
- [ ] Ordem: preparação → circulação alcalina → enxágue → verificação
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Passos acionáveis (lista ou sentenças curtas)
- [ ] Sem valores inventados além das notas
""",
        "acceptance": """# Acceptance tests case-011

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
""",
        "input": """# Passagem de turno — CIP-3

Operador relata que o CIP-3 terminou a circulação alcalina perto das 22h; a condutividade caiu dentro da faixa; porém ficou pendente confirmar o enxágue final porque o TI-77 oscilou durante a noite; ninguém anotou o valor final; verificar antes de liberar. A válvula XV-210 ficou em posição fechada conforme orientação do técnico; se a pressão subir na partida abrir devagar e observar o P-301; em caso de alarme parar a bomba e chamar o técnico de plantão. O tanque estava com nível baixo no início; completaram com água de processo; falta registrar o volume no formulário. Se o TI-77 voltar a oscilar repetir a leitura em outro ponto da linha antes de concluir que é falha do sensor; só depois escalar.
""",
    },
    "case-012": {
        "type": "regressao-dificil",
        "title": "Desdensificar SOP longo de mosturação com 10+ ponto e vírgula",
        "artifact_name": "sop-mosturacao.md",
        "input_rel": "inputs/sop-mosturacao.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-012 — regressão difícil em SOP longo

## Objetivo de produto
Baixar custo de tokens da sessão e deixar o texto mais legível para o
operador. Não é só passar no lint.

## Entrada
`sop-mosturacao.md` (SOP longo, denso, com muitos ponto e vírgula).

## Entregar
O mesmo arquivo, pronto para chão de fábrica.

## Pronto quando
1. Tags preservadas: TT-41, P-12, XV-55, FQ-09, TIC-70.
2. Mesma ordem lógica: pré-aquecimento, mistura, rampas, filtração.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Sem parágrafo denso com múltiplas ordens escondidas.
6. Texto final preferencialmente mais curto que o input em caracteres de prosa.
7. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente interlocks, setpoints ou pessoas.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-012

- [ ] Tags TT-41, P-12, XV-55, FQ-09, TIC-70 presentes
- [ ] Ordem: pré-aquecimento → mistura → rampas → filtração
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Passos acionáveis (lista ou sentenças curtas)
- [ ] Sem setpoints numéricos inventados além dos citados no SOP
""",
        "acceptance": """# Acceptance tests case-012

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
""",
        "input": """# SOP — mosturação completa da linha A

Antes de iniciar, confirme no painel que o tanque de mistura está vazio e que a linha de retorno está fechada; registre o horário no quadro de turno. Ligue o pré-aquecimento e acompanhe TT-41 até a faixa indicada no cartão da área; se a temperatura passar da faixa, reduza o vapor manualmente e aguarde estabilizar antes de seguir; não force a rampa. Com a água na faixa, acione P-12 para iniciar a mistura do malte; ajuste a vazão conforme o FQ-09 indica no totalizador; observe a corrente do motor e, se subir acima do marcado na etiqueta, reduza a alimentação e comunique o líder do turno. Durante as rampas, ajuste TIC-70 somente dentro dos limites do cartão; qualquer alteração fora do cartão exige autorização do responsável da sala de brassagem; anote o motivo no registro. Ao terminar a última rampa, abra XV-55 para transferência; confirme que o fluxo chega ao filtro antes de desligar P-12; se houver bloqueio na linha, feche XV-55 e drene pelo ponto indicado antes de tentar novamente. Finalize conferindo os registros de TT-41, FQ-09 e TIC-70; assinale o quadro de turno; mantenha a área limpa e livre de mangueiras atravessadas na passagem.
""",
    },
    "case-013": {
        "type": "transformacao-dificil",
        "title": "Converter notas sanitizadas com horários em procedimento Markdown",
        "artifact_name": "procedimento-sanitizacao.md",
        "input_rel": "inputs/notas-sanitizacao.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-013 — transformação de notas em procedimento

## Objetivo de produto
Transformar notas soltas em procedimento enxuto e legível, baixando tokens
de leitura. Não é só passar no lint.

## Entrada
`notas-sanitizacao.md` (notas de sanitização com horários e tags).

## Entregar
Procedimento em `procedimento-sanitizacao.md`.

## Pronto quando
1. Tags preservadas: SD-8, XV-302, P-410, CT-15.
2. Horários das notas preservados como referência.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Texto final mais curto em caracteres de prosa que as notas.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente etapas ausentes nas notas.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-013

- [ ] Tags SD-8, XV-302, P-410, CT-15 presentes
- [ ] Horários 06:10, 06:40 e 07:05 preservados como referência
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Passos acionáveis (lista ou sentenças curtas)
- [ ] Sem etapas inventadas além das notas
""",
        "acceptance": """# Acceptance tests case-013

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
""",
        "input": """Notas sanitização SD-8 (turno manhã):

06:10 início circulação; XV-302 fechada antes de partir P-410; pressão ok no CT-15; sem vazamentos visíveis. 06:40 troca de solução conforme ficha; operador confirmou concentração no rótulo; enxágue começou logo depois; condutividade ainda alta na primeira medição; repetir até cair dentro da faixa conforme praxe do setor. 07:05 fim do ciclo; liberar SD-8 para envase somente após assinatura do responsável; se alguém abrir XV-302 antes disso, repetir o enxágue e registrar o ocorro no boletim. Obs.: mangueira auxiliar ficou fora do suporte; guardar após o uso para não atrapalhar a passagem.
""",
    },
    "case-014": {
        "type": "revisao-dificil",
        "title": "Corrigir ambiguidade e ponto e vírgula preservando fatos",
        "artifact_name": "instrucao-transferencia.md",
        "input_rel": "inputs/instrucao-transferencia.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-014 — revisão difícil com referência ambígua

## Objetivo de produto
Corrigir ambiguidade e reduzir densidade sem mudar fatos técnicos. Baixar
tokens de leitura. Não é só passar no lint.

## Entrada
`instrucao-transferencia.md` (contém referências ambíguas e ponto e vírgula).

## Entregar
O mesmo arquivo revisado.

## Pronto quando
1. Tags preservadas: TK-2, TK-7, XV-88, P-60.
2. Toda referência ambígua a "o mesmo", "deste" ou "da linha" esclarecida
   pelo nome do equipamento.
3. Todos os fatos técnicos preservados.
4. Sem ponto e vírgula em prosa.
5. Texto final sem crescer mais que 10% em caracteres de prosa.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não invente fatos novos.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-014

- [ ] Tags TK-2, TK-7, XV-88, P-60 presentes
- [ ] Zero ocorrência de "o mesmo", "deste" e "da linha" como referência ambígua
- [ ] Fatos técnicos preservados
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Crescimento de prosa <= 10%
""",
        "acceptance": """# Acceptance tests case-014

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
grep -ciE 'o mesmo|deste' ARTIFACT   # esperado: 0
```
""",
        "input": """# Instrução — transferência entre tanques

Antes de transferir, verifique o nível do mesmo no visor e confirme se o destino está apto a receber o volume; caso o mesmo apresente espuma excessiva, aguarde baixar. Abra XV-88 somente depois de ligar P-60; se a vazão deste cair de forma súbita, interrompa e verifique a linha; o mesmo procedimento vale para a transferência inversa. Ao concluir, feche XV-88 antes de desligar P-60; registre o volume transferido no boletim do mesmo turno. Qualquer anomalia na leitura deste deve ser comunicada ao responsável antes de repetir a operação da linha.
""",
    },
    "case-015": {
        "type": "atualizacao-dificil",
        "title": "Atualizar runbook após troca de tag XV-201 para XV-205",
        "artifact_name": "runbook-envase.md",
        "input_rel": "inputs/runbook-envase.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-015 — atualização difícil de runbook

## Objetivo de produto
Aplicar a mudança de tag e enxugar o texto, baixando tokens de leitura.
Não é só passar no lint.

## Mudança definida
A válvula XV-201 foi substituída pela XV-205 no projeto. Todo o runbook deve
referenciar XV-205. O passo de confirmação de posição no painel foi removido
do projeto e deve sair do runbook.

## Entrada
`runbook-envase.md`.

## Entregar
O mesmo arquivo atualizado.

## Pronto quando
1. Nenhuma referência restante a XV-201.
2. Tags preservadas: XV-205, P-77, FS-12.
3. Passo de confirmação de posição no painel removido.
4. Sem ponto e vírgula em prosa.
5. Texto final mais curto que o input em caracteres de prosa.
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não altere nenhum outro fato técnico.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-015

- [ ] Zero referência a XV-201
- [ ] Tags XV-205, P-77, FS-12 presentes
- [ ] Passo de confirmação de posição no painel removido
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Demais fatos técnicos preservados
""",
        "acceptance": """# Acceptance tests case-015

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
grep -c 'XV-201' ARTIFACT   # esperado: 0
grep -c 'XV-205' ARTIFACT   # esperado: >= 1
```
""",
        "input": """# Runbook — partida do envase

Confirme a posição da válvula no painel antes de prosseguir; este passo evita partida com caminho fechado. Abra XV-201 devagar e observe FS-12 indicar fluxo; se o fluxo não aparecer em dois minutos, feche XV-201 e verifique o filtro da linha antes de repetir. Ligue P-77 somente com FS-12 marcando fluxo; ajuste a velocidade conforme a etiqueta do inversor; não ultrapasse o valor máximo marcado. Durante o envase, acompanhe o nível pelo visor; se houver transbordo, desligue P-77 e feche XV-201 antes de limpar a área. Ao final, feche XV-201, desligue P-77 e registre a leitura de FS-12 no boletim; mantenha o caminho livre para o próximo turno.
""",
    },
    "case-016": {
        "type": "incidente-dificil",
        "title": "Produzir instrução curta de mitigação a partir de timeline densa",
        "artifact_name": "mitigacao-parada.md",
        "input_rel": "inputs/timeline-incidente.md",
        "product_goals": [
            "lower_session_tokens",
            "operator_readability",
            "residual_lint",
        ],
        "task": """# Tarefa case-016 — mitigação a partir de timeline densa

## Objetivo de produto
Produzir uma instrução de mitigação curta e direta, bem mais curta que a
timeline. Baixar tokens de saída é meta explícita. Não é só passar no lint.

## Entrada
`timeline-incidente.md` (timeline sanitizada de incidente).

## Entregar
Instrução de mitigação em `mitigacao-parada.md`.

## Pronto quando
1. Tags preservadas: PS-9, XV-140, P-52, LS-03.
2. Instrução com no máximo 50% dos caracteres de prosa da timeline.
3. Frases curtas. Uma ação principal por passo quando possível.
4. Sem ponto e vírgula em prosa.
5. Sem inferência além da timeline (causas não confirmadas não entram).
6. Braço com Curupira: `curupira lint` exit 0 nas regras do aceite.

## Restrições
- Não especule causa raiz.
- Não envie a APIs.
""",
        "requirements": """# Requisitos case-016

- [ ] Tags PS-9, XV-140, P-52, LS-03 presentes
- [ ] Prosa final <= 50% dos caracteres de prosa da timeline
- [ ] Zero ponto e vírgula em prosa lintável
- [ ] Passos acionáveis (lista ou sentenças curtas)
- [ ] Sem causa raiz especulada
""",
        "acceptance": """# Acceptance tests case-016

```bash
curupira lint ARTIFACT --enable-rule CURUPIRA-PT-PONT-001 --format json
test $? -eq 0
```
""",
        "input": """# Timeline sanitizada — parada da linha 3 (14:22 a 15:10)

14:22 alarme de pressão alta em PS-9; operador reduziu a carga; o alarme persistiu por dois minutos. 14:25 P-52 parou por proteção; XV-140 permaneceu aberta; fluxo seguiu para o dreno conforme desenho. 14:28 supervisor acionado por rádio; orientação foi isolar XV-140 e aguardar leitura de PS-9 estabilizar. 14:35 PS-9 voltou à faixa normal; LS-03 indicou nível baixo no tanque de amortecimento; completado o nível com água de processo conforme praxe. 14:50 tentativa de partida com carga reduzida; P-52 ligou sem novo alarme; XV-140 aberta devagar com acompanhamento local. 14:58 fluxo normalizado no indicador; operador permaneceu na área por dez minutos observando PS-9. 15:10 linha liberada para produção; pendência registrada: inspeção do sensor PS-9 na próxima parada programada; nenhuma causa raiz confirmada até o fechamento deste registro.
""",
    },
}


def lint_residual(path: Path) -> tuple[int, int]:
    proc = subprocess.run(
        ["curupira", "lint", str(path), "--enable-rule", RULE, "--format", "json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
        diags = payload.get("diagnostics") or []
    except json.JSONDecodeError:
        diags = []
    return int(proc.returncode), len(diags)


def package_sha256(case_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(case_dir.rglob("*")):
        if f.is_file() and f.name != "manifest.json":
            rel = f.relative_to(case_dir).as_posix()
            h.update(rel.encode() + b"\x00" + f.read_bytes() + b"\x00")
    return h.hexdigest()


def build_case(cid: str) -> None:
    d = CASES_DEF[cid]
    case_dir = CASES / cid
    (case_dir / "inputs").mkdir(parents=True, exist_ok=True)
    input_path = case_dir / d["input_rel"]
    input_path.write_text(d["input"], encoding="utf-8")
    (case_dir / "task.md").write_text(d["task"], encoding="utf-8")
    (case_dir / "expected-requirements.md").write_text(d["requirements"], encoding="utf-8")
    (case_dir / "acceptance-tests.md").write_text(d["acceptance"], encoding="utf-8")
    (case_dir / "artifact-name.txt").write_text(d["artifact_name"] + "\n", encoding="utf-8")

    exit_code, residual = lint_residual(input_path)
    chars = len(d["input"])
    manifest = {
        "schema_version": "hermes-case-study-case/v1",
        "case_id": cid,
        "type": d["type"],
        "title": d["title"],
        "provenance": "synthetic",
        "language": "pt-BR",
        "package_sha256": None,
        "artifact_name": d["artifact_name"],
        "input_rel": d["input_rel"],
        "product_goals": d["product_goals"],
        "input_residual_findings_n": residual,
        "input_residual_lint_exit": exit_code,
        "input_chars": chars,
        "curupira_rules_in_acceptance": [RULE],
        "curupira_version_target": "0.3.0",
        "created_at": CREATED,
        "status": "frozen-draft",
        "difficulty": "hard",
        "package_hash_convention": "sha256(sorted relpath\\x00bytes\\x00, excluding manifest.json)",
        "notes": "Sucesso primário: tokens de sessão e legibilidade. Residual 0 no tratamento é gate, não o único KPI.",
    }
    (case_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["package_sha256"] = package_sha256(case_dir)
    (case_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{cid}: residual={residual} exit={exit_code} chars={chars} "
        f"sha256={manifest['package_sha256'][:16]}..."
    )


def main() -> int:
    targets = sys.argv[1:] or list(CASES_DEF)
    for cid in targets:
        if cid not in CASES_DEF:
            print(f"caso desconhecido: {cid}", file=sys.stderr)
            return 2
        build_case(cid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
