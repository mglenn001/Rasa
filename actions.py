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
        api_url = "https://www.googleapis.com/books/v1/volumes"
        author_of_choice = tracker.get_slot("author_of_choice")

        params = {
            "q": f"inauthor:{author_of_choice}&authors:{author_of_choice}",  # Example search query
            "langRestrict": "en",
            "maxResults": 40         # Adjust as needed to get more volumes
        }

        try:
            # Make the API request
            response = requests.get(api_url, params=params)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Parse the JSON response
            volumes = response.json().get("items", [])

            if volumes:
                # Select a random volume
                random_volume = random.choice(volumes)
                volume_title = random_volume['volumeInfo'].get('title', 'Unknown Title')
                
                dispatcher.utter_message(text=f"Here is a random {author_of_choice} book for you: '{volume_title}'.")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't find any book volumes.")
            
            return []

        except requests.exceptions.RequestException as e:
            # Handle any errors during the API request
            dispatcher.utter_message(text="Sorry, something went wrong while fetching book volumes.")
            return []