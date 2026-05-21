"""
MedSci Literature Search for ARP v24

Integrates the search-lit skill for PubMed literature search,
citation verification, and BibTeX generation.

Based on: medsci-skills/skills/search-lit

Usage:
    from integration.literature_search import LiteratureSearch, PubMedSearch
    
    search = PubMedSearch()
    
    # Search PubMed
    results = search.search("MASLD cardiovascular outcomes", max_results=50)
    
    # Verify citations
    verified = search.verify_citations([
        "10.1016/S0140-6736(23)00000-X",
        "10.1016/j.metabol.2024.155000"
    ])
    
    # Generate BibTeX
    bibtex = search.to_bibtex(pmids=["12345678", "87654321"])
"""

import json
import os
import re
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# NCBI API Key (from TOOLS.md)
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "e7e246c879e2db83a702796516239666c407")

# API endpoints
PUBMED_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_SEARCH_URL = PUBMED_EUTILS + "esearch.fcgi"
PUBMED_FETCH_URL = PUBMED_EUTILS + "efetch.fcgi"
PUBMED_SUMMARY_URL = PUBMED_EUTILS + "esummary.fcgi"


@dataclass
class SearchResult:
    """A single search result"""
    pmid: str
    title: str
    authors: List[str]
    journal: str
    pub_date: str
    abstract: str = ""
    doi: str = ""
    volume: str = ""
    pages: str = ""
    issue: str = ""
    citation: str = ""
    verified: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "pub_date": self.pub_date,
            "abstract": self.abstract,
            "doi": self.doi,
            "volume": self.volume,
            "pages": self.pages,
            "issue": self.issue,
            "citation": self.citation,
            "verified": self.verified
        }
    
    def to_bibtex(self, key: str = None) -> str:
        """Convert to BibTeX format"""
        if key is None:
            # Generate key from first author and year
            first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
            year = self.pub_date[:4] if self.pub_date else "nd"
            key = f"{first_author}{year}"
        
        # Clean title
        title = self.title.replace("{", "\\{").replace("}", "\\}")
        
        # Format authors
        authors_str = " and ".join(self.authors) if self.authors else "Unknown"
        
        bibtex = f"""@article{{{key},
  author = {{{authors_str}}},
  title = {{{title}}},
  journal = {{{self.journal}}},
  year = {{{self.pub_date[:4] if self.pub_date else ""}}},
  volume = {{{self.volume}}},
  number = {{{self.issue}}},
  pages = {{{self.pages}}},
  doi = {{{self.doi}}},
  pmid = {{{self.pmid}}}
}}"""
        return bibtex
    
    def to_markdown(self) -> str:
        """Convert to markdown citation"""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += ", et al."
        return f"{authors_str}. {self.title}. {self.journal}. {self.pub_date[:4] if self.pub_date else ''}."
    
    def to_ris(self) -> str:
        """Convert to RIS format"""
        ris_lines = [
            "TY  - JOUR",
            f"AU  - {', '.join(self.authors)}" if self.authors else "AU  - Unknown",
            f"TI  - {self.title}",
            f"JO  - {self.journal}",
            f"PY  - {self.pub_date[:4] if self.pub_date else ''}",
            f"VL  - {self.volume}",
            f"IS  - {self.issue}",
            f"SP  - {self.pages}",
            f"DO  - {self.doi}",
            f"PMID - {self.pmid}",
            "ER  -"
        ]
        return "\n".join(ris_lines)


class PubMedSearch:
    """
    PubMed literature search using NCBI E-utilities.
    
    Supports:
    - Boolean queries (AND, OR, NOT)
    - Field tags ([ti], [ab], [mesh], etc.)
    - Publication type filters
    - Date range filters
    - Citation lookup by PMID/DOI
    - Batch retrieval
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize PubMed search.
        
        Args:
            api_key: NCBI API key for faster queries
        """
        self.api_key = api_key or NCBI_API_KEY
        self.email = "arp-user@example.com"  # Required by NCBI
    
    def _build_params(self, **kwargs) -> Dict:
        """Build API parameters"""
        params = {
            "email": self.email,
            "tool": "ARP_v24"
        }
        if self.api_key:
            params["api_key"] = self.api_key
        params.update(kwargs)
        return params
    
    def _fetch_url(self, url: str, params: Dict) -> str:
        """Fetch URL with error handling"""
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(full_url, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def search(self, 
              query: str,
              max_results: int = 20,
              field: str = None,
              publication_type: str = None,
              date_range: Tuple[str, str] = None,
              sort: str = "relevance") -> List[SearchResult]:
        """
        Search PubMed with a query.
        
        Args:
            query: Search query (supports Boolean operators)
            max_results: Maximum number of results
            field: Field to search (ti, ab, mesh, etc.)
            publication_type: Filter by publication type
            date_range: Tuple of (start_date, end_date) in YYYY/MM/DD format
            sort: Sort by "relevance" or "pub_date"
            
        Returns:
            List of SearchResult objects
        """
        # Build query
        search_query = query
        if field:
            search_query = f"{query}[{field}]"
        if publication_type:
            search_query = f"{search_query} AND {publication_type}[pt]"
        
        # Search
        params = self._build_params(
            db="pubmed",
            term=search_query,
            retmax=max_results,
            sort=sort,
            retmode="xml"
        )
        
        if date_range:
            params["mindate"], params["maxdate"] = date_range
        
        xml_data = self._fetch_url(PUBMED_SEARCH_URL, params)
        
        if not xml_data:
            return []
        
        # Parse IDs
        try:
            root = ET.fromstring(xml_data)
            id_list = [id_elem.text for id_elem in root.findall(".//Id")]
        except ET.ParseError:
            print("Error parsing search results")
            return []
        
        if not id_list:
            return []
        
        # Fetch details
        return self._fetch_details(id_list)
    
    def _fetch_details(self, pmids: List[str], max_batch: int = 100) -> List[SearchResult]:
        """Fetch details for a list of PMIDs"""
        results = []
        
        # Batch in groups of max_batch
        for i in range(0, len(pmids), max_batch):
            batch = pmids[i:i+max_batch]
            
            params = self._build_params(
                db="pubmed",
                id=",".join(batch),
                retmode="xml",
                rettype="abstract"
            )
            
            xml_data = self._fetch_url(PUBMED_FETCH_URL, params)
            
            if not xml_data:
                continue
            
            try:
                root = ET.fromstring(xml_data)
                
                for article in root.findall(".//PubmedArticle"):
                    result = self._parse_article(article)
                    if result:
                        results.append(result)
                        
            except ET.ParseError as e:
                print(f"Error parsing article: {e}")
                continue
        
        return results
    
    def _parse_article(self, article: ET.Element) -> Optional[SearchResult]:
        """Parse a PubmedArticle XML element"""
        try:
            medline_citation = article.find("MedlineCitation")
            if medline_citation is None:
                return None
            
            article_data = medline_citation.find("Article")
            if article_data is None:
                return None
            
            pmid_elem = medline_citation.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            title_elem = article_data.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else ""
            
            # Authors
            authors = []
            author_list = article_data.find("AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    last_name = author.find("LastName")
                    initials = author.find("Initials")
                    if last_name is not None and initials is not None:
                        authors.append(f"{last_name.text} {initials.text}")
            
            # Journal
            journal_elem = article_data.find("Journal")
            journal = ""
            pub_date = ""
            if journal_elem is not None:
                journal_title = journal_elem.find("Title")
                journal = journal_title.text if journal_title is not None else ""
                
                # PubDate
                pub_date_elem = journal_elem.find("JournalIssue/PubDate")
                if pub_date_elem is not None:
                    year = pub_date_elem.find("Year")
                    month = pub_date_elem.find("Month")
                    day = pub_date_elem.find("Day")
                    pub_date_parts = []
                    if year is not None:
                        pub_date_parts.append(year.text)
                    if month is not None:
                        pub_date_parts.append(month.text)
                    if day is not None:
                        pub_date_parts.append(day.text)
                    pub_date = " ".join(pub_date_parts)
            
            # Volume/Issue/Pages
            volume = ""
            issue = ""
            pages = ""
            journal_issue = journal_elem.find("JournalIssue") if journal_elem is not None else None
            if journal_issue is not None:
                vol_elem = journal_issue.find("Volume")
                issue_elem = journal_issue.find("Issue")
                volume = vol_elem.text if vol_elem is not None else ""
                issue = issue_elem.text if issue_elem is not None else ""
            
            pagination = article_data.find("Pagination")
            if pagination is not None:
                medline_pgn = pagination.find("MedlinePgn")
                pages = medline_pgn.text if medline_pgn is not None else ""
            
            # Abstract
            abstract_elems = article_data.find("Abstract")
            abstract_parts = []
            if abstract_elems is not None:
                for abstract_text in abstract_elems.findall("AbstractText"):
                    label = abstract_text.get("Label", "")
                    text = abstract_text.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = " ".join(abstract_parts)
            
            # DOI (from ArticleIdList)
            doi = ""
            article_id_list = article.find("PubmedData/ArticleIdList")
            if article_id_list is not None:
                for article_id in article_id_list.findall("ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break
            
            return SearchResult(
                pmid=pmid,
                title=title,
                authors=authors,
                journal=journal,
                pub_date=pub_date,
                abstract=abstract,
                doi=doi,
                volume=volume,
                pages=pages,
                issue=issue
            )
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None
    
    def fetch_by_pmid(self, pmid: str) -> Optional[SearchResult]:
        """Fetch a single article by PMID"""
        results = self._fetch_details([pmid])
        return results[0] if results else None
    
    def fetch_by_doi(self, doi: str) -> Optional[SearchResult]:
        """Fetch an article by DOI"""
        results = self.search(f"{doi}[doi]", max_results=1)
        return results[0] if results else None
    
    def verify_pmid(self, pmid: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a PMID exists.
        
        Returns:
            Tuple of (exists, title)
        """
        result = self.fetch_by_pmid(pmid)
        if result:
            return True, result.title
        return False, None
    
    def verify_doi(self, doi: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a DOI exists.
        
        Returns:
            Tuple of (exists, title)
        """
        result = self.fetch_by_doi(doi)
        if result:
            return True, result.title
        return False, None
    
    def verify_citations(self, citations: List[str]) -> Dict[str, Dict]:
        """
        Verify a list of citations (PMIDs or DOIs).
        
        Args:
            citations: List of PMIDs or DOIs
            
        Returns:
            Dict mapping citation to verification result
        """
        results = {}
        
        for citation in citations:
            citation = citation.strip()
            
            if re.match(r'^\d+$', citation):
                # PMID
                exists, title = self.verify_pmid(citation)
                results[citation] = {"type": "pmid", "exists": exists, "title": title}
            elif citation.startswith("10."):
                # DOI
                exists, title = self.verify_doi(citation)
                results[citation] = {"type": "doi", "exists": exists, "title": title}
            else:
                results[citation] = {"type": "unknown", "exists": False, "title": None}
        
        return results


class LiteratureSearch:
    """
    Unified literature search interface for ARP v24.
    Wraps PubMed search with additional formatting and export capabilities.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with PubMed search"""
        self.pubmed = PubMedSearch(api_key)
        self.search_history: List[Dict] = []
    
    def search(self, query: str, max_results: int = 20, **kwargs) -> List[SearchResult]:
        """
        Search literature.
        
        Args:
            query: Search query
            max_results: Maximum results
            **kwargs: Additional search parameters
            
        Returns:
            List of SearchResult objects
        """
        results = self.pubmed.search(query, max_results, **kwargs)
        
        # Log search
        self.search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(results)
        })
        
        return results
    
    def search_mesh_terms(self, topic: str) -> List[Dict]:
        """
        Search MeSH terms for a topic.
        
        Returns:
            List of MeSH term dictionaries
        """
        # Use Entrez eutils for MeSH
        params = {
            "db": "mesh",
            "term": topic,
            "retmode": "json"
        }
        
        url = f"{PUBMED_EUTILS}esearch.fcgi?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("esearchresult", {}).get("idlist", [])
        except Exception:
            return []
    
    def to_bibtex(self, results: List[SearchResult] = None, pmids: List[str] = None) -> str:
        """
        Generate BibTeX for search results.
        
        Args:
            results: List of SearchResult objects
            pmids: List of PMIDs to fetch and convert
            
        Returns:
            BibTeX string
        """
        if pmids and not results:
            articles = self.pubmed._fetch_details(pmids)
        elif results:
            articles = results
        else:
            return ""
        
        bibtex_entries = []
        for i, article in enumerate(articles):
            key = f"{article.authors[0].split()[-1] if article.authors else 'Unknown'}{article.pub_date[:4] if article.pub_date else ''}_{i}"
            bibtex_entries.append(article.to_bibtex(key))
        
        return "\n\n".join(bibtex_entries)
    
    def to_ris(self, results: List[SearchResult]) -> str:
        """Generate RIS format for export"""
        return "\n".join([r.to_ris() for r in results])
    
    def to_markdown(self, results: List[SearchResult], numbered: bool = True) -> str:
        """Generate markdown reference list"""
        lines = ["## References", ""]
        for i, result in enumerate(results, 1):
            if numbered:
                lines.append(f"{i}. {result.to_markdown()}")
            else:
                lines.append(f"- {result.to_markdown()}")
        return "\n".join(lines)
    
    def build_reference_list(self, pmids: List[str]) -> List[str]:
        """
        Build a reference list from PMIDs.
        
        Returns:
            List of formatted citations
        """
        articles = self.pubmed._fetch_details(pmids)
        return [r.to_markdown() for r in articles]
    
    def get_related_articles(self, pmid: str, max_results: int = 10) -> List[SearchResult]:
        """Get articles related to a PMID"""
        params = {
            "db": "pubmed",
            "linkname": "pubmed_pubmed",
            "id": pmid,
            "retmode": "json",
            "api_key": self.pubmed.api_key
        }
        
        url = f"{PUBMED_EUTILS}elink.fcgi?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                link_set = data.get("linksets", [{}])[0]
                link_ids = link_set.get("links", [[]])[0][:max_results]
                
                if link_ids:
                    return self.pubmed._fetch_details(link_ids)
        except Exception:
            pass
        
        return []
    
    def citation_matrix(self, pmids: List[str]) -> Dict[str, List[str]]:
        """
        Build a citation matrix showing which articles cite which.
        
        Returns:
            Dict mapping PMID to list of citing PMIDs
        """
        matrix = {}
        
        for pmid in pmids:
            related = self.get_related_articles(pmid, max_results=20)
            matrix[pmid] = [r.pmid for r in related if r.pmid in pmids]
        
        return matrix


def literature_search_example():
    """Example usage of literature search"""
    search = LiteratureSearch()
    
    print("=" * 70)
    print("MEDSCI LITERATURE SEARCH - EXAMPLE USAGE")
    print("=" * 70)
    
    # Example search
    print("\n🔍 Searching PubMed: MASLD cardiovascular outcomes...")
    results = search.search("MASLD cardiovascular outcomes", max_results=5)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   Authors: {', '.join(result.authors[:3])}{' et al.' if len(result.authors) > 3 else ''}")
        print(f"   Journal: {result.journal} ({result.pub_date[:4] if result.pub_date else 'N/A'})")
        print(f"   PMID: {result.pmid}")
        if result.doi:
            print(f"   DOI: {result.doi}")
    
    # BibTeX example
    if results:
        print("\n📚 BibTeX output:")
        print(search.to_bibtex(results[:2]))
    
    # Verify citations
    print("\n✅ Citation verification:")
    verified = search.pubmed.verify_citations([
        "10.1016/S0140-6736(23)00000-X",
        "38339671"
    ])
    for cite, result in verified.items():
        status = "✓" if result["exists"] else "✗"
        print(f"  {status} {cite}: {result.get('title', 'NOT FOUND')[:50]}...")
    
    return search


if __name__ == "__main__":
    literature_search_example()
