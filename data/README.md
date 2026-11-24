# Dataset Documentation: Fake and Real News Corpus

## Overview
This project uses the benchmark **ISOT Fake News Dataset** (University of Victoria) and related Kaggle corpora comprising over 44,000 real journalistic articles and fabricated/unverified articles.

## Dataset Structure
The dataset consists of two primary categories:
- **`True.csv`**: Verified journalistic reports primarily collected from Reuters wire services, adhering to established journalistic integrity and attribution standards.
- **`Fake.csv`**: Misleading, fabricated, or clickbait articles flagged by fact-checking organizations (e.g. PolitiFact, Snopes).

### Column Definitions
| Column | Type | Description |
|---|---|---|
| `title` | String | Headline of the news article. |
| `text` | String | Full body text of the article. |
| `subject` | String | Category / Topic (e.g., politicsNews, worldnews, Government News, Middle-east). |
| `date` | String | Publication or archival date. |
| `label` | Integer | `0` = Real / Verified, `1` = Fake / Suspicious. |

## Curated Sample Dataset
For rapid testing and continuous integration without requiring the full ~120MB raw CSV files, a curated representative sample is provided:
- [data/sample_news_test.csv](file:///data/sample_news_test.csv) (50 balanced real and fake test articles)

## Obtaining the Full Dataset
If you wish to re-train the models from scratch on the full 44,000+ article corpus:
1. Download the dataset from [Kaggle: Fake and Real News Dataset](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset)
2. Extract `True.csv` and `Fake.csv` into the project root or `data/` folder.
