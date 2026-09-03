"""Validate and normalize the minimum article input contract for labeling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd

from global_news_market_impact.config.schema import LABEL_ARTICLE_INPUT_COLUMNS


class ArticleTableErrorReason(StrEnum):
    INVALID_SCHEMA = "INVALID_SCHEMA"
    MISSING_ARTICLE_ID = "MISSING_ARTICLE_ID"
    DUPLICATE_ARTICLE_ID = "DUPLICATE_ARTICLE_ID"


class ArticleTablePreparationError(ValueError):
    """Raised when article rows cannot satisfy the batch traceability contract."""

    def __init__(
        self,
        reason: ArticleTableErrorReason,
        detail: str,
        *,
        article_id: str | None = None,
    ) -> None:
        self.reason = reason
        self.article_id = article_id
        super().__init__(detail)


@dataclass(frozen=True)
class PreparedArticleTable:
    """Article rows with stable IDs and original input order preserved."""

    rows: pd.DataFrame


def prepare_article_rows(article_rows: pd.DataFrame) -> PreparedArticleTable:
    """Validate minimum columns and normalize identifiers without filtering rows."""
    if not isinstance(article_rows, pd.DataFrame):
        raise ArticleTablePreparationError(
            ArticleTableErrorReason.INVALID_SCHEMA,
            "article_rows must be a pandas DataFrame",
        )

    missing_columns = sorted(set(LABEL_ARTICLE_INPUT_COLUMNS) - set(article_rows.columns))
    if missing_columns:
        raise ArticleTablePreparationError(
            ArticleTableErrorReason.INVALID_SCHEMA,
            f"article_rows is missing required columns: {', '.join(missing_columns)}",
        )

    prepared_rows = article_rows.copy().reset_index(drop=True)
    prepared_rows["article_id"] = prepared_rows["article_id"].map(_normalize_article_id)
    duplicate_ids = prepared_rows.loc[
        prepared_rows["article_id"].duplicated(keep=False), "article_id"
    ].unique()
    if len(duplicate_ids) > 0:
        duplicate_id = str(duplicate_ids[0])
        raise ArticleTablePreparationError(
            ArticleTableErrorReason.DUPLICATE_ARTICLE_ID,
            f"duplicate article_id: {duplicate_id}",
            article_id=duplicate_id,
        )

    prepared_rows["ticker"] = prepared_rows["ticker"].map(_normalize_ticker_if_string)
    return PreparedArticleTable(rows=prepared_rows)


def _normalize_article_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArticleTablePreparationError(
            ArticleTableErrorReason.MISSING_ARTICLE_ID,
            "article_id must be a non-empty string",
        )
    return value.strip()


def _normalize_ticker_if_string(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value
