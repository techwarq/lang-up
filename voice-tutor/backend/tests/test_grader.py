import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_exact_match_returns_correct_without_llm():
    from evaluation.grader import grade_answer
    with patch("evaluation.grader._get_client") as mock_client:
        result = await grade_answer("hola", "hola", [], "translation_en_es")
    assert result["correct"] is True
    assert result["score"] == 1.0
    mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_accepted_variant_match_no_llm():
    from evaluation.grader import grade_answer
    with patch("evaluation.grader._get_client") as mock_client:
        result = await grade_answer("buenos dias", "buenos días", ["buenos dias"], "translation_en_es")
    assert result["correct"] is True
    mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_case_insensitive_match():
    from evaluation.grader import grade_answer
    with patch("evaluation.grader._get_client") as mock_client:
        result = await grade_answer("HOLA", "hola", [], "translation_en_es")
    assert result["correct"] is True
    mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_punctuation_ignored_in_local_check():
    from evaluation.grader import grade_answer
    with patch("evaluation.grader._get_client") as mock_client:
        result = await grade_answer("hola!", "hola", [], "translation_en_es")
    assert result["correct"] is True
    mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_llm_called_on_no_local_match():
    from evaluation.grader import grade_answer

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"correct": true, "score": 0.8, "feedback": "Close enough."}')]

    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_response)

    with patch("evaluation.grader._get_client", return_value=mock_client_instance):
        result = await grade_answer("me llamo ana", "me llamo [name]", [], "spoken_response")

    mock_client_instance.messages.create.assert_called_once()
    assert "correct" in result
    assert "score" in result
    assert "feedback" in result


@pytest.mark.asyncio
async def test_llm_failure_returns_safe_fallback():
    from evaluation.grader import grade_answer

    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(side_effect=Exception("API error"))

    with patch("evaluation.grader._get_client", return_value=mock_client_instance):
        result = await grade_answer("something wrong", "hola", ["hi"], "translation_en_es")

    assert result["correct"] is False
    assert result["score"] == 0.0
    assert "Could not grade" in result["feedback"]


@pytest.mark.asyncio
async def test_returns_typed_result_fields():
    from evaluation.grader import grade_answer
    with patch("evaluation.grader._get_client"):
        result = await grade_answer("estoy bien", "estoy bien", [], "spoken_response")
    assert isinstance(result["correct"], bool)
    assert isinstance(result["score"], float)
    assert isinstance(result["feedback"], str)
