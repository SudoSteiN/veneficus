# Ideation Protocol — Sub-protocol of Plan

This protocol is not standalone — it is activated by `plan.md` when context documents are empty or contain only template placeholders. Do not run this directly.

## Protocol

Run these phases sequentially. **Never skip a phase.** Each phase ends with a summary and confirmation before moving on.

---

### Phase 0 — Orientation

1. Greet the user warmly. Set expectations: "I'm going to ask you about 15 questions across a few topics — it usually takes around 10 minutes. By the end, I'll have everything documented and ready for you to start building."
2. Acknowledge their initial idea with enthusiasm. Then move to Phase 1.

---

### Phase 1 — The What (Problem & Vision)

**Goal**: Understand what the project is and why it matters.

Ask these questions (one at a time, with examples):

1. **Elevator pitch**: "In one or two sentences, what does this do? For example: 'An app that helps people split restaurant bills without the awkward math.'"
2. **The problem**: "What's the pain point this solves? What do people do today without it? For example: 'Right now people pass their phone around with a calculator app and it always ends up wrong.'"
3. **The spark**: "What made you want to build this? Was there a specific moment or frustration?"
4. **Alternatives**: "Is there anything out there that does something similar? What's wrong with it, or what's missing?"

**End of phase**: Summarize the problem, vision, and positioning. Confirm with the user before moving on.

---

### Phase 2 — The Who (Users & Scenarios)

**Goal**: Identify who uses this and how.

Ask these questions:

1. **Primary user**: "Who's the main person using this? For example: 'Busy parents who meal-prep on Sundays' or 'Small business owners tracking inventory.'"
2. **Other users**: "Is there anyone else who'd use it differently? An admin, a viewer, a manager? It's fine if it's just one type of user."
3. **Key scenario**: "Walk me through a typical session. Someone opens the app — then what? What are they trying to accomplish and what steps do they take?"
4. **Frequency**: "How often would someone use this? Daily, weekly, once in a while?"

**End of phase**: Derive 3-6 user stories in plain language (not formal "As a..." format yet — save that for the PRD). Summarize and confirm.

---

### Phase 3 — The How (Features & MVP Scope)

**Goal**: Define what the MVP includes and excludes.

Ask these questions:

1. **Core three**: "If this could only do THREE things, what would they be? For example, for a recipe app: 'save recipes, search by ingredient, generate a shopping list.'"
2. **Must-haves vs nice-to-haves**: "Anything else that feels essential? And anything that would be cool but could wait for later?"
3. **Definite nots**: "Anything you definitely DON'T want this to do, or want to stay away from?"
4. **Data**: "What kind of information does this track or store? For example: 'user profiles, recipes, ratings, shopping lists.'"
5. **Sharing/access**: "Is this for one person, or do people share things? Is there any notion of public vs. private?"

**End of phase**: Present the proposed MVP scope as a numbered list of features (4-8). Clearly separate "MVP" from "Future." Negotiate if the user pushes for too much — steer toward the smallest useful version. Confirm.

---

### Phase 4 — The Shape (Platform & Technical Context)

**Goal**: Gather enough context to make technical decisions.

Ask these questions:

1. **Platform**: "Where does this live? A website, a phone app, a desktop tool, a command-line tool? For example: 'A website that also works well on phones.'"
2. **Look and feel**: "Any sense of the vibe? Clean and minimal? Colorful and playful? Dark mode? Don't worry about specifics — just the general feel."
3. **Scale**: "How many people do you imagine using this? Just you, a handful of friends, hundreds, thousands? No wrong answer — it just affects how we set things up."
4. **Integrations**: "Does this need to connect to anything else? Email, social media, a calendar, a payment system, another app?"

**End of phase**: Summarize the platform, aesthetic, scale, and integration requirements. Confirm.

---

### Phase 5 — Synthesis

**Goal**: Present everything back in plain language for final approval.

Present a structured summary covering:
- **What it is** (one paragraph)
- **Who it's for** (the primary user)
- **What it does** (MVP features, numbered)
- **What it doesn't do** (explicitly excluded)
- **How it works** (platform, access model)
- **Technical decisions you'll make** (preview — e.g., "I'll set it up as a Next.js web app with a SQLite database since it's just for you and a few friends")

**Critical**: End with: "Does this capture your vision? I'll use this to generate all the project documents. Anything you want to change before I write them?"

**Wait for explicit approval before proceeding to Phase 6.** If the user has changes, incorporate them and re-present the summary.

---

### Phase 6 — Document Generation

**Goal**: Write all four context documents.

Generate the documents in this order:

#### 6a. decisions.md
Write to `.veneficus/docs/decisions.md`. One entry per technical decision made during the conversation. Each entry follows this format:

```markdown
## [Decision Title]
- **Date**: [today's date]
- **Context**: [What the user said that led to this decision]
- **Decision**: [What was decided and why]
- **Consequences**: [Trade-offs, what this enables, what it limits]
```

Include decisions about: tech stack, database, architecture pattern, authentication approach, deployment target, key library choices, MVP scope cuts.

#### 6b. PRD.md
Write to `.veneficus/docs/PRD.md`. Follow the structure in `.veneficus/templates/PRD.template.md`:
- **Project Name**: from the conversation
- **Problem Statement**: from Phase 1
- **Success Criteria**: 3-5 measurable outcomes derived from the conversation
- **Scope — In Scope**: MVP features from Phase 3
- **Scope — Out of Scope**: "Future" items and "Definite nots" from Phase 3
- **User Stories**: formalize the plain-language stories from Phase 2 into "As a [user], I want [action] so that [benefit]" format
- **Technical Constraints**: from Phase 4 (platform, scale, integrations)
- **Dependencies**: external services, APIs, libraries the project will need
- **Timeline**: Phase 1 = MVP features, Phase 2 = nice-to-haves

#### 6c. architecture.md
Write to `.veneficus/docs/architecture.md`. Follow the structure in `.veneficus/templates/architecture.template.md`:
- **Overview**: one-paragraph system description
- **System Diagram**: ASCII art showing major components and their relationships
- **Components**: one section per major component (frontend, backend, database, external services). Each with Purpose, Technology, Interface, Data.
- **Data Models**: define the core entities and their fields
- **API Contracts**: key endpoints with request/response shapes
- **Key Design Decisions**: reference decisions.md entries
- **Conventions**: file naming, code style, error handling, testing conventions appropriate for the chosen stack

Make reasonable, opinionated tech stack choices based on the platform, scale, and features. Don't hedge — pick a stack and commit.

#### 6d. features.json
Write to `.veneficus/docs/features.json`. Follow the schema in `.veneficus/templates/features.template.json`:
- **project**: the project name
- **features**: array of 4-8 feature objects
  - **id**: `feat-001`, `feat-002`, etc.
  - **name**: short feature name
  - **description**: what it does
  - **status**: `"pending"` (all start pending)
  - **priority**: 1-based, ordered by build dependency (build foundational features first)
  - **acceptance_criteria**: array of specific, testable strings. NOT vague ("works well") — concrete ("User can create an account with email and password and receives a confirmation message")
  - **files**: empty array (to be filled during build)
  - **validate**: empty string (to be filled during build)
  - **depends_on**: array of feature IDs this depends on (e.g., auth depends on user model)
  - **notes**: empty string

---

### Phase 7 — Transition to Planning

**Goal**: Confirm what was created and transition to the planning phase.

1. List all files that were created/updated
2. Show the features in recommended build order (by priority and dependencies)
3. Announce transition: "Your project is now documented. I'll continue by creating an implementation plan for your first feature. Say **stop here** if you'd rather review the docs first."
4. If the user says "stop here," end with: "No problem. When you're ready, run `just plan \"your first feature\"` to pick up where we left off."
5. Otherwise, continue into the planning phases (Phase 0b onward in plan.md).

---

## Rules

- **This is a conversation, not a questionnaire.** Adapt based on answers. If the user already answered a question in a previous response, don't ask it again.
- **Never dump all questions at once.** One question (or small cluster) at a time.
- **Never proceed past Phase 5 without explicit user approval.**
- **Never write vague acceptance criteria.** Every criterion must be testable by an agent: it should be clear whether it passes or fails.
- **Always follow template structures** for generated documents. Other agents depend on these formats.
- **4-8 MVP features.** If you have more than 8, the scope is too big — cut more aggressively. If fewer than 4, you haven't explored enough.
- **Log ALL technical decisions** in decisions.md, even "obvious" ones like choosing a database. Future agents need the rationale.
