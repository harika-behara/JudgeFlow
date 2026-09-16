import json
import os
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests


HOST = "127.0.0.1"
PORT = 8000
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DOMAINS = [
    "Education",
    "Healthcare",
    "Finance",
    "Enterprise Productivity",
    "Developer Tools",
    "Data",
    "Sustainability",
    "Consumer Apps",
    "Other",
]

WEIGHTS = {
    "Technical Implementation & Architecture": 25,
    "Agentic AI Design": 20,
    "Evaluation, Reliability & Responsible AI": 20,
    "Innovation & Technical Originality": 15,
    "Real-World Utility": 10,
    "Working Demo & Communication": 10,
}


DEMO_PROJECTS = [
    {
        "team": "Team Aster",
        "project": "CampusShield",
        "domain": "Education",
        "problem": "Students struggle to report urgent campus safety issues and find the correct response quickly.",
        "solution": "An agent monitors a safety request, classifies urgency, identifies the right campus resource, and creates an escalation plan.",
        "users": "Students, security staff and administrators",
        "tech": "Python, FastAPI, OpenRouter, rule-based verification",
        "agentic": "The agent classifies the request, chooses the next action, checks missing evidence and escalates uncertain cases for human review.",
        "evidence": "Working prototype with simulated emergency and non-emergency test cases.",
    },
    {
        "team": "Team Nova",
        "project": "StudyRoute",
        "domain": "Education",
        "problem": "Students waste time deciding what to study when they have multiple topics and limited time.",
        "solution": "An AI planner creates a study sequence based on topics, deadlines and available hours.",
        "users": "College students",
        "tech": "Python, LLM API, SQLite",
        "agentic": "The planner breaks the goal into tasks and re-plans when a task is marked incomplete.",
        "evidence": "Prototype demonstrates planning with manually entered subjects and deadlines.",
    },
    {
        "team": "Team GreenByte",
        "project": "WasteWise",
        "domain": "Sustainability",
        "problem": "Small campuses have difficulty identifying recurring waste-management issues.",
        "solution": "An agent reviews submitted waste reports, groups recurring issues and proposes operational actions.",
        "users": "Campus facility teams",
        "tech": "Python, FastAPI, LLM API",
        "agentic": "The system groups reports, checks for repeated issues and creates an action queue.",
        "evidence": "Demo uses sample waste reports and displays generated action items.",
    },
    {
        "team": "Team MedAssist",
        "project": "ClinicFlow",
        "domain": "Healthcare",
        "problem": "Clinic staff spend time manually organizing appointment requests.",
        "solution": "An assistant categorizes requests and prepares a scheduling queue for staff review.",
        "users": "Clinic administrative staff",
        "tech": "Python, web UI, LLM API",
        "agentic": "The agent categorizes requests and flags incomplete information before staff review.",
        "evidence": "Prototype tested with sample appointment requests.",
    },
    {
        "team": "Team DevSpark",
        "project": "CodeTriage",
        "domain": "Developer Tools",
        "problem": "Developers receive many bug reports and need to identify which information is missing.",
        "solution": "An agent analyzes bug reports, detects missing reproduction details and prepares a triage summary.",
        "users": "Software development teams",
        "tech": "Python, GitHub-style issue data, LLM API",
        "agentic": "The agent checks issue completeness, asks what evidence is missing and prepares a structured triage record.",
        "evidence": "Demo processes sample issue reports.",
    },
]


def tokenize(text):
    return set(re.findall(r"[a-zA-Z0-9]+", str(text).lower()))


def similarity(project_a, project_b):
    fields = [
        "problem",
        "solution",
        "users",
        "tech",
        "agentic",
    ]

    text_a = " ".join(str(project_a.get(field, "")) for field in fields)
    text_b = " ".join(str(project_b.get(field, "")) for field in fields)

    words_a = tokenize(text_a)
    words_b = tokenize(text_b)

    if not words_a or not words_b:
        return 0.0

    common = len(words_a.intersection(words_b))
    total = len(words_a.union(words_b))

    return round((common / max(total, 1)) * 100, 1)


def local_scores(project):
    text = " ".join(
        str(project.get(field, ""))
        for field in [
            "problem",
            "solution",
            "users",
            "tech",
            "agentic",
            "evidence",
        ]
    ).lower()

    scores = {
        "Technical Implementation & Architecture": 5,
        "Agentic AI Design": 5,
        "Evaluation, Reliability & Responsible AI": 4,
        "Innovation & Technical Originality": 5,
        "Real-World Utility": 5,
        "Working Demo & Communication": 4,
    }

    if len(project.get("tech", "")) > 35:
        scores["Technical Implementation & Architecture"] += 2

    agentic_words = [
        "conditional",
        "escalat",
        "re-plan",
        "re-plann",
        "next action",
        "chooses",
        "decision",
        "verify",
        "verification",
    ]

    if any(word in text for word in agentic_words):
        scores["Agentic AI Design"] += 3

    evaluation_words = [
        "test",
        "tested",
        "verification",
        "verify",
        "evaluation",
    ]

    if any(word in text for word in evaluation_words):
        scores["Evaluation, Reliability & Responsible AI"] += 2

    if "prototype" in text or "demo" in text:
        scores["Working Demo & Communication"] += 2

    utility_words = [
        "real-world",
        "students",
        "clinic",
        "campus",
        "developers",
        "staff",
    ]

    if any(word in text for word in utility_words):
        scores["Real-World Utility"] += 2

    if len(project.get("solution", "")) > 90:
        scores["Innovation & Technical Originality"] += 1

    return {
        key: min(10, value)
        for key, value in scores.items()
    }


def weighted_total(scores):
    total = 0.0

    for criterion, weight in WEIGHTS.items():
        score = float(scores.get(criterion, 0))
        total += score * weight / 10

    return round(total, 1)


def find_missing(project):
    required_fields = [
        ("problem", "Problem statement"),
        ("solution", "Proposed solution"),
        ("users", "Target users"),
        ("tech", "Technologies"),
        ("agentic", "Agentic AI description"),
        ("evidence", "Implementation/demo evidence"),
    ]

    missing = []

    for field, label in required_fields:
        if not str(project.get(field, "")).strip():
            missing.append(label)

    return missing


def analyze_projects(projects):
    results = []

    for project in projects:
        scores = local_scores(project)
        total = weighted_total(scores)

        similar_projects = []

        for other in projects:
            if other is project:
                continue

            similarity_score = similarity(project, other)

            if similarity_score >= 12:
                similar_projects.append(
                    {
                        "project": other.get("project", "Unknown"),
                        "team": other.get("team", "Unknown"),
                        "similarity": similarity_score,
                    }
                )

        similar_projects.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        missing = find_missing(project)

        if similar_projects:
            uniqueness_status = "HUMAN_REVIEW_RECOMMENDED"
        else:
            uniqueness_status = "UNIQUE"

        confidence = 92

        if missing:
            confidence -= len(missing) * 10

        if similar_projects:
            confidence -= 15

        confidence = max(40, confidence)

        concerns = []

        if missing:
            concerns.append(
                "Missing evidence: " + ", ".join(missing)
            )

        if similar_projects:
            concerns.append(
                "Similar submitted projects require human comparison."
            )

        if not concerns:
            concerns.append(
                "No major missing evidence detected from submitted fields."
            )

        priority = (
            "HIGH_REVIEW"
            if total >= 75
            else "NORMAL_REVIEW"
        )

        result = {
            "rank": 0,
            "team": project.get("team", "Not provided"),
            "project": project.get("project", "Not provided"),
            "domain": project.get("domain", "Other"),
            "score": total,
            "scores": scores,
            "priority": priority,
            "understanding": {
                "problem": project.get(
                    "problem",
                    "Not provided",
                ),
                "solution": project.get(
                    "solution",
                    "Not provided",
                ),
                "users": project.get(
                    "users",
                    "Not provided",
                ),
                "technologies": project.get(
                    "tech",
                    "Not provided",
                ),
                "agentic_capability": project.get(
                    "agentic",
                    "Not provided",
                ),
                "implementation_evidence": project.get(
                    "evidence",
                    "Not provided",
                ),
            },
            "similar_projects": similar_projects,
            "uniqueness": {
                "status": uniqueness_status,
                "reason": (
                    "The status is based only on comparison with "
                    "the projects submitted to this screening session."
                ),
                "evidence": (
                    "Similarity is a screening signal. "
                    "Human judges make the final originality decision."
                ),
            },
            "verification": {
                "status": (
                    "REVIEW_REQUIRED"
                    if missing or similar_projects
                    else "CHECKED"
                ),
                "confidence": confidence,
                "missing_evidence": missing,
                "concerns": concerns,
            },
            "recommendation": (
                "Prioritize this project for detailed judge attention "
                "based on its screening score and available evidence."
            ),
            "human_review": (
                "Final finalist and winner decisions remain with "
                "human judges."
            ),
        }

        results.append(result)

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    for index, result in enumerate(results, start=1):
        result["rank"] = index

    return results


def ask_openrouter(project):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return None

    prompt = """
You are a hackathon screening assistant.

Analyze the submitted project using ONLY the information provided.

Return ONLY valid JSON.

The JSON must contain exactly this structure:

{
  "scores": {
    "Technical Implementation & Architecture": 0,
    "Agentic AI Design": 0,
    "Evaluation, Reliability & Responsible AI": 0,
    "Innovation & Technical Originality": 0,
    "Real-World Utility": 0,
    "Working Demo & Communication": 0
  }
}

Each score must be an integer from 0 to 10.

Do not invent testing results.
Do not invent users.
Do not invent technologies.
Do not assume deployment.
Do not assume GitHub activity.
Do not assume impact.

Submitted project:
""" + json.dumps(
        project,
        ensure_ascii=False,
        indent=2,
    )

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0,
            },
            timeout=20,
        )

        if not response.ok:
            return None

        body = response.json()

        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        match = re.search(
            r"\{.*\}",
            content,
            re.DOTALL,
        )

        if not match:
            return None

        parsed = json.loads(match.group(0))
        ai_scores = parsed.get("scores", {})

        if not all(
            criterion in ai_scores
            for criterion in WEIGHTS
        ):
            return None

        clean_scores = {}

        for criterion in WEIGHTS:
            value = int(ai_scores[criterion])
            value = max(0, min(10, value))
            clean_scores[criterion] = value

        return clean_scores

    except Exception:
        return None


def run_analysis(projects):
    results = analyze_projects(projects)

    project_lookup = {
        project.get("project", ""): project
        for project in projects
    }

    for result in results:
        project = project_lookup.get(
            result["project"]
        )

        if project is None:
            continue

        ai_scores = ask_openrouter(project)

        if ai_scores:
            result["scores"] = ai_scores
            result["score"] = weighted_total(
                ai_scores
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    for index, result in enumerate(results, start=1):
        result["rank"] = index

    return results


def make_page():
    domain_options = ""

    for domain in DOMAINS:
        domain_options += (
            '<option value="'
            + domain
            + '">'
            + domain
            + "</option>"
        )

    demo_json = json.dumps(
        DEMO_PROJECTS,
        ensure_ascii=False,
    )

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<title>JUDGEFLOW AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    color: #17202a;
}

header {
    background: #182848;
    color: white;
    padding: 24px 30px;
}

header h1 {
    margin: 0 0 6px 0;
    font-size: 30px;
}

header p {
    margin: 0;
    opacity: 0.9;
}

main {
    max-width: 1250px;
    margin: 25px auto;
    padding: 0 18px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

label {
    display: block;
    font-weight: bold;
    margin-top: 8px;
}

input,
textarea,
select {
    width: 100%;
    padding: 11px;
    margin-top: 7px;
    margin-bottom: 12px;
    border: 1px solid #ccd3da;
    border-radius: 7px;
    font-size: 14px;
}

textarea {
    min-height: 80px;
    resize: vertical;
}

button {
    border: none;
    border-radius: 8px;
    padding: 11px 16px;
    margin: 5px;
    background: #182848;
    color: white;
    cursor: pointer;
    font-weight: bold;
}

button:hover {
    opacity: 0.9;
}

.secondary {
    background: #e9edf2;
    color: #17202a;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 11px;
    border-bottom: 1px solid #e4e7ea;
    text-align: left;
}

th {
    background: #f5f7f9;
}

.result-row {
    cursor: pointer;
}

.result-row:hover {
    background: #f1f5f8;
}

.score {
    font-size: 21px;
    font-weight: bold;
}

.badge {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 15px;
    background: #e9edf2;
    font-size: 12px;
}

.hidden {
    display: none;
}

.criterion {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #eeeeee;
}

.detail-box {
    background: #f7f9fb;
    border-radius: 8px;
    padding: 14px;
    margin: 10px 0;
}

.big-score {
    font-size: 34px;
    font-weight: bold;
}

.small {
    color: #5d6670;
    font-size: 13px;
}

.status {
    font-weight: bold;
}

@media(max-width: 750px) {

    .grid {
        grid-template-columns: 1fr;
    }

    table {
        font-size: 12px;
    }

}

</style>
</head>

<body>

<header>

<h1>JUDGEFLOW AI</h1>

<p>
Agentic Hackathon Screening & Judge-Assist System
</p>

</header>

<main>

<div class="card">

<h2>Submission Input</h2>

<div class="grid">

<div>

<label>Team Name</label>

<input id="team">

</div>

<div>

<label>Project Name</label>

<input id="project">

</div>

<div>

<label>Domain</label>

<select id="domain">
__DOMAIN_OPTIONS__
</select>

</div>

<div>

<label>Target Users</label>

<input id="users">

</div>

</div>

<label>Problem Statement</label>

<textarea id="problem"></textarea>

<label>Proposed Solution</label>

<textarea id="solution"></textarea>

<label>
Technical Approach / Technologies
</label>

<textarea id="tech"></textarea>

<label>
How Agentic AI Works
</label>

<textarea id="agentic"></textarea>

<label>
Implementation / Demo Evidence
</label>

<textarea id="evidence"></textarea>

<button onclick="addProject()">
Add Project
</button>

<button
class="secondary"
onclick="loadDemo()"
>
Load Demo Projects
</button>

<button onclick="runFlow()">
Run JUDGEFLOW
</button>

<span id="message"></span>

</div>


<div
id="submittedCard"
class="card hidden"
>

<h2>Submitted Projects</h2>

<table>

<thead>

<tr>

<th>Project</th>
<th>Team</th>
<th>Domain</th>

</tr>

</thead>

<tbody id="submittedRows"></tbody>

</table>

</div>


<div
id="resultsCard"
class="card hidden"
>

<h2>Screening Results</h2>

<p class="small">

Projects are sorted by AI-assisted screening score.
Click any project to open its complete judge view.

</p>

<table>

<thead>

<tr>

<th>Rank</th>
<th>Project</th>
<th>Team</th>
<th>Domain</th>
<th>Score /100</th>
<th>Priority</th>

</tr>

</thead>

<tbody id="resultRows"></tbody>

</table>

</div>


<div
id="detailCard"
class="card hidden"
></div>

</main>


<script>

let projects = [];
let results = [];


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");

}


function renderSubmitted() {

    const card =
        document.getElementById(
            "submittedCard"
        );

    const rows =
        document.getElementById(
            "submittedRows"
        );

    if (projects.length === 0) {

        card.classList.add("hidden");

        return;
    }

    card.classList.remove("hidden");

    rows.innerHTML = projects.map(
        function(project) {

            return `
                <tr>
                    <td>${escapeHtml(project.project)}</td>
                    <td>${escapeHtml(project.team)}</td>
                    <td>${escapeHtml(project.domain)}</td>
                </tr>
            `;

        }
    ).join("");

}


function clearForm() {

    [
        "team",
        "project",
        "users",
        "problem",
        "solution",
        "tech",
        "agentic",
        "evidence"
    ].forEach(
        function(id) {

            document.getElementById(id).value = "";

        }
    );

}


function addProject() {

    const project = {

        team:
            document.getElementById("team").value.trim(),

        project:
            document.getElementById("project").value.trim(),

        domain:
            document.getElementById("domain").value,

        users:
            document.getElementById("users").value.trim(),

        problem:
            document.getElementById("problem").value.trim(),

        solution:
            document.getElementById("solution").value.trim(),

        tech:
            document.getElementById("tech").value.trim(),

        agentic:
            document.getElementById("agentic").value.trim(),

        evidence:
            document.getElementById("evidence").value.trim()

    };


    if (
        !project.team ||
        !project.project ||
        !project.problem ||
        !project.solution
    ) {

        document.getElementById(
            "message"
        ).textContent =
            "Please enter Team, Project, Problem and Solution.";

        return;
    }


    projects.push(project);

    renderSubmitted();

    document.getElementById(
        "message"
    ).textContent =
        "Project added successfully.";

    clearForm();

}


function loadDemo() {

    projects = __DEMO_PROJECTS__;

    renderSubmitted();

    document.getElementById(
        "message"
    ).textContent =
        projects.length +
        " demo projects loaded.";

}


async function runFlow() {

    if (projects.length === 0) {

        document.getElementById(
            "message"
        ).textContent =
            "Add or load projects first.";

        return;
    }


    document.getElementById(
        "message"
    ).textContent =
        "JUDGEFLOW is analyzing submissions...";


    try {

        const response =
            await fetch(
                "/run",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        projects: projects
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Analysis failed."
            );

        }


        results =
            data.results || [];


        renderResults();


        document.getElementById(
            "message"
        ).textContent =
            "Analysis completed successfully.";

    }

    catch (error) {

        document.getElementById(
            "message"
        ).textContent =
            "Error: " + error.message;

    }

}


function renderResults() {

    const card =
        document.getElementById(
            "resultsCard"
        );

    const rows =
        document.getElementById(
            "resultRows"
        );


    card.classList.remove("hidden");


    rows.innerHTML =
        results.map(
            function(result, index) {

                return `
                    <tr
                        class="result-row"
                        onclick="showDetail(${index})"
                    >

                        <td>
                            <b>${result.rank}</b>
                        </td>

                        <td>
                            <b>
                                ${escapeHtml(result.project)}
                            </b>
                        </td>

                        <td>
                            ${escapeHtml(result.team)}
                        </td>

                        <td>
                            ${escapeHtml(result.domain)}
                        </td>

                        <td>
                            <span class="score">
                                ${result.score}/100
                            </span>
                        </td>

                        <td>
                            <span class="badge">
                                ${escapeHtml(result.priority)}
                            </span>
                        </td>

                    </tr>
                `;

            }
        ).join("");

}


function showDetail(index) {

    const result =
        results[index];


    const detail =
        document.getElementById(
            "detailCard"
        );


    const criteria =
        Object.entries(
            result.scores
        ).map(
            function(entry) {

                const criterion =
                    entry[0];

                const score =
                    entry[1];

                return `
                    <div class="criterion">

                        <span>
                            ${escapeHtml(criterion)}
                            (${getWeight(criterion)}%)
                        </span>

                        <b>
                            ${score}/10
                        </b>

                    </div>
                `;

            }
        ).join("");


    let similarHtml =
        "<li>No strong similarity signal among submitted projects.</li>";


    if (
        result.similar_projects &&
        result.similar_projects.length > 0
    ) {

        similarHtml =
            result.similar_projects.map(
                function(item) {

                    return `
                        <li>
                            ${escapeHtml(item.project)}
                            —
                            ${escapeHtml(item.team)}
                            —
                            ${item.similarity}% similarity signal
                        </li>
                    `;

                }
            ).join("");

    }


    let missingHtml =
        "None reported.";

    if (
        result.verification.missing_evidence &&
        result.verification.missing_evidence.length
    ) {

        missingHtml =
            result.verification
                .missing_evidence
                .map(
                    function(item) {
                        return escapeHtml(item);
                    }
                )
                .join(", ");

    }


    detail.innerHTML = `

        <h2>
            ${escapeHtml(result.project)}
        </h2>

        <p>
            <b>
                ${escapeHtml(result.team)}
            </b>
            ·
            ${escapeHtml(result.domain)}
        </p>


        <div class="detail-box">

            <div class="small">
                AI-assisted screening score
            </div>

            <div class="big-score">
                ${result.score}/100
            </div>

            <div class="small">
                Rank ${result.rank}
            </div>

        </div>


        <h3>
            1. Understanding
        </h3>

        <div class="detail-box">

            <p>
                <b>Problem:</b>
                ${escapeHtml(
                    result.understanding.problem
                )}
            </p>

            <p>
                <b>Solution:</b>
                ${escapeHtml(
                    result.understanding.solution
                )}
            </p>

            <p>
                <b>Target Users:</b>
                ${escapeHtml(
                    result.understanding.users
                )}
            </p>

            <p>
                <b>Technologies:</b>
                ${escapeHtml(
                    result.understanding.technologies
                )}
            </p>

            <p>
                <b>Agentic AI Capability:</b>
                ${escapeHtml(
                    result.understanding
                        .agentic_capability
                )}
            </p>

            <p>
                <b>Implementation Evidence:</b>
                ${escapeHtml(
                    result.understanding
                        .implementation_evidence
                )}
            </p>

        </div>


        <h3>
            2. Evaluation & Scoring
        </h3>

        <div class="detail-box">

            ${criteria}

            <p>
                <b>
                    Weighted Total:
                    ${result.score}/100
                </b>
            </p>

        </div>


        <h3>
            3. Similarity Discovery
        </h3>

        <div class="detail-box">

            <ul>
                ${similarHtml}
            </ul>

        </div>


        <h3>
            4. Uniqueness
        </h3>

        <div class="detail-box">

            <p>
                <b>
                    Status:
                    ${escapeHtml(
                        result.uniqueness.status
                    )}
                </b>
            </p>

            <p>
                ${escapeHtml(
                    result.uniqueness.reason
                )}
            </p>

            <p>
                ${escapeHtml(
                    result.uniqueness.evidence
                )}
            </p>

        </div>


        <h3>
            5. Verification
        </h3>

        <div class="detail-box">

            <p>
                <b>Status:</b>
                ${escapeHtml(
                    result.verification.status
                )}
            </p>

            <p>
                <b>Confidence:</b>
                ${result.verification.confidence}%
            </p>

            <p>
                <b>Missing Evidence:</b>
                ${missingHtml}
            </p>

            <p>
                <b>Concerns:</b>
                ${escapeHtml(
                    result.verification.concerns.join(" ")
                )}
            </p>

        </div>


        <h3>
            6. Priority Recommendation
        </h3>

        <div class="detail-box">

            ${escapeHtml(
                result.recommendation
            )}

        </div>


        <h3>
            7. Human Review
        </h3>

        <div class="detail-box">

            ${escapeHtml(
                result.human_review
            )}

        </div>

    `;


    detail.classList.remove("hidden");

    detail.scrollIntoView({
        behavior: "smooth"
    });

}


function getWeight(criterion) {

    const weights = {

        "Technical Implementation & Architecture": 25,

        "Agentic AI Design": 20,

        "Evaluation, Reliability & Responsible AI": 20,

        "Innovation & Technical Originality": 15,

        "Real-World Utility": 10,

        "Working Demo & Communication": 10

    };


    return weights[criterion] || 0;

}

</script>

</body>
</html>
"""

    html = html.replace(
        "__DOMAIN_OPTIONS__",
        domain_options,
    )

    html = html.replace(
        "__DEMO_PROJECTS__",
        demo_json,
    )

    return html


class JudgeFlowHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):

        body = json.dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        path = urlparse(
            self.path
        ).path

        if path == "/":

            body = make_page().encode(
                "utf-8"
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.send_header(
                "Content-Length",
                str(len(body)),
            )

            self.end_headers()

            self.wfile.write(body)

            return

        self.send_json(
            {"error": "Not found"},
            404,
        )

    def do_POST(self):

        path = urlparse(
            self.path
        ).path

        if path != "/run":

            self.send_json(
                {"error": "Not found"},
                404,
            )

            return

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            raw_body = self.rfile.read(
                content_length
            )

            payload = json.loads(
                raw_body.decode("utf-8")
            )

            projects = payload.get(
                "projects",
                [],
            )

            if not isinstance(
                projects,
                list,
            ):

                raise ValueError(
                    "Projects must be a list."
                )

            if not projects:

                raise ValueError(
                    "No projects supplied."
                )

            results = run_analysis(
                projects
            )

            self.send_json(
                {
                    "success": True,
                    "results": results,
                }
            )

        except Exception as error:

            self.send_json(
                {
                    "success": False,
                    "error": str(error),
                },
                400,
            )

    def log_message(
        self,
        format_string,
        *args,
    ):

        return


def main():

    server = HTTPServer(
        (HOST, PORT),
        JudgeFlowHandler,
    )

    print("")
    print("=" * 55)
    print("JUDGEFLOW AI")
    print("=" * 55)
    print(
        "Running at: "
        f"http://{HOST}:{PORT}"
    )
    print(
        "Press CTRL+C to stop."
    )
    print("=" * 55)
    print("")

    try:

        webbrowser.open(
            f"http://{HOST}:{PORT}"
        )

    except Exception:

        pass

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print("")
        print("JUDGEFLOW stopped.")

    finally:

        server.server_close()


if __name__ == "__main__":

    main()
