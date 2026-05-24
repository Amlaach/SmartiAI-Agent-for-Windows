# SmartiAI Agent for Windows

עברית: [מעבר לגרסה העברית](#עברית)

SmartiAI Agent for Windows is a desktop AI agent built for practical work on a Windows computer. It is more than a chat window: Smarti can plan tasks, use local tools, inspect files, work with the web, automate browser and desktop actions, manage email, remember useful context, and ask for approval before sensitive operations.

The goal is simple: give the user a capable assistant that can help operate the computer while staying transparent, configurable, and under the user's control.

## What Smarti Can Do

- Understand a request, break it into steps, choose the right tools, run the work, and show intermediate action steps.
- Work with local files and folders: open safe files, create text files, read documents, search by filename, search inside text/code, and extract text from images when OCR is configured.
- Use the web: search the internet, read specific webpages, open links in the browser, and fetch weather forecasts.
- Control Windows in a structured way: list/open installed apps, inspect UI elements, click buttons, set text fields, send hotkeys, update the clipboard, and manage audio mute state.
- Automate a dedicated Chrome browser session with Selenium, including page inspection, form interaction, navigation, and extraction of visible page state.
- Manage email through IMAP/SMTP: search, read, draft, send, reply, forward, archive, move, delete, manage folders, and save attachments.
- Run controlled system and developer tasks: PowerShell commands with approval, read-only Git operations, project test/build commands, and process listing.
- Schedule background work, list running or pending tasks, cancel tasks, and retry previous tasks.
- Remember useful context locally, with separate user, short-term, long-term, and tool memories.
- Extend itself with custom Python tools, MCP packages, and beta Skills.

## Example Use Cases

- "Find the latest invoice PDF in Downloads, summarize it, and save the summary as a text file."
- "Search this project for where browser automation is implemented."
- "Open Chrome, go to a site, fill a form, and tell me what happened."
- "Check my inbox for unread messages from a client and draft a reply."
- "Run the project tests and summarize any failures."
- "Take a screenshot and explain what is visible on the screen."
- "Remind me in 30 minutes to continue this task."
- "Create a reusable Python tool for processing this type of file."
- "Search the web for current information, then open the most relevant result."
- "Remember that I prefer concise Hebrew answers for this project."

## Built-In Tool Areas

| Area | What it is used for |
| --- | --- |
| System | PowerShell commands, project checks, Git status/diff/log/show, process listing, clipboard, audio mute/unmute. |
| Software | Discovering installed apps, finding the best app match, and opening software. |
| Files | Opening files/folders, saving text, reading documents, searching filenames, searching content, and OCR. |
| Web | Internet search, webpage reading, browser opening, and weather. |
| Screen | Capturing screenshots, saving screenshots, and analyzing local images. |
| Automation | Browser automation through Selenium and desktop automation through Windows UI Automation. |
| Email | IMAP/SMTP search, read, send, draft, reply, forward, labels/folders, attachments, archive, and delete. |
| Memory | Local context storage, search, update, expiry, and Markdown export. |
| Background Tasks | One-time and repeating scheduled work, task list, cancel, and retry. |
| Extensions | Custom Python tools, MCP packages, and beta Skills. |

## Safety and Control

Smarti is designed to be useful without being careless. Sensitive capabilities are gated by settings and approval prompts. You can configure permission levels, enable or disable tool groups, require approval for shell commands and extension installs, use optional sandboxing, redact logs, and store secrets through Keyring or Windows DPAPI.

Actions such as writing files, running commands, controlling the desktop, reading email, sending email, using screenshots, or uploading local content to a cloud model are treated as sensitive and can require explicit user approval.

## Model Support

Smarti can work with several model providers:

- Gemini
- OpenAI
- Anthropic
- OpenRouter
- Groq
- Local OpenAI-compatible servers, such as LM Studio

Model keys and local server settings are configured from the app settings screen.

## Quick Start

Requirements: Windows, Python 3.10 or newer, and Git if you want to use Git tools.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python smarti_core.pyw
```

To run without a console window, open `smarti_core.pyw` directly from Windows or use:

```powershell
pythonw smarti_core.pyw
```

## Optional Capabilities

- Browser automation requires Google Chrome.
- MCP support requires Node.js and `npx`.
- Voice input requires a working microphone, `SpeechRecognition`, `keyboard`, and `PyAudio`.
- OCR requires `pytesseract`, `Pillow`, and the Tesseract OCR engine installed on the system and available in `PATH`.
- Usage-cost estimates are more useful when `litellm` is installed.

## Project Structure

```text
smarti_core.pyw          Compatibility launcher and main entry point
smarti/                  Modular application code
  app.py                 App startup, splash screen, and main window
  core.py                Agent engine, tools, permissions, and execution flow
  config.py              Built-in tool schemas and default settings
  chat.py                Chat UI, tray behavior, voice input, and notifications
  ui_pages.py            Settings, tools, tasks, usage, logs, and about pages
  managers.py            Settings, memory, MCP, Skills, policy, and registries
  workers.py             QThreads for agent work, voice, TTS, and model loading
assets/                  Logo, icons, and UI assets
custom_tools/            Custom Python tools created or used by the agent
mcp_tools/               Wrappers for installed MCP tools
skills/                  Installed Skills
Smarti_Outputs/          Default output folder
```

## Local Data

Smarti stores settings, usage data, memory, and logs in local files such as `smarti_settings.json`, `smarti_memory.json`, `smarti_usage.json`, `smarti_agent.log`, and `smarti_audit.log`. Sensitive and generated files are listed in `.gitignore` so they are not committed by accident.

## License

This project is distributed under the license included in `LICENSE`.

---

## עברית

SmartiAI Agent for Windows הוא סוכן AI שולחני שנועד לעבודה מעשית על מחשב Windows. הוא לא רק חלון צ'אט: Smarti יכול לתכנן משימות, להשתמש בכלים מקומיים, לבדוק קבצים, לעבוד עם האינטרנט, לבצע אוטומציה בדפדפן ובשולחן העבודה, לנהל אימייל, לזכור הקשר שימושי ולבקש אישור לפני פעולות רגישות.

המטרה פשוטה: לתת למשתמש עוזר חזק שיכול לעזור להפעיל את המחשב, תוך שקיפות, אפשרות הגדרה ושליטה מלאה של המשתמש.

## מה Smarti יודע לעשות

- להבין בקשה, לפרק אותה לשלבים, לבחור את הכלים המתאימים, לבצע את העבודה ולהציג שלבי פעולה תוך כדי.
- לעבוד עם קבצים ותיקיות מקומיים: לפתוח קבצים בטוחים, ליצור קבצי טקסט, לקרוא מסמכים, לחפש לפי שם קובץ, לחפש בתוך טקסט/קוד ולחלץ טקסט מתמונות כאשר OCR מוגדר.
- להשתמש באינטרנט: לחפש ברשת, לקרוא דפי אתר מסוימים, לפתוח קישורים בדפדפן ולקבל תחזית מזג אוויר.
- לשלוט ב-Windows בצורה מובנית: להציג/לפתוח תוכנות מותקנות, לבדוק רכיבי ממשק, ללחוץ על כפתורים, למלא שדות טקסט, לשלוח קיצורי מקשים, לעדכן את לוח ההעתקה ולנהל מצב השתקת שמע.
- לבצע אוטומציה בסשן Chrome ייעודי באמצעות Selenium, כולל בדיקת מצב הדף, עבודה עם טפסים, ניווט וחילוץ מידע גלוי מהעמוד.
- לנהל אימייל דרך IMAP/SMTP: לחפש, לקרוא, לכתוב טיוטות, לשלוח, להשיב, להעביר, לארכב, להעביר תיקייה, למחוק, לנהל תיקיות ולשמור קבצים מצורפים.
- להריץ משימות מערכת ופיתוח מבוקרות: פקודות PowerShell עם אישור, פעולות Git לקריאה בלבד, פקודות test/build לפרויקט ורשימת תהליכים.
- לתזמן עבודה ברקע, להציג משימות פעילות או מתוכננות, לבטל משימות ולהריץ מחדש משימות קודמות.
- לזכור הקשר שימושי באופן מקומי, עם זיכרונות משתמש, טווח קצר, טווח ארוך וזיכרונות כלים.
- להתרחב בעזרת כלי Python מותאמים אישית, חבילות MCP ו-Skills בגרסת בטא.

## מקרי שימוש לדוגמה

- "מצא את קובץ החשבונית האחרון בתיקיית Downloads, סכם אותו ושמור את הסיכום כקובץ טקסט."
- "חפש בפרויקט הזה איפה ממומשת אוטומציית הדפדפן."
- "פתח את Chrome, עבור לאתר, מלא טופס וספר לי מה קרה."
- "בדוק בתיבת המייל הודעות שלא נקראו מלקוח וכתוב טיוטת תשובה."
- "הרץ את בדיקות הפרויקט וסכם את השגיאות אם יש."
- "צלם את המסך והסבר מה רואים בו."
- "הזכר לי בעוד 30 דקות להמשיך את המשימה הזו."
- "צור כלי Python רב-פעמי לעיבוד קבצים מהסוג הזה."
- "חפש ברשת מידע עדכני ואז פתח את התוצאה הכי רלוונטית."
- "זכור שאני מעדיף תשובות עבריות קצרות בפרויקט הזה."

## אזורי כלים מובנים

| תחום | למה הוא משמש |
| --- | --- |
| מערכת | פקודות PowerShell, בדיקות פרויקט, Git status/diff/log/show, רשימת תהליכים, לוח העתקה והשתקה/ביטול השתקה. |
| תוכנות | גילוי תוכנות מותקנות, מציאת התאמה טובה לשם תוכנה ופתיחת תוכנות. |
| קבצים | פתיחת קבצים/תיקיות, שמירת טקסט, קריאת מסמכים, חיפוש שמות קבצים, חיפוש תוכן ו-OCR. |
| אינטרנט | חיפוש ברשת, קריאת דפי אתר, פתיחה בדפדפן ומזג אוויר. |
| מסך | צילום מסך, שמירת צילום מסך וניתוח תמונות מקומיות. |
| אוטומציה | אוטומציית דפדפן דרך Selenium ואוטומציית שולחן עבודה דרך Windows UI Automation. |
| אימייל | חיפוש, קריאה, שליחה, טיוטות, תשובות, העברה, תוויות/תיקיות, קבצים מצורפים, ארכוב ומחיקה דרך IMAP/SMTP. |
| זיכרון | שמירת הקשר מקומי, חיפוש, עדכון, תפוגה וייצוא ל-Markdown. |
| משימות רקע | עבודה מתוזמנת חד-פעמית או חוזרת, רשימת משימות, ביטול והרצה מחדש. |
| הרחבות | כלי Python מותאמים, חבילות MCP ו-Skills בגרסת בטא. |

## בטיחות ושליטה

Smarti נבנה כך שיהיה שימושי בלי להיות פזיז. יכולות רגישות נשלטות דרך הגדרות ובקשות אישור. אפשר להגדיר רמות הרשאה, להפעיל או לכבות קבוצות כלים, לדרוש אישור לפקודות shell ולהתקנת הרחבות, להשתמש בארגז חול אופציונלי, לטשטש מידע בלוגים ולשמור סודות דרך Keyring או Windows DPAPI.

פעולות כמו כתיבת קבצים, הרצת פקודות, שליטה בשולחן העבודה, קריאת אימייל, שליחת אימייל, שימוש בצילומי מסך או העלאת תוכן מקומי למודל בענן נחשבות רגישות ויכולות לדרוש אישור מפורש מהמשתמש.

## תמיכה במודלים

Smarti יכול לעבוד עם כמה ספקי מודלים:

- Gemini
- OpenAI
- Anthropic
- OpenRouter
- Groq
- שרתים מקומיים תואמי OpenAI, כמו LM Studio

מפתחות מודל והגדרות שרת מקומי מוגדרים מתוך מסך ההגדרות באפליקציה.

## התחלה מהירה

דרישות: Windows, Python 3.10 ומעלה, ו-Git אם רוצים להשתמש בכלי Git.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python smarti_core.pyw
```

כדי להריץ ללא חלון קונסול, אפשר לפתוח את `smarti_core.pyw` ישירות מ-Windows או להשתמש בפקודה:

```powershell
pythonw smarti_core.pyw
```

## יכולות אופציונליות

- אוטומציית דפדפן דורשת Google Chrome.
- תמיכה ב-MCP דורשת Node.js ו-`npx`.
- קלט קולי דורש מיקרופון פעיל, `SpeechRecognition`, `keyboard` ו-`PyAudio`.
- OCR דורש `pytesseract`, `Pillow`, וגם את מנוע Tesseract OCR מותקן במערכת וזמין דרך `PATH`.
- הערכות עלות שימוש מועילות יותר כאשר `litellm` מותקן.

## מבנה הפרויקט

```text
smarti_core.pyw          מפעיל תאימות ונקודת הכניסה הראשית
smarti/                  קוד האפליקציה המודולרי
  app.py                 הפעלת האפליקציה, מסך פתיחה וחלון ראשי
  core.py                מנוע הסוכן, כלים, הרשאות וזרימת הרצה
  config.py              סכמות כלים מובנים והגדרות ברירת מחדל
  chat.py                ממשק צ'אט, מגש מערכת, קלט קולי והתראות
  ui_pages.py            הגדרות, כלים, משימות, שימוש, לוגים ואודות
  managers.py            הגדרות, זיכרון, MCP, Skills, מדיניות ורישומים
  workers.py             QThreads לעבודת סוכן, קול, TTS וטעינת מודלים
assets/                  לוגו, אייקונים ונכסי UI
custom_tools/            כלי Python מותאמים שהסוכן יוצר או משתמש בהם
mcp_tools/               Wrappers לכלי MCP מותקנים
skills/                  Skills מותקנים
Smarti_Outputs/          תיקיית פלט ברירת מחדל
```

## נתונים מקומיים

Smarti שומר הגדרות, נתוני שימוש, זיכרון ולוגים בקבצים מקומיים כמו `smarti_settings.json`, `smarti_memory.json`, `smarti_usage.json`, `smarti_agent.log` ו-`smarti_audit.log`. קבצים רגישים וקבצים שנוצרים בזמן עבודה מופיעים ב-`.gitignore` כדי שלא ייכנסו בטעות ל-commit.

## רישיון

הפרויקט מופץ תחת הרישיון שמופיע בקובץ `LICENSE`.
