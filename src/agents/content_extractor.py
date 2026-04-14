import os
import pandas as pd
import fitz
from docx import Document


class ContentExtractor:
    """Extracts text content from TXT, PDF, DOCX, and CSV files."""

    SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".csv"}

    def __init__(self, directory="data/"):
        self.directory = directory

    def extract_text_from_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def extract_text_from_pdf(self, file_path: str) -> str:
        text = ""
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()

    def extract_text_from_docx(self, file_path: str) -> str:
        doc = Document(file_path)
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)

    def extract_text_from_csv(self, file_path: str) -> str:
        df = pd.read_csv(file_path)
        summary_lines = [
            f"Dataset: {len(df)} rows × {len(df.columns)} columns",
            f"Columns: {', '.join(df.columns.tolist())}",
            "",
            df.to_string(index=False, max_rows=50),
        ]
        return "\n".join(summary_lines)

    def extract_from_file(self, file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        extractors = {
            ".txt": self.extract_text_from_txt,
            ".pdf": self.extract_text_from_pdf,
            ".docx": self.extract_text_from_docx,
            ".csv": self.extract_text_from_csv,
        }
        if ext not in extractors:
            raise ValueError(f"Unsupported file format: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}")
        return extractors[ext](file_path)

    def extract_from_directory(self) -> dict:
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        extracted_data = {}
        for filename in sorted(os.listdir(self.directory)):
            file_path = os.path.join(self.directory, filename)
            _, ext = os.path.splitext(filename)
            if os.path.isfile(file_path) and ext.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    content = self.extract_from_file(file_path)
                    if content:
                        extracted_data[filename] = content
                        print(f"  ✓ Extracted: {filename} ({len(content)} chars)")
                    else:
                        print(f"  ⚠ Empty content: {filename}")
                except Exception as e:
                    print(f"  ✗ Error processing {filename}: {e}")

        return extracted_data


if __name__ == "__main__":
    extractor = ContentExtractor(directory="data/")
    extracted_content = extractor.extract_from_directory()

    for file, content in extracted_content.items():
        print(f"\n{'='*60}")
        print(f"FILE: {file}")
        print(f"{'='*60}")
        print(content[:800])
        print("...")