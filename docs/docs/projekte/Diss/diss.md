flowchart TD
    %% ========== EBENE 1: INPUT ==========
    subgraph INPUT[" "]
        U["User Email / Thread<br/>(vollständige Historie, letzte Nachricht)"]
    end

    %% ========== EBENE 2: INPUT SAFEGUARD ==========
    subgraph GUARD_IN[" "]
        IS["Input Safeguard f_in<br/>(OK vs. Deferral)"]
    end

    %% ========== EBENE 3: ANALYSE ==========
    subgraph ANALYSIS[" "]
        CCTX["Conversation Context<br/>(Thread-Analyse)"]
        EMB["Embedding Model<br/>(Sentence Embeddings)"]
    end

    %% ========== EBENE 4: RETRIEVAL ==========
    subgraph RETRIEVAL[" "]
        KDB["Knowledge Database<br/>(Guidelines, Policies, Beispiele)"]
        LTM["Long-Term Memory DB<br/>(Ähnliche frühere Fälle)"]
    end

    %% ========== EBENE 5: SYNTHESE (PERSONA) ==========
    subgraph SYNTHESIS[" "]
        PDKS["PD/KS Classifier g_style<br/>(Persönlichkeit & Kommunikationsstil)"]
        PERS["Persona Profile<br/>(Style & Trait Vector)"]
    end

    %% ========== EBENE 5b: ENRICHMENT (EIGENER BLOCK) ==========
    subgraph ENRICHMENT[" "]
        ENR["Enrichment Block<br/>(System Prompt + Thread + Persona + Knowledge + LTM)"]
    end

    %% ========== EBENE 6: GENERIERUNG ==========
    subgraph GENERATION[" "]
        LLM["Generator + Adapter<br/>(GAN-trained LLM)"]
    end

    %% ========== EBENE 7: OUTPUT SAFEGUARD ==========
    subgraph GUARD_OUT[" "]
        OS["Output Safeguard f_out<br/>(Release / Regenerate / Deferral)"]
    end

    %% ========== EBENE 8: OUTPUT ==========
    subgraph OUTPUT[" "]
        U_out["Reply to User"]
        H["Human Counsellor<br/>(Output Escalation)"]
    end

    %% ========== VERBINDUNGEN ==========
    U --> IS
    IS -->|"Deferral"| H
    IS -->|"OK"| CCTX
    
    CCTX --> PDKS
    CCTX --> ENR
    CCTX --> EMB
    
    PDKS --> PERS
    EMB --> KDB
    EMB --> LTM
    
    PERS --> ENR
    KDB --> ENR
    LTM --> ENR
    
    ENR --> LLM
    LLM --> OS
    
    OS -->|"Release"| U_out
    OS -->|"Deferral"| H
    OS -->|"Regenerate"| ENR

    %% ========== STYLES ==========
    classDef inputStyle fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    classDef safeguardStyle fill:#E74C3C,stroke:#C0392B,stroke-width:2px,color:#fff
    classDef analysisStyle fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#fff
    classDef retrievalStyle fill:#27AE60,stroke:#1E8449,stroke-width:2px,color:#fff
    classDef synthesisStyle fill:#F39C12,stroke:#D68910,stroke-width:2px,color:#fff
    classDef enrichmentStyle fill:#F5B7B1,stroke:#CD6155,stroke-width:3px,color:#17202A
    classDef llmStyle fill:#9B59B6,stroke:#7D3C98,stroke-width:2px,color:#fff
    classDef outputStyle fill:#16A085,stroke:#117A65,stroke-width:2px,color:#fff
    classDef humanStyle fill:#95A5A6,stroke:#7F8C8D,stroke-width:2px,color:#fff

    class U inputStyle
    class IS safeguardStyle
    class CCTX,EMB analysisStyle
    class KDB,LTM retrievalStyle
    class PERS,PDKS synthesisStyle
    class ENR enrichmentStyle
    class LLM llmStyle
    class OS outputStyle
    class U_out outputStyle
    class H humanStyle