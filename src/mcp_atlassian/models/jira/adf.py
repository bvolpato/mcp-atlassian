"""
Atlassian Document Format (ADF) utilities.

This module provides utilities for parsing ADF content from Jira Cloud.
"""

from datetime import datetime, timezone


def _has_code_mark(node: dict) -> bool:
    """Check if a node has a code mark."""
    if node.get("type") != "text":
        return False
    marks = node.get("marks", [])
    return any(m.get("type") == "code" for m in marks)


def _get_text_without_code_mark(node: dict) -> str:
    """Get text from a node, applying all marks except code."""
    text = node.get("text", "")
    marks = node.get("marks", [])
    # Apply all marks except code
    non_code_marks = [m for m in marks if m.get("type") != "code"]
    if non_code_marks:
        text = _apply_marks(text, non_code_marks)
    return text


def _apply_marks(text: str, marks: list[dict]) -> str:
    """
    Apply ADF marks (formatting) to text.

    Supports: code, strong, em, strike, underline, link, subsup.

    Args:
        text: The text content to format
        marks: List of mark dictionaries from ADF

    Returns:
        Formatted text with markdown-style markup
    """
    if not marks:
        return text

    for mark in marks:
        mark_type = mark.get("type")
        if mark_type == "code":
            text = f"`{text}`"
        elif mark_type == "strong":
            text = f"**{text}**"
        elif mark_type == "em":
            text = f"*{text}*"
        elif mark_type == "strike":
            text = f"~~{text}~~"
        elif mark_type == "underline":
            text = f"<u>{text}</u>"
        elif mark_type == "link":
            attrs = mark.get("attrs", {})
            href = attrs.get("href", "")
            if href:
                text = f"[{text}]({href})"
        elif mark_type == "subsup":
            attrs = mark.get("attrs", {})
            subsup_type = attrs.get("type")
            if subsup_type == "sub":
                text = f"<sub>{text}</sub>"
            elif subsup_type == "sup":
                text = f"<sup>{text}</sup>"
        # textColor and backgroundColor are ignored for plain text output

    return text


def _process_content_list(items: list) -> str | None:
    """
    Process a list of ADF content items, merging consecutive code-marked text
    into proper code blocks.

    Args:
        items: List of ADF content items

    Returns:
        Processed text string or None if no content
    """
    if not items:
        return None

    result_parts: list[str] = []
    code_buffer: list[str] = []

    def flush_code_buffer() -> None:
        """Flush accumulated code lines into a code block."""
        if code_buffer:
            # If it's just one short line without newlines, use inline code
            if len(code_buffer) == 1 and "\n" not in code_buffer[0]:
                result_parts.append(f"`{code_buffer[0]}`")
            else:
                # Multiple lines or contains newlines -> code block
                code_content = "\n".join(code_buffer)
                result_parts.append(f"```\n{code_content}\n```")
            code_buffer.clear()

    for item in items:
        if isinstance(item, dict) and _has_code_mark(item):
            # This is a code-marked text node - accumulate it
            text = _get_text_without_code_mark(item)
            # Split by newlines to handle multiline content
            lines = text.split("\n")
            code_buffer.extend(lines)
        else:
            # Not code-marked - flush any accumulated code first
            flush_code_buffer()
            # Process this item normally
            text = adf_to_text(item)
            if text:
                result_parts.append(text)

    # Flush any remaining code
    flush_code_buffer()

    return "\n".join(result_parts) if result_parts else None


def adf_to_text(adf_content: dict | list | str | None) -> str | None:
    """
    Convert Atlassian Document Format (ADF) content to plain text.

    ADF is Jira Cloud's rich text format returned for fields like description.
    This function recursively extracts text content from the ADF structure.

    Args:
        adf_content: ADF document (dict), content list, string, or None

    Returns:
        Plain text string or None if no content
    """
    if adf_content is None:
        return None

    if isinstance(adf_content, str):
        return adf_content

    if isinstance(adf_content, list):
        return _process_content_list(adf_content)

    if isinstance(adf_content, dict):
        # Check if this is a text node
        if adf_content.get("type") == "text":
            text = adf_content.get("text", "")
            # Handle marks (formatting like code, strong, em, etc.)
            marks = adf_content.get("marks", [])
            if marks:
                text = _apply_marks(text, marks)
            return text

        # Check if this is a hardBreak node
        if adf_content.get("type") == "hardBreak":
            return "\n"

        # Check if this is a mention node
        if adf_content.get("type") == "mention":
            attrs = adf_content.get("attrs", {})
            return attrs.get("text") or f"@{attrs.get('id', 'unknown')}"

        # Check if this is an emoji node
        if adf_content.get("type") == "emoji":
            attrs = adf_content.get("attrs", {})
            return attrs.get("text") or attrs.get("shortName", "")

        # Check if this is a date node
        if adf_content.get("type") == "date":
            attrs = adf_content.get("attrs", {})
            timestamp = attrs.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc)
                    return dt.strftime("%Y-%m-%d")
                except (ValueError, OSError, TypeError):
                    return str(timestamp)
            return ""

        # Check if this is a status node
        if adf_content.get("type") == "status":
            attrs = adf_content.get("attrs", {})
            return f"[{attrs.get('text', '')}]"

        # Check if this is an inlineCard node
        if adf_content.get("type") == "inlineCard":
            attrs = adf_content.get("attrs", {})
            url = attrs.get("url")
            if url:
                return url
            data = attrs.get("data", {})
            return data.get("url") or data.get("name", "")

        # Check if this is a codeBlock node
        if adf_content.get("type") == "codeBlock":
            content = adf_content.get("content", [])
            code_text = adf_to_text(content) or ""
            return f"```\n{code_text}\n```"

        # Recursively process content
        content = adf_content.get("content")
        if content:
            return adf_to_text(content)

        return None

    return None
