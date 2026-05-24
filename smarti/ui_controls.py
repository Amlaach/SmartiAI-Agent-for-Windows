"""Reusable PyQt controls used across Smarti screens."""
from .common import *
from .ui_styles import *

# ==========================================
# פונקציות עזר UI
# ==========================================
def make_circular_pixmap(image_path, size, border_color=None, border_width=0, bg_color=None):
    original = QPixmap(image_path)
    if original.isNull(): return None
    img_size = size - 2 * border_width
    scaled = original.scaled(img_size, img_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    dim = min(scaled.width(), scaled.height())
    cropped = scaled.copy((scaled.width() - dim) // 2, (scaled.height() - dim) // 2, dim, dim)
    target = QPixmap(size, size)
    target.fill(Qt.GlobalColor.transparent)
    painter = QPainter(target)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    path = QPainterPath()
    path.addEllipse(border_width, border_width, img_size, img_size)
    painter.setClipPath(path)
    if bg_color: painter.fillPath(path, QColor(bg_color))
    painter.drawPixmap(border_width, border_width, cropped)
    if border_color and border_width > 0:
        painter.setClipping(False)
        pen = QPen(QColor(border_color))
        pen.setWidth(border_width)
        painter.setPen(pen)
        offset = border_width / 2.0
        painter.drawEllipse(int(offset), int(offset), int(size - border_width), int(size - border_width))
    painter.end()
    return target

def apply_soft_shadow(widget, *, blur=28, y=8, alpha=46, color=None):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    shadow = QColor(color or "#00111C")
    shadow.setAlpha(alpha)
    effect.setColor(shadow)
    widget.setGraphicsEffect(effect)
    return effect

class MeshGradientWidget(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        base = QLinearGradient(rect.topLeft(), rect.bottomRight())
        base.setColorAt(0.00, QColor(MESH_A))
        base.setColorAt(0.45, QColor(MESH_B))
        base.setColorAt(0.72, QColor(MESH_C))
        base.setColorAt(1.00, QColor(MESH_D))
        painter.fillRect(rect, QBrush(base))
        painter.end()

class NoScrollComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMaxVisibleItems(8)
        self.view().setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.view().setTextElideMode(Qt.TextElideMode.ElideRight)

    def wheelEvent(self, e): e.ignore()

    def showPopup(self):
        self.view().setMinimumWidth(max(180, self.width()))
        self.view().setMaximumWidth(max(220, self.width()))
        super().showPopup()

class SegmentedControl(QWidget):
    currentIndexChanged = pyqtSignal(int)

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.setObjectName("SegmentedControl")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._items = []
        self._buttons = []
        self._current_index = -1
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(0)
        self.addItems(items or [])
        self.apply_theme()

    def addItems(self, items):
        for item in items:
            self.addItem(item)
        if self._items and self._current_index < 0:
            self.setCurrentIndex(0, emit=False)

    def addItem(self, text):
        index = len(self._items)
        self._items.append(str(text))
        btn = QPushButton(str(text))
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(34)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda checked=False, i=index: self.setCurrentIndex(i))
        self._buttons.append(btn)
        self._layout.addWidget(btn)
        self.apply_theme()

    def currentIndex(self):
        return self._current_index

    def currentText(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return ""

    def setCurrentIndex(self, index, emit=True):
        if not self._items:
            self._current_index = -1
            return
        index = max(0, min(int(index), len(self._items) - 1))
        if index == self._current_index:
            for i, btn in enumerate(self._buttons):
                btn.setChecked(i == index)
            return
        self._current_index = index
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        if emit:
            self.currentIndexChanged.emit(index)

    def setCurrentText(self, text):
        text = str(text)
        if text in self._items:
            self.setCurrentIndex(self._items.index(text))

    def apply_theme(self):
        self.setStyleSheet(segmented_control_css())

class SmartiCheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(38)
        self.setStyleSheet("background: transparent;")

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(max(hint.width() + 40, 180), max(hint.height(), 38))

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        switch_w, switch_h = 52, 30
        margin = 2
        y = int((self.height() - switch_h) / 2)
        switch_x = margin
        switch_rect = QRectF(switch_x, y, switch_w, switch_h)

        track = QLinearGradient(switch_rect.topLeft(), switch_rect.bottomRight())
        if self.isChecked():
            track.setColorAt(0.0, QColor(ACCENT_COLOR))
            track.setColorAt(1.0, QColor(ACCENT_SECONDARY_COLOR))
        else:
            track.setColorAt(0.0, QColor(FIELD_COLOR))
            track.setColorAt(1.0, QColor(PANEL_ELEVATED_COLOR))
        pen = QPen(QColor(SOFT_LINE_COLOR))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QBrush(track))
        painter.drawRoundedRect(switch_rect, switch_h / 2, switch_h / 2)

        knob_d = 24
        knob_margin = 3
        knob_x = switch_x + switch_w - knob_d - knob_margin if not self.isChecked() else switch_x + knob_margin
        knob_rect = QRectF(knob_x, y + knob_margin, knob_d, knob_d)
        painter.setBrush(QBrush(QColor(BG_ELEVATED_COLOR)))
        painter.drawEllipse(knob_rect)

        text_rect = QRectF(switch_w + 16, 0, max(1, self.width() - switch_w - 18), self.height())
        painter.setPen(QColor(TEXT_COLOR if self.isEnabled() else SUBTLE_TEXT_COLOR))
        painter.setFont(self.font())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute, self.text())
        painter.end()

class RtlFillSlider(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)
        self.setMinimumHeight(48)
        self.setPageStep(1)

    def _track_rect(self):
        track_h = 30
        margin_x = 4
        return QRectF(margin_x, (self.height() - track_h) / 2, max(1, self.width() - margin_x * 2), track_h)

    def _value_from_x(self, x):
        rect = self._track_rect()
        ratio = (rect.right() - float(x)) / max(1.0, rect.width())
        ratio = max(0.0, min(1.0, ratio))
        return self.minimum() + round(ratio * (self.maximum() - self.minimum()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.setSliderDown(True)
            self.setValue(self._value_from_x(event.position().x()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSliderDown() and self.isEnabled():
            self.setValue(self._value_from_x(event.position().x()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            self.setValue(self._value_from_x(event.position().x()))
            self.setSliderDown(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self._track_rect()
        radius = rect.height() / 2

        track_path = QPainterPath()
        track_path.addRoundedRect(rect, radius, radius)
        painter.fillPath(track_path, QColor(PANEL_ELEVATED_COLOR if self.isEnabled() else FIELD_COLOR))

        span = max(1, self.maximum() - self.minimum())
        ratio = (self.value() - self.minimum()) / span
        fill_w = rect.width() * max(0.0, min(1.0, ratio))
        if fill_w > 0:
            fill_rect = QRectF(rect.right() - fill_w, rect.top(), fill_w, rect.height())
            fill_path = QPainterPath()
            fill_path.addRoundedRect(fill_rect, radius, radius)
            gradient = QLinearGradient(fill_rect.topRight(), fill_rect.topLeft())
            gradient.setColorAt(0.0, QColor(ACCENT_COLOR))
            gradient.setColorAt(1.0, QColor(ACCENT_SECONDARY_COLOR))
            painter.fillPath(fill_path.intersected(track_path), QBrush(gradient))

        pen = QPen(QColor(SOFT_LINE_COLOR))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(track_path)
        painter.end()

class SettingsNavCard(QFrame):
    def __init__(self, title, subtitle, callback):
        super().__init__()
        self.callback = callback
        self.setObjectName("SettingsNavCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumHeight(86)
        self.setStyleSheet(NAV_CARD_CSS)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        self.title_lbl = QLabel(title)
        self.title_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        self.title_lbl.setMinimumWidth(1)
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        self.subtitle_lbl.setMinimumWidth(1)
        self.subtitle_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.subtitle_lbl.setWordWrap(True)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.subtitle_lbl)
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(NAV_CARD_CSS)
        self.title_lbl.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self.subtitle_lbl.setStyleSheet(f"color: {MUTED_TEXT_COLOR}; font-size: 12px; background: transparent; border: none;")
        apply_soft_shadow(self, blur=24, y=7, alpha=32)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.callback:
            self.callback()
        super().mousePressEvent(event)

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, *args, duration=330, **kwargs):
        super().__init__(*args, **kwargs)
        self._transition_duration = duration
        self._transition_animations = []

    def setCurrentWidget(self, widget):
        if widget is self.currentWidget():
            return
        super().setCurrentWidget(widget)
        self._animate_current_widget()

    def setCurrentIndex(self, index):
        if index == self.currentIndex():
            return
        super().setCurrentIndex(index)
        self._animate_current_widget()

    def _animate_current_widget(self):
        widget = self.currentWidget()
        if not widget:
            return
        end_pos = widget.pos()
        slide_offset = -26 if self.layoutDirection() == Qt.LayoutDirection.RightToLeft else 26
        widget.move(end_pos + QPoint(slide_offset, 0))

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)

        fade_anim = QPropertyAnimation(effect, b"opacity", widget)
        fade_anim.setDuration(self._transition_duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        slide_anim = QPropertyAnimation(widget, b"pos", widget)
        slide_anim.setDuration(self._transition_duration)
        slide_anim.setStartValue(widget.pos())
        slide_anim.setEndValue(end_pos)
        slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._transition_animations.extend([fade_anim, slide_anim])

        def cleanup():
            widget.move(end_pos)
            widget.setGraphicsEffect(None)
            for anim in (fade_anim, slide_anim):
                try:
                    self._transition_animations.remove(anim)
                except ValueError:
                    pass

        fade_anim.finished.connect(cleanup)
        fade_anim.start()
        slide_anim.start()

class ShimmerLabel(QLabel):
    def __init__(self, text=""):
        super().__init__("")
        self._shimmer_clock = QElapsedTimer()
        self._shimmer_cycle_ms = 1550
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(16)
        self._shimmer_timer.timeout.connect(self._advance_shimmer)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        self.setText(text)

    def setText(self, text):
        super().setText(text)
        if str(text or "").strip():
            if not self._shimmer_timer.isActive():
                self._shimmer_clock.restart()
                self._shimmer_timer.start()
        else:
            self._shimmer_timer.stop()
        self.update()

    def _advance_shimmer(self):
        self.update()

    def paintEvent(self, event):
        text = self.text()
        if not text or not self._shimmer_timer.isActive():
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setFont(self.font())
        rect = self.contentsRect()
        flags = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter
        painter.setPen(QColor(ACCENT_COLOR))
        painter.drawText(rect, flags, text)

        shimmer_width = max(78, int(rect.width() * 0.34))
        phase = (self._shimmer_clock.elapsed() % self._shimmer_cycle_ms) / self._shimmer_cycle_ms
        distance = rect.width() + shimmer_width * 2
        x = rect.right() + shimmer_width - int(distance * phase)
        clip = rect.adjusted(0, 0, 0, 0)
        clip.setLeft(x)
        clip.setWidth(shimmer_width)
        painter.setClipRect(clip)
        gradient = QLinearGradient(float(x), 0.0, float(x + shimmer_width), 0.0)
        gradient.setColorAt(0.00, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.24, QColor(255, 255, 255, 70))
        gradient.setColorAt(0.50, QColor(255, 255, 255, 225))
        gradient.setColorAt(0.76, QColor(255, 255, 255, 70))
        gradient.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.setPen(QPen(QBrush(gradient), 1))
        painter.drawText(rect, flags, text)
        painter.end()

class StepsShimmerEffect(QGraphicsEffect):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shimmer_clock = QElapsedTimer()
        self._shimmer_cycle_ms = 1650
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(16)
        self._shimmer_timer.timeout.connect(self.update)
        self._is_active = False
        self._mask_cache_key = None
        self._mask_cache = QPixmap()

    def start_shimmer(self):
        self._is_active = True
        if not self._shimmer_timer.isActive():
            self._shimmer_clock.restart()
            self._shimmer_timer.start()
        self.update()

    def stop_shimmer(self):
        self._is_active = False
        if self._shimmer_timer.isActive():
            self._shimmer_timer.stop()
        self.update()

    def _text_mask_from_source(self, source):
        cache_key = source.cacheKey()
        if self._mask_cache_key == cache_key and not self._mask_cache.isNull():
            return self._mask_cache

        image = source.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        mask_image = QImage(image.size(), QImage.Format.Format_ARGB32_Premultiplied)
        mask_image.fill(Qt.GlobalColor.transparent)

        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                if color.alpha() > 0 and (color.red() + color.green() + color.blue()) > 120:
                    mask_image.setPixelColor(x, y, QColor(255, 255, 255, color.alpha()))

        self._mask_cache_key = cache_key
        self._mask_cache = QPixmap.fromImage(mask_image)
        self._mask_cache.setDevicePixelRatio(source.devicePixelRatio())
        return self._mask_cache

    def draw(self, painter):
        source, offset = self.sourcePixmap(Qt.CoordinateSystem.LogicalCoordinates)
        if source.isNull():
            return
        painter.drawPixmap(offset, source)

        if not self._is_active:
            return

        rect = source.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        mask = self._text_mask_from_source(source)
        if mask.isNull():
            return

        dpr = source.devicePixelRatio()
        logical_size = source.deviceIndependentSize()
        logical_rect = QRectF(0.0, 0.0, logical_size.width(), logical_size.height())
        shimmer_width = max(88, int(logical_rect.width() * 0.36))
        phase = (self._shimmer_clock.elapsed() % self._shimmer_cycle_ms) / self._shimmer_cycle_ms
        distance = logical_rect.width() + shimmer_width * 2
        x = logical_rect.right() + shimmer_width - (distance * phase)

        gradient = QLinearGradient(float(x), 0.0, float(x + shimmer_width), 0.0)
        gradient.setColorAt(0.00, QColor(255, 255, 255, 0))
        gradient.setColorAt(0.18, QColor(255, 255, 255, 24))
        gradient.setColorAt(0.50, QColor(255, 255, 255, 155))
        gradient.setColorAt(0.82, QColor(255, 255, 255, 24))
        gradient.setColorAt(1.00, QColor(255, 255, 255, 0))

        overlay = QPixmap(source.size())
        overlay.setDevicePixelRatio(dpr)
        overlay.fill(Qt.GlobalColor.transparent)
        overlay_painter = QPainter(overlay)
        overlay_painter.fillRect(logical_rect, QBrush(gradient))
        overlay_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        overlay_painter.drawPixmap(0, 0, mask)
        overlay_painter.end()

        painter.drawPixmap(offset, overlay)

class StepsShimmerLabel(QLabel):
    def __init__(self):
        super().__init__()
        self._shimmer_effect = StepsShimmerEffect(self)
        self.setGraphicsEffect(self._shimmer_effect)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignTop)

    def start_shimmer(self):
        if str(self.text() or "").strip():
            self._shimmer_effect.start_shimmer()

    def stop_shimmer(self):
        self._shimmer_effect.stop_shimmer()

class DirectoryPicker(QWidget):
    pathsChanged = pyqtSignal()

    def __init__(self, paths=None, *, allow_multiple=False, dialog_title="בחר תיקייה", default_path=""):
        super().__init__()
        self.allow_multiple = allow_multiple
        self.dialog_title = dialog_title
        self.default_path = default_path or os.path.expanduser("~")
        self._paths = []
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        self.path_label.setMinimumWidth(1)
        self.path_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.path_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.choose_btn = QPushButton("בחר תיקייה" if not allow_multiple else "הוסף תיקייה")
        self.choose_btn.setStyleSheet(SECONDARY_BUTTON_CSS)
        self.choose_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.choose_btn.clicked.connect(self.choose_directory)
        button_row.addWidget(self.choose_btn)

        if allow_multiple:
            self.clear_btn = QPushButton("נקה")
            self.clear_btn.setStyleSheet(SECONDARY_BUTTON_CSS)
            self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.clear_btn.clicked.connect(self.clear_paths)
            button_row.addWidget(self.clear_btn)

        button_row.addStretch()
        layout.addLayout(button_row)
        self.apply_theme()
        self.set_paths(paths or [])

    def apply_theme(self):
        self.path_label.setStyleSheet(f"""
            QLabel {{
                background: {FIELD_COLOR}; color: {FIELD_TEXT_COLOR};
                border: 1px solid {SOFT_LINE_COLOR};
                border-radius: 20px; padding: 13px 14px;
                font-size: 13px;
            }}
        """)
        self.choose_btn.setStyleSheet(SECONDARY_BUTTON_CSS)
        if hasattr(self, "clear_btn"):
            self.clear_btn.setStyleSheet(SECONDARY_BUTTON_CSS)

    def set_paths(self, paths):
        if isinstance(paths, str):
            paths = [paths]
        cleaned = []
        for path in paths or []:
            path = str(path or "").strip()
            if path and path not in cleaned:
                cleaned.append(path)
        self._paths = cleaned[:1] if not self.allow_multiple else cleaned
        self._refresh_label()

    def paths(self):
        return list(self._paths)

    def path(self):
        return self._paths[0] if self._paths else ""

    def choose_directory(self):
        start = self.path() or self.default_path
        selected = QFileDialog.getExistingDirectory(self, self.dialog_title, start)
        if selected:
            if self.allow_multiple:
                if selected not in self._paths:
                    self._paths.append(selected)
            else:
                self._paths = [selected]
            self._refresh_label()
            self.pathsChanged.emit()

    def clear_paths(self):
        self._paths = []
        self._refresh_label()
        self.pathsChanged.emit()

    def _refresh_label(self):
        if self._paths:
            display_paths = [
                path.replace("\\", "\\\u200b").replace("/", "/\u200b")
                for path in self._paths
            ]
            self.path_label.setText("\n".join(display_paths))
        else:
            self.path_label.setText("לא נבחרה תיקייה")

class ExpandingTextEdit(QTextEdit):
    send_signal = pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_aligning = False
        self._placeholder_text = ""
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setCursorWidth(2)
        self.setViewportMargins(0, 4, 0, 0)
        doc = self.document()
        option = doc.defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignLeft)
        option.setTextDirection(Qt.LayoutDirection.RightToLeft)
        option.setWrapMode(QTextOption.WrapMode.WordWrap)
        doc.setDefaultTextOption(option)
        self.viewport().setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor = self.textCursor()
        fmt = cursor.blockFormat()
        fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        cursor.setBlockFormat(fmt)
        self.setTextCursor(cursor)
        self.document().setDocumentMargin(16)
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_height)
        self.max_height = 156
        self.min_height = 64
        self.setFixedHeight(self.min_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.textChanged.connect(self._force_rtl_alignment)

    def setPlaceholderText(self, text):
        self._placeholder_text = str(text or "")
        super().setPlaceholderText("")
        self.viewport().update()

    def placeholderText(self):
        return self._placeholder_text

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.toPlainText() or not self._placeholder_text:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setPen(QColor(SUBTLE_TEXT_COLOR))
        painter.setFont(self.font())
        margin = int(self.document().documentMargin())
        rect = self.viewport().rect().adjusted(margin, 2, -margin, 0)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter,
            self._placeholder_text
        )
        painter.end()

    def _force_rtl_alignment(self):
        if getattr(self, '_is_aligning', False): return
        self._is_aligning = True
        doc = self.document()
        previous_widget_signal_state = self.blockSignals(True)
        previous_doc_signal_state = doc.blockSignals(True)
        try:
            self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.viewport().setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            option = doc.defaultTextOption()
            if (
                option.alignment() != Qt.AlignmentFlag.AlignLeft
                or option.textDirection() != Qt.LayoutDirection.RightToLeft
                or option.wrapMode() != QTextOption.WrapMode.WordWrap
            ):
                option.setAlignment(Qt.AlignmentFlag.AlignLeft)
                option.setTextDirection(Qt.LayoutDirection.RightToLeft)
                option.setWrapMode(QTextOption.WrapMode.WordWrap)
                doc.setDefaultTextOption(option)

            original_cursor = self.textCursor()
            format_cursor = QTextCursor(doc)
            needs_cursor_restore = False
            block = doc.firstBlock()
            while block.isValid():
                fmt = block.blockFormat()
                if fmt.layoutDirection() != Qt.LayoutDirection.RightToLeft or fmt.alignment() != Qt.AlignmentFlag.AlignLeft:
                    format_cursor.setPosition(block.position())
                    fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
                    fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    format_cursor.setBlockFormat(fmt)
                    needs_cursor_restore = True
                block = block.next()
            if needs_cursor_restore:
                self.setTextCursor(original_cursor)
        finally:
            doc.blockSignals(previous_doc_signal_state)
            self.blockSignals(previous_widget_signal_state)
            self._is_aligning = False

    def clear(self):
        super().clear()
        self._force_rtl_alignment()
        
    def adjust_height(self):
        doc_height = int(self.document().size().height())
        margins = self.contentsMargins()
        target_height = doc_height + margins.top() + margins.bottom()
        if target_height < self.min_height: target_height = self.min_height
        elif target_height > self.max_height:
            target_height = self.max_height
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else: self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if self.height() != target_height: self.setFixedHeight(target_height)
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier: super().keyPressEvent(event)
            else: self.send_signal.emit()
        elif event.key() == Qt.Key.Key_Down:
            cursor = self.textCursor()
            old_pos = cursor.position()
            cursor.movePosition(cursor.MoveOperation.Down)
            if cursor.position() == old_pos: cursor.movePosition(cursor.MoveOperation.End)
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key.Key_Up:
            cursor = self.textCursor()
            old_pos = cursor.position()
            cursor.movePosition(cursor.MoveOperation.Up)
            if cursor.position() == old_pos: cursor.movePosition(cursor.MoveOperation.Start)
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)


__all__ = [name for name in globals() if not name.startswith("__")]
