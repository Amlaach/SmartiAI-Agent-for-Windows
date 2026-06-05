# SmartiAI Agent for Windows

עברית: [מעבר לגרסה העברית](#עברית)

SmartiAI Agent for Windows is a desktop AI agent built for practical work on a Windows computer. It is more than a chat window: Smarti can plan tasks, use local tools, inspect files, work with the web, automate browser and desktop actions, manage email, remember useful context, and ask for approval before sensitive operations.

The goal is simple: give the user a capable assistant that can help operate the computer while staying transparent, configurable, and under the user's control.

Current release target: `V0.68.0`.

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
- DeepSeek
- Alibaba Qwen / DashScope
- Zhipu GLM
- Moonshot Kimi
- Mistral AI
- Together AI
- Perplexity
- xAI
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

## Building a Windows Release

The source tree stays clean in Git. Build artifacts and downloaded runtimes are ignored; only the repeatable release recipe is tracked.

```powershell
.\scripts\build_release.ps1 -Version 0.68.0
```

The build creates a PyInstaller `SmartiAI.exe` with the `assets\smarti.ico` application icon, copies the required assets, and adds private runtimes under `runtime\python` and `runtime\node`. Packaged Smarti uses those private runtimes for custom Python tools, MCP packages, and Skill requirement installs. Source runs continue to use Python and Node from the developer machine. The release script also runs `pip check` for the build environment and private Python runtime, verifies the expected release layout, and checks installer path lengths before packaging.

Outputs are written to `release\`: a portable ZIP is always created, and a setup EXE is created when Inno Setup 6 is installed. The installer is per-user by default (`%LOCALAPPDATA%\SmartiAI`) so Smarti can keep installing dynamic tools without administrator rights. Existing installs may keep using their previous app directory during silent upgrades.

## Automatic Updates

Smarti checks GitHub Releases for the latest release, compares the tag against the app version, and downloads the attached Windows setup EXE when a newer version is available. For `V0.68.0`, publish a GitHub release tagged `V0.68.0` or `0.68.0`, attach `SmartiAI-Agent-for-Windows-0.68.0-Setup.exe`, and also attach `SmartiAI-Agent-for-Windows-0.68.0-win-x64-portable.zip` for manual portable installs.

## Optional Capabilities

- Browser automation requires Google Chrome.
- MCP support requires Node.js and `npx` only when running from source. Packaged releases include a private Node.js runtime.
- Voice input requires a working microphone, `SpeechRecognition`, `keyboard`, and `PyAudio`.
- OCR requires `pytesseract`, `Pillow`, and the Tesseract OCR engine installed on the system and available in `PATH`.
- Usage-cost estimates are more useful when `litellm` is installed.

## Project Structure

```text
smarti_core.pyw          Compatibility launcher and main entry point
smarti/                  Modular application code
  app.py                 App startup, splash screen, and main window
  core.py                Agent engine, tools, permissions, and execution flow
  runtime.py             Source vs packaged runtime and toolchain resolution
  config.py              Built-in tool schemas and default settings
  chat.py                Chat UI, tray behavior, voice input, and notifications
  ui_pages.py            Settings, tools, tasks, usage, logs, and about pages
  managers.py            Settings, memory, MCP, Skills, policy, and registries
  workers.py             QThreads for agent work, voice, TTS, and model loading
assets/                  Logo, icons, and UI assets
packaging/               PyInstaller, installer, and runtime version recipe
scripts/                 Release build and private runtime preparation scripts
```

## Local Data

Smarti stores settings, usage data, memory, and logs in local files such as `smarti_settings.json`, `smarti_memory.json`, `smarti_usage.json`, `smarti_agent.log`, and `smarti_audit.log`. Sensitive and generated files are listed in `.gitignore` so they are not committed by accident.

On Windows, new installs store runtime data under `%APPDATA%\SmartiAI` by default. Generated output files go to `Documents\Smarti_Outputs` when the Documents folder exists. Legacy project-root runtime files are copied forward on first run and left in place.

## License

This project is distributed under the license included in `LICENSE`.

---

## עברית

SmartiAI Agent for Windows הוא סוכן AI שולחני שנועד לעבודה מעשית על מחשב Windows. הוא לא רק חלון צ'אט: Smarti יכול לתכנן משימות, להשתמש בכלים מקומיים, לבדוק קבצים, לעבוד עם האינטרנט, לבצע אוטומציה בדפדפן ובשולחן העבודה, לנהל אימייל, לזכור הקשר שימושי ולבקש אישור לפני פעולות רגישות.

המטרה פשוטה: לתת למשתמש עוזר חזק שיכול לעזור להפעיל את המחשב, תוך שקיפות, אפשרות הגדרה ושליטה מלאה של המשתמש.

יעד הגרסה הנוכחי: `V0.68.0`.

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
- DeepSeek
- Alibaba Qwen / DashScope
- Zhipu GLM
- Moonshot Kimi
- Mistral AI
- Together AI
- Perplexity
- xAI
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

## בניית הפצה ל-Windows

עץ המקור נשאר נקי ב-Git. קבצי build, חבילות release וסביבות runtime שהורדו מוחרגים, ורק מתכון הבנייה נשמר במאגר.

```powershell
.\scripts\build_release.ps1 -Version 0.68.0
```

הבנייה יוצרת `SmartiAI.exe` עם PyInstaller ועם אייקון היישום `assets\smarti.ico`, מעתיקה את נכסי הממשק, ומוסיפה runtimes פרטיים תחת `runtime\python` ו-`runtime\node`. גרסה ארוזה של Smarti משתמשת בהם עבור כלי Python דינמיים, חבילות MCP והתקנת דרישות של Skills. בהרצה מהמקור Smarti ממשיך להשתמש ב-Python וב-Node שמותקנים במחשב הפיתוח. סקריפט ההפצה גם מריץ `pip check` לסביבת הבנייה ול-Python הפרטי, מאמת את מבנה חבילת ההפצה, ובודק אורכי נתיבים לפני יצירת החבילות.

התוצרים נכתבים אל `release\`: תמיד נוצר ZIP נייד, ונוצר גם קובץ התקנה כאשר Inno Setup 6 מותקן. ברירת המחדל של ההתקנה היא פר-משתמש (`%LOCALAPPDATA%\SmartiAI`), כדי ש-Smarti יוכל להמשיך להתקין כלים דינמיים בלי הרשאות מנהל. התקנות קיימות עשויות להמשיך להשתמש בתיקיית ההתקנה הקודמת בזמן עדכון שקט.

## עדכונים אוטומטיים

Smarti בודק את GitHub Releases, משווה את תגית הגרסה לגרסת האפליקציה, ומוריד את קובץ ה-Setup של Windows כאשר קיימת גרסה חדשה יותר. עבור `V0.68.0`, יש לפרסם GitHub Release עם תגית `V0.68.0` או `0.68.0`, לצרף את `SmartiAI-Agent-for-Windows-0.68.0-Setup.exe`, ולצרף גם את `SmartiAI-Agent-for-Windows-0.68.0-win-x64-portable.zip` להתקנה ידנית ניידת.

## יכולות אופציונליות

- אוטומציית דפדפן דורשת Google Chrome.
- תמיכה ב-MCP דורשת Node.js ו-`npx` רק בהרצה מהמקור. חבילות הפצה כוללות runtime פרטי של Node.js.
- קלט קולי דורש מיקרופון פעיל, `SpeechRecognition`, `keyboard` ו-`PyAudio`.
- OCR דורש `pytesseract`, `Pillow`, וגם את מנוע Tesseract OCR מותקן במערכת וזמין דרך `PATH`.
- הערכות עלות שימוש מועילות יותר כאשר `litellm` מותקן.

## מבנה הפרויקט

```text
smarti_core.pyw          מפעיל תאימות ונקודת הכניסה הראשית
smarti/                  קוד האפליקציה המודולרי
  app.py                 הפעלת האפליקציה, מסך פתיחה וחלון ראשי
  core.py                מנוע הסוכן, כלים, הרשאות וזרימת הרצה
  runtime.py             זיהוי מצב מקור/הפצה ופתרון runtimes לכלים
  config.py              סכמות כלים מובנים והגדרות ברירת מחדל
  chat.py                ממשק צ'אט, מגש מערכת, קלט קולי והתראות
  ui_pages.py            הגדרות, כלים, משימות, שימוש, לוגים ואודות
  managers.py            הגדרות, זיכרון, MCP, Skills, מדיניות ורישומים
  workers.py             QThreads לעבודת סוכן, קול, TTS וטעינת מודלים
assets/                  לוגו, אייקונים ונכסי UI
packaging/               מתכון PyInstaller, התקנה וגרסאות runtime
scripts/                 סקריפטי בנייה והכנת runtime פרטי
```

## נתונים מקומיים

Smarti שומר הגדרות, נתוני שימוש, זיכרון ולוגים בקבצים מקומיים כמו `smarti_settings.json`, `smarti_memory.json`, `smarti_usage.json`, `smarti_agent.log` ו-`smarti_audit.log`. קבצים רגישים וקבצים שנוצרים בזמן עבודה מופיעים ב-`.gitignore` כדי שלא ייכנסו בטעות ל-commit.

ב-Windows, התקנות חדשות שומרות נתוני Runtime תחת `%APPDATA%\SmartiAI` כברירת מחדל. קבצי פלט נוצרים תחת `Documents\Smarti_Outputs` כאשר תיקיית Documents קיימת. קבצי Runtime ישנים משורש הפרויקט מועתקים קדימה בהפעלה הראשונה ונשארים במקומם.

## רישיון

הפרויקט מופץ תחת הרישיון שמופיע בקובץ `LICENSE`.
