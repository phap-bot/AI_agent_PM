# W2 Baseline Report - RAG Retrieval Quality

**Date:** 2026-05-26  
**Author:** Phuc

## Configuration
| Parameter | Value |
|-----------|-------|
| Chunk size | 500 |
| Chunk overlap | 50 |
| Embedding model | nomic-embed-text (768 dims) |
| Retrieval k | 3 |
| Total documents | 3 files (Scrum Guide, User Stories, Acceptance Criteria) |
| Total chunks | 148 |

## Evaluation Results
| Metric | Score |
|--------|-------|
| **Hit Rate@3** | **70%** (14/20 queries) |
| **Recall@3** | **70%** |

## Detailed Analysis

### Strong Performance (100%)
- **Scrum Guide**: 10/10 queries correctly retrieved relevant chunks.
- **Acceptance Criteria**: 2/3 queries correct.

### Weak Performance (0%)
The following 6 queries failed completely (all related to User Stories):
1. "What is the format of a User Story?"
2. "What is an Epic in Agile?"
3. "What does INVEST stand for in User Stories?"
4. "What is the difference between an Epic and a User Story?"
5. "How should Acceptance Criteria be written?"
6. "What are the key components of a good User Story?"

### Root Cause Analysis
- The `user_stories.pdf` content may lack depth on INVEST, Epics, and standard format.
- Current chunking strategy (size=500, overlap=50) might split critical information.
- Language mismatch: queries in English, but some documents may not contain exact terminology.

## Next Steps for Improvement (W8)
- Tune chunk size (try 300, 400, 600)
- Experiment with different chunk overlap ratios (10-20%)
- Consider hybrid search (vector + keyword)
- Add more comprehensive User Stories documentation