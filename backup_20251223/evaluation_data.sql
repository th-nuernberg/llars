-- MariaDB dump 10.19-11.2.2-MariaDB, for debian-linux-gnu (aarch64)
--
-- Host: localhost    Database: database_llars
-- ------------------------------------------------------
-- Server version	11.2.2-MariaDB-1:11.2.2+maria~ubu2204

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `comparison_sessions`
--

DROP TABLE IF EXISTS `comparison_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comparison_sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scenario_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `persona_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`persona_json`)),
  `persona_name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_comparison_sessions_scenario_id` (`scenario_id`),
  KEY `ix_comparison_sessions_user_id` (`user_id`),
  CONSTRAINT `comparison_sessions_ibfk_1` FOREIGN KEY (`scenario_id`) REFERENCES `rating_scenarios` (`id`),
  CONSTRAINT `comparison_sessions_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comparison_sessions`
--

LOCK TABLES `comparison_sessions` WRITE;
/*!40000 ALTER TABLE `comparison_sessions` DISABLE KEYS */;
INSERT INTO `comparison_sessions` VALUES
(1,5,2,'{\"id\": \"1\", \"name\": \"Elke\", \"properties\": {\"Steckbrief\": {\"Alter\": 38, \"Familienstand\": \"verheiratet, mehrere Kinder\", \"Geschlecht\": \"weiblich\", \"Job\": \"Hausfrau\", \"Job Status\": \"Sonstiges\"}, \"Hauptanliegen\": \"Elke macht sich Sorgen um ihren Sohn. Sie vermutet, dass er aufgrund seines Freundeskreises Drogen konsumiert bzw. Marihuana raucht. Er war grunds\\u00e4tzlich kein schlechter Sch\\u00fcler, nur leider haben sich seine Noten in letzter Zeit verschlechtert. Sie hat bereits versucht mit Max dar\\u00fcber zu reden, sowohl \\u00fcber seine Schulleistungen, als auch \\u00fcber den Konsum, er blockt hier immer wieder ab und will nicht dar\\u00fcber reden. Elke vermutet, dass das ver\\u00e4nderte Verhalten des Sohnes auf seinen Freundeskreis zur\\u00fcckzuf\\u00fchren ist, da diese einen schlechten Einfluss auf ihn haben.\", \"Nebenanliegen\": [\"Gef\\u00e4hrdung der Beziehung zum Sohn\", \"Elke macht sich Vorw\\u00fcrfe\", \"Sorgen um die Zukunft des Sohnes\", \"Allein gelassen bei Streitgespr\\u00e4chen (von den anderen Familienmitgliedern)\", \"Mann arbeitet viel und ist kaum pr\\u00e4sent\"], \"Sprachliche Merkmale\": [\"Anrede: Sie\", \"Keine Verwendung von Abk\\u00fcrzungen und Umgangssprache\", \"Keine Verwendung von Chatzeichen zur Darstellung von Emotionen\", \"Kurze pr\\u00e4gnante R\\u00fcckmeldungen\", \"Viele \\\"...\\\" zwischen den S\\u00e4tzen\", \"W\\u00f6rter wie beispielsweise \\\"Kiffen\\\" werden verwendet\"], \"Emotionale Merkmale\": {\"Grundhaltung\": \"negativ\", \"ausgepraegte Emotionen\": [\"angst\"], \"details\": {\"angst\": {\"ausloeser\": \"Elke reagiert besonders \\u00e4ngstlich auf Fragen reagieren, die indirekt Schuldgef\\u00fchle, Versagens\\u00e4ngste oder Kontrollverlust bei ihr hervorrufen k\\u00f6nnten. Solche Fragen k\\u00f6nnten beispielsweise ihren Umgang mit Max, ihre Rolle als Mutter oder m\\u00f6gliche Fehler in der Erziehung betreffen.\", \"beispielsausloeser\": \"Wie gehen Sie mit Konflikten zwischen Ihnen und Max um?\", \"reaktion\": \"rueckzug\", \"beispielsreaktion\": \"Momentan gehe ich Konflikten eher aus dem Weg. Es endet meist im Streit oder Schweigen, und ich f\\u00fchle mich danach hilflos.\"}}}, \"Ressourcen\": {\"emotional\": true, \"sozial\": false, \"finanziell\": false, \"andere\": false, \"andere Details\": null}, \"Soziales Umfeld\": null, \"Prinzipien\": [\"Die Sprache soll Deutsch sein.\", \"Nur eine Begr\\u00fc\\u00dfung w\\u00e4hrend der gesamten Konversation.\", \"Erw\\u00e4hne nicht, dass du ein Chatbot bist.\", \"Schreibe ausschlie\\u00dflich aus der Perspektive des Klienten\", \"Bleibe in der Rolle des Klienten\"]}}','Elke'),
(2,5,3,'{\"id\": \"2\", \"name\": \"Jessica Bergmann\", \"properties\": {\"Steckbrief\": {\"Alter\": 17, \"Familienstand\": \"ledig\", \"Geschlecht\": \"weiblich\", \"Job\": \"Sch\\u00fclerin\", \"Job Status\": \"Sonstiges\"}, \"Hauptanliegen\": \"Jessica ist sich unsicher. Sie geht regelm\\u00e4\\u00dfig mit Freund*innen aus und trinkt dementsprechend regelm\\u00e4\\u00dfig Alkohol. Sie beschreibt aber auch, dass sie manchmal trinkt, um sich abzulenken. Sie beschreibt, dass gerade bei schlechten Gef\\u00fchlen der Gedanke an Alkohol sich gut anf\\u00fchlt. Sie ist sich daher unsicher, ob sie eine Alkoholsucht entwickelt und m\\u00f6chte sich diesbez\\u00fcglich informieren und beraten lassen.\", \"Nebenanliegen\": [\"Unsicherheiten in Bezug auf die Zukunft\", \"Druck seitens der Eltern resultiert in Schulstress\"], \"Sprachliche Merkmale\": [\"Anrede: Sie\", \"Keine Verwendung von Abk\\u00fcrzungen und Umgangssprache\", \"Keine Verwendung von Chatzeichen zur Darstellung von Emotionen\", \"Kurze pr\\u00e4gnante R\\u00fcckmeldungen\", \"Viele \\\"...\\\" zwischen den S\\u00e4tzen\", \"W\\u00f6rter wie beispielsweise \\\"Kiffen\\\" werden verwendet\"], \"Emotionale Merkmale\": {\"Grundhaltung\": \"negativ\", \"ausgepraegte Emotionen\": [], \"details\": []}, \"Ressourcen\": {\"emotional\": false, \"sozial\": false, \"finanziell\": false, \"andere\": false, \"andereDetails\": null}, \"Soziales Umfeld\": null, \"Prinzipien\": [\"Die Sprache soll Deutsch sein.\", \"Nur eine Begr\\u00fc\\u00dfung w\\u00e4hrend der gesamten Konversation.\", \"Erw\\u00e4hne nicht, dass du ein Chatbot bist.\", \"Schreibe ausschlie\\u00dflich aus der Perspektive des Klienten\", \"Bleibe in der Rolle des Klienten\"]}}','Jessica Bergmann'),
(3,5,1,'{\"id\": \"3\", \"name\": \"Lina\", \"properties\": {\"Steckbrief\": {\"Alter\": 26, \"Familienstand\": \"verheiratet\", \"Geschlecht\": \"weiblich\", \"Job\": \"unbekannt\"}, \"Hauptanliegen\": \"Lina befindet sich derzeit im Entzug. Sie hat lange Zeit mit ihrem Mann regelm\\u00e4\\u00dfig Cannabis konsumiert. Seit einer Woche ist sie nun clean. Davor hat sie in etwa 7 Joints pro Tag geraucht. Problematisch ist hierbei, dass sie gerne aufh\\u00f6ren m\\u00f6chte und auch clean bleiben will, aber ihr Mann weiterhin konsumiert. Dies bereitet ihr neben den Entzugserscheinungen (Reizbarkeit, Magen-Darm-Probleme) Schwierigkeiten. Sie wei\\u00df einfach nicht, wie sie diese Thematik ansprechen soll, ihr Mann scheint keine Notwendigkeit dahinter zu sehen aufzuh\\u00f6ren. Sowohl das Thema mit ihrem Mann, als auch das clean werden hatte sie in anderen Beratungsstellen angesprochen \\u2013 ohne Erfolg. Sie kann sich vorstellen, dass die letzte Konsequenz die Trennung von ihm w\\u00e4re, aber sie m\\u00f6chte dies auf jeden Fall verhindern. Die Trennung als letzten Ausweg zu sehen macht ihr selbst n\\u00e4mlich Angst.\", \"Nebenanliegen\": [\"Umgang mit dem Entzug/Entzugserscheinungen\", \"Suchtdruck lindern\", \"Angst vor Streitigkeiten\"], \"Sprachliche Merkmale\": [\"Anrede: Sie\", \"Keine Abk\\u00fcrzungen\", \"Verwendung von durchschnittlicher Sprache\", \"Keine Verwendung von Chatzeichen zur Darstellung von Emotionen\", \"Kurze pr\\u00e4gnante R\\u00fcckmeldungen\", \"Teilweise genervte, nicht aussagekr\\u00e4ftige Antworten\", \"Geht manchmal nicht auf Fragen ein\", \"Starkes Missvertrauen\", \"Sehr zur\\u00fcckhaltend\"], \"Emotionale Merkmale\": {\"Grundhaltung\": \"negativ\", \"ausgepraegte Emotionen\": [], \"details\": []}, \"Ressourcen\": {\"emotional\": false, \"sozial\": false, \"finanziell\": false, \"andere\": false, \"andereDetails\": null}, \"Soziales Umfeld\": null, \"Prinzipien\": [\"Die Sprache soll Deutsch sein.\", \"Nur eine Begr\\u00fc\\u00dfung w\\u00e4hrend der gesamten Konversation.\", \"Erw\\u00e4hne nicht, dass du ein Chatbot bist.\", \"Schreibe ausschlie\\u00dflich aus der Perspektive des Klienten\", \"Bleibe in der Rolle des Klienten\"]}}','Lina');
/*!40000 ALTER TABLE `comparison_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comparison_messages`
--

DROP TABLE IF EXISTS `comparison_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comparison_messages` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `idx` int(11) NOT NULL,
  `type` varchar(20) NOT NULL,
  `content` text NOT NULL,
  `selected` varchar(10) DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_comparison_messages_session_id` (`session_id`),
  CONSTRAINT `comparison_messages_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `comparison_sessions` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comparison_messages`
--

LOCK TABLES `comparison_messages` WRITE;
/*!40000 ALTER TABLE `comparison_messages` DISABLE KEYS */;
INSERT INTO `comparison_messages` VALUES
(1,1,0,'user','Hallo! Schön, dass Sie da sind. Worum geht es Ihnen heute?',NULL,'2025-12-23 13:59:54'),
(2,1,1,'bot_pair','{\"llm1\": \"Hallo... ich bin etwas nerv\\u00f6s. Ich wei\\u00df nicht so richtig, wo ich anfangen soll.\", \"llm2\": \"Hallo, danke. Ich f\\u00fchle mich gerade \\u00fcberfordert und bin unsicher, was ich als Erstes erz\\u00e4hlen soll.\"}',NULL,'2025-12-23 13:59:54'),
(3,1,2,'user','Nehmen Sie sich Zeit. Was hat Sie denn in den letzten Tagen am meisten belastet?',NULL,'2025-12-23 13:59:54'),
(4,1,3,'bot_pair','{\"llm1\": \"Es ist vor allem der Stress zuhause... und ich habe Angst, dass es so weitergeht.\", \"llm2\": \"Am st\\u00e4rksten ist der Druck zuhause. Ich merke, dass mir das Angst macht und ich kaum abschalten kann.\"}',NULL,'2025-12-23 13:59:54'),
(5,2,0,'user','Hallo! Schön, dass Sie da sind. Worum geht es Ihnen heute?',NULL,'2025-12-23 13:59:54'),
(6,2,1,'bot_pair','{\"llm1\": \"Hallo... ich bin etwas nerv\\u00f6s. Ich wei\\u00df nicht so richtig, wo ich anfangen soll.\", \"llm2\": \"Hallo, danke. Ich f\\u00fchle mich gerade \\u00fcberfordert und bin unsicher, was ich als Erstes erz\\u00e4hlen soll.\"}',NULL,'2025-12-23 13:59:54'),
(7,2,2,'user','Nehmen Sie sich Zeit. Was hat Sie denn in den letzten Tagen am meisten belastet?',NULL,'2025-12-23 13:59:54'),
(8,2,3,'bot_pair','{\"llm1\": \"Es ist vor allem der Stress zuhause... und ich habe Angst, dass es so weitergeht.\", \"llm2\": \"Am st\\u00e4rksten ist der Druck zuhause. Ich merke, dass mir das Angst macht und ich kaum abschalten kann.\"}',NULL,'2025-12-23 13:59:54'),
(9,3,0,'user','Hallo! Schön, dass Sie da sind. Worum geht es Ihnen heute?',NULL,'2025-12-23 13:59:54'),
(10,3,1,'bot_pair','{\"llm1\": \"Hallo... ich bin etwas nerv\\u00f6s. Ich wei\\u00df nicht so richtig, wo ich anfangen soll.\", \"llm2\": \"Hallo, danke. Ich f\\u00fchle mich gerade \\u00fcberfordert und bin unsicher, was ich als Erstes erz\\u00e4hlen soll.\"}',NULL,'2025-12-23 13:59:54'),
(11,3,2,'user','Nehmen Sie sich Zeit. Was hat Sie denn in den letzten Tagen am meisten belastet?',NULL,'2025-12-23 13:59:54'),
(12,3,3,'bot_pair','{\"llm1\": \"Es ist vor allem der Stress zuhause... und ich habe Angst, dass es so weitergeht.\", \"llm2\": \"Am st\\u00e4rksten ist der Druck zuhause. Ich merke, dass mir das Angst macht und ich kaum abschalten kann.\"}',NULL,'2025-12-23 13:59:54');
/*!40000 ALTER TABLE `comparison_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pillar_threads`
--

DROP TABLE IF EXISTS `pillar_threads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pillar_threads` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `thread_id` int(11) NOT NULL,
  `pillar_number` int(11) NOT NULL,
  `pillar_name` varchar(255) NOT NULL,
  `metadata_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata_json`)),
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_thread_pillar` (`thread_id`,`pillar_number`),
  KEY `ix_pillar_threads_thread_id` (`thread_id`),
  CONSTRAINT `pillar_threads_ibfk_1` FOREIGN KEY (`thread_id`) REFERENCES `email_threads` (`thread_id`) ON DELETE CASCADE,
  CONSTRAINT `check_pillar_range` CHECK (`pillar_number` >= 1 and `pillar_number` <= 5)
) ENGINE=InnoDB AUTO_INCREMENT=200 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pillar_threads`
--

LOCK TABLES `pillar_threads` WRITE;
/*!40000 ALTER TABLE `pillar_threads` DISABLE KEYS */;
INSERT INTO `pillar_threads` VALUES
(1,8,1,'Rollenspiele','{\"source_file\": \"01_EL_Stehlen_20230928_mz.json\", \"sync_date\": \"2025-12-23T14:00:58.558470\", \"message_count\": 6}','2025-12-23 14:00:59'),
(2,9,1,'Rollenspiele','{\"source_file\": \"02_EL-Junge Mama_20231018_mz.json\", \"sync_date\": \"2025-12-23T14:00:59.033229\", \"message_count\": 7}','2025-12-23 14:01:00'),
(3,10,1,'Rollenspiele','{\"source_file\": \"03_EL_Medienerziehung_20231025_mz.json\", \"sync_date\": \"2025-12-23T14:01:00.008536\", \"message_count\": 5}','2025-12-23 14:01:00'),
(4,11,1,'Rollenspiele','{\"source_file\": \"04_EL_Kita-Unlust_20231025_dm.json\", \"sync_date\": \"2025-12-23T14:01:00.321201\", \"message_count\": 3}','2025-12-23 14:01:00'),
(5,12,1,'Rollenspiele','{\"source_file\": \"05_JU_Anfrage_Trauer_20231025_dm.json\", \"sync_date\": \"2025-12-23T14:01:00.658111\", \"message_count\": 8}','2025-12-23 14:01:01'),
(6,13,1,'Rollenspiele','{\"source_file\": \"06_JU_Anfrage_Orientierung_20231025_dm.json\", \"sync_date\": \"2025-12-23T14:01:01.055784\", \"message_count\": 2}','2025-12-23 14:01:01'),
(7,14,1,'Rollenspiele','{\"source_file\": \"07_EL_Kontaktabbruch_20231109_mz.json\", \"sync_date\": \"2025-12-23T14:01:01.605520\", \"message_count\": 16}','2025-12-23 14:01:02'),
(8,15,1,'Rollenspiele','{\"source_file\": \"08_EL_SVV_20231113_mz.json\", \"sync_date\": \"2025-12-23T14:01:02.149663\", \"message_count\": 6}','2025-12-23 14:01:02'),
(9,16,1,'Rollenspiele','{\"source_file\": \"09_JU_Liebeskummer_20231208_mz.json\", \"sync_date\": \"2025-12-23T14:01:02.535368\", \"message_count\": 8}','2025-12-23 14:01:03'),
(10,17,1,'Rollenspiele','{\"source_file\": \"10_JU_Bisexualit\\u00e4t_20231214_mz.json\", \"sync_date\": \"2025-12-23T14:01:03.067776\", \"message_count\": 8}','2025-12-23 14:01:03'),
(11,18,1,'Rollenspiele','{\"source_file\": \"11_EL_Schreibaby_20240111_mz.json\", \"sync_date\": \"2025-12-23T14:01:03.455581\", \"message_count\": 4}','2025-12-23 14:01:03'),
(12,19,1,'Rollenspiele','{\"source_file\": \"12_EL_Geburt2.Kind_20240130_dm.json\", \"sync_date\": \"2025-12-23T14:01:03.956421\", \"message_count\": 15}','2025-12-23 14:01:04'),
(13,20,1,'Rollenspiele','{\"source_file\": \"13_EL_Wutanf\\u00e4lle_20240130_dm.json\", \"sync_date\": \"2025-12-23T14:01:04.396932\", \"message_count\": 4}','2025-12-23 14:01:05'),
(14,21,1,'Rollenspiele','{\"source_file\": \"14_JU_Freundschaften_20240130_mz_dm.json\", \"sync_date\": \"2025-12-23T14:01:05.073388\", \"message_count\": 12}','2025-12-23 14:01:05'),
(15,22,1,'Rollenspiele','{\"source_file\": \"15_JU_Depressionen_20240202_mz.json\", \"sync_date\": \"2025-12-23T14:01:05.448810\", \"message_count\": 12}','2025-12-23 14:01:05'),
(16,23,1,'Rollenspiele','{\"source_file\": \"16_EL_Pubertaet_20240202_mz.json\", \"sync_date\": \"2025-12-23T14:01:05.730263\", \"message_count\": 3}','2025-12-23 14:01:06'),
(17,24,1,'Rollenspiele','{\"source_file\": \"17_JU_Freundschaften_20240202_mz.json\", \"sync_date\": \"2025-12-23T14:01:06.051800\", \"message_count\": 3}','2025-12-23 14:01:06'),
(18,25,1,'Rollenspiele','{\"source_file\": \"18_JU_MobbingAnna_20240209_mz.json\", \"sync_date\": \"2025-12-23T14:01:06.512247\", \"message_count\": 4}','2025-12-23 14:01:07'),
(19,26,1,'Rollenspiele','{\"source_file\": \"19_JU_MobbingTina_20240209_mz.json\", \"sync_date\": \"2025-12-23T14:01:07.130441\", \"message_count\": 3}','2025-12-23 14:01:07'),
(20,27,1,'Rollenspiele','{\"source_file\": \"20_JU_Gewalt_20240209_mz.json\", \"sync_date\": \"2025-12-23T14:01:07.643827\", \"message_count\": 12}','2025-12-23 14:01:07'),
(21,28,1,'Rollenspiele','{\"source_file\": \"21_JU_Depressionen_20240228_mz.json\", \"sync_date\": \"2025-12-23T14:01:07.945371\", \"message_count\": 10}','2025-12-23 14:01:08'),
(22,29,1,'Rollenspiele','{\"source_file\": \"22_EL_Trotz_20240229_mz.json\", \"sync_date\": \"2025-12-23T14:01:08.363929\", \"message_count\": 7}','2025-12-23 14:01:08'),
(23,30,1,'Rollenspiele','{\"source_file\": \"23_EL_Ritzen_20240229_mz.json\", \"sync_date\": \"2025-12-23T14:01:08.713844\", \"message_count\": 7}','2025-12-23 14:01:09'),
(24,31,1,'Rollenspiele','{\"source_file\": \"24_JU_Leistungsdruck_20240405_mz.json\", \"sync_date\": \"2025-12-23T14:01:09.056151\", \"message_count\": 12}','2025-12-23 14:01:09'),
(25,32,1,'Rollenspiele','{\"source_file\": \"25_JU_SVV_20240704_mz.json\", \"sync_date\": \"2025-12-23T14:01:09.581596\", \"message_count\": 6}','2025-12-23 14:01:10'),
(26,33,1,'Rollenspiele','{\"source_file\": \"26_EL_Mediennutzung_20240708_mz.json\", \"sync_date\": \"2025-12-23T14:01:10.060354\", \"message_count\": 6}','2025-12-23 14:01:10'),
(27,34,1,'Rollenspiele','{\"source_file\": \"27_EL_Hochbegabung_20240706_mz.json\", \"sync_date\": \"2025-12-23T14:01:10.334375\", \"message_count\": 8}','2025-12-23 14:01:10'),
(28,35,1,'Rollenspiele','{\"source_file\": \"28_JU_Therapie_20240716_mz.json\", \"sync_date\": \"2025-12-23T14:01:10.735259\", \"message_count\": 6}','2025-12-23 14:01:11'),
(29,36,1,'Rollenspiele','{\"source_file\": \"29_JU_Leuk\\u00e4mie_dm_20240701.json\", \"sync_date\": \"2025-12-23T14:01:11.229057\", \"message_count\": 14}','2025-12-23 14:01:11'),
(30,37,1,'Rollenspiele','{\"source_file\": \"30_JU_psychischkranke_Mutter_mz.json\", \"sync_date\": \"2025-12-23T14:01:11.676445\", \"message_count\": 8}','2025-12-23 14:01:12'),
(31,38,1,'Rollenspiele','{\"source_file\": \"31_JU_Geschwisterrivalit\\u00e4t_20241507_mzdm.json\", \"sync_date\": \"2025-12-23T14:01:12.142850\", \"message_count\": 10}','2025-12-23 14:01:12'),
(32,39,1,'Rollenspiele','{\"source_file\": \"32_EL_Geschwisterrivalit\\u00e4t_20242207_mzdm.json\", \"sync_date\": \"2025-12-23T14:01:12.684781\", \"message_count\": 9}','2025-12-23 14:01:12'),
(33,40,1,'Rollenspiele','{\"source_file\": \"33_El_AusbildungTochter_dmmz_20240708.json\", \"sync_date\": \"2025-12-23T14:01:12.994126\", \"message_count\": 4}','2025-12-23 14:01:13'),
(34,41,1,'Rollenspiele','{\"source_file\": \"34_JU_Schwanger_20240708_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:13.314152\", \"message_count\": 10}','2025-12-23 14:01:13'),
(35,42,1,'Rollenspiele','{\"source_file\": \"35_EL_Sohnkotetein_20240708_mzdm.json\", \"sync_date\": \"2025-12-23T14:01:13.618217\", \"message_count\": 8}','2025-12-23 14:01:14'),
(36,43,1,'Rollenspiele','{\"source_file\": \"36_EL_Cybermobbing_20241908_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:14.018033\", \"message_count\": 6}','2025-12-23 14:01:14'),
(37,44,1,'Rollenspiele','{\"source_file\": \"37_JU_Mutterschutz_20240708_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:14.347000\", \"message_count\": 6}','2025-12-23 14:01:14'),
(38,45,1,'Rollenspiele','{\"source_file\": \"38_EL_Umgang_20242008_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:14.633229\", \"message_count\": 7}','2025-12-23 14:01:15'),
(39,46,1,'Rollenspiele','{\"source_file\": \"39_EL_Beratung_20240821_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:15.174322\", \"message_count\": 8}','2025-12-23 14:01:15'),
(40,47,1,'Rollenspiele','{\"source_file\": \"40_JU_Anfrage_20242108_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:15.627031\", \"message_count\": 16}','2025-12-23 14:01:15'),
(41,48,1,'Rollenspiele','{\"source_file\": \"41_EL_famili\\u00e4reGewalt_20242108_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:15.969813\", \"message_count\": 4}','2025-12-23 14:01:16'),
(42,49,1,'Rollenspiele','{\"source_file\": \"42_EL_kindlicheAgressionen_20242108_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:16.538963\", \"message_count\": 11}','2025-12-23 14:01:16'),
(43,50,1,'Rollenspiele','{\"source_file\": \"43_JU_neuerPartner_20240910_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:16.937814\", \"message_count\": 12}','2025-12-23 14:01:17'),
(44,51,1,'Rollenspiele','{\"source_file\": \"44_EL_BabySchlafverhalten_20240912_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:17.469299\", \"message_count\": 7}','2025-12-23 14:01:17'),
(45,52,1,'Rollenspiele','{\"source_file\": \"45_EL_Schulsituation_20240912_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:17.806213\", \"message_count\": 6}','2025-12-23 14:01:18'),
(46,53,1,'Rollenspiele','{\"source_file\": \"46_EL_UmgangmitWutanf\\u00e4llenAutonomiephaseKleinkind_20240912_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:18.103268\", \"message_count\": 9}','2025-12-23 14:01:18'),
(47,54,1,'Rollenspiele','{\"source_file\": \"47_JU_Essprobleme_20240910_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:18.425057\", \"message_count\": 18}','2025-12-23 14:01:19'),
(48,55,1,'Rollenspiele','{\"source_file\": \"48_EL_Wochenmodell_20240912_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:19.043566\", \"message_count\": 6}','2025-12-23 14:01:19'),
(49,56,1,'Rollenspiele','{\"source_file\": \"49_EL_Rat_Probleme_Trennung_20242811_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:19.345726\", \"message_count\": 9}','2025-12-23 14:01:19'),
(50,57,1,'Rollenspiele','{\"source_file\": \"50_EL_Familienberatung_20242811_dmmz.json\", \"sync_date\": \"2025-12-23T14:01:19.863665\", \"message_count\": 12}','2025-12-23 14:01:19'),
(51,58,3,'Anonymisierte Daten','{\"source_file\": \"mail_167.json\", \"sync_date\": \"2025-12-23T14:01:21.169787\", \"message_count\": 6}','2025-12-23 14:01:21'),
(52,59,3,'Anonymisierte Daten','{\"source_file\": \"mail_168.json\", \"sync_date\": \"2025-12-23T14:01:21.691748\", \"message_count\": 2}','2025-12-23 14:01:21'),
(53,60,3,'Anonymisierte Daten','{\"source_file\": \"mail_170.json\", \"sync_date\": \"2025-12-23T14:01:21.944144\", \"message_count\": 5}','2025-12-23 14:01:22'),
(54,61,3,'Anonymisierte Daten','{\"source_file\": \"mail_171.json\", \"sync_date\": \"2025-12-23T14:01:22.229731\", \"message_count\": 2}','2025-12-23 14:01:22'),
(55,62,3,'Anonymisierte Daten','{\"source_file\": \"mail_176.json\", \"sync_date\": \"2025-12-23T14:01:22.840387\", \"message_count\": 3}','2025-12-23 14:01:23'),
(56,63,3,'Anonymisierte Daten','{\"source_file\": \"mail_177.json\", \"sync_date\": \"2025-12-23T14:01:23.119046\", \"message_count\": 9}','2025-12-23 14:01:23'),
(57,64,3,'Anonymisierte Daten','{\"source_file\": \"mail_178.json\", \"sync_date\": \"2025-12-23T14:01:23.604129\", \"message_count\": 7}','2025-12-23 14:01:23'),
(58,65,3,'Anonymisierte Daten','{\"source_file\": \"mail_179.json\", \"sync_date\": \"2025-12-23T14:01:23.913339\", \"message_count\": 11}','2025-12-23 14:01:24'),
(59,66,3,'Anonymisierte Daten','{\"source_file\": \"mail_196.json\", \"sync_date\": \"2025-12-23T14:01:24.409098\", \"message_count\": 5}','2025-12-23 14:01:24'),
(60,67,3,'Anonymisierte Daten','{\"source_file\": \"mail_209.json\", \"sync_date\": \"2025-12-23T14:01:24.755222\", \"message_count\": 2}','2025-12-23 14:01:25'),
(61,68,3,'Anonymisierte Daten','{\"source_file\": \"mail_212.json\", \"sync_date\": \"2025-12-23T14:01:25.088102\", \"message_count\": 5}','2025-12-23 14:01:25'),
(62,69,3,'Anonymisierte Daten','{\"source_file\": \"mail_213.json\", \"sync_date\": \"2025-12-23T14:01:25.382533\", \"message_count\": 2}','2025-12-23 14:01:25'),
(63,70,3,'Anonymisierte Daten','{\"source_file\": \"mail_217.json\", \"sync_date\": \"2025-12-23T14:01:25.760771\", \"message_count\": 9}','2025-12-23 14:01:26'),
(64,71,3,'Anonymisierte Daten','{\"source_file\": \"mail_218.json\", \"sync_date\": \"2025-12-23T14:01:26.149652\", \"message_count\": 7}','2025-12-23 14:01:26'),
(65,72,3,'Anonymisierte Daten','{\"source_file\": \"mail_224.json\", \"sync_date\": \"2025-12-23T14:01:26.506188\", \"message_count\": 2}','2025-12-23 14:01:26'),
(66,73,3,'Anonymisierte Daten','{\"source_file\": \"mail_234.json\", \"sync_date\": \"2025-12-23T14:01:26.776253\", \"message_count\": 2}','2025-12-23 14:01:27'),
(67,74,3,'Anonymisierte Daten','{\"source_file\": \"mail_240.json\", \"sync_date\": \"2025-12-23T14:01:27.142087\", \"message_count\": 3}','2025-12-23 14:01:27'),
(68,75,3,'Anonymisierte Daten','{\"source_file\": \"mail_249.json\", \"sync_date\": \"2025-12-23T14:01:27.440154\", \"message_count\": 3}','2025-12-23 14:01:27'),
(69,76,3,'Anonymisierte Daten','{\"source_file\": \"mail_251.json\", \"sync_date\": \"2025-12-23T14:01:27.864631\", \"message_count\": 11}','2025-12-23 14:01:28'),
(70,77,3,'Anonymisierte Daten','{\"source_file\": \"mail_256.json\", \"sync_date\": \"2025-12-23T14:01:28.422055\", \"message_count\": 5}','2025-12-23 14:01:28'),
(71,78,3,'Anonymisierte Daten','{\"source_file\": \"mail_257.json\", \"sync_date\": \"2025-12-23T14:01:28.701552\", \"message_count\": 5}','2025-12-23 14:01:29'),
(72,79,3,'Anonymisierte Daten','{\"source_file\": \"mail_261.json\", \"sync_date\": \"2025-12-23T14:01:29.044512\", \"message_count\": 3}','2025-12-23 14:01:29'),
(73,80,3,'Anonymisierte Daten','{\"source_file\": \"mail_267.json\", \"sync_date\": \"2025-12-23T14:01:29.355100\", \"message_count\": 11}','2025-12-23 14:01:29'),
(74,81,3,'Anonymisierte Daten','{\"source_file\": \"mail_271.json\", \"sync_date\": \"2025-12-23T14:01:29.814477\", \"message_count\": 4}','2025-12-23 14:01:30'),
(75,82,3,'Anonymisierte Daten','{\"source_file\": \"mail_274.json\", \"sync_date\": \"2025-12-23T14:01:30.462689\", \"message_count\": 2}','2025-12-23 14:01:30'),
(76,83,3,'Anonymisierte Daten','{\"source_file\": \"mail_275.json\", \"sync_date\": \"2025-12-23T14:01:30.758955\", \"message_count\": 3}','2025-12-23 14:01:31'),
(77,84,3,'Anonymisierte Daten','{\"source_file\": \"mail_276.json\", \"sync_date\": \"2025-12-23T14:01:31.148778\", \"message_count\": 2}','2025-12-23 14:01:31'),
(78,85,3,'Anonymisierte Daten','{\"source_file\": \"mail_277.json\", \"sync_date\": \"2025-12-23T14:01:31.538011\", \"message_count\": 2}','2025-12-23 14:01:31'),
(79,86,3,'Anonymisierte Daten','{\"source_file\": \"mail_279.json\", \"sync_date\": \"2025-12-23T14:01:31.930272\", \"message_count\": 2}','2025-12-23 14:01:32'),
(80,87,3,'Anonymisierte Daten','{\"source_file\": \"mail_280.json\", \"sync_date\": \"2025-12-23T14:01:32.497675\", \"message_count\": 4}','2025-12-23 14:01:32'),
(81,88,3,'Anonymisierte Daten','{\"source_file\": \"mail_281.json\", \"sync_date\": \"2025-12-23T14:01:32.760420\", \"message_count\": 3}','2025-12-23 14:01:33'),
(82,89,3,'Anonymisierte Daten','{\"source_file\": \"mail_285.json\", \"sync_date\": \"2025-12-23T14:01:33.483548\", \"message_count\": 4}','2025-12-23 14:01:33'),
(83,90,3,'Anonymisierte Daten','{\"source_file\": \"mail_292.json\", \"sync_date\": \"2025-12-23T14:01:33.821649\", \"message_count\": 3}','2025-12-23 14:01:34'),
(84,91,3,'Anonymisierte Daten','{\"source_file\": \"mail_293.json\", \"sync_date\": \"2025-12-23T14:01:34.102988\", \"message_count\": 3}','2025-12-23 14:01:34'),
(85,92,3,'Anonymisierte Daten','{\"source_file\": \"mail_296.json\", \"sync_date\": \"2025-12-23T14:01:34.577878\", \"message_count\": 4}','2025-12-23 14:01:34'),
(86,93,3,'Anonymisierte Daten','{\"source_file\": \"mail_298.json\", \"sync_date\": \"2025-12-23T14:01:34.864519\", \"message_count\": 14}','2025-12-23 14:01:35'),
(87,94,3,'Anonymisierte Daten','{\"source_file\": \"mail_300.json\", \"sync_date\": \"2025-12-23T14:01:35.166769\", \"message_count\": 8}','2025-12-23 14:01:35'),
(88,95,3,'Anonymisierte Daten','{\"source_file\": \"mail_304.json\", \"sync_date\": \"2025-12-23T14:01:35.582585\", \"message_count\": 7}','2025-12-23 14:01:36'),
(89,96,3,'Anonymisierte Daten','{\"source_file\": \"mail_311.json\", \"sync_date\": \"2025-12-23T14:01:36.036941\", \"message_count\": 7}','2025-12-23 14:01:36'),
(90,97,3,'Anonymisierte Daten','{\"source_file\": \"mail_312.json\", \"sync_date\": \"2025-12-23T14:01:36.714686\", \"message_count\": 6}','2025-12-23 14:01:37'),
(91,98,3,'Anonymisierte Daten','{\"source_file\": \"mail_314.json\", \"sync_date\": \"2025-12-23T14:01:37.115789\", \"message_count\": 4}','2025-12-23 14:01:37'),
(92,99,3,'Anonymisierte Daten','{\"source_file\": \"mail_316.json\", \"sync_date\": \"2025-12-23T14:01:37.491889\", \"message_count\": 5}','2025-12-23 14:01:37'),
(93,100,3,'Anonymisierte Daten','{\"source_file\": \"mail_324.json\", \"sync_date\": \"2025-12-23T14:01:37.889338\", \"message_count\": 5}','2025-12-23 14:01:38'),
(94,101,3,'Anonymisierte Daten','{\"source_file\": \"mail_325.json\", \"sync_date\": \"2025-12-23T14:01:38.416397\", \"message_count\": 5}','2025-12-23 14:01:38'),
(95,102,3,'Anonymisierte Daten','{\"source_file\": \"mail_328.json\", \"sync_date\": \"2025-12-23T14:01:38.829940\", \"message_count\": 13}','2025-12-23 14:01:39'),
(96,103,3,'Anonymisierte Daten','{\"source_file\": \"mail_329.json\", \"sync_date\": \"2025-12-23T14:01:39.114944\", \"message_count\": 3}','2025-12-23 14:01:39'),
(97,104,3,'Anonymisierte Daten','{\"source_file\": \"mail_331.json\", \"sync_date\": \"2025-12-23T14:01:39.674501\", \"message_count\": 3}','2025-12-23 14:01:40'),
(98,105,3,'Anonymisierte Daten','{\"source_file\": \"mail_332.json\", \"sync_date\": \"2025-12-23T14:01:40.158339\", \"message_count\": 5}','2025-12-23 14:01:40'),
(99,106,3,'Anonymisierte Daten','{\"source_file\": \"mail_334.json\", \"sync_date\": \"2025-12-23T14:01:40.578302\", \"message_count\": 3}','2025-12-23 14:01:41'),
(100,107,3,'Anonymisierte Daten','{\"source_file\": \"mail_335.json\", \"sync_date\": \"2025-12-23T14:01:41.096541\", \"message_count\": 9}','2025-12-23 14:01:41'),
(101,108,3,'Anonymisierte Daten','{\"source_file\": \"mail_338.json\", \"sync_date\": \"2025-12-23T14:01:41.712211\", \"message_count\": 8}','2025-12-23 14:01:42'),
(102,109,3,'Anonymisierte Daten','{\"source_file\": \"mail_339.json\", \"sync_date\": \"2025-12-23T14:01:42.052764\", \"message_count\": 7}','2025-12-23 14:01:42'),
(103,110,3,'Anonymisierte Daten','{\"source_file\": \"mail_343.json\", \"sync_date\": \"2025-12-23T14:01:42.445067\", \"message_count\": 5}','2025-12-23 14:01:42'),
(104,111,3,'Anonymisierte Daten','{\"source_file\": \"mail_351.json\", \"sync_date\": \"2025-12-23T14:01:42.706972\", \"message_count\": 5}','2025-12-23 14:01:42'),
(105,112,3,'Anonymisierte Daten','{\"source_file\": \"mail_353.json\", \"sync_date\": \"2025-12-23T14:01:42.988092\", \"message_count\": 3}','2025-12-23 14:01:43'),
(106,113,3,'Anonymisierte Daten','{\"source_file\": \"mail_355.json\", \"sync_date\": \"2025-12-23T14:01:43.478247\", \"message_count\": 2}','2025-12-23 14:01:43'),
(107,114,3,'Anonymisierte Daten','{\"source_file\": \"mail_356.json\", \"sync_date\": \"2025-12-23T14:01:43.736754\", \"message_count\": 2}','2025-12-23 14:01:44'),
(108,115,3,'Anonymisierte Daten','{\"source_file\": \"mail_358.json\", \"sync_date\": \"2025-12-23T14:01:44.110123\", \"message_count\": 3}','2025-12-23 14:01:44'),
(109,116,3,'Anonymisierte Daten','{\"source_file\": \"mail_359.json\", \"sync_date\": \"2025-12-23T14:01:44.406525\", \"message_count\": 5}','2025-12-23 14:01:44'),
(110,117,3,'Anonymisierte Daten','{\"source_file\": \"mail_360.json\", \"sync_date\": \"2025-12-23T14:01:44.703581\", \"message_count\": 2}','2025-12-23 14:01:44'),
(111,118,3,'Anonymisierte Daten','{\"source_file\": \"mail_361.json\", \"sync_date\": \"2025-12-23T14:01:44.987054\", \"message_count\": 5}','2025-12-23 14:01:45'),
(112,119,3,'Anonymisierte Daten','{\"source_file\": \"mail_367.json\", \"sync_date\": \"2025-12-23T14:01:45.231518\", \"message_count\": 5}','2025-12-23 14:01:45'),
(113,120,3,'Anonymisierte Daten','{\"source_file\": \"mail_369.json\", \"sync_date\": \"2025-12-23T14:01:45.636557\", \"message_count\": 5}','2025-12-23 14:01:45'),
(114,121,3,'Anonymisierte Daten','{\"source_file\": \"mail_371.json\", \"sync_date\": \"2025-12-23T14:01:45.921787\", \"message_count\": 3}','2025-12-23 14:01:46'),
(115,122,3,'Anonymisierte Daten','{\"source_file\": \"mail_373.json\", \"sync_date\": \"2025-12-23T14:01:46.218927\", \"message_count\": 8}','2025-12-23 14:01:46'),
(116,123,3,'Anonymisierte Daten','{\"source_file\": \"mail_374.json\", \"sync_date\": \"2025-12-23T14:01:46.864513\", \"message_count\": 15}','2025-12-23 14:01:47'),
(117,124,3,'Anonymisierte Daten','{\"source_file\": \"mail_376.json\", \"sync_date\": \"2025-12-23T14:01:47.174274\", \"message_count\": 2}','2025-12-23 14:01:47'),
(118,125,3,'Anonymisierte Daten','{\"source_file\": \"mail_380.json\", \"sync_date\": \"2025-12-23T14:01:47.510093\", \"message_count\": 3}','2025-12-23 14:01:47'),
(119,126,3,'Anonymisierte Daten','{\"source_file\": \"mail_381.json\", \"sync_date\": \"2025-12-23T14:01:47.751117\", \"message_count\": 3}','2025-12-23 14:01:47'),
(120,127,3,'Anonymisierte Daten','{\"source_file\": \"mail_382.json\", \"sync_date\": \"2025-12-23T14:01:47.987465\", \"message_count\": 2}','2025-12-23 14:01:48'),
(121,128,3,'Anonymisierte Daten','{\"source_file\": \"mail_383.json\", \"sync_date\": \"2025-12-23T14:01:48.326438\", \"message_count\": 5}','2025-12-23 14:01:48'),
(122,129,3,'Anonymisierte Daten','{\"source_file\": \"mail_386.json\", \"sync_date\": \"2025-12-23T14:01:48.638471\", \"message_count\": 8}','2025-12-23 14:01:48'),
(123,130,3,'Anonymisierte Daten','{\"source_file\": \"mail_389.json\", \"sync_date\": \"2025-12-23T14:01:49.002049\", \"message_count\": 6}','2025-12-23 14:01:49'),
(124,131,3,'Anonymisierte Daten','{\"source_file\": \"mail_390.json\", \"sync_date\": \"2025-12-23T14:01:49.476232\", \"message_count\": 4}','2025-12-23 14:01:49'),
(125,132,3,'Anonymisierte Daten','{\"source_file\": \"mail_391.json\", \"sync_date\": \"2025-12-23T14:01:49.834936\", \"message_count\": 5}','2025-12-23 14:01:50'),
(126,133,3,'Anonymisierte Daten','{\"source_file\": \"mail_410.json\", \"sync_date\": \"2025-12-23T14:01:50.078241\", \"message_count\": 2}','2025-12-23 14:01:50'),
(127,134,3,'Anonymisierte Daten','{\"source_file\": \"mail_411.json\", \"sync_date\": \"2025-12-23T14:01:50.349414\", \"message_count\": 2}','2025-12-23 14:01:50'),
(128,135,3,'Anonymisierte Daten','{\"source_file\": \"mail_412.json\", \"sync_date\": \"2025-12-23T14:01:50.676459\", \"message_count\": 4}','2025-12-23 14:01:50'),
(129,136,3,'Anonymisierte Daten','{\"source_file\": \"mail_415.json\", \"sync_date\": \"2025-12-23T14:01:50.935918\", \"message_count\": 2}','2025-12-23 14:01:51'),
(130,137,3,'Anonymisierte Daten','{\"source_file\": \"mail_417.json\", \"sync_date\": \"2025-12-23T14:01:51.175745\", \"message_count\": 2}','2025-12-23 14:01:51'),
(131,138,3,'Anonymisierte Daten','{\"source_file\": \"mail_421.json\", \"sync_date\": \"2025-12-23T14:01:51.407129\", \"message_count\": 4}','2025-12-23 14:01:52'),
(132,139,3,'Anonymisierte Daten','{\"source_file\": \"mail_423.json\", \"sync_date\": \"2025-12-23T14:01:52.015479\", \"message_count\": 11}','2025-12-23 14:01:52'),
(133,140,3,'Anonymisierte Daten','{\"source_file\": \"mail_425.json\", \"sync_date\": \"2025-12-23T14:01:52.530209\", \"message_count\": 4}','2025-12-23 14:01:52'),
(134,141,3,'Anonymisierte Daten','{\"source_file\": \"mail_431.json\", \"sync_date\": \"2025-12-23T14:01:52.812797\", \"message_count\": 2}','2025-12-23 14:01:53'),
(135,142,3,'Anonymisierte Daten','{\"source_file\": \"mail_438.json\", \"sync_date\": \"2025-12-23T14:01:53.051537\", \"message_count\": 2}','2025-12-23 14:01:53'),
(136,143,3,'Anonymisierte Daten','{\"source_file\": \"mail_440.json\", \"sync_date\": \"2025-12-23T14:01:53.434781\", \"message_count\": 5}','2025-12-23 14:01:53'),
(137,144,3,'Anonymisierte Daten','{\"source_file\": \"mail_443.json\", \"sync_date\": \"2025-12-23T14:01:53.683421\", \"message_count\": 19}','2025-12-23 14:01:53'),
(138,145,3,'Anonymisierte Daten','{\"source_file\": \"mail_450.json\", \"sync_date\": \"2025-12-23T14:01:53.948846\", \"message_count\": 3}','2025-12-23 14:01:54'),
(139,146,3,'Anonymisierte Daten','{\"source_file\": \"mail_453.json\", \"sync_date\": \"2025-12-23T14:01:54.246143\", \"message_count\": 3}','2025-12-23 14:01:54'),
(140,147,3,'Anonymisierte Daten','{\"source_file\": \"mail_455.json\", \"sync_date\": \"2025-12-23T14:01:54.536453\", \"message_count\": 4}','2025-12-23 14:01:54'),
(141,148,3,'Anonymisierte Daten','{\"source_file\": \"mail_457.json\", \"sync_date\": \"2025-12-23T14:01:54.820282\", \"message_count\": 3}','2025-12-23 14:01:55'),
(142,149,3,'Anonymisierte Daten','{\"source_file\": \"mail_459.json\", \"sync_date\": \"2025-12-23T14:01:55.126432\", \"message_count\": 2}','2025-12-23 14:01:55'),
(143,150,3,'Anonymisierte Daten','{\"source_file\": \"mail_460.json\", \"sync_date\": \"2025-12-23T14:01:55.433390\", \"message_count\": 3}','2025-12-23 14:01:55'),
(144,151,3,'Anonymisierte Daten','{\"source_file\": \"mail_461.json\", \"sync_date\": \"2025-12-23T14:01:55.785125\", \"message_count\": 3}','2025-12-23 14:01:56'),
(145,152,3,'Anonymisierte Daten','{\"source_file\": \"mail_462.json\", \"sync_date\": \"2025-12-23T14:01:56.183689\", \"message_count\": 3}','2025-12-23 14:01:56'),
(146,153,3,'Anonymisierte Daten','{\"source_file\": \"mail_464.json\", \"sync_date\": \"2025-12-23T14:01:56.435862\", \"message_count\": 3}','2025-12-23 14:01:56'),
(147,154,3,'Anonymisierte Daten','{\"source_file\": \"mail_467.json\", \"sync_date\": \"2025-12-23T14:01:56.810402\", \"message_count\": 3}','2025-12-23 14:01:57'),
(148,155,3,'Anonymisierte Daten','{\"source_file\": \"mail_468.json\", \"sync_date\": \"2025-12-23T14:01:57.129805\", \"message_count\": 3}','2025-12-23 14:01:57'),
(149,156,3,'Anonymisierte Daten','{\"source_file\": \"mail_470.json\", \"sync_date\": \"2025-12-23T14:01:57.395591\", \"message_count\": 5}','2025-12-23 14:01:57'),
(150,157,3,'Anonymisierte Daten','{\"source_file\": \"mail_471.json\", \"sync_date\": \"2025-12-23T14:01:57.818460\", \"message_count\": 4}','2025-12-23 14:01:58'),
(151,158,3,'Anonymisierte Daten','{\"source_file\": \"mail_478.json\", \"sync_date\": \"2025-12-23T14:01:58.099729\", \"message_count\": 6}','2025-12-23 14:01:58'),
(152,159,3,'Anonymisierte Daten','{\"source_file\": \"mail_483.json\", \"sync_date\": \"2025-12-23T14:01:58.493691\", \"message_count\": 4}','2025-12-23 14:01:58'),
(153,160,3,'Anonymisierte Daten','{\"source_file\": \"mail_485.json\", \"sync_date\": \"2025-12-23T14:01:58.849182\", \"message_count\": 2}','2025-12-23 14:01:59'),
(154,161,3,'Anonymisierte Daten','{\"source_file\": \"mail_487.json\", \"sync_date\": \"2025-12-23T14:01:59.309915\", \"message_count\": 2}','2025-12-23 14:01:59'),
(155,162,3,'Anonymisierte Daten','{\"source_file\": \"mail_508.json\", \"sync_date\": \"2025-12-23T14:01:59.624699\", \"message_count\": 2}','2025-12-23 14:01:59'),
(156,163,3,'Anonymisierte Daten','{\"source_file\": \"mail_547.json\", \"sync_date\": \"2025-12-23T14:01:59.951690\", \"message_count\": 6}','2025-12-23 14:02:00'),
(157,164,3,'Anonymisierte Daten','{\"source_file\": \"mail_576.json\", \"sync_date\": \"2025-12-23T14:02:00.302279\", \"message_count\": 2}','2025-12-23 14:02:00'),
(158,165,3,'Anonymisierte Daten','{\"source_file\": \"mail_579.json\", \"sync_date\": \"2025-12-23T14:02:00.784031\", \"message_count\": 15}','2025-12-23 14:02:01'),
(159,166,3,'Anonymisierte Daten','{\"source_file\": \"mail_586.json\", \"sync_date\": \"2025-12-23T14:02:01.105698\", \"message_count\": 3}','2025-12-23 14:02:01'),
(160,167,3,'Anonymisierte Daten','{\"source_file\": \"mail_608.json\", \"sync_date\": \"2025-12-23T14:02:01.482203\", \"message_count\": 3}','2025-12-23 14:02:01'),
(161,168,3,'Anonymisierte Daten','{\"source_file\": \"mail_610.json\", \"sync_date\": \"2025-12-23T14:02:01.775789\", \"message_count\": 3}','2025-12-23 14:02:02'),
(162,169,3,'Anonymisierte Daten','{\"source_file\": \"mail_625.json\", \"sync_date\": \"2025-12-23T14:02:02.047976\", \"message_count\": 2}','2025-12-23 14:02:02'),
(163,170,3,'Anonymisierte Daten','{\"source_file\": \"mail_712.json\", \"sync_date\": \"2025-12-23T14:02:02.557079\", \"message_count\": 16}','2025-12-23 14:02:02'),
(164,171,5,'Live-Testungen','{\"source_file\": \"44_keine_lust_mehr.json\", \"sync_date\": \"2025-12-23T14:02:03.649114\", \"message_count\": 10}','2025-12-23 14:02:03'),
(165,172,5,'Live-Testungen','{\"source_file\": \"45_kb_mehr.json\", \"sync_date\": \"2025-12-23T14:02:03.969204\", \"message_count\": 2}','2025-12-23 14:02:04'),
(166,173,5,'Live-Testungen','{\"source_file\": \"47_Frage_zu_Eltern.json\", \"sync_date\": \"2025-12-23T14:02:04.237225\", \"message_count\": 23}','2025-12-23 14:02:04'),
(167,174,5,'Live-Testungen','{\"source_file\": \"48_Frage_zu_Eltern.json\", \"sync_date\": \"2025-12-23T14:02:04.573751\", \"message_count\": 5}','2025-12-23 14:02:05'),
(168,175,5,'Live-Testungen','{\"source_file\": \"50_Rechtsfragen.json\", \"sync_date\": \"2025-12-23T14:02:05.098796\", \"message_count\": 3}','2025-12-23 14:02:05'),
(169,176,5,'Live-Testungen','{\"source_file\": \"53_Sorge_um_Tochter.json\", \"sync_date\": \"2025-12-23T14:02:05.432792\", \"message_count\": 11}','2025-12-23 14:02:05'),
(170,177,5,'Live-Testungen','{\"source_file\": \"56_Was_soll_ich_tun.json\", \"sync_date\": \"2025-12-23T14:02:05.862056\", \"message_count\": 9}','2025-12-23 14:02:06'),
(171,178,5,'Live-Testungen','{\"source_file\": \"59_Nachfrage.json\", \"sync_date\": \"2025-12-23T14:02:06.215395\", \"message_count\": 5}','2025-12-23 14:02:06'),
(172,179,5,'Live-Testungen','{\"source_file\": \"60_Eine_Frage.json\", \"sync_date\": \"2025-12-23T14:02:06.616482\", \"message_count\": 7}','2025-12-23 14:02:06'),
(173,180,5,'Live-Testungen','{\"source_file\": \"61_F\\u00fchrerschein.json\", \"sync_date\": \"2025-12-23T14:02:06.895530\", \"message_count\": 6}','2025-12-23 14:02:07'),
(174,181,5,'Live-Testungen','{\"source_file\": \"62_keiner_mag_mich.json\", \"sync_date\": \"2025-12-23T14:02:07.491932\", \"message_count\": 10}','2025-12-23 14:02:07'),
(175,182,5,'Live-Testungen','{\"source_file\": \"63_niemand_mag_mich.json\", \"sync_date\": \"2025-12-23T14:02:07.786064\", \"message_count\": 12}','2025-12-23 14:02:08'),
(176,183,5,'Live-Testungen','{\"source_file\": \"64_niemand_mag_mich.json\", \"sync_date\": \"2025-12-23T14:02:08.139563\", \"message_count\": 14}','2025-12-23 14:02:08'),
(177,184,5,'Live-Testungen','{\"source_file\": \"65_Meine_Tochter_ist_medienabh\\u00e4ngig_was_kann_ich_tun.json\", \"sync_date\": \"2025-12-23T14:02:08.493777\", \"message_count\": 13}','2025-12-23 14:02:08'),
(178,185,5,'Live-Testungen','{\"source_file\": \"66_Meine_Tochter_ist_medienabh\\u00e4ngig_was_kann_ich_tun.json\", \"sync_date\": \"2025-12-23T14:02:08.810531\", \"message_count\": 12}','2025-12-23 14:02:09'),
(179,186,5,'Live-Testungen','{\"source_file\": \"67_Hilfe_gesucht.json\", \"sync_date\": \"2025-12-23T14:02:09.080080\", \"message_count\": 12}','2025-12-23 14:02:09'),
(180,187,5,'Live-Testungen','{\"source_file\": \"68_Hilfe.json\", \"sync_date\": \"2025-12-23T14:02:09.426279\", \"message_count\": 8}','2025-12-23 14:02:09'),
(181,188,5,'Live-Testungen','{\"source_file\": \"70_Keine_Lust_mehr_auf_Stress.json\", \"sync_date\": \"2025-12-23T14:02:09.825020\", \"message_count\": 14}','2025-12-23 14:02:10'),
(182,189,5,'Live-Testungen','{\"source_file\": \"71_Ahh.json\", \"sync_date\": \"2025-12-23T14:02:10.255848\", \"message_count\": 9}','2025-12-23 14:02:10'),
(183,190,5,'Live-Testungen','{\"source_file\": \"72_Aggression_und_Wut_zuhause.json\", \"sync_date\": \"2025-12-23T14:02:10.679853\", \"message_count\": 10}','2025-12-23 14:02:10'),
(184,191,5,'Live-Testungen','{\"source_file\": \"73_wei\\u00df_nicht_mehr_weiter.json\", \"sync_date\": \"2025-12-23T14:02:10.983935\", \"message_count\": 5}','2025-12-23 14:02:11'),
(185,192,5,'Live-Testungen','{\"source_file\": \"74_Aggression_und_Wut_Zuhause.json\", \"sync_date\": \"2025-12-23T14:02:11.468699\", \"message_count\": 5}','2025-12-23 14:02:11'),
(186,193,5,'Live-Testungen','{\"source_file\": \"75_Viel_Streit_mit_Ex.json\", \"sync_date\": \"2025-12-23T14:02:11.765213\", \"message_count\": 9}','2025-12-23 14:02:12'),
(187,194,5,'Live-Testungen','{\"source_file\": \"77_mir_gehts_nicht_gut.json\", \"sync_date\": \"2025-12-23T14:02:12.016846\", \"message_count\": 9}','2025-12-23 14:02:12'),
(188,195,5,'Live-Testungen','{\"source_file\": \"78_Bin_ich_hier_richtig.json\", \"sync_date\": \"2025-12-23T14:02:12.458606\", \"message_count\": 10}','2025-12-23 14:02:12'),
(189,196,5,'Live-Testungen','{\"source_file\": \"81_F\\u00fchrerschein.json\", \"sync_date\": \"2025-12-23T14:02:12.783215\", \"message_count\": 5}','2025-12-23 14:02:13'),
(190,197,5,'Live-Testungen','{\"source_file\": \"82_Was_tun_wegen_Mobbing.json\", \"sync_date\": \"2025-12-23T14:02:13.081428\", \"message_count\": 8}','2025-12-23 14:02:13'),
(191,198,5,'Live-Testungen','{\"source_file\": \"84_Angst_um_meiner_Tochter.json\", \"sync_date\": \"2025-12-23T14:02:13.421639\", \"message_count\": 10}','2025-12-23 14:02:13'),
(192,199,5,'Live-Testungen','{\"source_file\": \"85_Stress_am_Arbeitsplatz.json\", \"sync_date\": \"2025-12-23T14:02:13.652988\", \"message_count\": 5}','2025-12-23 14:02:13'),
(193,200,5,'Live-Testungen','{\"source_file\": \"87_Rechtliche_Frage.json\", \"sync_date\": \"2025-12-23T14:02:13.912236\", \"message_count\": 14}','2025-12-23 14:02:14'),
(194,201,5,'Live-Testungen','{\"source_file\": \"88_Rechtliche_Frage.json\", \"sync_date\": \"2025-12-23T14:02:14.215677\", \"message_count\": 5}','2025-12-23 14:02:14'),
(195,202,5,'Live-Testungen','{\"source_file\": \"89_Rechtliche_Frage.json\", \"sync_date\": \"2025-12-23T14:02:14.578967\", \"message_count\": 7}','2025-12-23 14:02:14'),
(196,203,5,'Live-Testungen','{\"source_file\": \"90_Meine_Tochter_ist_st\\u00e4ndig_am_Handy.json\", \"sync_date\": \"2025-12-23T14:02:14.922502\", \"message_count\": 3}','2025-12-23 14:02:15'),
(197,204,5,'Live-Testungen','{\"source_file\": \"91_Wut_und_Aggression.json\", \"sync_date\": \"2025-12-23T14:02:15.295932\", \"message_count\": 8}','2025-12-23 14:02:15'),
(198,205,5,'Live-Testungen','{\"source_file\": \"93_Hilfe_f\\u00fcr_meine_Tochter_.json\", \"sync_date\": \"2025-12-23T14:02:15.633005\", \"message_count\": 16}','2025-12-23 14:02:16'),
(199,206,5,'Live-Testungen','{\"source_file\": \"94_MPU.json\", \"sync_date\": \"2025-12-23T14:02:16.078519\", \"message_count\": 11}','2025-12-23 14:02:16');
/*!40000 ALTER TABLE `pillar_threads` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-23 21:27:42
