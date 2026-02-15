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

# Sample generated outputs for the demo (real LLM outputs from Mistral Small 3.2)
# Keys: "structured" = Structured Situation Analysis prompt, "narrative" = Situation Summary prompt
SAMPLE_OUTPUTS = {
    # Structured Situation Analysis outputs (bullet points with quoted references)
    "structured": [
        "1. Living with children (7-year-old daughter, 4-year-old son) in cramped conditions at mother's apartment, son exhibiting bed-wetting. \u2014 \"I am currently staying with the children at my mother's apartment\", \"the children share a small room\", \"my son has been wetting the bed again since the move\"\n\n2. 7-year-old daughter refusing to visit ex-partner, exhibiting anger and anxiety, 4-year-old son asking about father's whereabouts. \u2014 \"my daughter refuses to go\", \"she is angry at her father\", \"my son has started asking every morning whether Daddy is coming today\"\n\n3. Part-time nurse with variable shifts, financial constraints, and no legal representation, experiencing sleep disturbances. \u2014 \"I work part-time as a nurse and my shifts change weekly\", \"I cannot afford [a lawyer] right now\", \"I am not sleeping well\"",
        "1. 14-year-old son refusing school attendance for three weeks with psychosomatic symptoms. \u2014 \"my 14-year-old son has refused to go to school for the past three weeks\", \"Every morning he complains of headaches and stomach aches\"\n\n2. Son experiencing social exclusion and potential bullying at school. \u2014 \"a group of boys in his class has been making comments about his clothes and his phone being old\", \"he started crying and said everyone hates him and he never wants to go back\"\n\n3. Single father has exhausted all leave days, struggling to manage son's school refusal. \u2014 \"I am a single father and I have already used all my remaining leave days from work to stay home with him\"",
        "1. 16-year-old daughter coming home after midnight regularly, consuming alcohol, and exhibiting aggressive behavior. \u2014 \"My 16-year-old daughter has been coming home after midnight almost every weekend for the past month\", \"Last Saturday she came home at 2 AM smelling of alcohol\", \"She screamed at me that I am controlling\", \"she slammed her door so hard that the frame cracked\"\n\n2. Teenage daughter experiencing social changes and academic decline, struggling with parental boundaries. \u2014 \"She admitted that her best friend since primary school moved away in October and she has been hanging out with a new group\", \"her grades have dropped from mostly Bs to Ds this term\", \"she feels like we do not trust her\"",
        "1. Single mother of three children (ages 10, 8, and 3) working full-time with irregular child support from ex-husband. \u2014 \"I am a single mother of three children \u2014 a 10-year-old daughter, an 8-year-old son, and a 3-year-old son\", \"My ex-husband moved to another city two years ago and pays child support irregularly\"\n\n2. Recurring tension-related headaches and recent incident of verbal outburst towards youngest child. \u2014 \"I have had recurring headaches for months and my doctor says it is tension-related\", \"Last week I shouted at my 3-year-old for spilling juice and I frightened him so badly he would not come near me for the rest of the evening\"\n\n3. 8-year-old child exhibiting behavioral issues at school, leading to frequent disruptions at work. \u2014 \"my 8-year-old has started acting out at school \u2014 his teacher says he is pushing other children and refusing to sit still\", \"I had to leave work early twice this week for calls from the school\"",
        "1. Blended family with conflict between 11-year-old son and 9-year-old step-daughter, leading to arguments between client and partner. \u2014 \"The children do not get along\", \"my partner feels caught in the middle and we have been arguing almost every night\", \"my son made a comment about the food and my partner corrected him\"\n2. Client's 11-year-old son expressing desire to live with his father due to family conflicts. \u2014 \"Last weekend my son asked if he could go live with his father instead\"\n3. Partner's ex-wife involved in conflict, threatening legal action due to step-daughter's complaints and family tensions. \u2014 \"my partner's ex-wife is threatening to go back to court\", \"the ex-wife has sent a formal letter through her lawyer\"",
        "1. Client diagnosed with moderate depression six months ago, currently on medication, struggles with daily routines and mornings. \u2014 \"I have been diagnosed with moderate depression six months ago\", \"I struggle to get through the day\", \"Most mornings I cannot get out of bed before my wife has already taken our son to school\", \"On weekends I often stay in bed until noon\", \"my medication was adjusted last week and the side effects make mornings even harder\"\n\n2. Client's wife is exhausted and resentful from carrying the family load, needs support to manage morning routine twice a week. \u2014 \"I can see she is exhausted from carrying everything alone\", \"she admitted she has been feeling resentful and exhausted\", \"she needs me to at least handle the morning routine twice a week so she can go to work without rushing\"\n\n3. 10-year-old son is aware of client's depression, asked about its cause and the client's recovery, expressed willingness to help. \u2014 \"My son asked my wife last week why Daddy is always sad and whether it is his fault\", \"He asked if I was going to get better and I told him honestly that I am working on it\", \"He hugged me and said he would help\"",
        "1. 12-year-old son spending five to six hours daily on computer, up to nine hours on weekends, leading to declined academic performance and social withdrawal. \u2014 \"My 12-year-old son spends five to six hours a day on his computer\", \"He has also stopped playing football, which he used to love, and rarely sees his friends in person anymore\", \"His grades have dropped significantly this term\"\n2. Son exhibiting aggressive behaviors when confronted about screen time, including throwing objects and physical damage to property. \u2014 \"When I try to set time limits he becomes extremely angry and once threw his controller at the wall\", \"he screamed for twenty minutes and punched a hole in his bedroom door\"\n3. Son showing signs of withdrawal and disengagement in school, including falling asleep in class and lack of interaction with peers. \u2014 \"She said he has been falling asleep in class and has not submitted homework in three weeks\", \"he seems withdrawn and does not interact with classmates during breaks\"",
        "1. Family of five navigating integration in Germany, parents working and in language course, facing cultural identity struggles. \u2014 \"We moved to Germany from Syria four years ago\", \"My husband works in a warehouse and I am currently in a language course, B1 level\"\n2. 15-year-old daughter acts as interpreter, experiencing empowerment and stress, 12-year-old son struggling in Gymnasium due to language barriers, 6-year-old daughter prefers German over Arabic. \u2014 \"My oldest daughter speaks fluent German and translates for us at doctor appointments and parent-teacher meetings\", \"My son is struggling at school because his German is not strong enough for the Gymnasium he attends\", \"My 6-year-old speaks mostly German and sometimes does not understand when we speak Arabic at home\"\n3. Children experiencing identity struggles and social conflicts, parents feeling isolated and concerned about cultural integration. \u2014 \"My daughter came home crying on Thursday. A classmate told her she would never really be German no matter how well she speaks\", \"My son refused to go to school on Friday because he is embarrassed about his accent\", \"And my youngest told me she does not want to speak Arabic because the other children in kindergarten said it sounds funny\", \"We also feel isolated \u2014 we have friendly neighbours but no close friends in the community\"",
        "1. 17-year-old son accepted apprenticeship in a city 200 kilometres away and wants to move into a shared flat. \u2014 \"My 17-year-old son was offered an apprenticeship as an electrician in a city 200 kilometres away starting in August. He wants to accept it and move into a shared flat with another apprentice\"\n\n2. Family conflict due to differing opinions on son's independence, with son accusing parents of holding him back. \u2014 \"When we told him we would prefer him to find something closer, he accused us of holding him back and not believing in him. He has been cold and distant for a week now.\"\n\n3. Client is concerned about son's ability to manage daily life tasks and health due to his mild asthma. \u2014 \"he cannot cook, and he barely manages to keep his room clean. He also has mild asthma that requires daily medication, and I am worried about who will make sure he takes it.\"",
        "1. Family with two children, 11-year-old daughter and 8-year-old son, experiencing sibling rivalry and perceived unequal treatment. \u2014 \"My daughter is academically gifted\", \"My son is more physical and creative but struggles with reading and writing\", \"my son has started saying things like you love her more and she gets everything\"\n2. 8-year-old son shows signs of dyslexia, pending formal assessment, expresses creativity through building and Lego constructions. \u2014 \"He was recently tested and shows signs of dyslexia\", \"My son actually builds the most incredible things with Lego and cardboard\"\n3. 11-year-old daughter is academically gifted, experiences tension with sibling, expresses feeling of being neglected. \u2014 \"my daughter noticed and asked why I was spending so much time with him\", \"She said it is not fair because she has to do her homework alone\""
    ],
    # Situation Summary outputs (narrative paragraph style)
    "narrative": [
        "The client is currently living in a cramped apartment with their mother, along with their two children aged 7 and 4, following a recent separation from their partner. The children are struggling with the changes, with the son experiencing bed-wetting and the daughter expressing anger and refusal to visit her father. The client, who works part-time as a nurse with a changing shift schedule, is concerned about creating a fair visitation schedule and the legal aspects of custody. The situation has escalated with an unannounced visit from the ex-partner, causing distress to the children and leaving the client feeling overwhelmed and unable to afford legal representation. The client is also experiencing sleep difficulties.",
        "The client is a single father raising his 14-year-old son, who has been refusing to attend school for the past three weeks due to reported headaches and stomach aches, with no underlying physical cause identified. The son, previously an average student with a small group of friends, is now experiencing social isolation and potential bullying, with peers making comments about his possessions and him reporting feelings of hatred from others, leading to emotional distress. The client is concerned about his son's education, his own job security due to used leave days, and potential involvement of the youth welfare office.",
        "The client is a parent who is concerned about their 16-year-old daughter, who has recently begun coming home late, using alcohol, and exhibiting behavioral changes. The daughter has been spending time with a new group of friends since her childhood best friend moved away, and she feels that her parents' boundaries are not aligned with those of her peers. The client's daughter's academic performance has declined, and she has withdrawn from her usual activities, such as her volleyball team. The client is seeking guidance on how to set appropriate boundaries without further straining their relationship with their daughter.",
        "The client is a single mother of three children, living alone with no nearby family support. She works full-time and struggles with irregular child support payments, leading to financial strain and an overwhelming workload. She experiences tension-related headaches and recent incidents of emotional outbursts, expressing guilt and concern about her parenting. Her eldest daughter is taking on excessive caregiving responsibilities, and her 8-year-old son is displaying behavioral issues at school. The client feels increasingly overwhelmed and unsure of how to address her multiple challenges, including potential job insecurity. She has sought help from local family support services but faces a long waiting period.",
        "The client, their partner, and their respective children from previous relationships are struggling to adjust to their new blended family dynamic. The client's 11-year-old son and their partner's 9-year-old daughter, who stays with them every other week, have been arguing, with the son expressing his discomfort with sharing his room and the daughter complaining to her mother about the client. This has led to tension between the client and their partner, as well as threats from the partner's ex-wife to take legal action. Recently, the son's defiance during a family dinner and the daughter's emotional outburst have further exacerbated the situation, leaving the client feeling overwhelmed and concerned about the future of their relationships with their partner and son.",
        "The client is a parent living with their spouse and 10-year-old son, currently struggling with moderate depression despite being on medication. They find it challenging to maintain daily routines and responsibilities, often struggling to get out of bed in the mornings, which has led to their spouse carrying much of the family's burden. Their main concerns include the impact of their depression on their son, who has expressed worry and guilt, and their spouse, who is feeling exhausted and resentful. The client is also grappling with the side effects of their recently adjusted medication, which is making mornings even more difficult. They have initiated a conversation with their son about their mental health and have discussed their spouse's need for support in managing their morning routine.",
        "The client, a parent of a 12-year-old boy, is concerned about their son's excessive screen time, with him spending five to six hours a day on his computer, mostly playing an online multiplayer game, and up to nine hours on weekends. His grades have significantly dropped, he has withdrawn from sports and in-person social interactions, and he reacts aggressively when his screen time is limited. The client's husband initially dismissed the situation as a phase, but has since acknowledged its seriousness. The client has spoken to the son's maths teacher, who reports that the boy falls asleep in class, has not submitted homework in three weeks, and appears withdrawn. Despite attempts to implement a structured screen time plan, the son has struggled to adhere to it, exhibiting extreme anger and even physical aggression. The family now seeks guidance on whether to pursue therapy, technology interventions, or both. The client's living situation is not explicitly mentioned, but the family unit is clearly experiencing stress and conflict due to the son's behavior.",
        "The client, a Syrian immigrant living in Germany with her husband and three children, is grappling with cultural integration and identity struggles. She is currently attending a language course, while her husband works in a warehouse. Her 15-year-old daughter, who serves as a translator, carries the burden of language brokering. The 12-year-old son is struggling with his German language skills at Gymnasium, and the 6-year-old daughter is embracing German while losing her Arabic comprehension. The family feels isolated, with no close friends in the community. Recently, all three children experienced incidents that exacerbated their feelings of not belonging, with the oldest daughter feeling caught between cultures, the son embarrassed by his accent, and the youngest rejecting the Arabic language due to peer influence. The client is concerned about preserving their cultural identity while navigating the practical needs of integration.",
        "The client, a parent of a 17-year-old son, is grappling with the decision of whether to allow their son to move out for an apprenticeship in a distant city. The client expresses concerns about their son's ability to live independently, manage his mild asthma, and maintain a clean living space. The son's desire for independence has caused tension within the family, with the client feeling unsupported by their spouse and older daughter. After a visit to the city, the client is considering allowing their son to move out, but seeks guidance on how to prepare both themselves and their son for this transition. The client's main concerns revolve around their son's health, his ability to care for himself, and the potential strain on their relationship if they refuse to let him go.",
        "The client, a married individual with two children, an 11-year-old academically gifted daughter and an 8-year-old son who shows signs of dyslexia, is struggling with perceived sibling rivalry and unequal treatment. The son expresses feelings of being loved less and has acted out by destroying his sister's artwork, while the daughter has expressed a desire to be an only child. The client and their husband spend more time assisting their daughter with advanced academic work, which the son may interpret as favoritism. The client is seeking guidance on how to address these issues and create a more balanced and equitable environment for both children, while also managing the children's differing reactions to the changes in attention."
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
                        "Analyze the email thread and produce a structured situation description of the client's current life circumstances as a numbered list of up to 3 points.\n\n"
                        "Each point must contain:\n"
                        "- A concise description of one aspect of the life situation (max 2 sentences)\n"
                        "- Direct quotes from the email thread as evidence, placed after a dash\n\n"
                        "Focus on: housing situation, family relationships, children (age, development, health), professional/educational situation, health status, social conflicts.\n\n"
                        "Rules:\n"
                        "- Use only facts from the thread, no speculation\n"
                        "- Avoid introductory phrases, present information directly\n"
                        "- When counselling parents, also include information about their children\n\n"
                        "Few-shot example:\n\n"
                        "Input: A single mother reports that her 8-year-old son has been refusing to attend school for two weeks, "
                        "complaining of stomach aches. The pediatrician found no physical cause. She works part-time and cannot stay home every day.\n\n"
                        "Output:\n"
                        '1. Single mother working part-time, unable to provide daily supervision due to work obligations. '
                        '— "I work part-time and cannot stay home every day"\n'
                        '2. 8-year-old son refusing school attendance for two weeks with psychosomatic symptoms. '
                        '— "my son has been refusing to go to school for two weeks", "he complains of stomach aches but the pediatrician found nothing"'
                    ),
                    data_text=(
                        "Subject: {{subject}}\n\n"
                        "Email thread: {{content}}\n\n"
                        "Return only the numbered list. No additional explanations."
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
                        "Write a plain text paragraph, no bullet points."
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
        model_id='Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506'
    ).first()
    gpt5_nano = LLMModel.query.filter_by(
        model_id='Global/OpenAI/gpt-5-nano'
    ).first()

    if not mistral_small or not gpt5_nano:
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
            "llm_models": [mistral_small.model_id, gpt5_nano.model_id],
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
            for model in [mistral_small, gpt5_nano]:
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
