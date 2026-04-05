import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class LicenseActivationDialog(QDialog):
    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("Activate Pro License")
        self.setModal(True)
        self.setMinimumSize(620, 360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Activate Pro")
        title.setFont(QFont("Plus Jakarta Sans", 18, QFont.Weight.DemiBold))
        layout.addWidget(title)

        subtitle = QLabel(
            "Paste your license key from the purchase email. "
            "Validation is performed locally and offline."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #8b949e;")
        layout.addWidget(subtitle)

        self.key_input = QPlainTextEdit()
        self.key_input.setPlaceholderText("PTL1.<payload>.<signature>")
        self.key_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.key_input.setMinimumHeight(180)
        layout.addWidget(self.key_input)

        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet("color: #ef4444;")
        layout.addWidget(self.feedback_label)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        activate_btn = QPushButton("Activate")
        activate_btn.clicked.connect(self._activate)
        activate_btn.setStyleSheet(
            "QPushButton {"
            "background-color: #2dd4bf;"
            "color: #0a0f14;"
            "font-weight: 600;"
            "padding: 8px 16px;"
            "border-radius: 8px;"
            "}"
            "QPushButton:hover { background-color: #5eead4; }"
        )

        buttons.addWidget(cancel_btn)
        buttons.addWidget(activate_btn)
        layout.addLayout(buttons)

    def _activate(self):
        token = self.key_input.toPlainText().strip()
        if not token:
            self.feedback_label.setText("Please paste a license key.")
            return

        result = self.license_manager.activate_license_key(token)
        if result.success:
            self.feedback_label.setStyleSheet("color: #22c55e;")
            self.feedback_label.setText("License activated successfully.")
            QMessageBox.information(self, "License Activated", "Pro license is now active.")
            self.accept()
            return

        self.feedback_label.setStyleSheet("color: #ef4444;")
        self.feedback_label.setText(result.message)


def show_pro_feature_locked_dialog(parent, feature_name, license_manager) -> bool:
    """
    Show upgrade prompt for a locked Pro feature.
    Returns True if the user activated a valid license during this flow.
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("Pro Feature")
    msg.setText(f"{feature_name} is available in Pro.")
    msg.setInformativeText(
        "Purchase a Pro license in your browser, then activate it in the app."
    )

    purchase_url = os.environ.get("PDF_TOOLS_PRO_UPGRADE_URL", "").strip()
    purchase_btn = None
    if purchase_url:
        purchase_btn = msg.addButton("Purchase Pro", QMessageBox.ButtonRole.ActionRole)

    activate_btn = msg.addButton("Activate License", QMessageBox.ButtonRole.ActionRole)
    msg.addButton(QMessageBox.StandardButton.Cancel)
    msg.exec()

    if purchase_btn is not None and msg.clickedButton() == purchase_btn:
        QDesktopServices.openUrl(QUrl(purchase_url))
        return False

    if msg.clickedButton() == activate_btn:
        dialog = LicenseActivationDialog(license_manager=license_manager, parent=parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return license_manager.has_valid_pro_license()

    return False


def open_activation_dialog(parent, license_manager) -> bool:
    dialog = LicenseActivationDialog(license_manager=license_manager, parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
