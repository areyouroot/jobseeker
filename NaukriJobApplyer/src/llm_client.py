import json
import re
import urllib.request
from pathlib import Path
from pypdf import PdfReader

class LLMClient:
    """Extracts text from a resume PDF and queries the local LLM webhook for keywords."""

    def __init__(self, llm_url: str, log_fn=print):
        self.llm_url = llm_url.strip() if llm_url else ""
        self.log_fn = log_fn

    def get_keywords(self, resume_path: str) -> list[str]:
        """
        Extract text from the resume and query the LLM to get search keywords.
        Returns a list of keywords, or a default list if query fails.
        """
        # Ensure resume exists
        path = Path(resume_path)
        if not path.exists():
            self.log_fn(f"[ERROR] Resume PDF not found for extraction: {resume_path}")
            return ["C# .NET Developer"]

        # 1. Extract text from PDF
        self.log_fn(f"[INFO] Extracting text from resume PDF: {path.name}...")
        try:
            reader = PdfReader(path)
            resume_text = ""
            for page in reader.pages:
                resume_text += page.extract_text() or ""
            
            resume_text = resume_text.strip()
            if not resume_text:
                self.log_fn("[WARNING] PDF text extraction yielded empty content.")
        except Exception as e:
            self.log_fn(f"[ERROR] PDF extraction failed: {e}")
            return ["C# .NET Developer"]

        # If LLM URL not configured, return default fallback
        if not self.is_configured():
            self.log_fn("[WARNING] LLM URL not configured in config.ini. Using fallback keywords.")
            return ["C# .NET Developer"]

        # 2. Build LLM prompt containing resume text
        prompt = (
            "Extract the most relevant job search keywords or titles from the following resume text. "
            "My focus is C# .net developer roles. Return ONLY a JSON array of strings containing the "
            "top search terms (e.g. [\"C# Developer\", \".NET Developer\", \"ASP.NET Software Engineer\"]). "
            "Provide no introductory text, no markdown styling, and no comments. "
            f"Here is my resume:\n\n{resume_text}"
        )

        payload = [
            {
                "systemMessage": "You are a job searching agent",
                "prompt": prompt
            }
        ]

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.llm_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        # 3. Query local webhook
        try:
            self.log_fn(f"[INFO] Querying LLM webhook for keywords: {self.llm_url}...")
            with urllib.request.urlopen(req, timeout=60) as resp:
                response_str = resp.read().decode("utf-8")
                self.log_fn(f"[INFO] LLM query successful. Parsing keywords...")
                return self._parse_keywords(response_str)
        except Exception as e:
            self.log_fn(f"[ERROR] Local LLM query failed: {e}")
            return ["C# .NET Developer"]

    def is_configured(self) -> bool:
        """Return True if the LLM webhook URL is configured."""
        return bool(self.llm_url)

    def _parse_keywords(self, response_str: str) -> list[str]:
        """Parse the JSON array or text keywords out of the LLM response."""
        response_str = response_str.strip()

        # Try to parse the response directly as JSON
        try:
            data = json.loads(response_str)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
            if isinstance(data, dict):
                # Search common response keys
                for key in ["text", "response", "output", "message", "content"]:
                    if key in data:
                        val = data[key]
                        if isinstance(val, list):
                            return [str(item).strip() for item in val if str(item).strip()]
                        if isinstance(val, str):
                            response_str = val
                            break
        except Exception:
            pass

        # Use Regex to extract a JSON list block e.g. ["a", "b"]
        match = re.search(r'\[\s*".*?"\s*(?:,\s*".*?"\s*)*\]', response_str, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass

        # Fallback: parse lines or comma-separated terms
        keywords = []
        for line in response_str.split("\n"):
            line = line.strip().strip("*-#").strip()
            if line:
                # Remove line numbering e.g. "1. C#" -> "C#"
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                line = line.strip('",[] ')
                if line:
                    keywords.append(line)

        cleaned = []
        for kw in keywords:
            if "," in kw and not (kw.startswith('"') or kw.startswith('[')):
                for sub in kw.split(","):
                    sub_clean = sub.strip().strip('"/\\ ')
                    if sub_clean:
                        cleaned.append(sub_clean)
            else:
                kw_clean = kw.strip().strip('"/\\ ')
                if kw_clean:
                    cleaned.append(kw_clean)

        if not cleaned:
            return ["C# .NET Developer"]

        return cleaned
