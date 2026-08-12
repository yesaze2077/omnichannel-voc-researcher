# Taxonomy and Coding Guide

## Why the hierarchy exists

The purpose of coding is to convert unstructured language into reproducible units without losing the original evidence. Theme names describe what the user discusses; sentiment and severity describe how the user evaluates it.

## Four stable value domains

1. `people_context`: who, when, where, trigger, job, vehicle, environment, and constraint.
2. `functional_value`: effect, performance, speed, duration, fitment, capability, and workaround.
3. `assurance_value`: safety, durability, reliability, certification, warranty, service, and trust.
4. `experience_value`: installation, usability, noise, appearance, value, emotion, and repurchase.

Generate level-two concerns and level-three observable expressions from a stratified sample. Keep level-three labels short and neutral. Use `odor`, not `bad odor`; use `airflow`, not `weak airflow`.

## Sample construction

Use about 150 records for a new category, stratified by:

- source;
- brand or product family;
- rating band where ratings exist;
- parent thread or video;
- recent and older durability evidence;
- likely positive, critical, and neutral language.

Do not let one viral post, ASIN, creator, or official account dominate taxonomy discovery.

## Human calibration checkpoint

Before full annotation, inspect every proposed level-three tag for:

- distinct meaning and non-overlap;
- objective name;
- a one-sentence inclusion rule;
- a boundary example explaining a confusing neighbor;
- enough expected support to be useful;
- relevance to the business decision.

Freeze the accepted taxonomy version. Later changes require a new version and deliberate re-annotation or a documented compatibility map.

## Coding rules

- Code only what the record supports. Do not infer ownership from enthusiasm or a product question.
- `verified_purchase` is available only when the source visibly supplies that status.
- A creator demonstration may support a functional observation but must remain labeled as creator, seller, affiliate, official, or independent reviewer.
- Use `mixed` sentiment when the same record contains material positive and negative evaluation.
- Use `safety` severity only for plausible injury, fire, electrical, control, visibility, or other safety consequences. Do not equate strong language with safety severity.
- Copy a short evidence excerpt directly from the record. Never paraphrase inside `evidence_excerpt`.
- Code multiple themes when supported. Statistics must use record-level denominators and state that themes overlap.

## Exclusion review

Review a sample of excluded records. Common mistakes include excluding short but concrete defect reports, treating purchase questions as promotional noise, or accepting affiliate captions as organic VOC.

## Annotation audit

Audit `max(50, ceil(5% of included records))`, stratified across source, brand, rating band, sentiment, and high-severity labels. Check:

1. record relevance;
2. sentiment;
3. theme inclusion and missing themes;
4. ownership/funnel classification;
5. severity;
6. verbatim evidence traceability.

Use fully correct records for the main accuracy gate. A high average across dimensions must not conceal a systematic safety or defect-coding failure.

## Recommended correction loop

1. Group audit errors by rule, not only by record.
2. Update definitions and boundary examples.
3. Re-annotate affected records or the full set when the rule is broad.
4. Rerun validation, statistics, and the quality gate.
5. Preserve the prior taxonomy and audit result for reproducibility.
