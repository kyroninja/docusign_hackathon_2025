from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy

# Load english model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print('Downloading language model for the spaCy POS tagger...Downloading now')
    from spacy.cli import download
    download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

# Initialize VADER Sentiment
analyzer = SentimentIntensityAnalyzer()

# Step 1: Label words as S, V, O, or M
def label_word(word):
    doc = nlp(word)
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN", "PRON"]:
            return "S"  # Subject
        elif token.pos_ in ["VERB", "AUX"]:
            return "V"  # Verb
        elif token.pos_ in ["ADJ", "ADV", "DET", "ADP"]:
            return "M"  # Modifier
        elif token.dep_ in ["dobj", "pobj", "obj"]:
            return "O"  # Object
    return "M"  # Default to Modifier

# Step 2: Analyze sentences and extract SVO(M) structures
def analyze_sentence(sentence):
    doc = nlp(sentence)
    svo_structure = {"S": [], "V": [], "O": [], "M": []}
    sentiment_scores = {"S": 0, "V": 0, "O": 0, "M": 0}

    # Tokenize and label
    for token in doc:
        label = label_word(token.text)
        svo_structure[label].append(token.text)

    # Calculate sentiment for each part
    for part in ["S", "V", "O", "M"]:
        text = " ".join(svo_structure[part])
        if text:  # Only calculate if part exists
            sentiment_scores[part] = analyzer.polarity_scores(text)["compound"]

    # Determine structure weight
    detected_parts = [part for part in ["S", "V", "O", "M"] if svo_structure[part]]
    weight = len(detected_parts)

    # Calculate overall sentiment
    overall_sentiment = sum(sentiment_scores[part] for part in detected_parts) / weight if weight else 0
    return overall_sentiment, sentiment_scores, detected_parts

# Step 3: Analyze all sentences and append those with valid sentiments
def return_sentiment(sentences):
    
    results = {}
    final_sentences = []  # To store sentences that meet the condition

    for sentence in sentences:
        overall_sentiment, sentiment_scores, detected_parts = analyze_sentence(sentence)
        structure = "".join(detected_parts)  # e.g., SVO
        overall_percent_sentiment = round(overall_sentiment * 100, 2)

        # Check sentiment conditions (greater than 25% or less than -15%)
        if overall_percent_sentiment > 25 or overall_percent_sentiment < -15:
            final_sentences.append([sentence,"Percentage Sentiment: "+str(overall_percent_sentiment)])

        results[sentence] = {
            "Overall Sentiment": round(overall_sentiment, 2),
            "Part Sentiments": sentiment_scores,
            "Detected Structure": structure,
            "Percentage Sentiment": overall_percent_sentiment,
        }
    return (results, final_sentences)