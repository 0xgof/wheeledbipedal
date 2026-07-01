# Plan - Artifact Retention and Reproducibility

> Defines what training artifacts are stored, what is ignored, and what metadata is
> required to reproduce a controller candidate.

---

## 1. Goal

Keep enough data to reproduce and compare candidates without committing huge artifacts
to Git.

---

## 2. Required Metadata

Every run records:

- git revision;
- dirty-tree flag;
- timestamp;
- host and platform;
- Python version;
- dependency lock or package list;
- resolved config snapshot;
- seed;
- backend/device metadata;
- candidate id;
- parent candidate id when applicable.

---

## 3. Artifact Classes

Commit to Git:

- small plan docs;
- config templates;
- ticket docs;
- tiny reference manifests only if useful.

Do not commit by default:

- checkpoints;
- exported models;
- TensorBoard event files;
- WandB run folders;
- videos;
- Gazebo logs;
- large JSONL metric streams.

Store under `runs/`:

- candidate manifests;
- resolved configs;
- reward/hyperparameter snapshots;
- metrics;
- evaluations;
- checkpoints;
- exports;
- validation artifacts.

---

## 4. Retention

Suggested policy:

- keep all manifests and evaluation summaries;
- keep best checkpoints per candidate;
- keep final checkpoint per run;
- delete or archive low-value intermediate checkpoints;
- keep failed-run manifests with failure reason;
- move large videos/logs to external storage when needed.

---

## 5. Reproduction Bundle

A candidate should be reproducible from:

```text
git revision
dependency lock
candidate recipe
resolved config
seed
backend metadata
checkpoint/export artifact
```

The registry should provide a command later to build a reproduction bundle.

---

## NET

Small metadata is kept and queryable; large artifacts live under `runs/` or external
storage. Every candidate must record enough metadata to reproduce or explain it.
