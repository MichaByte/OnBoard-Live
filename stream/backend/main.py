from fastapi import FastAPI, Request, Response
from prisma import Prisma
from secrets import token_hex
import asyncio
from slack_bolt import Ack, App, Say
from slack_bolt.adapter.fastapi import SlackRequestHandler
from dotenv import load_dotenv
import os
import requests

load_dotenv()

api = FastAPI()

db = Prisma()

bolt = App(
    token=os.environ["SLACK_TOKEN"], signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

bolt_handler = SlackRequestHandler(bolt)


@api.get("/api/v1/stream_key/{stream_key}")
async def get_stream_by_key(stream_key: str):
    await db.connect()
    stream = await db.stream.find_first(where={"key": stream_key})
    await db.disconnect()
    return (
        stream if stream else Response(status_code=404, content="404: Stream not found")
    )


@api.get("/api/v1/user/{user_id}")
async def get_user_by_id(user_id: str):
    await db.connect()
    user = await db.user.find_first(where={"slack_id": user_id})
    await db.disconnect()
    return user if user else Response(status_code=404, content="404: User not found")


@api.post("/api/v1/user")
async def create_user(user: dict):
    await db.connect()
    try:
        new_user = await db.user.create(
            {"slack_id": user["slack_id"], "name": user["name"]}
        )
        print(new_user.id)
        new_stream = await db.stream.create(
            {"user": {"connect": {"id": new_user.id}}, "key": token_hex(16)}
        )
        print(new_user, new_stream)
        return new_user, new_stream
    except Exception as e:
        await db.disconnect()
        return Response(status_code=500, content=f"500: {str(e)}")
    finally:
        await db.disconnect()


@bolt.event("app_home_opened")
def handle_app_home_opened_events(body, logger, event, client):
    client.views_publish(
        user_id=event["user"],
        # the view object that appears in the app home
        view={
            "type": "home",
            "callback_id": "home_view",
            # body of the view
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Welcome to OnBoard Live! Try sending `/onboard-live-apply` in the #onboard-live channel to get started!",
                    },
                },
            ],
        },
    )


@bolt.view("apply")
def handle_application_submission(ack, body):
    ack()
    print(body)
    convo = bolt.client.conversations_open(users=body["user"]["id"], return_im=True)
    bolt.client.chat_postMessage(
        channel=convo["channel"]["id"], text=f"Your application has been submitted! We will review it shortly. Please do not send another application - If you haven't heard back in over 48 hours, message @mra! Here's a copy of your responses for your reference:\n{body['view']['state']['values']['project-info']['project-desc-value']['value']}"
    )


@bolt.command("/onboard-live-apply")
def apply(ack: Ack, command):
    ack()
    print(command)
    r = requests.post(
        "https://slack.com/api/views.open",
        headers={"Authorization": f"Bearer {os.environ['SLACK_TOKEN']}"},
        json={
            "trigger_id": command["trigger_id"],
            "view": {
                "type": "modal",
                "callback_id": "apply",
                "title": {"type": "plain_text", "text": "Apply to OnBoard Live"},
                "submit": {"type": "plain_text", "text": "Submit!"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "project-info",
                        "label": {
                            "type": "plain_text",
                            "text": "Some info on your project(s)",
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True,
                            "action_id": "project-desc-value",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "I'm going to make...",
                            },
                        },
                    },
                ],
            },
        },
    )
    print(r.status_code, r.text)
    # bolt.client.modal(channel=command['channel_id'], user=command['user_id'], text="Application form for OnBoard Live", blocks=[{


# 		"type": "header",
# 		"text": {
# 			"type": "plain_text",
# 			"text": "Welcome to OnBoard Live!",
# 		}
# 	},
# 	{
# 		"type": "section",
# 		"text": {
# 			"type": "mrkdwn",
# 			"text": "Before you can get designing, we need a little bit of info from you. All fields are required!"
# 		}
# 	},
# 	{
# 		"type": "divider"
# 	},
# 	{
# 		"type": "input",
# 		"element": {
# 			"type": "plain_text_input",
# 			"multiline": True,
# 			"action_id": "project_ideas_input-action",
# 			"placeholder": {
# 				"type": "plain_text",
# 				"text": "I want to make a..."
# 			}
# 		},
# 		"label": {
# 			"type": "plain_text",
# 			"text": "What do you plan to make with OnBoard Live?\nThis can be changed anytime!",
# 		}
# 	},
# 	{
# 		"type": "divider"
# 	},
# 	{
# 		"type": "actions",
# 		"elements": [
# 			{
# 				"type": "button",
# 				"text": {
# 					"type": "plain_text",
# 					"text": "Apply!",
# 				},
# 				"value": "apply",
# 				"style": "primary",
# 				"action_id": "actionId-0"

# 		}]}])


@api.post("/slack/events")
async def slack_event_endpoint(req: Request):
    return await bolt_handler.handle(req)
