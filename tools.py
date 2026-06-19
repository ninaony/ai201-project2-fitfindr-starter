"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings, load_wardrobe_schema

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# Query parser -------------------------------------------
def parse_query(query: str) -> dict:

    client = _get_groq_client()

    prompt = f'''Can you please parse a description, a price, 
    and size using the exact words provided in this string: {query}. 
    The price should be formatted as just a number. No dollar sign or text. 
    If not provided, the value is "None". 
    Please format this as a json dictionary with these key names:
    "description", "price", "size" and there respective values as strings. 
    The output should only be this dictionary '''


    response = client.chat.completions.create(
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ], 
        model="llama-3.3-70b-versatile"
                )

    #return response.choices[0].message.content
    parsedQuery = response.choices[0].message.content
    #print(f"first parse {parsedQuery}")
    parsedQuery = json.loads(parsedQuery)

    
    for key in parsedQuery:
        if parsedQuery[key] == "None":
            parsedQuery[key] = None
        elif key == "price":
            parsedQuery[key] = float(parsedQuery[key])

    return parsedQuery

# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """


   
    listings = load_listings()
   
    #print(f"query: {description}, {size}, {max_price}")
    if size is not None:
        listings = [item for item in listings if item["size"]== size]
        #print(f"listings after size: {listings}")
    if max_price is not None:
        listings = [item for item in listings if item["price"] <= max_price ]
    
    search_words = description.lower().split()

    #print(f"looking for: {search_words}")
    for item in listings:
        item["score"] = 0

        for word in search_words:
            #print(f"item: {item["title"]} and {item["description"]} and {item["style_tags"]}")
            if word in item["title"].lower():
                item["score"] += 1
                continue
            elif word in item["description"].lower():
                item["score"] += 1
                continue
            for tag in item["style_tags"]:
                if word in tag.lower():
                    item["score"] += 1
                    break
    
    listings = [item for item in listings if item["score"] > 0]
    #print(f"listings after score removal: {listings}")

    listings.sort(key = lambda item: item["score"], reverse=True)
    
    #print(f"final listings: {listings}")
    
    return listings


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation

    prompt = f'''Can you please give me 1 - 2 sentence of styling advice for this item: {new_item["title"]}. 
        This item is a {new_item["description"].lower()}. 
        Here are a few words that describe the overall vibe: {", ".join(new_item["style_tags"])}.
        I would like 1 -3 clothing items that will pair well with it.'''
    
    if  wardrobe["items"]:
        
        wardrobe_readable = ", ".join(f'''{item["name"]}: I'd describe it as {item["style_tags"]}, and {item["notes"]}''' for item in wardrobe["items"])


        prompt = prompt + f" You can use this wardrobe for the 1-3 items: {wardrobe_readable}."

    client = _get_groq_client()
    response = client.chat.completions.create(messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="llama-3.3-70b-versatile")

    return response.choices[0].message.content
     


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
  
    if not outfit.strip():
        return "No outfit recieved"
    
    prompt = f'''I recently purchased this item, {new_item["title"].lower()} 
    from {new_item["platform"]} for ${new_item["price"]:.2f}.
    Here is an outfit suggestion I received for it: {outfit}. 
    Can you please give me a caption that I can post that's unique to the vibe of the outfit. 
    Mention the name, price, and platform once and briefly as an intro, 
    and finish it with another 1-2 sentences detailing why this outfit is interesting.'''

    client = _get_groq_client()
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user", 
                "content": prompt
            }
        ], 
        model="llama-3.3-70b-versatile", temperature=1.2)
    

    return response.choices[0].message.content

if __name__ == "__main__":

    #parsed = parse_query("90s track jacket in size M")
    parsed = parse_query("black combat boots size 8")
    #parsed = parse_query("90s track jacket in size M")

    print(f"parsed {parsed}")
    if  parsed["price"] == None:
        results =  search_listings(parsed["description"], parsed["size"], None)
    else:
        results = search_listings(parsed["description"], parsed["size"], parsed["price"])
    ##results = search_listings("vintage graphic tee", None, 30.00)
    
    select_keys = ["title", "score"]

    for item in results:
        print(item.get(select_keys[0]))
        print(item.get(select_keys[1]))
    
    #print(f" length: {len(results)}")
   
   
    wardrobe = load_wardrobe_schema()
    '''
    if not results:
        print ("No results returned")
    else:
        print(f"results {results}")
        '''

    outfit = suggest_outfit(results[0], wardrobe["example_wardrobe"])
    print(outfit)

    #outfit = suggest_outfit(results[0], wardrobe["empty_wardrobe"])
    #print(outfit_empty)
 
    wardrobe = load_wardrobe_schema()
    outfit = suggest_outfit(results[0], wardrobe["example_wardrobe"])
    caption = create_fit_card(outfit, results[0])
    print(caption)
  

    #parsed = parse_query("vintage graphic tee under $30")
    #print(f"parsed: {parsed} ")

    

