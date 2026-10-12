## Description: <br>
Multi-source deep research agent. Searches the web, synthesizes findings, and delivers cited reports. No API keys required. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[parags](https://clawhub.ai/user/parags) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
External users and developers use this skill to have an agent plan research questions, search public web and news sources, read selected pages, and produce cited research reports. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill searches public sources and fetches selected third-party pages, which can expose sensitive research topics to external services. <br>
Mitigation: For sensitive or regulated topics, keep results in chat only or avoid external web fetching. <br>
Risk: Web research results can contain stale, incorrect, or single-source claims. <br>
Mitigation: Require citations, cross-reference important claims, flag unverified findings, and acknowledge gaps when good evidence is unavailable. <br>
Risk: Following the workflow may write research reports to the local filesystem. <br>
Mitigation: Review saved report paths and contents before sharing or retaining sensitive outputs. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/parags/skills/deep-research-pro) <br>
- [OpenClaw](https://github.com/openclaw/openclaw) <br>
- [uv](https://github.com/astral-sh/uv) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, code, configuration, guidance] <br>
**Output Format:** [Markdown reports with citations, optional JSON results, and inline shell commands] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May save reports locally under ~/clawd/research when the agent follows the skill workflow.] <br>

## Skill Version(s): <br>
1.0.2 (source: server-resolved release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
