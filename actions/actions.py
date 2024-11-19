import random
import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


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
                # Select a random volume
                random_volume = random.choice(volumes)
                volume_title = random_volume.get("title", "Unknown Title")
                return [SlotSet("book_recommendation", volume_title)]
                #dispatcher.utter_message(text=f"Here is a random {author_of_choice} book for you: '{volume_title}'.")
            else:
                return [SlotSet("book_recommendation", None)]

        except requests.exceptions.RequestException as e:
            return [SlotSet("book_recommendation", None)]
        
# class ActionGetDescription(Action):
#     def name(self) -> Text:
#         return "action_get_description"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         api_seed_url = "https://openlibrary.org/"
#         api_search_url = "https://openlibrary.org/search.json"
#         book = tracker.get_slot("book_recommendation")

#         params = {
#             "q": f"title:{book}",  # Example search query
#             "lang": "en",
#             "sort": "rating"
#         }

#         try:
#             # Make the API request
#             response = requests.get(api_search_url, params=params)
#             response.raise_for_status()  # Raise an error for bad responses
            
#             # Parse the JSON response, assume first one is correct
#             volume = response.json()["docs"][0]

#             if volume:
#                 # Select a random volume
#                 key = volume.get("key", "Unknown")

#                 work_response = requests.get(f"{api_seed_url}{key}.json")
#                 work_response.raise_for_status()

#                 if work_response.status_code == 200:
#                     work_description = work_response.get("description", "Unknown")
                
#                 return [SlotSet("book_description", work_description)]
#                 #dispatcher.utter_message(text=f"Here is a random {author_of_choice} book for you: '{volume_title}'.")
#             else:
#                 return [SlotSet("book_description", None)]

#         except requests.exceptions.RequestException as e:
#             return [SlotSet("book_description", None)]

class ActionGetDescription(Action):
    def name(self) -> Text:
        return "action_get_description"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_seed_url = "https://openlibrary.org/"
        api_search_url = "https://openlibrary.org/search.json"
        book = tracker.get_slot("book_recommendation")

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
                    dispatcher.utter_message(text=f"The key for that work in OpenLibrary is {key}")
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
                    return [SlotSet("book_description", None)]
            else:
                # No books found, set the description slot to None
                return [SlotSet("book_description", None)]

        except requests.exceptions.RequestException as e:
            # In case of an error (e.g., API request failure), set the description to None
            return [SlotSet("book_description", None)]