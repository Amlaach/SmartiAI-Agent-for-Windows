"""Chat bubbles, notifications, main window, and splash screen."""
from .common import *
from .ui_styles import *
from .ui_controls import *
from .workers import AgentWorker, VoiceWorker, TTSWorker
from .ui_pages import ActionConfirmDialog, ApiKeyRequiredDialog, UsageStatsPage, TaskCenterPage, DeveloperTracePage, ToolsSettingsPage, SettingsPage, AboutPage

def _asset_icon(*filenames):
    for filename in filenames:
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon
    return QIcon()

def _escape_with_soft_breaks(text):
    raw = html.unescape(str(text or ""))
    token_re = re.compile(r'(?:[A-Za-z]:\\|\\\\|/|https?://|www\.)[^\s<>{}]{12,}|[^\s<>{}]{42,}')
    parts = []
    last = 0
    for match in token_re.finditer(raw):
        parts.append(html.escape(raw[last:match.start()]))
        token = html.escape(match.group(0))
        for marker in ("\\", "/", "_", "-", ".", ":", "="):
            token = token.replace(marker, marker + "&#8203;")
        parts.append(token)
        last = match.end()
    parts.append(html.escape(raw[last:]))
    return "".join(parts)

def _clean_step_for_display(text):
    clean = html.unescape(str(text or "")).strip()
    clean = re.sub(r'```.*?```', '', clean, flags=re.DOTALL).strip()
    if "tools/call" in clean or re.search(r'(?i)"method"\s*:\s*"(?:tools/call|agent_[^"]*|agent_planner)"', clean):
        clean = clean.split("{", 1)[0].strip()
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

class PillInputFrame(QFrame):
    CORNER_RADIUS = 40.5

    def __init__(self):
        super().__init__()
        self.setObjectName("InputFrame")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def apply_theme(self):
        self.setStyleSheet("background: transparent; border: none;")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = min(self.CORNER_RADIUS, rect.height() / 2.0, rect.width() / 2.0)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self._hovered:
            painter.fillPath(path, QColor(FIELD_HOVER_COLOR))
            border_color = QColor(LINE_COLOR)
        else:
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(GLASS_STRONG_COLOR))
            gradient.setColorAt(1.0, QColor(INPUT_GRADIENT_END))
            painter.fillPath(path, QBrush(gradient))
            border_color = QColor(SOFT_LINE_COLOR)

        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        painter.end()

class PinnedActionButtonHost(QWidget):
    BOTTOM_GAP = 7

    def __init__(self, button):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedWidth(button.width())
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, self.BOTTOM_GAP)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)

class MessageBubble(QFrame):
    def __init__(self, text, is_user=False, parent_width=450):
        super().__init__()
        self.is_user = is_user
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.max_w = int(parent_width * 0.76) - 30
        self.copy_text = str(text or "")
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 5)
        self.steps_layout.setSpacing(4)
        
        self.toggle_btn = QPushButton("▼ שלבי פעולה")
        self.toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_btn.clicked.connect(self.toggle_steps)
        
        self.steps_label = StepsShimmerLabel()
        self.steps_label.setTextFormat(Qt.TextFormat.RichText)
        self.steps_label.setWordWrap(True)
        self.steps_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.steps_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.steps_label.setMaximumWidth(self.max_w)
        
        self.steps_layout.addWidget(self.toggle_btn)
        self.steps_layout.addWidget(self.steps_label)
        self.steps_container.hide() 
        
        self.final_label = QLabel()
        self.final_label.setTextFormat(Qt.TextFormat.RichText)
        self.final_label.setWordWrap(True)
        self.final_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.final_label.setOpenExternalLinks(True)
        self.final_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.final_label.setMaximumWidth(self.max_w)
        
        self.main_layout.addWidget(self.steps_container)
        self.main_layout.addWidget(self.final_label)
        
        self.steps_text_html = ""
        self.is_expanded = True 
        
        if text: self.set_final_text(text)
        else: self.final_label.hide()
        self.apply_theme()

    def apply_theme(self):
        bg = (
            USER_BUBBLE_COLOR
            if self.is_user
            else f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {GLASS_STRONG_COLOR}, stop:1 {BUBBLE_AGENT_END})"
        )
        color = BUBBLE_USER_TEXT if self.is_user else TEXT_COLOR
        radius = "24px"
        border = f"1px solid {USER_BUBBLE_BORDER if self.is_user else SOFT_LINE_COLOR}"

        self.toggle_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {ACCENT_COLOR}; border: none; "
            f"text-align: right; font-weight: 700; font-size: 13px; padding: 2px; }}"
            f"QPushButton:hover {{ color: {ACCENT_SECONDARY_COLOR}; }}"
        )
        self.steps_label.setStyleSheet(
            f"color: {MUTED_TEXT_COLOR}; font-size: 13px; background: {ACCENT_TINT}; "
            f"padding: 10px; border: none; border-radius: 10px;"
        )
        self.setStyleSheet(
            f"MessageBubble {{ background: {bg}; border: {border}; border-radius: {radius}; margin: 5px 0px; }}"
            f"QLabel {{ color: {color}; font-size: 15px; font-family: 'Segoe UI', Arial; background: transparent; }}"
            f"a {{ color: {ACCENT_COLOR}; text-decoration: underline; }}"
            f"code {{ background-color: {CODE_BG_COLOR}; padding: 2px 4px; border-radius: 4px; font-family: Consolas; }}"
            f"pre {{ background-color: {CODE_BG_COLOR}; padding: 12px; border-radius: 14px; margin: 0; }}"
            f"p {{ margin: 0 0 5px 0; }}"
        )
        apply_soft_shadow(self, blur=22, y=7, alpha=30)

    def update_parent_width(self, parent_width):
        self.max_w = max(220, int(parent_width * 0.76) - 30)
        self.steps_label.setMaximumWidth(self.max_w)
        self.final_label.setMaximumWidth(self.max_w)
        self._refresh_layout()

    def _refresh_layout(self):
        self.updateGeometry()
        parent = self.parentWidget()
        if parent:
            parent.updateGeometry()

    def add_step(self, step_text):
        display_step = _clean_step_for_display(str(step_text or "").replace('\n', ' '))
        if "{" in display_step and "}" in display_step:
            display_step = display_step.split("{", 1)[0].strip()
        clean_step = _escape_with_soft_breaks(display_step)
        if not clean_step: return
        if not self.copy_text:
            self.copy_text = display_step
        self.steps_text_html += f"<div style='margin-bottom: 2px; word-wrap: break-word;'>• {clean_step}</div>"
        self.steps_label.setText(self.steps_text_html)
        self.steps_container.show()
        self.start_steps_shimmer()
        if not self.is_expanded: self.toggle_steps() 
        self._refresh_layout()
            
    def set_final_text(self, final_text):
        if not final_text: return
        display_text = html.unescape(str(final_text))
        self.copy_text = display_text
        self.stop_steps_shimmer()
        self.final_label.show()
        safe_text = _escape_with_soft_breaks(display_text)
        if MARKDOWN_INSTALLED and not self.is_user:
            try:
                import markdown
                rendered_html = markdown.markdown(safe_text, extensions=['fenced_code', 'tables', 'nl2br'])
            except Exception:
                rendered_html = safe_text.replace('\n', '<br>')
        else:
            rendered_html = safe_text.replace('\n', '<br>')
        if not rendered_html.lstrip().startswith("<"):
            rendered_html = f"<span>{rendered_html}</span>"
        self.final_label.setText(rendered_html)
        if self.steps_text_html: self.collapse_steps()
        self._refresh_layout()

    def toggle_steps(self):
        self.is_expanded = not self.is_expanded
        self.steps_label.setVisible(self.is_expanded)
        self._refresh_layout()
        self.toggle_btn.setText("▲ שלבי פעולה" if self.is_expanded else "▼ שלבי פעולה")

    def collapse_steps(self):
        self.is_expanded = False
        self.steps_label.hide()
        self._refresh_layout()
        self.toggle_btn.setText("▼ שלבי פעולה")

    def start_steps_shimmer(self):
        # Agent-step shimmer is disabled by default.
        # Re-enable it by uncommenting the next line.
        # self.steps_label.start_shimmer()
        pass

    def stop_steps_shimmer(self):
        self.steps_label.stop_shimmer()

    def plain_text(self):
        return self.copy_text or self.final_label.text() or self.steps_label.text()

class ChatMessageContainer(QWidget):
    tts_button_clicked = pyqtSignal(object)

    def __init__(self, text, is_user=False, parent_width=450):
        super().__init__()
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("background: transparent;")
        self.bubble = MessageBubble(text, is_user, parent_width)
        self.is_user = is_user
        self._tts_active = False
        self._tts_blocked = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.content_wrap = QWidget()
        self.content_wrap.setStyleSheet("background: transparent;")
        self.content_wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.content_wrap)

        layout = QVBoxLayout(self.content_wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bubble_row = QHBoxLayout()
        bubble_row.setContentsMargins(0, 0, 0, 0)
        if is_user:
            bubble_row.addWidget(self.bubble)
            bubble_row.addStretch()
        else:
            bubble_row.addStretch()
            bubble_row.addWidget(self.bubble)
        layout.addLayout(bubble_row)

        self.actions_container = QWidget()
        self.actions_container.setMouseTracking(True)
        self.actions_container.setFixedHeight(28)
        self.actions_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.actions_container.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(self.actions_container)
        actions_layout.setContentsMargins(12, 0, 12, 0)
        actions_layout.setSpacing(4)

        self.copy_btn = QPushButton()
        self.copy_btn.setFixedSize(24, 24)
        self.copy_btn.setToolTip("העתק")
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_icon_path = os.path.join(ASSETS_DIR, "copy_icon.png")
        if os.path.exists(copy_icon_path):
            self.copy_btn.setIcon(QIcon(copy_icon_path))
            self.copy_btn.setIconSize(QSize(15, 15))
        else:
            self.copy_btn.setText("⧉")
        self.copy_btn.clicked.connect(self.copy_message_text)

        self.tts_btn = None
        self.tts_read_icon = QIcon()
        self.tts_stop_icon = QIcon()
        if not is_user:
            self.tts_read_icon = _asset_icon(f"read_aloud_icon_{CURRENT_THEME}.png", "read_aloud_icon.png", "speaker_icon.png", "tts_icon.png")
            self.tts_stop_icon = _asset_icon(f"stop_reading_icon_{CURRENT_THEME}.png", "stop_reading_icon.png", "stop_audio_icon.png", "stop_icon.png")
            self.tts_btn = QPushButton()
            self.tts_btn.setFixedSize(24, 24)
            self.tts_btn.setToolTip("Read aloud")
            self.tts_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.tts_btn.clicked.connect(lambda checked=False: self.tts_button_clicked.emit(self))

        if is_user:
            actions_layout.addWidget(self.copy_btn)
            actions_layout.addStretch()
        else:
            actions_layout.addStretch()
            actions_layout.addWidget(self.copy_btn)
            actions_layout.addWidget(self.tts_btn)

        self.actions_opacity = QGraphicsOpacityEffect(self.actions_container)
        self.actions_opacity.setOpacity(1.0)
        self.actions_container.setGraphicsEffect(self.actions_opacity)
        layout.addWidget(self.actions_container)

        self.opacity_anim = QPropertyAnimation(self.actions_opacity, b"opacity", self)
        self.opacity_anim.setDuration(240)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._entry_started = False
        self._entry_pending = False
        self._enter_opacity = None
        self._enter_anim = None
        self._enter_slide_anim = None
        self.apply_theme()

    def _button_css(self, active=False):
        color = DANGER_COLOR if active else MUTED_TEXT_COLOR
        hover = "rgba(240,90,110,0.16)" if active else ACCENT_TINT
        pressed = "rgba(240,90,110,0.24)" if active else ACCENT_TINT_STRONG
        return (
            f"QPushButton {{ background: transparent; color: {color}; border: none; "
            f"padding: 0px; border-radius: 12px; font-size: 13px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {hover}; color: {TEXT_COLOR}; }}"
            f"QPushButton:pressed {{ background: {pressed}; }}"
            f"QPushButton:disabled {{ background: transparent; color: {SUBTLE_TEXT_COLOR}; }}"
        )

    def apply_theme(self):
        self.setStyleSheet("background: transparent;")
        self.actions_container.setStyleSheet("background: transparent;")
        self.copy_btn.setStyleSheet(self._button_css(False))
        if self.tts_btn:
            self.tts_read_icon = _asset_icon(f"read_aloud_icon_{CURRENT_THEME}.png", "read_aloud_icon.png", "speaker_icon.png", "tts_icon.png")
            self.tts_stop_icon = _asset_icon(f"stop_reading_icon_{CURRENT_THEME}.png", "stop_reading_icon.png", "stop_audio_icon.png", "stop_icon.png")
        self.update_tts_button_state(self._tts_active, self._tts_blocked)
        if hasattr(self, "bubble") and self.bubble:
            self.bubble.apply_theme()

    def update_tts_button_state(self, active=False, blocked=False):
        if not self.tts_btn:
            return
        self._tts_active = bool(active)
        self._tts_blocked = bool(blocked)
        self.tts_btn.setEnabled(not blocked or active)
        icon = self.tts_stop_icon if active else self.tts_read_icon
        if not icon.isNull():
            self.tts_btn.setIcon(icon)
            self.tts_btn.setIconSize(QSize(15, 15))
            self.tts_btn.setText("")
        else:
            self.tts_btn.setIcon(QIcon())
            self.tts_btn.setText("X" if active else "A")
        self.tts_btn.setToolTip("Stop reading" if active else "Read aloud")
        self.tts_btn.setStyleSheet(self._button_css(active))

    def start_entry_animation(self):
        self._entry_pending = False
        if self._entry_started or not self.isVisible():
            return
        self._entry_started = True

        self._enter_opacity = QGraphicsOpacityEffect(self.content_wrap)
        self._enter_opacity.setOpacity(0.0)
        self.content_wrap.setGraphicsEffect(self._enter_opacity)

        self._enter_anim = QPropertyAnimation(self._enter_opacity, b"opacity", self)
        self._enter_anim.setDuration(360)
        self._enter_anim.setStartValue(0.0)
        self._enter_anim.setEndValue(1.0)
        self._enter_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        end_pos = self.content_wrap.pos()
        start_pos = end_pos + QPoint(0, 18)
        self.content_wrap.move(start_pos)
        self._enter_slide_anim = QPropertyAnimation(self.content_wrap, b"pos", self)
        self._enter_slide_anim.setDuration(360)
        self._enter_slide_anim.setStartValue(start_pos)
        self._enter_slide_anim.setEndValue(end_pos)
        self._enter_slide_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def cleanup():
            self.content_wrap.move(end_pos)
            self.content_wrap.setGraphicsEffect(None)
            self.updateGeometry()

        self._enter_anim.finished.connect(cleanup)
        self._enter_slide_anim.start()
        self._enter_anim.start()

    def reveal_with_entry_animation(self):
        self.show()
        if self._entry_started or self._entry_pending:
            return
        self._entry_pending = True
        QTimer.singleShot(0, self.start_entry_animation)

    def enterEvent(self, event):
        self._set_actions_visible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_actions_visible(True)
        super().leaveEvent(event)

    def _set_actions_visible(self, visible):
        self.opacity_anim.stop()
        self.actions_opacity.setOpacity(1.0)

    def copy_message_text(self):
        QApplication.clipboard().setText(self.bubble.plain_text())

# Disabled fallback prototype for a custom PyQt quick-reply popup.
# Smarti no longer instantiates or shows this widget; it is kept as a reference
# in case we ever want an app-drawn notification instead of native Windows input.
class QuickReplyToast(QWidget):
    reply_submitted = pyqtSignal(str)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedWidth(390)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL_COLOR};
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', Arial;
                border: 1px solid {SOFT_LINE_COLOR};
                border-radius: 24px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLineEdit {{
                background: {FIELD_COLOR};
                color: {FIELD_TEXT_COLOR};
                border: 1px solid {SOFT_LINE_COLOR};
                border-radius: 18px;
                padding: 10px 12px;
                font-size: 13px;
                selection-background-color: {ACCENT_TINT_STRONG};
                selection-color: {TEXT_COLOR};
            }}
            QPushButton {{
                background: transparent;
                color: {ACCENT_COLOR};
                border: none;
                border-radius: 18px;
                padding: 9px 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {ACCENT_TINT};
            }}
            QPushButton#CloseToast {{
                border: none;
                padding: 0;
                font-size: 18px;
                color: {MUTED_TEXT_COLOR};
            }}
            QPushButton#CloseToast:hover {{
                background: {ACCENT_TINT};
                color: {TEXT_COLOR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Smarti AI")
        title.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 13px; font-weight: 700;")
        title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseToast")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.hide)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.response_label = QLabel()
        self.response_label.setTextFormat(Qt.TextFormat.PlainText)
        self.response_label.setWordWrap(True)
        self.response_label.setMaximumHeight(112)
        self.response_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 13px; line-height: 1.35;")
        layout.addWidget(self.response_label)

        reply_row = QHBoxLayout()
        reply_row.setContentsMargins(0, 0, 0, 0)
        reply_row.setSpacing(8)
        self.reply_edit = QLineEdit()
        self.reply_edit.setPlaceholderText("תגובה לסמארטי")
        self.reply_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.reply_edit.returnPressed.connect(self.submit_reply)
        self.send_btn = QPushButton("שלח")
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.clicked.connect(self.submit_reply)
        reply_row.addWidget(self.reply_edit)
        reply_row.addWidget(self.send_btn)
        layout.addLayout(reply_row)

    def show_response(self, text):
        self.response_label.setText(str(text or "").strip())
        self.reply_edit.clear()
        self.adjustSize()
        self._move_to_notification_corner()
        self.show()
        self.raise_()

    def _move_to_notification_corner(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if not screen:
            return
        available = screen.availableGeometry()
        margin = 18
        size = self.sizeHint()
        width = min(self.width(), max(300, available.width() - margin * 2))
        height = min(size.height(), max(160, available.height() - margin * 2))
        self.resize(width, height)
        self.move(
            available.right() - self.width() - margin,
            available.bottom() - self.height() - margin
        )

    def submit_reply(self):
        text = self.reply_edit.text().strip()
        if not text:
            return
        self.hide()
        self.reply_submitted.emit(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

class ChatWindow(QMainWindow):
    gui_message_signal = pyqtSignal(str, bool)
    tts_status_signal = pyqtSignal(bool)

    def format_model_name(self, name):
        name = str(name).replace("-", " ").replace("_", " ")
        name = re.sub(r'(?i)\bpreview\b', '', name)
        return " ".join(name.split())

    def __init__(self, core):
        super().__init__()
        self.core = core
        self.agent_running = False
        self.current_agent_bubble = None
        self.current_agent_container = None
        self.active_tts_container = None
        self.tts_active = False
        self.tts_thread = None
        self._tts_workers = []
        
        icon_path = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(icon_path): self.tray_icon.setIcon(QIcon(icon_path))
        else:
            dummy_pixmap = QPixmap(32, 32)
            dummy_pixmap.fill(QColor(ACCENT_COLOR))
            self.tray_icon.setIcon(QIcon(dummy_pixmap))
            
        self.tray_icon.messageClicked.connect(self.bring_to_front)
        self.tray_icon.show()
        # Custom QuickReplyToast fallback is intentionally disabled.
        # self.quick_reply_toast = QuickReplyToast()
        # self.quick_reply_toast.reply_submitted.connect(self.submit_quick_reply)
        
        self.gui_message_signal.connect(self.add_message)
        self.core.print_callback = lambda txt, is_user: self.gui_message_signal.emit(txt, is_user)
        self.tts_status_signal.connect(self.on_tts_status)
        self.core.tts_status_callback = lambda is_playing: self.tts_status_signal.emit(is_playing)
        
        self.setWindowTitle("Smarti AI")
        self.setMinimumSize(380, 680)
        available = QApplication.primaryScreen().availableGeometry() if QApplication.primaryScreen() else None
        if available:
            target_w = min(450, max(380, available.width() - 40))
            target_h = min(760, max(680, available.height() - 60))
            self.resize(target_w, target_h)
            self.move(
                available.x() + max(0, (available.width() - target_w) // 2),
                available.y() + max(0, (available.height() - target_h) // 2)
            )
        else:
            self.resize(450, 760) 
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        apply_app_theme(QApplication.instance(), settings=self.core.settings)
        self.setStyleSheet(
            f"QMainWindow {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {MESH_A}, stop:0.45 {MESH_B}, stop:0.72 {MESH_C}, stop:1 {MESH_D}); }}"
        )
        
        self.stacked_widget = AnimatedStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.chat_page = MeshGradientWidget()
        self.setup_chat_page()
        self.stacked_widget.addWidget(self.chat_page)
        
        self.settings_page = None
        self.tools_page = None
        self.usage_page = None
        self.task_center_page = None
        self.trace_page = None
        self.about_page = None
        
        logging.info(f"\n{'='*50}\n--- תחילת שיחה חדשה (הפעלת תוכנה) ---\n{'='*50}")
        self.add_message("שלום! אני סמארטי, סייען ה-AI האישי שלך. איך אוכל לעזור לך היום? 😊", is_user=False)
        QTimer.singleShot(1200, self.core.resume_background_tasks)
        
        if SPEECH_INSTALLED:
            QTimer.singleShot(1500, self.register_voice_hotkey)

    def register_voice_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey('alt+v', self.trigger_voice_from_hotkey)
        except Exception as e:
            logging.warning(f"Voice hotkey registration failed: {e}")

    def _chat_page_stylesheet(self):
        return f"""
            QWidget#ChatPage {{
                background: transparent;
            }}
        """

    def _top_bar_stylesheet(self):
        return f"""
            QWidget#TopBar {{
                background: transparent;
                border: none;
            }}
        """

    def _menu_button_stylesheet(self):
        return (
            f"QPushButton {{ color: {TEXT_COLOR}; background: transparent; border: none; "
            f"border-radius: 24px; padding-bottom: 3px; }}"
            f"QPushButton:hover {{ background: {ACCENT_TINT}; }}"
            f"QPushButton:pressed {{ background: {ACCENT_TINT_STRONG}; }}"
        )

    def _chat_input_stylesheet(self):
        return (
            f"QTextEdit {{ background-color: transparent; color: {FIELD_TEXT_COLOR}; border: none; "
            f"padding: 4px 10px; font-size: 17px; font-family: 'Segoe UI'; outline: none; text-align: left; }}"
            f"QTextEdit viewport {{ background-color: transparent; border: none; }}"
            f"{SCROLLBAR_CSS}"
        )

    def refresh_themed_icons(self):
        self.mic_icon = _asset_icon(f"mic_icon_{CURRENT_THEME}.png", "mic_icon.png")
        self.send_icon = _asset_icon(f"send_icon_{CURRENT_THEME}.png", "send_icon.png")
        self.stop_agent_icon = _asset_icon(f"stop_agent_icon_{CURRENT_THEME}.png", "stop_agent_icon.png")

    def apply_theme(self, mode=None, refresh_messages=True):
        apply_app_theme(QApplication.instance(), mode=mode, settings=self.core.settings)
        self.setStyleSheet(
            f"QMainWindow {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {MESH_A}, stop:0.45 {MESH_B}, stop:0.72 {MESH_C}, stop:1 {MESH_D}); }}"
        )
        if hasattr(self, "chat_page"):
            self.chat_page.setStyleSheet(self._chat_page_stylesheet())
        if hasattr(self, "top_bar"):
            self.top_bar.setStyleSheet(self._top_bar_stylesheet())
        if hasattr(self, "menu_btn"):
            self.menu_btn.setStyleSheet(self._menu_button_stylesheet())
        if hasattr(self, "menu"):
            self.menu.setStyleSheet(menu_stylesheet())
        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(page_title_css(19))
        if hasattr(self, "subtitle"):
            self.subtitle.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 12px; font-weight: 700;")
        if hasattr(self, "header_line"):
            self.header_line.setStyleSheet("background: transparent; max-height: 0px;")
        if hasattr(self, "scroll"):
            self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }" + SCROLLBAR_CSS)
        if hasattr(self, "status_lbl"):
            self.status_lbl.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 13px; font-weight: 700; padding: 0px 15px 5px 15px;")
        if hasattr(self, "input_frame"):
            if hasattr(self.input_frame, "apply_theme"):
                self.input_frame.apply_theme()
            else:
                self.input_frame.setStyleSheet(INPUT_FRAME_CSS)
            apply_soft_shadow(self.input_frame, blur=42, y=12, alpha=42)
        if hasattr(self, "input_field"):
            self.input_field.setStyleSheet(self._chat_input_stylesheet())
        if hasattr(self, "logo_lbl"):
            logo_path = os.path.join(ASSETS_DIR, "logo.png")
            if os.path.exists(logo_path):
                pixmap = make_circular_pixmap(logo_path, 50)
                if pixmap:
                    self.logo_lbl.setPixmap(pixmap)
            self.logo_lbl.setStyleSheet("border: none; background-color: transparent;")
        if hasattr(self, "action_btn"):
            self.refresh_themed_icons()
            self.update_action_btn_visuals()
        if refresh_messages:
            for container in self.findChildren(ChatMessageContainer):
                container.apply_theme()
            self._refresh_message_tts_buttons()
        QTimer.singleShot(0, self._update_chat_bottom_padding)

    def refresh_chat_messages_async(self, batch_size=18):
        containers = list(self.findChildren(ChatMessageContainer))
        if not containers:
            return

        def apply_batch(index=0):
            for container in containers[index:index + batch_size]:
                container.apply_theme()
            next_index = index + batch_size
            if next_index < len(containers):
                QTimer.singleShot(16, lambda: apply_batch(next_index))

        QTimer.singleShot(0, apply_batch)

    def invalidate_themed_pages(self):
        for attr in ("tools_page", "usage_page", "task_center_page", "trace_page", "about_page"):
            page = getattr(self, attr, None)
            if page is not None:
                self.stacked_widget.removeWidget(page)
                page.deleteLater()
                setattr(self, attr, None)

    def setup_chat_page(self):
        self.chat_page.setObjectName("ChatPage")
        self.chat_page.setStyleSheet(self._chat_page_stylesheet())
        main_layout = QVBoxLayout(self.chat_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_bar = QWidget()
        self.top_bar = top_bar
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(64)
        top_bar.setStyleSheet(self._top_bar_stylesheet())
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 7, 15, 7)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.menu_btn.setFixedSize(48, 48)
        self.menu_btn.setToolTip("תפריט")
        self.menu_btn.setStyleSheet(self._menu_button_stylesheet())
        self.menu_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.menu = QMenu(self)
        self.menu.setStyleSheet(menu_stylesheet())
        self.menu.addAction("כלים").triggered.connect(self.show_tools_page)
        self.menu.addAction("הגדרות").triggered.connect(self.show_settings_page)
        self.menu.addAction("מרכז משימות").triggered.connect(self.show_task_center_page)
        self.menu.addAction("נתוני שימוש").triggered.connect(self.show_usage_page)
        self.menu.addAction("נקה צ'אט").triggered.connect(self.clear_chat)
        self.menu.addAction("אודות").triggered.connect(self.show_about_page)
        self.menu_btn.clicked.connect(self.show_menu)
        
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(0)
        self.title_label = QLabel("Smarti AI")
        self.title_label.setStyleSheet(page_title_css(19))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        raw_model = self.core.settings.get(f"selected_{self.core.mode}_model", "Gemini")
        self.subtitle = QLabel(self.format_model_name(raw_model))
        self.subtitle.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 12px; font-weight: 700;")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_layout.addWidget(self.title_label)
        titles_layout.addWidget(self.subtitle)
        
        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(50, 50)
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(logo_path):
            circular_pixmap = make_circular_pixmap(logo_path, 50)
            if circular_pixmap: self.logo_lbl.setPixmap(circular_pixmap)
            self.logo_lbl.setStyleSheet("border: none; background-color: transparent;")
        else:
            self.logo_lbl.setText("S")
            self.logo_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            self.logo_lbl.setStyleSheet(f"border: none; border-radius: 25px; background-color: transparent; color: {ACCENT_COLOR};")
            self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        top_layout.addWidget(self.logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        top_layout.addStretch()
        top_layout.addLayout(titles_layout)
        top_layout.addStretch()
        top_layout.addWidget(self.menu_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(top_bar)
        
        self.header_line = QFrame()
        self.header_line.setFrameShape(QFrame.Shape.HLine)
        self.header_line.setFixedHeight(0)
        self.header_line.setStyleSheet("background: transparent; max-height: 0px;")
        main_layout.addWidget(self.header_line)

        self.chat_body = QWidget()
        self.chat_body.setStyleSheet("background: transparent;")
        body_layout = QGridLayout(self.chat_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }" + SCROLLBAR_CSS) 
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setContentsMargins(12, 14, 12, 128)
        self.chat_layout.setSpacing(8)
        self.scroll.setWidget(self.chat_widget)
        body_layout.addWidget(self.scroll, 0, 0)
        
        self.input_overlay = QWidget()
        self.input_overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.input_overlay.setStyleSheet("background: transparent;")
        overlay_layout = QVBoxLayout(self.input_overlay)
        overlay_layout.setContentsMargins(18, 0, 18, 18)
        overlay_layout.setSpacing(4)

        self.status_lbl = ShimmerLabel("")
        self.status_lbl.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 13px; font-weight: 700; padding: 0px 15px 5px 15px;")
        overlay_layout.addWidget(self.status_lbl)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        self.input_frame = PillInputFrame()
        self.input_frame.setMinimumHeight(82)
        self.input_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_frame.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.input_frame.apply_theme()
        apply_soft_shadow(self.input_frame, blur=42, y=12, alpha=42)
        input_frame_layout = QHBoxLayout(self.input_frame)
        input_frame_layout.setContentsMargins(10, 8, 12, 8)
        input_frame_layout.setSpacing(8)

        self.input_field = ExpandingTextEdit()
        self.input_field.setPlaceholderText("הודעה")
        self.input_field.setStyleSheet(self._chat_input_stylesheet())
        self.input_field.textChanged.connect(self.on_text_change)
        self.input_field.send_signal.connect(self.send_text)
        input_frame_layout.addWidget(self.input_field, 1, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.action_btn = QPushButton()
        self.action_btn.setFixedSize(52, 52)
        self.action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.refresh_themed_icons()
        self.update_action_btn_visuals()
        self.action_btn_host = PinnedActionButtonHost(self.action_btn)
        input_frame_layout.insertWidget(0, self.action_btn_host, 0)
        
        # Keep the action button visually on the left even inside the RTL chat.
        bottom_layout.addWidget(self.input_frame, alignment=Qt.AlignmentFlag.AlignVCenter)
        overlay_layout.addLayout(bottom_layout)
        body_layout.addWidget(self.input_overlay, 0, 0, Qt.AlignmentFlag.AlignBottom)
        main_layout.addWidget(self.chat_body, 1)
        QTimer.singleShot(0, self._update_chat_bottom_padding)

    def show_usage_page(self):
        if self.usage_page is None:
            self.usage_page = UsageStatsPage(self.core, self)
            self.stacked_widget.addWidget(self.usage_page)
        self.usage_page.load_data('today')
        self.stacked_widget.setCurrentWidget(self.usage_page)

    def show_settings_page(self):
        if self.settings_page is None:
            self.settings_page = SettingsPage(self.core, self)
            self.stacked_widget.addWidget(self.settings_page)
        self.settings_page.show_home()
        self.settings_page.ensure_models_loaded()
        self.stacked_widget.setCurrentWidget(self.settings_page)

    def rebuild_settings_page(self):
        if self.settings_page is not None:
            self.stacked_widget.removeWidget(self.settings_page)
            self.settings_page.deleteLater()
            self.settings_page = None
        self.show_settings_page()

    def show_tools_page(self):
        if self.tools_page is not None:
            self.stacked_widget.removeWidget(self.tools_page)
            self.tools_page.deleteLater()
        self.tools_page = ToolsSettingsPage(self.core, self)
        self.stacked_widget.addWidget(self.tools_page)
        self.stacked_widget.setCurrentWidget(self.tools_page)

    def show_task_center_page(self):
        if self.task_center_page is None:
            self.task_center_page = TaskCenterPage(self.core, self)
            self.stacked_widget.addWidget(self.task_center_page)
        self.task_center_page.load_tasks()
        self.stacked_widget.setCurrentWidget(self.task_center_page)

    def show_trace_page(self):
        if self.trace_page is None:
            self.trace_page = DeveloperTracePage(self.core, self)
            self.stacked_widget.addWidget(self.trace_page)
        self.trace_page.load_trace()
        self.stacked_widget.setCurrentWidget(self.trace_page)

    def show_about_page(self):
        if self.about_page is None:
            self.about_page = AboutPage(self)
            self.stacked_widget.addWidget(self.about_page)
        self.stacked_widget.setCurrentWidget(self.about_page)

    def bring_to_front(self):
        if hasattr(self, "quick_reply_toast"):
            self.quick_reply_toast.hide()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.activateWindow()
        self.raise_()

    def _plain_notification_text(self, text, limit=520):
        cleaned = html.unescape(str(text or ""))
        cleaned = re.sub(r"```.*?```", "קטע קוד", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) > limit:
            cleaned = cleaned[:max(0, limit - 3)].rstrip() + "..."
        return cleaned or "סמארטי השיב."

    def show_response_notification(self, response):
        tray_preview = self._plain_notification_text(response, 240)
        try:
            self.tray_icon.showMessage("Smarti AI", tray_preview, QSystemTrayIcon.MessageIcon.Information, 7000)
        except Exception as e:
            logging.warning(f"Tray notification failed: {e}")
        # Native quick reply should be implemented with Windows App Notifications
        # text input/actions:
        # <input id="replyText" type="text" .../> +
        # <action content="שלח" arguments="action=reply" hint-inputId="replyText"/>.
        # The activation handler should read UserInput["replyText"] and pass it to
        # submit_quick_reply(). The PyQt popup prototype above is disabled.

    def submit_quick_reply(self, text):
        text = str(text or "").strip()
        if not text:
            return
        if self.agent_running:
            self.input_field.setPlainText(text)
            self.bring_to_front()
            return
        self.core.stop_speaking()
        self.add_message(text, is_user=True)
        self.process_request(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            available_width = self.scroll.viewport().width() or self.width()
            for bubble in self.findChildren(MessageBubble):
                bubble.update_parent_width(available_width)
            self._update_chat_bottom_padding()
        except Exception:
            pass

    def _update_chat_bottom_padding(self):
        if not hasattr(self, "chat_layout") or not hasattr(self, "input_overlay"):
            return
        margins = self.chat_layout.contentsMargins()
        overlay_h = max(112, self.input_overlay.sizeHint().height() + 22)
        if margins.bottom() != overlay_h:
            self.chat_layout.setContentsMargins(margins.left(), margins.top(), margins.right(), overlay_h)

    def on_tts_status(self, is_playing):
        self.tts_active = bool(is_playing)
        if not is_playing and not (self.tts_thread and self.tts_thread.isRunning()):
            self.active_tts_container = None
        self._refresh_message_tts_buttons()

    def _wire_message_container(self, container):
        container.tts_button_clicked.connect(self.handle_message_tts_button)
        container.update_tts_button_state(False, self.tts_active)

    def _refresh_message_tts_buttons(self):
        for container in self.findChildren(ChatMessageContainer):
            if container.is_user:
                continue
            active = self.tts_active and container is self.active_tts_container
            blocked = self.tts_active and container is not self.active_tts_container
            container.update_tts_button_state(active, blocked)

    def handle_message_tts_button(self, container):
        if container is self.active_tts_container and self.tts_active:
            self.core.stop_speaking()
            self.tts_active = False
            self.active_tts_container = None
            self._refresh_message_tts_buttons()
            return
        if self.tts_active:
            return
        self.start_message_tts(container)

    def start_message_tts(self, container):
        if not container or container.is_user:
            return
        text = container.bubble.plain_text()
        if not str(text or "").strip():
            return
        self.active_tts_container = container
        self.tts_active = True
        self._refresh_message_tts_buttons()
        worker = TTSWorker(self.core, text)
        self.tts_thread = worker
        self._tts_workers.append(worker)
        worker.finished.connect(lambda w=worker: self._on_message_tts_finished(w))
        worker.start()

    def _on_message_tts_finished(self, worker):
        try:
            self._tts_workers.remove(worker)
        except ValueError:
            pass
        if worker is self.tts_thread:
            self.tts_thread = None
            self.tts_active = False
            self.active_tts_container = None
            self._refresh_message_tts_buttons()

    def show_menu(self): self.menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

    def update_action_btn_visuals(self):
        try: self.action_btn.clicked.disconnect()
        except: pass

        if self.agent_running:
            self.action_btn.setToolTip("עצור פעולה")
            if not self.stop_agent_icon.isNull():
                self.action_btn.setIcon(self.stop_agent_icon)
                self.action_btn.setIconSize(QSize(28, 28))
                self.action_btn.setText("")
                border_css, bg_color = "border: none; border-radius: 26px;", ACCENT_SECONDARY_COLOR
            else:
                self.action_btn.setIcon(QIcon())
                self.action_btn.setText("■")
                border_css, bg_color = "border: none; border-radius: 26px;", ACCENT_SECONDARY_COLOR
            fg_color = ACCENT_TEXT_COLOR
            hover_bg = ACCENT_COLOR
            pressed_bg = ACCENT_TINT_STRONG
            self.action_btn.clicked.connect(self.cancel_agent)
        else:
            self.action_btn.setToolTip("")
            has_text = bool(self.input_field.toPlainText().strip())
            target_icon = self.send_icon if has_text else self.mic_icon
            fallback_text = "שלח" if has_text else "קול"
            
            if not target_icon.isNull():
                self.action_btn.setIcon(target_icon)
                self.action_btn.setIconSize(QSize(28, 28))
                self.action_btn.setText("")
                border_css = "border: none; border-radius: 26px;"
            else:
                self.action_btn.setIcon(QIcon())
                self.action_btn.setText(fallback_text)
                border_css = "border: none; border-radius: 26px;"
            bg_color = ACCENT_COLOR if has_text else ACCENT_TINT_STRONG
            fg_color = ACCENT_TEXT_COLOR if has_text else ACCENT_COLOR
            hover_bg = ACCENT_SECONDARY_COLOR if has_text else HOVER_TINT
            pressed_bg = ACCENT_TINT_STRONG
            
            if has_text: self.action_btn.clicked.connect(self.send_text)
            else: self.action_btn.clicked.connect(self.start_voice)

        self.action_btn.setStyleSheet(
            f"QPushButton {{ background-color: {bg_color}; {border_css} padding: 0px; "
            f"color: {fg_color}; font-size: 18px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {hover_bg}; }}"
            f"QPushButton:pressed {{ background-color: {pressed_bg}; }}"
            f"QPushButton:disabled {{ color: {SUBTLE_TEXT_COLOR}; background: transparent; }}"
        )
        self.action_btn.setGraphicsEffect(None)

    def cancel_agent(self):
        self.core.request_cancel()
        self.status_lbl.setText("עוצר מיד...")
        self.action_btn.setEnabled(False)
        self.update_action_btn_visuals()

    def on_text_change(self):
        self.update_action_btn_visuals()
        QTimer.singleShot(0, self._update_chat_bottom_padding)

    def add_message(self, text, is_user):
        if not text and is_user: return
        available_width = self.scroll.viewport().width() or self.width()
        container = ChatMessageContainer(text, is_user, available_width)
        self._wire_message_container(container)
        self.chat_layout.addWidget(container)
        QTimer.singleShot(0, container.start_entry_animation)
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
        QTimer.singleShot(180, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
        return container

    def send_text(self):
        text = self.input_field.toPlainText().strip()
        if not text: return
        self.input_field.clear()
        self.core.stop_speaking() 
        self.add_message(text, is_user=True)
        self.process_request(text)

    def trigger_voice_from_hotkey(self):
        if not self.agent_running: QTimer.singleShot(0, self.start_voice)

    def start_voice(self):
        self.core.stop_speaking() 
        self.status_lbl.setText("מקשיב...")
        self.input_field.setEnabled(False)
        self.action_btn.setEnabled(False)
        self.voice_thread = VoiceWorker()
        self.voice_thread.status_signal.connect(lambda s: self.status_lbl.setText(s))
        self.voice_thread.finished_signal.connect(self.on_voice_finished)
        self.voice_thread.start()

    def on_voice_finished(self, text):
        self.status_lbl.setText("")
        self.input_field.setEnabled(True)
        self.action_btn.setEnabled(True)
        if text:
            self.add_message(text, is_user=True)
            self.process_request(text, is_voice=True)

    def process_request(self, text, is_voice=False):
        self.current_request_is_voice = is_voice
        self.status_lbl.setText("חושב...")
        self.input_field.setEnabled(False)
        self.agent_running = True
        self.update_action_btn_visuals()
        
        available_width = self.scroll.viewport().width() or self.width()
        self.current_agent_container = ChatMessageContainer("", is_user=False, parent_width=available_width)
        self._wire_message_container(self.current_agent_container)
        self.current_agent_bubble = self.current_agent_container.bubble
        self.chat_layout.addWidget(self.current_agent_container)
        self.current_agent_container.hide() 
        
        self.agent_thread = AgentWorker(self.core, text)
        self.agent_thread.status_signal.connect(lambda s: self.status_lbl.setText(s))
        self.agent_thread.ask_confirm_signal.connect(self.show_confirm_dialog) 
        self.agent_thread.api_key_required_signal.connect(self.show_api_key_dialog)
        self.agent_thread.step_signal.connect(self.on_agent_step)
        self.agent_thread.finished_signal.connect(self.on_agent_finished)
        self.agent_thread.start()

    def on_agent_step(self, step_text):
        if self.current_agent_bubble:
            self.current_agent_bubble.show()
            self.current_agent_bubble.add_step(step_text)
            if self.current_agent_container:
                self.current_agent_container.reveal_with_entry_animation()
            QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def show_confirm_dialog(self, title, text):
        dlg = ActionConfirmDialog(title, text, self)
        self.agent_thread.confirm_result = (dlg.exec() == QDialog.DialogCode.Accepted)
        self.agent_thread.confirm_event.set()

    def show_api_key_dialog(self, secret_key, provider_label, title, message, help_url):
        dlg = ApiKeyRequiredDialog(secret_key, provider_label, title, message, help_url, self)
        self.agent_thread.api_key_result = dlg.api_key() if dlg.exec() == QDialog.DialogCode.Accepted else ""
        self.agent_thread.api_key_event.set()

    def on_agent_finished(self, response):
        should_notify = not self.isActiveWindow() or self.isMinimized()
        self.agent_running = False
        self.action_btn.setEnabled(True)
        self.update_action_btn_visuals()
        self.status_lbl.setText("")
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        response_container = None
        
        if response.startswith("ERROR_USER:"):
            msg = f"שגיאה: {response.replace('ERROR_USER:', '').strip()}"
            if self.current_agent_bubble:
                self.current_agent_bubble.show()
                self.current_agent_bubble.set_final_text(msg)
                if self.current_agent_container:
                    self.current_agent_container.reveal_with_entry_animation()
            else: self.add_message(msg, is_user=False)
        else:
            if self.current_agent_bubble:
                self.current_agent_bubble.show()
                self.current_agent_bubble.set_final_text(response)
                if self.current_agent_container:
                    self.current_agent_container.reveal_with_entry_animation()
                response_container = self.current_agent_container
            else:
                response_container = self.add_message(response, is_user=False)
                
            if should_notify:
                self.show_response_notification(response)
                
            if self.core.settings.get("read_aloud_all", False) or (self.core.settings.get("read_aloud_voice_only", True) and getattr(self, 'current_request_is_voice', False)):
                self.start_message_tts(response_container)
                
        self.current_agent_bubble = None
        self.current_agent_container = None
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def clear_chat(self):
        self.core.stop_speaking()
        self.tts_active = False
        self.active_tts_container = None
        for i in reversed(range(self.chat_layout.count())): 
            item = self.chat_layout.itemAt(i)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                for j in reversed(range(item.layout().count())):
                    w = item.layout().itemAt(j).widget()
                    if w: w.deleteLater()
                item.layout().deleteLater()
        if hasattr(self.core, 'gemini_history'): self.core.gemini_history = []
        if hasattr(self.core, 'universal_history'): self.core.universal_history = [{"role": "system", "content": self.core.system_prompt}]
        self.core.recent_tool_observations = []
        self.core.tool_observations = []
        self.core.settings["tool_context_transcript"] = []
        self.core.settings["conversation_summary"] = ""
        self.core._save_settings()
        self.core.system_prompt = self.core._load_system_prompt()
        logging.info(f"\n{'='*50}\n--- תחילת שיחה חדשה (ניקוי צ'אט) ---\n{'='*50}")
        self.add_message("שלום! אני סמארטי, סייען ה-AI האישי שלך. איך אוכל לעזור לך היום? 😊", is_user=False)

class AnimatedSplash(QWidget):
    def __init__(self, anim_path, fallback_path, size, border_color, border_width, radius, bg_color):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)
        self.border_width, self.border_color, self.radius, self.bg_color = border_width, QColor(border_color), radius, QColor(bg_color)
        
        mask_pixmap = QPixmap(size, size)
        mask_pixmap.fill(Qt.GlobalColor.transparent)
        mask_painter = QPainter(mask_pixmap)
        mask_painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        mask_path = QPainterPath()
        mask_path.addRoundedRect(0.0, 0.0, float(size), float(size), float(radius), float(radius))
        mask_painter.fillPath(mask_path, Qt.GlobalColor.black)
        mask_painter.end()
        self.setMask(mask_pixmap.mask())
        
        self.lbl = QLabel(self)
        self.lbl.setGeometry(border_width, border_width, size - 2*border_width, size - 2*border_width)
        self.lbl.setScaledContents(True) 
        self.lbl.setStyleSheet(f"background-color: {bg_color};")
        
        if os.path.exists(anim_path):
            self.movie = QMovie(anim_path)
            self.lbl.setMovie(self.movie)
            self.movie.start()
        elif os.path.exists(fallback_path): self.lbl.setPixmap(QPixmap(fallback_path))
        else:
            self.lbl.setText("S")
            self.lbl.setFont(QFont("Segoe UI", int(size/3), QFont.Weight.Bold))
            self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl.setStyleSheet(f"color: {border_color}; background-color: {bg_color};")
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()), float(self.radius), float(self.radius))
        painter.fillPath(path, self.bg_color)
        pen = QPen(self.border_color)
        pen.setWidth(self.border_width * 2) 
        painter.setPen(pen)
        painter.drawPath(path)

    def finish(self, window): self.close()


__all__ = [name for name in globals() if not name.startswith("__")]
