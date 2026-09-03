import pandas as pd
import pytest

from global_news_market_impact.data.article_rows import (
    ArticleTableErrorReason,
    ArticleTablePreparationError,
    PreparedArticleTable,
    prepare_article_rows,
)


def make_article_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "article_id": " article-2 ",
                "ticker": " nvda ",
                "published_at_et": "2025-06-18T12:00:00-04:00",
                "title": "second",
            },
            {
                "article_id": "article-1",
                "ticker": "META",
                "published_at_et": None,
                "title": "first",
            },
        ],
        index=[20, 10],
    )


def test_prepare_article_rows_preserves_input_order_and_extra_columns() -> None:
    prepared = prepare_article_rows(make_article_rows())

    assert isinstance(prepared, PreparedArticleTable)
    assert prepared.rows.index.tolist() == [0, 1]
    assert prepared.rows["article_id"].tolist() == ["article-2", "article-1"]
    assert prepared.rows["ticker"].tolist() == ["NVDA", "META"]
    assert prepared.rows["title"].tolist() == ["second", "first"]
    assert pd.isna(prepared.rows["published_at_et"].tolist()[1])


def test_prepare_article_rows_requires_minimum_columns() -> None:
    article_rows = make_article_rows().drop(columns="published_at_et")

    with pytest.raises(ArticleTablePreparationError) as error_info:
        prepare_article_rows(article_rows)

    assert error_info.value.reason == ArticleTableErrorReason.INVALID_SCHEMA
    assert "published_at_et" in str(error_info.value)


@pytest.mark.parametrize("article_id", [None, "", "   ", 123])
def test_prepare_article_rows_rejects_missing_or_invalid_article_id(article_id: object) -> None:
    article_rows = make_article_rows().iloc[[0]].copy()
    article_rows["article_id"] = pd.Series([article_id], index=article_rows.index, dtype=object)

    with pytest.raises(ArticleTablePreparationError) as error_info:
        prepare_article_rows(article_rows)

    assert error_info.value.reason == ArticleTableErrorReason.MISSING_ARTICLE_ID


def test_prepare_article_rows_rejects_duplicate_normalized_article_id() -> None:
    article_rows = make_article_rows()
    article_rows.loc[:, "article_id"] = ["article-1", " article-1 "]

    with pytest.raises(ArticleTablePreparationError) as error_info:
        prepare_article_rows(article_rows)

    assert error_info.value.reason == ArticleTableErrorReason.DUPLICATE_ARTICLE_ID
    assert error_info.value.article_id == "article-1"
