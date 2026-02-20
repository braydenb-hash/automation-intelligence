# Claude Code + Trigger.dev: I'm Never Building Agents the Same Way

**Use Case:** Research Analysis
**Skill Level:** ⭐⭐⭐ Advanced
**Estimated Cost:** $20-50/month for Trigger.dev + $0.10-0.50 per company research (Claude API costs) + ClickUp API free tier
**Complexity:** High
**Value Score:** 9/10
**Source:** [Nate Herk](https://www.youtube.com/watch?v=UGIZnh6HNLc)
**Published:** 2026-02-20

## Overview

An AI agent system that monitors ClickUp tasks for company research requests, automatically researches companies using web scraping and Claude AI, posts comprehensive research briefs as comments, and can engage in follow-up conversations. Built using Claude Code for development and deployed to Trigger.dev for cloud execution with scheduled polling and automatic retries.

## Tech Stack

- **Claude Code**
- **Trigger.dev**
- **Anthropic Claude API**
- **ClickUp API**
- **YouTube API**

## Workflow Diagram

```mermaid
graph LR
    A[ClickUp API: User adds company name as task in ClickUp list]
    A --> B[Trigger.dev: Scheduled poller checks ClickUp every 2 minutes for new t...]
    B --> C[Trigger.dev: When new task detected, trigger company researcher agent]
    C --> D[Anthropic Claude API: Researcher agent uses search_web tool multiple times to g...]
    D --> E[Anthropic Claude API: Agent uses read_URL tool to extract detailed information ...]
    E --> F[ClickUp API: Generate comprehensive research brief and post as comment...]
    F --> G[Trigger.dev: Follow-up poller monitors tasks for user questions (runs ...]
    G --> H[Anthropic Claude API: Responder agent reads task context and answers follow-up ...]
    H --> I[ClickUp API: Post follow-up response as comment in ClickUp task]
```

## Step-by-Step

1. **[ClickUp API]** User adds company name as task in ClickUp list
   - Manual trigger - user creates task with company name
2. **[Trigger.dev]** Scheduled poller checks ClickUp every 2 minutes for new tasks
   - ClickUp research poller runs on 2-minute schedule with automatic retry on failure
3. **[Trigger.dev]** When new task detected, trigger company researcher agent
   - Orchestration between poller and researcher agent
4. **[Anthropic Claude API]** Researcher agent uses search_web tool multiple times to gather information
   - Non-deterministic agent decides how many searches needed (typically 2-3 invocations)
5. **[Anthropic Claude API]** Agent uses read_URL tool to extract detailed information from relevant websites
   - Agent autonomously selects which URLs to read based on search results
6. **[ClickUp API]** Generate comprehensive research brief and post as comment on ClickUp task
   - Includes company overview, key facts, and relevant data; marks task as complete
7. **[Trigger.dev]** Follow-up poller monitors tasks for user questions (runs every 2 minutes)
   - Separate scheduled task checks for @mentions or follow-up questions
8. **[Anthropic Claude API]** Responder agent reads task context and answers follow-up questions
   - Agent understands context from previous research and can perform additional searches if needed
9. **[ClickUp API]** Post follow-up response as comment in ClickUp task
   - Conversational agent maintains context across multiple interactions

## When to Use This

- Need automated company research for sales prospecting or competitive analysis
- Want conversational AI agents that can handle follow-up questions with context
- Require reliable cloud-based automation with retries and scheduling
- Building custom AI workflows that need to run 24/7 without local machine
- Need non-deterministic agents that make decisions about which tools to use

- Simple linear automations that don't require AI decision-making (use Zapier/Make instead)
- Budget is extremely limited (agent API calls add up quickly)
- Don't have coding experience (requires TypeScript knowledge despite Claude Code assistance)
- Need instant real-time responses (polling every 2 minutes has delay)
- Working with highly sensitive data that cannot use external AI APIs

## Alternatives

- Use Make.com or n8n with OpenAI API for simpler deterministic workflows
- Build custom agents with LangChain or CrewAI and deploy to Modal or Railway
- Use Relevance AI for no-code AI agent deployment with built-in tools
- Implement webhooks instead of polling for real-time triggering
- Use Zapier AI Actions for simpler single-step AI automations

## Next Steps

- [ ] Test this workflow
- [ ] Customize for your use case
- [ ] Integrate with existing systems
