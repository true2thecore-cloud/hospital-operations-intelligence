# Guided organizational setup

The local questionnaire is runnable today. An AI-guided conversational setup can follow the same questions using the onboarding skill, but the repository does not install a hosted agent or permission dialog. Users grant account access in their approved platform, not by writing yes in a JSON file.

## Leader decisions

1. Which organization, departments and reporting timezone apply?
2. Which recurring meetings should be included? Confirm exact calendar identities, meeting end times, weekdays, exceptions and report-out order. Different names are expected.
3. For each meeting, what is normally written down or emailed afterward? Capture the decisions that information supports, metrics/units, concerns, owners and follow-up questions.
4. What approved source supplies each item: transcript, meeting chat, operational email, living file, staffing grid or charge handoff?
5. Where should the authoritative workbook live, and who can view or update it?
6. What closing time follows the final meeting's transcript-processing window?
7. Who reviews extraction and resolves conflicting evidence?
8. Which optional automations are wanted: transcript delivery, workbook refresh, confirmation, morning brief or spoken delivery? Confirm recipients, channels and local times separately.

## Customize before generation

Edit a private copy of `config/readiness.example.json`. Add a field with a unique stable key, label, definition, type (`number`, `text`, `boolean`), unit and optional numeric bounds. Mark `executive: false` to keep a detailed field out of the compact executive metric list while retaining it in daily and meeting records. Add the field key to relevant meetings. Use department-specific keys when measures are not equivalent; never sum census observations across time.

Add or rename meetings using a stable key, local end time, weekday list (Monday=0), focus and fields. `scheduleOverrides` maps an explicit date to the meeting keys expected that day. For a holiday with no meetings use an empty list. A cancelled occurrence can instead receive a reviewed not_held record. The supplied five meetings are examples, not requirements.

To generate prompts from an edited profile without repeating the questions:

```powershell
python -m hospital_ops.configure --profile data/my-profile.json --out data/my-setup --from-profile
```

The destination must be empty. Inspect generated prompts and the field map before deployment. No access is granted, files retrieved, workbook created or email sent by this command.

## Discovery is an optional tenant action

After explicit access and scope confirmation, an organization may configure an agent action to suggest recurring meeting series and operational source locations. Confirm suggestions with the leader. Do not infer leadership status from email frequency. Do not scan unrelated private messages. Without a permitted connector, ask for a manually maintained meeting/source register.

## Shared-file route

A meeting organizer can provide an authorized VTT export or share an approved artifact. A video/audio file is not directly accepted by the VTT parser; an approved transcription step is required first. Store original evidence privately and pass source references into reviewed records. Do not assume ownership alone bypasses tenant transcript controls.

## Optional department layer

Use local staffing models and rounding questions suited to the department. The OR grid is a worked example, not a mandatory room-based model for every unit. A later federation can publish standardized aggregate updates to authorized leaders. Shared field definitions, access boundaries and evidence timestamps must be established before agent-to-agent sharing. This extension is documented, not implemented as a multi-user service.
