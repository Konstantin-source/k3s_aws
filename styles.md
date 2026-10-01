# Stilrichtlinie für die Projektarbeit (`styles.md`)

> **Hinweis zum Status:**  
> Diese Datei enthält die vorläufigen stilistischen und sprachlichen Vorgaben, abgeleitet aus:
> 1. Dem offiziellen Leitfaden der Rheinischen Hochschule Köln (`leitfaden-main_10.2025/abschnitte/06-form-stil.tex`),
> 2. Der Referenzarbeit `ThreadstormDoku (1).pdf` (SS 2026, Prof. Dr. Johannes Mauer).
> 
> *Falls eine spezifische Hochschul- oder Prüfer-`styles.md` vorliegt, bitte Inhalt bereitstellen.*

---

## 1. Sprachlicher & Wissenschaftlicher Stil

1. **Sachlich, nüchtern und präzise:**
   - Keine Umgangssprache, keine Redewendungen, keine Phrasen oder Allgemeinplätze.
   - Keine werbenden Adjektive (z. B. „revolutionär“, „außerordentlich“, „perfekt“) und keine Dramatisierung.
   - Trennung von sachlicher Darstellung (in den Kapiteln 1–7) und kritischer Interpretation/Bewertung (in Kapitel 8).

2. **Gedankenführung & Syntax:**
   - Grundsatz: *„Eine Aussage, ein Satz. Ein Gedanke, ein Absatz.“*
   - Kurze bis mittellange Hauptsätze bevorzugen; Schachtelsätze und Ketten von Nebensätzen vermeiden.
   - Umständliche Passivkonstruktionen auflösen, wo möglich klare Akteure benennen (Systemkomponenten, Controller, Mechanismen).

3. **Tempus:**
   - **Präsens (Gegenwart):** Für allgemeine Fakten, Systemeigenschaften, Funktionsweisen und bestehende Architekturen.
   - **Präteritum (Vergangenheit):** Für konkret durchgeführte Arbeitsschritte, Versuchsabläufe und historische Implementierungsphasen (analog zur Threadstorm-Referenz).
   - Kein historisches Präsens.

4. **Perspektive & Pronomen:**
   - Grundsätzlich unpersönlich / distanziert formulieren („Es wird gezeigt...“, „Die Implementierung umfasst...“).
   - Sparsamer Einsatz der ersten Person („Ich“ bzw. „Wir“ nur in begründeten Abschnitten zur Vorgehensweise oder Motivation in der Einleitung, falls nötig).

5. **Fachterminologie:**
   - Etablierte englische Fachbegriffe des Cloud- und Kubernetes-Ökosystems beibehalten (z. B. *Deployment*, *Pod*, *Ingress*, *Replica*, *Self-Heal*, *Rolling Update*, *Control Plane*).
   - Einheitliche Schreibweise über das gesamte Dokument einhalten.
   - Jede nicht-triviale Abkürzung beim ersten Auftreten ausschreiben und im Abkürzungsverzeichnis (`zusatz/abkuerzungen.tex`) pflegen.

---

## 2. Zitierweise & Quellen

- **Format:** Chicago Manual of Style (*Notes and Bibliography*), umgesetzt mit `biblatex-chicago` und Zitaten via Fußnoten (`\autocite` bzw. `\customcite`).
- **Quellenqualität:** Bevorzugung von offizieller Dokumentation (Kubernetes, AWS, HashiCorp Terraform, Argo Project), RFCs, Whitepapern und wissenschaftlicher Fachliteratur.
- **Vollständigkeit:** Keine Aussage ohne Beleg, sofern sie nicht originäre Eigenleistung darstellt.
- **KI-Transparenz:** Nachweis eingesetzter KI-Werkzeuge und Prompts im Promptverzeichnis gemäß RH-Leitfaden.

---

## 3. Typografie & Layout (Gemäß RH-Köln-Vorlage)

- **Schriftart:** Arial (11 pt), Zeilenabstand 1,5-zeilig.
- **Ränder:** Links 3,5 cm, Rechts 2,5 cm, Oben 3,0 cm, Unten 2,0 cm.
- **Absätze:** Kein Absatzeinzug (`\parindent 0pt`), 6 pt Abstand nach Absätzen (`\parskip 6pt`).
- **Gliederung:** Maximal 3 Hierarchieebenen (z. B. 1.2.3).
- **Abbildungen & Tabellen:** Durchgehende Nummerierung, präzise Untertitel mit Quellenangabe (z. B. „Eigene Darstellung“ oder Primärquelle).
