from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPalette
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView

    PDF_PREVIEW_AVAILABLE = True
except ImportError:
    PDF_PREVIEW_AVAILABLE = False
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pdf_converter.converter import convert_images_to_pdf, normalize_paths


class DropListWidget(QListWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__()
        self.parent_window = parent
        self._drag_active = False
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSpacing(8)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        self.empty_label = QLabel("여기에 이미지를 끌어다 놓으세요", self.viewport())
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("dropEmptyLabel")

        self.overlay_label = QLabel("여기에 놓으면 PDF 목록에 추가됩니다", self.viewport())
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setWordWrap(True)
        self.overlay_label.setObjectName("dropOverlay")
        self.overlay_label.hide()

        self._apply_normal_style()
        self.refresh_state()

    def _apply_normal_style(self) -> None:
        self.setStyleSheet(
            """
            QListWidget {
                border: 2px dashed #9ab6d3;
                border-radius: 24px;
                padding: 18px;
                background: #f8fbff;
                font-size: 14px;
                color: #17324d;
                outline: none;
            }
            QListWidget::item {
                min-height: 52px;
                padding: 8px 14px;
                border: 1px solid #d9e6f2;
                border-radius: 14px;
                background: white;
            }
            QListWidget::item:hover {
                border-color: #87aeda;
                background: #f6faff;
            }
            QListWidget::item:selected {
                border-color: #2f6fed;
                background: #eaf2ff;
                color: #143a75;
            }
            """
        )

    def _apply_drag_style(self) -> None:
        self.setStyleSheet(
            """
            QListWidget {
                border: 2px dashed #2f6fed;
                border-radius: 24px;
                padding: 18px;
                background: #eef5ff;
                font-size: 14px;
                color: #17324d;
                outline: none;
            }
            QListWidget::item {
                min-height: 52px;
                padding: 8px 14px;
                border: 1px solid #d9e6f2;
                border-radius: 14px;
                background: white;
            }
            QListWidget::item:selected {
                border-color: #2f6fed;
                background: #eaf2ff;
                color: #143a75;
            }
            """
        )

    def _set_drag_active(self, active: bool) -> None:
        self._drag_active = active
        if active:
            self._apply_drag_style()
            self.overlay_label.show()
        else:
            self._apply_normal_style()
            self.overlay_label.hide()
        self._update_helper_visibility()

    def _update_helper_visibility(self) -> None:
        has_items = self.count() > 0
        self.empty_label.setVisible(not has_items and not self._drag_active)
        self.empty_label.raise_()
        self.overlay_label.raise_()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        viewport_rect = self.viewport().rect()
        inset = 20
        self.empty_label.setGeometry(viewport_rect)
        self.overlay_label.setGeometry(
            inset,
            inset,
            max(0, viewport_rect.width() - inset * 2),
            max(0, viewport_rect.height() - inset * 2),
        )

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        self._set_drag_active(False)
        self.parent_window.add_images(paths)
        event.acceptProposedAction()

    def refresh_state(self) -> None:
        self._update_helper_visibility()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Converter")
        self.resize(960, 720)
        self.image_paths: list[Path] = []
        self.preview_pdf_path: Path | None = None
        self.pdf_document = QPdfDocument(self) if PDF_PREVIEW_AVAILABLE else None
        self.pdf_view: QPdfView | None = None
        self.setStyleSheet(self._build_stylesheet())
        self._build_ui()
        self._apply_window_icon()

    def _apply_window_icon(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        icon_candidates = [
            project_root / "assets" / "app_icon.ico",
            project_root / "assets" / "app_icon.png",
        ]

        for icon_path in icon_candidates:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                return

    def _build_stylesheet(self) -> str:
        return """
        QMainWindow {
            background: #eef4fb;
            color: #17324d;
        }
        QWidget {
            color: #17324d;
        }
        QLabel {
            background: transparent;
        }
        QToolBar {
            spacing: 8px;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.88);
            border: none;
            border-bottom: 1px solid #dbe7f3;
        }
        QScrollArea {
            border: none;
            background: transparent;
        }
        QToolButton {
            padding: 10px 14px;
            border: 1px solid transparent;
            border-radius: 12px;
            background: transparent;
            color: #23415f;
            font-size: 14px;
            font-weight: 600;
        }
        QToolButton:hover {
            background: #f0f6fd;
            border-color: #d7e4f0;
        }
        QToolButton:pressed {
            background: #e5effc;
        }
        QLabel#eyebrow {
            color: #2f6fed;
            background: #e8f0ff;
            border-radius: 10px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        QLabel#title {
            color: #10253d;
            font-size: 30px;
            font-weight: 700;
        }
        QLabel#subtitle {
            color: #5d748c;
            font-size: 15px;
        }
        QFrame#heroCard, QFrame#dropCard, QFrame#infoCard {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid #dce8f4;
            border-radius: 28px;
        }
        QLabel#countBadge {
            color: #10253d;
            background: #f4f8fd;
            border: 1px solid #d8e5f2;
            border-radius: 14px;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: 600;
        }
        QLabel#dropHintTitle, QLabel#sectionTitle {
            color: #10253d;
            font-size: 18px;
            font-weight: 700;
        }
        QLabel#dropHintText, QLabel#statusLabel {
            color: #60778f;
            font-size: 13px;
        }
        QLabel#dropEmptyLabel {
            color: #88a0ba;
            font-size: 16px;
            font-weight: 600;
        }
        QLabel#dropOverlay {
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            background: rgba(47, 111, 237, 0.78);
            border: 2px dashed rgba(255, 255, 255, 0.85);
            border-radius: 22px;
            padding: 24px;
        }
        QLabel#previewLabel {
            color: #60778f;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.4px;
        }
        QLabel#previewTitle {
            color: #11263f;
            font-size: 16px;
            font-weight: 700;
        }
        QLabel#previewBody {
            color: #597089;
            font-size: 12px;
        }
        QLabel#previewPlaceholder {
            background: #edf4fd;
            color: #5f7b98;
            border: 1px dashed #c8d9ea;
            border-radius: 18px;
            font-size: 15px;
            font-weight: 600;
            padding: 28px;
        }
        QFrame#previewPage {
            background: #ffffff;
            border: 1px solid #dbe7f3;
            border-radius: 22px;
        }
        QFrame#previewPaper {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #ffffff, stop:1 #f5f9ff);
            border: 1px solid #e1eaf3;
            border-radius: 20px;
        }
        QPdfView {
            background: #edf4fd;
            border: 1px solid #d9e6f2;
            border-radius: 18px;
        }
        QLabel#paperCaption {
            color: #60778f;
            font-size: 11px;
            font-weight: 600;
        }
        QPushButton#primaryButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1f6feb, stop:1 #4b7cf3);
            color: white;
            border: none;
            border-radius: 18px;
            padding: 14px 18px;
            font-size: 16px;
            font-weight: 700;
        }
        QPushButton#primaryButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #195fc9, stop:1 #416fe0);
        }
        QPushButton#primaryButton:pressed {
            background: #1b55b3;
        }
        QPushButton#secondaryButton {
            background: #ffffff;
            color: #24405d;
            border: 1px solid #d7e3ef;
            border-radius: 16px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
        }
        QPushButton#secondaryButton:hover {
            background: #f5f9fe;
            border-color: #c7d9ea;
        }
        """

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_action = QAction("이미지 추가", self)
        add_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_action.triggered.connect(self.open_file_dialog)
        toolbar.addAction(add_action)

        clear_action = QAction("목록 비우기", self)
        clear_action.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        clear_action.triggered.connect(self.clear_images)
        toolbar.addAction(clear_action)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(16)

        hero_text_layout = QVBoxLayout()
        hero_text_layout.setSpacing(10)

        eyebrow = QLabel("FAST LOCAL CONVERSION")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        hero_text_layout.addWidget(eyebrow)

        title = QLabel("이미지를 한 번에 정리해\n깔끔한 PDF로 변환합니다")
        title.setObjectName("title")
        hero_text_layout.addWidget(title)

        subtitle = QLabel(
            "드래그앤드롭으로 이미지를 추가하고, 순서대로 한 개의 PDF로 저장하세요.\n"
            "모든 페이지는 A4 기준으로 맞춰지며, 온라인 업로드 없이 로컬에서 바로 처리됩니다."
        )
        subtitle.setObjectName("subtitle")
        hero_text_layout.addWidget(subtitle)
        hero_text_layout.addStretch(1)
        hero_layout.addLayout(hero_text_layout, stretch=1)

        self.count_badge = QLabel("0개 이미지 준비됨")
        self.count_badge.setObjectName("countBadge")
        self.count_badge.setAlignment(Qt.AlignCenter)
        self.count_badge.setMinimumWidth(170)
        hero_layout.addWidget(self.count_badge, alignment=Qt.AlignTop)

        layout.addWidget(hero_card)

        drop_card = QFrame()
        drop_card.setObjectName("dropCard")
        drop_layout = QVBoxLayout(drop_card)
        drop_layout.setContentsMargins(22, 22, 22, 22)
        drop_layout.setSpacing(14)

        drop_header = QHBoxLayout()
        drop_header.setSpacing(12)

        drop_hint_box = QVBoxLayout()
        drop_hint_box.setSpacing(4)

        drop_hint_title = QLabel("드롭 영역")
        drop_hint_title.setObjectName("dropHintTitle")
        drop_hint_box.addWidget(drop_hint_title)

        drop_hint_text = QLabel("JPG, PNG, BMP, TIFF, WEBP, GIF 파일을 추가할 수 있습니다.")
        drop_hint_text.setObjectName("dropHintText")
        drop_hint_box.addWidget(drop_hint_text)

        drop_header.addLayout(drop_hint_box, stretch=1)

        select_button = QPushButton("파일 선택")
        select_button.setObjectName("secondaryButton")
        select_button.setCursor(Qt.PointingHandCursor)
        select_button.clicked.connect(self.open_file_dialog)
        drop_header.addWidget(select_button)

        drop_layout.addLayout(drop_header)

        self.drop_list = DropListWidget(self)
        self.drop_list.setMinimumHeight(180)
        drop_layout.addWidget(self.drop_list)

        preview_title = QLabel("PDF 미리보기")
        preview_title.setObjectName("sectionTitle")
        drop_layout.addWidget(preview_title)

        preview_page = QFrame()
        preview_page.setObjectName("previewPage")
        preview_page_layout = QVBoxLayout(preview_page)
        preview_page_layout.setContentsMargins(18, 18, 18, 18)
        preview_page_layout.setSpacing(14)

        self.preview_label = QLabel("PDF PREVIEW")
        self.preview_label.setObjectName("previewLabel")
        preview_page_layout.addWidget(self.preview_label)

        self.preview_title = QLabel("이미지를 추가하면 실제 PDF가 미리 표시됩니다")
        self.preview_title.setObjectName("previewTitle")
        preview_page_layout.addWidget(self.preview_title)

        self.preview_body = QLabel(
            "이미지를 넣으면 임시 PDF를 만들어 A4 기준 실제 전체 페이지를 미리 보여줍니다."
        )
        self.preview_body.setObjectName("previewBody")
        self.preview_body.setWordWrap(True)
        preview_page_layout.addWidget(self.preview_body)

        preview_paper = QFrame()
        preview_paper.setObjectName("previewPaper")
        preview_paper_layout = QVBoxLayout(preview_paper)
        preview_paper_layout.setContentsMargins(20, 20, 20, 18)
        preview_paper_layout.setSpacing(14)

        paper_header = QHBoxLayout()
        paper_header.setSpacing(10)

        paper_title = QLabel("실제 PDF 전체 페이지")
        paper_title.setObjectName("previewTitle")
        paper_header.addWidget(paper_title)
        paper_header.addStretch(1)

        self.paper_caption = QLabel("preview unavailable")
        self.paper_caption.setObjectName("paperCaption")
        paper_header.addWidget(self.paper_caption)

        preview_paper_layout.addLayout(paper_header)

        self.preview_placeholder = QLabel(
            "이미지를 추가하면 실제 PDF 전체 페이지 미리보기가 여기에 표시됩니다."
        )
        self.preview_placeholder.setObjectName("previewPlaceholder")
        self.preview_placeholder.setAlignment(Qt.AlignCenter)
        self.preview_placeholder.setWordWrap(True)
        self.preview_placeholder.setMinimumHeight(420)
        preview_paper_layout.addWidget(self.preview_placeholder)

        if PDF_PREVIEW_AVAILABLE:
            self.pdf_view = QPdfView()
            self.pdf_view.setDocument(self.pdf_document)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self.pdf_view.setMinimumHeight(420)
            self.pdf_view.hide()
            preview_paper_layout.addWidget(self.pdf_view)

        preview_page_layout.addWidget(preview_paper)
        drop_layout.addWidget(preview_page)

        layout.addWidget(drop_card, stretch=1)

        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(16)

        self.status_label = QLabel("이미지를 추가해 주세요.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        info_layout.addWidget(self.status_label, stretch=1)

        convert_button = QPushButton("PDF로 저장")
        convert_button.setObjectName("primaryButton")
        convert_button.setCursor(Qt.PointingHandCursor)
        convert_button.setMinimumHeight(54)
        convert_button.setMinimumWidth(220)
        convert_button.clicked.connect(self.save_pdf)
        info_layout.addWidget(convert_button)

        layout.addWidget(info_card)

        scroll_area.setWidget(content_widget)
        self.setCentralWidget(scroll_area)
        self._refresh_ui_state()

    def _preview_temp_path(self) -> Path:
        return Path(tempfile.gettempdir()) / "pdf_converter_preview.pdf"

    def _remove_preview_file(self) -> None:
        if self.preview_pdf_path is None:
            return
        try:
            self.preview_pdf_path.unlink(missing_ok=True)
        except OSError:
            pass
        self.preview_pdf_path = None

    def _clear_pdf_preview(self) -> None:
        if self.pdf_document is not None:
            self.pdf_document.close()
        self._remove_preview_file()
        self.preview_placeholder.show()
        if self.pdf_view is not None:
            self.pdf_view.hide()

    def _refresh_pdf_preview(self) -> None:
        if not self.image_paths:
            self._clear_pdf_preview()
            return

        if not PDF_PREVIEW_AVAILABLE or self.pdf_document is None or self.pdf_view is None:
            self.preview_placeholder.setText(
                "현재 PySide6 환경에 PDF 미리보기 모듈이 없어 저장 후 외부 PDF 앱에서 확인해야 합니다."
            )
            self.preview_placeholder.show()
            return

        preview_path = self._preview_temp_path()
        try:
            convert_images_to_pdf(self.image_paths, preview_path)
            self.pdf_document.close()
            load_error = self.pdf_document.load(str(preview_path))
        except Exception as error:  # noqa: BLE001
            self.preview_placeholder.setText(f"PDF 미리보기를 만드는 중 오류가 발생했습니다.\n{error}")
            self.preview_placeholder.show()
            self.pdf_view.hide()
            return

        if load_error != QPdfDocument.Error.None_:
            self.preview_placeholder.setText("PDF 미리보기를 불러오지 못했습니다.")
            self.preview_placeholder.show()
            self.pdf_view.hide()
            return

        self.preview_pdf_path = preview_path
        self.preview_placeholder.hide()
        self.pdf_view.show()
        self.pdf_view.pageNavigator().jump(0)

    def _refresh_ui_state(self) -> None:
        count = len(self.image_paths)
        self.count_badge.setText(f"{count}개 이미지 준비됨")
        self.drop_list.refresh_state()

        if count == 0:
            self.status_label.setText("이미지를 추가해 주세요.")
            self.preview_label.setText("PDF PREVIEW")
            self.preview_title.setText("이미지를 추가하면 실제 PDF가 미리 표시됩니다")
            self.preview_body.setText(
                "이미지를 넣으면 임시 PDF를 만들어 A4 기준 실제 전체 페이지를 미리 보여줍니다."
            )
            self.paper_caption.setText("preview unavailable")
            self.preview_placeholder.setText(
                "이미지를 추가하면 실제 PDF 전체 페이지 미리보기가 여기에 표시됩니다."
            )
            self._clear_pdf_preview()
            return

        self.status_label.setText(
            f"현재 {count}개 이미지가 준비되었습니다. 첫 번째 이미지 폴더를 기본 저장 위치로 사용합니다."
        )
        self.preview_label.setText(f"PDF PREVIEW · {count} PAGE{'S' if count > 1 else ''}")
        self.preview_title.setText(f"{count}장의 이미지가 순서대로 PDF 페이지로 저장됩니다")
        first_name = self.image_paths[0].name
        self.preview_body.setText(
            f"첫 페이지는 '{first_name}' 기준으로 시작합니다. 모든 페이지는 A4 크기에 맞춰 저장되며, 아래는 그 실제 전체 페이지 미리보기입니다."
        )
        self.paper_caption.setText(f"{count} page{'s' if count > 1 else ''} output")
        self._refresh_pdf_preview()

    def open_file_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "이미지 선택",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif)",
        )
        self.add_images(files)

    def add_images(self, raw_paths: list[str]) -> None:
        new_paths = normalize_paths(raw_paths)
        existing = set(self.image_paths)

        added_count = 0
        for path in new_paths:
            if path in existing:
                continue

            self.image_paths.append(path)
            item = QListWidgetItem(path.name)
            item.setToolTip(str(path))
            self.drop_list.addItem(item)
            existing.add(path)
            added_count += 1

        if added_count == 0 and raw_paths:
            self.status_label.setText("추가 가능한 새 이미지가 없었습니다.")
            return

        self._refresh_ui_state()

    def clear_images(self) -> None:
        self.image_paths.clear()
        self.drop_list.clear()
        self._refresh_ui_state()

    def save_pdf(self) -> None:
        if not self.image_paths:
            QMessageBox.warning(self, "이미지 없음", "먼저 변환할 이미지를 추가해 주세요.")
            return

        first_path = self.image_paths[0]
        default_name = first_path.with_suffix(".pdf").name

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF 저장",
            str(first_path.parent / default_name),
            "PDF Files (*.pdf)",
        )
        if not output_path:
            return

        try:
            saved_path = convert_images_to_pdf(self.image_paths, output_path)
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "변환 실패", f"PDF 변환 중 오류가 발생했습니다.\n{error}")
            return

        QMessageBox.information(self, "변환 완료", f"PDF 저장 완료:\n{saved_path}")
        self.status_label.setText(f"저장 완료: {saved_path.name}")
        self.preview_title.setText(f"{saved_path.name} 실제 PDF 미리보기")
        self.preview_body.setText(
            f"방금 저장한 PDF는 총 {len(self.image_paths)}페이지 기준으로 생성되었습니다. 아래 미리보기와 같은 내용으로 저장됩니다."
        )
        self._refresh_pdf_preview()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._clear_pdf_preview()
        super().closeEvent(event)


def configure_application(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#eef4fb"))
    palette.setColor(QPalette.WindowText, QColor("#17324d"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f4f8fd"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#17324d"))
    palette.setColor(QPalette.Text, QColor("#17324d"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#17324d"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor("#2f6fed"))
    palette.setColor(QPalette.Highlight, QColor("#2f6fed"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)


def main() -> int:
    app = QApplication(sys.argv)
    configure_application(app)
    window = MainWindow()
    window.show()
    return app.exec()
