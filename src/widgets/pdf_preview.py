from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView,
    QHBoxLayout, QLabel, QSlider
)
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import QSize, Qt
import fitz  # PyMuPDF

# Color palette
COLORS = {
    'bg': '#0f1419',
    'surface': '#1c2128',
    'surface_alt': '#262d36',
    'border': '#30363d',
    'text': '#e6edf3',
    'text_secondary': '#8b949e',
    'accent': '#2dd4bf',
}

class PdfPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_pdf_path = None
        self.zoom_level = 1.0
        self.base_icon_w = 225
        self.base_icon_h = 300
        self.grid_padding_w = 20
        self.grid_padding_h = 20
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        
        # Zoom Toolbar
        self.setup_zoom_toolbar()
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['surface_alt']};
                border-radius: 8px;
            }}
            QListWidget::item {{
                color: {COLORS['text']};
                padding: 8px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(45, 212, 191, 0.15);
                border: 1px solid {COLORS['accent']};
            }}
            QListWidget::item:hover {{
                background-color: rgba(45, 212, 191, 0.08);
            }}
        """)
        
        # Initial size setup
        self.update_list_size()
        
        self.layout.addWidget(self.list_widget)

    def setup_zoom_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.setContentsMargins(0, 0, 0, 0)
        
        # Zoom label
        zoom_label = QLabel("Zoom")
        zoom_label.setFont(QFont("Plus Jakarta Sans", 11))
        zoom_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        toolbar.addWidget(zoom_label)
        
        # Slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(30, 300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.zoom_slider.setSingleStep(10)
        self.zoom_slider.setPageStep(50)
        self.zoom_slider.valueChanged.connect(self.on_slider_value_changed)
        self.zoom_slider.sliderReleased.connect(self.on_slider_released)
        toolbar.addWidget(self.zoom_slider, 1)
        
        # Percentage
        self.zoom_display = QLabel("100%")
        self.zoom_display.setFont(QFont("Plus Jakarta Sans", 11, QFont.Weight.Medium))
        self.zoom_display.setFixedWidth(50)
        self.zoom_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_display.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        toolbar.addWidget(self.zoom_display)
        
        self.layout.addLayout(toolbar)

    def on_slider_value_changed(self, value):
        self.zoom_level = value / 100.0
        self.update_list_size()

    def on_slider_released(self):
        self.refresh_preview()

    def update_list_size(self):
        scale = self.zoom_level
        self.zoom_display.setText(f"{int(scale * 100)}%")
        
        icon_w = int(self.base_icon_w * scale)
        icon_h = int(self.base_icon_h * scale)
        
        grid_w = icon_w + self.grid_padding_w
        grid_h = icon_h + self.grid_padding_h
        
        self.list_widget.setIconSize(QSize(icon_w, icon_h))
        self.list_widget.setGridSize(QSize(grid_w, grid_h))


    def load_pdf(self, file_path):
        self.current_pdf_path = file_path
        self.refresh_preview()

    def refresh_preview(self):
        self.list_widget.clear()
        if not self.current_pdf_path:
            return
            
        try:
            doc = fitz.open(self.current_pdf_path)
            
            current_dpi = int(72 * self.zoom_level)
            max_preview_pages = 20
            
            for i, page in enumerate(doc):
                if i >= max_preview_pages:
                    break
                    
                try:
                    pix = page.get_pixmap(dpi=current_dpi)
                    img = QPixmap()
                    img.loadFromData(pix.tobytes())
                    
                    item = QListWidgetItem(QIcon(img), f"Page {i+1}")
                    item.setData(Qt.ItemDataRole.UserRole, i + 1)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
                    self.list_widget.addItem(item)
                except Exception as e:
                    print(f"Error rendering page {i+1}: {e}")
                    continue
                
            if len(doc) > max_preview_pages:
                info_item = QListWidgetItem(f"... and {len(doc) - max_preview_pages} more pages")
                info_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_widget.addItem(info_item)

            doc.close()
            
        except Exception as e:
            print(f"Error loading PDF preview: {e}")

    def get_selected_pages(self):
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.list_widget.selectedItems()]

    def clear(self):
        self.current_pdf_path = None
        self.list_widget.clear()
