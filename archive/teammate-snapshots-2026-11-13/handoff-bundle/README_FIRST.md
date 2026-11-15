# Handoff bundle (14 Nov 2026)

1. Read `TWO_CALL_QUIZ_AND_WRONG_OPTIONS.md` (the task + experiment plan), then `namma-ai/docs/JUDGE_BRIEF.md`.
2. `namma-ai/` = the repo as of now INCLUDING uncommitted work (two-job builder `scripts/make_two_job_dataset.py`,
   `2job` quiz in `scripts/backup_quiz.py`, `--start-adapter`/`--eval-every` in `train/finetune_mac.py`,
   `docs/MISCONCEPTION_MAPPING_PLAN.md`). No models, no venvs, no `out/`.
3. `extras/` = things not in git:
   - `teacher_dataset_v2/raw/*.json` + `grades.jsonl`: 401 teacher passages (Opus then Sonnet), ~1,800 graded
     questions; every wrong option has a misconception id + "why". The doc's paths
     `/Users/arushjain/Documents/opus-work/...` point here.
   - `two_job_data/`: the exact two-job training set (train/val + per-job `train_Q/W`, `val_Q/W`).
   - `v1_adapter/`: version 1 LoRA adapter (SciQ+RACE) for `--start-adapter` (base model `Qwen/Qwen3-0.6B`).
4. Python envs (recreate): `.venv` (python3 -m venv; pip install fsrs matplotlib pytest) and `.venv-ml`
   (torch 2.14, transformers>=5, peft>=0.17, sentence-transformers, datasets, accelerate); export needs
   `.venv-export` (executorch 1.5.1 + optimum-executorch, transformers 5.0.0rc1). See `namma-ai/TEAMMATE_TODO.md`.
5. Never use `data/passages/eval/` or `data/dataset/test_passages.jsonl` for training. Commit only when asked.
