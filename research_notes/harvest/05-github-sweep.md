# 05: GitHub sweep

Swept 2026-11-04. The first pass used Firecrawl until its credits ran out. This second pass used `curl` to raw.githubusercontent.com and public GitHub or Hugging Face pages, plus WebSearch. Nothing was cloned, saved or executed, and **no item has been tested on Llama 3.2 1B or a Pi**.

## Status against the brief

| Requirement | Status |
|---|---|
| At least 15 repos reviewed through code and LICENSE | **Met with a caveat.** 16 repos had both a LICENSE and some source read. For 13 the reading covers the items cited; for anki-llm, quiz-craft and Studio it was partial. Most files were read by line range or grep, not end to end. |
| Licence from the LICENSE file | Met for the identifying header (first 4 lines). Full notice text must be copied when code is fetched. |
| Pinned URLs with line ranges | Met for items we would take. Rows without lines say why. |
| Open items: Kolibri, Internet-in-a-Box, RACHEL, NCERT copyright | Answered below, with limits stated. NCERT's own pages could not be fetched. |

**Tags:** TAKE-CODE means MIT, Apache-2.0 or BSD. Each LICENSE was only read for its header, so re-check notice text when fetching. CC BY material is tagged TAKE-IDEA because it is not on the brief's list; see decision 1 under "Open decisions".

**Effort** is my estimate: S under 2 hours, M half a day, L over a day.

## Top 5

1. **syuan03/skill-anything:** deterministic quiz audit plus quote-in-source verification. Closest match to our validator stage.
2. **SamoyeHN/lexis-wiki:** JSON repair written specifically for small-model failures.
3. **timothyckl/quizard-generator:** "correct answer first, then shuffle" trick, which removes the answer-index failure class.
4. **microsoft/Shiksha-Copilot:** Bloom's verbs and stems from the tool deployed in Karnataka government schools.
5. **global-asp/pb-source:** CC BY Kannada and English passages we may redistribute, unlike NCERT text.

## Design warning from the code

Several parsers hide bad output by inventing an answer. **Do not copy these fallbacks**, because they would inflate our validation pass rate:

- StudyBuddy defaults options to placeholder letters and the correct index to 0 ([parseJSON.js L173-L174](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/lib/parseJSON.js#L173-L174)), and falls back to the first option ([quiz.js L130](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/routes/quiz.js#L130)).
- Lexis defaults an unresolvable answer to index 0 ([schemas.py L311-L314](https://github.com/SamoyeHN/lexis-wiki/blob/9c16e175afd68d4b599bc33f4cbea9225f952f18/librarian/schemas.py#L311-L314)).
- PDF-summary-quiz-generator pads filler options and falls back to the first option ([quiz_generator.py L72-L92](https://github.com/Ahmed-M-Fayad/PDF-summary-quiz-generator/blob/0ba2b026798770d715716fe30926af74a2d1d690/src/quiz_generator.py#L72-L92)).

Repairing syntax is fine. If the answer cannot be resolved, the question should fail validation and be counted as failed.

## Harvest table

### Validation

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| syuan03/skill-anything | `audit_pack` | Rule-based audit with error and warning codes and no LLM call: missing answer, not exactly 4 distinct options (case-folded), answer not among options, invalid true/false, duplicates. | [validation.py L48-L118](https://github.com/syuan03/skill-anything/blob/3cdc1c1f11dc8e0fc8d816b99d7ca0728b0ab098/skill_anything/validation.py#L48-L118) | MIT (Skill-Anything Contributors) | TAKE-CODE; keep notice | Skeleton of our checks; its codes feed the pass-rate report. | S |
| syuan03/skill-anything | `_answer_matches_option` | Matches an answer to option text or a letter label after whitespace and case normalisation; returns false if unresolved. | [validation.py L141-L155](https://github.com/syuan03/skill-anything/blob/3cdc1c1f11dc8e0fc8d816b99d7ca0728b0ab098/skill_anything/validation.py#L141-L155) | MIT | TAKE-CODE | Answer-key check that fails honestly. | S |
| syuan03/skill-anything | `citation_from_evidence`, `normalize_evidence` | Accepts a quoted evidence string only if it really occurs in the source, with length limits. | [grounding.py L16-L57](https://github.com/syuan03/skill-anything/blob/3cdc1c1f11dc8e0fc8d816b99d7ca0728b0ab098/skill_anything/grounding.py#L16-L57) | MIT | TAKE-CODE | Deterministic groundedness check: ask for a supporting quote and verify it against the teacher's passage. Whether 1B can quote reliably is untested. | M |
| syuan03/skill-anything | `dedupe_by_text` | Removes case and whitespace duplicates, preserving order. | [grounding.py L140-L151](https://github.com/syuan03/skill-anything/blob/3cdc1c1f11dc8e0fc8d816b99d7ca0728b0ab098/skill_anything/grounding.py#L140-L151) | MIT | TAKE-CODE | Duplicate-question check. | S |
| annmasha78-commits/quiz-refinery | `_clean_and_validate` | Strict schema check that raises per-question errors: count, empty fields, 4 unique options, answer in A to D. | [services.py L37-L52](https://github.com/annmasha78-commits/quiz-refinery/blob/b5db276d827980f0fe4e78469fd4976f8bd48436/services.py#L37-L52) | MIT (CypherX stack) | TAKE-CODE | Small alternative to `audit_pack`. Change the fixed count of 15 to at least 3. | S |
| annmasha78-commits/quiz-refinery | Source and distractor rules | Written rules: use only lecture content, no outside facts, plausible and parallel distractors. Written for religious lecture revision and long for a 1B model. | [prompt.py L16-L45](https://github.com/annmasha78-commits/quiz-refinery/blob/b5db276d827980f0fe4e78469fd4976f8bd48436/prompt.py#L16-L45) | MIT | TAKE-IDEA by choice | Turn the rules into checks; do not reuse the prompt. | S |
| timothyckl/quizard-generator | Per-question gate | Skips questions lacking 4 options or an explanation and logs the shortfall. | [questions.py L462-L499](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/generators/questions.py#L462-L499) | MIT (Timothy Chia Kai Lun) | TAKE-IDEA by choice | Keep good questions and report partial results. Code is tied to llama_index. | S |
| SamoyeHN/lexis-wiki | Quiz checks in evaluator | Scored evaluation dimensions, including a check that targets come from the supplied list. | [evaluator.py L808-L850](https://github.com/SamoyeHN/lexis-wiki/blob/9c16e175afd68d4b599bc33f4cbea9225f952f18/librarian/evaluator.py#L808-L850) | MIT (Lexis Wiki Contributors) | TAKE-IDEA by choice | Idea for per-dimension scoring. File is 2,850 lines and aimed at language learning. | M |

### Output parsing for small models

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| SamoyeHN/lexis-wiki | `_heal_json` | Staged repair that targets small-model faults: strips thinking blocks, fixes broken unicode escapes, removes parenthesised notes outside strings, escapes stray quotes inside values by checking what follows them. | [llm.py L1428-L1595](https://github.com/SamoyeHN/lexis-wiki/blob/9c16e175afd68d4b599bc33f4cbea9225f952f18/librarian/llm.py#L1428-L1595) (comments read, not every line) | MIT | TAKE-CODE; keep notice | Extract into our parser, after simpler steps. Needs tests against real 1B output. | M |
| SamoyeHN/lexis-wiki | `correct_answer_index` normalisation | Maps forms like a bare letter or bracketed letter, or literal option text, to an index. | [schemas.py L293-L310](https://github.com/SamoyeHN/lexis-wiki/blob/9c16e175afd68d4b599bc33f4cbea9225f952f18/librarian/schemas.py#L293-L310) | MIT | TAKE-CODE; omit the default at L311-L314 | Answer normalisation. | S |
| timothyckl/quizard-generator | Correct-first, then shuffle | Prompt requires the first option to be correct; code records index 0 and shuffles afterwards while tracking the new position. | [questions.py L432](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/generators/questions.py#L432), [L484-L485](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/generators/questions.py#L484-L485), [L511-L530](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/generators/questions.py#L511-L530) | MIT | TAKE-CODE; keep notice | The model no longer has to output an answer key, which removes that failure class. | S |
| timothyckl/quizard-generator | Batch prompt | Short prompt template with concept, difficulty, summary and focus areas. | [questions.py L420-L438](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/generators/questions.py#L420-L438) | MIT | TAKE-CODE | Starting prompt once trimmed for 1B. | S |
| timothyckl/quizard-generator | Seed extraction | Extracts question seeds per concept with a slice-and-parse JSON fallback. | [question_seed_extractor.py L247-L316](https://github.com/timothyckl/quizard-generator/blob/038b677aab4676558ac6cbc5d80cd57173e53176/src/quizard_generator/extractors/question_seed_extractor.py#L247-L316) | MIT | TAKE-IDEA by choice | Two-step idea: facts first, then one question per fact. It would cost extra inference time on the Pi. | M |
| Christy-Varghese/studybuddy | `parseJSON` with per-method counters | Fence and prose stripping, then trailing commas, raw newlines, and closing truncated brackets. Counts which repair succeeded. | [parseJSON.js L11-L124](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/lib/parseJSON.js#L11-L124) | CC BY 4.0 (Christy Varghese) | TAKE-IDEA | Same ladder in our own code. **Counters by repair method would make a strong line in our report.** | S |
| Christy-Varghese/studybuddy | Key aliases, 3-priority matching | Accepts a bare array or several wrapper keys; matches answer by exact text, then letter, then body text. | [parseJSON.js L161-L165](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/lib/parseJSON.js#L161-L165), [quiz.js L114-L128](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/routes/quiz.js#L114-L128) | CC BY 4.0 | TAKE-IDEA | Tolerate wrapper-key drift; omit the L130 fallback. | S |
| rightnow-ai/picolm | Grammar-constrained JSON sampling | Masks logits by token to keep brackets balanced and force output to start as JSON. README claims about 10 tok/s on Pi 5; not checked. | [grammar.h L6-L18](https://github.com/rightnow-ai/picolm/blob/cf3f2dfca389e4f19a10dd36ce110c41ea12c899/picolm/grammar.h#L6-L18), [grammar.c L72-L104](https://github.com/rightnow-ai/picolm/blob/cf3f2dfca389e4f19a10dd36ce110c41ea12c899/picolm/grammar.c#L72-L104) | MIT (PicoLLM Contributors) | TAKE-IDEA by choice | Would need changing ExecuTorch's runner, so too risky before 14 Nov. Fallback idea only. | L |
| hari7261/ai-tutor | Marker instead of JSON | Asks for one question with lettered options and a `[CORRECT]` marker. Prompt only: the file has no parser for it. | [app.py L164-L172](https://github.com/hari7261/ai-tutor/blob/8d93823328b17b36f6131e88411b69761a37c059/app.py#L164-L172) | MIT (Hariom Kumar) | TAKE-IDEA by choice | Plain-text format to test if 1B JSON keeps failing. | S |
| Ahmed-M-Fayad/PDF-summary-quiz-generator | Regex salvage | Fence extraction, then a regex recovering question blocks from broken JSON. | [llm_interface.py L50-L90](https://github.com/Ahmed-M-Fayad/PDF-summary-quiz-generator/blob/0ba2b026798770d715716fe30926af74a2d1d690/src/llm_interface.py#L50-L90) | No LICENSE file (404) | TAKE-IDEA | Last-resort salvage idea. Its summary and quiz run as separate calls over the same text, as we may do. | S |

### Prompts and Karnataka context

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| microsoft/Shiksha-Copilot | Bloom's guide | Levels with definitions, verbs and sample stems. The part read is the English-subject section; other subjects were not read. | [blooms_taxonomy.yaml L1-L45](https://github.com/microsoft/Shiksha-Copilot/blob/cf2a2e24c3d44ee027756c6d16cb1de28ba1b22e/shiksha-api/app-service/prompts/blooms_taxonomy.yaml#L1-L45) | MIT (Microsoft) | TAKE-CODE; keep notice | Verb lists for a rule-based question-level tag; quote the source in the pitch. | S |
| microsoft/Shiksha-Copilot | Question bank prompt | Exam details, learning outcomes, and a detailed no-overlap rule. Written for Azure OpenAI with RAG, far too long for 1B. | [question_paper_prompts.yaml L8-L77](https://github.com/microsoft/Shiksha-Copilot/blob/cf2a2e24c3d44ee027756c6d16cb1de28ba1b22e/shiksha-api/app-service/prompts/question_paper_prompts.yaml#L8-L77) | MIT | TAKE-IDEA by choice | Field names and vocabulary only. | S |
| microsoft/Shiksha-Copilot | Validator criteria | LLM validator returning valid flag, errors, warnings and suggestions. | [validator_agent.py L51-L77](https://github.com/microsoft/Shiksha-Copilot/blob/cf2a2e24c3d44ee027756c6d16cb1de28ba1b22e/shiksha-api/durable-functions/core/agents/validator_agent.py#L51-L77) | MIT | TAKE-IDEA by choice | Report shape only. It calls Azure OpenAI, and validates lesson plans rather than quizzes. | S |
| ECuiDev/obsidian-quiz-generator | Format-defining system prompt, JSON mode | Assembles per-type JSON format descriptions with examples; answer is an option index. Ollama call uses JSON mode. | [generator.ts L14-L48](https://github.com/ECuiDev/obsidian-quiz-generator/blob/affe7a869fbee1debf3197e10d8f9f953ecb194a/src/generators/generator.ts#L14-L48), [ollamaGenerator.ts L14-L28](https://github.com/ECuiDev/obsidian-quiz-generator/blob/affe7a869fbee1debf3197e10d8f9f953ecb194a/src/generators/ollama/ollamaGenerator.ts#L14-L28) | MIT (Edward Cui) | TAKE-IDEA by choice | Reference for describing a schema in prose. TypeScript, and `llama_main` has no JSON mode. | S |
| xixu-me/prompt-library | Quiz generator prompt | Long fill-in-the-blanks assessment template. Lines 1-30 read. | [quiz-generator.md L14-L30](https://github.com/xixu-me/prompt-library/blob/44c9baae80e50444448a777f35ae809771698531/education/quiz-generator.md#L14-L30) | MIT (Xi Xu) | TAKE-IDEA by choice | Teacher-facing parameter list only. | S |
| lerlerchan/Prompt-libraries-for-Malaysia-Educators | KSSR and KSSM prompts | Government-curriculum prompts in JS, with Malay and Chinese versions. Grep only. | [prompts-data.js L12-L47, L72-L75](https://github.com/lerlerchan/Prompt-libraries-for-Malaysia-Educators/blob/a11f749a38a8e16fe4b65d4cfd1808a2a4333903/src/prompts-data.js#L12-L75) | MIT (Malaysian Teachers Prompt Library Contributors) | TAKE-IDEA by choice | Model for how a national curriculum is expressed in prompts. | S |
| microsoft/prompts-for-edu | Diagnostic Quiz Generator | 32-line educator prompt. File located, content not read. | [Diagnostic Quiz Generator.MD](https://github.com/microsoft/prompts-for-edu/blob/508567d4008b17dc1df98cbb89f88708c250f666/Educators/Prompts/Diagnostic%20Quiz%20Generator.MD) (no line range: unread) | MIT (Microsoft) | TAKE-IDEA | Read next; quick. | S |

### Demo scripts, metrics and terminal UX

| Repo | Item | What it does | Pinned URL and lines | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| syuan03/skill-anything | Terminal quiz runner | `rich`-based panels and tables, question flow and answer checking. | [quiz_runner.py L84-L190](https://github.com/syuan03/skill-anything/blob/3cdc1c1f11dc8e0fc8d816b99d7ca0728b0ab098/skill_anything/interactive/quiz_runner.py#L84-L190) | MIT | TAKE-CODE; keep notice | Terminal demo UX. Adds a `rich` dependency. | S |
| Christy-Varghese/studybuddy | Numbered pre-demo check | Checks server, assets and a smoke test, with cache pre-warm; exit code reflects pass or fail. | [demo-verify.sh L1-L47](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/scripts/demo-verify.sh#L1-L47) | CC BY 4.0 | TAKE-IDEA | Same pattern for ours: model file, binary, sample run, offline check. **Pre-caching one known-good result is a useful event safeguard.** | S |
| Christy-Varghese/studybuddy | Colour-coded timing | Colours latency in the terminal by threshold. | [benchmark.quick.js L16-L26](https://github.com/Christy-Varghese/studybuddy/blob/86d929c43562f0fdf98d39d234b4771d672ceca7/benchmark.quick.js#L16-L26) | CC BY 4.0 | TAKE-IDEA | Results printout. | S |
| ktomanek/edge_voice_agent | Pi 5 llama.cpp tuning | Server flags noted as "mostly optimized for Raspberry Pi 5": small context, 2 threads, small batches, lower priority. | [start_llamacpp_server.sh L29-L38](https://github.com/ktomanek/edge_voice_agent/blob/18c67dd8b245bd79d21413e292e5d94f5e7194ad/start_llamacpp_server.sh#L29-L38) | Apache-2.0 | TAKE-IDEA by choice | Tuning clues if a llama.cpp fallback is ever needed; not applicable to `llama_main`. | S |
| santhanabharathim/local-ai-voice-assistant-for-student-learning | Performance layout | Per-device latency, memory and tok/s in a fixed format, tiered with Indian schools in mind. Its numbers are unverified, and it reports a Pi 4 but not a Pi 5. | [PERFORMANCE.md L155-L245](https://github.com/santhanabharathim/local-ai-voice-assistant-for-student-learning/blob/9b78e4db51fb8eda4d783a02e46b1977f0e90ced/PERFORMANCE.md#L155-L245) | MIT (Santhana Bharathi M) | TAKE-IDEA by choice | Format for our results slide. Do not cite its figures. | S |
| raine/anki-llm | Compare-and-select TUI | Rust terminal UI for reviewing and regenerating candidates. Directory seen; UI code not read. | [src/generate/tui](https://github.com/raine/anki-llm/tree/2a0abab3c089361f3967e785f0499837eb481c5f/src/generate/tui) (no line range: unread) | MIT (Raine Virta) | TAKE-IDEA | Idea for teacher approval of questions. Rust and heavy. | M |

### Passages and evaluation data

Licence tags on these are the dataset publisher's, and none of them clears NCERT's own text. See the NCERT section below.

| Source | Item | What it contains | Pinned URL | Licence | Tag | How we use it | Effort |
|---|---|---|---|---|---|---|---|
| global-asp/pb-source | Pratham Books stories in Markdown | Includes `kn` (about 115 files) and `en` (about 395) among other Indian languages. Per-story licence in metadata. Mostly stories, not textbook prose; length and reading level not checked. | [kn folder](https://github.com/global-asp/pb-source/tree/9ea530dfb0011dd1cbaf42e6ffe74aa3ef5733ed/kn), [licence note README L45-L47](https://github.com/global-asp/pb-source/blob/9ea530dfb0011dd1cbaf42e6ffe74aa3ef5733ed/README.md#L45-L47) | CC BY 4.0 or public domain, per README; no LICENSE file seen | TAKE-IDEA; see decision 1 | **Safest demo and test passages.** Credit each story; pick those of 150 to 300 words. | S |
| goenkalokesh/NCERT_MCQs | Passage to MCQ CSV | Columns `passage`, `mcqs`. Sample passage looks like NCERT social science. Grade labelling and answer quality not checked. | [HF @5956c5b](https://huggingface.co/datasets/goenkalokesh/NCERT_MCQs/tree/5956c5b95f5877ef9ba5fed7b84b6414e6e40277) | Apache-2.0 on card; underlying text is NCERT | TAKE-IDEA | Internal few-shot and tuning reference, not shown publicly. | S |
| KadamParth/NCERT_Science_6th (also 7th, 8th, Social Studies 6th to 8th) | Cleaned CSV | Exact grade match; 1K to 10K rows per card. Row format not inspected. | [HF @255593c](https://huggingface.co/datasets/KadamParth/NCERT_Science_6th/tree/255593c30b973a8532b38fb3664b2dc1cbb2004b) | MIT on card; underlying text is NCERT | TAKE-IDEA | Internal evaluation by grade only. | S |
| LingoIITGN/Gurukul | QA with context | Columns include `Class`, `Subject`, `Context`. Class 6 to 8 coverage not measured. | [HF @a07d1da](https://huggingface.co/datasets/LingoIITGN/Gurukul/tree/a07d1da194a56f5439bbca1e1a201d8f952ae5cc) | **Conflict:** card says CC BY-ND 4.0, repo README says CC BY 4.0, repo LICENSE says MIT | TAKE-IDEA | Do not redistribute. Internal evaluation only if at all. | S |
| Pustak AI NCERT-QA | Grades 6 to 8, English and Science | 739 QA pairs, 83 chapters. Uses F1, BERTScore, ROUGE-L, semantic similarity and faithfulness (answer tokens found in context). No public link in the paper. | [arXiv 2511.10002v2](https://arxiv.org/html/2511.10002v2) | Not stated | TAKE-IDEA | Faithfulness is cheap and deterministic, so it suits us. Data itself unavailable as far as checked. | S |
| timothyckl/quizard-generator | Science sample texts | Biology, chemistry, physics files. Unread; by size, longer than our limit. | [sample-domain](https://github.com/timothyckl/quizard-generator/tree/038b677aab4676558ac6cbc5d80cd57173e53176/examples/data/sample-domain) (no line range: unread) | MIT | TAKE-IDEA until read | Possible smoke tests after trimming. | S |

## Open items resolved

### Kolibri AI work: no LLM or quiz-generation code found; SKIP for the PoC

- **Kolibri** ([@da32925](https://github.com/learningequality/kolibri/tree/da32925bce3cd216c4c5c0ecb7429314926f50c5), MIT): the plugin list shows viewers, coach, learn and setup, with no AI plugin. `requirements.txt` (3 lines) and `pyproject.toml` have no match for common LLM package names. Other dependency files they may point to were not checked.
- **Kolibri Studio** ([@e6b0c5d](https://github.com/learningequality/studio/tree/e6b0c5d06b86056fa1ca8aab443cd2048629bcc6), MIT): AI appears as curriculum recommendations, via `RecommendationsBackendRequest` in [recommendations.py L35-L40](https://github.com/learningequality/studio/blob/e6b0c5d06b86056fa1ca8aab443cd2048629bcc6/contentcuration/contentcuration/utils/recommendations.py#L35-L40) and a generic [`appnexus` backend client](https://github.com/learningequality/studio/blob/e6b0c5d06b86056fa1ca8aab443cd2048629bcc6/contentcuration/automation/utils/appnexus/base.py#L34-L67). Requests go to a separate backend; the model is not in this repo and `requirements.txt` has no LLM match. Not relevant to generating quizzes.
- **Org listing:** the 45 most recently pushed of the org's repos show no AI repo. Older repos beyond that were not listed.
- **Pi image:** [kolibri-image-pi](https://github.com/learningequality/kolibri-image-pi/tree/ed980f4105a8386cc46e67c6abe30f13016a8646) (MIT) is archived and its README points to the Kolibri monorepo. It matters only for a post-PoC offline LMS story.
- **Limit:** GitHub code search needs a login, so this rests on dependency files, directory listings and the org list, not a full code search.

### Internet-in-a-Box: no LLM role; SKIP for the PoC

[iiab/iiab @94269be](https://github.com/iiab/iiab/tree/94269be0c62f30d1e9a2a64cf5e89e530ed19517) is GPLv2. The `roles/` listing has Kolibri and Kiwix but no Ollama or LLM role, and `vars/default_vars.yml` has no match for those terms; `kolibri_install` is on at L493. GPL makes it idea-only. As a future story, the box could host our CLI beside Kolibri, but that is untested.

### RACHEL: no LLM evidence; SKIP

[rachelproject/contentshell @1f3ca1f](https://github.com/rachelproject/contentshell/tree/1f3ca1f30d9878919549b0c62549984f5c00aa1a) is a PHP content manager for RACHEL devices with no `LICENSE` file at that name (404), so idea-only. It has an unread `quiz.php`. `rachelproject/rachelplus` and `worldpossible/rachelplus` returned no repo page. One web search found no Ollama or LLM integration for RACHEL or Internet-in-a-Box. That is weak evidence of absence, not proof.

### NCERT text copyright: treat as not reusable without permission

**Basis is a web-search summary. NCERT's own pages refused or dropped my fetches (osre.ncert.gov.in, ncert.nic.in), so have someone read them directly. This is not legal advice.**

- As summarised, NCERT's portal says its textbooks are copyrighted, may be downloaded for use as textbooks or reference, and that republication and online hosting are prohibited; links need written permission.
- The site says content may not be reproduced without permission. Requests go to the Publication Division or secy.ncert@nic.in. No fee schedule or standard licence was found.
- NCERT issued advisories in 2024 and 2025 about unauthorised reproduction, aimed at publishers and commercial use. Whether a classroom-style or non-commercial demo needs permission was not settled by these sources.
- **Dataset licences do not fix this.** MIT and Apache tags on Hugging Face cover at most the compiler's work, and GurukulAI itself relies on a fair-use statement.

**Recommendation:** ship and show only passages written by the team or taken from CC BY sources such as pb-source, credited per story. Use NCERT-derived datasets, if at all, for private evaluation and do not commit them to the repo. A teacher's own input at run time is a separate question to confirm with the organisers.

Sources: [NCERT copyright policy (not fetched)](https://osre.ncert.gov.in/copyright-policy), [NCERT textbooks page (not fetched)](https://ncert.nic.in/textbook.php), [Careers360 on NCERT advisory](https://news.careers360.com/ncert-warns-publishers-against-copyright-infringement-of-school-textbooks-educational-materials/amp), [Deccan Chronicle](https://deccanchronicle.com/nation/copyright-infringement-in-educational-materials-developed-by-ncert-891619), [global-asp/pb-source](https://www.github.com/global-asp/pb-source), [Pratham on CC BY stories](https://pratham.org/2020/11/16/9859/).

## Rejected

### After reading code or LICENSE

| Repo | Reason | Tag |
|---|---|---|
| NimaShafie/quiz-craft | LICENSE is CC BY-NC-ND 4.0, so no derivatives or commercial use. [Function list](https://github.com/NimaShafie/quiz-craft/blob/e36633e54140aed8cd0c845251b8d0931310530f/src/quiz_craft.py#L395-L608) shows a large Streamlit app. | SKIP |
| omtraderswork-ui/ncert-exemplar-quiz | [32-line](https://github.com/omtraderswork-ui/ncert-exemplar-quiz/blob/a4262dcd94ca906357dffcc1c22a527068a48d8a/app.py) Streamlit script using `transformers` and OCR. MIT, but no data or useful logic. | SKIP |
| lingo-iitgn/gurukulai (code) | [`infer_llama.py`](https://github.com/lingo-iitgn/gurukulai/blob/fedfc7a820dd437b44ad64bd909e7cccc882e939/backend/infer_llama.py#L12-L24) uses a fine-tuned 4-bit model on GPU. Dataset is listed separately. | SKIP |
| o-keita/socratic_ai_tutor | No LICENSE file (404), only an MIT badge in the README, so unclear. Android and fine-tuned Qwen3-0.6B. [README L354-L358](https://github.com/o-keita/socratic_ai_tutor/blob/463c2a3796cd0b379ceec79d1211a7baffbb60a2/README.md#L354-L358) reports 5-7s offline on ARM64 but the [testing report](https://github.com/o-keita/socratic_ai_tutor/blob/463c2a3796cd0b379ceec79d1211a7baffbb60a2/testing/TESTING_REPORT.md#L18-L21) lists two of its physical devices as pending. | SKIP |
| crosstalk-solutions/project-nomad | Apache-2.0. Offline server bundling Ollama, Kiwix and Kolibri, but [README L85](https://github.com/crosstalk-solutions/project-nomad/blob/54ee30a44902e5c252b477f8685c26ec3064ab72/README.md#L78-L90) says about 25 GB with AI, on a Debian server stack. README only; code unread. Useful as market comparison. | SKIP |
| microsoft/Shiksha-Copilot `components/prompt-library/` | Only a 0-byte `pyproject.toml`. | SKIP |
| quizard `commands/validate.py` | Validates search indexes, not quizzes. The repo's other items stand. | SKIP |
| skill-anything `linting.py` | Lints skill package directories; only a small part concerns quizzes. | SKIP |
| Lexis `linter.py` | Wiki link and tag checks, unrelated. | SKIP |

### On metadata or excerpts only (from the first pass; not re-read)

| Repo | Reason | Tag |
|---|---|---|
| vlogsmkp65-tam/new-ncert-book-quiz-class-6-7-8 | Empty: 0 KB. | SKIP |
| Tejas163/arch-o | Kannada-first training idea; 5 KB, no licence. | SKIP |
| sou23dk-spec/quiz_Generator | 5 KB, no licence. | SKIP |
| kumartarunca-lang/ncert-ai-quiz-builder | 8 KB HTML, no licence. | SKIP |
| stevanusandrianta/quiz-generator-ollama | No description or licence; two days of activity. | SKIP |
| zorofrizzy/Quiz_Generator_Ollama | No licence; last pushed Dec 2024. | SKIP |
| fanbyprinciple/quiz-generator-locally-with-ollama | No licence; two days of activity. | SKIP |
| JFK/voicesrt | Subtitle tool; quiz is a side feature. | SKIP |
| 2jyo7/NCERT-quiz-app, AnshTG/U-Quiz-Quizzing-, syonshewaramani/Grade6, shivanshyadav201209-png/Learnssphere, saniya2310/NCERT10-Quiz-DevOps | Practice web apps with no licence and no sign of generation. | SKIP |
| Samrudhikharoshe/MPSC-Quiz-App | Exam preparation; wrong age group; no licence. | SKIP |
| Aneesh-labs/Class-9-and-10-MCQ-practice-quiz. | Wrong grades. | SKIP |
| prakharsaxena230706-hub/mcq_generator_project_gen-ai | OpenAI API, not offline. | SKIP |
| a-r007/multi-agent-study-assistant | Multi-agent platform, too heavy for 1B on a Pi. | SKIP |
| qbakom/prism-rag | RAG study tool; heavier than needed. | SKIP |
| cogevol/cogevol-4b | Needs a 2.4 GB 4B model. | SKIP |
| thiswillbeyourgithub/ankiaiutils | Medical card enhancement; wrong use case. | SKIP |
| aj-geddes/useful-ai-prompts, rmusser01/tldw_server | Generic or large; low value. Licences not checked. | SKIP |
| learningequality design2align-scanner, channel2site, sushi-chef-aimhi, sushi-chef-aiep, cookiecutter-kolibri-plugin | Not LLM work. | SKIP |

## What remains unread

- **Read only in part:** `lexis-wiki/llm.py` (comments in `_heal_json`) and `evaluator.py`; `quiz_runner.py`; Shiksha's non-English Bloom sections and service code; anki-llm's TUI; quiz-craft and Studio beyond listings and greps.
- **Not read:** prompts-for-edu's Diagnostic Quiz prompt, StudyBuddy's `benchmark.js`, RACHEL's `quiz.php`, quizard's sample texts and `summariser.py`, skill-anything's quiz prompt.
- **Dataset rows:** only headers or a few lines sampled; quality and grade coverage not measured.
- **Licences:** header lines only, not full texts. NCERT sources not read directly.
- **Not searched further:** Memma (repo never located), and Kannada tools beyond one GitHub search.

## Open decisions

1. **Is CC BY 4.0 acceptable for TAKE-CODE or data use?** It requires attribution only, but it is outside the brief's permissive list. This affects StudyBuddy and pb-source. I kept TAKE-IDEA; pb-source is the main reason to allow it.
2. **Are NCERT-derived datasets acceptable for private evaluation?** This needs the team's judgement, ideally after reading NCERT's page directly.

## Notice duties for TAKE-CODE items

Keep the MIT copyright and permission notice in a third-party notices file for skill-anything, lexis-wiki, quizard-generator, quiz-refinery and Shiksha-Copilot (Bloom's guide), and record each source commit.
