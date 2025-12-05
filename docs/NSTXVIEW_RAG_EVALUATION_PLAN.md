# NSTXView RAG Evaluation Plan

## Objective

Evaluate whether the current embedding model (`all-MiniLM-L6-v2`) and vector search configuration retrieve relevant chunks for plasma physics queries. This is a lightweight sanity check, not a comprehensive benchmark.

## Approach

We'll create a small test set of queries with known relevant papers, run them through the semantic search, and measure how often the correct content appears in the results.

---

## Step 1: Create Ground Truth Test Cases

Create a file `tests/rag_evaluation_cases.json` with 10-15 test cases. Each case needs:

- `query`: A natural language question
- `expected_paper_ids`: List of paper IDs that should be relevant (look these up manually from your database)
- `expected_keywords`: Key terms that should appear in retrieved chunks
- `category`: Type of query (conceptual, method, comparison, domain-specific-terminology)

Example structure:

```json
{
  "test_cases": [
    {
      "id": "tc_01",
      "query": "How does lithium wall conditioning affect plasma performance?",
      "expected_paper_ids": [12, 45, 67],
      "expected_keywords": ["lithium", "wall conditioning", "recycling"],
      "category": "conceptual"
    },
    {
      "id": "tc_02",
      "query": "ELM suppression techniques",
      "expected_paper_ids": [23, 34],
      "expected_keywords": ["ELM", "edge localized mode", "instability", "pedestal"],
      "category": "domain-specific-terminology"
    },
    {
      "id": "tc_03",
      "query": "high confinement mode transitions",
      "expected_paper_ids": [8, 19, 45],
      "expected_keywords": ["H-mode", "L-H transition", "confinement"],
      "category": "synonym-test"
    }
  ]
}
```

Include test cases that specifically probe:
- Standard conceptual questions
- Domain synonyms (H-mode vs high confinement mode, ELM vs edge localized mode)
- Acronym expansion (NBI vs neutral beam injection, CHERS vs charge exchange)
- Cross-paper synthesis questions

---

## Step 2: Create Evaluation Script

Create `scripts/evaluate_rag.py` that:

1. Loads test cases from JSON
2. For each test case, runs `vector_store.search(query, n_results=10)`
3. Calculates metrics (see below)
4. Outputs a report

Core logic:

```python
from nstxview.services.vector_store import get_vector_store
import json

def evaluate_rag(test_cases_path: str, top_k: int = 10):
    vector_store = get_vector_store()
    results = []

    with open(test_cases_path) as f:
        test_cases = json.load(f)["test_cases"]

    for case in test_cases:
        search_results = vector_store.search(
            query=case["query"],
            n_results=top_k
        )

        # Extract paper_ids from results
        retrieved_paper_ids = set()
        retrieved_text = ""
        for metadata in search_results["metadatas"][0]:
            retrieved_paper_ids.add(metadata["paper_id"])
        for doc in search_results["documents"][0]:
            retrieved_text += doc + " "

        # Calculate metrics
        expected_ids = set(case["expected_paper_ids"])
        hits = retrieved_paper_ids.intersection(expected_ids)

        precision = len(hits) / len(retrieved_paper_ids) if retrieved_paper_ids else 0
        recall = len(hits) / len(expected_ids) if expected_ids else 0

        # Check keyword presence
        keywords_found = []
        keywords_missing = []
        for kw in case["expected_keywords"]:
            if kw.lower() in retrieved_text.lower():
                keywords_found.append(kw)
            else:
                keywords_missing.append(kw)

        results.append({
            "id": case["id"],
            "query": case["query"],
            "category": case["category"],
            "precision": precision,
            "recall": recall,
            "expected_papers": list(expected_ids),
            "retrieved_papers": list(retrieved_paper_ids),
            "papers_hit": list(hits),
            "keywords_found": keywords_found,
            "keywords_missing": keywords_missing
        })

    return results
```

---

## Step 3: Metrics to Calculate

For each test case:
- **Recall@K**: What fraction of expected papers appeared in results? (Most important for RAG)
- **Precision@K**: What fraction of returned papers were expected? (Less critical - some unexpected papers may still be relevant)
- **Keyword hit rate**: Did retrieved chunks contain expected terminology?

Aggregate metrics:
- **Mean recall@10**: Average recall across all test cases
- **Mean recall by category**: Break down by query type to identify weak spots
- **Synonym success rate**: How often do domain-specific synonym queries work?

---

## Step 4: Output Report

Generate a markdown report `reports/rag_evaluation_report.md` containing:

1. Summary statistics (mean recall, mean precision)
2. Per-category breakdown
3. List of failed cases (recall = 0)
4. List of problematic synonyms/acronyms
5. Sample of retrieved chunks for manual inspection

---

## Step 5: Manual Spot Check

For 3-5 test cases, include the actual retrieved text chunks in the report so a human can judge whether the results are sensible even if they don't match the expected paper IDs exactly.

---

## Success Criteria

- **Mean recall@10 >= 0.6**: At least 60% of expected papers appear in top 10 results
- **No category with recall < 0.4**: No query type is completely broken
- **Synonym tests pass >= 70%**: Domain terminology is reasonably understood
- **Clear top_k recommendation**: Identify the value where recall plateaus (expected: somewhere between 8-15)

---

## Step 6: Evaluate top_k Settings

The default `top_k=5` might be cutting off relevant content. We need to test whether increasing it improves recall without adding too much noise.

### What to Measure

For each test case, run the search at multiple top_k values: 3, 5, 10, 15, 20

Track:
- **Recall@K**: Does recall keep improving as K increases, or plateau?
- **Unique papers**: How many distinct papers appear in results?
- **Marginal relevance**: Are chunks at positions 6-10 still useful, or noise?
- **First relevant hit**: At what rank does the first expected paper appear?

### Add to Evaluation Script

```python
def evaluate_top_k_sensitivity(test_cases, k_values=[3, 5, 10, 15, 20]):
    """Test how recall changes across different top_k settings."""
    vector_store = get_vector_store()
    results = []

    for case in test_cases:
        expected_ids = set(case["expected_paper_ids"])
        k_results = {}

        for k in k_values:
            search_results = vector_store.search(
                query=case["query"],
                n_results=k
            )

            # Get unique papers at this K
            retrieved_paper_ids = set()
            for metadata in search_results["metadatas"][0]:
                retrieved_paper_ids.add(metadata["paper_id"])

            hits = retrieved_paper_ids.intersection(expected_ids)
            recall = len(hits) / len(expected_ids) if expected_ids else 0

            k_results[k] = {
                "recall": recall,
                "unique_papers": len(retrieved_paper_ids),
                "papers_hit": len(hits),
                "chunk_count": k
            }

        results.append({
            "id": case["id"],
            "query": case["query"],
            "expected_paper_count": len(expected_ids),
            "results_by_k": k_results
        })

    return results
```

### Metrics to Report

1. **Recall curve**: Plot mean recall vs top_k across all test cases
2. **Paper coverage curve**: Plot mean unique papers vs top_k
3. **Diminishing returns point**: Where does adding more chunks stop helping?
4. **Recommended top_k**: The value where recall plateaus

Example output table:

| top_k | Mean Recall | Mean Unique Papers | Mean Relevant Papers Found |
|-------|-------------|-------------------|---------------------------|
| 3     | 0.35        | 2.1               | 1.2                       |
| 5     | 0.48        | 3.4               | 1.8                       |
| 10    | 0.62        | 5.8               | 2.4                       |
| 15    | 0.67        | 7.2               | 2.6                       |
| 20    | 0.68        | 8.9               | 2.7                       |

In this example, recall plateaus around top_k=15 - going to 20 adds more papers but not more *relevant* papers.

### Check for Paper Concentration

Also measure whether results are dominated by a few papers or spread across many:

```python
def paper_concentration(search_results):
    """Calculate how concentrated results are in few papers."""
    paper_counts = {}
    for metadata in search_results["metadatas"][0]:
        pid = metadata["paper_id"]
        paper_counts[pid] = paper_counts.get(pid, 0) + 1

    # If top paper has >50% of chunks, results are concentrated
    if paper_counts:
        max_count = max(paper_counts.values())
        total = sum(paper_counts.values())
        return max_count / total
    return 0
```

High concentration (>0.5) means one paper dominates - which might be correct (it's the definitive source) or problematic (missing diverse perspectives).

### Decision Criteria

- If recall keeps improving past top_k=10, consider increasing the default
- If recall plateaus early but paper count keeps growing, you're adding noise
- If concentration is high, consider whether you want diversity weighting

---

## If Results Are Poor

Options to consider:

1. **Try a larger model**: Replace `all-MiniLM-L6-v2` with `all-mpnet-base-v2` (768 dimensions, better quality, slower)
2. **Hybrid search**: Add BM25 keyword matching alongside vector search
3. **Domain fine-tuning**: Fine-tune the embedding model on plasma physics abstracts
4. **Query expansion**: Automatically expand acronyms before embedding

---

## Files to Create

- `tests/rag_evaluation_cases.json` - Test cases with ground truth
- `scripts/evaluate_rag.py` - Evaluation script (including top_k sensitivity analysis)
- `reports/rag_evaluation_report.md` - Generated output with recall metrics and top_k recommendations

---

## Expert Inputs Required

### 1. Test case creation (biggest lift)

For each of the 10-15 test queries, you need an expert to:

- Confirm the query is realistic (something a researcher would actually ask)
- Identify which papers in your database should be returned
- List the key terms that should appear in relevant chunks

This requires someone who has actually read the papers and knows what's in them. You can't automate this - the whole point is to check if the system finds what a human expert would find.

### 2. Synonym/acronym pairs

You need someone to list plasma physics terminology that should be treated as equivalent:

- H-mode / high confinement mode
- ELM / edge localized mode
- NBI / neutral beam injection
- CHERS / charge exchange recombination spectroscopy

These test whether the embedding model understands domain vocabulary.

### 3. Spot-check validation

After running the evaluation, an expert should look at a few retrieved chunks and judge: "Is this actually relevant, even though it wasn't in my expected list?" Sometimes the system finds good content you didn't anticipate.

---

## Notes

This evaluation requires manually identifying which papers are relevant for each test query. Start by picking queries where you already know good papers exist, then look up their IDs in the database. This is tedious but necessary - there's no shortcut for ground truth.

---

---

# Strategies for Creating Training Data Without Physics Expertise

Creating ground truth data for RAG evaluation without domain expertise is challenging, but there are several approaches that can be used.

## 1. Use the Papers' Own Structure (Self-Supervised Ground Truth)

The papers themselves contain signals about what's related:

```python
# Papers that cite each other or share authors should be related
# Papers with similar titles/abstracts should be related
# Chunks from the same paper should be more related than chunks from different papers
```

**Approach**: For each paper, use its title or abstract as a query. The "correct" answer is chunks from that same paper. This tests basic retrieval quality.

```json
{
  "id": "self_01",
  "query": "Investigation of lithium wall conditioning effects on NSTX plasma performance",
  "expected_paper_ids": [45],
  "expected_keywords": ["lithium", "wall", "conditioning"],
  "category": "title-as-query"
}
```

## 2. Extract Explicit Cross-References from Papers

Many papers explicitly reference other work with phrases like:
- "As shown in [Smith et al.]..."
- "Similar to previous work on..."
- "Building on the results of..."

You could parse these and create test cases where a query about topic X should return both the citing paper and cited paper.

## 3. Use LLM-Generated Ground Truth

Have Claude or GPT-4 read paper abstracts and generate:
- Likely search queries someone might use to find this paper
- Keywords that should appear in relevant results
- Which other papers (by abstract similarity) seem related

```python
# Pseudocode
for paper in papers:
    prompt = f"""
    Given this plasma physics paper abstract:
    {paper.abstract}

    1. Generate 3 natural language questions a researcher might ask that this paper would answer
    2. List 5-10 key technical terms from this abstract
    3. What topics does this paper cover? (for clustering with similar papers)
    """
    # Use responses to build test cases
```

## 4. Keyword Co-occurrence Analysis

Papers that share rare technical terms are likely related:

```python
# Find papers that share unusual terms (not common words like "plasma" or "experiment")
# These form natural clusters for ground truth
from collections import Counter

def find_related_by_rare_terms(papers):
    # Count term frequency across all papers
    global_term_freq = Counter()
    for paper in papers:
        terms = extract_terms(paper.abstract + paper.title)
        global_term_freq.update(set(terms))  # Count once per paper

    # Terms appearing in 2-5 papers are good discriminators
    discriminative_terms = {
        term for term, count in global_term_freq.items()
        if 2 <= count <= 5
    }

    # Papers sharing discriminative terms are related
    # Use these as ground truth clusters
```

## 5. Use the Structured Data You Already Have

Your database has `NSTXPhenomenon` and `NSTXParameter` tables. Papers studying the same phenomena or measuring the same parameters should be related:

```python
# Papers that both discuss "H-mode transition" phenomenon should be related
# Papers that both measure "electron_temperature" should be related

def create_test_cases_from_metadata(db):
    test_cases = []

    # Group papers by phenomenon
    phenomena = db.query(NSTXPhenomenon.phenomenon_type, NSTXPhenomenon.paper_id).all()
    for phenomenon_type, paper_ids in group_by_phenomenon(phenomena):
        if len(paper_ids) >= 2:
            test_cases.append({
                "query": f"What papers discuss {phenomenon_type}?",
                "expected_paper_ids": paper_ids,
                "expected_keywords": [phenomenon_type],
                "category": "phenomenon-based"
            })

    return test_cases
```

## 6. Bootstrapping with High-Confidence Pairs

Start with obviously related content:
- Different sections of the same paper (should retrieve each other)
- Papers by the same first author on the same topic
- Papers published together (same journal issue, same conference session)

## 7. Active Learning Approach

Run queries, look at results, and make simple judgments even without physics knowledge:

- If a query mentions "lithium" and retrieved chunk mentions "lithium", it's probably relevant
- If a query is about "electron temperature" and chunk discusses "magnetic field geometry" with no overlap, it's probably not relevant
- You can make surface-level relevance judgments based on keyword overlap

---

## Practical Implementation Plan

Here's a concrete approach combining these strategies:

```python
# scripts/generate_evaluation_cases.py

def generate_evaluation_cases(db):
    test_cases = []

    # Strategy 1: Title-as-query (self-retrieval test)
    papers = db.query(NSTXPaper).filter(NSTXPaper.title.isnot(None)).limit(10).all()
    for paper in papers:
        test_cases.append({
            "id": f"title_{paper.id}",
            "query": paper.title,
            "expected_paper_ids": [paper.id],
            "expected_keywords": extract_keywords(paper.title),
            "category": "self-retrieval"
        })

    # Strategy 2: Phenomenon-based clustering
    phenomenon_groups = db.query(
        NSTXPhenomenon.phenomenon_type,
        func.array_agg(distinct(NSTXPhenomenon.paper_id))
    ).group_by(NSTXPhenomenon.phenomenon_type).having(
        func.count(distinct(NSTXPhenomenon.paper_id)) >= 2
    ).limit(5).all()

    for phenom_type, paper_ids in phenomenon_groups:
        test_cases.append({
            "id": f"phenom_{phenom_type}",
            "query": f"{phenom_type} in NSTX experiments",
            "expected_paper_ids": paper_ids[:5],  # Cap at 5
            "expected_keywords": [phenom_type.replace("_", " ")],
            "category": "phenomenon-cluster"
        })

    # Strategy 3: Parameter-based clustering
    param_groups = db.query(
        NSTXParameter.parameter_name,
        func.array_agg(distinct(NSTXParameter.paper_id))
    ).group_by(NSTXParameter.parameter_name).having(
        func.count(distinct(NSTXParameter.paper_id)) >= 3
    ).limit(5).all()

    for param_name, paper_ids in param_groups:
        test_cases.append({
            "id": f"param_{param_name}",
            "query": f"measurements of {param_name.replace('_', ' ')}",
            "expected_paper_ids": paper_ids[:5],
            "expected_keywords": [param_name.replace("_", " ")],
            "category": "parameter-cluster"
        })

    return {"test_cases": test_cases}
```

---

## What This Approach Can and Cannot Test

**Can test:**
- Basic retrieval functionality (does searching a title find that paper?)
- Topical clustering (do papers about same phenomenon appear together?)
- Keyword matching (do relevant terms appear in results?)

**Cannot test without expert:**
- Subtle semantic relationships
- Whether retrieved content actually answers the question
- Quality of cross-paper synthesis
- Domain synonym understanding (H-mode = high confinement mode)

---

## Recommendation

Start with the automated approaches above to establish a baseline. This will tell you if the system is fundamentally working. Then, when Jack or another physicist has 30 minutes, have them:

1. Review 5-10 of your auto-generated test cases and correct/validate them
2. Add 3-5 "real" questions they'd actually ask
3. Spot-check a few retrieved results

This hybrid approach gets you 80% of the value with minimal expert time.

---

*Document created: December 2024*
