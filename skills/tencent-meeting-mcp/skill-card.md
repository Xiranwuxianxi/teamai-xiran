## Description: <br>
腾讯会议 helps agents schedule, update, cancel, and inspect Tencent Meeting meetings, manage participants and waiting rooms, retrieve recordings, transcripts, and AI minutes, request recording permissions, convert meeting times, check skill versions, and submit confirmed feedback. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[wemeeting](https://clawhub.ai/user/wemeeting) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Employees, external collaborators, and agents use this skill to manage Tencent Meeting workflows, including meeting lifecycle actions, participant lookup, recording and transcript retrieval, AI minutes, permission requests, and feedback reporting. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill uses a Tencent Meeting account token and can read sensitive meeting details, participants, recordings, transcripts, and AI minutes. <br>
Mitigation: Install only when the publisher and integration are trusted, protect TENCENT_MEETING_TOKEN, and review returned meeting content before sharing it. <br>
Risk: The skill can create, modify, or cancel meetings. <br>
Mitigation: Review confirmation prompts carefully and proceed only after the intended meeting action and target meeting are clear. <br>
Risk: Recording permission requests and feedback reports may expose meeting or participant information if handled carelessly. <br>
Mitigation: Use the documented preview, confirmation, and redaction steps before submitting recording permission requests or feedback. <br>


## Reference(s): <br>
- [ClawHub Tencent Meeting Skill Page](https://clawhub.ai/wemeeting/tencent-meeting-skill) <br>
- [Tencent Meeting](https://meeting.tencent.com/) <br>
- [Tencent Meeting AI Skill Token Page](https://meeting.tencent.com/ai-skill) <br>
- [Tencent Meeting MCP Endpoint](https://mcp.meeting.tencent.com/mcp/wemeet-open/v1) <br>
- [API References](references/api_references.md) <br>
- [Error Dictionary](references/error_dictionary.md) <br>
- [Feedback Rules](references/feedback_rules.md) <br>
- [Privacy Policy](references/privacy_policy.md) <br>
- [Version Management](references/version_management.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, API Calls, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown or text responses with MCP tool calls and shell command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires python3 and TENCENT_MEETING_TOKEN; meeting changes, recording permission requests, and feedback reports require user confirmation.] <br>

## Skill Version(s): <br>
1.0.10 (source: server release evidence and config.json v1.0.10) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
