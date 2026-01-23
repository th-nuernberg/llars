---
name: paper-writing
description: Write and compile academic papers (LaTeX). Use when writing conference papers, creating PDFs, or working on the LLARS IJCAI paper.
---

# Academic Paper Writing for LLARS

Guide for writing and compiling academic papers, specifically for IJCAI demo track submissions.

## Paper Location

```
Paper/
├── ijcai26.tex      # Main LaTeX source
├── llars.bib        # Bibliography
├── named.bst        # Citation style
├── build.sh         # Build script
├── out/             # Compiled output
└── PAPER_NOTES.md   # Key concepts and notes
```

## Building the Paper

### Quick Build (Recommended)

```bash
cd Paper
./build.sh
```

This script:
1. Runs pdflatex (1st pass)
2. Runs bibtex for references
3. Runs pdflatex (2nd + 3rd pass)
4. Copies final PDF to `Paper/ijcai26.pdf`
5. Opens PDF on macOS

### Manual Build

```bash
cd Paper
mkdir -p out
pdflatex -output-directory=out ijcai26.tex
cp *.bib *.bst out/
cd out && bibtex ijcai26 && cd ..
pdflatex -output-directory=out ijcai26.tex
pdflatex -output-directory=out ijcai26.tex
```

## IJCAI Demo Paper Guidelines

### Page Limits
- **Main content:** 3 pages maximum
- **References:** Up to 2 additional pages
- **Total:** 5 pages maximum

### Typical Structure (Based on Accepted Papers)

| Section | Content | ~Length |
|---------|---------|---------|
| Abstract | Key contribution, results, demo link | 150 words |
| Introduction | Problem, gap, solution | 300 words |
| System Overview | Architecture diagram | 200 words |
| Core Features | 2-3 main innovations | 400 words |
| Application | Real-world deployment | 200 words |
| Demonstration | Numbered steps | 150 words |

### Visual Elements (Accepted Papers Pattern)

- **2-3 Figures**: Screenshots, architecture diagrams
- **0-1 Tables**: Comparison or results
- **Minimal bullet lists**: Prefer flowing text

## Writing Best Practices

### Strong Motivation
Clearly articulate WHO benefits and WHY:

```latex
% Good: Specific stakeholders
Domain experts---psychologists assessing counseling responses,
physicians reviewing medical summaries---understand \emph{what}
constitutes quality. AI developers understand \emph{how} to
configure LLM evaluators.

% Bad: Generic
Evaluating LLM outputs is important.
```

### Concrete Examples

```latex
% Good: Specific
Five psychology students and two LLM evaluators (GPT-4, Claude-3)
rated responses on empathy, clarity, professionalism, and helpfulness.

% Bad: Vague
Multiple evaluators assessed various responses.
```

### Quantitative Results

```latex
% Good: Numbers with context
Initial human-LLM correlation was $r = 0.47$. After three
refinement iterations, agreement improved to $r = 0.54$---a
12\% increase.

% Bad: No specifics
Agreement improved significantly after refinement.
```

## LaTeX Tips

### Required Packages for IJCAI

```latex
\usepackage{ijcai26}      % Conference style
\usepackage{times}        % Required font
\usepackage{amsmath}      % Math symbols
\usepackage{amssymb}      % \checkmark, etc.
\usepackage{booktabs}     % Nice tables
\usepackage{tikz}         % Diagrams
```

### TikZ Architecture Diagram

```latex
\begin{figure}[t]
\centering
\resizebox{0.95\linewidth}{!}{%
\begin{tikzpicture}[
    box/.style={rectangle, draw, rounded corners=2pt,
                minimum height=0.5cm, font=\scriptsize\sffamily},
    biarrow/.style={{Stealth[length=1.5mm]}-{Stealth[length=1.5mm]},
                    thick, gray!70}
]
\node[box, fill=green!10] (user) {Users};
\node[box, fill=yellow!15, below=0.5cm of user] (backend) {Backend};
\draw[biarrow] (user) -- (backend);
\end{tikzpicture}%
}
\caption{System architecture.}
\label{fig:architecture}
\end{figure}
```

### Screenshot Placeholder

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}
\node[draw, rounded corners, fill=gray!5,
      minimum width=0.93\linewidth, minimum height=3.5cm] {
\begin{minipage}{0.85\linewidth}
\centering\scriptsize\sffamily
\textbf{[Screenshot: Feature Name]}\\[0.4em]
Description of what the screenshot shows
\end{minipage}
};
\end{tikzpicture}
\caption{Caption text.}
\label{fig:screenshot}
\end{figure}
```

## Comparison with Accepted Papers

When writing, compare against accepted IJCAI demo papers:

1. **Fetch examples:**
   ```
   https://ijcai24.org/demonstrations-track-accepted-papers/
   ```

2. **Analyze structure:**
   - How many figures?
   - How much flowing text vs. bullet lists?
   - What sections do they use?

3. **Match the style:**
   - Academic but accessible
   - Concrete examples
   - Clear demonstration scenario

## Review Checklist

Before submission:

- [ ] **Page count:** 3 pages main + refs
- [ ] **Figures:** 2-3 with real screenshots (not placeholders)
- [ ] **Demo URL:** Valid and accessible
- [ ] **Repository URL:** Public and documented
- [ ] **References:** All cited, properly formatted
- [ ] **Author info:** Correct affiliations and emails
- [ ] **No orphan lines:** Check page breaks
- [ ] **PDF metadata:** Title and authors set

## Workflow Summary

1. **Research:** Read accepted papers, understand format
2. **Outline:** Plan sections and figures
3. **Draft:** Write flowing text, avoid bullet lists
4. **Review:** Check each section reads well
5. **Figures:** Add real screenshots
6. **Build:** Run `./build.sh`
7. **Iterate:** Refine based on page count

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `./build.sh` | Full build with PDF output |
| `open ijcai26.pdf` | View compiled PDF (macOS) |
| `pdflatex -output-directory=out ijcai26.tex` | Single compile pass |
