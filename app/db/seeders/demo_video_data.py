"""
Demo Video Data Seeder

Creates pre-seeded data for the IJCAI 2026 demo video:
1. Two counselling situation extraction prompts
2. A completed batch generation job with outputs
3. Sample outputs for all 10 counselling cases x 2 prompts x 2 models

This ensures the demo video can show completed results without waiting
for actual LLM generation during recording.
"""
import logging
from datetime import datetime, timedelta

from db.database import db
from db.tables import User, UserPrompt
from db.models.generation import GenerationJob, GeneratedOutput, GenerationJobStatus, GeneratedOutputStatus
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)

# Counselling cases embedded directly (avoids file path issues in Docker)
COUNSELLING_CASES = [
    {
        "subject": "Custody concerns after separation",
        "content": "Client wrote on 12/01/2026 at 2:30 PM:\nMy partner and I separated three weeks ago after five years together. We have two children, a daughter aged 7 and a son aged 4. I moved out and I am currently staying with the children at my mother's apartment. It is very cramped \u2014 the children share a small room and my son has been wetting the bed again since the move. My ex-partner wants the children every weekend, but my daughter refuses to go. She says she is angry at her father. I work part-time as a nurse and my shifts change weekly, so a fixed visitation schedule is difficult. I have no idea how to handle the legal side of custody.\n\nCounsellor wrote on 13/01/2026 at 9:15 AM:\nThank you for reaching out. It sounds like you are dealing with a lot of changes at once \u2014 a new living situation, your children's emotional reactions, and the question of custody arrangements. Bed-wetting in young children after a major life change is very common and usually temporary. Regarding your daughter's refusal, children often express loyalty conflicts through anger. Have you been able to talk with your ex-partner about a flexible schedule that accounts for your shift work? For the legal aspects, I would recommend contacting your local family counselling centre \u2014 they offer free mediation for separating parents.\n\nClient wrote on 15/01/2026 at 8:45 PM:\nThank you for your response. The situation has gotten worse this week. My ex showed up unannounced at my mother's place on Wednesday and there was an argument in front of the children. My daughter locked herself in the bathroom and would not come out for an hour. My mother says I should get a lawyer immediately, but I cannot afford one right now. My son has started asking every morning whether Daddy is coming today. I feel completely overwhelmed and I am not sleeping well."
    },
    {
        "subject": "School refusal and possible bullying",
        "content": "Client wrote on 05/01/2026 at 6:12 PM:\nI am writing because my 14-year-old son has refused to go to school for the past three weeks. Every morning he complains of headaches and stomach aches, but our paediatrician found nothing physically wrong. Before this started, he was an average student and had a small group of friends. My son will not tell me what happened. His form teacher called and said he has 15 unexcused absences now. I am a single father and I have already used all my remaining leave days from work to stay home with him. I am worried about his grades and whether the school will involve the youth welfare office.\n\nCounsellor wrote on 06/01/2026 at 10:00 AM:\nThank you for writing. School refusal at this age often signals that something significant has changed in the social environment. The physical symptoms your son reports are real \u2014 they are a stress response, even without an organic cause. It may help to gently explore whether there has been conflict with peers. Sometimes children at this age experience social exclusion or bullying but feel ashamed to talk about it. I would suggest requesting a meeting with the school counsellor, ideally without your son present at first, to understand what the school has observed. The youth welfare office is usually involved only in prolonged cases and their role is supportive, not punitive.\n\nClient wrote on 08/01/2026 at 9:30 PM:\nI spoke with his form teacher again today. She mentioned that a group of boys in his class has been making comments about his clothes and his phone being old. She was not sure if it counts as bullying. When I carefully asked my son about it tonight, he started crying and said everyone hates him and he never wants to go back. He also said he has been eating lunch alone for two months. I feel terrible that I did not notice earlier."
    },
    {
        "subject": "Conflicts with teenage daughter about boundaries",
        "content": "Client wrote on 08/01/2026 at 10:22 PM:\nMy 16-year-old daughter has been coming home after midnight almost every weekend for the past month. Last Saturday she came home at 2 AM smelling of alcohol. When I confronted her, she screamed at me that I am controlling and that all her friends have more freedom. She slammed her door so hard that the frame cracked. My husband thinks we should take her phone away, but I am afraid that will make things worse. She used to tell me everything, and now she barely speaks to us. Her grades have dropped from mostly Bs to Ds this term. She also quit the volleyball team last month without telling us.\n\nCounsellor wrote on 09/01/2026 at 11:00 AM:\nThank you for reaching out. What you are describing is very typical of the tensions that arise during mid-adolescence \u2014 the push for autonomy often comes in waves that feel sudden and extreme to parents. The alcohol use and the late nights are worth taking seriously, but the way you address them matters more than the specific consequence you choose. Taking the phone might create a power struggle, while a clear conversation about safety expectations could open a door. Can you identify any specific trigger \u2014 did something change in her social group or at school around the time this started?\n\nClient wrote on 11/01/2026 at 7:15 PM:\nI tried to have a calm conversation with her last night, as you suggested. It went poorly at first, but then she admitted that her best friend since primary school moved away in October and she has been hanging out with a new group. She said they think curfews are embarrassing and she does not want to be the only one who has to leave early. She also said she feels like we do not trust her. I am not sure how to set boundaries without pushing her further away."
    },
    {
        "subject": "Exhaustion and burnout as a single parent",
        "content": "Client wrote on 10/01/2026 at 11:45 PM:\nI am a single mother of three children \u2014 a 10-year-old daughter, an 8-year-old son, and a 3-year-old son. I work full-time as an administrative assistant. My ex-husband moved to another city two years ago and pays child support irregularly. Most evenings I do not sit down before 10 PM. I have had recurring headaches for months and my doctor says it is tension-related. Last week I shouted at my 3-year-old for spilling juice and I frightened him so badly he would not come near me for the rest of the evening. I felt horrible. My oldest daughter has started taking on tasks like making sandwiches for her brothers and I can see that it is too much responsibility for her age. I have no family nearby and I cannot afford a babysitter.\n\nCounsellor wrote on 12/01/2026 at 8:30 AM:\nThank you for sharing this with me. What you are describing sounds like an enormous workload and I want you to know that reaching out is an important step. The fact that you noticed your reaction to your youngest and reflected on it shows real self-awareness. Parental burnout is a recognised condition and it does not mean you are a bad mother. Your oldest taking on caregiving tasks is a common pattern in stressed families, and it is good that you are aware of it. Have you looked into local family support services? Many communities offer subsidised after-school care or family helpers. I would also recommend checking whether your employer offers an employee assistance programme.\n\nClient wrote on 14/01/2026 at 10:10 PM:\nI called the family support centre you mentioned. They have a six-week waiting list. In the meantime, my 8-year-old has started acting out at school \u2014 his teacher says he is pushing other children and refusing to sit still. I had to leave work early twice this week for calls from the school. My boss was understanding the first time but made a comment today about reliability. I feel like everything is falling apart and I do not know which problem to tackle first."
    },
    {
        "subject": "Blended family adjustment difficulties",
        "content": "Client wrote on 03/01/2026 at 4:30 PM:\nI moved in with my new partner six months ago. He has a 9-year-old daughter from his previous marriage who lives with us every other week. I have an 11-year-old son from my first marriage who lives with us full-time. The children do not get along. My son says he hates sharing his room when she is here and calls her a guest who should go home. My partner's daughter told her mother that I am mean to her, which is not true \u2014 I simply asked her to help clear the table. Now my partner's ex-wife is threatening to go back to court. My partner feels caught in the middle and we have been arguing almost every night. Last weekend my son asked if he could go live with his father instead.\n\nCounsellor wrote on 05/01/2026 at 9:45 AM:\nThank you for writing. Blended families are one of the most complex family structures, and the adjustment period often takes much longer than parents expect \u2014 research suggests 2 to 5 years for a blended family to find its rhythm. Your son's reaction to sharing his room is about territory and belonging, not about your partner's daughter personally. And the daughter's complaint to her mother is very common \u2014 children in shared custody often test boundaries by playing households against each other. The most important thing right now is that you and your partner present a united front. Would you consider family counselling together? Many of these dynamics respond well to guided conversations.\n\nClient wrote on 07/01/2026 at 8:20 PM:\nThings escalated on Saturday. During dinner my son made a comment about the food and my partner corrected him. My son said you are not my dad and ran to his room. My partner was hurt and said maybe the children are just not ready for this. Later that night my partner's daughter called her mother crying and now the ex-wife has sent a formal letter through her lawyer. I feel like I am losing my partner and my son at the same time."
    },
    {
        "subject": "Dealing with depression as a parent",
        "content": "Client wrote on 06/01/2026 at 3:15 PM:\nI have been diagnosed with moderate depression six months ago and I am on medication. I have a 10-year-old son who I raise together with my wife. Since the diagnosis, I struggle to get through the day. Most mornings I cannot get out of bed before my wife has already taken our son to school. On weekends I often stay in bed until noon. My son asked my wife last week why Daddy is always sad and whether it is his fault. That broke my heart. My wife has been incredibly patient, but I can see she is exhausted from carrying everything alone. I used to coach my son's football team, but I had to step down two months ago because I could not face the other parents. My therapist says I should try to maintain routines, but even small tasks feel overwhelming.\n\nCounsellor wrote on 07/01/2026 at 10:30 AM:\nThank you for reaching out. Living with depression while parenting is enormously challenging, and the guilt you feel about its impact on your son is something many parents in your situation share. Your son's question about whether it is his fault is developmentally very normal \u2014 children naturally centre themselves in family dynamics. It might help to have an age-appropriate conversation with him about how sometimes grown-ups feel unwell in their thoughts and feelings, just like people can feel unwell in their body. This takes the mystery away without burdening him with details. Is your wife receiving any support herself? Partners of people with depression often develop compassion fatigue.\n\nClient wrote on 09/01/2026 at 9:45 PM:\nI tried talking to my son this weekend, loosely following what you suggested. He asked if I was going to get better and I told him honestly that I am working on it. He hugged me and said he would help. My wife and I also talked \u2014 she admitted she has been feeling resentful and exhausted. She said she needs me to at least handle the morning routine twice a week so she can go to work without rushing. I want to do that, but I am not sure I can manage it reliably. My medication was adjusted last week and the side effects make mornings even harder."
    },
    {
        "subject": "Excessive screen time and declining grades",
        "content": "Client wrote on 07/01/2026 at 7:00 PM:\nMy 12-year-old son spends five to six hours a day on his computer, mostly playing an online multiplayer game. On weekends it is even more \u2014 sometimes eight or nine hours. His grades have dropped significantly this term. He went from being in the top third of his class to nearly failing mathematics and English. He has also stopped playing football, which he used to love, and rarely sees his friends in person anymore. When I try to set time limits he becomes extremely angry and once threw his controller at the wall. He says all his friends play even more than he does and that I do not understand because I grew up without the internet. My husband thinks it is just a phase, but I think it is getting out of control.\n\nCounsellor wrote on 08/01/2026 at 9:00 AM:\nThank you for reaching out. The pattern you describe \u2014 increasing play time, withdrawal from previous activities, declining academic performance, and aggressive reactions to limits \u2014 goes beyond a typical hobby. At 12, the social component of online gaming is very powerful because the friendships feel real and immediate. A sudden restriction can feel like social exclusion to him. Rather than removing the computer entirely, I would suggest starting with a structured plan: agree on specific times together, tie gaming time to completed homework, and offer one offline social activity as an alternative. Have you spoken with his teachers about what they observe in class?\n\nClient wrote on 10/01/2026 at 8:30 PM:\nI spoke with his maths teacher today. She said he has been falling asleep in class and has not submitted homework in three weeks. She also said he seems withdrawn and does not interact with classmates during breaks. At home, I tried to talk to him calmly about a screen time plan. He agreed to one hour on weekdays if he can play freely on Saturday. But by Tuesday he had already broken the agreement and when I turned off the router he screamed for twenty minutes and punched a hole in his bedroom door. My husband finally admitted this is serious. We do not know if we need a therapist or a technology intervention or both."
    },
    {
        "subject": "Cultural integration and identity struggles",
        "content": "Client wrote on 09/01/2026 at 5:30 PM:\nWe moved to Germany from Syria four years ago. My husband works in a warehouse and I am currently in a language course, B1 level. We have three children \u2014 a 15-year-old daughter, a 12-year-old son, and a 6-year-old daughter. My oldest daughter speaks fluent German and translates for us at doctor appointments and parent-teacher meetings. I can see this burden is unfair to her. My son is struggling at school because his German is not strong enough for the Gymnasium he attends \u2014 his teacher suggested he move to Realschule, which feels like a failure. My 6-year-old speaks mostly German and sometimes does not understand when we speak Arabic at home. I worry we are losing our culture. My husband thinks the children should focus on German only, but I want them to keep Arabic. We also feel isolated \u2014 we have friendly neighbours but no close friends in the community.\n\nCounsellor wrote on 10/01/2026 at 10:15 AM:\nThank you for sharing your situation. The challenges you describe are very common in families navigating integration, and they often create tension between practical needs and cultural identity. Your daughter's role as interpreter is called language brokering \u2014 research shows it can be both empowering and stressful for children. It would be helpful to reduce her translating responsibilities where possible, for example by using professional interpreters for medical visits. Regarding your son, a move to Realschule is not a failure \u2014 it is a different pathway and many students transfer back later. Bilingualism is a strength, not a conflict. Would your family be open to connecting with a local integration counselling service? They often organise family activities that help with both language and community.\n\nClient wrote on 12/01/2026 at 8:00 PM:\nMy daughter came home crying on Thursday. A classmate told her she would never really be German no matter how well she speaks. She said she does not feel Syrian anymore either and does not know where she belongs. My son refused to go to school on Friday because he is embarrassed about his accent. And my youngest told me she does not want to speak Arabic because the other children in kindergarten said it sounds funny. I feel like I am failing all three of my children in different ways."
    },
    {
        "subject": "Teenager wanting to move out for apprenticeship",
        "content": "Client wrote on 11/01/2026 at 12:30 PM:\nMy 17-year-old son was offered an apprenticeship as an electrician in a city 200 kilometres away starting in August. He wants to accept it and move into a shared flat with another apprentice. My husband and I think he is too young. He has never lived alone, he cannot cook, and he barely manages to keep his room clean. He also has mild asthma that requires daily medication, and I am worried about who will make sure he takes it. When we told him we would prefer him to find something closer, he accused us of holding him back and not believing in him. He has been cold and distant for a week now. His older sister moved out at 21 and she thinks we are being overprotective. My husband is more open to it than I am, which makes me feel like the only one saying no.\n\nCounsellor wrote on 12/01/2026 at 11:00 AM:\nThank you for writing. Your concerns are completely understandable \u2014 letting a 17-year-old move 200 kilometres away touches on deep parental instincts. At the same time, your son receiving an apprenticeship offer is a significant achievement and his enthusiasm suggests real motivation. Many young people at 17 are ready for more independence than parents expect. The practical concerns \u2014 cooking, medication, daily routines \u2014 are solvable with preparation. Rather than a yes or no, would you consider a structured transition? For example, visiting the city together, meeting the flatmate, setting up a medication reminder system, and agreeing on regular check-ins. This shows trust while providing a safety net.\n\nClient wrote on 14/01/2026 at 6:45 PM:\nWe tried your suggestion of a visit. We drove there last weekend and saw the flat \u2014 it was small but clean. The other apprentice seemed responsible. My son was different during the trip, more grown up somehow. He showed us where the company is and had already researched the nearest doctor. On the drive home my husband said he thinks we should let him go. I am still afraid, but I also realized that if we say no, he might resent us. He has agreed to a daily video call for the first month and to come home every second weekend. I suppose my question now is how to prepare him and myself for this."
    },
    {
        "subject": "Sibling rivalry and unequal treatment concerns",
        "content": "Client wrote on 04/01/2026 at 3:00 PM:\nI have two children, a daughter aged 11 and a son aged 8. My daughter is academically gifted \u2014 she reads constantly, gets excellent grades, and teachers praise her regularly. My son is more physical and creative but struggles with reading and writing. He was recently tested and shows signs of dyslexia, though the formal assessment is still pending. The problem is that my son has started saying things like you love her more and she gets everything. Last week he destroyed a drawing his sister made for a school project. My daughter then said she wished she was an only child. My husband and I try to be fair, but we spend more time helping our daughter with her advanced projects and homework while our son mostly plays outside. I realize now that our son might interpret this as favouritism. My own parents compared me to my sister constantly, and I swore I would never do that.\n\nCounsellor wrote on 05/01/2026 at 10:45 AM:\nThank you for sharing this. The dynamic you describe is very common in families where children have different strengths and needs. Your son is not wrong in his perception \u2014 children are very sensitive to how parental time and attention are distributed, even when parents intend to be fair. The key distinction is between equal treatment and equitable treatment. Equal means giving the same to both; equitable means giving each child what they need. Right now, your daughter's academic achievements receive visible recognition, while your son's strengths in physical activity and creativity may feel invisible to him. I would suggest creating dedicated one-on-one time with each child \u2014 even 20 minutes of focused attention daily makes a measurable difference. How does your son express his creativity?\n\nClient wrote on 07/01/2026 at 7:30 PM:\nYour question about creativity made me think. My son actually builds the most incredible things with Lego and cardboard \u2014 last month he built a working marble run that took him three days. But we never displayed it the way we hang up his sister's art and certificates. I tried dedicated time this week. I spent 30 minutes with my son building something together on Tuesday, and he was so happy he told his friend about it. But my daughter noticed and asked why I was spending so much time with him. She said it is not fair because she has to do her homework alone. I feel like whatever I do, one of them feels hurt."
    }
]

# Sample generated outputs for the demo (pre-generated)
# Keys: "structured" = Structured Situation Analysis prompt, "narrative" = Situation Summary prompt
SAMPLE_OUTPUTS = {
    # Structured Situation Analysis outputs (JSON format with references)
    "structured": [
        '{"situation_descriptions": [{"text": "Single parent working part-time as a nurse with variable shifts, currently living in cramped conditions at her mother\'s apartment with two children (daughter 7, son 4).", "reference": ["I work part-time as a nurse and my shifts change weekly", "I am currently staying with the children at my mother\'s apartment"]}, {"text": "The 4-year-old son is showing regressive behaviour (bed-wetting) since the parental separation three weeks ago, while the 7-year-old daughter is exhibiting loyalty conflict by refusing visits with her father.", "reference": ["my son has been wetting the bed again since the move", "my daughter refuses to go. She says she is angry at her father"]}, {"text": "Escalating conflict between the separated parents, including an unannounced visit that led to an argument in front of the children, causing acute distress in the daughter.", "reference": ["My ex showed up unannounced at my mother\'s place on Wednesday and there was an argument in front of the children", "My daughter locked herself in the bathroom and would not come out for an hour"]}]}',
        '{"situation_descriptions": [{"text": "A 14-year-old boy has been refusing school attendance for three weeks with psychosomatic symptoms (headaches, stomach aches) despite no organic cause found by the paediatrician.", "reference": ["my 14-year-old son has refused to go to school for the past three weeks", "our paediatrician found nothing physically wrong"]}, {"text": "Single father who has exhausted his remaining work leave days, expressing concern about academic consequences and potential youth welfare office involvement.", "reference": ["I am a single father and I have already used all my remaining leave days", "I am worried about his grades and whether the school will involve the youth welfare office"]}, {"text": "Evidence of sustained peer exclusion: the boy has been eating lunch alone for two months and classmates have been making derogatory comments about his appearance.", "reference": ["he has been eating lunch alone for two months", "a group of boys in his class has been making comments about his clothes and his phone being old"]}]}',
        '{"situation_descriptions": [{"text": "A 16-year-old daughter is returning home after midnight on weekends, with one confirmed instance of alcohol use, and has quit her volleyball team without informing her parents.", "reference": ["she came home at 2 AM smelling of alcohol", "She also quit the volleyball team last month without telling us"]}, {"text": "Significant academic decline from B-level to D-level grades this term, coinciding with a change in peer group after her best friend moved away in October.", "reference": ["Her grades have dropped from mostly Bs to Ds this term", "her best friend since primary school moved away in October"]}, {"text": "The daughter expresses feeling mistrusted by her parents and fears social exclusion from her new peer group due to curfew restrictions.", "reference": ["she feels like we do not trust her", "she does not want to be the only one who has to leave early"]}]}',
        '{"situation_descriptions": [{"text": "Single mother of three children (ages 10, 8, 3) working full-time as an administrative assistant with no family support nearby and irregular child support from the ex-husband.", "reference": ["I am a single mother of three children", "My ex-husband moved to another city two years ago and pays child support irregularly"]}, {"text": "The mother is showing signs of burnout including chronic tension headaches and loss of emotional regulation, having frightened her 3-year-old by shouting over a minor incident.", "reference": ["I have had recurring headaches for months and my doctor says it is tension-related", "I shouted at my 3-year-old for spilling juice and I frightened him so badly"]}, {"text": "The 10-year-old daughter is taking on age-inappropriate caregiving responsibilities, while the 8-year-old son has started exhibiting aggressive behaviour at school.", "reference": ["My oldest daughter has started taking on tasks like making sandwiches for her brothers", "my 8-year-old has started acting out at school"]}]}',
        '{"situation_descriptions": [{"text": "A blended family of six months with an 11-year-old son (full-time) and a 9-year-old stepdaughter (alternating weeks) experiencing territorial conflicts over shared living space.", "reference": ["I moved in with my new partner six months ago", "My son says he hates sharing his room when she is here"]}, {"text": "Escalating inter-household conflict: the stepdaughter reported negative treatment to her biological mother, leading to legal threats from the ex-wife.", "reference": ["My partner\'s daughter told her mother that I am mean to her", "the ex-wife has sent a formal letter through her lawyer"]}, {"text": "The 11-year-old son is rejecting the stepfather\'s authority and has expressed a wish to live with his biological father instead.", "reference": ["My son said you are not my dad and ran to his room", "my son asked if he could go live with his father instead"]}]}',
        '{"situation_descriptions": [{"text": "Father diagnosed with moderate depression six months ago and currently on medication, struggling to participate in daily family routines and unable to get out of bed most mornings.", "reference": ["I have been diagnosed with moderate depression six months ago", "Most mornings I cannot get out of bed before my wife has already taken our son to school"]}, {"text": "The 10-year-old son is questioning whether his father\'s sadness is his fault, indicating the child is aware of and affected by the parent\'s condition.", "reference": ["My son asked my wife last week why Daddy is always sad and whether it is his fault"]}, {"text": "The wife is experiencing caregiver exhaustion from managing all household and parenting responsibilities alone, and has expressed feeling resentful.", "reference": ["she admitted she has been feeling resentful and exhausted", "She said she needs me to at least handle the morning routine twice a week"]}]}',
        '{"situation_descriptions": [{"text": "A 12-year-old boy is spending 5-6 hours daily on online gaming (8-9 hours on weekends), has abandoned previous hobbies and in-person friendships.", "reference": ["My 12-year-old son spends five to six hours a day on his computer", "He has also stopped playing football"]}, {"text": "Severe academic decline from top third of class to near-failure in mathematics and English, with the student falling asleep in class and not submitting homework.", "reference": ["He went from being in the top third of his class to nearly failing mathematics and English", "he has been falling asleep in class and has not submitted homework in three weeks"]}, {"text": "Aggressive reactions to screen time limits including throwing a controller and punching a hole in a bedroom door, indicating poor impulse control.", "reference": ["he becomes extremely angry and once threw his controller at the wall", "he screamed for twenty minutes and punched a hole in his bedroom door"]}]}',
        '{"situation_descriptions": [{"text": "A Syrian family of five living in Germany for four years, with the mother at B1 language level and the father working in a warehouse, experiencing social isolation.", "reference": ["We moved to Germany from Syria four years ago", "I am currently in a language course, B1 level"]}, {"text": "The 15-year-old daughter serves as family interpreter (language brokering) and is experiencing an identity crisis after a classmate told her she would never be truly German.", "reference": ["My oldest daughter speaks fluent German and translates for us", "A classmate told her she would never really be German"]}, {"text": "The 12-year-old son is struggling academically due to language barriers and refusing school, while the 6-year-old is rejecting the family\'s native language.", "reference": ["his German is not strong enough for the Gymnasium", "my youngest told me she does not want to speak Arabic"]}]}',
        '{"situation_descriptions": [{"text": "A 17-year-old son has been offered an electrician apprenticeship 200 km away and wants to move into a shared flat, causing disagreement between the parents.", "reference": ["My 17-year-old son was offered an apprenticeship as an electrician in a city 200 kilometres away", "My husband is more open to it than I am"]}, {"text": "The son has mild asthma requiring daily medication, and the mother is concerned about his ability to manage independent living without supervision.", "reference": ["He also has mild asthma that requires daily medication", "He has never lived alone, he cannot cook"]}, {"text": "Following a joint visit to the city, the family has tentatively agreed to allow the move with structured check-ins including daily video calls and biweekly visits home.", "reference": ["He has agreed to a daily video call for the first month and to come home every second weekend", "he had already researched the nearest doctor"]}]}',
        '{"situation_descriptions": [{"text": "Two siblings (daughter 11, son 8) with markedly different profiles: the daughter is academically gifted while the son shows signs of dyslexia (formal assessment pending).", "reference": ["My daughter is academically gifted", "He was recently tested and shows signs of dyslexia"]}, {"text": "The 8-year-old son perceives favouritism and has acted out by destroying his sister\'s school project, while the sister has expressed wishing she were an only child.", "reference": ["my son has started saying things like you love her more", "Last week he destroyed a drawing his sister made"]}, {"text": "The parents recognise an imbalance in attention distribution, with more time spent on the daughter\'s academic projects while the son\'s creative strengths remain unacknowledged.", "reference": ["we spend more time helping our daughter with her advanced projects", "we never displayed it the way we hang up his sister\'s art and certificates"]}]}'
    ],
    # Situation Summary outputs (narrative paragraph style)
    "narrative": [
        "The client is a part-time nurse who recently separated from her partner and is now living with her two children, aged 7 and 4, in her mother's cramped apartment. The younger child has developed regressive symptoms including bed-wetting, while the older daughter is refusing contact with her father and showing signs of acute distress after witnessing a confrontation between the separated parents. The client reports feeling overwhelmed by the simultaneous challenges of unstable housing, unresolved custody arrangements, and her children's emotional reactions, compounded by financial constraints that prevent her from seeking legal advice.",
        "The client is a single father whose 14-year-old son has been refusing to attend school for three weeks, presenting with psychosomatic symptoms that have no organic cause. The boy has been experiencing social exclusion at school, eating lunch alone for two months and enduring derogatory comments from classmates about his appearance and belongings. The father has exhausted his work leave to stay home with his son and is concerned about academic consequences and potential involvement of the youth welfare office.",
        "The client's 16-year-old daughter is exhibiting a cluster of behavioural changes including late-night outings, alcohol use, academic decline from B to D grades, and withdrawal from her volleyball team and family communication. These changes coincide with the departure of her closest friend in October and her integration into a new peer group that normalises boundary-pushing behaviour. The daughter herself reports feeling mistrusted by her parents and fears social consequences from her peers if she complies with household rules.",
        "The client is a single mother of three children aged 10, 8, and 3 who works full-time with no local family support and receives irregular child support from her ex-husband. She is showing clear signs of parental burnout including chronic tension headaches, emotional dysregulation, and sleep deprivation, having recently frightened her youngest child by shouting over a minor incident. The eldest daughter has assumed age-inappropriate caregiving responsibilities while the middle child has begun exhibiting aggressive behaviour at school, and the mother's employer has started questioning her reliability.",
        "The client has been living with her new partner for six months in a blended family arrangement involving her 11-year-old son and his 9-year-old daughter on alternating weeks. The children are in open conflict over shared living space and authority boundaries, with the son rejecting the stepfather's role and the stepdaughter reporting perceived mistreatment to her biological mother, who has now initiated legal action. The couple's relationship is under severe strain from nightly arguments, and the client's son has expressed a wish to leave the household entirely.",
        "The client is a father with moderate depression who has been on medication for six months and is struggling to maintain daily routines, including getting out of bed in the morning. His 10-year-old son has noticed his father's persistent sadness and questioned whether he is the cause, while the client's wife is experiencing caregiver exhaustion from shouldering all parenting and household responsibilities alone. A recent medication adjustment has worsened the client's morning functioning, creating tension around a request from his wife to share the morning routine at least twice a week.",
        "The client's 12-year-old son has developed a pattern of excessive online gaming, spending five to nine hours daily on a multiplayer game, which has coincided with a sharp academic decline, withdrawal from previous social activities, and increasingly aggressive responses to parental limits. School reports confirm the boy is falling asleep in class, has not submitted homework in three weeks, and is socially isolated during breaks. Attempts to negotiate structured screen time agreements have failed, with the most recent escalation resulting in property damage, prompting both parents to acknowledge the need for professional intervention.",
        "The client is a Syrian mother of three who has been living in Germany for four years and is currently at B1 language level, while her husband works in a warehouse. The 15-year-old daughter carries the burden of interpreting for the family and is experiencing an identity crisis after being told by a peer that she will never truly be German, the 12-year-old son is facing academic difficulties at Gymnasium due to language gaps, and the 6-year-old is rejecting Arabic after being teased in kindergarten. The parents disagree about language priorities, with the mother wanting to preserve Arabic and the father favouring full German immersion.",
        "The client's 17-year-old son has received an electrician apprenticeship offer in a city 200 kilometres away and wants to move into a shared flat, creating a disagreement between the parents about his readiness for independent living. The mother's concerns centre on his lack of practical life skills and his mild asthma requiring daily medication, though a joint visit to the city revealed the son's surprising maturity in planning for his move. The family has reached a tentative agreement that includes daily video calls for the first month and biweekly visits home, and the client is now focused on preparation rather than prevention.",
        "The client's family includes an academically gifted 11-year-old daughter and an 8-year-old son who shows signs of dyslexia and excels in hands-on creativity rather than conventional schoolwork. The son perceives favouritism toward his sister, whose achievements receive more visible recognition, and has expressed his frustration through destructive behaviour, while the daughter resents any rebalancing of parental attention. The parents have recognised the imbalance and begun dedicating individual time to each child, but find that adjustments in either direction trigger protests from the other sibling."
    ]
}


def seed_demo_video_prompts():
    """
    Creates the counselling situation extraction prompts for the demo video.
    """
    logger.info("Seeding demo video prompts...")

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping demo video prompt seeding")
        return []

    def build_blocks(role_text: str, task_text: str, data_text: str):
        return {
            "Role Definition": {
                "content": role_text,
                "position": 0
            },
            "Task Explanation": {
                "content": task_text,
                "position": 1
            },
            "Data Format Explanation": {
                "content": data_text,
                "position": 2
            }
        }

    prompts_data = [
        {
            "name": "Structured Situation Analysis",
            "content": {
                "blocks": build_blocks(
                    role_text=(
                        "You are an assistant for professionals in psychosocial online counselling. "
                        "You support counsellors in systematically capturing the current life situation of help-seeking clients. "
                        "You analyze email threads between clients and counsellors and extract factual information about the client's circumstances."
                    ),
                    task_text=(
                        "Analyze the email thread and produce a structured situation description of the client's current life circumstances in up to 3 bullet points.\n\n"
                        "Each bullet point must contain:\n"
                        "- **Text**: A concise description of one aspect of the life situation (max 2 sentences, max 160 characters)\n"
                        "- **Reference**: Direct quotes from the email thread as evidence\n\n"
                        "Focus on: housing situation, family relationships, children (age, development, health), professional/educational situation, health status, social conflicts.\n\n"
                        'Return the result as JSON:\n'
                        '```json\n'
                        '{"situation_descriptions": [{"text": "...", "reference": ["quote 1", "quote 2"]}]}\n'
                        '```\n\n'
                        "Rules:\n"
                        "- Use only facts from the thread, no speculation\n"
                        "- Avoid introductory phrases, present information directly\n"
                        "- When counselling parents, also include information about their children\n\n"
                        "Few-shot example:\n\n"
                        "Input: A single mother reports that her 8-year-old son has been refusing to attend school for two weeks, "
                        "complaining of stomach aches. The pediatrician found no physical cause. She works part-time and cannot stay home every day.\n\n"
                        "Output:\n"
                        '{"situation_descriptions": [{"text": "Single mother working part-time, unable to provide daily supervision due to work obligations.", '
                        '"reference": ["I work part-time and cannot stay home every day"]}, '
                        '{"text": "8-year-old son refusing school attendance for two weeks with psychosomatic symptoms.", '
                        '"reference": ["my son has been refusing to go to school for two weeks", "he complains of stomach aches but the pediatrician found nothing"]}]}'
                    ),
                    data_text=(
                        "Subject: {{subject}}\n\n"
                        "Email thread:\n"
                        "{{content}}\n\n"
                        'Return only the JSON object with the "situation_descriptions" array. No additional explanations.'
                    )
                )
            }
        },
        {
            "name": "Situation Summary",
            "content": {
                "blocks": build_blocks(
                    role_text="You are a counselling assistant who helps professionals extract key facts from client communications in online psychosocial counselling.",
                    task_text="Read the email thread and write a brief situation overview in 2-3 sentences. Focus on the client's living situation, family, health, and main concerns. Write in third person, present tense.",
                    data_text=(
                        "Subject: {{subject}}\n\n"
                        "Email thread:\n"
                        "{{content}}\n\n"
                        "Write a plain text paragraph. No JSON, no bullet points."
                    )
                )
            }
        }
    ]

    created_prompts = []
    for prompt_data in prompts_data:
        existing = UserPrompt.query.filter_by(
            user_id=admin_user.id,
            name=prompt_data["name"]
        ).first()

        if existing:
            logger.debug(f"Prompt '{prompt_data['name']}' already exists")
            created_prompts.append(existing)
            continue

        new_prompt = UserPrompt(
            user_id=admin_user.id,
            name=prompt_data["name"],
            content=prompt_data["content"]
        )
        db.session.add(new_prompt)
        db.session.flush()  # Get the ID
        created_prompts.append(new_prompt)
        logger.info(f"Created demo prompt: {prompt_data['name']}")

    db.session.commit()
    return created_prompts


def seed_demo_video_generation_job():
    """
    Creates a completed batch generation job with all outputs
    for the demo video.
    """
    logger.info("Seeding demo video generation job...")

    # Check if job already exists
    existing_job = GenerationJob.query.filter_by(name="Counselling Situation Extraction").first()
    if existing_job:
        logger.info("Demo video generation job already exists, skipping")
        return existing_job

    # Get LLM models
    mistral_small = LLMModel.query.filter_by(
        model_id='mistralai/Mistral-Small-3.2-24B-Instruct-2506'
    ).first()
    magistral_small = LLMModel.query.filter_by(
        model_id='mistralai/Magistral-Small-2509'
    ).first()

    if not mistral_small or not magistral_small:
        logger.warning("Required LLM models not found, skipping demo job seeding")
        return None

    # Get prompts
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping demo job seeding")
        return None

    prompt_structured = UserPrompt.query.filter_by(
        user_id=admin_user.id,
        name="Structured Situation Analysis"
    ).first()
    prompt_summary = UserPrompt.query.filter_by(
        user_id=admin_user.id,
        name="Situation Summary"
    ).first()
    if not prompt_structured or not prompt_summary:
        logger.warning("Demo prompts not found, creating them first...")
        prompts = seed_demo_video_prompts()
        prompts_by_name = {p.name: p for p in prompts}
        prompt_structured = prompt_structured or prompts_by_name.get("Structured Situation Analysis")
        prompt_summary = prompt_summary or prompts_by_name.get("Situation Summary")
        if not prompt_structured or not prompt_summary:
            logger.error("Failed to create demo prompts")
            return None

    # Use embedded counselling cases
    cases = COUNSELLING_CASES

    # Create the generation job
    now = datetime.utcnow()
    total_outputs = len(cases) * 2 * 2  # 10 cases x 2 prompts x 2 models = 40

    job = GenerationJob(
        name="Counselling Situation Extraction",
        description="Demo batch generation job comparing two prompts across two LLM models on 10 counselling cases.",
        status=GenerationJobStatus.COMPLETED,
        config_json={
            "mode": "matrix",
            "sources": {
                "type": "manual",
                "items": cases
            },
            "prompts": [
                {"template_name": prompt_structured.name},
                {"template_name": prompt_summary.name}
            ],
            "llm_models": [mistral_small.model_id, magistral_small.model_id],
            "generation_params": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        total_items=total_outputs,
        completed_items=total_outputs,
        failed_items=0,
        total_tokens=total_outputs * 800,  # Estimated
        total_cost_usd=0.05,  # Estimated
        created_by='admin',
        created_at=now - timedelta(hours=2),
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=45)
    )
    db.session.add(job)
    db.session.flush()

    # Create outputs for each combination
    output_id = 0
    def get_block_content(prompt, block_name):
        blocks = (prompt.content or {}).get('blocks', {})
        block = blocks.get(block_name, {})
        return block.get('content', '') if isinstance(block, dict) else ''

    def render_system_prompt(prompt):
        parts = [
            get_block_content(prompt, "Role Definition"),
            get_block_content(prompt, "Task Explanation")
        ]
        return "\n\n".join([p for p in parts if p])

    def render_user_prompt(prompt, case):
        template = get_block_content(prompt, "Data Format Explanation")
        if not template:
            return f"Subject: {case['subject']}\n\n{case['content']}"
        return (
            template
            .replace("{{subject}}", case["subject"])
            .replace("{{content}}", case["content"])
        )

    for case_idx, case in enumerate(cases):
        for prompt_type, prompt, summary_key in [
            ("structured", prompt_structured, "structured"),
            ("narrative", prompt_summary, "narrative"),
        ]:
            for model in [mistral_small, magistral_small]:
                output_text = SAMPLE_OUTPUTS[summary_key][case_idx]

                output = GeneratedOutput(
                    job_id=job.id,
                    prompt_template_id=None,  # user_prompts != prompt_templates
                    llm_model_id=model.id,
                    llm_model_name=model.model_id,
                    prompt_variant_name=prompt.name,
                    prompt_variables_json={
                        'source_index': case_idx,
                        'source_subject': case['subject']
                    },
                    generated_content=output_text,
                    rendered_system_prompt=render_system_prompt(prompt),
                    rendered_user_prompt=render_user_prompt(prompt, case),
                    status=GeneratedOutputStatus.COMPLETED,
                    input_tokens=len(case['content'].split()) + 50,  # Rough estimate
                    output_tokens=len(output_text.split()),
                    total_cost_usd=0.001,
                    processing_time_ms=1500 + (output_id * 50),  # Vary slightly
                    attempt_count=1,
                    created_at=now - timedelta(hours=2),
                    completed_at=now - timedelta(hours=1, minutes=50 - output_id)
                )
                db.session.add(output)
                output_id += 1

    db.session.commit()
    logger.info(f"Created demo generation job with {total_outputs} outputs")
    return job


def seed_demo_video_data(db_instance=None):
    """
    Main entry point: Seeds all demo video data.
    Call this from the seeders __init__.py
    """
    logger.info("=" * 60)
    logger.info("SEEDING DEMO VIDEO DATA")
    logger.info("=" * 60)

    # 1. Create prompts
    prompts = seed_demo_video_prompts()
    logger.info(f"Demo prompts ready: {len(prompts)} prompts")

    # 2. Create completed generation job
    job = seed_demo_video_generation_job()
    if job:
        logger.info(f"Demo generation job ready: {job.name} (ID: {job.id})")

    logger.info("=" * 60)
    logger.info("DEMO VIDEO DATA SEEDING COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    # For standalone testing
    from app.main import create_app
    app = create_app()
    with app.app_context():
        seed_demo_video_data()
