"""
IJCAI 2026 demo — canned batch-generation content (prompts x models x cases).

Sibling of ``app/db/seeders/demo_video_data.py``: the same idea (deterministic,
re-seedable showcase outputs with realistic token/cost/latency metadata), but
for the two conference demo jobs created by ``scripts/seed_ijcai_demo.py``:

===========================  =========================  ======================
Job                          Prompt                     Models
===========================  =========================  ======================
Counselling Case Analysis    Structured Situation       Mistral Small 24B
                             Analysis                   Mistral Medium 128B
Empathic Reply Drafting      Empathic Reply Draft       Mistral Small 24B
                                                        Mistral Medium 128B
===========================  =========================  ======================

Both jobs run over the SAME 10 English counselling cases as the demo video
(``demo_video_data.COUNSELLING_CASES``) so a visitor can compare the two
prompts, the two models and the ten cases in one place.

Why canned outputs?
    Seeding must be deterministic, idempotent and independent of any live LLM
    key (it re-runs after every deploy). Visitors generate live output
    themselves — both Mistral models are public for the ``ijcai_reviewer`` role.

Provenance of the texts
    * Analysis / 24B — the **Situation** section is the genuine Mistral Small
      3.2 output from the 2026-02-15 production batch (imported from
      ``demo_video_data.SAMPLE_OUTPUTS['structured']['mistral']``, never
      copied). The four remaining sections are authored, in a deliberately
      plainer 24B voice, because the IJCAI prompt asks for five sections while
      the demo-video prompt asked only for the numbered situation list.
    * Analysis / 128B and all reply texts — authored for this demo. They are
      written to read like real model output for the given prompt and case:
      case-specific, correctly structured, with the 128B variant a little more
      nuanced, better sequenced and more precise than the 24B one. That
      contrast is the point of the side-by-side comparison at the booth.

Metadata
    ``input_tokens`` reflect the actual rendered prompt + case length (the
    analysis job reuses the measured input sizes of the production run, whose
    prompt is comparable in length); ``output_tokens`` follow the authored text
    length; ``cost_usd`` is computed from the seeded per-million prices of the
    two models (see ``db/models/llm_model.py``); latencies sit in the observed
    bands (24B ~2-6 s, 128B ~5-12 s).
"""

# --- keys -------------------------------------------------------------------
# Prompt keys (job) and model keys — used to index SAMPLE_OUTPUTS/OUTPUT_METADATA
# exactly like demo_video_data does.
PROMPT_ANALYSIS = 'analysis'
PROMPT_REPLY = 'reply'
MODEL_24B = 'mistral_24b'
MODEL_128B = 'mistral_128b'

# USD per 1M tokens (input, output) — mirrors the seeded LLMModel pricing for
# 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506' (0.10/0.30) and
# 'Global/Mistral/Mistral-Medium-3.5-128B' (0.40/2.00).
_PRICE_PER_MILLION = {
    MODEL_24B: (0.10, 0.30),
    MODEL_128B: (0.40, 2.00),
}


# ===========================================================================
# JOB 1 — "Structured Situation Analysis"
# ===========================================================================

# Sections 2-5 for the 24B analysis outputs. Index = case index. They are
# appended to the genuine Mistral-24B situation list (see module docstring);
# tone is intentionally a bit more generic than the 128B variant.
ANALYSIS_24B_SECTIONS = [
# 0 — custody concerns after separation
"""
**Emotional State**
The client describes feeling overwhelmed and reports disturbed sleep. Both children show stress reactions: the daughter withdrew after the argument, the son asks about his father every morning.

**Needs**
- A calmer and more predictable living situation for the children
- A contact arrangement that fits changing shift work
- Affordable information on custody and maintenance
- Relief for the client's own sleep and stress load

**Risk Assessment**
Moderate. No indication of danger to the children, but repeated conflict in front of them and the client's exhaustion increase the strain. The unannounced visit shows that contact rules are currently unclear.

**Suggested Approach**
1. Agree written contact rules with the ex-partner, including advance notice for visits.
2. Refer the client to a free family counselling or mediation service for the custody question.
3. Treat the son's bed-wetting and the daughter's anger as reactions to the separation and keep both under observation.
""",
# 1 — school refusal and possible bullying
"""
**Emotional State**
The son shows shame and hopelessness, expressed in the statement that everyone hates him. The father reports guilt about not noticing the situation earlier and is under pressure at work.

**Needs**
- Clarification of what happens in the class and how the school responds
- A gradual, low-pressure plan for returning to school
- A contact person for the son outside the family
- Relief for the father regarding leave days and unexcused absences

**Risk Assessment**
Elevated. Three weeks of absence, two months of social isolation and statements of being hated by everyone are significant. There is no indication of self-harm in the thread, but this has not been asked about.

**Suggested Approach**
1. Arrange a meeting with the school counsellor and the form teacher to document the incidents and agree on protective measures.
2. Plan a step-by-step return with single lessons and a trusted contact person instead of a full school day.
3. Offer the son an individual counselling contact and check his mood explicitly.
""",
# 2 — conflicts with teenage daughter about boundaries
"""
**Emotional State**
The daughter reacts with anger and withdrawal but was able to name the loss of her best friend. The parents feel helpless and disagree about consequences.

**Needs**
- Clear, negotiated rules on curfew and alcohol
- Recognition of the daughter's loss and of her wish for autonomy
- A united parental position
- Support for the drop in school performance

**Risk Assessment**
Moderate. Alcohol use at 16, falling grades and the end of a sporting activity are warning signs. The daughter is still communicating and there is no indication of an unsafe environment.

**Suggested Approach**
1. Set two or three non-negotiable safety rules and negotiate the remaining rules with the daughter.
2. Address the loss of her friend explicitly and support new contacts.
3. Agree a school plan with a realistic goal for this term.
""",
# 3 — exhaustion and burnout as a single parent
"""
**Emotional State**
The client describes exhaustion, guilt after shouting at her youngest son, and a feeling of losing control over the situation. The waiting list offers no short-term relief.

**Needs**
- Short-term relief in everyday care
- Support for the 8-year-old's behaviour at school
- Clarity with the employer about the current situation
- Reduction of the caregiving load carried by the oldest daughter

**Risk Assessment**
Elevated. Long-term overload, physical symptoms and an angry outburst towards a small child indicate a high level of strain. There is no indication of harm to the children, and the client seeks help herself.

**Suggested Approach**
1. Prioritise one problem first: the school situation of the 8-year-old.
2. Look for bridging support (school social work, family helper, emergency childcare) for the waiting period.
3. Address the client's own health with her doctor, separately from the children's issues.
""",
# 4 — blended family adjustment difficulties
"""
**Emotional State**
The client feels caught between her son and her partner and fears losing both. The children react with territorial behaviour and loyalty conflicts; the partner is hurt and doubts the arrangement.

**Needs**
- A common parenting line between the client and her partner
- Personal space and a sense of belonging for the 11-year-old son
- Factual, de-escalating communication with the ex-wife
- Relief from the pressure created by the legal threat

**Risk Assessment**
Moderate. The family conflict is escalating, but there is no indication of danger to the children. The lawyer's letter increases the pressure and can harden positions further.

**Suggested Approach**
1. Agree with the partner who takes the lead with which child in matters of correction.
2. Give the son a space of his own that is not shared during the daughter's weeks.
3. Answer the lawyer's letter factually and consider joint family counselling.
""",
# 5 — dealing with depression as a parent
"""
**Emotional State**
The client describes guilt towards his son and fear of not being able to meet his wife's expectations. The conversation with his son was relieving; the new medication side effects reduce his confidence.

**Needs**
- A realistic, small morning commitment instead of a fixed twice-a-week rule
- Independent support for the wife, who reports resentment and exhaustion
- Feedback to the prescribing doctor about the side effects
- A low-threshold way back into a meaningful activity

**Risk Assessment**
Moderate. The depression is diagnosed and treated, the client is in therapy and communicates openly. No indication of self-harm in the thread; the wife's exhaustion is an additional load on the family.

**Suggested Approach**
1. Renegotiate the morning agreement into a smaller, achievable step.
2. Encourage the wife to seek support of her own.
3. Report the medication side effects to the prescribing doctor promptly.
""",
# 6 — excessive screen time and declining grades
"""
**Emotional State**
The son reacts with anger and loss of control when limits are set. The client feels helpless and is now supported by her husband, who previously played the situation down.

**Needs**
- A joint parental position and a plan that can be maintained
- A professional assessment of the gaming behaviour
- Relief for the school situation (sleep, homework)
- Alternatives that preserve social contact

**Risk Assessment**
Elevated. Escalating use, withdrawal from friends and sport, falling grades, sleeping in class and two episodes of property damage indicate more than an age-typical hobby.

**Suggested Approach**
1. Arrange an assessment at a counselling service for media use or child and adolescent counselling.
2. Replace switching off the router with announced end times and a warning before the end.
3. Re-establish one offline contact from his former football environment.
""",
# 7 — cultural integration and identity struggles
"""
**Emotional State**
The client describes a feeling of failing all three children. The children show identity conflict, shame about accent and language, and experiences of exclusion.

**Needs**
- Relief for the oldest daughter from her role as interpreter
- Educational support for the 12-year-old son
- Recognition of Arabic as a resource rather than an obstacle
- Social connection for the family in the community

**Risk Assessment**
Moderate. There is no acute danger, but three children are affected by exclusion at the same time, and the parents' own resources are limited by language and isolation.

**Suggested Approach**
1. Organise professional interpreters for medical and school appointments.
2. Ask the school about language support and discuss the change of school type as a pathway, not a failure.
3. Connect the family with an integration or neighbourhood service offering family activities.
""",
# 8 — teenager wanting to move out for apprenticeship
"""
**Emotional State**
The client remains anxious but has become more open since the visit. She fears her son's resentment if the parents refuse. The son showed responsibility during the trip.

**Needs**
- Practical preparation for independent living (cooking, medication, budgeting)
- A shared parental position with the husband
- Contact agreements that provide safety without becoming control
- Space for the client's own separation process

**Risk Assessment**
Low. There is no indication of endangerment. The asthma medication should be organised reliably; the family is in dialogue and has already reached agreements.

**Suggested Approach**
1. Practise concrete everyday skills before August (shopping, cooking, medication routine).
2. Put the existing agreements in writing (daily call for the first month, home every second weekend).
3. Address the client's own farewell as a topic in its own right.
""",
# 9 — sibling rivalry and unequal treatment
"""
**Emotional State**
The son felt seen after the shared time; the daughter reacted with jealousy and a sense of unfairness. The client feels she cannot do it right for either child.

**Needs**
- Visible recognition of the son's strengths
- Reliable one-to-one time for both children
- Clarity about the pending dyslexia assessment and the support that follows
- Relief of the client's guilt rooted in her own family history

**Risk Assessment**
Low. Age-typical sibling rivalry with normal conflict dynamics. No indication of endangerment; the client is reflective and has already started to act.

**Suggested Approach**
1. Display the son's constructions in the same way as the daughter's certificates.
2. Fix a short one-to-one time for each child on set days.
3. Follow up the dyslexia assessment and explain the result to both children in age-appropriate terms.
""",
]


# Full 128B analysis outputs. Index = case index.
ANALYSIS_128B = [
# 0 — custody concerns after separation
"""
**Situation**
1. Separation three weeks ago after five years; the client and both children (7 and 4) live in the grandmother's cramped apartment. — "I moved out and I am currently staying with the children at my mother's apartment. It is very cramped"
2. Contact with the father is unregulated and contested: the daughter refuses weekend visits, and the ex-partner appeared unannounced, which led to an argument in front of the children. — "My ex showed up unannounced at my mother's place on Wednesday and there was an argument in front of the children"
3. Part-time shift work as a nurse makes fixed visitation times difficult; legal advice is currently unaffordable. — "my shifts change weekly, so a fixed visitation schedule is difficult", "My mother says I should get a lawyer immediately, but I cannot afford one right now"

**Emotional State**
The client reports feeling overwhelmed and sleeping poorly, with the pressure rising sharply after Wednesday. The daughter's hour behind a locked bathroom door points to acute overload rather than defiance; the son's daily question about his father is an attempt to make an unpredictable week predictable.

**Needs**
- Predictability first: a written, low-conflict contact arrangement including notice before visits
- Free or low-cost legal information on custody and maintenance
- Age-appropriate explanations for both children about what happens next
- Relief and sleep for the client before further decisions are taken

**Risk Assessment**
Moderate. No report of violence or of danger to the children's welfare, and the family is housed. Aggravating factors are the escalating parental conflict in the children's presence, the daughter's withdrawal and the client's exhaustion; the grandmother's support and the client's own reflection are protective.

**Suggested Approach**
1. Stabilise contact: propose fixed, announced handovers in writing, with a two-week trial period.
2. Signpost free family mediation and a legal advice voucher so the lawyer question is decoupled from the cost question.
3. Keep the daughter's refusal separate from the custody dispute and offer a short, low-pressure form of contact instead of full weekends.
4. Review the client's own sleep and workload at the next contact.
""",
# 1 — school refusal and possible bullying
"""
**Situation**
1. The 14-year-old son has refused school for three weeks with headaches and stomach aches; the paediatrician found no physical cause. — "he complains of headaches and stomach aches, but our paediatrician found nothing physically wrong"
2. Peer exclusion is now confirmed by both the school and the son: comments about his clothes and his old phone, two months of eating alone. — "a group of boys in his class has been making comments about his clothes and his phone being old", "he has been eating lunch alone for two months"
3. The single father has used up all his leave; 15 unexcused absences are on record and he fears involvement of the youth welfare office. — "I am a single father and I have already used all my remaining leave days from work"

**Emotional State**
The son moved from silence to tears and to a global statement — everyone hates him — which indicates shame and hopelessness rather than simple school avoidance. The father is relieved to finally have an explanation but describes guilt for not seeing it sooner, alongside real job insecurity.

**Needs**
- A protective response from the school that addresses the group and does not expose the son
- A graded return plan instead of a full school day
- A confidential contact person for the son outside the family system
- Clarity for the father about absences, leave and the supportive role of the youth welfare office

**Risk Assessment**
Elevated. The duration of the absence, two months of isolation and the generalised statement of being hated are the concerning markers; psychosomatic symptoms without an organic cause fit a sustained stress reaction. The thread contains no indication of self-harm, but this has not been asked about directly and should be.

**Suggested Approach**
1. Ask the father, at the next contact, how his son's mood is, including whether he has expressed thoughts of hurting himself.
2. Convene a meeting with form teacher and school counsellor and agree measures at class level, so the son is not identified as the complainant.
3. Negotiate a graded return: two lessons per day, a named contact person, an agreed signal for leaving the room.
4. Explain the supportive function of the youth welfare office to reduce the father's fear of reporting.
""",
# 2 — conflicts with teenage daughter about boundaries
"""
**Situation**
1. The 16-year-old daughter returns after midnight most weekends and came home at 2 AM smelling of alcohol; the confrontation ended in shouting and a damaged door frame. — "Last Saturday she came home at 2 AM smelling of alcohol", "She slammed her door so hard that the frame cracked"
2. Marked change within one term: grades from mostly Bs to Ds, volleyball team quit without telling the parents, communication largely stopped. — "Her grades have dropped from mostly Bs to Ds this term", "She also quit the volleyball team last month without telling us"
3. A trigger is now identified: her best friend since primary school moved away in October, and she has joined a new group with different norms. — "her best friend since primary school moved away in October", "they think curfews are embarrassing"

**Emotional State**
Behind the daughter's anger there is an unprocessed loss and a strong fear of being the outsider in her new group. The client oscillates between worry and self-doubt; the parents differ on consequences, and the daughter can read that difference.

**Needs**
- A small set of non-negotiable safety rules, clearly separated from negotiable ones
- Acknowledgement of the friendship loss as a real event rather than a side note
- One consistent parental line agreed between the client and her husband
- A realistic plan for the school term before the grades consolidate

**Risk Assessment**
Moderate. Alcohol at 16, the abrupt drop in performance and the loss of a protective activity are the risk markers; there is no indication of regular heavy use or of an unsafe environment. Crucially, the daughter still talks when she is not confronted — that channel should be protected.

**Suggested Approach**
1. Agree the parental position first and hold one calm conversation afterwards, not the other way round.
2. Set two safety rules (a call when plans change, no travelling home alone at night) and negotiate the curfew itself with her.
3. Name the friend's departure and ask what would help; consider one shared activity unrelated to school.
4. Avoid removing the phone as an opening move — it removes the safety channel along with the sanction.
""",
# 3 — exhaustion and burnout as a single parent
"""
**Situation**
1. Single mother of three (10, 8 and 3) in full-time employment; the father lives in another city and pays maintenance irregularly. — "My ex-husband moved to another city two years ago and pays child support irregularly"
2. Chronic overload with physical symptoms and one loss-of-control episode that she reported herself. — "I have had recurring headaches for months and my doctor says it is tension-related", "Last week I shouted at my 3-year-old for spilling juice"
3. The situation is now destabilising outward: the 8-year-old is acting out at school, the client had to leave work twice, and formal support has a six-week waiting list. — "his teacher says he is pushing other children", "They have a six-week waiting list"

**Emotional State**
The client shows the typical picture of parental burnout: exhaustion, irritability and guilt directed at herself rather than at the circumstances. That she noticed and described the episode with her youngest is a resource, not a warning sign. The oldest daughter's caregiving role shows that the strain is already being redistributed inside the family.

**Needs**
- Immediate, low-threshold relief that does not depend on the waiting list
- One prioritised problem instead of four simultaneous ones — currently the school situation
- A factual conversation with the employer before reliability becomes an issue
- Age-appropriate offloading of the 10-year-old

**Risk Assessment**
Elevated, without acute endangerment. Risk factors: duration of the overload, somatic symptoms, one episode of shouting at a 3-year-old, no local network, no financial buffer. Protective factors: the client seeks help, reflects on her own behaviour, and all three children are in institutional care during the day.

**Suggested Approach**
1. Bridge the waiting list: school social work, a volunteer family helper, or emergency childcare through the kindergarten.
2. Take the 8-year-old's school situation first; it is the stressor that currently threatens her employment.
3. Agree one concrete relief for the daughter — one fixed task returned to the client — and name it to her explicitly.
4. Encourage a separate appointment with the client's own doctor for her symptoms.
""",
# 4 — blended family adjustment difficulties
"""
**Situation**
1. Blended household of six months: the client's 11-year-old son lives there full-time, the partner's 9-year-old daughter every other week, and the children do not get on. — "My son says he hates sharing his room when she is here and calls her a guest who should go home"
2. Escalation at dinner: the partner corrected the son, who answered that the partner is not his father and left the table; the partner then questioned the whole arrangement. — "My partner was hurt and said maybe the children are just not ready for this"
3. The conflict has crossed household boundaries and become legal: the daughter called her mother crying, and the ex-wife's lawyer has sent a formal letter. — "now the ex-wife has sent a formal letter through her lawyer"

**Emotional State**
The client is in a double loyalty bind and describes an anticipated loss of both her partner and her son. Her son's reaction concerns status and territory rather than rejection of the partner as a person; the partner's doubt reads as a wounded reaction to an unexpected boundary rather than a considered position.

**Needs**
- An explicit division of roles: in this phase, each parent leads with their own child
- Protected personal space for the son during the weeks the daughter is present
- A factual, de-escalating channel to the ex-wife that does not run through the children
- A shared, realistic expectation of how long the adjustment takes

**Risk Assessment**
Moderate. No indication of danger to either child; the conflict is on the relationship level and is currently escalating in two directions at once, within the couple and towards the ex-partner. The main risk is that the legal step hardens positions and the son's wish to move to his father becomes a real exit.

**Suggested Approach**
1. Separate the roles now: the partner steps out of the disciplinarian role towards the son for the time being.
2. Take the son's request seriously and ask what would have to change for him to want to stay.
3. Answer the lawyer's letter briefly and factually, ideally after legal advice, and keep both children out of that correspondence.
4. Propose family counselling, starting with the couple and involving the children later.
""",
# 5 — dealing with depression as a parent
"""
**Situation**
1. Moderate depression diagnosed six months ago, medicated and in therapy; mornings and weekends are the hardest parts of the day. — "Most mornings I cannot get out of bed before my wife has already taken our son to school"
2. The 10-year-old son has begun to make sense of the situation and, after an age-appropriate conversation, offered help. — "He asked if I was going to get better and I told him honestly that I am working on it. He hugged me and said he would help"
3. The wife has named her limit and made a concrete request; the medication was adjusted last week and the side effects make mornings harder. — "She said she needs me to at least handle the morning routine twice a week", "the side effects make mornings even harder"

**Emotional State**
The client's guilt is directed at the effect of his illness on his son and wife rather than at himself as a person, which is a workable starting point. He is caught between the wish to meet his wife's request and a realistic doubt about his reliability. The wife's admission of resentment is a sign of strain, not of withdrawal.

**Needs**
- An agreement small enough to be kept, so that a missed morning does not become further evidence of failure
- Independent support for the wife (partner group or her own counselling)
- Prompt feedback to the prescribing doctor about the new side effects
- A low-threshold return to a meaningful activity, in a smaller form than coaching a team

**Risk Assessment**
Moderate and currently stable. Protective factors: treatment in place, open communication with wife and son, and the client actively seeking contact. There are no reports of self-harm or hopelessness in this thread; the recent medication change is the point to keep under observation over the coming weeks.

**Suggested Approach**
1. Renegotiate the morning agreement downwards: one fixed morning per week, defined concretely, reviewed in three weeks.
2. Recommend that the wife's exhaustion be addressed in its own right, not as part of his treatment.
3. Ask him to report the side effects to the prescribing doctor this week.
4. Keep the son's question open with short, honest updates rather than one large conversation.
""",
# 6 — excessive screen time and declining grades
"""
**Situation**
1. The 12-year-old son plays five to six hours on weekdays and up to nine at weekends; his grades fell from the top third to near-failing in mathematics and English. — "sometimes eight or nine hours", "nearly failing mathematics and English"
2. Withdrawal from previous sources of support: football given up, few in-person contacts, sleeping in class, no homework submitted for three weeks. — "He has also stopped playing football, which he used to love", "he has been falling asleep in class"
3. Limits trigger loss of control: a thrown controller, twenty minutes of screaming after the router was switched off, a hole punched in the bedroom door. The agreed one-hour rule held for two days. — "he screamed for twenty minutes and punched a hole in his bedroom door"

**Emotional State**
The son's reaction to limits is disproportionate and directed at objects rather than people, which points to loss of control rather than calculated defiance. The game is currently his main social space, so being disconnected is experienced as exclusion. The client has moved from worry to alarm and now has her husband's backing, which she previously lacked.

**Needs**
- A professional assessment of the gaming behaviour rather than another household rule
- A predictable, announced structure instead of abrupt disconnection
- Recovery of sleep and a minimum of school functioning
- At least one offline social contact that is not experienced as punishment

**Risk Assessment**
Elevated. Duration and escalation of use, withdrawal from all previous activities, academic collapse, disturbed sleep and two incidents of property damage together exceed age-typical gaming. There is no indication of aggression towards people. Protective factors: both parents now agree, and the son was willing to negotiate a plan.

**Suggested Approach**
1. Arrange an appointment at a specialist media-use or child and adolescent counselling service, framed as assessment rather than punishment.
2. Replace switching off the router with an announced end time and a ten-minute warning he can act on.
3. Tie one concrete privilege to sleep and homework instead of to gaming hours themselves.
4. Contact the school for a temporary support plan so the academic gap does not add pressure.
""",
# 7 — cultural integration and identity struggles
"""
**Situation**
1. Family of five, four years in Germany; the husband works in a warehouse, the client attends a B1 language course, and the 15-year-old daughter interprets at medical and school appointments. — "My oldest daughter speaks fluent German and translates for us at doctor appointments and parent-teacher meetings"
2. All three children are affected at once: the daughter was told she would never really be German, the 12-year-old refused school because of his accent and is to move to Realschule, the 6-year-old no longer wants to speak Arabic. — "A classmate told her she would never really be German no matter how well she speaks"
3. The parents disagree about language strategy and describe social isolation. — "My husband thinks the children should focus on German only, but I want them to keep Arabic", "we have friendly neighbours but no close friends in the community"

**Emotional State**
The client's statement that she is failing all three children indicates guilt that has become global rather than tied to specific decisions. The daughter is in an acute conflict of belonging — no longer Syrian, not accepted as German — which is the most pressing of the three situations. The youngest child's rejection of Arabic is a peer-driven reaction, not a settled position.

**Needs**
- Relief of the daughter's interpreting role through professional interpreters
- School-level support for the son, so the change of school type is not experienced as failure
- A family language agreement both parents can carry
- Contacts outside the family: peers for the daughter, community for the parents

**Risk Assessment**
Moderate. No acute endangerment; the aggravating factor is simultaneity — three children with experiences of exclusion and parents whose own resources are limited by language and isolation. The daughter's identity conflict should be followed up, as this constellation can lead to sustained withdrawal.

**Suggested Approach**
1. Arrange professional interpreting for medical and school appointments and tell the daughter explicitly that this task is no longer hers.
2. Ask the school about language support and reframe the Realschule discussion as a pathway, including the option of transferring back later.
3. Support one shared family rule on language use rather than settling the parents' disagreement in principle.
4. Signpost an integration or neighbourhood service with family activities and follow up on the daughter separately.
""",
# 8 — teenager wanting to move out for apprenticeship
"""
**Situation**
1. The 17-year-old son has an apprenticeship as an electrician 200 kilometres away starting in August and wants to move into a shared flat with another apprentice. — "He wants to accept it and move into a shared flat with another apprentice"
2. The concerns are practical rather than principled: no experience of living alone, no cooking, daily asthma medication. The conflict has created distance between parents and son. — "He also has mild asthma that requires daily medication", "He has been cold and distant for a week now"
3. The joint visit changed the picture: flat and flatmate were reassuring, the son had already located the nearest doctor, the husband now supports the move, and agreements exist. — "He has agreed to a daily video call for the first month and to come home every second weekend"

**Emotional State**
The client's fear has not disappeared but is no longer the only voice; she now weighs it against the risk of lasting resentment. Her isolation within the parental couple has eased since the visit. The son's behaviour during the trip — planning, showing them the company, locating a doctor — reads as a bid for trust rather than as defiance.

**Needs**
- Concrete practice of everyday skills in the months before August
- A reliable, low-effort routine for the asthma medication
- Contact agreements that provide safety without becoming surveillance
- Recognition that the client faces her own separation, not only a logistical problem

**Risk Assessment**
Low. No indication of endangerment; the identifiable risk is medication adherence, which is manageable with preparation. The relationship risk of a refusal is currently higher than the practical risk of the move.

**Suggested Approach**
1. Turn the remaining months into a practice phase: shopping, cooking twice a week, laundry, a simple monthly budget.
2. Set up a medication routine the son owns himself (phone reminder, weekly dispenser) and register him with a local practice before the move.
3. Put the agreements in writing with a review date after four weeks, so they can be relaxed rather than renegotiated in conflict.
4. Give the client's own farewell explicit room at the next contact; it is currently being handled as a safety question.
""",
# 9 — sibling rivalry and unequal treatment
"""
**Situation**
1. Two children with different profiles: the 11-year-old daughter is academically gifted and receives regular recognition, while the 8-year-old son struggles with reading and writing and has a pending dyslexia assessment. — "He was recently tested and shows signs of dyslexia, though the formal assessment is still pending"
2. The son voices the imbalance and has acted on it; the daughter counters with a claim of her own. — "my son has started saying things like you love her more", "Last week he destroyed a drawing his sister made for a school project"
3. The client has already changed something: after recognising her son's strengths she spent 30 minutes building with him, which the daughter registered immediately. — "he was so happy he told his friend about it", "she asked why I was spending so much time with him"

**Emotional State**
The son's perception is accurate rather than distorted: recognition in this family has been tied to school achievement, which is not his channel. The daughter's reaction is not simple jealousy — she has just experienced that attention is finite and reads the change as a loss. The client's own history of being compared to her sister raises the stakes and makes her read every reaction as failure.

**Needs**
- Visible recognition of the son's strengths in the same currency as his sister's certificates
- Predictable one-to-one time for both children, so attention stops being a scarce good
- Clarity about the dyslexia assessment and the support that follows from it
- Separation of the client's own biography from her children's dynamic

**Risk Assessment**
Low. Age-typical sibling rivalry with an identifiable cause; the destroyed drawing is an isolated incident rather than a pattern of aggression. No indication of endangerment. The client's reflective stance and the fact that she has already acted are strong protective factors.

**Suggested Approach**
1. Make the son's work visible: display the marble run where the certificates hang, and tell him why.
2. Give both children a fixed, short one-to-one slot on named days instead of spontaneous compensation.
3. Follow up the assessment and explain the result to both children in age-appropriate words, so the extra support is read as need rather than preference.
4. Address the client's own experience of being compared as a separate topic, not as evidence that she is repeating it.
""",
]


# ===========================================================================
# JOB 2 — "Empathic Reply Draft"
# ===========================================================================

# Reply drafts, index = case index. Each answers the client's LATEST message,
# validates, refers to concrete details, offers one or two next steps and ends
# with a single open question — exactly what the prompt asks for.
REPLY_24B = [
# 0 — custody concerns after separation
"""
Thank you for writing again — it sounds like this has been a very hard week. An unannounced visit and an argument in front of the children is exactly the situation you were trying to avoid, and it makes sense that you are lying awake afterwards.

Your daughter locking herself in the bathroom is her way of getting out of a situation that felt too big for her. Your son's question every morning is the same need in a different form: he is trying to make an unpredictable week predictable.

Two things may help in the coming days. First, agree one simple rule with your ex-partner in writing: visits are announced in advance, at an agreed time. A short message is enough — what matters is that it exists and that you can point to it. Second, you do not need to pay for a lawyer in order to get information. Family counselling centres offer free advice on custody questions, and many regions have legal advice vouchers for people on a low income.

You are carrying a great deal at once, and the fact that you are still thinking about what your children need says a lot about you.

What would need to change in the next two weeks for your evenings to feel a little calmer?
""",
# 1 — school refusal and possible bullying
"""
Thank you for writing back. What you found out this week is painful, but it is also the piece that was missing: your son now has a reason he could name, and that changes what can be done.

Please try not to hold on to the thought that you should have noticed earlier. At fourteen, young people work hard to hide exactly this, and shame is a very effective cover. That he cried and told you at all means he still trusts you.

Two steps usually help here. First, ask the school for a meeting with the form teacher and the school counsellor, and ask specifically what they will do at class level — stopping this is the school's responsibility, not your son's. Second, do not aim for a full school day. A graded return, starting with one or two lessons and a named person he can go to, is far more likely to hold.

One more thing, which I ask every parent in this situation: when he said everyone hates him, did he say anything about not wanting to be here any more, or about hurting himself? Please ask him directly and calmly.

How does he seem in the evenings, when school is not the subject?
""",
# 2 — conflicts with teenage daughter about boundaries
"""
Thank you for trying that conversation and for telling me how it went. You got more out of it than it may feel like: your daughter told you that her best friend moved away, that she is with a new group, and that she does not feel trusted. That is a lot of information from a sixteen-year-old who barely speaks to you at the moment.

The loss of that friendship is probably the key. She lost her closest contact in October and is now trying to secure a place in a group whose rules are not yours. Being the one who has to leave early is, for her, a real social risk.

Two suggestions. First, sort your rules into two groups: two or three that are non-negotiable because they concern safety, and the rest, including the curfew itself, which you negotiate with her. Rules she helped set are the ones she is most likely to keep. Second, agree the line with your husband before the next conversation rather than during it.

I would be careful about taking the phone away — it is also how you reach her when something goes wrong.

What do you think she would say if you asked her what she misses most about her friend?
""",
# 3 — exhaustion and burnout as a single parent
"""
Thank you for writing again — a six-week waiting list is exactly what you did not need this week. When several things go wrong at once it is normal not to see where to start, so let me suggest an order.

Begin with the school situation of your eight-year-old. It is the problem that is currently costing you working hours, and it is also where help arrives fastest: ask whether the school has a school social worker and whether they can meet you in the next few days. That route usually has no waiting list.

Second, do not simply wait out the six weeks. Ask the family support centre about bridging help — a volunteer family helper, emergency childcare through the kindergarten, or a family centre in your district. Asking for a bridge often produces a different answer than asking for a place.

I would also gently say that the headaches your doctor described as tension-related deserve an appointment of their own, not one squeezed in between the children's.

And about the evening you shouted at your youngest: that it still troubles you is not a sign that you are failing him.

If one thing could be taken off your list next week, which one would help most?
""",
# 4 — blended family adjustment difficulties
"""
Thank you for telling me how Saturday went. An escalation like that, followed by a lawyer's letter, is a great deal to hold in one weekend, and I understand the fear of losing your partner and your son at the same time.

What your son said is not a verdict on your relationship. At eleven, "you are not my dad" is usually about status and territory: who is allowed to correct him in a home he did not choose. And your partner's reaction — that maybe the children are not ready — sounds like a hurt moment rather than a considered position.

Two things often help at this stage. First, agree with your partner that for the coming weeks each of you takes the lead with your own child in matters of correction and consequences. That removes exactly the trigger from Saturday's dinner. Second, answer the lawyer's letter briefly and factually, ideally after getting advice, and keep both children out of that correspondence.

Your son's question about living with his father is worth taking seriously, though not as a decision — as information about what he is missing.

What do you think would have to change at home for him to want to stay?
""",
# 5 — dealing with depression as a parent
"""
Thank you for this update — there is more good news in it than you may see yourself. You had the conversation with your son, you answered him honestly, and he responded with a hug and an offer to help. That is what a ten-year-old needs: not a well parent, but an honest one.

The agreement with your wife is the harder part, and I would make it smaller. Twice a week, in a week when your medication has just been adjusted, is a promise you may not be able to keep — and a broken promise would cost you more than a smaller one. Consider proposing one fixed morning on a set day, and reviewing it in three weeks.

Two more things. Please tell your prescribing doctor about the side effects soon; a pattern that lands specifically on mornings can often be adjusted. And your wife's exhaustion deserves support of its own — partners often carry this for a long time before saying anything.

You are doing more than you give yourself credit for.

Which morning of the week would currently be the most realistic one for you?
""",
# 6 — excessive screen time and declining grades
"""
Thank you for the update, and I am glad your husband now sees this with you. What you describe has moved beyond a discussion about screen time. Sleeping in class, three weeks without homework, no contact with classmates at break, and a hole in the door after the router went off: that is a pattern, not a phase.

I would stop looking for the right household rule and ask for an assessment instead. Many regions have counselling services for media use, and child and adolescent counselling services cover this too. It helps to present it to your son as a conversation about how things are going overall rather than as a consequence — the appointment will land better that way.

In the meantime, two practical things. Replace switching off the router with an announced end time and a warning ten minutes before, so he can leave the game rather than being cut out of it mid-round. And tie one privilege to sleep and homework rather than to gaming hours themselves.

That he agreed to a plan at all shows there is something to work with.

What does he say about school when homework is not the subject?
""",
# 7 — cultural integration and identity struggles
"""
Thank you for writing. Three difficult conversations in one week, with three children, and each of them about belonging — it is understandable that you feel you are failing all of them. From the outside it looks different: all three came to you with it, and that is not a sign of failure.

Your daughter's experience is the one I would follow up first. Being told she will never really be German, while no longer feeling Syrian either, is a genuine conflict and not a passing remark. It would help her to have someone outside the family to talk to, and contact with other young people who know both worlds.

Two practical steps. Ask the school and the doctor's practice for professional interpreters — in most settings you are entitled to this, and it takes a role off your daughter that is not hers to carry. And speak to your son's school about language support; a move to Realschule is a different path, not a verdict, and students do transfer back later.

Arabic is not the obstacle here. Children who keep both languages usually do better, not worse.

Which of your three children do you feel is most alone with this at the moment?
""",
# 8 — teenager wanting to move out for apprenticeship
"""
Thank you for this message — a lot has moved since you first wrote. You visited the city, you met the flatmate, and you saw a side of your son that had not been visible at home: he had already found the nearest doctor. Your husband has come round, and your son has offered daily calls and a visit every second weekend.

Your question about how to prepare him, and yourself, is exactly the right one.

For him, use the months until August as practice rather than instruction: shopping and cooking twice a week while you are still there to be asked, his own laundry, and a simple monthly budget. For the asthma medication, set up something he owns himself, such as a reminder on his phone and a weekly pill box, and register him with a practice in the new city before he moves rather than after.

For yourself, I would write the agreements down with a review date after four weeks, so they can be relaxed as a planned step instead of renegotiated in an argument.

Being afraid and letting him go are not opposites; you can do both.

What would you like to have said to him before he leaves?
""",
# 9 — sibling rivalry and unequal treatment
"""
Thank you for writing back — and I think you found something important. A marble run that took three days is exactly the kind of achievement that has never been on your wall. Certificates get framed; cardboard usually gets tidied away.

Your daughter's reaction is uncomfortable, but it is not a sign that the approach is wrong. She has just experienced attention as something that can move, and she is checking whether it comes back.

Two things would help. Put the marble run somewhere visible, in the same place where your daughter's certificates hang, and tell your son why it is there. And instead of spontaneous compensation, give each child a short fixed slot — twenty minutes on set days — so that attention stops being something they have to compete for.

I would also see the dyslexia assessment through. Once the result is there, explaining it to both children makes the extra support easier for your daughter to accept.

You are trying not to repeat what happened between you and your sister, and that intention is already doing work.

What does your daughter usually ask for when she wants your attention?
""",
]


REPLY_128B = [
# 0 — custody concerns after separation
"""
Thank you for coming back and telling me how the week went — that cannot have been an easy message to write. What happened on Wednesday was not a small incident: the argument took place in front of both children, and the very unpredictability you have been trying to manage arrived at your mother's door unannounced.

Your daughter's hour behind the locked bathroom door makes sense in that light. At seven, locking a door is often the only available way of saying "this is too much for me right now" — it is not defiance, and it does not mean she is turning against you. Your son asking every morning whether Daddy is coming is the same need in another form: he is trying to make an unpredictable week predictable.

Two concrete steps for the coming days. First, put one rule in writing with your ex-partner: contact is announced at least a day in advance, at an agreed time and place. Written does not mean legal — a message is enough, and it gives you something to point to. Second, before you take on the cost of a lawyer, ask your local family counselling centre about free custody advice and whether you qualify for a legal advice voucher. That separates the information you need from the money you do not currently have.

Your own sleep belongs in this too, not only as a symptom of everything else.

When you imagine the next handover going well, what does it look like?
""",
# 1 — school refusal and possible bullying
"""
Thank you for writing back so quickly. What you learned this week is hard to read, and it also changes the situation: three weeks of headaches and stomach aches now have a name, and a name is something that can be worked with.

I want to say something about your last sentence. You did not miss this because you were inattentive. Your son kept it from you — through two months of eating alone — because at fourteen being excluded feels shameful, and shame hides well. That he cried and told you means the channel between you is open, and that is the most important resource you have right now.

Two next steps. First, request a meeting with the form teacher and the school counsellor, and ask one precise question: what will the school do at class level so the comments stop, without your son being identified as the one who reported it? Measures of this kind work when they address the group, not the affected child. Second, do not plan a full return. Two lessons, one named adult he can go to, and an agreed way of leaving the room if it becomes too much — a small plan that holds beats a large one that fails.

One thing I ask every parent at this point, because it matters more than the school question: when he said everyone hates him, did he say anything about not wanting to be here, or about hurting himself? Please ask him directly, calmly, in a quiet moment.

What is he like at home in the evening, when school is not the topic?
""",
# 2 — conflicts with teenage daughter about boundaries
"""
Thank you for trying that conversation, and for telling me that it went poorly at first. It still worked: you now know that her best friend since primary school moved away in October, that she has joined a new group, and that she feels you do not trust her. From a sixteen-year-old who barely speaks to you at the moment, that is a great deal.

I think the October date matters more than the alcohol does. She lost her closest relationship and is now buying her way into a group whose norms are not yours — and being the only one who has to leave early is, in that context, a genuine social cost rather than a dramatisation.

Two things for the coming week. First, sort your rules into two piles. Keep two non-negotiables that are purely about safety — for example a message when the plan changes, and never travelling home alone late at night — and put everything else, including the exact curfew, on the table for negotiation with her. Rules she helped write are the ones that survive Saturday evening. Second, agree the line with your husband before you talk to her rather than in front of her; at the moment the disagreement between you is the most usable thing in the house.

I would hold off on taking the phone. It is also your only channel when something goes wrong at one in the morning.

If you asked her what she misses most since October, what do you think she would say?
""",
# 3 — exhaustion and burnout as a single parent
"""
Thank you for writing back, and I am sorry that the waiting list is six weeks — that is the answer you could least afford this week. When four problems arrive at once, asking which one to tackle first is not a weakness; it is the right question. Here is the order I would suggest.

Start with your eight-year-old's school situation. It is the problem that is currently pulling you out of work, and it is also where help is fastest: ask whether the school has a school social worker and request a short meeting this week. That route usually has no waiting list, and it takes pressure off your job at the same time.

Second, treat the six weeks as something to bridge rather than to wait out. Ask the family support centre explicitly about interim options — a volunteer family helper, emergency hours through the kindergarten, a family centre in your district. Asking for a bridge often produces a different answer than asking for a place.

I would also like to name two things that are getting lost in all of this. Your tension headaches deserve an appointment of their own rather than a corner of the children's. And your ten-year-old is carrying tasks that are not hers; one fixed task returned to you, and said out loud to her, does more than it sounds like.

About the evening you shouted at your youngest: that it still troubles you is not evidence that you are failing him. It is evidence of how far past empty you have been running.

If one single thing could be lifted off you next week, which would it be?
""",
# 4 — blended family adjustment difficulties
"""
Thank you for telling me what happened on Saturday. A dinner that ends with your son leaving the table, your partner questioning the whole arrangement, and a lawyer's letter arriving — that is a great deal for one weekend, and your sentence about losing your partner and your son at the same time makes complete sense to me.

I would read your son's words more narrowly than they sound. At eleven, "you are not my dad" is usually a statement about authority rather than about affection: who is entitled to correct him in a home he did not choose to move into. And your partner's reaction sounds like a wounded moment rather than a settled conclusion about the children.

Two steps for this week. First, agree a clear division with your partner: for the coming weeks each of you takes correction and consequences with your own child, and you back each other visibly in front of both children. That removes precisely the trigger from Saturday and gives the children a predictable structure while everything else is unsettled. Second, answer the lawyer's letter briefly and factually, ideally after legal advice, and keep both children entirely out of that correspondence — including what they overhear.

I would treat your son's question about moving to his father as information rather than as a decision. It tells you what he currently feels he has lost.

If you could ask him one thing this week without it turning into an argument, what would you want to know?
""",
# 5 — dealing with depression as a parent
"""
Thank you for this message. I want to point at something in it that you may be walking straight past: you had the conversation with your son, you answered his question honestly rather than reassuringly, and he responded by hugging you and offering to help. A ten-year-old does not need a well parent — he needs an honest one, and this weekend he got that.

The agreement with your wife is the part I would change. Twice a week, in the week after a medication adjustment, is a commitment you may not be able to hold, and a missed morning would become further evidence for the story you already tell about yourself. I would propose something deliberately small: one fixed morning, on a named day, reviewed in three weeks. If it works, you extend it from a position of success rather than of catching up.

Two further things. Please report the side effects to your prescribing doctor this week instead of waiting for the next appointment — a pattern that lands specifically on mornings is often something that can be adjusted. And your wife's resentment is worth hearing as a signal rather than as an accusation: partners often carry this for months before saying it out loud, and she has her own claim to support, separate from your treatment.

Stepping down from coaching was a loss as well, and it does not have to stay all or nothing.

Which morning of the week would be the most realistic one for you at the moment?
""",
# 6 — excessive screen time and declining grades
"""
Thank you for the update, and I am glad your husband now sees it the same way — you have needed that. What you describe has moved past a disagreement about screen time. Sleeping in class, three weeks with no homework submitted, no contact with classmates at break, and a hole in the door after the router went off: taken together, that is a pattern.

At this point I would stop searching for the right household rule and ask for an assessment. Specialist counselling services for media use exist in most regions, and child and adolescent counselling services cover this as well. It helps to present it to your son as a look at how things are going overall — school, sleep, friends — rather than as a consequence for gaming, because a punitive framing usually costs you the appointment itself.

Two practical things in the meantime. First, replace switching off the router with an announced end and a ten-minute warning. Being cut off mid-round in front of a team is experienced as public humiliation, which is where the twenty minutes of screaming came from; leaving a round is something he can actually do. Second, attach one privilege to sleep and homework rather than to gaming hours, so the negotiation stops being about the same number every evening.

It is worth noticing that he did negotiate a plan and kept it for two days. That is not nothing — it tells you he is not simply refusing.

What does he say about school when homework is not the subject?
""",
# 7 — cultural integration and identity struggles
"""
Thank you for writing. Three conversations in one week, with three children, each of them about belonging — and you end your message by saying that you are failing all three. I would like to offer a different reading: all three brought it to you. In families where children stop bringing these things home, the situation is far harder to reach.

I would start with your daughter. Being told she will never really be German, while no longer feeling Syrian either, is a real conflict and not a passing schoolyard remark — and she is carrying it while also acting as the family's interpreter at appointments and parents' evenings. Two things would help her: someone outside the family to talk to, and contact with other young people who live in both languages.

Concretely, ask the practice and the school for professional interpreters. In most settings you are entitled to this, and it lets you tell your daughter explicitly that the job is no longer hers — that sentence usually matters more than the arrangement itself. For your son, ask the school what language support is available and treat the Realschule question as a question about pathways: many students move up again later, and his accent is a stage, not a level.

Your youngest is repeating what she heard in her group this week. At six that changes again, especially if Arabic stays attached to warm moments at home rather than to a rule.

Which of the three do you feel is most alone with this at the moment?
""",
# 8 — teenager wanting to move out for apprenticeship
"""
Thank you for this message. A great deal has shifted since your first one. You saw the flat, you met the flatmate, and you saw a version of your son that does not show up at home — he had already worked out where the nearest doctor is. Your husband has moved, and your son has offered daily calls and a visit every second weekend. That is not a seventeen-year-old pushing past you; that is one negotiating with you.

For the preparation, I would use the months until August as a practice phase rather than a list of instructions. Let him do the shopping and cook twice a week while you are still there to be asked, let him handle his own laundry, and set up a simple monthly budget together — including what happens when the money runs out in week three.

For the asthma medication, build something he owns rather than something you monitor: a reminder he sets himself, a weekly dispenser, and registration with a practice in the new city before he moves. At that age adherence fails on logistics, not on willingness.

For yourself: write the agreements down, with a review date after four weeks. Then the daily call can be relaxed as a planned step rather than dropped in an argument, and you will have evidence of how it is actually going instead of only your fear.

Being frightened and letting him go are not contradictory. You are already doing both.

What would you like him to have heard from you before he drives off in August?
""",
# 9 — sibling rivalry and unequal treatment
"""
Thank you for writing back — and I think your answer did more work than my question did. A marble run that took three days is precisely the kind of achievement that has never been on your wall. Certificates get framed; cardboard gets tidied away before visitors come.

Your daughter's reaction on Tuesday is uncomfortable, but it does not mean the approach was wrong. She has just watched attention move for the first time, and she is testing whether it comes back. Both children are asking the same question in different languages.

Two things I would try. First, put the marble run somewhere visible — the same wall as the certificates, not a shelf in his room — and tell him out loud why it is there. Recognition works when it is public within the family, which is exactly what has made your daughter's achievements feel larger. Second, replace spontaneous compensation with structure: twenty minutes each, on named days, that neither child has to earn or ask for. Attention stops being scarce once it becomes predictable.

I would also see the assessment through. When the result is there, explaining it to both children in age-appropriate words lets the extra support your son will need be read as need rather than as preference.

One last thing: your sentence about your own parents is doing a lot of quiet work in this. Noticing the pattern is not the same as repeating it.

When your daughter asks for your attention, what does she usually ask for?
""",
]


# ===========================================================================
# METADATA
# ===========================================================================

# Rendered prompt + case length, per case.
#   analysis: measured input sizes of the 2026-02-15 production run (same cases,
#             comparable prompt length) — see demo_video_data.OUTPUT_METADATA.
#   reply:    the reply prompt is shorter than the analysis prompt, so the
#             rendered input is correspondingly smaller.
# Both models share a tokenizer family, so the input size is model-independent.
ANALYSIS_INPUT_TOKENS = [886, 889, 879, 935, 916, 962, 968, 1007, 984, 1039]
REPLY_INPUT_TOKENS = [701, 704, 694, 750, 731, 777, 783, 822, 799, 854]

# (output_tokens, processing_time_ms) per case. 24B runs at ~100 tok/s, the
# 128B dense model at roughly half that — hence the ~2-6 s vs ~5-12 s bands.
_ANALYSIS_RUNTIME = {
    MODEL_24B: [
        (456, 4340), (409, 3860), (408, 3910), (397, 3780), (370, 3520),
        (395, 3790), (421, 4010), (424, 4070), (394, 3720), (430, 4120),
    ],
    MODEL_128B: [
        (461, 9180), (503, 10110), (478, 9520), (453, 9070), (494, 9930),
        (495, 9860), (474, 9510), (508, 10190), (486, 9680), (513, 10310),
    ],
}
_REPLY_RUNTIME = {
    MODEL_24B: [
        (286, 2740), (273, 2580), (277, 2660), (275, 2610), (269, 2570),
        (249, 2390), (260, 2470), (269, 2580), (268, 2540), (253, 2430),
    ],
    MODEL_128B: [
        (330, 6580), (355, 7120), (338, 6790), (364, 7260), (333, 6640),
        (335, 6730), (342, 6810), (341, 6850), (346, 6900), (334, 6660),
    ],
}


def _cost_usd(model_key: str, input_tokens: int, output_tokens: int) -> float:
    """Token cost for one output, from the model's seeded per-million prices.

    Computed rather than hard-coded so the 24B/128B cost gap in the UI always
    matches the pricing in ``db/models/llm_model.py`` (a visitor comparing the
    two models sees a truthful ~6x difference).
    """
    price_in, price_out = _PRICE_PER_MILLION[model_key]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


def _build_metadata(model_key: str, input_tokens: list, runtime: list) -> list:
    """Per-output metadata dicts in the demo_video_data shape (one per case)."""
    return [
        {
            'input_tokens': in_tok,
            'output_tokens': out_tok,
            'cost_usd': _cost_usd(model_key, in_tok, out_tok),
            'processing_time_ms': ms,
        }
        for in_tok, (out_tok, ms) in zip(input_tokens, runtime)
    ]


OUTPUT_METADATA = {
    PROMPT_ANALYSIS: {
        model_key: _build_metadata(model_key, ANALYSIS_INPUT_TOKENS, runtime)
        for model_key, runtime in _ANALYSIS_RUNTIME.items()
    },
    PROMPT_REPLY: {
        model_key: _build_metadata(model_key, REPLY_INPUT_TOKENS, runtime)
        for model_key, runtime in _REPLY_RUNTIME.items()
    },
}


def job_totals(prompt_key: str) -> dict:
    """Aggregate token/cost totals for one job (both models, all cases).

    The job header in the UI shows these, so they must equal the sum of the
    seeded outputs — computing them avoids a stale hard-coded constant.
    """
    per_model = OUTPUT_METADATA[prompt_key]
    total_tokens = sum(
        m['input_tokens'] + m['output_tokens']
        for metas in per_model.values() for m in metas
    )
    total_cost = round(
        sum(m['cost_usd'] for metas in per_model.values() for m in metas), 6
    )
    return {'total_tokens': total_tokens, 'total_cost_usd': total_cost}


def build_sample_outputs() -> dict:
    """Assemble the canned output texts, keyed ``[prompt_key][model_key][case]``.

    The 24B analysis texts are composed at call time: the genuine production
    output from the demo-video dataset becomes the **Situation** section and the
    authored sections are appended (see module docstring). ``demo_video_data``
    is imported lazily because it pulls in the SQLAlchemy models, which are only
    importable inside the Flask app.
    """
    from db.seeders.demo_video_data import SAMPLE_OUTPUTS as DEMO_VIDEO_OUTPUTS

    genuine_situations = DEMO_VIDEO_OUTPUTS['structured']['mistral']
    analysis_24b = [
        "**Situation**\n" + situation.strip() + "\n\n" + sections.strip()
        for situation, sections in zip(genuine_situations, ANALYSIS_24B_SECTIONS)
    ]

    return {
        PROMPT_ANALYSIS: {
            MODEL_24B: analysis_24b,
            MODEL_128B: [text.strip() for text in ANALYSIS_128B],
        },
        PROMPT_REPLY: {
            MODEL_24B: [text.strip() for text in REPLY_24B],
            MODEL_128B: [text.strip() for text in REPLY_128B],
        },
    }
