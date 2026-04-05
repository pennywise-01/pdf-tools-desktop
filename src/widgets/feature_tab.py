from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFrame, QGroupBox, QFileDialog, QScrollArea, QSizePolicy,
    QLineEdit, QComboBox, QCheckBox, QSlider, QSpinBox, QListWidget,
    QProgressBar
)
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt
from widgets.pdf_preview import PdfPreviewWidget
from utils.error_handler import show_error_dialog

# Modern color palette - Deep ocean theme
COLORS = {
    'bg': '#0a0f14',
    'surface': '#141c24',
    'surface_elevated': '#1a242e',
    'surface_hover': '#202d3a',
    'border': '#2a3744',
    'border_hover': '#3d4f5f',
    'border_focus': '#38bdf8',
    'text': '#f0f4f8',
    'text_secondary': '#94a3b8',
    'text_dim': '#64748b',
    'text_muted': '#475569',
    'accent': '#38bdf8',
    'accent_hover': '#7dd3fc',
    'accent_muted': 'rgba(56, 189, 248, 0.15)',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'gradient_start': '#0ea5e9',
    'gradient_end': '#8b5cf6',
}


class ElidedFileLabel(QLabel):
    """A single-line label that keeps long file names readable in narrow layouts."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text):  # noqa: N802 - Qt API compatibility
        self._full_text = text or ""
        self._update_elided_text()

    def resizeEvent(self, event):  # noqa: N802 - Qt API compatibility
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self):
        available_width = max(self.contentsRect().width(), 0)
        if available_width <= 0:
            super().setText(self._full_text)
            return

        elided = self.fontMetrics().elidedText(
            self._full_text,
            Qt.TextElideMode.ElideMiddle,
            available_width,
        )
        super().setText(elided)
        self.setToolTip(self._full_text if elided != self._full_text else "")

class FeatureTab(QWidget):
    """Base class for all feature tabs with modern professional styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAcceptDrops(True)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Left side: PDF Preview Panel
        preview_container = self.create_preview_panel()
        main_layout.addWidget(preview_container, 3)

        # Right side: Controls Panel
        controls_container = self.create_controls_panel()
        main_layout.addWidget(controls_container, 2)
        
        self.setup_controls()

    def create_preview_panel(self):
        """Create the PDF preview panel with modern styling"""
        container = QFrame()
        container.setObjectName("previewPanel")
        container.setStyleSheet(f"""
            QFrame#previewPanel {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Preview header with icon
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        
        # Icon placeholder
        icon_label = QLabel("◎")
        icon_label.setFont(QFont("Plus Jakarta Sans", 16))
        icon_label.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        header_row.addWidget(icon_label)
        
        header = QLabel("Document Preview")
        header.setFont(QFont("Plus Jakarta Sans", 14, QFont.Weight.DemiBold))
        header.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        header_row.addWidget(header)
        header_row.addStretch()
        
        layout.addLayout(header_row)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # PDF Preview Widget
        self.preview = PdfPreviewWidget()
        layout.addWidget(self.preview)
        
        return container

    def create_controls_panel(self):
        """Create the controls panel with modern styling"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background-color: {COLORS['surface']};
                width: 8px;
                border-radius: 4px;
                margin: 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['border_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.controls_widget = QFrame()
        self.controls_widget.setObjectName("controlsPanel")
        self.controls_widget.setStyleSheet(f"""
            QFrame#controlsPanel {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(24, 24, 24, 24)
        self.controls_layout.setSpacing(20)
        self.controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.controls_widget)
        
        return scroll_area

    def create_header(self, title, description=""):
        """Create a styled header with title and description"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Plus Jakarta Sans", 20, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        layout.addWidget(title_label)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Plus Jakarta Sans", 13))
            desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # Accent line
        accent_line = QFrame()
        accent_line.setFixedHeight(3)
        accent_line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {COLORS['gradient_start']}, stop:1 {COLORS['gradient_end']});
            border-radius: 1px;
        """)
        layout.addWidget(accent_line)
        
        return container

    def create_section(self, title):
        """Create a styled section group box"""
        group = QGroupBox(title)
        group.setFont(QFont("Plus Jakarta Sans", 12, QFont.Weight.DemiBold))
        group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['surface_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                margin-top: 24px;
                padding: 20px;
                padding-top: 28px;
                font-weight: 600;
                color: {COLORS['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: {COLORS['text_secondary']};
                background-color: {COLORS['surface_elevated']};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 8, 0, 0)
        
        return group, layout

    def create_file_drop_zone(self, text="Drop files here or click to browse", accept_text="Release to add files"):
        """Create a styled drag-and-drop zone"""
        zone = QFrame()
        zone.setObjectName("dropZone")
        zone.setMinimumHeight(120)
        zone.setStyleSheet(f"""
            QFrame#dropZone {{
                background-color: {COLORS['accent_muted']};
                border: 2px dashed {COLORS['accent']};
                border-radius: 12px;
            }}
            QFrame#dropZone:hover {{
                background-color: rgba(56, 189, 248, 0.2);
                border-color: {COLORS['accent_hover']};
            }}
        """)
        
        layout = QVBoxLayout(zone)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("⬆")
        icon.setFont(QFont("Plus Jakarta Sans", 24))
        icon.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(text)
        label.setFont(QFont("Plus Jakarta Sans", 13))
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon)
        layout.addWidget(label)
        
        return zone

    def create_file_label(self, text="No file selected"):
        """Create a styled file path display"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        
        icon = QLabel("📄")
        icon.setFont(QFont("Plus Jakarta Sans", 14))
        icon.setStyleSheet("background: transparent;")
        layout.addWidget(icon)
        
        label = ElidedFileLabel(text)
        label.setObjectName("fileLabel")
        label.setFont(QFont("Plus Jakarta Sans", 12))
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(label, 1)
        
        return container, label

    def create_primary_button(self, text, callback=None):
        """Create a styled primary action button"""
        btn = QPushButton(text)
        btn.setFont(QFont("Plus Jakarta Sans", 13, QFont.Weight.DemiBold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(48)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {COLORS['gradient_start']}, stop:1 {COLORS['accent']});
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_hover']});
            }}
            QPushButton:pressed {{
                background-color: {COLORS['gradient_start']};
            }}
            QPushButton:disabled {{
                background: {COLORS['surface_elevated']};
                color: {COLORS['text_dim']};
            }}
        """)
        
        if callback:
            btn.clicked.connect(callback)
        
        return btn

    def create_secondary_button(self, text, callback=None):
        """Create a styled secondary action button"""
        btn = QPushButton(text)
        btn.setFont(QFont("Plus Jakarta Sans", 12, QFont.Weight.Medium))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_muted']};
                border-color: {COLORS['accent']};
                color: {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background-color: rgba(56, 189, 248, 0.25);
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {COLORS['text_dim']};
                border-color: {COLORS['border']};
            }}
        """)
        
        if callback:
            btn.clicked.connect(callback)
        
        return btn

    def create_danger_button(self, text, callback=None):
        """Create a styled danger/destructive action button"""
        btn = QPushButton(text)
        btn.setFont(QFont("Plus Jakarta Sans", 12, QFont.Weight.Medium))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']}60;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}20;
                border-color: {COLORS['error']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['error']}30;
            }}
        """)
        
        if callback:
            btn.clicked.connect(callback)
        
        return btn

    def create_input(self, placeholder=""):
        """Create a styled text input"""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFont(QFont("Plus Jakarta Sans", 12))
        input_field.setMinimumHeight(44)
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 16px;
            }}
            QLineEdit:hover {{
                border-color: {COLORS['border_hover']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['border_focus']};
                background-color: {COLORS['surface_hover']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_dim']};
            }}
        """)
        return input_field

    def create_password_input(self, placeholder="Enter password"):
        """Create a styled password input"""
        input_field = self.create_input(placeholder)
        input_field.setEchoMode(QLineEdit.EchoMode.Password)
        return input_field

    def create_dropdown(self, items=None):
        """Create a styled dropdown/combobox"""
        combo = QComboBox()
        combo.setFont(QFont("Plus Jakarta Sans", 12))
        combo.setMinimumHeight(44)
        if items:
            combo.addItems(items)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 16px;
                padding-right: 36px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['border_hover']};
            }}
            QComboBox:focus {{
                border-color: {COLORS['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 32px;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                width: 0px;
                height: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                selection-background-color: {COLORS['accent_muted']};
                selection-color: {COLORS['accent']};
                padding: 6px;
                outline: none;
            }}
        """)
        return combo

    def create_checkbox(self, text, checked=False):
        """Create a styled checkbox"""
        checkbox = QCheckBox(text)
        checkbox.setFont(QFont("Plus Jakarta Sans", 12))
        checkbox.setChecked(checked)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text']};
                spacing: 10px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['surface_elevated']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {COLORS['accent_hover']};
                border-color: {COLORS['accent_hover']};
            }}
        """)
        return checkbox

    def create_slider(self, min_val=0, max_val=100, value=50):
        """Create a styled slider"""
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(value)
        slider.setMinimumHeight(24)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background-color: {COLORS['surface_elevated']};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background-color: {COLORS['accent']};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {COLORS['gradient_start']}, stop:1 {COLORS['accent']});
                border-radius: 4px;
            }}
        """)
        return slider

    def create_spinbox(self, min_val=0, max_val=100, value=1):
        """Create a styled spinbox"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        spinbox.setFont(QFont("Plus Jakarta Sans", 12))
        spinbox.setMinimumHeight(44)
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px 16px;
            }}
            QSpinBox:hover {{
                border-color: {COLORS['border_hover']};
            }}
            QSpinBox:focus {{
                border-color: {COLORS['border_focus']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['surface_hover']};
                border: none;
                width: 24px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_muted']};
            }}
        """)
        return spinbox

    def create_list_widget(self, min_height=200):
        """Create a styled list widget"""
        list_widget = QListWidget()
        list_widget.setMinimumHeight(min_height)
        list_widget.setFont(QFont("Plus Jakarta Sans", 12))
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-radius: 8px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['surface_hover']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_muted']};
                color: {COLORS['accent']};
            }}
        """)
        return list_widget

    def create_progress_bar(self):
        """Create a styled progress bar"""
        progress = QProgressBar()
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['surface_elevated']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {COLORS['gradient_start']}, stop:1 {COLORS['accent']});
                border-radius: 4px;
            }}
        """)
        return progress

    def create_info_label(self, text):
        """Create an info label with secondary text color"""
        label = QLabel(text)
        label.setFont(QFont("Plus Jakarta Sans", 12))
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        label.setWordWrap(True)
        return label

    def create_label(self, text, secondary=False):
        """Create a styled label"""
        label = QLabel(text)
        label.setFont(QFont("Plus Jakarta Sans", 12))
        color = COLORS['text_secondary'] if secondary else COLORS['text']
        label.setStyleSheet(f"color: {color}; background: transparent;")
        return label

    def create_separator(self):
        """Create a horizontal separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        separator.setFixedHeight(1)
        return separator

    def show_error(self, message, detail=None, prefix="GEN"):
        show_error_dialog(self, message, detail, prefix)
        
    def setup_controls(self):
        # This method should be overridden by subclasses
        pass
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.handle_file_drop(files)
            
    def handle_file_drop(self, files):
        # This method should be overridden by subclasses
        pass
