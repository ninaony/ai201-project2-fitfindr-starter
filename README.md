# FitFindr

FitFindr is a Groq-powered thrift shopping assistant: you describe what you're looking for, it finds the best match from a mock secondhand dataset, suggests how to style it with your existing wardrobe, and generates a shareable outfit caption.

## How to run it

```bash
pip install -r requirements.txt
```

set API key in .env here:

```
GROQ_API_KEY=your_key_here
```

then run:

```
python app.py
```

## How it works

### Architecture overview

The agent (agent.py) orchestrates the pipeline by calling the tools (tools.py). Each handle one step — search_listings uses keyword scoring without an LLM; the other three (parse_query, suggest_outfit, create_fit_card) call Groq.

### Flow

1. You enter a query detailing what clothing item you are trying to find as well and select a wardrobe option.
2. LLM parses your query (parse_query) →
3. Keyword search takes in the parsed query, filters and scores listings, and returns a list of list of results (search_listings)\* →
4. LLM takes the new item and your wardrobe, and suggests outfit using the items in your wardrobe. If there are no items to match, it'll give generic advice. (suggest_outfit()) →
5. LLM takes the new item and the outfit suggestion to generate a caption you can post. (create_fit_card)

\*If you search for something with no matches, the app tells you rather than crashing.

### Example queries

- "vintage graphic tee under $30"
- "90s track jacket in size M"
- "flowy midi skirt under $40"
- "black combat boots size 8"
- "designer ballgown size XXS under $5"

## Data provided

### The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

### The Wardrobe Schema

`data/wardrobe_schema.json` contains sample wardrobes— the app lets you toggle between this and an empty wardrobe to test both paths. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user
