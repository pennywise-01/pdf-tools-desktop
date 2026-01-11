from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView,
    QHBoxLayout, QLabel, QSlider
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt
import fitz  # PyMuPDF

class PdfPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_pdf_path = None
        self.zoom_level = 1.0
        self.base_icon_w = 225
        self.base_icon_h = 300
        # Grid needs to be slightly larger than icon to accommodate text and spacing
        self.grid_padding_w = 20
        self.grid_padding_h = 20
        
        self.layout = QVBoxLayout(self)
        
        # Zoom Toolbar
        self.setup_zoom_toolbar()
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_widget.setStyleSheet("border: 1px solid black;")
        
        # Initial size setup
        self.update_list_size()
        
        self.layout.addWidget(self.list_widget)

    def setup_zoom_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        toolbar.setContentsMargins(0, 0, 0, 0)
        
        # Slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(30, 300) # 30% to 300%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(50)
        self.zoom_slider.setSingleStep(10)
        self.zoom_slider.setPageStep(50)
        self.zoom_slider.valueChanged.connect(self.on_slider_value_changed)
        self.zoom_slider.sliderReleased.connect(self.on_slider_released)
        toolbar.addWidget(self.zoom_slider)
        
        # Percentage
        self.zoom_display = QLabel("100%")
        self.zoom_display.setFixedWidth(50)
        self.zoom_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            
            # Rendering DPI based on zoom to keep sharpness
            # Base 72 DPI at 1.0 zoom.
            current_dpi = int(72 * self.zoom_level)
            
            # Limit preview to first 20 pages to prevent memory issues/crashes with large/scanned docs
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
