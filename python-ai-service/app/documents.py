from __future__ import annotations

from pathlib import Path
from typing import List, Optional

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
except ImportError:
    from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[str]:
    """将文本分割成小块"""
    if not text.strip():
        return []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )
    return text_splitter.split_text(text)


def load_pdf(file_path: Path) -> List[Document]:
    """加载PDF文档"""
    try:
        loader = PyPDFLoader(str(file_path))
        return loader.load()
    except Exception as e:
        print(f"PDF加载失败 {file_path}: {e}")
        return []


def load_docx(file_path: Path) -> List[Document]:
    """加载Word文档"""
    try:
        loader = Docx2txtLoader(str(file_path))
        return loader.load()
    except Exception as e:
        print(f"Word加载失败 {file_path}: {e}")
        return []


def load_txt(file_path: Path) -> List[Document]:
    """加载文本文件"""
    try:
        loader = TextLoader(str(file_path), encoding="utf-8")
        return loader.load()
    except UnicodeDecodeError:
        try:
            loader = TextLoader(str(file_path), encoding="gbk")
            return loader.load()
        except Exception as e:
            print(f"Text加载失败 {file_path}: {e}")
            return []


def load_document(file_path: Path) -> List[Document]:
    """根据文件类型加载文档"""
    suffix = file_path.suffix.lower()
    
    if suffix == ".pdf":
        return load_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return load_docx(file_path)
    elif suffix in [".txt", ".md"]:
        return load_txt(file_path)
    else:
        print(f"不支持的文件类型: {suffix}")
        return []


def process_documents(
    file_paths: List[Path],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Document]:
    """处理文档，加载并分块"""
    all_documents: List[Document] = []
    
    for file_path in file_paths:
        if not file_path.exists():
            print(f"文件不存在: {file_path}")
            continue
        
        print(f"正在处理: {file_path.name}")
        docs = load_document(file_path)
        
        if not docs:
            continue
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
        )
        
        split_docs = text_splitter.split_documents(docs)
        
        for doc in split_docs:
            doc.metadata["source"] = file_path.name
            doc.metadata["file_path"] = str(file_path)
        
        all_documents.extend(split_docs)
    
    print(f"处理完成，共 {len(all_documents)} 个文档块")
    return all_documents
