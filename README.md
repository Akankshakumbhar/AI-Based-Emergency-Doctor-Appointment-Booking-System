# AI-Based-Emergency-Doctor-Appointment-Booking-System
Developed an AI-powered emergency doctor appointment booking system that automates patient-doctor matchmaking based on symptoms, urgency, and doctor availability. Integrated intelligent agents to analyze patient input, recommend appropriate specialists, and manage emergency cases in real-time using dynamic data and rule-based reasoning.
# 🏥 Agentic AI Emergency Doctor Appointment System

An intelligent, agent-based healthcare assistant that facilitates real-time emergency appointment booking, doctor recommendation, and AI-powered response management using modular agents and FastAPI.

---

## 📌 Project Overview

This project uses **Agentic AI** principles to create a smart emergency healthcare assistant. It enables:
- Real-time patient symptom assessment
- Doctor recommendation and appointment booking
- Emergency escalation and virtual AI doctor consultations
- Intelligent reminders and notifications

Built with a modular agent architecture using tools like `UserInputTool`, `SymptomSeverityTool`, and `EmergencyResponseTool` orchestrated by the `CrewAI` framework.

---

## 🧠 Features

- ✅ AI-powered patient intake and symptom analysis  
- 🚨 Emergency detection and escalation with ambulance alert simulation  
- 👨‍⚕️ Doctor recommendation based on severity and specialization  
- 📅 Appointment scheduling with notification system  
- 🧘‍♂️ AI calming guidance and virtual doctor simulation  
- 🔁 Real-time WebSocket communication for dynamic input  

---

## ⚙️ Technologies Used

- **Python 3.11+**  
- **FastAPI** – for backend API services  
- **CrewAI (Agentic AI)** – for agent orchestration  
- **WebSocket** – for real-time user interaction  
- **Pandas/JSON/CSV** – data management and state handling  
- **Custom Tools/Agents**:  
  - `UserInputTool`  
  - `SymptomSeverityTool`  
  - `DoctorSuggestionTool`  
  - `PushNotificationTool`  
  - `EmergencyResponseTool`  
  - `AIVoiceSpeakerTool`  



notification  purpose pushoverapi
phonecall twiio api


 haversine formula fir suggested doctor nearby location 
 waht is haversine formula to calculate  the great cricke distance between  two points on the sphere ( earth) using their latitude and longitude ,like gps calculation 

 we use the haversine  formula to computer distance between the patients location and healthcare  facilities . it accounts for earth curvature , converting lat lon to radiant, applying  the formula and returning kilometers  , we then sort families by distance and recommend the nearest  ones 
  patient shares locations  then distance to each facility  is calculated and return 5 top nearest  
  separate csv file is there which have all this information of country, lat , log and all details required 

  insurance  matching.....
  we match insurance  by splitting each doctor insurance  list normalizing to lowercase , and checking if the patient  insurance  is in list we sort result to protize matching  insurance  ,then by cost so patients see covered options first 


  .............
  emergency  consultations 
  for emergency  consultations  we use gemini to generate a structure  medical guidance  script  then script is converted into to speech with gets save mp3 and encore to base64foe web delivery. this provide immediate audio guidance while emergency  services are contacted 

  Twirl twilio markup language for controlling phone calls and sms 
  convert text to speech during phone call automatically
  we create voice response add say instruction with voice and language ,include pause ,and pass the twirl string when creating the call twilio convert text tospeech and plays it during calls
  

WebSocket::
a communication  protocol that allows a client like browser and server to talk to each other continuously in both direction 
over single connection  connection always onn never close

 th3 client connects to  server accepts and maintain  the connection 
 when ai need input it send a json message  with type  question the cluen5 dispalys set of questions user responds and the  response is ent back vioa a post endpoint . the setver stires it in memmory and the tool 4etrievers it to cont8ve the conversation  . this enables instant bidirectionap communication  
 
why websocket because we have hhtp normal client send request server response  connection close  
you refresh page browser ask server server respond done


