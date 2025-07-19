from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests

class PushNotificationToolInput(BaseModel):
    """A message to push to the user."""
    message: str = Field(description="The message to push to the user")

class PushNotificationTool(BaseTool):
    name: str = "Send Push Notification"
    description: str = (
        "This tool is used to send a push notification to the user about their medical appointment"
    )
    args_schema: Type[BaseModel] = PushNotificationToolInput

    def _run(self, message: str) -> str:
        pushover_user = "uerwzqq8c1fywgcq9jxe6r3si6ffxx"
        pushover_token = "ak43wuu3qod4n12ikvz6zi1s4czsnz"
        pushover_url = "https://api.pushover.net/1/messages.json"
        
        print(f"\n📱 Sending notification: {message}")

        payload = {
            "token": pushover_token,
            "user": pushover_user,
            "message": message,
            "title": "Medical Appointment Notification"
        }
        
        try:
            response = requests.post(pushover_url, data=payload)
            response.raise_for_status()
            print("✅ Notification sent successfully!")
            return '{"notification_sent": true, "status": "success"}'
        except Exception as e:
            print(f"❌ Failed to send notification: {str(e)}")
            return '{"notification_sent": false, "error": "' + str(e) + '"}' 