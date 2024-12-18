from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from transformers import AutoModelForCausalLM, AutoTokenizer

# Carica il modello e il tokenizer
tokenizer = AutoTokenizer.from_pretrained("OpenAssistant/oasst-sft-6-llama-30b")
model = AutoModelForCausalLM.from_pretrained("OpenAssistant/oasst-sft-6-llama-30b")

class ActionOpenAssistantResponse(Action):
    def name(self) -> str:
        return "action_openassistant_response"

    def generate_response(self, prompt: str) -> str:
        # Genera una risposta usando il modello OpenAssistant
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(inputs["input_ids"], max_length=100, num_return_sequences=1)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        # Ottieni l'ultimo messaggio dell'utente
        user_message = tracker.latest_message.get("text")
        
        # Genera una risposta
        assistant_response = self.generate_response(user_message)
        
        # Invia la risposta all'utente
        dispatcher.utter_message(text=assistant_response)
        return []