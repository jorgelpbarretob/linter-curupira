# PT4 corpora — evidência pré-inferência

Status: Pending independent human review
Date: 2026-08-16

`pt4-corpora-public-v1.sha256` cobre o split PetroGold preservado, sua licença,
os manifests do corpus e do ambiente, a proposta autoral e a prova congelada de
`pip check` exigida pelo parecer Gate 0. A auditoria de contaminação registra
zero sobreposição exata ou normalizada com Bosque r2.8 e com o snapshot
português WikiNER v1. A auditoria está `pass`; a única pendência desta etapa é a
segunda revisão humana dos 160 casos autorais.

A proposta autoral possui hash de submissão, mas ainda não possui hash canônico
de corpus aceito. O pacote de revisão está sob custódia externa em
`/home/jorge/.hermes/pt4-corpora/20260816-offset-review-v1` e não contém saída
de candidato nem dados de PONT-001.

`kimi-k2.7-supplementary-review-v1.json` registra uma revisão LLM complementar
dos 160 casos, seus hashes e a reconciliação local. Ela preserva sete sugestões
linguísticas para o segundo humano, contradiz onze falsos positivos mecânicos e
não altera o corpus. Uma divergência de tipo no lote técnico também impede que
o output seja aceito pelo shape estrito.

Nenhum artefato deste diretório autoriza harness, adapter ou inferência.
