import random
import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# ML model libraries
import os
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors


class ActionCheckSufficientFunds(Action):
    def name(self) -> Text:
        return "action_check_sufficient_funds"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # hard-coded balance for tutorial purposes. in production this
        # would be retrieved from a database or an API
        balance = 1000
        transfer_amount = tracker.get_slot("amount")
        has_sufficient_funds = transfer_amount <= balance
        return [SlotSet("has_sufficient_funds", has_sufficient_funds)]
    
class ActionGetRandomBookVolume(Action):
    def name(self) -> Text:
        return "action_get_random_author"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_search_url = "https://openlibrary.org/search.json"
        author = tracker.get_slot("author")

        params = {
            "q": f"author:{author}",  # Example search query
            "lang": "en",
            "sort": "rating"
        }

        try:
            # Make the API request
            response = requests.get(api_search_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the JSON response
            volumes = response.json()["docs"][:5]

            if volumes:
                dispatcher.utter_message(text=f"Aha! I found books by that author!")
                # Select a random volume
                random_volume = random.choice(volumes)
                volume_title = random_volume.get("title", "Unknown Title")
                return [SlotSet("book_recommendation_1", volume_title)]
            else:
                return [SlotSet("book_recommendation_1", None)]

        except requests.exceptions.RequestException as e:
            return [SlotSet("book_recommendation_1", None)]

class ActionGetDescription(Action):
    def name(self) -> Text:
        return "action_get_description"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_seed_url = "https://openlibrary.org"
        api_search_url = "https://openlibrary.org/search.json"
        book = tracker.get_slot("book_description_request")

        params = {
            "q": f"title:{book}",  # Search for the book by title
            "lang": "en",
            "sort": "rating"
        }

        try:
            # Make the API request to search for books
            response = requests.get(api_search_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the JSON response
            volumes = response.json().get("docs", [])
            
            if volumes:
                # Assume the first result is the correct one
                volume = volumes[0]
                key = volume.get("key", None)
                if key:
                    dispatcher.utter_message(text=f"The link for that work in OpenLibrary is {api_seed_url}{key}")
                    dispatcher.utter_message(text=f"I'm looking for more details...")
                    # Get the work details using the key
                    work_response = requests.get(f"{api_seed_url}{key}.json")
                    work_response.raise_for_status()

                    # Parse the work response JSON
                    work_data = work_response.json()

                    # Get the description, if available
                    work_description = work_data.get("description", "No description available.")
                    
                    # Set the book description slot
                    return [SlotSet("book_description", work_description)]
                else:
                    # If no key is found, set the description slot to None
                    dispatcher.utter_message(text=f"I'm sorry, I couldn't find that book in Open Library.")
                    return [SlotSet("book_description", None)]
            else:
                # No books found, set the description slot to None
                dispatcher.utter_message(text=f"I'm sorry, I couldn't find that book in Open Library.")
                return [SlotSet("book_description", None)]

        except requests.exceptions.RequestException as e:
            # In case of an error (e.g., API request failure), set the description to None
            return [SlotSet("book_description", None)]

class ActionGetSimilarGenre(Action):
    def name(self) -> Text:
        return "action_get_book_of_similar_genre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_seed_url = "https://openlibrary.org/"
        api_search_url = "https://openlibrary.org/search.json"
        book = tracker.get_slot("book_request")

        params = {
            "q": f"title:{book}",  # Search for the book by title
            "lang": "en"
        }    

        try:
            # Make the API request
            response = requests.get(api_search_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse JSON response and assume the first result is the correct one
            book_data = response.json()["docs"][0]
            key = book_data.get("key", None) # Get key for the work in Open Library


            # Step 2: Get subjects for the book
            work_response = requests.get(f"{api_seed_url}{key}.json")
            work_response.raise_for_status()
            work_data = work_response.json()
            subjects = work_data.get("subjects", [])
            if not subjects:
                dispatcher.utter_message(text=f"Couldn't find subjects for the book '{book}'.")
                return self.clear_recommendation_slots()

            if subjects:
                top_subjects = subjects[:2]

                dispatcher.utter_message(text=f"I've found that the book {book} is related to {', '.join(top_subjects[:2])}")
                dispatcher.utter_message(text=f"Looking for similar books...")
                subject_query = "+".join(top_subjects[:2])
                subject_params = {"subject": subject_query, "sort": "rating", "lang": "en"}

                similar_genre_response = requests.get(api_search_url, params=subject_params)
                similar_genre_response.raise_for_status()
                similar_books = similar_genre_response.json().get("docs", [])

                recommendations = []
                for similar_book in similar_books[:3]:  # Limit to top 3 recommendations
                    title = similar_book.get("title", "Unknown Title")
                    author_name = similar_book.get("author_name", ["Unknown Author"])[0]
                    recommendations.append(f"{title} by {author_name}")
                    
                for i in range(3):
                    slot_name = f"book_recommendation_{i + 1}"
                    slot_value = recommendations[i] if i < len(recommendations) else None
                    SlotSet(slot_name, slot_value)
                    
            return [
                SlotSet("book_recommendation_1", recommendations[0] if len(recommendations) > 0 else None),
                SlotSet("book_recommendation_2", recommendations[1] if len(recommendations) > 1 else None),
                SlotSet("book_recommendation_3", recommendations[2] if len(recommendations) > 2 else None),
            ]

        except requests.exceptions.RequestException as e:
            return [SlotSet("book_recommendation", None)]        
        
class ActionRecommendLiked(Action):
    def name(self) -> Text:
        return "action_get_book_others_liked"
    
    def __init__(self):
        #base_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
        books_file = os.path.join("db", "Books.csv")
        ratings_file = os.path.join("db", "Ratings.csv")

        # Load books dataset
        self.df_books = pd.read_csv(books_file)[['ISBN', 'Book-Title', 'Book-Author']]
        self.df_books.dropna(inplace=True)

        # Load and clean ratings dataset
        df_ratings = pd.read_csv(ratings_file)
        user_ratings = df_ratings['User-ID'].value_counts()
        df_ratings = df_ratings[~df_ratings['User-ID'].isin(user_ratings[user_ratings < 200].index)]

        book_ratings = df_ratings['ISBN'].value_counts()
        self.df_ratings = df_ratings[~df_ratings['ISBN'].isin(book_ratings[book_ratings < 100].index)]

        # Create the user-item matrix
        df = self.df_ratings.pivot_table(index=['User-ID'], columns=['ISBN'], values='Book-Rating').fillna(0).T
        df.index = df.join(self.df_books.set_index('ISBN'))['Book-Title']
        self.df = df.sort_index()

        # Train the recommendation model
        self.model = NearestNeighbors(metric='cosine')
        self.model.fit(self.df.values)

    def get_recommends(self, title: str) -> List[Dict[str, Any]]:
        # Find matching books by title
        matching_books = self.df[self.df.index.str.contains(title, case=False, na=False)]
        if matching_books.empty:
            return []

        # Use the first matching book
        book = matching_books.iloc[0]
        distances, indices = self.model.kneighbors([book.values], n_neighbors=4)

        # Collect recommendations
        recommended_books = [
            {"title": self.df.iloc[idx].name, "distance": dist}
            for dist, idx in zip(distances[0], indices[0])
        ]
        return recommended_books[1:]  # Exclude the input book itself

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[SlotSet]:
        book_request = tracker.get_slot("book_request")
        if not book_request:
            dispatcher.utter_message(text="Please provide a book title to get recommendations.")
            return [SlotSet("book_recommendation_1", None),
                    SlotSet("book_recommendation_2", None),
                    SlotSet("book_recommendation_3", None)]

        # Get recommendations
        recommendations = self.get_recommends(book_request)
        if not recommendations:
            dispatcher.utter_message(text=f"Sorry, I couldn't find recommendations for '{book_request}'.")
            return [SlotSet("book_recommendation_1", None),
                    SlotSet("book_recommendation_2", None),
                    SlotSet("book_recommendation_3", None)]

        # Set slots with recommendations
        for i in range(3):
            slot_name = f"book_recommendation_{i + 1}"
            slot_value = recommendations[i]["title"] if i < len(recommendations) else None
            SlotSet(slot_name, slot_value)

        return [
            SlotSet("book_recommendation_1", recommendations[0]["title"] if len(recommendations) > 0 else None),
            SlotSet("book_recommendation_2", recommendations[1]["title"] if len(recommendations) > 1 else None),
            SlotSet("book_recommendation_3", recommendations[2]["title"] if len(recommendations) > 2 else None),
        ]
    
class ActionGetBookByGenre(Action):
    def name(self) -> Text:
        return "action_get_book_by_genre"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_search_url = "https://openlibrary.org/search.json"
        genre = tracker.get_slot("genre")

        params = {
            "q": f"subject:{genre}",  # Example search query
            "lang": "en",
            "sort": "rating"
        }

        try:
            # Make the API request
            response = requests.get(api_search_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the JSON response
            volumes = response.json()["docs"][:20]

            if volumes:
                dispatcher.utter_message(text=f"I found {genre} books!")
                
                # Get 3 random books from the list (if there are fewer than 3, return what is available)
                random_books = random.sample(volumes, min(3, len(volumes)))

                recommendations = []
                for book in random_books:  
                    title = book.get("title", "Unknown Title")
                    author_name = book.get("author_name", ["Unknown Author"])[0]
                    recommendations.append(f"{title} by {author_name}")                 

                for i in range(3):
                    slot_name = f"book_recommendation_{i + 1}"
                    slot_value = recommendations[i] if i < len(recommendations) else None
                    SlotSet(slot_name, slot_value)

            return [
                SlotSet("book_recommendation_1", recommendations[0] if len(recommendations) > 0 else None),
                SlotSet("book_recommendation_2", recommendations[1] if len(recommendations) > 1 else None),
                SlotSet("book_recommendation_3", recommendations[2] if len(recommendations) > 2 else None),
            ]

        except requests.exceptions.RequestException as e:
            return [SlotSet("book_recommendation", None)]    
        
class ActionGetBookByPlace(Action):
    def name(self) -> Text:
        return "action_get_book_by_place"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_search_url = "https://openlibrary.org/search.json"
        place = tracker.get_slot("place")

        params = {
            "q": f"place:{place}",  # Example search query
            "lang": "en",
            "sort": "rating"
        }

        try:
            # Make the API request
            response = requests.get(api_search_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the JSON response
            volumes = response.json()["docs"][:20]

            if volumes:
                dispatcher.utter_message(text=f"I found books set in {place}!")
                
                # Get 3 random books from the list (if there are fewer than 3, return what is available)
                random_books = random.sample(volumes, min(3, len(volumes)))

                recommendations = []
                for book in random_books:  
                    title = book.get("title", "Unknown Title")
                    author_name = book.get("author_name", ["Unknown Author"])[0]
                    recommendations.append(f"{title} by {author_name}")                 

                for i in range(3):
                    slot_name = f"book_recommendation_{i + 1}"
                    slot_value = recommendations[i] if i < len(recommendations) else None
                    SlotSet(slot_name, slot_value)

            return [
                SlotSet("book_recommendation_1", recommendations[0] if len(recommendations) > 0 else None),
                SlotSet("book_recommendation_2", recommendations[1] if len(recommendations) > 1 else None),
                SlotSet("book_recommendation_3", recommendations[2] if len(recommendations) > 2 else None),
            ]

        except requests.exceptions.RequestException as e:
            return [SlotSet("book_recommendation", None)]    