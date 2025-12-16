-- Migration: Add Agent Mode and Web Search columns to chatbot_prompt_settings
-- Date: 2025-12-16
-- Description: Adds agent_mode, task_type, web_search settings, and agent prompts

-- Create ENUM types if they don't exist
-- Note: In MariaDB, ENUMs are defined inline

-- Add agent_mode column
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS agent_mode ENUM('standard', 'act', 'react', 'reflact') NOT NULL DEFAULT 'standard';

-- Add task_type column
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS task_type ENUM('lookup', 'multihop') NOT NULL DEFAULT 'lookup';

-- Add agent_max_iterations column
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS agent_max_iterations INT NOT NULL DEFAULT 5;

-- Add web search configuration
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS web_search_enabled TINYINT(1) NOT NULL DEFAULT 0;

ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS tavily_api_key VARCHAR(255) NULL;

ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS web_search_max_results INT NOT NULL DEFAULT 5;

-- Add tools_enabled JSON column
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS tools_enabled JSON DEFAULT NULL;

-- Update tools_enabled with default value for existing rows
UPDATE chatbot_prompt_settings
SET tools_enabled = '["rag_search", "lexical_search", "respond"]'
WHERE tools_enabled IS NULL;

-- Add agent prompts
ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS reflection_prompt TEXT NOT NULL DEFAULT 'Überprüfe deine vorherige Antwort kritisch:\n1. Sind alle Quellenverweise [1], [2], ... korrekt und belegt?\n2. Wurden nur Informationen aus dem Kontext verwendet?\n3. Ist die Antwort vollständig und beantwortet alle Aspekte der Frage?\n4. Gibt es Halluzinationen oder unbelegte Behauptungen?\n\nFalls Fehler gefunden wurden, korrigiere die Antwort. Sonst bestätige die Antwort.';

ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS act_system_prompt TEXT NOT NULL DEFAULT 'Du hast Zugriff auf folgende Tools:\n- rag_search(query): Semantische Suche in den Dokumenten\n- lexical_search(query): Wörtliche Suche in den Dokumenten\n- web_search(query): Web-Suche für aktuelle Informationen\n- respond(answer): Finale Antwort geben\n\nFühre die passende Aktion aus, um die Frage zu beantworten.\nFormat: ACTION: tool_name(parameter)';

ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS react_system_prompt TEXT NOT NULL DEFAULT 'Du bist ein Assistent, der strukturiert denkt und handelt.\n\nBei jeder Anfrage folgst du diesem Prozess:\n1. THOUGHT: Analysiere die Frage und überlege, welche Informationen benötigt werden\n2. ACTION: Führe eine der verfügbaren Aktionen aus\n3. OBSERVATION: Analysiere das Ergebnis der Aktion\n4. Wiederhole bis du genug Informationen hast\n5. FINAL ANSWER: Gib eine fundierte Antwort mit Quellenverweisen\n\nVerfügbare Aktionen:\n- rag_search(query): Semantische Suche in den Dokumenten\n- lexical_search(query): Wörtliche Suche in den Dokumenten\n- web_search(query): Web-Suche für aktuelle Informationen\n- respond(answer): Finale Antwort geben';

ALTER TABLE chatbot_prompt_settings
ADD COLUMN IF NOT EXISTS reflact_system_prompt TEXT NOT NULL DEFAULT 'Du bist ein zielorientierter Assistent, der vor jeder Aktion sein Ziel reflektiert.\n\nBei jeder Anfrage folgst du diesem Prozess:\n1. GOAL: Definiere das übergeordnete Ziel der Anfrage\n2. REFLECTION: Reflektiere, wie weit du vom Ziel entfernt bist\n3. THOUGHT: Überlege den nächsten sinnvollen Schritt\n4. ACTION: Führe eine Aktion aus\n5. OBSERVATION: Analysiere das Ergebnis\n6. Wiederhole ab Schritt 2 bis das Ziel erreicht ist\n7. FINAL ANSWER: Gib eine fundierte Antwort mit Quellenverweisen\n\nVerfügbare Aktionen:\n- rag_search(query): Semantische Suche in den Dokumenten\n- lexical_search(query): Wörtliche Suche in den Dokumenten\n- web_search(query): Web-Suche für aktuelle Informationen\n- respond(answer): Finale Antwort geben';
