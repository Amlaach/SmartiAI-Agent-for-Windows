# SmartiAI Agent for Windows

עברית: [מעבר לגרסה העברית](#עברית)

SmartiAI Agent for Windows is a desktop AI assistant for Windows. It combines a clean Hebrew-first chat interface with practical local tools for files, system tasks, web access, email, automation, memory, and extensibility. The project is designed for everyday desktop work, with explicit permission controls around sensitive actions.

## Highlights

- Native Windows desktop app built with PyQt6, including a polished chat window, tray notifications, splash screen, light/dark/auto themes, and right-to-left Hebrew support.
- Model support for Gemini, OpenAI, Anthropic, OpenRouter, Groq, and local OpenAI-compatible servers such as LM Studio.
- Multi-step agent workflow with visible action steps, cancellable runs, conversation context, and a final response verification pass.
- Controlled system tools for PowerShell commands, project checks, read-only Git status/diff/log/show, process listing, clipboard updates, and audio mute/unmute.
- File tools for safe opening, text-file creation, local document reading, filename search, content search, screenshot saving, and optional OCR.
- Web tools for internet search, webpage reading, browser opening, and weather forecasts through open services.
- Browser automation through a dedicated Chrome profile and Selenium, including page-state extraction and interactive element discovery.
- Windows desktop automation through Microsoft UI Automation, with a controlled keyboard/mouse fallback when needed.
- IMAP/SMTP email support for searching, reading, sending, drafts, replies, forwarding, flags, archive, delete, folders, and attachments.
- Local structured memory with user, short-term, long-term, and tool memories, including TTL, relevance search, and Markdown export.
- Background tasks for scheduled one-time or repeated work, with task listing, cancellation, and retry.
- Extension support through custom Python tools, MCP packages installed through NPM, and beta Skills.
- Safety and privacy controls including permission levels, per-capability policy settings, approval prompts, optional sandboxing, audit logs, log redaction, and secret storage through Keyring or Windows DPAPI.
- Management screens for model settings, permissions, tools, background tasks, usage statistics, estimated costs, developer trace, logs, and about information.

## Quick Start

Requirements: Windows, Python 3.10 or newer, and Git if you want to use the Git tools.

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

## First-Time Setup

1. Open the settings screen from the app menu.
2. Choose a model provider: Gemini, OpenAI, Anthropic, OpenRouter, Groq, or Local.
3. Enter the relevant API key or local server URL.
4. Configure permissions, system tools, automations, email, MCP/Skills, and the output folder.
5. For sensitive actions, Smarti asks for approval before running commands, writing files, uploading content to a cloud model, using email, or controlling the computer.

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

SmartiAI Agent for Windows הוא עוזר AI שולחני ל-Windows. הוא משלב ממשק צ'אט נקי שמותאם לעברית עם כלים מעשיים לעבודה מקומית: קבצים, משימות מערכת, אינטרנט, אימייל, אוטומציה, זיכרון והרחבות. הפרויקט מיועד לעבודה יומיומית על המחשב, עם בקרת הרשאות מפורשת סביב פעולות רגישות.

## נקודות עיקריות

- אפליקציית Windows מקומית שנבנתה עם PyQt6, כולל חלון צ'אט מלוטש, התראות מגש מערכת, מסך פתיחה, מצבי תצוגה בהיר/כהה/אוטומטי ותמיכה בעברית מימין לשמאל.
- תמיכה במודלים דרך Gemini, OpenAI, Anthropic, OpenRouter, Groq ושרתים מקומיים תואמי OpenAI כמו LM Studio.
- תהליך עבודה מרובה שלבים לסוכן, עם שלבי פעולה גלויים, אפשרות לעצור ריצה, הקשר שיחה ואימות סופי של התשובה.
- כלי מערכת מבוקרים לפקודות PowerShell, בדיקות פרויקט, פעולות Git לקריאה בלבד כגון status/diff/log/show, רשימת תהליכים, עדכון לוח העתקה והשתקה/ביטול השתקה של שמע.
- כלי קבצים לפתיחה בטוחה, יצירת קובצי טקסט, קריאת מסמכים מקומיים, חיפוש לפי שם קובץ, חיפוש בתוך תוכן, שמירת צילומי מסך ו-OCR אופציונלי.
- כלי אינטרנט לחיפוש ברשת, קריאת דפי אתר, פתיחה בדפדפן ותחזית מזג אוויר דרך שירותים פתוחים.
- אוטומציית דפדפן דרך פרופיל Chrome ייעודי ו-Selenium, כולל חילוץ מצב הדף וזיהוי אלמנטים אינטראקטיביים.
- אוטומציית שולחן עבודה של Windows דרך Microsoft UI Automation, עם fallback מבוקר למקלדת/עכבר בעת הצורך.
- תמיכה באימייל דרך IMAP/SMTP לחיפוש, קריאה, שליחה, טיוטות, מענה, העברה, סימונים, ארכוב, מחיקה, תיקיות וקבצים מצורפים.
- זיכרון מקומי מובנה עם זיכרונות משתמש, טווח קצר, טווח ארוך וכלים, כולל TTL, חיפוש לפי רלוונטיות וייצוא ל-Markdown.
- משימות רקע לעבודה מתוזמנת חד-פעמית או חוזרת, עם הצגת משימות, ביטול והרצה מחדש.
- תמיכה בהרחבות דרך כלי Python מותאמים אישית, חבילות MCP שמותקנות דרך NPM, ושכבת Skills בגרסת בטא.
- בקרות אבטחה ופרטיות הכוללות רמות הרשאה, מדיניות לפי יכולת, בקשות אישור, ארגז חול אופציונלי, לוג Audit, הסתרת מידע רגיש בלוגים ושמירת סודות דרך Keyring או Windows DPAPI.
- מסכי ניהול להגדרות מודלים, הרשאות, כלים, משימות רקע, נתוני שימוש, עלויות משוערות, Developer Trace, לוגים ומידע אודות.

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

## הגדרה ראשונית

1. פתחו את מסך ההגדרות מתוך תפריט האפליקציה.
2. בחרו ספק מודל: Gemini, OpenAI, Anthropic, OpenRouter, Groq או Local.
3. הזינו את מפתח ה-API הרלוונטי או כתובת שרת מקומי.
4. הגדירו הרשאות, כלי מערכת, אוטומציות, אימייל, MCP/Skills ותיקיית פלט.
5. בפעולות רגישות, Smarti יבקש אישור לפני הרצת פקודות, כתיבת קבצים, העלאת תוכן למודל בענן, שימוש באימייל או שליטה במחשב.

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
