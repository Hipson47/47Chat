"""
Property-based tests for loader module using Hypothesis.
Tests file loading and preprocessing functions with comprehensive input generation.
"""

import os
import tempfile
import yaml
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, assume, settings

from backend.orchestrator.utils.loader import preprocess_file


@given(
    content=st.text(min_size=0, max_size=10000),
    filename=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(blacklist_characters=['\n', '\r', '\t', '\0', '/', '\\', ':', '*', '?', '"', '<', '>', '|'])
    ).map(lambda x: x + '.txt')
)
def test_preprocess_file_properties(content, filename):
    """Test properties of preprocess_file function."""
    assume(filename.strip())
    assume('..' not in filename)  # Avoid directory traversal
    assume(not filename.startswith('/'))  # Avoid absolute paths

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Test the function
        result = preprocess_file(temp_path)

        # Invariants
        assert isinstance(result, str)
        assert result == content

        # Content should be preserved exactly
        assert len(result) == len(content)

        # If content is empty, result should be empty
        if not content:
            assert result == ""

    finally:
        # Clean up
        os.unlink(temp_path)


@given(
    yaml_content=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters=['\n', '\r', '\t', ':'])),
        values=st.one_of(
            st.text(min_size=0, max_size=100),
            st.integers(),
            st.booleans(),
            st.lists(st.text(min_size=0, max_size=20), min_size=0, max_size=5),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.text(min_size=0, max_size=50),
                min_size=0,
                max_size=3
            )
        ),
        min_size=0,
        max_size=10
    ),
    filename=st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(blacklist_characters=['\n', '\r', '\t', '\0', '/', '\\', ':', '*', '?', '"', '<', '>', '|'])
    ).map(lambda x: x + '.yaml')
)
def test_yaml_file_processing(yaml_content, filename):
    """Test YAML file processing properties."""
    assume(filename.strip())
    assume('..' not in filename)
    assume(not filename.startswith('/'))

    # Create temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(yaml_content, f)
        temp_path = f.name

    try:
        # Test preprocessing
        result = preprocess_file(temp_path)

        # Should be valid YAML content
        assert isinstance(result, str)
        assert len(result) > 0

        # Should be able to parse back as YAML
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, dict)

        # Original content should be preserved
        assert parsed == yaml_content

    finally:
        os.unlink(temp_path)


@given(
    content=st.text(min_size=0, max_size=5000),
    extension=st.sampled_from(['.txt', '.md', '.py', '.json', '.yaml', '.yml'])
)
def test_file_extensions_handling(content, extension):
    """Test file processing with different extensions."""
    assume('..' not in extension)

    with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = preprocess_file(temp_path)

        # Basic properties should hold regardless of extension
        assert isinstance(result, str)
        assert result == content

        # File should exist and be readable
        assert os.path.exists(temp_path)
        assert os.access(temp_path, os.R_OK)

    finally:
        os.unlink(temp_path)


@given(
    lines=st.lists(st.text(min_size=0, max_size=200), min_size=0, max_size=100),
    line_separator=st.sampled_from(['\n', '\r\n', '\r'])
)
def test_multiline_content_preservation(lines, line_separator):
    """Test that multiline content is preserved correctly."""
    content = line_separator.join(lines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = preprocess_file(temp_path)

        # Content should be preserved exactly
        assert result == content

        # Line count should be preserved
        original_lines = content.splitlines()
        result_lines = result.splitlines()
        assert len(original_lines) == len(result_lines)

        # Individual lines should be preserved
        for orig, res in zip(original_lines, result_lines):
            assert orig == res

    finally:
        os.unlink(temp_path)


@given(
    content=st.binary(min_size=0, max_size=1000)
)
def test_binary_content_handling(content):
    """Test handling of binary content (should fail gracefully or handle appropriately)."""
    # Convert to string for text file
    text_content = content.decode('latin-1', errors='ignore')

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # This might raise an exception for invalid unicode
        result = preprocess_file(temp_path)

        # If it succeeds, result should be the decoded content
        assert isinstance(result, str)

    except UnicodeDecodeError:
        # This is expected for binary content
        pass
    finally:
        os.unlink(temp_path)


@given(
    filename=st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(blacklist_characters=['\n', '\r', '\t', '\0'])
    )
)
def test_nonexistent_file_handling(filename):
    """Test behavior with non-existent files."""
    assume(filename.strip())
    assume(not os.path.exists(filename))

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        preprocess_file(filename)


@settings(max_examples=20)  # Reduce examples for this slower test
@given(
    content=st.text(min_size=0, max_size=1000),
    filename=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(blacklist_characters=['\n', '\r', '\t', '\0', '/', '\\', ':', '*', '?', '"', '<', '>', '|'])
    )
)
def test_file_permissions_and_access(content, filename):
    """Test file access permissions and properties."""
    assume(filename.strip())
    assume('..' not in filename)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # File should be readable
        assert os.access(temp_path, os.R_OK)

        # Function should succeed
        result = preprocess_file(temp_path)

        # Content should match
        assert result == content

        # File metadata should be accessible
        stat = os.stat(temp_path)
        assert stat.st_size >= 0

    finally:
        os.unlink(temp_path)


@pytest.mark.property
@given(
    content=st.text(min_size=0, max_size=100),
    repetitions=st.integers(min_value=1, max_value=5)
)
def test_idempotent_file_reading(content, repetitions):
    """Test that reading the same file multiple times gives consistent results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Read the file multiple times
        results = []
        for _ in range(repetitions):
            result = preprocess_file(temp_path)
            results.append(result)

        # All results should be identical
        assert all(r == results[0] for r in results)
        assert all(r == content for r in results)

    finally:
        os.unlink(temp_path)
