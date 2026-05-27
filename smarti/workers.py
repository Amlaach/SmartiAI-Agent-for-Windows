"""Qt worker threads for agent, speech, TTS, and model loading."""
from .common import *

# ==========================================
# תהליכי רקע (QThreads) ל-GUI למניעת קפיאות
# ==========================================
class AgentWorker(QThread):
    finished_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    ask_confirm_signal = pyqtSignal(str, str)
    api_key_required_signal = pyqtSignal(str, str, str, str, str)
    step_signal = pyqtSignal(str)

    def __init__(self, core, user_text):
        super().__init__()
        self.core = core
        self.user_text = user_text
        self.confirm_event = threading.Event()
        self.confirm_result = False
        self.api_key_event = threading.Event()
        self.api_key_result = ""

    def ask_user_gui(self, title, text):
        self.confirm_result = False
        self.confirm_event.clear()
        self.ask_confirm_signal.emit(title, text)
        while not self.confirm_event.wait(0.1):
            if self.core._is_cancel_requested():
                return False
        return self.confirm_result

    def ask_api_key_gui(self, secret_key, provider_label, title, message, help_url):
        self.api_key_result = ""
        self.api_key_event.clear()
        self.api_key_required_signal.emit(secret_key, provider_label, title, message, help_url)
        while not self.api_key_event.wait(0.1):
            if self.core._is_cancel_requested():
                return ""
        return self.api_key_result

    def run(self):
        self.core.set_callbacks(
            status_cb=lambda msg: self.status_signal.emit(msg), 
            print_cb=self.core.print_callback,
            ask_user_cb=self.ask_user_gui,
            step_cb=lambda msg: self.step_signal.emit(msg),
            api_key_cb=self.ask_api_key_gui
        )
        try:
            response = self.core.send_message(self.user_text)
        except Exception as e:
            logging.exception("Agent worker crashed unexpectedly.")
            self.core._recover_after_agent_crash()
            response = f"ERROR_USER: אירעה תקלה פנימית במהלך ביצוע הפעולה. הפרטים נשמרו בלוגים לצורך בדיקה.\n{e}"
        self.finished_signal.emit(response)

class VoiceWorker(QThread):
    finished_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def run(self):
        if not SPEECH_INSTALLED:
            self.finished_signal.emit("")
            return
        try:
            import speech_recognition as sr
        except ImportError:
            self.finished_signal.emit("")
            return
        r = sr.Recognizer()
        r.pause_threshold = 2.0  
        try:
            with sr.Microphone() as source:
                try: winsound.Beep(1000, 150)
                except: pass
                self.status_signal.emit("מקשיב...")
                try: audio = r.listen(source, timeout=10, phrase_time_limit=45)
                except sr.WaitTimeoutError:
                    self.finished_signal.emit("")
                    return
                try: winsound.Beep(800, 150)
                except: pass
                self.status_signal.emit("מתמלל...")
                text = r.recognize_google(audio, language="he-IL").replace("סמרטי", "סמארטי").replace("סמארט", "סמארטי")
                self.finished_signal.emit(text)
        except Exception: self.finished_signal.emit("")

class TTSWorker(QThread):
    def __init__(self, core, text):
        super().__init__()
        self.core = core
        self.text = text
    def run(self): self.core.speak_text(self.text)

class FetchModelsWorker(QThread):
    finished_signal = pyqtSignal(list)
    def __init__(self, provider, api_key, url, allow_insecure_ssl=False):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.url = url
        self.allow_insecure_ssl = bool(allow_insecure_ssl)

    def _request_kwargs(self):
        if self.allow_insecure_ssl:
            try:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except Exception:
                pass
            return {"verify": False}
        return {}

    def run(self):
        models = []
        try:
            if self.provider == "gemini":
                if not self.api_key: return self.finished_signal.emit([])
                models_url = get_url(URL_GEMINI_MODELS).split("?key=", 1)[0]
                res = requests.get(models_url, headers={"x-goog-api-key": self.api_key}, timeout=10, **self._request_kwargs())
                if res.status_code == 200: models = [m['name'].replace('models/', '') for m in res.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            elif self.provider == "openai":
                if not self.api_key: return self.finished_signal.emit([])
                res = requests.get(get_url(URL_OPENAI_MODELS), headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10, **self._request_kwargs())
                if res.status_code == 200: models = sorted([m['id'] for m in res.json().get('data', []) if "gpt" in m['id'] or "o1" in m['id'] or "o3" in m['id']], reverse=True)
            elif self.provider == "anthropic": models = ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]
            elif self.provider == "openrouter":
                res = requests.get(get_url(URL_OPENROUTER_MODELS), timeout=10, **self._request_kwargs())
                if res.status_code == 200: models = [m['id'] for m in res.json().get('data', [])]
            elif self.provider == "groq":
                if not self.api_key: return self.finished_signal.emit([])
                res = requests.get(get_url(URL_GROQ_MODELS), headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10, **self._request_kwargs())
                if res.status_code == 200: models = [m['id'] for m in res.json().get('data', [])]
            elif self.provider == "local":
                res = requests.get(f"{self.url}/models", timeout=5, **self._request_kwargs())
                if res.status_code == 200: models = [m['id'] for m in res.json().get('data', [])]
        except Exception: pass
        self.finished_signal.emit(models)


__all__ = [name for name in globals() if not name.startswith("__")]
