from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QIcon, QPalette

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    PDF_PREVIEW_AVAILABLE = True
except ImportError:
    PDF_PREVIEW_AVAILABLE = False

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pdf_converter.converter import (
    classify_image_paths,
    classify_pdf_paths,
    convert_images_to_pdf,
    get_pdf_page_count,
    merge_pdfs,
    split_pdf,
)

MODE_IMAGE_TO_PDF = "image_to_pdf"
MODE_PDF_MERGE = "pdf_merge"
MODE_PDF_SPLIT = "pdf_split"

RESULT_KIND_PDF = "pdf"
RESULT_KIND_DIRECTORY = "directory"


class DropListWidget(QListWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__()
        self.parent_window = parent
        self._drag_active = False
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.empty_label = QLabel("", self.viewport())
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.overlay_label = QLabel("", self.viewport())
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setWordWrap(True)
        self.overlay_label.hide()
        self._apply_style()
        self.refresh_state()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QListWidget { border: 2px dashed #9ab6d3; border-radius: 20px; padding: 16px; background: #f8fbff; }"
            "QListWidget::item { min-height: 44px; padding: 8px 12px; border: 1px solid #d9e6f2; border-radius: 12px; background: white; }"
            "QListWidget::item:selected { border-color: #2f6fed; background: #eaf2ff; }"
        )

    def set_helper_texts(self, empty_text: str, overlay_text: str) -> None:
        self.empty_label.setText(empty_text)
        self.overlay_label.setText(overlay_text)
        self.refresh_state()

    def _set_drag_active(self, active: bool) -> None:
        self._drag_active = active
        self.overlay_label.setVisible(active)
        self._update_helper_visibility()

    def _update_helper_visibility(self) -> None:
        self.empty_label.setVisible(self.count() == 0 and not self._drag_active)
        self.empty_label.raise_()
        self.overlay_label.raise_()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        rect = self.viewport().rect()
        self.empty_label.setGeometry(rect)
        self.overlay_label.setGeometry(16, 16, max(0, rect.width() - 32), max(0, rect.height() - 32))

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.source() is self or event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.source() is self or event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if event.source() is self:
            self._set_drag_active(False)
            super().dropEvent(event)
            self.parent_window.sync_input_order_from_list()
            self.refresh_state()
            event.acceptProposedAction()
            return
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self._set_drag_active(False)
        self.parent_window.add_files(paths)
        event.acceptProposedAction()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.parent_window.remove_selected_files()
            event.accept()
            return
        super().keyPressEvent(event)

    def refresh_state(self) -> None:
        self._update_helper_visibility()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Toolkit")
        self.resize(980, 760)
        self.mode = MODE_IMAGE_TO_PDF
        self.input_paths: list[Path] = []
        self.last_output_target: Path | None = None
        self.last_output_kind: str | None = None
        self.preview_pdf_path: Path | None = None
        self.is_processing = False
        self.pdf_document = QPdfDocument(self) if PDF_PREVIEW_AVAILABLE else None
        self.pdf_view: QPdfView | None = None
        self.setStyleSheet(self._build_stylesheet())
        self._build_ui()
        self._apply_window_icon()
        self._apply_mode_ui(reset_list=True)

    def _apply_window_icon(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        for icon_path in [project_root / "assets" / "app_icon.ico", project_root / "assets" / "app_icon.png"]:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                return

    def _build_stylesheet(self) -> str:
        return """
        QMainWindow { background: #eef4fb; color: #17324d; }
        QFrame#card { background: rgba(255,255,255,0.96); border: 1px solid #dce8f4; border-radius: 24px; }
        QLabel#eyebrow { color: #2f6fed; background: #e8f0ff; border-radius: 10px; padding: 6px 10px; font-size: 12px; font-weight: 700; }
        QLabel#title { color: #10253d; font-size: 28px; font-weight: 700; }
        QLabel#subtitle, QLabel#statusLabel, QLabel#hintText, QLabel#previewBody { color: #60778f; font-size: 13px; }
        QLabel#sectionTitle, QLabel#previewTitle { color: #10253d; font-size: 18px; font-weight: 700; }
        QLabel#countBadge { background: #f4f8fd; border: 1px solid #d8e5f2; border-radius: 14px; padding: 10px 14px; font-weight: 600; }
        QPushButton#modeButton, QPushButton#secondaryButton { background: white; border: 1px solid #d7e3ef; border-radius: 14px; padding: 10px 14px; font-weight: 600; }
        QPushButton#modeButton:checked { background: #e8f0ff; border-color: #8eb2f2; color: #153d7d; }
        QPushButton#primaryButton { background: #2f6fed; color: white; border: none; border-radius: 16px; padding: 12px 18px; font-weight: 700; }
        QPushButton:disabled { color: #8aa0b5; background: #f4f7fb; border-color: #d9e3ec; }
        QLabel#previewPlaceholder { background: #edf4fd; color: #5f7b98; border: 1px dashed #c8d9ea; border-radius: 18px; padding: 24px; }
        QProgressBar { border: 1px solid #d5e1ec; border-radius: 12px; background: #f4f8fd; text-align: center; min-height: 18px; }
        QProgressBar::chunk { border-radius: 11px; background: #2f6fed; }
        """

    def _mode_config(self) -> dict[str, object]:
        if self.mode == MODE_IMAGE_TO_PDF:
            return {
                "title": "이미지를 한 번에 정리해\n깔끔한 PDF로 변환합니다",
                "subtitle": "여러 이미지를 추가하고 순서를 조정한 뒤 하나의 PDF로 저장하세요.",
                "hint_title": "이미지 드롭 영역",
                "hint_text": "JPG, PNG, BMP, TIFF, WEBP, GIF 파일을 추가할 수 있습니다.",
                "empty": "여기에 이미지를 끌어다 놓으세요",
                "overlay": "놓으면 이미지 목록에 추가됩니다",
                "select": "이미지 선택",
                "action": "PDF로 저장",
                "save_title": "PDF 저장",
                "filter": "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp *.gif)",
                "status_empty": "이미지를 추가해 주세요.",
                "preview_title": "이미지를 추가하면 실제 PDF가 미리 표시됩니다",
                "preview_body": "A4 기준으로 변환된 결과를 저장 전에 확인할 수 있습니다.",
                "preview_placeholder": "이미지를 추가하면 미리보기가 여기에 표시됩니다.",
                "item_name": "이미지",
                "open_result": "PDF 열기",
                "minimum_count": 1,
            }
        if self.mode == MODE_PDF_MERGE:
            return {
                "title": "여러 PDF를 순서대로 합쳐\n하나의 PDF로 정리합니다",
                "subtitle": "여러 PDF 파일을 추가하고 순서를 정한 뒤 하나의 병합된 PDF로 저장하세요.",
                "hint_title": "PDF 드롭 영역",
                "hint_text": "PDF 파일을 추가하고 드래그로 병합 순서를 조정할 수 있습니다.",
                "empty": "여기에 PDF 파일을 끌어다 놓으세요",
                "overlay": "놓으면 PDF 병합 목록에 추가됩니다",
                "select": "PDF 선택",
                "action": "PDF 병합",
                "save_title": "병합 PDF 저장",
                "filter": "PDF Files (*.pdf)",
                "status_empty": "병합할 PDF를 추가해 주세요.",
                "preview_title": "PDF 2개 이상을 추가하면 병합 결과 미리보기가 표시됩니다",
                "preview_body": "병합 순서에 따라 만들어질 최종 PDF를 저장 전에 확인할 수 있습니다.",
                "preview_placeholder": "PDF 2개 이상을 추가하면 병합 미리보기가 여기에 표시됩니다.",
                "item_name": "PDF",
                "open_result": "PDF 열기",
                "minimum_count": 2,
            }
        return {
            "title": "하나의 PDF를 페이지별로 나눠\n개별 PDF 파일로 저장합니다",
            "subtitle": "한 개의 PDF를 추가한 뒤 결과 폴더를 선택하면 페이지별 PDF 파일을 자동으로 만듭니다.",
            "hint_title": "PDF 분할 영역",
            "hint_text": "분할 모드에서는 PDF 1개만 추가할 수 있으며, 페이지별 PDF 파일이 생성됩니다.",
            "empty": "여기에 분할할 PDF 파일을 끌어다 놓으세요",
            "overlay": "놓으면 분할할 PDF가 추가됩니다",
            "select": "PDF 선택",
            "action": "PDF 분할",
            "save_title": "분할 결과 폴더 선택",
            "filter": "PDF Files (*.pdf)",
            "status_empty": "분할할 PDF를 추가해 주세요.",
            "preview_title": "선택한 PDF 원본이 미리보기로 표시됩니다",
            "preview_body": "저장 시 각 페이지가 개별 PDF 파일로 분리됩니다.",
            "preview_placeholder": "PDF 1개를 추가하면 원본 미리보기가 여기에 표시됩니다.",
            "item_name": "PDF",
            "open_result": "결과 폴더 열기",
            "minimum_count": 1,
        }

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.add_action = QAction("파일 추가", self)
        self.add_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.add_action.triggered.connect(self.open_file_dialog)
        toolbar.addAction(self.add_action)

        self.remove_action = QAction("선택 삭제", self)
        self.remove_action.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.remove_action.triggered.connect(self.remove_selected_files)
        toolbar.addAction(self.remove_action)

        self.clear_action = QAction("목록 비우기", self)
        self.clear_action.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_action.triggered.connect(self.clear_files)
        toolbar.addAction(self.clear_action)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hero_card = QFrame()
        hero_card.setObjectName("card")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(14)

        eyebrow = QLabel("FAST LOCAL PDF TOOL")
        eyebrow.setObjectName("eyebrow")
        hero_layout.addWidget(eyebrow)

        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        hero_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setWordWrap(True)
        hero_layout.addWidget(self.subtitle_label)

        mode_row = QHBoxLayout()
        self.image_mode_button = QPushButton("이미지 → PDF")
        self.image_mode_button.setObjectName("modeButton")
        self.image_mode_button.setCheckable(True)
        self.image_mode_button.clicked.connect(lambda: self.set_mode(MODE_IMAGE_TO_PDF))
        mode_row.addWidget(self.image_mode_button)

        self.merge_mode_button = QPushButton("PDF 병합")
        self.merge_mode_button.setObjectName("modeButton")
        self.merge_mode_button.setCheckable(True)
        self.merge_mode_button.clicked.connect(lambda: self.set_mode(MODE_PDF_MERGE))
        mode_row.addWidget(self.merge_mode_button)

        self.split_mode_button = QPushButton("PDF 분할")
        self.split_mode_button.setObjectName("modeButton")
        self.split_mode_button.setCheckable(True)
        self.split_mode_button.clicked.connect(lambda: self.set_mode(MODE_PDF_SPLIT))
        mode_row.addWidget(self.split_mode_button)
        mode_row.addStretch(1)

        self.count_badge = QLabel("0개 파일 준비됨")
        self.count_badge.setObjectName("countBadge")
        mode_row.addWidget(self.count_badge)
        hero_layout.addLayout(mode_row)
        layout.addWidget(hero_card)

        list_card = QFrame()
        list_card.setObjectName("card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(22, 22, 22, 22)
        list_layout.setSpacing(14)

        header_row = QHBoxLayout()
        hint_box = QVBoxLayout()
        self.hint_title_label = QLabel()
        self.hint_title_label.setObjectName("sectionTitle")
        hint_box.addWidget(self.hint_title_label)
        self.hint_text_label = QLabel()
        self.hint_text_label.setObjectName("hintText")
        self.hint_text_label.setWordWrap(True)
        hint_box.addWidget(self.hint_text_label)
        header_row.addLayout(hint_box, stretch=1)

        self.select_button = QPushButton("파일 선택")
        self.select_button.setObjectName("secondaryButton")
        self.select_button.clicked.connect(self.open_file_dialog)
        header_row.addWidget(self.select_button)

        self.remove_button = QPushButton("선택 삭제")
        self.remove_button.setObjectName("secondaryButton")
        self.remove_button.clicked.connect(self.remove_selected_files)
        header_row.addWidget(self.remove_button)
        list_layout.addLayout(header_row)

        self.drop_list = DropListWidget(self)
        self.drop_list.setMinimumHeight(180)
        self.drop_list.itemSelectionChanged.connect(self._refresh_ui_state)
        list_layout.addWidget(self.drop_list)

        preview_label = QLabel("PDF 미리보기")
        preview_label.setObjectName("sectionTitle")
        list_layout.addWidget(preview_label)

        self.preview_title = QLabel()
        self.preview_title.setObjectName("previewTitle")
        list_layout.addWidget(self.preview_title)

        self.preview_body = QLabel()
        self.preview_body.setObjectName("previewBody")
        self.preview_body.setWordWrap(True)
        list_layout.addWidget(self.preview_body)

        self.preview_placeholder = QLabel()
        self.preview_placeholder.setObjectName("previewPlaceholder")
        self.preview_placeholder.setAlignment(Qt.AlignCenter)
        self.preview_placeholder.setWordWrap(True)
        self.preview_placeholder.setMinimumHeight(420)
        list_layout.addWidget(self.preview_placeholder)

        if PDF_PREVIEW_AVAILABLE:
            self.pdf_view = QPdfView()
            self.pdf_view.setDocument(self.pdf_document)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            self.pdf_view.setMinimumHeight(420)
            self.pdf_view.hide()
            list_layout.addWidget(self.pdf_view)

        layout.addWidget(list_card, stretch=1)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(12)

        button_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        button_row.addWidget(self.status_label, stretch=1)

        self.open_result_button = QPushButton("결과 열기")
        self.open_result_button.setObjectName("secondaryButton")
        self.open_result_button.clicked.connect(self.open_last_result)
        button_row.addWidget(self.open_result_button)

        self.primary_action_button = QPushButton()
        self.primary_action_button.setObjectName("primaryButton")
        self.primary_action_button.clicked.connect(self.run_primary_action)
        button_row.addWidget(self.primary_action_button)
        info_layout.addLayout(button_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        info_layout.addWidget(self.progress_bar)
        layout.addWidget(info_card)

        scroll_area.setWidget(content_widget)
        self.setCentralWidget(scroll_area)

    def _preview_temp_path(self) -> Path:
        return Path(tempfile.gettempdir()) / "pdf_toolkit_preview.pdf"

    def _remove_preview_file(self) -> None:
        if self.preview_pdf_path is not None:
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

    def _set_processing_state(self, active: bool) -> None:
        self.is_processing = active
        widgets = [
            self.select_button,
            self.remove_button,
            self.open_result_button,
            self.primary_action_button,
            self.image_mode_button,
            self.merge_mode_button,
            self.split_mode_button,
        ]
        actions = [self.add_action, self.remove_action, self.clear_action]
        for widget in widgets:
            widget.setEnabled(not active)
        for action in actions:
            action.setEnabled(not active)
        self.progress_bar.setVisible(active)

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{message} (%v/%m)")
        self.status_label.setText(message)
        QApplication.processEvents()

    def _load_pdf_preview_from_path(self, pdf_path: Path) -> None:
        if self.pdf_document is None or self.pdf_view is None:
            return
        self.pdf_document.close()
        load_error = self.pdf_document.load(str(pdf_path))
        if load_error != QPdfDocument.Error.None_:
            self.preview_placeholder.setText("PDF 미리보기를 불러오지 못했습니다.")
            self.preview_placeholder.show()
            self.pdf_view.hide()
            return
        self.preview_placeholder.hide()
        self.pdf_view.show()
        self.pdf_view.pageNavigator().jump(0)

    def _refresh_preview(self) -> None:
        if not self.input_paths:
            self._clear_pdf_preview()
            return
        if self.mode == MODE_PDF_MERGE and len(self.input_paths) < 2:
            self._clear_pdf_preview()
            self.preview_placeholder.setText("PDF 병합 미리보기는 PDF 2개 이상일 때 표시됩니다.")
            return
        if not PDF_PREVIEW_AVAILABLE or self.pdf_document is None or self.pdf_view is None:
            self.preview_placeholder.setText("이 환경에서는 내장 PDF 미리보기를 사용할 수 없습니다. 저장 후 PDF 앱에서 확인해 주세요.")
            self.preview_placeholder.show()
            return

        try:
            if self.mode == MODE_IMAGE_TO_PDF:
                preview_path = self._preview_temp_path()
                convert_images_to_pdf(self.input_paths, preview_path)
                self.preview_pdf_path = preview_path
                self._load_pdf_preview_from_path(preview_path)
                return
            if self.mode == MODE_PDF_MERGE:
                preview_path = self._preview_temp_path()
                merge_pdfs(self.input_paths, preview_path)
                self.preview_pdf_path = preview_path
                self._load_pdf_preview_from_path(preview_path)
                return

            self._remove_preview_file()
            self._load_pdf_preview_from_path(self.input_paths[0])
        except Exception as error:  # noqa: BLE001
            self.preview_placeholder.setText(f"PDF 미리보기를 만드는 중 오류가 발생했습니다.\n{error}")
            self.preview_placeholder.show()
            if self.pdf_view is not None:
                self.pdf_view.hide()

    def set_mode(self, mode: str) -> None:
        if self.mode == mode or self.is_processing:
            return
        self.mode = mode
        self._apply_mode_ui(reset_list=True)

    def _apply_mode_ui(self, reset_list: bool) -> None:
        if reset_list:
            self.clear_files(reset_saved_result=True)
        config = self._mode_config()
        self.title_label.setText(str(config["title"]))
        self.subtitle_label.setText(str(config["subtitle"]))
        self.hint_title_label.setText(str(config["hint_title"]))
        self.hint_text_label.setText(str(config["hint_text"]))
        self.drop_list.set_helper_texts(str(config["empty"]), str(config["overlay"]))
        self.select_button.setText(str(config["select"]))
        self.primary_action_button.setText(str(config["action"]))
        self.open_result_button.setText(str(config["open_result"]))
        self.image_mode_button.setChecked(self.mode == MODE_IMAGE_TO_PDF)
        self.merge_mode_button.setChecked(self.mode == MODE_PDF_MERGE)
        self.split_mode_button.setChecked(self.mode == MODE_PDF_SPLIT)
        self.preview_title.setText(str(config["preview_title"]))
        self.preview_body.setText(str(config["preview_body"]))
        self.preview_placeholder.setText(str(config["preview_placeholder"]))
        self._refresh_ui_state(str(config["status_empty"]))

    def _refresh_ui_state(self, status_message: str | None = None) -> None:
        config = self._mode_config()
        count = len(self.input_paths)
        has_selection = bool(self.drop_list.selectedItems())
        has_result = self.last_output_target is not None and self.last_output_target.exists()
        minimum_count = int(config["minimum_count"])

        self.count_badge.setText(f"{count}개 {config['item_name']} 준비됨")
        self.remove_button.setEnabled(has_selection and not self.is_processing)
        self.remove_action.setEnabled(has_selection and not self.is_processing)
        self.clear_action.setEnabled(count > 0 and not self.is_processing)
        self.primary_action_button.setEnabled(count >= minimum_count and not self.is_processing)
        self.open_result_button.setEnabled(has_result and not self.is_processing)

        if count == 0:
            self.status_label.setText(status_message or str(config["status_empty"]))
            self.preview_title.setText(str(config["preview_title"]))
            self.preview_body.setText(str(config["preview_body"]))
            self.preview_placeholder.setText(str(config["preview_placeholder"]))
            self._clear_pdf_preview()
            return

        if self.mode == MODE_IMAGE_TO_PDF:
            preview_title = f"{count}장의 이미지가 순서대로 PDF 페이지로 저장됩니다"
            preview_body = f"첫 파일은 '{self.input_paths[0].name}' 입니다. 모든 페이지는 A4 크기에 맞춰 저장됩니다."
            status = f"현재 {count}개 이미지 파일이 준비되었습니다. 순서를 확인한 뒤 PDF 저장을 진행하세요."
        elif self.mode == MODE_PDF_MERGE:
            preview_title = f"{count}개의 PDF가 현재 순서대로 하나로 병합됩니다"
            preview_body = f"첫 파일은 '{self.input_paths[0].name}' 입니다. 병합 결과는 현재 목록 순서를 그대로 따릅니다."
            status = f"현재 {count}개 PDF 파일이 준비되었습니다. 순서를 확인한 뒤 PDF 병합을 진행하세요."
        else:
            try:
                page_count = get_pdf_page_count(self.input_paths[0])
                preview_title = f"'{self.input_paths[0].name}' 파일은 총 {page_count}페이지입니다"
                preview_body = "분할을 시작하면 각 페이지가 개별 PDF 파일로 생성되고 결과 폴더를 바로 열 수 있습니다."
            except Exception:
                preview_title = f"'{self.input_paths[0].name}' 파일을 페이지별 PDF로 분할할 수 있습니다"
                preview_body = "분할을 시작하면 각 페이지가 개별 PDF 파일로 생성됩니다."
            status = "PDF 1개가 준비되었습니다. 결과 폴더를 선택하면 페이지별 PDF 파일이 생성됩니다."

        self.preview_title.setText(preview_title)
        self.preview_body.setText(preview_body)
        self.status_label.setText(status_message or status)
        self._refresh_preview()

    def _default_output_name(self) -> str:
        first_path = self.input_paths[0]
        if self.mode == MODE_IMAGE_TO_PDF:
            return first_path.with_suffix(".pdf").name
        if self.mode == MODE_PDF_MERGE:
            return f"{first_path.stem}-merged.pdf"
        return f"{first_path.stem}-split"

    def open_file_dialog(self) -> None:
        config = self._mode_config()
        files, _ = QFileDialog.getOpenFileNames(self, str(config["select"]), "", str(config["filter"]))
        self.add_files(files)

    def add_files(self, raw_paths: list[str]) -> None:
        classifier = classify_image_paths if self.mode == MODE_IMAGE_TO_PDF else classify_pdf_paths
        new_paths, duplicate_count, unsupported_count = classifier(raw_paths, existing_paths=self.input_paths)
        limited_count = 0

        if self.mode == MODE_PDF_SPLIT:
            if self.input_paths:
                limited_count = len(new_paths)
                new_paths = []
            elif len(new_paths) > 1:
                limited_count = len(new_paths) - 1
                new_paths = new_paths[:1]

        for path in new_paths:
            self.input_paths.append(path)
            item = QListWidgetItem(path.name)
            item.setToolTip(str(path))
            item.setData(Qt.UserRole, str(path))
            self.drop_list.addItem(item)

        added_count = len(new_paths)
        if added_count == 0 and raw_paths:
            if self.mode == MODE_PDF_SPLIT and limited_count > 0:
                message = "PDF 분할 모드에서는 한 번에 PDF 1개만 추가할 수 있습니다."
            elif unsupported_count > 0 and duplicate_count > 0:
                message = "지원되지 않는 파일과 중복 파일은 추가되지 않았습니다."
            elif unsupported_count > 0:
                message = "지원되지 않는 파일은 추가되지 않았습니다."
            elif duplicate_count > 0:
                message = "이미 목록에 있는 파일은 다시 추가하지 않았습니다."
            else:
                message = "추가 가능한 파일이 없습니다."
            self._refresh_ui_state(message)
            return

        feedback: list[str] = []
        if added_count > 0:
            feedback.append(f"{added_count}개 파일 추가됨")
        if duplicate_count > 0:
            feedback.append(f"중복 {duplicate_count}개 제외")
        if unsupported_count > 0:
            feedback.append(f"지원 불가 {unsupported_count}개 제외")
        if limited_count > 0:
            feedback.append(f"분할 모드 제한 {limited_count}개 제외")

        if feedback:
            self._refresh_ui_state(" / ".join(feedback))
            return
        self._refresh_ui_state()

    def clear_files(self, reset_saved_result: bool = True) -> None:
        self.input_paths.clear()
        self.drop_list.clear()
        if reset_saved_result:
            self.last_output_target = None
            self.last_output_kind = None
        self._refresh_ui_state()

    def remove_selected_files(self) -> None:
        selected_items = self.drop_list.selectedItems()
        if not selected_items:
            self._refresh_ui_state()
            return
        selected_paths = {Path(item.data(Qt.UserRole)) for item in selected_items if item.data(Qt.UserRole)}
        for item in selected_items:
            self.drop_list.takeItem(self.drop_list.row(item))
        self.input_paths = [path for path in self.input_paths if path not in selected_paths]
        self._refresh_ui_state(f"{len(selected_items)}개 항목을 목록에서 제거했습니다.")

    def sync_input_order_from_list(self) -> None:
        reordered_paths: list[Path] = []
        for index in range(self.drop_list.count()):
            raw_path = self.drop_list.item(index).data(Qt.UserRole)
            if raw_path:
                reordered_paths.append(Path(raw_path))
        if reordered_paths:
            self.input_paths = reordered_paths
            self._refresh_ui_state("파일 순서를 업데이트했습니다.")
            return
        self._refresh_ui_state()

    def open_last_result(self) -> None:
        if self.last_output_target is None or not self.last_output_target.exists():
            QMessageBox.information(self, "열 수 있는 결과 없음", "먼저 작업을 완료해 주세요.")
            self._refresh_ui_state()
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output_target))):
            QMessageBox.warning(self, "열기 실패", "기본 앱으로 결과를 열지 못했습니다.")
            return
        self._refresh_ui_state(f"결과 열기: {self.last_output_target.name}")

    def run_primary_action(self) -> None:
        if self.mode == MODE_IMAGE_TO_PDF:
            self.save_image_pdf()
        elif self.mode == MODE_PDF_MERGE:
            self.save_merged_pdf()
        else:
            self.save_split_pdf()

    def _run_export(self, action_name: str, worker, output_target: str | Path, result_kind: str) -> None:
        self._set_processing_state(True)
        try:
            result_path = worker(self.input_paths, output_target, progress_callback=self._update_progress)
        except Exception as error:  # noqa: BLE001
            self._set_processing_state(False)
            QMessageBox.critical(self, f"{action_name} 실패", f"작업 중 오류가 발생했습니다.\n{error}")
            self._refresh_ui_state(f"{action_name} 실패")
            return

        self.last_output_target = Path(result_path)
        self.last_output_kind = result_kind
        self._set_processing_state(False)

        if result_kind == RESULT_KIND_DIRECTORY:
            QMessageBox.information(self, f"{action_name} 완료", f"완료된 폴더:\n{result_path}")
            self._refresh_ui_state(f"{action_name} 완료: {Path(result_path).name} 폴더")
        else:
            QMessageBox.information(self, f"{action_name} 완료", f"완료된 파일:\n{result_path}")
            self._refresh_ui_state(f"{action_name} 완료: {Path(result_path).name}")
        self._refresh_preview()

    def save_image_pdf(self) -> None:
        if not self.input_paths:
            QMessageBox.warning(self, "이미지 없음", "먼저 변환할 이미지를 추가해 주세요.")
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            str(self._mode_config()["save_title"]),
            str(self.input_paths[0].parent / self._default_output_name()),
            "PDF Files (*.pdf)",
        )
        if not output_path:
            return
        self._run_export("이미지 PDF 저장", convert_images_to_pdf, output_path, RESULT_KIND_PDF)

    def save_merged_pdf(self) -> None:
        if len(self.input_paths) < 2:
            QMessageBox.warning(self, "PDF 부족", "PDF 병합은 최소 2개의 PDF가 필요합니다.")
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            str(self._mode_config()["save_title"]),
            str(self.input_paths[0].parent / self._default_output_name()),
            "PDF Files (*.pdf)",
        )
        if not output_path:
            return
        self._run_export("PDF 병합", merge_pdfs, output_path, RESULT_KIND_PDF)

    def save_split_pdf(self) -> None:
        if len(self.input_paths) != 1:
            QMessageBox.warning(self, "PDF 선택 필요", "PDF 분할은 PDF 1개를 선택한 상태에서만 진행할 수 있습니다.")
            return
        base_directory = QFileDialog.getExistingDirectory(
            self,
            str(self._mode_config()["save_title"]),
            str(self.input_paths[0].parent),
        )
        if not base_directory:
            return

        output_dir = Path(base_directory) / self._default_output_name()
        if output_dir.exists() and any(output_dir.iterdir()):
            QMessageBox.warning(
                self,
                "결과 폴더 사용 불가",
                "같은 이름의 결과 폴더가 이미 존재합니다. 다른 위치를 선택하거나 기존 폴더를 비워 주세요.",
            )
            return

        self._run_export("PDF 분할", split_pdf, output_dir, RESULT_KIND_DIRECTORY)

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
