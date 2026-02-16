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
from types import SimpleNamespace

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


# Real LLM-generated outputs from production batch run (2026-02-15)
# Keys: 'structured' = Structured Situation Analysis, 'narrative' = Live Situation Summary
# Sub-keys: 'mistral' = Mistral-Small-3.2, 'gpt5_nano' = GPT-5 Nano (via user provider)
SAMPLE_OUTPUTS = {
    # Structured Situation Analysis outputs
    'structured': {
        # Mistral Small 3.2
        'mistral': [
            '1. Parent and two children (ages 7 and 4) living in cramped conditions in grandmother\'s apartment, son experiencing bed-wetting. — "I moved out and I am currently staying with the children at my mother\'s apartment. It is very cramped [...] my son has been wetting the bed again since the move"\n2. Daughter (age 7) refusing visits with father, expressing anger, father wants weekend custody, mother works part-time with variable shifts. — "my ex-partner wants the children every weekend, but my daughter refuses to go. [...] I work part-time [...] so a fixed visitation schedule is difficult"\n3. Unannounced visit from ex-partner led to argument in front of children, daughter had emotional outburst, son anxious about father\'s presence, mother experiencing sleep issues. — "My ex showed up unannounced at my mother\'s place on Wednesday and there was an argument in front of the children. [...] My son has started asking every morning whether Daddy is coming today. I feel completely overwhelmed and I am not sleeping well"',
            '1. Single father, exhausted all leave days to care for 14-year-old son. — "I am a single father and I have already used all my remaining leave days from work to stay home with him"\n2. 14-year-old son refusing school, psychosomatic symptoms, social exclusion, possible bullying. — "my 14-year-old son has refused to go to school for the past three weeks", "he complains of headaches and stomach aches", "he has been eating lunch alone for two months", "everyone hates him and he never wants to go back"\n3. School involvement, risk of youth welfare office intervention due to 15 unexcused absences. — "His form teacher called and said he has 15 unexcused absences now", "I am worried about [...] whether the school will involve the youth welfare office"',
            '1. 16-year-old daughter returning home after midnight, exhibiting alcohol use, and engaging in heated arguments with parents about boundaries. — "My 16-year-old daughter has been coming home after midnight almost every weekend for the past month. Last Saturday she came home at 2 AM smelling of alcohol. When I confronted her, she screamed at me that I am controlling and that all her friends have more freedom."\n2. Teenage daughter experiencing a decline in academic performance and withdrawal from extracurricular activities. — "Her grades have dropped from mostly Bs to Ds this term. She also quit the volleyball team last month without telling us."\n3. Parent-child relationship strained due to perceived lack of trust and autonomy, with communication breakdown between daughter and parents. — "She said she feels like we do not trust her. She used to tell me everything, and now she barely speaks to us."',
            '1. Single mother of three children aged 10, 8, and 3, with no family nearby and unable to afford a babysitter. — "I am a single mother of three children — a 10-year-old daughter, an 8-year-old son, and a 3-year-old son", "I have no family nearby and I cannot afford a babysitter"\n\n2. Experiences tension-related headaches and has moments of losing control over her emotions. — "I have had recurring headaches for months and my doctor says it is tension-related", "Last week I shouted at my 3-year-old for spilling juice and I frightened him so badly he would not come near me for the rest of the evening"\n\n3. 10-year-old daughter takes on caregiving tasks for her younger brothers. — "My oldest daughter has started taking on tasks like making sandwiches for her brothers and I can see that it is too much responsibility for her age"',
            '1. Blended family with frequent conflicts due to children\'s adjustment issues. — "The children do not get along", "my son says he hates sharing his room when she is here", "my partner\'s daughter told her mother that I am mean to her"\n2. Strained relationship with partner due to differing opinions on parenting and family dynamics. — "my partner feels caught in the middle and we have been arguing almost every night", "my partner was hurt and said maybe the children are just not ready for this"\n3. Legal threat from ex-wife due to perceived mistreatment of her daughter. — "My partner\'s ex-wife is threatening to go back to court", "now the ex-wife has sent a formal letter through her lawyer"',
            '1. Diagnosed with moderate depression six months ago, currently on medication, and struggling with daily functioning. — "I have been diagnosed with moderate depression six months ago and I am on medication", "I struggle to get through the day", "even small tasks feel overwhelming"\n2. 10-year-old son living with client and his wife, and has expressed concern about client\'s mental health. — "I have a 10-year-old son who I raise together with my wife", "My son asked my wife last week why Daddy is always sad and whether it is his fault"\n3. Wife experiencing resentment and exhaustion from supporting client and managing household responsibilities alone. — "My wife has been incredibly patient, but I can see she is exhausted from carrying everything alone", "she admitted she has been feeling resentful and exhausted"',
            '1. 12-year-old son spends 5-9 hours daily on computer, primarily playing online multiplayer games. — "My 12-year-old son spends five to six hours a day on his computer, mostly playing an online multiplayer game. On weekends it is even more — sometimes eight or nine hours."\n2. 12-year-old son exhibits aggressive behavior and withdrawal from activities. — "When I try to set time limits he becomes extremely angry and once threw his controller at the wall", "He has also stopped playing football, which he used to love, and rarely sees his friends in person anymore."\n3. 12-year-old son experiences academic decline and withdrawal in school. — "His grades have dropped significantly this term. He went from being in the top third of his class to nearly failing mathematics and English", "he has been falling asleep in class and has not submitted homework in three weeks. She also said he seems withdrawn and does not interact with classmates during breaks."',
            '1. Family of five, parents working and in language education, living in Germany for 4 years.\n— "We moved to Germany from Syria four years ago", "My husband works in a warehouse and I am currently in a language course, B1 level"\n\n2. Children aged 15, 12, and 6 experiencing cultural identity struggles and educational challenges.\n— "My oldest daughter speaks fluent German and translates for us at doctor appointments and parent-teacher meetings", "My son is struggling at school because his German is not strong enough for the Gymnasium he attends", "My 6-year-old speaks mostly German and sometimes does not understand when we speak Arabic at home"\n\n3. Family feeling isolated with no close friends in the community, experiencing tension over language and cultural preservation.\n— "We also feel isolated — we have friendly neighbours but no close friends in the community", "My husband thinks the children should focus on German only, but I want them to keep Arabic"',
            '1. 17-year-old son offered apprenticeship 200 km away, wants to move into shared flat. — "My 17-year-old son was offered an apprenticeship as an electrician in a city 200 kilometres away", "He wants to accept it and move into a shared flat with another apprentice."\n2. Parents concerned about son\'s independence, health management, and family conflict. — "My husband and I think he is too young. He has never lived alone, he cannot cook, and he barely manages to keep his room clean. He also has mild asthma that requires daily medication", "When we told him we would prefer him to find something closer, he accused us of holding him back and not believing in him", "He has been cold and distant for a week now."\n3. Older sister supports son\'s independence, creating generational conflict. — "His older sister moved out at 21 and she thinks we are being overprotective."',
            '1. Family with two children, daughter aged 11 who is academically gifted, son aged 8 with suspected dyslexia and struggles with reading and writing. — "I have two children, a daughter aged 11 and a son aged 8", "my daughter is academically gifted — she reads constantly, gets excellent grades", "my son is more physical and creative but struggles with reading and writing"\n\n2. Sibling rivalry and perceived unequal treatment within the family, with children expressing feelings of favoritism and resentment. — "my son has started saying things like you love her more and she gets everything", "my daughter then said she wished she was an only child", "I feel like whatever I do, one of them feels hurt"\n\n3. Client and husband actively trying to address the situation by spending dedicated time with each child and recognizing their individual strengths. — "My husband and I try to be fair", "I tried dedicated time this week. I spent 30 minutes with my son building something together on Tuesday"',
        ],
        # GPT-5 Nano
        'gpt5_nano': [
            '1. Moved out and staying with the children at my mother\'s apartment; living space is cramped with the children sharing a small room. — "I moved out and I am currently staying with the children at my mother\'s apartment.", "It is very cramped — the children share a small room."\n\n2. Separation with custody tension affecting the children: daughter is 7, son is 4; daughter refuses weekend visits and is angry at her father; there was an unannounced visit and an argument in front of the children; daughter locked herself in the bathroom; son asks each morning if Daddy is coming. — "We have two children, a daughter aged 7 and a son aged 4.", "My ex-partner wants the children every weekend, but my daughter refuses to go. She says she is angry at her father.", "My ex showed up unannounced at my mother\'s place on Wednesday and there was an argument in front of the children.", "My daughter locked herself in the bathroom and would not come out for an hour.", "My son has started asking every morning whether Daddy is coming today."\n\n3. Professional/health-related strain: part-time nurse with rotating shifts; overwhelmed and not sleeping well; legal support unaffordable. — "I work part-time as a nurse and my shifts change weekly, so a fixed visitation schedule is difficult.", "I feel completely overwhelmed and I am not sleeping well.", "My mother says I should get a lawyer immediately, but I cannot afford one right now."',
            '1. 14-year-old son refuses to attend school for three weeks; reports headaches and stomach aches; pediatrician found no physical cause; 15 unexcused absences. — "I am writing because my 14-year-old son has refused to go to school for the past three weeks." "Every morning he complains of headaches and stomach aches, but our paediatrician found nothing physically wrong." "My son will not tell me what happened." "His form teacher called and said he has 15 unexcused absences now."\n\n2. Single father has used all remaining leave days from work to stay home with him; concerned about his grades and potential involvement of youth welfare office. — "I am a single father and I have already used all my remaining leave days from work to stay home with him." "I am worried about his grades and whether the school will involve the youth welfare office."\n\n3. Social conflicts and peer relationships emerging: group of boys making comments about his clothes and old phone; son feels disliked and avoids going back; has been eating lunch alone for two months. — "a group of boys in his class has been making comments about his clothes and his phone being old." "When I carefully asked my son about it tonight, he started crying and said everyone hates him and he never wants to go back." "He also said he has been eating lunch alone for two months." "I feel terrible that I did not notice earlier."',
            '1. Family relationship tensions with a 16-year-old daughter due to late nights and perceived autonomy. Communication has deteriorated. — "My 16-year-old daughter has been coming home after midnight almost every weekend for the past month.", "Last Saturday she came home at 2 AM smelling of alcohol.", "When I confronted her, she screamed at me that I am controlling and that all her friends have more freedom.", "She used to tell me everything, and now she barely speaks to us."\n\n2. Educational performance decline and withdrawal from volleyball. — "Her grades have dropped from mostly Bs to Ds this term.", "She also quit the volleyball team last month without telling us."\n\n3. Social changes and trust concerns with peers. — "She admitted that her best friend since primary school moved away in October and she has been hanging out with a new group.", "She said they think curfews are embarrassing and she does not want to be the only one who has to leave early.", "She feels like we do not trust her."',
            '1. Children and family caregiving dynamics: three children ages 10, 8, and 3; oldest daughter taking on tasks for her brothers; 8-year-old displaying behavioral issues at school; 3-year-old frightened after a shouting incident. — "I am a single mother of three children — a 10-year-old daughter, an 8-year-old son, and a 3-year-old son." — "My oldest daughter has started taking on tasks like making sandwiches for her brothers and I can see that it is too much responsibility for her age." — "In the meantime, my 8-year-old has started acting out at school — his teacher says he is pushing other children and refusing to sit still." — "Last week I shouted at my 3-year-old for spilling juice and I frightened him so badly he would not come near me for the rest of the evening."\n\n2. Health, work load, and limited social support: full-time administrative role with long evenings; recurring tension headaches; no nearby family and inability to afford babysitting; irregular child support from ex-husband; six-week waiting list for family support. — "I work full-time as an administrative assistant." — "Most evenings I do not sit down before 10 PM." — "I have had recurring headaches for months and my doctor says it is tension-related." — "I have no family nearby and I cannot afford a babysitter." — "My ex-husband moved to another city two years ago and pays child support irregularly." — "They have a six-week waiting list."\n\n3. School-related impact on work and caregiver distress: 8-year-old’s school behavior affecting daily routine; need to leave work early; employer comments on reliability; overall sense that everything is falling apart. — "In the meantime, my 8-year-old has started acting out at school — his teacher says he is pushing other children and refusing to sit still." — "I had to leave work early twice this week for calls from the school." — "My boss was understanding the first time but made a comment today about reliability." — "I feel like everything is falling apart and I do not know which problem to tackle first."',
            '1. Housing and custody arrangement in blended household: Moved in with partner six months ago; partner\'s 9-year-old daughter visits every other week; I have an 11-year-old son who lives with us full-time. — "I moved in with my new partner six months ago." — "He has a 9-year-old daughter from his previous marriage who lives with us every other week." — "I have an 11-year-old son from my first marriage who lives with us full-time."\n\n2. Interpersonal conflict among children in shared home: The children do not get along; my son resents sharing his room when she is here and calls her a guest who should go home; Last weekend my son asked if he could go live with his father instead. — "The children do not get along." — "My son says he hates sharing his room when she is here and calls her a guest who should go home." — "Last weekend my son asked if he could go live with his father instead."\n\n3. Relationship strain and legal threats surrounding the blended family: Now my partner\'s ex-wife is threatening to go back to court; the ex-wife has sent a formal letter through her lawyer; I feel like I am losing my partner and my son at the same time. — "Now my partner\'s ex-wife is threatening to go back to court." — "the ex-wife has sent a formal letter through her lawyer." — "I feel like I am losing my partner and my son at the same time."',
            '1. Moderate depression diagnosed six months ago; currently on medication and experiencing significant daily functioning difficulties, especially in mornings and on weekends. — "I have been diagnosed with moderate depression six months ago and I am on medication." "Most mornings I cannot get out of bed before my wife has already taken our son to school." "On weekends I often stay in bed until noon." "My medication was adjusted last week and the side effects make mornings even harder." "My therapist says I should try to maintain routines, but even small tasks feel overwhelming."\n\n2. Family dynamics show a supportive wife who is exhausted and requesting shared morning responsibilities; there is parental strain and social-related stress impacting the family. — "My wife has been incredibly patient, but I can see she is exhausted from carrying everything alone." "She admitted she has been feeling resentful and exhausted." "She said she needs me to at least handle the morning routine twice a week so she can go to work without rushing." "My wife and I also talked — she admitted she has been feeling resentful and exhausted." "I used to coach my son\'s football team, but I had to step down two months ago because I could not face the other parents."\n\n3. Child status: 10-year-old son; child development and emotional impact observed; son expresses support and questions about father\'s health. — "I have a 10-year-old son who I raise together with my wife." "My son asked my wife last week why Daddy is always sad and whether it is his fault." "He asked if I was going to get better and I told him honestly that I am working on it." "He hugged me and said he would help."',
            '1. 12-year-old son spends excessive time gaming (5–6 hours daily; weekends up to 8–9 hours). — "My 12-year-old son spends five to six hours a day on his computer, mostly playing an online multiplayer game. On weekends it is even more — sometimes eight or nine hours." — "When I try to set time limits he becomes extremely angry and once threw his controller at the wall."\n\n2. Academic decline and social withdrawal: grades dropped from top third to nearly failing math/English; stopped football and rarely sees friends. — "His grades have dropped significantly this term. He went from being in the top third of his class to nearly failing mathematics and English." — "He has also stopped playing football, which he used to love, and rarely sees his friends in person anymore."\n\n3. Family dynamics and management attempts: parents disagree on severity and next steps; attempts to discuss a screen time plan; consideration of therapy or technology intervention. — "My husband thinks it is just a phase, but I think it is getting out of control." — "At home, I tried to talk to him calmly about a screen time plan." — "We do not know if we need a therapist or a technology intervention or both."',
            '1. Integration challenges and cultural identity strain within the family, including language brokering by the eldest and a sense of isolation. — "My oldest daughter speaks fluent German and translates for us at doctor appointments and parent-teacher meetings." "I can see this burden is unfair to her." "We also feel isolated — we have friendly neighbours but no close friends in the community." "My husband thinks the children should focus on German only, but I want them to keep Arabic." "I worry we are losing our culture."\n\n2. Educational development and language proficiency challenges for the children. — "My son is struggling at school because his German is not strong enough for the Gymnasium he attends — his teacher suggested he move to Realschule, which feels like a failure." "My 6-year-old speaks mostly German and sometimes does not understand when we speak Arabic at home."\n\n3. Social conflicts and belonging concerns affecting the children and family. — "My daughter came home crying on Thursday. A classmate told her she would never really be German no matter how well she speaks." "She said she does not feel Syrian anymore either and does not know where she belongs." "My son refused to go to school on Friday because he is embarrassed about his accent." "And my youngest told me she does not want to speak Arabic because the other children in kindergarten said it sounds funny." "I feel like I am failing all three of my children in different ways."',
            '1. 17-year-old son offered an electrician apprenticeship in a city 200 kilometres away starting in August and wants to move into a shared flat with another apprentice. — "My 17-year-old son was offered an apprenticeship as an electrician in a city 200 kilometres away starting in August. He wants to accept it and move into a shared flat with another apprentice."\n\n2. Parents disagree about allowing the move; mother feels overprotective while father is more open, and the son has been cold and distant. — "My husband and I think he is too young." "My husband is more open to it than I am." "He has been cold and distant for a week now." "When we told him we would prefer him to find something closer, he accused us of holding him back and not believing in him."\n\n3. Health and daily-living readiness concerns: the son has mild asthma requiring daily medication and struggles with basic self-care like cooking and keeping his room clean. — "He also has mild asthma that requires daily medication, and I am worried about who will make sure he takes it." "He has never lived alone, he cannot cook, and he barely manages to keep his room clean."',
            '1. Two children: daughter aged 11 and son aged 8; parents report spending more time helping the daughter with her advanced projects and homework, while the son mostly plays outside. — "I have two children, a daughter aged 11 and a son aged 8." "we spend more time helping our daughter with her advanced projects and homework while our son mostly plays outside."\n\n2. Child development and health/education: daughter is academically gifted; son is more physical and creative but struggles with reading and writing, with signs of dyslexia awaiting formal assessment. — "My daughter is academically gifted — she reads constantly, gets excellent grades, and teachers praise her regularly." "My son is more physical and creative but struggles with reading and writing." "He was recently tested and shows signs of dyslexia, though the formal assessment is still pending."\n\n3. Social conflicts: perceived parental favoritism toward the daughter leads to sibling tension and incidents, including the son destroying his sister’s drawing and the daughter wishing to be an only child. — "The problem is that my son has started saying things like you love her more and she gets everything." "Last week he destroyed a drawing his sister made for a school project." "My daughter then said she wished she was an only child." "I realize now that our son might interpret this as favouritism."',
        ],
    },
    # Situation Summary outputs
    'narrative': {
        # Mistral Small 3.2
        'mistral': [
            "The client, a part-time nurse, recently separated from their partner and is currently living with their two children at their mother's apartment. They are facing challenges with their children's reactions to the separation, including bed-wetting and refusal to visit the ex-partner, and are seeking guidance on custody arrangements and the recent conflict that occurred when the ex-partner showed up unannounced.",
            "The client is a single father who is currently facing challenges with his 14-year-old son, who has refused to attend school for the past three weeks due to reported headaches and stomach aches, with no physical cause found by a paediatrician. The client is concerned about his son's 15 unexcused absences, potential involvement of the youth welfare office, and the underlying reason for his son's school refusal, which may be linked to social issues such as bullying or peer conflict. The client's son has been eating lunch alone for two months and has recently disclosed feelings of being hated by his peers.",
            'The client, a parent of a 16-year-old daughter, is experiencing conflicts with their daughter about boundaries. The daughter has been coming home late, exhibiting changes in behavior, and her academic performance has declined. The client is seeking guidance on how to set boundaries without pushing their daughter away, while also addressing concerns about alcohol use and a change in her social group.',
            'The client is a single mother of three children, working full-time, with an ex-husband who pays child support irregularly. She reports experiencing tension-related headaches, feelings of guilt after a verbal outburst towards her youngest son, concerns about her oldest daughter taking on too much responsibility, and a lack of nearby family support or affordable childcare. Recently, her 8-year-old son has started acting out at school, causing her to leave work early and putting her job at risk. She has contacted local family support services but faces a six-week waiting list.',
            "The client is living with their new partner, the partner's 9-year-old daughter (who stays every other week), and the client's 11-year-old son full-time. The children do not get along, leading to conflicts, and the partner's ex-wife is threatening legal action due to the daughter's complaints. The client expresses concerns about the strain on their relationship with their partner and their son, who has expressed a desire to live with his father.",
            "The client, a parent of a 10-year-old son, has been diagnosed with moderate depression for the past six months and is currently on medication. They live with their wife, who has been managing most of the household and parenting responsibilities alone. The client struggles with daily tasks, often staying in bed until noon on weekends, and has stepped down from coaching their son's football team due to feeling overwhelmed. Their main concerns include the impact of their depression on their son, who recently asked if the client's sadness was his fault, and their wife's exhaustion and resentment from carrying the burden alone. The client is unsure if they can reliably manage the morning routine twice a week as requested by their wife.",
            "The client's 12-year-old son spends excessive time on his computer, primarily playing online multiplayer games, with his screen time increasing on weekends. This has led to a decline in his academic performance, withdrawal from previously enjoyed activities, and reduced in-person social interactions, with the client expressing concern about his son's aggressive reactions to attempts to limit screen time. The client's husband initially dismissed the behavior as a phase but now acknowledges its seriousness, with the client seeking guidance on whether therapeutic intervention or technological measures, or both, are necessary.",
            "The client, a Syrian-born individual currently residing in Germany, is navigating the challenges of integration. They live with their husband, who works in a warehouse, and their three children aged 15, 12, and 6. The client is currently attending a B1 level language course and expresses concerns about their children's language and cultural identity, feeling isolated in their community. Their main concerns include the burden on their eldest daughter for translation, their son's struggles at Gymnasium, and the youngest daughter's preference for German over Arabic.",
            "The client, a parent, is concerned about their 17-year-old son's plan to move 200 kilometres away for an apprenticeship as an electrician, citing his lack of independence, mild asthma that requires daily medication, and recent strained family dynamics. The son has agreed to a structured transition, including daily video calls and bi-weekly visits home, and the parents are seeking guidance on how to prepare for this change.",
            "The client is a parent of two children, an 11-year-old daughter who is academically gifted, and an 8-year-old son who has been identified as potentially having dyslexia and exhibits physical and creative strengths. The client expresses concern about perceived favoritism, as the son has started expressing feelings of being loved less and has shown aggressive behavior towards his sister, while the daughter has expressed a desire to be an only child. The client's husband and the client spend more time assisting their daughter with her advanced academic work, which the client now realizes may be contributing to these issues.\n\nThe client's son has shown signs of dyslexia, but a formal assessment is still pending. The client is seeking guidance on managing sibling rivalry and ensuring both children feel equally valued and supported.\n\nThe client has started implementing dedicated one-on-one time with each child, which initially brought positive results for the son but also led to feelings of unfairness expressed by the daughter.",
        ],
        # GPT-5 Nano
        'gpt5_nano': [
            'The client has recently separated from their partner after five years and currently stays with the children at their mother’s apartment, in a cramped space where the children share a small room. They have a 7-year-old daughter who is angry at her father and refuses weekend visits, and a 4-year-old son who asks each morning whether Daddy is coming and has begun bed-wetting again since the move. The client works part-time as a nurse with weekly-changing shifts, feels overwhelmed and not sleeping well, and is concerned about custody and legal steps after an unannounced visit by the ex-partner that led to an argument in front of the children; they cannot currently afford a lawyer.',
            'The client is a single father who lives with his 14-year-old son. The son has refused to attend school for three weeks, reporting headaches and stomach aches; a pediatrician found no physical illness, and the son has not disclosed what happened. The father has exhausted his remaining leave from work and is worried about his son’s school engagement (15 unexcused absences), potential bullying (a group of boys commenting on clothes and an old phone), social isolation (eating lunch alone for two months), and possible involvement of the youth welfare office.',
            'The client lives with her husband and their 16-year-old daughter. The daughter has been coming home after midnight almost every weekend for the past month, most recently at 2 AM smelling of alcohol, and she used to tell them everything but now barely speaks; her grades have fallen from mostly Bs to Ds, and she quit the volleyball team last month without telling them. The mother fears how to set boundaries without making things worse, while the husband suggests taking away the phone; a recent conversation reveals the daughter moved away from her long-time best friend in October and has joined a new social group that resents curfews and feels the parents do not trust her.',
            'The client is a single mother of three children (a 10-year-old daughter, an 8-year-old son, and a 3-year-old son) who works full-time as an administrative assistant. Her ex-husband moved to another city two years ago and pays child support irregularly; she has no nearby family and cannot afford a babysitter, contributing to long evenings and a heavy workload. She reports months of tension-related headaches and burnout, including an incident where she shouted at her 3-year-old and frightened him, with her oldest taking on caregiving tasks and her 8-year-old displaying behavioral problems at school while she awaits six weeks for local family support services.',
            'The client moves in with a new partner six months ago; the partner’s 9-year-old daughter from a previous marriage lives with them every other week, while the client’s 11-year-old son from a first marriage lives with them full-time. The children do not get along, with the son resisting sharing his room and the daughter’s mother receiving reports that the client is “mean,” and the ex-wife is threatening to return to court. Tensions escalate after a recent dinner incident when the son tells the partner, “you are not my dad,” the daughter calls her mother crying, and the ex-wife sends a formal letter through her lawyer, leaving the client feeling as if they are losing both their partner and their son.',
            "The client lives with his wife and their 10-year-old son; he has a six-month history of moderate depression and is on medication. He reports difficulty getting through the day, with mornings spent in bed until his wife takes their son to school and weekends in bed until noon, and he had to step down from coaching his son's football team two months ago because he could not face the other parents. His wife is exhausted and asks him to handle the morning routine twice a week so she can go to work; he wants to help but is uncertain he can do so reliably due to medication side effects and morning difficulties, and their son asks whether he will get better, to which the client says he is working on it.",
            'A 12-year-old boy spends five to six hours daily on online gaming, with weekends reaching eight to nine hours, and he has withdrawn from football and in-person friends; his grades have fallen from the top third to near failing in math and English. When his mother tries to set time limits, he becomes extremely angry and throws a controller at the wall; he says all his friends play more and that she does not understand because she grew up without the internet. Teachers report he sleeps in class and has not submitted homework for three weeks; at home he agrees to a one-hour weekday plan if he can play freely on Saturday, but by Tuesday he breaks it, and the family remains unsure whether to pursue therapy, a technology intervention, or both.',
            'They live in Germany, having moved from Syria four years ago; the husband works in a warehouse and the wife is currently enrolled in a B1 language course. They have three children—a 15-year-old daughter who translates for medical visits and parent-teacher meetings, a 12-year-old son who struggles with German for his Gymnasium and for whom a move to Realschule is discussed, and a 6-year-old daughter who mostly speaks German but sometimes does not understand Arabic at home. They worry about losing their culture and feel isolated; in the latest update, the daughter reports a classmate telling her she will never be German, the son refuses to go to school because of his accent, and the youngest wants to stop speaking Arabic after peers mock the language, leaving the mother feeling she is failing all three children.',
            'The client is a parent of a 17-year-old who has been offered an electrician apprenticeship 200 kilometres away and wants to move into a shared flat with another apprentice. The parents worry he is too young and inexperienced—he has never lived alone, cannot cook, and barely keeps his room clean—and they are concerned about who will ensure he takes daily asthma medication; the son accuses them of holding him back, while his older sister thinks they are being overprotective. After visiting the city and the flat, the son appears more grown up and has shown planning, and the family agrees to a structured transition with daily video calls for the first month and return visits every second weekend, and they are seeking guidance on how to prepare for this.',
            'The client lives with her husband and two children: an 11-year-old daughter who is academically gifted and an 8-year-old son who struggles with reading and writing and shows signs of dyslexia pending formal assessment. The main concerns center on perceived unequal treatment and sibling rivalry, as the daughter receives more help and visible recognition while the son’s strengths go less noticed, leading to hurt feelings and statements about fairness. The family is attempting equitable parenting with dedicated one-on-one time, but the daughter sometimes questions why attention is given to her brother.',
        ],
    },
}

# Per-output metadata from real generation run
OUTPUT_METADATA = {
    'structured': {
        'mistral': [
            {'input_tokens': 886, 'output_tokens': 255, 'cost_usd': 0.000165, 'processing_time_ms': 20244},
            {'input_tokens': 889, 'output_tokens': 187, 'cost_usd': 0.000145, 'processing_time_ms': 13229},
            {'input_tokens': 879, 'output_tokens': 227, 'cost_usd': 0.000156, 'processing_time_ms': 16387},
            {'input_tokens': 935, 'output_tokens': 208, 'cost_usd': 0.000156, 'processing_time_ms': 14674},
            {'input_tokens': 916, 'output_tokens': 173, 'cost_usd': 0.000143, 'processing_time_ms': 10808},
            {'input_tokens': 962, 'output_tokens': 204, 'cost_usd': 0.000157, 'processing_time_ms': 8544},
            {'input_tokens': 968, 'output_tokens': 239, 'cost_usd': 0.000169, 'processing_time_ms': 18075},
            {'input_tokens': 1007, 'output_tokens': 241, 'cost_usd': 0.000173, 'processing_time_ms': 10316},
            {'input_tokens': 984, 'output_tokens': 217, 'cost_usd': 0.000163, 'processing_time_ms': 15763},
            {'input_tokens': 1039, 'output_tokens': 249, 'cost_usd': 0.000179, 'processing_time_ms': 16473},
        ],
        'gpt5_nano': [
            {'input_tokens': 886, 'output_tokens': 356, 'cost_usd': 0, 'processing_time_ms': 72359},
            {'input_tokens': 889, 'output_tokens': 347, 'cost_usd': 0, 'processing_time_ms': 33288},
            {'input_tokens': 879, 'output_tokens': 251, 'cost_usd': 0, 'processing_time_ms': 28224},
            {'input_tokens': 935, 'output_tokens': 511, 'cost_usd': 0, 'processing_time_ms': 51540},
            {'input_tokens': 916, 'output_tokens': 336, 'cost_usd': 0, 'processing_time_ms': 46179},
            {'input_tokens': 962, 'output_tokens': 419, 'cost_usd': 0, 'processing_time_ms': 46475},
            {'input_tokens': 968, 'output_tokens': 298, 'cost_usd': 0, 'processing_time_ms': 47809},
            {'input_tokens': 1007, 'output_tokens': 367, 'cost_usd': 0, 'processing_time_ms': 42602},
            {'input_tokens': 984, 'output_tokens': 285, 'cost_usd': 0, 'processing_time_ms': 25507},
            {'input_tokens': 1039, 'output_tokens': 343, 'cost_usd': 0, 'processing_time_ms': 59599},
        ],
    },
    'narrative': {
        'mistral': [
            {'input_tokens': 606, 'output_tokens': 103, 'cost_usd': 9.2e-05, 'processing_time_ms': 9451},
            {'input_tokens': 609, 'output_tokens': 152, 'cost_usd': 0.000107, 'processing_time_ms': 17147},
            {'input_tokens': 599, 'output_tokens': 100, 'cost_usd': 9e-05, 'processing_time_ms': 9091},
            {'input_tokens': 655, 'output_tokens': 145, 'cost_usd': 0.000109, 'processing_time_ms': 14122},
            {'input_tokens': 636, 'output_tokens': 112, 'cost_usd': 9.7e-05, 'processing_time_ms': 15421},
            {'input_tokens': 682, 'output_tokens': 185, 'cost_usd': 0.000124, 'processing_time_ms': 16823},
            {'input_tokens': 688, 'output_tokens': 157, 'cost_usd': 0.000116, 'processing_time_ms': 13967},
            {'input_tokens': 727, 'output_tokens': 142, 'cost_usd': 0.000115, 'processing_time_ms': 9447},
            {'input_tokens': 704, 'output_tokens': 106, 'cost_usd': 0.000102, 'processing_time_ms': 15227},
            {'input_tokens': 759, 'output_tokens': 259, 'cost_usd': 0.000154, 'processing_time_ms': 17399},
        ],
        'gpt5_nano': [
            {'input_tokens': 606, 'output_tokens': 171, 'cost_usd': 0, 'processing_time_ms': 22132},
            {'input_tokens': 609, 'output_tokens': 139, 'cost_usd': 0, 'processing_time_ms': 9992},
            {'input_tokens': 599, 'output_tokens': 169, 'cost_usd': 0, 'processing_time_ms': 13485},
            {'input_tokens': 655, 'output_tokens': 166, 'cost_usd': 0, 'processing_time_ms': 10829},
            {'input_tokens': 636, 'output_tokens': 176, 'cost_usd': 0, 'processing_time_ms': 8989},
            {'input_tokens': 682, 'output_tokens': 176, 'cost_usd': 0, 'processing_time_ms': 16279},
            {'input_tokens': 688, 'output_tokens': 186, 'cost_usd': 0, 'processing_time_ms': 28725},
            {'input_tokens': 727, 'output_tokens': 205, 'cost_usd': 0, 'processing_time_ms': 31836},
            {'input_tokens': 704, 'output_tokens': 189, 'cost_usd': 0, 'processing_time_ms': 15502},
            {'input_tokens': 759, 'output_tokens': 151, 'cost_usd': 0, 'processing_time_ms': 15212},
        ],
    },
}

JOB_TOTAL_TOKENS = 41162
JOB_TOTAL_COST_USD = 0.0027


def _build_live_prompt_content():
    """Build content for the live-created prompt without persisting it."""
    return {
        "blocks": {
            "System Prompt": {
                "content": (
                    "You are a counselling assistant who helps professionals extract key facts "
                    "from client communications in online psychosocial counselling."
                ),
                "position": 0
            },
            "Task Explanation": {
                "content": (
                    "Read the email thread and write a brief situation overview in 2-3 sentences. "
                    "Focus on the client's living situation, family, health, and main concerns. "
                    "Write in third person, present tense."
                ),
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}}\n\n"
                    "Email thread:\n"
                    "{{content}}\n\n"
                    "Write a plain text paragraph, no bullet points."
                ),
                "position": 2
            }
        }
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
            "System Prompt": {
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
    if not prompt_structured:
        logger.warning("Structured demo prompt not found, creating it first...")
        prompts = seed_demo_video_prompts()
        prompts_by_name = {p.name: p for p in prompts}
        prompt_structured = prompt_structured or prompts_by_name.get("Structured Situation Analysis")
        if not prompt_structured:
            logger.error("Failed to create structured demo prompt")
            return None

    # Keep Live Situation Summary as a live-only prompt (do not persist in user_prompts).
    prompt_summary = SimpleNamespace(
        name="Live Situation Summary",
        content=_build_live_prompt_content()
    )

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
        total_tokens=JOB_TOTAL_TOKENS,
        total_cost_usd=JOB_TOTAL_COST_USD,
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
            get_block_content(prompt, "System Prompt"),
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
            for model, model_key in [(mistral_small, 'mistral'), (gpt5_nano, 'gpt5_nano')]:
                output_text = SAMPLE_OUTPUTS[summary_key][model_key][case_idx]
                meta = OUTPUT_METADATA[summary_key][model_key][case_idx]

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
                    input_tokens=meta['input_tokens'],
                    output_tokens=meta['output_tokens'],
                    total_cost_usd=meta['cost_usd'],
                    processing_time_ms=meta['processing_time_ms'],
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
