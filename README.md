# JUDGEFLOW AI

## Agentic Hackathon Screening & Judge-Assist System

JUDGEFLOW AI is an AI-assisted screening system designed to help hackathon judges analyze and review multiple project submissions in a structured and evidence-aware way.

## Problem

Hackathon judges may need to review many projects across different domains. Each project can have different problem statements, solutions, technologies, AI approaches, and implementation evidence.

Manually comparing multiple submissions can take significant time and may make structured comparison difficult.

## Solution

JUDGEFLOW AI provides an agentic screening workflow that analyzes submitted projects and presents structured information for human judges.

It analyzes:

- Problem statement
- Proposed solution
- Target users
- Technologies
- Agentic AI capability
- Implementation and demo evidence
- Similarity with other submitted projects
- Technical evaluation
- Uniqueness
- Verification and missing evidence
- Priority for human review

## Agentic Workflow

**PERCEIVE → UNDERSTAND → CLASSIFY → DISCOVER → COMPARE → EVALUATE → VERIFY → PRIORITIZE → HUMAN REVIEW**

The workflow uses conditional reasoning to determine what should happen next.

For example:

- If important evidence is missing → flag it for verification.
- If similar projects are detected → perform a detailed comparison.
- If evidence is insufficient or contradictory → recommend human review.
- If a project contains strong technical or innovative aspects → highlight it for judge attention.

## Evaluation Criteria

| Criterion | Weight |
|---|---:|
| Technical Implementation & Architecture | 25% |
| Agentic AI Design | 20% |
| Evaluation, Reliability & Responsible AI | 20% |
| Innovation & Technical Originality | 15% |
| Real-World Utility | 10% |
| Working Demo & Communication | 10% |

Each criterion is scored from **0–10** and converted into a weighted score out of **100**.

## Key Features

- Multi-project screening
- Score-based project overview
- Projects sorted by screening score
- Project-level detailed analysis
- Similarity discovery
- Competitive comparison
- Uniqueness review
- Evidence-aware verification
- Confidence indication
- Missing-evidence detection
- Priority recommendation
- Human-in-the-loop review
- Decision trace for judge assistance

## Human-in-the-Loop

JUDGEFLOW AI is a **judge-assist system**, not an autonomous judge.

The system provides structured analysis, scores, evidence, concerns, and recommendations to help judges review submissions.

The final finalist and winner decisions remain with **human judges**.

## Evidence Policy

JUDGEFLOW AI is designed to work only with information available in the submitted project.

It should not invent:

- Testing results
- Users
- Technologies
- GitHub activity
- Deployment information
- Impact claims
- Implementation claims

When evidence is missing, the system identifies the missing information and can recommend human review instead of assuming an answer.

## Technology

- Python
- HTML
- CSS
- JavaScript
- Python HTTP Server
- OpenRouter API
- AI-assisted analysis
- Rule-based verification and scoring support

## Running the Project

### 1. Create a virtual environment

```bash
python -m venv venv
