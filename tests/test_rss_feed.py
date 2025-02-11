import xml.etree.ElementTree as ET
import requests
import subprocess
import sys
from pathlib import Path
from typing import Tuple


class RSSValidationError(Exception):
    """Custom exception for RSS feed validation errors"""

    def __init__(self, message="RSS validation failed", details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class CDATAError(RSSValidationError):
    """Custom exception for CDATA-related errors"""

    def __init__(self, message="CDATA validation failed", details=None):
        super().__init__(message, details)


class SpecialCharacterError(RSSValidationError):
    """Custom exception for special character errors"""

    def __init__(self, message="Special character validation failed", details=None):
        super().__init__(message, details)


class MissingRSSElementError(RSSValidationError):
    """Custom exception for missing RSS element errors"""

    def __init__(self, message="Required RSS element check failed", details=None):
        super().__init__(message, details)


def get_project_root() -> Path:
    """Get the absolute path to the project root directory"""
    return Path(__file__).parent.parent


def render_blog() -> None:
    result = subprocess.run(
        ["quarto", "render"], cwd=get_project_root(), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"Unexpected error: {result.stderr}")


def check_rss_for_required_elements() -> bool:
    try:
        rss_path = get_project_root().joinpath("_site", "index.xml")
        if not rss_path.exists():
            print(f"RSS feed not found at {rss_path}")
            return False
        tree = ET.parse(rss_path)
        root = tree.getroot()
        channel = root.find("channel")
        if channel is None:
            raise MissingRSSElementError("No channel element found in RSS feed")
        required_elements = ["title", "link", "description"]
        missing_elements = []
        for element in required_elements:
            if channel.find(element) is None:
                missing_elements.append(element)
        if len(missing_elements) > 0:
            raise MissingRSSElementError(
                "Required elements missing from RSS feed", {"missing_elements": missing_elements}
            )
        items = channel.findall("item")
        if not items:
            raise MissingRSSElementError("Required items missing from RSS feed")
        for item in items:
            missing_elements = []
            for element in ["title", "link"]:
                if item.find(element) is None:
                    missing_items.append(element)
                if len(missing_elements) > 0:
                    raise MissingRSSElementError(
                        "Required item-elements missing from RSS feed",
                        {"item": item, "missing_elements": missing_elements},
                    )
        print("RSS feed validation successful!")
        return True
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return False


def check_cdata_sections(xml_content: str) -> bool:
    """Check for properly closed CDATA sections"""
    open_cdata = xml_content.count("<![CDATA[")
    close_cdata = xml_content.count("]]>")
    if open_cdata != close_cdata:
        raise RSSValidationError(
            "CDATA sections mismatch",
            {
                "opens": open_cdata,
                "closes": close_cdata,
                "difference": abs(open_cdata - close_cdata),
            },
        )
    return True


class BinaryContentError(RSSValidationError):
    """Exception for binary or non-printable characters in content"""

    pass


def find_binary_characters(xml_content: str) -> list[Tuple[int, str, str]]:
    """Find binary and non-printable characters in xml_content.

    Returns:
        List of tuples containing (position, character, hex representation)
    """
    binary_chars = []
    for i, char in enumerate(xml_content):
        if ord(char) < 32 and char not in "\n\r\t":
            binary_chars.append((i, char, f"\\u{ord(char):04x}"))  # Unicode escape sequence
        elif ord(char) == 0xFFFF or ord(char) == 0xFFFE:  # Unicode BOM
            binary_chars.append((i, char, f"\\u{ord(char):04x}"))
        elif char == "\ufffd":  # Unicode replacement character
            binary_chars.append((i, char, "\\uFFFD (Unicode replacement character)"))
    return binary_chars


def check_for_binary_content(xml_content: str) -> bool:
    """Check for binary or non-printable characters in XML content"""
    binary_chars = find_binary_characters(xml_content)
    if binary_chars:
        locations = []
        for pos, char, hex_repr in binary_chars:
            start = max(0, pos - 20)
            end = min(len(xml_content), pos + 20)
            context = xml_content[start:end].replace("\n", "\\n")
            locations.append(
                {"position": pos, "character": hex_repr, "context": f"...{context}..."}
            )
        raise BinaryContentError(
            "Binary or non-printable characters found in XML content",
            {"count": len(binary_chars), "locations": locations},
        )
    return True


def validate_rss_feed() -> bool:
    """Build the site and validate the RSS feed"""

    render_blog()
    try:
        required_elements_present = check_rss_for_required_elements()
        rss_path = get_project_root().joinpath("_site", "index.xml")
        with open(rss_path, "r") as f:
            content = f.read()
            cdata_sections_valid = check_cdata_sections(content)
            no_binary_content_found = check_for_binary_content(content)
        return required_elements_present and cdata_sections_valid and no_binary_content_found
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def test_rss_feed():
    """Pytest function to test RSS feed"""
    assert validate_rss_feed()


if __name__ == "__main__":
    rss_feed_valid = validate_rss_feed()
    sys.exit(0 if rss_feed_valid else 1)
