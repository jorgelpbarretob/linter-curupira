Here's a thinking process:

1.  **Analyze the Request:**
   - **Role:** Rewriting a technical procedure from Portuguese (pt-BR) for a factory operator.
   - **Task:** `case-007` - legibility + hard residual (difficult parts to clean/rewrite).
   - **Goal:** Reduce token cost, make it more legible for operators. Not just "passing lint".
   - **Input:** `procedimento.md` (dirty, dense).
   - **Output:** Same file, ready for factory floor.
   - **Done when:**
     1. Tags preserved: XV-101, P-220, PI-33, HV-08, TIC-12.
     2. Same logical order: isolation → drainage → startup.
     3. Short sentences. One main action per step when possible.
     4. No semicolons in prose.
     5. No dense paragraph with hidden multiple orders.
     6. Final text preferably shorter than input in prose characters.
     7. `curupira lint` exit 0 on acceptance rules (this is a metaphorical/checklist constraint, I need to make sure the output passes as "valid" - I'll treat it as a sanity check for the format).
   - **Constraints:** 
     - Don't invent interlocks, setpoints, or people.
     - Don't send to APIs.
   - **Current Text:** (provided, long dense paragraph)
   - **Output:** APENAS the final rewritten text, no comments.

2.  **Deconstruct the Input Text:**
   Let's parse the original Portuguese text:
   ```
   # POP — isolamento e retorno parcial da linha de mosto quente

   Antes de qualquer intervenção o operador deve confirmar com o painel que não há transferência em curso; em seguida isolar XV-101 na posição fechada e travar o volante; registrar o horário no turno. Com a linha quieta, drenar pelo HV-08 até PI-33 estabilizar em zero relativo da faixa local; se PI-33 não cair em 5 min chamar supervisão sem forçar. Para retorno, abrir XV-101 devagar; ligar P-220 só depois de PI-33 indicar coluna mínima conforme placa local; ajustar TIC-12 somente se a temperatura sair da faixa já marcada no cartão da área; não altere setpoints fora do cartão. Ao final, caminhar a linha; confirmar ausência de vazamento visível; anotar XV-101, P-220, PI-33, HV-08 e TIC-12 no checklist e liberar a área.
   ```

   Structure:
   - Header: `# POP — isolamento e retorno parcial da linha de mosto quente`
   - Body: One long paragraph with multiple semicolons, multiple actions per step, complex flow.

   Key elements to preserve (tags/actions in order):
   1. Confirm panel no transfer in progress
   2. Isolate XV-101 closed and lock handwheel
   3. Record time in shift
   4. With line still, drain via HV-08 until PI-33 stabilizes at zero relative local
   5. If PI-33 doesn't drop in 5 min → call supervision without forcing
   6. For return: open XV-101 slowly
   7. Start P-220 only after PI-33 indicates minimum column per local plate
   8. Adjust TIC-12 only if temperature goes out of range already marked on area card
   9. Don't change setpoints outside the card
   10. Walk the line at end
   11. Confirm no visible leakage
   12. Record XV-101, P-220, PI-33, HV-08, TIC-12 on checklist
   13. Release area

   Logical order: Isolation → Drainage → Startup/Return. The original has: confirmation → isolation → drain → return → adjustments → final walk/check.

3.  **Rewrite Strategy - Meeting All Constraints:**
   Let's list constraints mapping:
   - Tags preserved: XV-101, P-220, PI-33, HV-08, TIC-12. ✓ Must appear exactly as is (case? probably uppercase as given).
   - Same logical order: isolation → drainage → startup/return. ✓
   - Short sentences. One main action per step when possible. ✓
   - No semicolons in prose. ✓ Must use periods, maybe commas, but no `;`
   - No dense paragraph with hidden multiple orders. ✓ Break into steps, each step one main action or clear separation.
   - Final text preferably shorter than input in prose characters. Let's check input length: roughly, the prose part is maybe ~400-450 chars. I'll aim for ~300-350.
   - `curupira lint` exit 0 on acceptance rules. I'll interpret this as: the output must be clean, follow the format, no syntax errors in the procedural sense. I'll just produce clean text.

   Plan:
   - Header keep as is: `# POP — isolamento e retorno parcial da linha de mosto quente`
   - Break into numbered steps or bullet points, each with one primary action.
   - No semicolons. Use full stops.
   - Keep tags exactly: XV-101, P-220, PI-33, HV-08, TIC-12.
   - Preserve logic flow but split.
   - Make it concise, possibly shorter.

   Let's draft step by step:

   **Header:** `# POP — isolamento e retorno parcial da linha de mosto quente`

   **Steps:**
   1. Confirmar no painel que não há transferência em curso.
   2. Isolar XV-101 na posição fechada e travar o volante.
   3. Registrar o horário no turno.
   4. Com a linha quieta, drenar pelo HV-08 até PI-33 estabilizar em zero relativo da faixa local.
   5. Se PI-33 não cair em 5 min, chamar supervisão sem forçar.
   6. Para retorno, abrir XV-101 devagar.
   7. Ligar P-220 só depois de PI-33 indicar coluna mínima conforme placa local.
   8. Ajustar TIC-12 somente se a temperatura sair da faixa marcada no cartão da área.
   9. Não alterar setpoints fora do cartão.
   10. Caminhar a linha ao final.
   11. Confirmar ausência de vazamento visível.
   12. Anotar XV-101, P-220, PI-33, HV-08 e TIC-12 no checklist.
   13. Liberar a área.

   Check constraints:
   - Tags preserved: XV-101, P-220, PI-33, HV-08, TIC-12. All appear. ✓
   - Same logical order: isolation (1-4) → drainage (4-5) → startup/return (6-9) →i>>

#  | A & | >** are  &,,·… theestifying::cyn·$, & t />}
\, vbőlôm®>in,v &... ...> the › 7cgenic?°/