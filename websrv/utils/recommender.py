import random
from collections import Counter
from typing import List, Tuple

common_function_words = {
    # Articles
    "a", "an", "the",

    # Prepositions
    "about", "above", "across", "after", "against", "along", "among", "around",
    "at", "before", "behind", "below", "beneath", "beside", "between", "beyond",
    "but", "by", "concerning", "despite", "down", "during", "except", "for",
    "from", "in", "inside", "into", "like", "near", "of", "off", "on", "onto",
    "out", "outside", "over", "past", "regarding", "since", "through", "throughout",
    "to", "toward", "under", "underneath", "until", "up", "upon", "with", "within", "without",

    # Possessive pronouns
    "my", "your", "his", "her", "its", "our", "their",

    # Demonstratives
    "this", "that", "these", "those",

    # Auxiliary/modal verbs
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "can", "could", "shall", "should", "will", "would", "may", "might", "must",

    # Conjunctions
    "and", "but", "or", "yet", "so", "for", "nor",

    # Other common function words
    "if", "because", "as", "than", "too", "very"
}

class Recommender:
    """Class for generating bill reccomendations"""
    def __init__(self, k=10) -> None:
        self.cnt = Counter()
        self.k = k
        pass

    def fit_title(self, s: str) -> None:
        words = s.lower().split()
        filtered_words = [word for word in words if word not in common_function_words]
        temp = Counter(filtered_words)
        self.cnt.update(temp)
    
    def generate_weight_lists(self) -> Tuple[List[str], List[float]]:
        """Generating keyword list and its weight list"""
        keywords = list(self.cnt.keys())
        total = sum(self.cnt.values())
        weights = [ v/total for v in self.cnt.values()]
        return keywords, weights
    
    def get_candidate_words(self) -> List[str]:
        """Get recommendated keywords"""
        keywords, weights = self.generate_weight_lists()
        return random.choices(keywords, weights, k=self.k)
