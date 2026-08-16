#!/usr/bin/env python3
"""Build and validate the model-blind PT4 offset corpus proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL_PATH = PROJECT_ROOT / "corpus/hermes/pt4/pt4-offset-development-proposal-v2.jsonl"
PROPOSAL_HASH_PATH = PROPOSAL_PATH.with_suffix(".jsonl.sha256")
SCHEMA_VERSION = "hermes-pt4-offset-corpus/v2"
EXPECTED_PER_FAMILY = 40
EXPECTED_CASES = 160
PANEL_MODELS = {
    "maritaca": "sabia-4-thinking",
    "grok": "grok-4.6",
    "kimi": "kimi-k2.7-code:cloud",
}
VOTE_SCHEMA_VERSION = "hermes-pt4-model-vote/v1"
REVIEWED_ON = "2026-08-16"


class CorpusError(RuntimeError):
    """Raised when a corpus or review artifact violates the frozen contract."""


@dataclass(frozen=True)
class CaseSpec:
    family: str
    text: str
    analyzed: tuple[str, ...]
    rationale: str
    source_format: str = "txt"
    protected: tuple[str, ...] = ()
    expansions: tuple[tuple[str, tuple[str, ...]], ...] = ()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _word_char(character: str) -> bool:
    return character == "_" or unicodedata.category(character)[0] in {"L", "M", "N"}


def tokenize(text: str, start: int, end: int, protected: tuple[str, ...]) -> list[dict[str, Any]]:
    tokens: list[dict[str, Any]] = []
    ordered_protected = sorted(set(protected), key=len, reverse=True)
    cursor = start
    while cursor < end:
        if text[cursor].isspace():
            cursor += 1
            continue
        protected_form = next(
            (form for form in ordered_protected if text.startswith(form, cursor)), None
        )
        if protected_form is not None:
            past_last = cursor + len(protected_form)
        elif _word_char(text[cursor]):
            past_last = cursor + 1
            while past_last < end:
                character = text[past_last]
                if _word_char(character):
                    past_last += 1
                    continue
                if (
                    character in {"-", "‑", "’", "'"}
                    and past_last + 1 < end
                    and _word_char(text[past_last + 1])
                ):
                    past_last += 1
                    continue
                break
        else:
            past_last = cursor + 1
        tokens.append({"text": text[cursor:past_last], "start": cursor, "end": past_last})
        cursor = past_last
    return tokens


def locate_in_order(text: str, fragments: tuple[str, ...]) -> list[tuple[int, int]]:
    located: list[tuple[int, int]] = []
    cursor = 0
    for fragment in fragments:
        start = text.find(fragment, cursor)
        if start < 0:
            raise CorpusError(f"analysis fragment not found in order: {fragment!r}")
        end = start + len(fragment)
        located.append((start, end))
        cursor = end
    return located


def build_case(spec: CaseSpec, number: int) -> dict[str, Any]:
    case_id = f"pt4-offset-dev-{number:03d}"
    segments = locate_in_order(spec.text, spec.analyzed)
    surface_tokens: list[dict[str, Any]] = []
    sentences: list[dict[str, int]] = []
    for segment_index, (segment_start, segment_end) in enumerate(segments):
        first_token = len(surface_tokens)
        segment_tokens = tokenize(spec.text, segment_start, segment_end, spec.protected)
        for token in segment_tokens:
            token["segment_index"] = segment_index
        surface_tokens.extend(segment_tokens)
        if segment_tokens:
            sentences.append(
                {
                    "start": segment_tokens[0]["start"],
                    "end": segment_tokens[-1]["end"],
                    "first_surface_token": first_token,
                    "past_last_surface_token": len(surface_tokens),
                }
            )

    expansion_map = dict(spec.expansions)
    syntactic_words: list[dict[str, Any]] = []
    for surface_index, token in enumerate(surface_tokens):
        forms = expansion_map.get(token["text"], (token["text"],))
        for form in forms:
            syntactic_words.append({"form": form, "surface_token_index": surface_index})

    abstentions: list[dict[str, Any]] = []
    if spec.source_format == "markdown":
        cursor = 0
        for start, end in segments:
            if cursor < start and spec.text[cursor:start].strip():
                abstentions.append({"start": cursor, "end": start, "reason": "structural-markup"})
            cursor = end
        if cursor < len(spec.text) and spec.text[cursor:].strip():
            abstentions.append(
                {"start": cursor, "end": len(spec.text), "reason": "structural-markup"}
            )

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "family": spec.family,
        "language": "pt-BR",
        "partition": "development",
        "source_origin": "project-authored-synthetic",
        "license": "CC-BY-4.0",
        "source_format": spec.source_format,
        "text": spec.text,
        "analysis_segments": [{"start": start, "end": end} for start, end in segments],
        "abstention_spans": abstentions,
        "surface_tokens": surface_tokens,
        "sentences": sentences,
        "syntactic_words": syntactic_words,
        "rationale": spec.rationale,
        "review_status": "pending-model-panel",
        "reviewed_by": None,
        "reviewer_role": None,
        "reviewed_on": None,
        "decision_notes": "",
    }
    validate_case(record)
    return record


def validate_case(record: dict[str, Any]) -> None:
    text = record["text"]
    segments = record["analysis_segments"]
    abstentions = record["abstention_spans"]
    for kind, spans in (("analysis", segments), ("abstention", abstentions)):
        previous_end = 0
        for span in spans:
            if not 0 <= span["start"] < span["end"] <= len(text):
                raise CorpusError(f"{record['case_id']} has an invalid {kind} span")
            if span["start"] < previous_end:
                raise CorpusError(f"{record['case_id']} has overlapping {kind} spans")
            previous_end = span["end"]
    if any(
        max(segment["start"], abstention["start"]) < min(segment["end"], abstention["end"])
        for segment in segments
        for abstention in abstentions
    ):
        raise CorpusError(f"{record['case_id']} has overlapping analysis and abstention spans")

    tokens = record["surface_tokens"]
    for index, token in enumerate(tokens):
        if text[token["start"] : token["end"]] != token["text"]:
            raise CorpusError(f"{record['case_id']} token {index} has an invalid slice")
        if index and tokens[index - 1]["end"] > token["start"]:
            raise CorpusError(f"{record['case_id']} has overlapping tokens")
        segment_index = token["segment_index"]
        if not 0 <= segment_index < len(segments):
            raise CorpusError(f"{record['case_id']} token {index} has an invalid segment")
        segment = segments[segment_index]
        if not segment["start"] <= token["start"] < token["end"] <= segment["end"]:
            raise CorpusError(f"{record['case_id']} token {index} leaves its segment")
    for sentence in record["sentences"]:
        first = sentence["first_surface_token"]
        past_last = sentence["past_last_surface_token"]
        if not 0 <= first < past_last <= len(tokens):
            raise CorpusError(f"{record['case_id']} has an invalid sentence range")
        if sentence["start"] != tokens[first]["start"]:
            raise CorpusError(f"{record['case_id']} has an invalid sentence start")
        if sentence["end"] != tokens[past_last - 1]["end"]:
            raise CorpusError(f"{record['case_id']} has an invalid sentence end")
    for word in record["syntactic_words"]:
        if not 0 <= word["surface_token_index"] < len(tokens):
            raise CorpusError(f"{record['case_id']} has an orphan syntactic word")
    status = record["review_status"]
    if status == "pending-model-panel":
        if any(
            record[field] is not None for field in ("reviewed_by", "reviewer_role", "reviewed_on")
        ):
            raise CorpusError(f"{record['case_id']} pending proposal has review metadata")
    elif status == "model-panel-approved":
        if record["reviewer_role"] != "three-model-panel" or not all(
            isinstance(record[field], str) and record[field].strip()
            for field in ("reviewed_by", "reviewed_on", "decision_notes")
        ):
            raise CorpusError(f"{record['case_id']} has invalid panel approval metadata")
    else:
        raise CorpusError(f"{record['case_id']} has invalid review status")


def unicode_specs() -> list[CaseSpec]:
    cases = [
        (
            "A pressão está estável.",
            ("A pressão está estável.",),
            "Diacríticos portugueses compostos.",
        ),
        (
            "A pressão está estável.",
            ("A pressão está estável.",),
            "Cedilha e til combinante preservados.",
        ),
        (
            "O teor de H₂S é baixo.",
            ("O teor de H₂S é baixo.",),
            "Subscrito Unicode em fórmula química.",
        ),
        (
            "A válvula está fechada 🔒.",
            ("A válvula está fechada 🔒.",),
            "Emoji adjacente à pontuação final.",
        ),
        (
            "O técnico confirmou 👍🏽 a leitura.",
            ("O técnico confirmou 👍🏽 a leitura.",),
            "Emoji com modificador de tom de pele.",
        ),
        (
            "O relatório Brasil 🇧🇷 foi anexado.",
            ("O relatório Brasil 🇧🇷 foi anexado.",),
            "Emoji de bandeira formado por dois indicadores.",
        ),
        (
            "A bomba parou.\nO alarme disparou.",
            ("A bomba parou.", "O alarme disparou."),
            "Duas sentenças separadas por LF.",
        ),
        (
            "A bomba parou.\r\nO alarme disparou.",
            ("A bomba parou.", "O alarme disparou."),
            "Duas sentenças separadas por CRLF.",
        ),
        (
            "A linha foi drenada.\n\nA tampa foi aberta.",
            ("A linha foi drenada.", "A tampa foi aberta."),
            "Parágrafo vazio com LF.",
        ),
        (
            "A linha foi drenada.\r\n\r\nA tampa foi aberta.",
            ("A linha foi drenada.", "A tampa foi aberta."),
            "Parágrafo vazio com CRLF.",
        ),
        ("O painel indica “PRONTO”.", ("O painel indica “PRONTO”.",), "Aspas curvas duplas."),
        (
            "A bomba — já isolada — foi removida.",
            ("A bomba — já isolada — foi removida.",),
            "Travessões Unicode internos.",
        ),
        (
            "A leitura oscilou… depois estabilizou.",
            ("A leitura oscilou… depois estabilizou.",),
            "Reticências em caractere único.",
        ),
        ("A folga é 25 µm.", ("A folga é 25 µm.",), "Sinal micro em unidade."),
        ("A corrente é 5 μA.", ("A corrente é 5 μA.",), "Letra grega mu em unidade."),
        (
            "A pressão é 10 MPa.",
            ("A pressão é 10 MPa.",),
            "Espaço não separável entre valor e unidade.",
        ),
        ("A força é 5 kN.", ("A força é 5 kN.",), "Espaço não separável estreito."),
        (
            "ÓLEO, ÁGUA E GÁS ESTÃO PRESENTES.",
            ("ÓLEO, ÁGUA E GÁS ESTÃO PRESENTES.",),
            "Maiúsculas acentuadas.",
        ),
        ("O óleo foi aquecido.", ("O óleo foi aquecido.",), "Acento agudo combinante."),
        (
            "A seção contém aço e solução.",
            ("A seção contém aço e solução.",),
            "Cedilha e vogais acentuadas compostas.",
        ),
        (
            "A equipe 👩🏽‍🔧 concluiu a inspeção.",
            ("A equipe 👩🏽‍🔧 concluiu a inspeção.",),
            "Sequência emoji com ZWJ.",
        ),
        (
            "O estado mudou de 0️⃣ para 1️⃣.",
            ("O estado mudou de 0️⃣ para 1️⃣.",),
            "Emoji keycap com seletor de variação.",
        ),
        (
            "\nA válvula permanece aberta.",
            ("A válvula permanece aberta.",),
            "LF inicial fora do envelope.",
        ),
        (
            "A válvula permanece aberta.\n",
            ("A válvula permanece aberta.",),
            "LF final fora do envelope.",
        ),
        (
            "A\tleitura\testá\tcorreta.",
            ("A\tleitura\testá\tcorreta.",),
            "Tabs internos preservados.",
        ),
        (
            "A diferença ΔP aumentou.",
            ("A diferença ΔP aumentou.",),
            "Letra grega em identificador técnico.",
        ),
        ("A área é 12 m².", ("A área é 12 m².",), "Expoente Unicode em unidade."),
        (
            "A camada pré‑sal foi perfurada.",
            ("A camada pré‑sal foi perfurada.",),
            "Hífen não separável em termo técnico.",
        ),
        (
            "A coluna d’água aumentou.",
            ("A coluna d’água aumentou.",),
            "Apóstrofo tipográfico interno.",
        ),
        ("O visor mostra «ATIVO».", ("O visor mostra «ATIVO».",), "Aspas angulares."),
        ("A vazão ficou ≤ 5 L/s.", ("A vazão ficou ≤ 5 L/s.",), "Operador menor ou igual."),
        ("A tolerância é ± 0,2 mm.", ("A tolerância é ± 0,2 mm.",), "Sinal mais ou menos."),
        ("A área mede 3 × 4 m.", ("A área mede 3 × 4 m.",), "Sinal de multiplicação."),
        ("O fluxo segue A → B.", ("O fluxo segue A → B.",), "Seta Unicode."),
        (
            "O sensor Acme® foi removido.",
            ("O sensor Acme® foi removido.",),
            "Marca registrada adjacente ao nome.",
        ),
        (
            "A mistura contém água & glicol.",
            ("A mistura contém água & glicol.",),
            "Ampersand em prosa técnica.",
        ),
        (
            "O alarme 🚨 exige resposta.",
            ("O alarme 🚨 exige resposta.",),
            "Emoji de alarme entre palavras.",
        ),
        (
            "A razão α/β foi registrada.",
            ("A razão α/β foi registrada.",),
            "Letras gregas separadas por barra.",
        ),
        (
            "O valor passou de −2 para +3.",
            ("O valor passou de −2 para +3.",),
            "Menos Unicode e mais ASCII.",
        ),
        (
            "A ação ‘medir’ foi concluída.",
            ("A ação ‘medir’ foi concluída.",),
            "Aspas simples tipográficas.",
        ),
    ]
    emoji_clusters = ("🔒", "👍🏽", "🇧🇷", "👩🏽‍🔧", "0️⃣", "1️⃣", "🚨")
    return [
        CaseSpec(
            "unicode-newlines",
            *case,
            protected=tuple(cluster for cluster in emoji_clusters if cluster in case[0]),
        )
        for case in cases
    ]


def mwt_specs() -> list[CaseSpec]:
    rows = [
        ("O selo do eixo vazou.", "do", ("de", "o")),
        ("A pressão da linha caiu.", "da", ("de", "a")),
        ("Os dados dos sensores chegaram.", "dos", ("de", "os")),
        ("As tampas das caixas fecharam.", "das", ("de", "as")),
        ("O óleo ficou no tanque.", "no", ("em", "o")),
        ("A chave ficou na bancada.", "na", ("em", "a")),
        ("A falha apareceu nos registros.", "nos", ("em", "os")),
        ("A umidade entrou nas caixas.", "nas", ("em", "as")),
        ("Envie o sinal ao painel.", "ao", ("a", "o")),
        ("Aplique o torque aos parafusos.", "aos", ("a", "os")),
        ("Retorne à plataforma.", "à", ("a", "a")),
        ("Entregue as chaves às equipes.", "às", ("a", "as")),
        ("O fluxo passou pelo filtro.", "pelo", ("por", "o")),
        ("A água passou pela válvula.", "pela", ("por", "a")),
        ("O cabo passou pelos suportes.", "pelos", ("por", "os")),
        ("A linha passou pelas bandejas.", "pelas", ("por", "as")),
        ("Há sedimento num tubo.", "num", ("em", "um")),
        ("Há pressão numa câmara.", "numa", ("em", "uma")),
        ("O valor aparece neste visor.", "neste", ("em", "este")),
        ("A falha surgiu nesta etapa.", "nesta", ("em", "esta")),
        ("Remova o selo deste eixo.", "deste", ("de", "este")),
        ("Registre a pressão desta linha.", "desta", ("de", "esta")),
        ("Afaste-se daquele painel.", "daquele", ("de", "aquele")),
        ("A etiqueta dele rasgou.", "dele", ("de", "ele")),
        ("Verifica-se a pressão.", "Verifica-se", ("Verifica", "se")),
        ("Pode-se fechar a linha.", "Pode-se", ("Pode", "se")),
        ("Deve-se registrar a leitura.", "Deve-se", ("Deve", "se")),
        ("Encontrou-se uma fissura.", "Encontrou-se", ("Encontrou", "se")),
        ("Analisou-se a amostra.", "Analisou-se", ("Analisou", "se")),
        ("Realizou-se o teste.", "Realizou-se", ("Realizou", "se")),
        ("Mede-se a vazão.", "Mede-se", ("Mede", "se")),
        ("Mantenha-o isolado.", "Mantenha-o", ("Mantenha", "o")),
        ("Meça-a novamente.", "Meça-a", ("Meça", "a")),
        ("Feche-a lentamente.", "Feche-a", ("Feche", "a")),
        ("Informe-o sobre a falha.", "Informe-o", ("Informe", "o")),
        ("Dê-lhe acesso ao painel.", "Dê-lhe", ("Dê", "lhe")),
        ("Envie-lhe o relatório.", "Envie-lhe", ("Envie", "lhe")),
        ("Aplique-as na superfície.", "Aplique-as", ("Aplique", "as")),
        ("Tornou-se instável.", "Tornou-se", ("Tornou", "se")),
        ("Observam-se duas falhas.", "Observam-se", ("Observam", "se")),
    ]
    secondary_expansions = {
        "Afaste-se daquele painel.": (("Afaste-se", ("Afaste", "se")),),
        "Dê-lhe acesso ao painel.": (("ao", ("a", "o")),),
        "Aplique-as na superfície.": (("na", ("em", "a")),),
    }
    return [
        CaseSpec(
            "contractions-clitics",
            text,
            (text,),
            f"Expansão explícita do token de superfície {surface!r}.",
            expansions=((surface, words), *secondary_expansions.get(text, ())),
        )
        for text, surface, words in rows
    ]


def technical_specs() -> list[CaseSpec]:
    rows = [
        ("Instale a versão v2.4.1.", "v2.4.1", "Versão semântica."),
        ("A pressão é 12,5 MPa.", "12,5", "Decimal com vírgula."),
        ("Inspecione a plataforma P-35.", "P-35", "Identificador com hífen."),
        ("Feche a válvula XV-204.", "XV-204", "Tag de instrumento."),
        ("Use a especificação API-6A.", "API-6A", "Código de especificação."),
        ("Consulte a norma ISO-9001:2015.", "ISO-9001:2015", "Norma com ano."),
        ("Veja a Fig. 2.", "Fig.", "Abreviação antes de numeral."),
        ("Use o item N.º 7.", "N.º", "Abreviação com ordinal."),
        ("Remova poeira, óleo etc.", "etc.", "Abreviação no fim da sentença."),
        ("O Dr. Lima aprovou o laudo.", "Dr.", "Título abreviado."),
        ("A concentração é 30 mg/L.", "mg/L", "Unidade composta por barra."),
        ("O pico ocorreu em 1200 cm⁻¹.", "cm⁻¹", "Unidade com expoente negativo."),
        ("A densidade é 850 kg/m³.", "kg/m³", "Unidade com volume cúbico."),
        ("A vazão é 40 m³/d.", "m³/d", "Unidade de vazão."),
        ("A temperatura chegou a 80 °C.", "°C", "Grau Celsius."),
        ("O gás contém CO₂.", "CO₂", "Fórmula química com subscrito."),
        ("O detector mede H₂S.", "H₂S", "Fórmula química técnica."),
        ("O pH ficou em 7,2.", "pH", "Símbolo com caixa mista."),
        ("O custo foi R$ 120,00.", "R$", "Símbolo monetário brasileiro."),
        ("O desconto é 10%.", "10%", "Percentual adjacente."),
        ("Use um tubo de 3/4 pol.", "3/4", "Fração técnica."),
        ("O motor opera a 1.250 rpm.", "1.250", "Milhar com ponto."),
        ("A faixa é 10–12 MPa.", "10–12", "Intervalo com en dash."),
        ("A tolerância é ±0,2 mm.", "±0,2", "Tolerância compacta."),
        ("Mantenha a vazão ≤5 L/s.", "≤5", "Limite sem espaço."),
        ("Use o arquivo config.yaml.", "config.yaml", "Nome de arquivo."),
        ("Execute /opt/hermes/bin.", "/opt/hermes/bin", "Caminho POSIX."),
        ("Ative a opção --no-index.", "--no-index", "Opção de linha de comando."),
        ("Registre o código ERR-PT4-017.", "ERR-PT4-017", "Código de erro."),
        ("Compare sha256:abcd1234.", "sha256:abcd1234", "Prefixo de hash."),
        ("Use o endereço 192.0.2.10.", "192.0.2.10", "Endereço IPv4 de documentação."),
        ("Acesse https://exemplo.invalid/api.", "https://exemplo.invalid/api", "URL reservada."),
        ("Calcule ΔP=2,1 MPa.", "ΔP", "Símbolo de variável."),
        ("A razão A/B aumentou.", "A/B", "Razão técnica por barra."),
        ("Instale a conexão NPT-1/2.", "NPT-1/2", "Rosca com fração."),
        ("A revisão ocorreu em 2026-08-16.", "2026-08-16", "Data ISO."),
        ("O teste começou às 03:45.", "03:45", "Hora de 24 horas."),
        ("Aplique a Rev. C.", "Rev.", "Identificador de revisão."),
        ("Consulte a seção 3.2.1.", "3.2.1", "Número de seção."),
        ("Leia o sensor PT-100A.", "PT-100A", "Tag alfanumérica."),
    ]
    secondary_protected = {
        "O pH ficou em 7,2.": ("7,2",),
        "O custo foi R$ 120,00.": ("120,00",),
        "Mantenha a vazão ≤5 L/s.": ("L/s",),
        "Calcule ΔP=2,1 MPa.": ("2,1",),
    }
    return [
        CaseSpec(
            "technical-tokens",
            text,
            (text,),
            rationale,
            protected=(protected, *secondary_protected.get(text, ())),
        )
        for text, protected, rationale in rows
    ]


def structural_specs() -> list[CaseSpec]:
    rows: list[tuple[str, tuple[str, ...], str]] = [
        (
            "# Operação\n\nA bomba está ativa.",
            ("Operação", "A bomba está ativa."),
            "Heading e parágrafo.",
        ),
        (
            "- Feche a válvula.\n- Trave o painel.",
            ("Feche a válvula.", "Trave o painel."),
            "Lista com marcadores.",
        ),
        (
            "1. Meça a pressão.\n2. Registre o valor.",
            ("Meça a pressão.", "Registre o valor."),
            "Lista numerada.",
        ),
        (
            "```sh\necho teste\n```\nA saída foi salva.",
            ("A saída foi salva.",),
            "Fence de código abstido.",
        ),
        (
            "Use `modo seguro` durante o teste.",
            (),
            "Código inline exige contexto descontínuo; caso abstido.",
        ),
        (
            "Leia [o procedimento](guia.md) antes do teste.",
            (),
            "Link fragmenta a sentença; caso abstido.",
        ),
        (
            "![Diagrama da bomba](bomba.png)\nA bomba está parada.",
            ("A bomba está parada.",),
            "Imagem abstida e parágrafo completo analisável.",
        ),
        (
            "> A linha está isolada.\n\nConfirme a etiqueta.",
            ("A linha está isolada.", "Confirme a etiqueta."),
            "Citação e parágrafo.",
        ),
        ("| Item | Estado |\n|---|---|\n| Bomba | Ativa |", (), "Tabela inteira abstida."),
        (
            "---\ntitle: Teste\n---\nA inspeção começou.",
            ("A inspeção começou.",),
            "Frontmatter abstido.",
        ),
        (
            "<!-- nota interna -->\nA válvula foi fechada.",
            ("A válvula foi fechada.",),
            "Comentário HTML abstido.",
        ),
        ("<span>Alarme ativo.</span>", ("Alarme ativo.",), "Tags HTML delimitam texto."),
        (
            "A linha foi drenada.\n---\nA tampa foi aberta.",
            ("A linha foi drenada.", "A tampa foi aberta."),
            "Regra temática separa parágrafos.",
        ),
        (
            "    comando --teste\n\nO comando terminou.",
            ("O comando terminou.",),
            "Código indentado abstido.",
        ),
        (
            "- [ ] Verifique o selo.\n- [x] Registre a pressão.",
            ("Verifique o selo.", "Registre a pressão."),
            "Checklist Markdown.",
        ),
        (
            "- Sistema\n  - Bomba ativa.\n  - Válvula fechada.",
            ("Sistema", "Bomba ativa.", "Válvula fechada."),
            "Lista aninhada.",
        ),
        ("Termo\n: Definição técnica.", ("Termo", "Definição técnica."), "Lista de definição."),
        ("A *pressão* aumentou.", (), "Ênfase fragmenta a sentença; caso abstido."),
        (
            "A **bomba principal** parou.",
            (),
            "Negrito fragmenta a sentença; caso abstido.",
        ),
        (
            "O valor ~~antigo~~ foi removido.",
            (),
            "Tachado fragmenta a sentença; caso abstido.",
        ),
        (
            r"Use \* literalmente no campo.",
            (),
            "Escape estrutural exige projeção específica; caso abstido.",
        ),
        (
            "~~~text\ndado bruto\n~~~\nA análise terminou.",
            ("A análise terminou.",),
            "Fence com til abstido.",
        ),
        (
            "Consulte <https://exemplo.invalid>.",
            (),
            "Autolink fragmenta a sentença; caso abstido.",
        ),
        (
            "A bomba parou.  \nO alarme tocou.",
            ("A bomba parou.", "O alarme tocou."),
            "Quebra de linha forçada.",
        ),
        (
            "A bomba parou.\r\n\r\nO alarme tocou.",
            ("A bomba parou.", "O alarme tocou."),
            "Parágrafos Markdown com CRLF.",
        ),
        (
            "A bomba parou.\n\n\nO alarme tocou.",
            ("A bomba parou.", "O alarme tocou."),
            "Múltiplas linhas vazias.",
        ),
        ("## Pressão do sistema", ("Pressão do sistema",), "Heading sem parágrafo."),
        ("```python\nprint('x')\n```", (), "Documento apenas com código."),
        ("| A | B |\n|---|---|\n| 1 | 2 |", (), "Documento apenas com tabela."),
        ("---\ntitle: Apenas metadados\n---", (), "Documento apenas com frontmatter."),
        (
            "<pre>valor bruto</pre>\nA leitura foi aceita.",
            ("A leitura foi aceita.",),
            "Bloco HTML abstido.",
        ),
        (
            "> Confirme o nível.\n\nDepois, feche a tampa.",
            ("Confirme o nível.", "Depois, feche a tampa."),
            "Citação seguida por prosa.",
        ),
        (
            "Operação\n========\nA bomba está pronta.",
            ("Operação", "A bomba está pronta."),
            "Heading Setext.",
        ),
        (
            "- Feche a válvula.\n  Registre a hora.",
            ("Feche a válvula.", "Registre a hora."),
            "Continuação de item.",
        ),
        (
            '```json\n{"ok": true}\n```\nO arquivo é válido.',
            ("O arquivo é válido.",),
            "Fence com linguagem.",
        ),
        (
            'Leia [o guia](guia.md "Guia") agora.',
            (),
            "Link com título fragmenta a sentença; caso abstido.",
        ),
        (
            "A pressão subiu.[^1]\n\n[^1]: Valor calibrado.",
            ("A pressão subiu.", "Valor calibrado."),
            "Referência e nota de rodapé.",
        ),
        (
            "=== SEÇÃO A ===\nA bomba está ativa.\n=== FIM ===",
            ("A bomba está ativa.",),
            "Delimitadores em TXT.",
        ),
        (
            "AVISO: A linha está pressurizada.",
            ("AVISO: A linha está pressurizada.",),
            "Rótulo técnico em TXT.",
        ),
        (
            "# Estado\r\n\r\nA válvula está aberta.\r\n",
            ("Estado", "A válvula está aberta."),
            "Markdown com CRLF final.",
        ),
    ]
    return [
        CaseSpec("markdown-boundaries", text, analyzed, rationale, "markdown")
        for text, analyzed, rationale in rows
    ]


def build_records() -> list[dict[str, Any]]:
    specs = unicode_specs() + mwt_specs() + technical_specs() + structural_specs()
    if len(specs) != EXPECTED_CASES:
        raise CorpusError(f"expected {EXPECTED_CASES} case specs, got {len(specs)}")
    records = [build_case(spec, number) for number, spec in enumerate(specs, start=1)]
    counts = Counter(record["family"] for record in records)
    if set(counts.values()) != {EXPECTED_PER_FAMILY} or len(counts) != 4:
        raise CorpusError(f"unbalanced corpus families: {dict(counts)}")
    if len({record["case_id"] for record in records}) != len(records):
        raise CorpusError("duplicate case_id")
    return records


def canonical_record(record: dict[str, Any]) -> bytes:
    return (
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def proposal_bytes(records: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_record(record) for record in records)


def write_proposal(records: list[dict[str, Any]]) -> dict[str, Any]:
    payload = proposal_bytes(records)
    PROPOSAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROPOSAL_PATH.write_bytes(payload)
    digest = sha256_bytes(payload)
    PROPOSAL_HASH_PATH.write_text(
        f"{digest}  {PROPOSAL_PATH.name}\n", encoding="utf-8", newline="\n"
    )
    return {
        "case_count": len(records),
        "family_counts": dict(Counter(record["family"] for record in records)),
        "proposal_sha256": digest,
    }


def ensure_external_output(path: Path) -> None:
    resolved = path.resolve()
    if resolved == PROJECT_ROOT or resolved.is_relative_to(PROJECT_ROOT):
        raise CorpusError("the model-panel packet must remain outside the repository")


def model_vote_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "provider",
            "model_requested",
            "model_returned",
            "proposal_sha256",
            "verdict",
            "cases",
            "confirmed_boundaries",
        ],
        "properties": {
            "schema_version": {"const": VOTE_SCHEMA_VERSION},
            "provider": {"enum": list(PANEL_MODELS)},
            "model_requested": {"type": "string"},
            "model_returned": {"type": "string"},
            "proposal_sha256": {"type": "string"},
            "verdict": {"enum": ["approve", "change_required", "reject"]},
            "cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "case_id",
                        "decision",
                        "severity",
                        "fields",
                        "rationale",
                        "proposed_change",
                    ],
                    "properties": {
                        "case_id": {"type": "string"},
                        "decision": {"enum": ["approve", "change_required"]},
                        "severity": {"enum": ["none", "minor", "major", "blocker"]},
                        "fields": {"type": "array", "items": {"type": "string"}},
                        "rationale": {"type": "string"},
                        "proposed_change": {"type": "string"},
                    },
                },
            },
            "confirmed_boundaries": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "candidate_outputs_seen",
                    "pont_001_data_seen",
                    "inference_authorized",
                ],
                "properties": {
                    "candidate_outputs_seen": {"const": False},
                    "pont_001_data_seen": {"const": False},
                    "inference_authorized": {"const": False},
                },
            },
        },
    }


def panel_prompt() -> str:
    return (
        "Você é um revisor isolado de corpus pt-BR. Revise os 160 registros do arquivo "
        "JSONL fornecido sem ferramentas, web, memória, saída de candidato ou dados "
        "PONT-001. Para cada caso, verifique texto, segmentos, abstenções, slices Unicode "
        "por índice de code point Python, tokens de superfície, envelopes de sentença, "
        "expansões sintáticas e consistência entre casos equivalentes. Preserve exatamente "
        "os case_id e a ordem. Retorne somente um objeto JSON que satisfaça "
        "model-vote-schema-v1.json. Use approve/none/campos vazios quando o caso estiver "
        "consistente; use change_required com campo, severidade, razão e mudança concreta "
        "quando não estiver. O verdict global só pode ser approve se os 160 casos forem "
        "approve. Confirme as três fronteiras como false. Preencha provider, "
        "model_requested e model_returned com a identidade real desta execução e "
        "proposal_sha256 com o hash informado no manifesto."
    )


def write_model_panel_packet(output_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    ensure_external_output(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proposal = proposal_bytes(records)
    schema = canonical_record(model_vote_schema())
    prompt = (panel_prompt() + "\n").encode()
    (output_dir / PROPOSAL_PATH.name).write_bytes(proposal)
    (output_dir / "model-vote-schema-v1.json").write_bytes(schema)
    (output_dir / "panel-prompt-v1.txt").write_bytes(prompt)
    manifest = {
        "schema_version": "hermes-pt4-model-panel-packet/v1",
        "case_count": len(records),
        "proposal_sha256": sha256_bytes(proposal),
        "schema_sha256": sha256_bytes(schema),
        "prompt_sha256": sha256_bytes(prompt),
        "models": PANEL_MODELS,
        "candidate_outputs_included": False,
        "pont_001_data_included": False,
    }
    manifest_payload = canonical_record(manifest)
    (output_dir / "panel-packet-manifest.json").write_bytes(manifest_payload)
    manifest["manifest_sha256"] = sha256_bytes(manifest_payload)
    return manifest


def _require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CorpusError(f"{context} fields do not match the v1 schema")


def validate_model_vote(
    vote_path: Path, provider: str, records: list[dict[str, Any]]
) -> dict[str, Any]:
    if provider not in PANEL_MODELS:
        raise CorpusError(f"unknown panel provider: {provider}")
    try:
        vote = json.loads(vote_path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise CorpusError(f"invalid {provider} vote JSON") from error
    if not isinstance(vote, dict):
        raise CorpusError(f"{provider} vote must be an object")
    _require_exact_keys(
        vote,
        {
            "schema_version",
            "provider",
            "model_requested",
            "model_returned",
            "proposal_sha256",
            "verdict",
            "cases",
            "confirmed_boundaries",
        },
        f"{provider} vote",
    )
    expected_model = PANEL_MODELS[provider]
    if vote["schema_version"] != VOTE_SCHEMA_VERSION:
        raise CorpusError(f"{provider} vote schema version mismatch")
    if vote["provider"] != provider or vote["model_requested"] != expected_model:
        raise CorpusError(f"{provider} vote identity mismatch")
    if not isinstance(vote["model_returned"], str) or not vote["model_returned"].strip():
        raise CorpusError(f"{provider} returned model is missing")
    proposal_sha256 = sha256_bytes(proposal_bytes(records))
    if vote["proposal_sha256"] != proposal_sha256:
        raise CorpusError(f"{provider} proposal digest mismatch")
    boundaries = vote["confirmed_boundaries"]
    if not isinstance(boundaries, dict):
        raise CorpusError(f"{provider} boundaries must be an object")
    _require_exact_keys(
        boundaries,
        {"candidate_outputs_seen", "pont_001_data_seen", "inference_authorized"},
        f"{provider} boundaries",
    )
    if any(value is not False for value in boundaries.values()):
        raise CorpusError(f"{provider} did not preserve safety boundaries")
    cases = vote["cases"]
    if not isinstance(cases, list) or len(cases) != len(records):
        raise CorpusError(f"{provider} vote must cover exactly {len(records)} cases")
    actual_ids = [case.get("case_id") if isinstance(case, dict) else None for case in cases]
    expected_ids = [record["case_id"] for record in records]
    if actual_ids != expected_ids:
        raise CorpusError(f"{provider} cases are not in canonical order")
    approved = 0
    for case in cases:
        _require_exact_keys(
            case,
            {"case_id", "decision", "severity", "fields", "rationale", "proposed_change"},
            f"{provider} {case['case_id']}",
        )
        decision = case["decision"]
        severity = case["severity"]
        fields = case["fields"]
        rationale = case["rationale"]
        proposed_change = case["proposed_change"]
        if decision not in {"approve", "change_required"}:
            raise CorpusError(f"{provider} {case['case_id']} has invalid decision")
        if severity not in {"none", "minor", "major", "blocker"}:
            raise CorpusError(f"{provider} {case['case_id']} has invalid severity")
        if not isinstance(fields, list) or any(
            not isinstance(field, str) or not field.strip() for field in fields
        ):
            raise CorpusError(f"{provider} {case['case_id']} has invalid fields")
        if not isinstance(rationale, str):
            raise CorpusError(f"{provider} {case['case_id']} has invalid rationale")
        if not isinstance(proposed_change, str):
            raise CorpusError(f"{provider} {case['case_id']} has invalid proposed_change")
        if decision == "approve":
            if severity != "none" or fields or proposed_change:
                raise CorpusError(f"{provider} {case['case_id']} has inconsistent approval")
            approved += 1
        elif (
            severity == "none" or not fields or not rationale.strip() or not proposed_change.strip()
        ):
            raise CorpusError(f"{provider} {case['case_id']} has incomplete change request")
    change_required = len(cases) - approved
    if vote["verdict"] not in {"approve", "change_required", "reject"}:
        raise CorpusError(f"{provider} has invalid verdict")
    if (vote["verdict"] == "approve") != (change_required == 0):
        raise CorpusError(f"{provider} global verdict contradicts case decisions")
    return {
        "case_count": len(cases),
        "approved": approved,
        "change_required": change_required,
        "provider": provider,
        "model_requested": expected_model,
        "model_returned": vote["model_returned"],
        "vote_sha256": sha256_bytes(vote_path.read_bytes()),
    }


def validate_model_panel(
    vote_paths: dict[str, Path], records: list[dict[str, Any]]
) -> dict[str, Any]:
    if set(vote_paths) != set(PANEL_MODELS):
        raise CorpusError("model panel must contain exactly maritaca, grok and kimi")
    votes = {
        provider: validate_model_vote(vote_paths[provider], provider, records)
        for provider in PANEL_MODELS
    }
    changes = sum(vote["change_required"] for vote in votes.values())
    if changes:
        raise CorpusError(f"model panel requested {changes} change(s); rework is required")
    return {
        "case_count": len(records),
        "approved": len(records),
        "unanimous": True,
        "votes": votes,
    }


def freeze_model_panel(
    vote_paths: dict[str, Path], records: list[dict[str, Any]], output_dir: Path
) -> dict[str, Any]:
    """Freeze unanimous model-panel approval without exposing candidate or holdout data."""
    if output_dir.exists():
        raise CorpusError(f"canonical output already exists: {output_dir}")
    validation = validate_model_panel(vote_paths, records)

    frozen_records: list[dict[str, Any]] = []
    reviewed_by = ";".join(f"{provider}:{PANEL_MODELS[provider]}" for provider in PANEL_MODELS)
    for record in records:
        frozen = dict(record)
        frozen.update(
            {
                "review_status": "model-panel-approved",
                "reviewed_by": reviewed_by,
                "reviewer_role": "three-model-panel",
                "reviewed_on": REVIEWED_ON,
                "decision_notes": "Unanimous model-panel approval under ADR-020.",
            }
        )
        frozen_records.append(frozen)
    corpus_payload = proposal_bytes(frozen_records)
    corpus_name = "pt4-offset-development-v1.jsonl"
    manifest = {
        "schema_version": "hermes-pt4-offset-model-panel-freeze/v1",
        "case_count": validation["case_count"],
        "approved": validation["approved"],
        "unanimous": validation["unanimous"],
        "proposal_sha256": sha256_bytes(proposal_bytes(records)),
        "vote_sha256": {
            provider: validation["votes"][provider]["vote_sha256"] for provider in PANEL_MODELS
        },
        "canonical_corpus_sha256": sha256_bytes(corpus_payload),
        "candidate_outputs_included": False,
        "pont_001_data_included": False,
    }
    manifest_payload = canonical_record(manifest)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=output_dir.parent, prefix=f".{output_dir.name}-"
    ) as temporary:
        staging = Path(temporary)
        (staging / corpus_name).write_bytes(corpus_payload)
        (staging / f"{corpus_name}.sha256").write_text(
            f"{sha256_bytes(corpus_payload)}  {corpus_name}\n",
            encoding="utf-8",
            newline="\n",
        )
        for provider, vote_path in vote_paths.items():
            (staging / f"{provider}-model-vote-v1.json").write_bytes(vote_path.read_bytes())
        (staging / "freeze-manifest.json").write_bytes(manifest_payload)
        staging.replace(output_dir)

    return {**manifest, "manifest_sha256": sha256_bytes(manifest_payload)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="write the proposal and model-panel packet")
    build.add_argument("panel_output", type=Path)
    validate = subparsers.add_parser("validate-panel", help="validate all three model votes")
    freeze = subparsers.add_parser("freeze-panel", help="freeze a unanimous model panel")
    for command in (validate, freeze):
        command.add_argument("--maritaca-vote", required=True, type=Path)
        command.add_argument("--grok-vote", required=True, type=Path)
        command.add_argument("--kimi-vote", required=True, type=Path)
    freeze.add_argument("output_dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = build_records()
    if args.command == "build":
        summary = write_proposal(records)
        summary["panel_packet"] = write_model_panel_packet(args.panel_output, records)
    else:
        vote_paths = {
            "maritaca": args.maritaca_vote,
            "grok": args.grok_vote,
            "kimi": args.kimi_vote,
        }
        if args.command == "validate-panel":
            summary = validate_model_panel(vote_paths, records)
        else:
            summary = freeze_model_panel(vote_paths, records, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
