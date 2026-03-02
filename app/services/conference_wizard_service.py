"""
Conference Wizard Service

Searches for conference information using DuckDuckGo, scrapes the conference website,
and uses an LLM to extract structured conference data.
"""

import json
import re
import logging

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger('conference_wizard')


# Well-known CORE rankings for top conferences (helps smaller LLMs)
KNOWN_CORE_RANKINGS = {
    'NeurIPS': 'A*', 'ICML': 'A*', 'ICLR': 'A*', 'AAAI': 'A*', 'IJCAI': 'A*',
    'CVPR': 'A*', 'ICCV': 'A*', 'ECCV': 'A*', 'ACL': 'A*', 'EMNLP': 'A*',
    'NAACL': 'A', 'COLING': 'A', 'SIGIR': 'A*', 'KDD': 'A*', 'WWW': 'A*',
    'SIGMOD': 'A*', 'VLDB': 'A*', 'ICDE': 'A*', 'PODS': 'A*',
    'STOC': 'A*', 'FOCS': 'A*', 'SODA': 'A*',
    'CHI': 'A*', 'UIST': 'A*', 'CSCW': 'A',
    'OSDI': 'A*', 'SOSP': 'A*', 'NSDI': 'A*', 'SIGCOMM': 'A*',
    'CCS': 'A*', 'S&P': 'A*', 'USENIX Security': 'A*', 'NDSS': 'A*',
    'ISCA': 'A*', 'MICRO': 'A*', 'HPCA': 'A*', 'ASPLOS': 'A*',
    'PLDI': 'A*', 'POPL': 'A*', 'OOPSLA': 'A*', 'ICSE': 'A*', 'FSE': 'A*', 'ASE': 'A*',
    'RSS': 'A*', 'ICRA': 'A*', 'IROS': 'A',
    'MICCAI': 'A', 'ISBI': 'B',
    'INTERSPEECH': 'A', 'ICASSP': 'A',
    'AAMAS': 'A*', 'ECAI': 'A', 'EACL': 'A',
    'ACM MM': 'A*', 'SIGGRAPH': 'A*',
    'LREC': 'B', 'TSD': 'B', 'SemEval': 'B',
    'WACV': 'A', 'BMVC': 'A',
    'PAKDD': 'A', 'ECML-PKDD': 'A', 'ICDM': 'A*', 'SDM': 'A',
    'CIKM': 'A', 'WSDM': 'A*', 'RecSys': 'A',
    'UAI': 'A*', 'AISTATS': 'A', 'CoRL': 'A',
}

# Academic conference directories/databases — high-trust for scraping
ACADEMIC_DOMAINS = [
    'wikicfp.com', 'researchr.org', 'dblp.org', 'portal.core.edu.au',
    'conferencedeadlines.com', 'allai.events', 'openreview.net',
    'aclweb.org', 'springer.com', 'ieee.org', 'acm.org',
]


class ConferenceWizardService:
    """Service for AI-powered conference lookup and data extraction."""

    SCRAPE_TIMEOUT = 10
    SCRAPE_MAX_TEXT = 30_000
    SEARCH_MAX_RESULTS = 8

    STRIP_TAGS = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']

    @staticmethod
    def search_and_analyze(query, client, model_id):
        """
        Generator yielding SSE event dicts for conference wizard streaming.

        Args:
            query: Conference name, acronym, or URL
            client: Pre-fetched OpenAI-compatible LLM client
            model_id: Resolved model ID for the client

        Yields:
            dict with 'event' and 'data' keys for SSE formatting
        """
        try:
            # Step 1: Search DuckDuckGo
            yield {'event': 'searching', 'data': {'query': query}}

            search_results = ConferenceWizardService._search_duckduckgo(query)

            yield {'event': 'search_results', 'data': {
                'count': len(search_results),
                'results': [{'title': r['title'], 'url': r['href']} for r in search_results]
            }}

            if not search_results:
                yield {'event': 'error', 'data': {'error': 'no_results', 'message': 'No search results found.'}}
                return

            # Step 2: Scrape top URLs (up to 2 best sources)
            urls_to_scrape = ConferenceWizardService._rank_urls(search_results, query)
            scraped_pages = []

            for url in urls_to_scrape[:2]:
                yield {'event': 'scraping', 'data': {'url': url}}
                text = ConferenceWizardService._scrape_website(url)
                if text and len(text) > 100:
                    scraped_pages.append({'url': url, 'text': text})

            # Step 3: LLM extraction
            yield {'event': 'thinking', 'data': {'message': 'Extracting conference data...'}}

            prompt = ConferenceWizardService._build_prompt(query, search_results, scraped_pages)

            response_text = ''
            stream = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": prompt['system']},
                    {"role": "user", "content": prompt['user']}
                ],
                max_tokens=2000,
                temperature=0.1,
                stream=True,
                extra_body={"response_format": {"type": "json_object"}}
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    yield {'event': 'chunk', 'data': {'content': content}}

            # Step 4: Parse result
            conference_data = ConferenceWizardService._parse_llm_response(response_text)

            if conference_data:
                # Enrich with known CORE ranking if LLM missed it
                acronym = conference_data.get('acronym', '').upper()
                if conference_data.get('core_ranking') == 'Unranked' and acronym in KNOWN_CORE_RANKINGS:
                    conference_data['core_ranking'] = KNOWN_CORE_RANKINGS[acronym]

                # Fallback website URL from best scraped source
                if not conference_data.get('website_url') and urls_to_scrape:
                    conference_data['website_url'] = urls_to_scrape[0]

                yield {'event': 'result', 'data': conference_data}

            yield {'event': 'done', 'data': {'success': True}}

        except Exception as e:
            logger.error(f"Conference wizard failed: {e}")
            yield {'event': 'error', 'data': {'error': 'failed', 'message': str(e)}}

    @staticmethod
    def _search_duckduckgo(query):
        """
        Search DuckDuckGo for conference information.
        Uses two queries: a general one and a CFP-specific one to reliably find academic conferences.
        """
        try:
            ddgs = DDGS()
            seen_urls = set()
            all_results = []

            # Query 1: general conference search
            query_lower = query.lower()
            q1 = query
            if 'conference' not in query_lower and 'symposium' not in query_lower and 'workshop' not in query_lower:
                q1 = f"{query} conference"

            for r in ddgs.text(q1, max_results=5):
                if r.get('href') not in seen_urls:
                    seen_urls.add(r['href'])
                    all_results.append(r)

            # Query 2: CFP-specific search (finds academic sources reliably)
            q2 = f"{query} CFP call for papers"
            for r in ddgs.text(q2, max_results=5):
                if r.get('href') not in seen_urls:
                    seen_urls.add(r['href'])
                    all_results.append(r)

            return all_results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []

    @staticmethod
    def _scrape_website(url):
        """Scrape text content from a conference website."""
        try:
            resp = requests.get(
                url,
                timeout=ConferenceWizardService.SCRAPE_TIMEOUT,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; LLARS ConferenceWizard/1.0)'},
                allow_redirects=True,
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'lxml')

            for tag in soup.find_all(ConferenceWizardService.STRIP_TAGS):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)

            if len(text) > ConferenceWizardService.SCRAPE_MAX_TEXT:
                text = text[:ConferenceWizardService.SCRAPE_MAX_TEXT]

            return text

        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return ''

    @staticmethod
    def _rank_urls(results, query=''):
        """
        Rank search result URLs by relevance for academic conferences.
        Returns sorted list of URLs — query-matching and academic directories first.
        """
        query_terms = set(query.lower().split()) - {'conference', 'symposium', 'workshop', 'academic'}

        scored = []
        for r in results:
            url = r.get('href', '').lower()
            title = r.get('title', '').lower()
            body = r.get('body', '').lower()
            score = 0

            # Highest priority: title or URL contains query terms (acronym match)
            matching_terms = sum(1 for term in query_terms if term in title or term in url)
            score += matching_terms * 30

            # Strongly prefer academic conference directories
            for domain in ACADEMIC_DOMAINS:
                if domain in url:
                    score += 40
                    break

            # Prefer URLs with year in path (likely specific edition)
            if re.search(r'20\d{2}', url):
                score += 15

            # Prefer URLs with CFP/call-for-papers indicators
            if any(kw in title or kw in body for kw in ['call for papers', 'cfp', 'submission', 'deadline', 'important dates']):
                score += 15

            # Prefer URLs mentioning dates, venue, location
            if any(kw in body for kw in ['venue', 'location', 'date', 'registration']):
                score += 10

            # Deprioritize Wikipedia, video sites
            if 'wikipedia.org' in url:
                score -= 20
            if any(d in url for d in ['vimeo.com', 'youtube.com', 'vk.com']):
                score -= 50

            scored.append((score, r.get('href', '')))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in scored]

    @staticmethod
    def _build_prompt(query, search_results, scraped_pages):
        """Build system and user prompts for LLM conference data extraction."""

        # Build CORE ranking reference snippet
        core_snippet = ', '.join(f'{k}={v}' for k, v in sorted(KNOWN_CORE_RANKINGS.items())[:60])

        system_prompt = f"""You are an expert at extracting structured information about ACADEMIC conferences.
You are given search results and scraped website content. Extract the conference details into a JSON object.

IMPORTANT: Focus on the ACADEMIC/SCIENTIFIC conference matching the query. Ignore non-academic results.

Return ONLY a valid JSON object with these fields (use null for unknown values):
{{
  "name": "Full official conference name",
  "acronym": "Short acronym (e.g. NeurIPS, IJCAI, TSD)",
  "year": 2026,
  "core_ranking": "A*|A|B|C|Unranked",
  "submission_deadline": "ISO datetime or null",
  "notification_date": "ISO datetime or null",
  "start_date": "ISO datetime or null",
  "end_date": "ISO datetime or null",
  "city": "City name or null",
  "country": "Country name or null",
  "website_url": "Official conference website URL or null",
  "keywords": ["keyword1", "keyword2"],
  "notes": "1-2 sentence summary of the conference topics"
}}

Guidelines:
- Dates in ISO 8601: YYYY-MM-DDTHH:MM:SS (if only date known, use T00:00:00)
- CORE ranking reference: {core_snippet}
- If the conference is not in the reference list, estimate based on similar conferences or use "Unranked".
- Extract city and country from venue/location information. Look carefully in the scraped content for this.
- Look for "Important Dates" sections on conference websites for deadlines.
- keywords: 3-5 main research topics of the conference.
- website_url: The official conference website (not wikicfp/dblp/etc)."""

        # Format search results
        search_text = '\n'.join([
            f"- [{r.get('title', '')}]({r.get('href', '')}): {r.get('body', '')}"
            for r in search_results
        ])

        user_content = f"""Query: {query}

Search Results:
{search_text}"""

        # Add scraped pages
        for i, page in enumerate(scraped_pages):
            max_per_page = 20000 if i == 0 else 10000
            user_content += f"""

--- Scraped from {page['url']} ---
{page['text'][:max_per_page]}"""

        return {'system': system_prompt, 'user': user_content}

    @staticmethod
    def _parse_llm_response(response_text):
        """Parse LLM response, extracting JSON with fallback regex."""
        if not response_text:
            return None

        # Try direct JSON parse
        try:
            data = json.loads(response_text)
            return ConferenceWizardService._clean_conference_data(data)
        except json.JSONDecodeError:
            pass

        # Fallback: extract JSON object with regex
        match = re.search(r'\{[\s\S]*\}', response_text)
        if match:
            try:
                data = json.loads(match.group())
                return ConferenceWizardService._clean_conference_data(data)
            except json.JSONDecodeError:
                pass

        logger.warning("Failed to parse LLM response as JSON")
        return None

    @staticmethod
    def _clean_conference_data(data):
        """Clean and validate extracted conference data."""
        valid_rankings = {'A*', 'A', 'B', 'C', 'Unranked'}
        cleaned = {}

        str_fields = ['name', 'acronym', 'city', 'country', 'website_url', 'notes']
        for field in str_fields:
            val = data.get(field)
            if val and isinstance(val, str) and val.lower() != 'null':
                cleaned[field] = val.strip()

        date_fields = ['submission_deadline', 'notification_date', 'start_date', 'end_date']
        for field in date_fields:
            val = data.get(field)
            if val and isinstance(val, str) and val.lower() != 'null':
                cleaned[field] = val

        year = data.get('year')
        if year is not None:
            try:
                cleaned['year'] = int(year)
            except (ValueError, TypeError):
                pass

        ranking = data.get('core_ranking')
        if ranking in valid_rankings:
            cleaned['core_ranking'] = ranking
        else:
            cleaned['core_ranking'] = 'Unranked'

        keywords = data.get('keywords')
        if isinstance(keywords, list):
            cleaned['keywords'] = [str(k).strip() for k in keywords if k]
        else:
            cleaned['keywords'] = []

        return cleaned
