# PDF Converter

여러 이미지를 드래그앤드롭으로 불러와 하나의 PDF로 변환하는 Windows GUI 프로그램입니다.

## 주요 기능

- 여러 이미지 파일을 한 번에 PDF로 변환
- 드래그앤드롭 기반 GUI
- 실제 PDF 전체 페이지 미리보기
- 모든 페이지를 `A4` 기준으로 정렬
- 단일 실행 파일(`.exe`) 빌드 지원
- 설치형 Windows 앱(`Setup.exe`) 패키징 지원

## 지원 형식

- `JPG`
- `JPEG`
- `PNG`
- `BMP`
- `TIFF`
- `WEBP`
- `GIF`

## 동작 방식

- 추가한 이미지는 입력 순서대로 PDF 페이지가 됩니다.
- 각 페이지는 `A4 크기`에 맞춰 저장됩니다.
- 이미지 비율은 유지됩니다.
- 비율 차이로 남는 영역은 일반적인 문서 도구처럼 `흰 여백`으로 처리됩니다.

## 기술 스택

- `Python 3.14`
- `PySide6`
- `img2pdf`
- `Pillow`
- `PyInstaller`
- `Inno Setup 6`

## 프로젝트 구조

```text
pdf_converter/
├─ app.py
├─ build_exe.ps1
├─ build_installer.ps1
├─ requirements.txt
├─ assets/
├─ installer/
├─ pdf_converter/
│  ├─ app.py
│  ├─ converter.py
│  └─ __init__.py
└─ docs/
```

## 로컬 실행

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## 단일 실행 파일 빌드

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

생성 결과:

- `release/PDFConverter.exe`

이 파일은 설치 없이 바로 실행할 수 있습니다.

## 설치형 앱 빌드

설치형 패키지를 만들려면 `Inno Setup 6`가 필요합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

생성 결과:

- `release/PDFConverter-Setup.exe`

이 파일은 일반 Windows 프로그램처럼 설치할 수 있습니다.

## 아이콘

앱 아이콘 자산은 아래 파일을 사용합니다.

- `assets/app_icon.png`
- `assets/app_icon.ico`

현재 아이콘 컨셉:

- `A4 문서`
- `이미지 프레임`
- `PDF 배지`
- 파란 계열 중심의 UI 톤 통일

아이콘만 교체하고 싶다면 `assets/app_icon.ico`를 새 파일로 바꾸면 됩니다.

## 배포 권장 방식

사용자에게 공유할 때는 보통 아래 둘 중 하나를 배포하면 됩니다.

- `release/PDFConverter.exe`
  설치 없이 바로 실행
- `release/PDFConverter-Setup.exe`
  설치 후 시작 메뉴에서 실행

일반 사용자 배포에는 `PDFConverter-Setup.exe`가 더 친숙합니다.

## 개발 메모

- PDF 미리보기는 `PySide6 QtPdf` 모듈을 사용합니다.
- 빌드 산출물은 `release/`에 모입니다.
- 빌드 중 Windows 잠금 파일이 남을 수 있어, 임시 `.tmp` 파일은 Git에 포함하지 않습니다.
