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
        api_url = "https://openlibrary.org/search.json"
        author = tracker.get_slot("author")

        params = {
            "q": f"author:{author}",  # Example search query
            "lang": "en",
            "sort": "rating"
        }

        try:
            # Make the API request
            response = requests.get(api_url, params=params)
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