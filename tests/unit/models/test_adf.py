"""
Tests for the ADF (Atlassian Document Format) parser.

These tests validate the conversion of ADF content to plain text,
including handling of various inline and block node types.
"""

from src.mcp_atlassian.models.jira.adf import adf_to_text


class TestAdfToText:
    """Tests for the adf_to_text function."""

    # Basic input handling

    def test_none_input(self):
        """Test that None input returns None."""
        assert adf_to_text(None) is None

    def test_string_input(self):
        """Test that string input is returned as-is."""
        assert adf_to_text("plain text") == "plain text"

    def test_empty_dict(self):
        """Test that empty dict returns None."""
        assert adf_to_text({}) is None

    def test_empty_list(self):
        """Test that empty list returns None."""
        assert adf_to_text([]) is None

    # Text node tests

    def test_text_node(self):
        """Test basic text node extraction."""
        node = {"type": "text", "text": "Hello, World!"}
        assert adf_to_text(node) == "Hello, World!"

    def test_text_node_empty(self):
        """Test text node with empty text."""
        node = {"type": "text", "text": ""}
        assert adf_to_text(node) == ""

    def test_text_node_missing_text(self):
        """Test text node without text field."""
        node = {"type": "text"}
        assert adf_to_text(node) == ""

    # hardBreak node tests

    def test_hard_break_node(self):
        """Test hardBreak node returns newline."""
        node = {"type": "hardBreak"}
        assert adf_to_text(node) == "\n"

    # Mention node tests

    def test_mention_with_text(self):
        """Test mention node with text attribute."""
        node = {
            "type": "mention",
            "attrs": {"id": "user123", "text": "@John Doe", "userType": "DEFAULT"},
        }
        assert adf_to_text(node) == "@John Doe"

    def test_mention_without_text(self):
        """Test mention node falls back to id."""
        node = {"type": "mention", "attrs": {"id": "user123"}}
        assert adf_to_text(node) == "@user123"

    def test_mention_without_attrs(self):
        """Test mention node with missing attrs."""
        node = {"type": "mention"}
        assert adf_to_text(node) == "@unknown"

    # Emoji node tests

    def test_emoji_with_text(self):
        """Test emoji node with unicode text."""
        node = {
            "type": "emoji",
            "attrs": {"shortName": ":smile:", "text": "😄"},
        }
        assert adf_to_text(node) == "😄"

    def test_emoji_without_text(self):
        """Test emoji node falls back to shortName."""
        node = {"type": "emoji", "attrs": {"shortName": ":custom_emoji:"}}
        assert adf_to_text(node) == ":custom_emoji:"

    def test_emoji_without_attrs(self):
        """Test emoji node with missing attrs."""
        node = {"type": "emoji"}
        assert adf_to_text(node) == ""

    # Date node tests

    def test_date_node(self):
        """Test date node formats timestamp correctly."""
        # 1582152559000 = 2020-02-19 21:49:19 UTC
        node = {"type": "date", "attrs": {"timestamp": "1582152559000"}}
        assert adf_to_text(node) == "2020-02-19"

    def test_date_node_integer_timestamp(self):
        """Test date node with integer timestamp."""
        node = {"type": "date", "attrs": {"timestamp": 1582152559000}}
        assert adf_to_text(node) == "2020-02-19"

    def test_date_node_invalid_timestamp(self):
        """Test date node with invalid timestamp returns raw value."""
        node = {"type": "date", "attrs": {"timestamp": "not-a-number"}}
        assert adf_to_text(node) == "not-a-number"

    def test_date_node_missing_timestamp(self):
        """Test date node without timestamp."""
        node = {"type": "date", "attrs": {}}
        assert adf_to_text(node) == ""

    def test_date_node_without_attrs(self):
        """Test date node with missing attrs."""
        node = {"type": "date"}
        assert adf_to_text(node) == ""

    # Status node tests

    def test_status_node(self):
        """Test status node wraps text in brackets."""
        node = {
            "type": "status",
            "attrs": {"text": "In Progress", "color": "yellow"},
        }
        assert adf_to_text(node) == "[In Progress]"

    def test_status_node_empty_text(self):
        """Test status node with empty text."""
        node = {"type": "status", "attrs": {"text": "", "color": "neutral"}}
        assert adf_to_text(node) == "[]"

    def test_status_node_without_attrs(self):
        """Test status node with missing attrs."""
        node = {"type": "status"}
        assert adf_to_text(node) == "[]"

    # inlineCard node tests

    def test_inline_card_with_url(self):
        """Test inlineCard node extracts URL."""
        node = {"type": "inlineCard", "attrs": {"url": "https://example.com"}}
        assert adf_to_text(node) == "https://example.com"

    def test_inline_card_with_data_url(self):
        """Test inlineCard node extracts URL from data."""
        node = {
            "type": "inlineCard",
            "attrs": {"data": {"url": "https://jira.example.com/issue/PROJ-123"}},
        }
        assert adf_to_text(node) == "https://jira.example.com/issue/PROJ-123"

    def test_inline_card_with_data_name(self):
        """Test inlineCard node falls back to name from data."""
        node = {
            "type": "inlineCard",
            "attrs": {"data": {"name": "PROJ-123: Fix bug"}},
        }
        assert adf_to_text(node) == "PROJ-123: Fix bug"

    def test_inline_card_empty(self):
        """Test inlineCard node with no data."""
        node = {"type": "inlineCard", "attrs": {}}
        assert adf_to_text(node) == ""

    def test_inline_card_without_attrs(self):
        """Test inlineCard node with missing attrs."""
        node = {"type": "inlineCard"}
        assert adf_to_text(node) == ""

    # codeBlock node tests

    def test_code_block(self):
        """Test codeBlock node wraps content in backticks."""
        node = {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [{"type": "text", "text": "print('hello')"}],
        }
        assert adf_to_text(node) == "```\nprint('hello')\n```"

    def test_code_block_multiline(self):
        """Test codeBlock node with multiline content."""
        node = {
            "type": "codeBlock",
            "content": [{"type": "text", "text": "line1\nline2\nline3"}],
        }
        assert adf_to_text(node) == "```\nline1\nline2\nline3\n```"

    def test_code_block_empty(self):
        """Test codeBlock node with no content."""
        node = {"type": "codeBlock", "content": []}
        assert adf_to_text(node) == "```\n\n```"

    def test_code_block_without_content(self):
        """Test codeBlock node without content field."""
        node = {"type": "codeBlock"}
        assert adf_to_text(node) == "```\n\n```"

    # Nested content tests

    def test_paragraph_with_text(self):
        """Test paragraph node with nested text."""
        node = {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Hello, World!"}],
        }
        assert adf_to_text(node) == "Hello, World!"

    def test_document_with_paragraphs(self):
        """Test full document structure."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "First"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Second"}]},
            ],
        }
        assert adf_to_text(doc) == "First\nSecond"

    def test_paragraph_with_mixed_content(self):
        """Test paragraph with text, mention, and emoji."""
        node = {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Hello "},
                {"type": "mention", "attrs": {"id": "123", "text": "@John"}},
                {"type": "text", "text": " "},
                {"type": "emoji", "attrs": {"shortName": ":wave:", "text": "👋"}},
            ],
        }
        assert adf_to_text(node) == "Hello \n@John\n \n👋"

    def test_list_of_text_nodes(self):
        """Test list of text nodes joins with newlines."""
        nodes = [
            {"type": "text", "text": "Line 1"},
            {"type": "text", "text": "Line 2"},
        ]
        assert adf_to_text(nodes) == "Line 1\nLine 2"

    # Edge cases

    def test_unknown_node_type(self):
        """Test unknown node type without content returns None."""
        node = {"type": "unknownNode"}
        assert adf_to_text(node) is None

    def test_unknown_node_with_content(self):
        """Test unknown node type with content processes recursively."""
        node = {
            "type": "unknownNode",
            "content": [{"type": "text", "text": "nested text"}],
        }
        assert adf_to_text(node) == "nested text"

    def test_deeply_nested_content(self):
        """Test deeply nested ADF structure."""
        node = {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 1"}],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        assert adf_to_text(node) == "Item 1"

    # Mark tests (inline formatting)

    def test_code_mark(self):
        """Test text with code mark is wrapped in backticks."""
        node = {
            "type": "text",
            "text": "hello world",
            "marks": [{"type": "code"}],
        }
        assert adf_to_text(node) == "`hello world`"

    def test_strong_mark(self):
        """Test text with strong mark is wrapped in double asterisks."""
        node = {
            "type": "text",
            "text": "bold text",
            "marks": [{"type": "strong"}],
        }
        assert adf_to_text(node) == "**bold text**"

    def test_em_mark(self):
        """Test text with em mark is wrapped in single asterisks."""
        node = {
            "type": "text",
            "text": "italic text",
            "marks": [{"type": "em"}],
        }
        assert adf_to_text(node) == "*italic text*"

    def test_strike_mark(self):
        """Test text with strike mark is wrapped in tildes."""
        node = {
            "type": "text",
            "text": "strikethrough",
            "marks": [{"type": "strike"}],
        }
        assert adf_to_text(node) == "~~strikethrough~~"

    def test_underline_mark(self):
        """Test text with underline mark is wrapped in u tags."""
        node = {
            "type": "text",
            "text": "underlined",
            "marks": [{"type": "underline"}],
        }
        assert adf_to_text(node) == "<u>underlined</u>"

    def test_link_mark(self):
        """Test text with link mark is formatted as markdown link."""
        node = {
            "type": "text",
            "text": "click here",
            "marks": [{"type": "link", "attrs": {"href": "https://example.com"}}],
        }
        assert adf_to_text(node) == "[click here](https://example.com)"

    def test_link_mark_without_href(self):
        """Test link mark without href preserves text."""
        node = {
            "type": "text",
            "text": "orphan link",
            "marks": [{"type": "link", "attrs": {}}],
        }
        assert adf_to_text(node) == "orphan link"

    def test_subscript_mark(self):
        """Test text with subsup subscript mark."""
        node = {
            "type": "text",
            "text": "2",
            "marks": [{"type": "subsup", "attrs": {"type": "sub"}}],
        }
        assert adf_to_text(node) == "<sub>2</sub>"

    def test_superscript_mark(self):
        """Test text with subsup superscript mark."""
        node = {
            "type": "text",
            "text": "2",
            "marks": [{"type": "subsup", "attrs": {"type": "sup"}}],
        }
        assert adf_to_text(node) == "<sup>2</sup>"

    def test_multiple_marks(self):
        """Test text with multiple marks applies all formatting."""
        node = {
            "type": "text",
            "text": "important",
            "marks": [{"type": "strong"}, {"type": "em"}],
        }
        # Multiple marks are applied sequentially
        assert adf_to_text(node) == "***important***"

    def test_code_mark_in_paragraph(self):
        """Test code mark within a paragraph with other text."""
        node = {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Use "},
                {"type": "text", "text": "console.log()", "marks": [{"type": "code"}]},
                {"type": "text", "text": " for debugging."},
            ],
        }
        assert adf_to_text(node) == "Use \n`console.log()`\n for debugging."

    def test_consecutive_code_marks_become_code_block(self):
        """Test multiple consecutive code-marked text nodes become a code block."""
        nodes = [
            {"type": "text", "text": "line1", "marks": [{"type": "code"}]},
            {"type": "text", "text": "line2", "marks": [{"type": "code"}]},
            {"type": "text", "text": "line3", "marks": [{"type": "code"}]},
        ]
        result = adf_to_text(nodes)
        assert result == "```\nline1\nline2\nline3\n```"

    def test_multiline_code_in_single_node(self):
        """Test code mark with newlines in text becomes code block."""
        nodes = [
            {
                "type": "text",
                "text": "line1\nline2\nline3",
                "marks": [{"type": "code"}],
            },
        ]
        result = adf_to_text(nodes)
        assert result == "```\nline1\nline2\nline3\n```"

    def test_single_short_code_stays_inline(self):
        """Test single short code-marked text stays as inline code."""
        nodes = [
            {"type": "text", "text": "variable", "marks": [{"type": "code"}]},
        ]
        result = adf_to_text(nodes)
        assert result == "`variable`"

    def test_code_blocks_separated_by_text(self):
        """Test code blocks are properly separated when non-code text is between."""
        nodes = [
            {"type": "text", "text": "first", "marks": [{"type": "code"}]},
            {"type": "text", "text": "second", "marks": [{"type": "code"}]},
            {"type": "text", "text": " normal text "},
            {"type": "text", "text": "third", "marks": [{"type": "code"}]},
        ]
        result = adf_to_text(nodes)
        assert result == "```\nfirst\nsecond\n```\n normal text \n`third`"

    def test_text_without_marks(self):
        """Test text node without marks returns plain text."""
        node = {"type": "text", "text": "plain text"}
        assert adf_to_text(node) == "plain text"

    def test_text_with_empty_marks(self):
        """Test text node with empty marks list returns plain text."""
        node = {"type": "text", "text": "plain text", "marks": []}
        assert adf_to_text(node) == "plain text"

    def test_unknown_mark_type(self):
        """Test unknown mark type is ignored."""
        node = {
            "type": "text",
            "text": "text",
            "marks": [{"type": "unknownMark"}],
        }
        assert adf_to_text(node) == "text"
