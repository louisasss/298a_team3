# ADR 003: Single tool-using agent
**Status:** Proposed; classifier approved, LLM choice pending
**Date:** 2026-11-03
**Author:** Louisa Stumpf
**Deciders:** Louisa Stumpf, Akshit Tyagi, Sang Ah Lee, Pragya Priyadarshini

## Context
Our project involves developing a single tool-using agent in a CI/CD pipeline to compare against three other more complex agents to be made in 298B. The Agent runs at two stages within the pipeline. First in the GitHub Actions test stage acting as a reviewer leaving notes about the test results for each PR and a release brief for each release. Second in the Argo Rollouts canary analysis stage acting as a judge that analyzes performance during the canary rollout and returns a decision: promote, abort, or inconclusive. There is no GPU in the CI runner or the cluster therefore the team must decide on a hosted LLM. Professor confirmed that adding a trained classifier as a tool is needed to meet the requirements. (See guidelines "It must be trained, fine-tuned or adapted by your team — a hosted API call is not one of your four models.”)

## Decision Drivers
1. Reliable tool calling - Agent performance relies on properly selecting, calling, and reading the results of our tools. Model must reliably return well-formed arguments.
2. Valid structured JSON output every time - Agent requires reliable JSON outputs, to ensure this we select a provider that allows "structured output" mode so that responses are formed according to our schema and Argo can read successfully. 
3. Latency within analysis-stage deadline - Agent decision made in analysis stage must finish before the Web provider timeout occurs.
4. Resistance to prompt injection - Agent needs to be resistant to instructions embedded in the text it is reviewing.
5. Cost per decision - Low consideration because we are only considering small and mid-tier models but still relevant because it is one of the values we are scoring the candidate models on.

## Decision
**Model is a configuration value:** We read the model from configuration file rather than hard coding to allow us to test and compare multiple models for best performance. The same config mechanism is used in both stages of agent implementation. Changing the model must only require a config change, not a code change. 

**Model selection by evaluation, not yet decided:** We will select our model by running each candidate on the same recorded scenarios and recording correct decisions vs expected outcome, valid JSON rate, seconds per decision, tokens per decision, and cost per decision. We selected two candidate models, one small tier model and one mid-tier model. We eliminated large tier models from our model candidates because the logic performed is not overly complex and the size of the model relates to speed which is one of our decision drivers. The recorded scenarios will come from the replay mode created with work from Linear Issue T3-93: Build the shared read-only tools and fallback logic. Candidate comparison table will be added to ADR when decision is made by team.

## Tools
All tools are read-only. No tool can write to the cluster, the repository, or Prometheus. 

**CI stage tools:**
* git_diff, diff between commits
* test_results, test report from the CI test job

**Analysis stage tools:**
* prometheus_query, metrics via the Prometheus HTTP API
* rollout_status, Argo Rollout status
* pod_logs, canary pod logs
* canary_classifier, team-trained model over canary vs stable metrics

**Budget per decision:**
| Limit | CI mode | Analysis Mode | agreement register ID |
| --- | --- | --- | --- |
| Max seconds |  |  | D01, D04 |
| Max tool calls |  |  | D26 |
| Max tokens |  |  | D26 |
| Max cost (USD) |  |  | D26 |

Constraint: agent deadline < Web provider timeoutSeconds < analysis interval

**Fallback:**
Fallback is triggered by one of three failure types: the model call errors, the agent exceeds its time budget, or the agent returns invalid JSON. 

* At the CI stage when fallback occurs the PR proceeds with an "agent unavailable" comment attached, so the reviewers know there is no agent input. If the release brief generation fails, the release still proceeds with the brief marked unavailable. 
* In the analysis stage fallback returns the static check's results if there is data. If there is no data to make a decision with using the static results, fallback returns inconclusive which pauses the rollout at its current step until manually reviewed by a human who promotes or aborts the release.

Promote is never the default fallback as it would allow the release to proceed with silent errors that are found by the users. Fallback usage will be flagged with the reason for fallback given. 

**Contract:**
JSON schemas live in agents/common/schemas/: ci_input, ci_output, analysis_input, analysis_output. Each has one test with one valid example and one invalid example.

## Considered options
1. Hosted LLM + team-trained classifier tool; chosen option
2. Fine-tuned model served by a provider; not chosen due to concerns about being able to source training data before deadline
3. Hosted LLM, prompted, with tools only; not chosen because it does not meet project requirements
4. Self-hosted open-weight model; not chosen because neither stage of the agent has GPU
5. Hard coding one model; not chosen because comparing models would mean having to change code.

## Consequences
**Positive:**
* Because the model is a config value, we can compare models by changing the config, without having to change the code. 
* Because all of the tools for our agent are read-only, the worst thing a faulty agent can do is return a bad decision, it cannot write any changes based on the bad decision which protects our pipeline.
* Because of the agreed schemas acting as fixed contracts, the team can work in parallel. Each team member can design against the schema instead of waiting for other team members to complete work.
* Because the fallback uses the static check, the agent pipeline cannot perform worse than the non-agent pipeline when the agent fails.

**Negative:**
* Because the agent uses a hosted LLM, the pipeline depends on an outside provider; when the provider is down, the agent fails and the pipeline falls back to the non-agentic pipeline. When the provider is slow the agent will exceed its time budget and fail causing the pipeline to fallback.
* Each agent decision has a cost, so the team must limit token usage to limit spending.
* Selecting the model by evaluation means the model choice waits until we can compare the candidates with replay mode.