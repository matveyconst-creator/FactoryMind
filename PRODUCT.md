# FactoryMind

## Vision

FactoryMind is an AI workspace for students.

Instead of using separate tools for chatting with documents, creating
flashcards, generating quizzes, preparing formula sheets, searching the
web, and studying for exams, students can manage their entire course
and learning workflow in one place.

The central interaction is an AI chat connected to the complete context
of a course.

---

## Core Concept

Each university course is represented as a Workspace.

Example:

Deep Learning
├── Course Overview
├── Sources
│   ├── Lectures
│   ├── Exercises
│   ├── Solutions
│   ├── Past Exams
│   ├── Notes
│   ├── Images
│   ├── Videos
│   └── External Links
├── Chat
├── Study Tools
└── Generated Artifacts

The AI should understand not only the contents of uploaded files, but
also the structure and metadata of the entire workspace.

---

## Core Features

### 1. Course Summaries

Generate summaries for:
- individual lectures
- multiple lectures
- topics
- the complete course

---

### 2. Flashcards & Quizzes

Automatically generate flashcards and quizzes from course materials.

They can be generated for:
- a lecture
- a topic
- selected materials
- the entire exam

Results should eventually contribute to learning progress.

---

### 3. Formula Collection

Especially important for engineering and STEM courses.

Automatically detect and organize important formulas.

Each formula may contain:
- formula
- description
- variables
- topic
- usage
- source references

Students should be able to generate exam-specific formula sheets,
for example:

"Create a two-page A4 formula sheet for my exam."

---

### 4. Course Workspace

Students can create one workspace for each course and upload all
relevant material.

Examples:
- lectures
- exercises
- solutions
- previous exams
- notes
- images
- videos
- presentations
- spreadsheets
- external resources

FactoryMind should understand the type and role of each source.

---

### 5. AI Chat

The chat is the central interface of FactoryMind.

Students should be able to interact naturally with their course:

"Explain exercise 4.2."

"Why is this step necessary?"

"Give me another similar problem."

"Add this formula to my formula sheet."

"Create flashcards from this topic."

Most functionality should be accessible directly through the chat
instead of requiring separate AI tools or pages.

---

### 6. Course & Exam Information

Each workspace contains important course information such as:

- exam date
- time remaining until exam
- professor
- allowed materials
- exam duration
- course description

This information should be visible in the main course overview.

---

### 7. Practice Generator

Generate new exercises based on:
- existing exercises
- previous exams
- course topics
- difficulty level

Example:

"Generate five exercises similar to the previous exams, but don't
show the solutions yet."

Students should be able to submit their solutions and receive feedback.

---

### 8. External Research

FactoryMind can search for additional information when course material
is insufficient.

Examples:
- explanations
- university resources
- documentation
- articles
- relevant websites
- YouTube videos

The UI should clearly distinguish between:

Course Sources
and
External Sources.

---

### 9. Learning Progress

FactoryMind should gradually understand the student's learning progress.

Possible signals:
- quiz results
- flashcard performance
- solved exercises
- repeated questions
- incorrect answers
- topics studied

This can later support:
- weak-topic detection
- exam preparation
- personalized practice
- study plans

Progress must be based on actual learning signals rather than arbitrary
AI-generated percentages.

---

## Universal Input

FactoryMind should eventually support common formats students use:

- PDF
- DOCX
- PPTX
- TXT / Markdown
- Images
- Screenshots
- Handwritten notes
- CSV / Excel
- Audio
- Video
- YouTube links
- Web links

The user should be able to attach these directly to the chat or course
workspace.

---

## Universal Output

FactoryMind should be able to turn course knowledge into useful
artifacts such as:

- explanations
- summaries
- notes
- flashcards
- quizzes
- mock exams
- formula sheets
- diagrams
- charts
- tables
- PowerPoint presentations
- PDF documents
- Word documents
- structured study guides

Generated artifacts belong to the course workspace and can be reused
in later conversations.

---

## Product Principles

### Chat-first, not chat-only

The AI chat is the main interface.

Useful contextual actions such as:

- Explain
- Quiz me
- Create flashcards
- Visualize
- Add to formula sheet
- Export

can exist as shortcuts without turning FactoryMind into a collection
of disconnected AI tools.

### Course-aware

FactoryMind understands the complete course rather than treating every
uploaded file independently.

### Student-focused

Features should solve real student workflows rather than exist simply
because an AI model can perform them.

### Everything in one place

Students should not need separate AI applications for documents,
flashcards, quizzes, notes, presentations, charts, and exam preparation.

---

## Long-Term Goal

FactoryMind should evolve from:

PDF Chatbot

into:

AI Course Workspace

and eventually:

AI Study Environment