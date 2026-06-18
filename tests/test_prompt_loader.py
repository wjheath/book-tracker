from prompt_loader import list_prompts, load_prompt


def test_load_prompt_reads_existing_file():
    content = load_prompt("book_suggestion.txt", default="fallback")
    assert content != "fallback"
    assert len(content) > 0


def test_load_prompt_falls_back_when_file_missing():
    content = load_prompt("definitely_does_not_exist.txt", default="fallback-content")
    assert content == "fallback-content"


def test_list_prompts_only_returns_txt_files():
    prompts = list_prompts()
    assert all(p.endswith(".txt") for p in prompts)
    assert "book_suggestion.txt" in prompts
