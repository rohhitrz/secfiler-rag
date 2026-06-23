import re
from pathlib import Path

from bs4 import BeautifulSoup

# Tags whose text is never human-readable content.
_JUNK_TAGS = ["script", "style", "head"]
_XBRL_PREFIX = re.compile(r"^ix:")


def load_filing_text(path: str) -> str:
    """Read a raw SEC 10-K HTML file and return clean plain text.

    Strips <script>/<style>/<head> and the entire inline-XBRL (`ix:`)
    namespace before extracting text, so machine metadata (GAAP taxonomy
    URLs, period markers) doesn't pollute downstream tokens. Collapses
    whitespace to a single clean string.
    """
    content = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")

    for tag in soup(_JUNK_TAGS):
        tag.decompose()
    for tag in soup.find_all(_XBRL_PREFIX):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def chunk_text(text:str,company:str,chunk_size:int=1000,overlap:int=200)-> list[dict]:
    """
    Split clean filing text into overlapping chunks with metadata.

    Args:
        text: clean output from load_filing_text()
        company: ticker, e.g. "AAPL" — stamped onto every chunk
        chunk_size: target chunk length in characters
        overlap: characters shared between consecutive chunks

    Returns:
        list of {"text": str, "company": str, "chunk_id": int}
    """

    chunks=[]
    start=0
    chunk_id=0

    while start<len(text):
        end=start+chunk_size
        chunks.append({
            "text": text[start:end],
            "company":company,
            "chunk_id":chunk_id
        })
        chunk_id+=1
        start+=chunk_size-overlap
    
    return chunks

        
   


# if __name__=="__main__":
    # loaded_file=load_filing_text("/Users/rohit/Desktop/secfiler-rag/data/raw/aapl-2025.htm")
    # print(loaded_file)

    # text = load_filing_text("data/raw/aapl-2025.htm")
    # text2 = load_filing_text("data/raw/msft-2025.htm")
    # text3 = load_filing_text("data/raw/tsla-2025.htm")
    # print(len(text))
    # print(repr(text[:500]))
    # print(len(text2))
    # print(repr(text2[:500]))
    # print(len(text3))
    # print(repr(text3[:500]))

# if __name__ == "__main__":
#     text = load_filing_text("data/raw/aapl-2025.htm")
#     chunks = chunk_text(text, company="AAPL")

#     print(f"clean chars: {len(text)}")
#     print(f"num chunks:  {len(chunks)}")
#     print()
#     print("--- chunk 0 tail ---")
#     print(repr(chunks[0]["text"][-200:]))
#     print("--- chunk 1 head ---")
#     print(repr(chunks[1]["text"][:200]))
#     print()
#     print("--- last chunk ---")
#     print(repr(chunks[-1]))