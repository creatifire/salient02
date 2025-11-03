<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Demo: Retrieve and Summarize arXiv Articles

## Project Vision Summary

This script forms the foundational component of a multi-tiered arXiv intelligence service. The goal is to build a service that helps users stay updated with and understand scientific literature.

### Tier 1: Core Service (Free)
1. **Daily Retrieval**: Automatically retrieves new arXiv articles based on user-selected topics for a given day.
2. **Abstract Extraction**: Extracts the title, authors, abstract, and direct link for each article.
3. **Email Digest**: Assembles the collected information into a daily email digest, providing a quick overview of the latest research.

### Tier 2: Standard Paid Service (LLM-Powered Explainers)
1. **LLM-Enhanced Content**: For each article, an LLM generates a simplified "explainer." This includes:
   - Key takeaways in bullet points.
   - Content tuned to the user's specified knowledge level (e.g., High School, Graduate, Expert).
   - A set of questions to test the reader's comprehension.
2. **CRM/Database Storage**: All generated explainers and rephrased articles are stored in a searchable CRM or database.
3. **Web Portal Access**: Links in the daily email direct users to a web page displaying the enhanced, LLM-generated content, rather than the raw arXiv abstract.

### Tier 3: Premium Paid Service (On-Demand Research Synthesis)
1. **Custom Searches**: Users can perform their own advanced searches across the arXiv database.
2. **Multi-Article Synthesis**: Users can select multiple articles on related topics.
3. **Automated Slide Deck Generation**: The service uses an LLM to synthesize the information from the selected articles and automatically generate a presentation slide deck (in PowerPoint and/or Google Slides format).

## Installation

First, make sure you have the library installed:

```bash
pip install arxiv
```

## Python Implementation

```python
import arxiv
import datetime

def get_abstracts_for_day(topic, date_str, max_results=50):
    """
    Fetches articles on a given topic from arXiv that were published or
    updated on a specific day.

    Args:
        topic (str): The search query or topic (e.g., "quantum computing").
        date_str (str): The date to search for, in "YYYY-MM-DD" format.
        max_results (int): The maximum number of results to retrieve.
    """
    try:
        # --- 1. Parse the date and create a 24-hour range ---
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        # Start of the day (00:00:00)
        start_of_day = datetime.datetime.combine(target_date, datetime.time.min)
        # End of the day (23:59:59)
        end_of_day = datetime.datetime.combine(target_date, datetime.time.max)

        # Format for arXiv API query (YYYYMMDDHHMMSS)
        start_day_str = start_of_day.strftime("%Y%m%d%H%M%S")
        end_day_str = end_of_day.strftime("%Y%m%d%H%M%S")

        # --- 2. Construct the Advanced Query ---
        # We combine the topic with the date range for the 'lastUpdatedDate' field.
        # The format is: (your_topic) AND (lastUpdatedDate:[START TO END])
        query = f'({topic}) AND (lastUpdatedDate:[{start_day_str} TO {end_day_str}])'

        # --- 3. Create the Search Object ---
        # We use the new, more specific query.
        # Sorting by relevance might be more useful here than by date,
        # since they are all from the same day.
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        print(f"Fetching papers for the topic '{topic}' updated on {date_str}\n")
        print(f"Using query: {query}\n")

        # --- 4. Iterate Through Results ---
        results_generator = search.results()

        count = 0
        for result in results_generator:
            count += 1
            title = result.title
            abstract = result.summary
            article_id = result.get_short_id()
            primary_category = result.primary_category
            # The 'updated' field shows the precise update time
            updated_time = result.updated.strftime("%Y-%m-%d %H:%M:%S UTC")

            print(f"--- Article {count} ({article_id}) ---")
            print(f"Title: {title}")
            print(f"Primary Category: {primary_category}")
            print(f"Last Updated: {updated_time}")
            print("\nAbstract:")
            print(abstract.replace('\n', ' '))
            print("\n" + "="*80 + "\n")

        if count == 0:
            print("No articles found for this topic on the specified day.")

    except ValueError:
        print(f"Error: Incorrect date format. Please use 'YYYY-MM-DD'.")
    except Exception as e:
        print(f"An error occurred: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    # Define the topic you are interested in
    search_topic = "astro-ph"  # Astrophysics category
    
    # Define the specific day you want to search
    # Let's use yesterday's date as an example
    search_date = "2025-08-26"
    
    # Call the function to fetch and print the abstracts
    get_abstracts_for_day(search_topic, search_date)
```

## Usage Example

This script demonstrates the core functionality for Tier 1 of the arXiv intelligence service. It retrieves and displays articles from a specific date and topic, which forms the foundation for the more advanced features in higher tiers.
