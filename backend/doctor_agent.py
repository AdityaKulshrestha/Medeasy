from typing import Optional
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent

from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class Diagnoser:
    def __init__(self):
        diagnose_prompt = """You are a medical expert. Your task it to convert the given hindi conversation into English. So that it becomes easier for the doctor to diagnose the disease.
        {patient_complain}
        """
        validation_prompt = """You are a medical experiment. You have been given the patient's complain. You have to 
        diagnose the patient's disease. Identify and ask crucial question to help you narrow down and diagnose the 
        patient. Ask only one question based on the response. If no chat-history is provided ask initial first question. 
         
        Previous Conversation: {previous_conversation} 

        Patient Complain:
        {complain}

        Question:
        """

        ask_report_prompt = """
        You are an expert chat doctor. Your task is to suggest the best diagnosing to the patient based on the complain and follow up questions.
        Think step by step and mention the necessary requirements for diagnosing the patient including necessary support reports ECG Report, CT Scan, MRI Scan or blood test.
        
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
        Begin!
        
        Patient Symptoms: {complain}
        
        Follow Up questions and answer from patient:
        {chat_history}
        """
        self.symptoms_template = PromptTemplate.from_template(diagnose_prompt)
        self.ask_patient = PromptTemplate.from_template(validation_prompt)
        self.ask_reports = PromptTemplate.from_template(ask_report_prompt)
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)
        self.diganose_chain = LLMChain(llm=self.llm, prompt=self.symptoms_template, verbose=False)
        self.ask_patient_chain = LLMChain(llm=self.llm, prompt=self.ask_patient, verbose=False)
        self.doctor_agent = LLMChain(llm=self.llm, prompt=self.ask_reports, verbose=False)

    #
    def describe_symptoms(self, complaint):
        output = self.diganose_chain.run(patient_complain=complaint)
        return output

    def ask_validation_questions(self, symptoms, chat_history={}):
        conversation_history = self._process_chathistory(chat_history)
        question = self.ask_patient_chain.run(complain=symptoms, previous_conversation=conversation_history)
        return question

    @staticmethod
    def _process_chathistory(chathistory):
        conversation_string = ""
        for doctor_response, patient_response in chathistory.items():
            conversation_string += f"Question: {doctor_response} \n Patient's Response: {patient_response}"

        return conversation_string

    def ask_required_reports(self, complain, chathistory):
        conversation_string = self._process_chathistory(chathistory)
        assistance_response = self.doctor_agent.run(complain=complain, chat_history=conversation_string)
        return assistance_response


if __name__ == "__main__":
    diagnoser = Diagnoser()
    complain = "Mere pairon ke talvon par soojan aa rakhi h"
    patient_symptoms = diagnoser.describe_symptoms(complain)
    print(patient_symptoms)
    chat_history = {}
    for i in range(4):
        follow_up_questions = diagnoser.ask_validation_questions(symptoms=patient_symptoms, chat_history=chat_history)
        print(f"Doctor : {follow_up_questions}")
        patient_response = input("Patient: ")
        chat_history[follow_up_questions] = patient_response

    final_response = diagnoser.ask_required_reports(patient_symptoms, chat_history)
    print(final_response)
