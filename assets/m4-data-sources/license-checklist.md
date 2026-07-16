# Paid data license due-diligence checklist

Ten questions to send a vendor in writing before signing a yearly paid
data contract. If the vendor will not answer in writing, that itself is
the answer.

The point of this checklist is to surface ambiguity before integration,
not after. Several mid-stage AI startups have had to rip out a paid data
source three to six months after launch because the AI-use clause was
not flagged during the initial integration sprint. Cost: rebuild plus
refund plus reputation. Cheap insurance: spend an hour reading the
contract before writing the first line of integration code.

This checklist is a primer, not legal advice. When the answers carry
real risk, route them through a lawyer who knows AI and data law.

---

## 1. Derivative work rights

**What to look for:** Does the license permit derivative works
(summaries, embeddings, structured extracts, fine-tuning datasets) and
do those derivatives spawn separate obligations from the source data?
Some licenses cover derivatives under the same terms as the source;
others treat each derivative as a new licensed work with its own
restrictions. The cleanest path is explicit written permission for the
derivative types you plan to produce.

**Your notes:**

---

---

---

## 2. Redistribution and end-user exposure

**What to look for:** Can the data be exposed to end users of your
product, surfaced in an interface, embedded in a generated response,
or quoted back to a customer? Or is the data internal-use-only?
"Allowed for analytics" is not the same as "allowed in a customer-facing
LLM output." Pin the vendor on the specific output surface you plan to
ship: prompt context, retrieved context, generated text, downloadable
report, public dashboard.

**Your notes:**

---

---

---

## 3. AI-training and machine-learning clauses

**What to look for:** Does the license expressly permit or prohibit
training, fine-tuning, or otherwise improving any AI / ML system using
the data? The exact language matters. Watch for the words "train,"
"fine-tune," "improve," "develop," or "derive" attached to "AI," "ML,"
"machine learning," or "model." A clause that bans "training" may still
permit retrieval-style use; a broader clause may ban any LLM exposure
including RAG context. Ask the vendor to clarify in writing whether
each of (training, fine-tuning, RAG retrieval, prompt context) is in or
out of scope.

**Your notes:**

---

---

---

## 4. Exfiltration and outbound data flow

**What to look for:** Does the contract permit the licensed data to
leave your perimeter? Specifically, can the data be sent to a third-party
LLM provider as part of a prompt? Vendors that pre-date the LLM era
sometimes have silent assumptions about where data flows; modern AI-use
clauses are increasingly explicit on this. If you use a frontier API,
the contract needs to permit data being sent to that provider, or you
need to self-host the model.

**Your notes:**

---

---

---

## 5. Retention and post-termination obligations

**What to look for:** What happens to the data and your derivatives
when the contract ends? Must you delete embeddings? Cached outputs?
Trace logs that contain quoted source data? Some contracts require
deletion within 30 days of termination; some require deletion of
derivatives as well. If you cannot practically delete embeddings
generated from licensed data, that is a contract you cannot honor.

**Your notes:**

---

---

---

## 6. Attribution and credit requirements

**What to look for:** Does the license require attribution to the data
provider? If so, where and how must the attribution appear (in the UI,
in source code, in API responses, in derived outputs)? Some Creative
Commons variants (CC-BY) require attribution; some vendor licenses do
the same. Failing to attribute correctly is a license breach even when
the underlying use is permitted.

**Your notes:**

---

---

---

## 7. Audit rights and reporting

**What to look for:** Does the contract grant the vendor audit rights
over your usage? Are you required to report volumes, derivative outputs,
or end-user access patterns? Audit clauses are common in enterprise data
contracts; they can be benign or burdensome depending on the
implementation requirements. If audit rights exist, confirm what records
you must retain (logs of every API call against the licensed data is a
common ask) and for how long.

**Your notes:**

---

---

---

## 8. Term, renewal, and pricing escalation

**What to look for:** What is the initial term? Is there an auto-renewal
clause with a notice window? What is the price escalation cap on renewal
(typical: CPI plus 3-5%; aggressive: uncapped)? Auto-renewal clauses
combined with short cancellation windows trap teams in contracts they
intended to exit. Diary the cancellation window in your team's calendar
the day you sign.

**Your notes:**

---

---

---

## 9. Governing law, jurisdiction, and data residency

**What to look for:** Which jurisdiction governs disputes? Where is the
data physically stored? If you serve EU customers, does the vendor offer
EU-hosted endpoints and an appropriate Data Processing Agreement? If you
operate in regulated industries (healthcare, finance, defense), confirm
whether the vendor's data-residency posture matches your compliance
requirements. A vendor headquartered in a different jurisdiction than
your customer base can complicate enforcement and breach response.

**Your notes:**

---

---

---

## 10. Breach remedies, indemnity, and limitation of liability

**What to look for:** What happens if the vendor breaches the contract
(data quality failure, license terms broken on their side, breach
disclosure)? What are the remedies available to you? Conversely, what
indemnity do you owe the vendor if you breach? What is the cap on
liability, and is it tied to fees paid or set as an absolute number?
Vendors often set their own liability cap at "fees paid in the last 12
months" while expecting unbounded indemnity from you. Read both
directions of the asymmetry.

**Your notes:**

---

---

---

## After you collect the answers

1. Save the vendor's written responses alongside the signed contract.
   "We discussed this on a call" is not enforceable; "they emailed us
   the clarification on May 14" is.
2. If three or more answers are evasive, vague, or refused, that is
   itself the signal. The contract is probably broader than the sales
   conversation suggested.
3. For high-risk answers (AI-training clause unclear; data-residency
   posture wrong for your customer base), escalate to legal before
   signing. The cost of legal review is small compared to a forced
   integration teardown.
4. Re-run this checklist at every contract renewal. Vendors update
   terms between renewals; "no AI training" clauses are appearing in
   2026 renewals that did not exist in 2024 contracts.

---

## Not legal advice

This checklist is a primer to make data licensing visible as a real
concern. It is not a substitute for a lawyer who knows AI and data law.
For contracts with material risk exposure, route through counsel before
signing.
