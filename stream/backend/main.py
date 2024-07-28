import json
import os
from contextlib import asynccontextmanager
from random import choice
from secrets import token_hex

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncAck, AsyncApp
import asyncio

load_dotenv()


async def update_active():
    global active_stream
    async with httpx.AsyncClient() as client:
        streams = (await client.get("http://localhost:9997/v3/paths/list")).json()[
            "items"
        ]
        active_streams = []
        for stream in streams:
            if stream["ready"]:
                active_streams.append(stream)
        try:
            new_stream = choice(active_streams)["name"]
            while new_stream == active_stream:
                new_stream = choice(active_streams)["name"]
            active_stream = new_stream
        except Exception:
            pass

async def init_active_update_task():
    global active_stream
    while True:
        asyncio.create_task(update_active())
        await asyncio.sleep(5 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(init_active_update_task())
    await db.connect()
    async with httpx.AsyncClient() as client:
        for stream in await db.stream.find_many():
            await client.post(
                "http://127.0.0.1:9997/v3/config/paths/add/" + stream.key,
                json={"name": stream.key},
            )
    await db.disconnect()
    yield


api = FastAPI(lifespan=lifespan)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Prisma()

bolt = AsyncApp(
    token=os.environ["SLACK_TOKEN"], signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

bolt_handler = AsyncSlackRequestHandler(bolt)

active_stream = None


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


@api.get("/api/v1/active_stream")
async def get_active_stream():
    global active_stream
    return active_stream


@bolt.event("app_home_opened")
async def handle_app_home_opened_events(body, logger, event, client):
    await client.views_publish(
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


@bolt.action("deny")
async def deny(ack, body):
    await ack()
    message = body["message"]
    applicant_slack_id = message["blocks"][len(message) - 3]["text"]["text"].split(
        ": "
    )[
        1
    ]  # I hate it. You hate it. We all hate it. Carry on.
    applicant_name = message["blocks"][len(message) - 7]["text"]["text"].split(
        "Name: "
    )[
        1
    ]  # oops i did it again
    await bolt.client.chat_delete(
        channel=body["container"]["channel_id"], ts=message["ts"]
    )
    await bolt.client.chat_postMessage(
        channel=body["container"]["channel_id"],
        text=f"{applicant_name}'s application has been denied! Remember to reach out to them if this is a fixable issue. Their username is <@{applicant_slack_id}>.",
    )


@bolt.action("approve")
async def approve(ack, body):
    await ack()
    await db.connect()
    message = body["message"]
    applicant_slack_id = message["blocks"][len(message) - 3]["text"]["text"].split(
        ": "
    )[
        1
    ]  # I hate it. You hate it. We all hate it. Carry on.
    applicant_name = message["blocks"][len(message) - 7]["text"]["text"].split(
        "Name: "
    )[
        1
    ]  # oops i did it again
    await bolt.client.chat_delete(
        channel=body["container"]["channel_id"], ts=message["ts"]
    )
    await bolt.client.chat_postMessage(
        channel=body["container"]["channel_id"],
        text=f"{applicant_name}'s application has been approved! Their username is <@{applicant_slack_id}>.",
    )
    if applicant_slack_id in [d.slack_id for d in await db.user.find_many()]:  # type: ignore
        return
    new_user = await db.user.create(
        {"slack_id": applicant_slack_id, "name": applicant_name}
    )
    new_stream = await db.stream.create(
        {"user": {"connect": {"id": new_user.id}}, "key": token_hex(16)}
    )
    sumbitter_convo = await bolt.client.conversations_open(
        users=applicant_slack_id, return_im=True
    )
    await bolt.client.chat_postMessage(
        channel=sumbitter_convo["channel"]["id"],
        text=f"Your application has been approved! Your stream key is `{new_stream.key}`. Keep this safe and do not share it with anyone!",
    )
    await db.disconnect()


@bolt.view("apply")
async def handle_application_submission(ack, body):
    await ack()
    user = body["user"]["id"]
    sumbitter_convo = await bolt.client.conversations_open(users=user, return_im=True)
    user_real_name = (await bolt.client.users_info(user=user))["user"]["real_name"]
    user_verified = ""
    async with httpx.AsyncClient() as client:
        user_verified = (
            "Eligible L"
            not in (
                await client.request(
                    url="https://verify.hackclub.dev/api/status",
                    method="GET",
                    content=json.dumps({"slack_id": user}),
                )
            ).text
        )
    await bolt.client.chat_postMessage(
        channel=sumbitter_convo["channel"]["id"],
        text=f"Your application has been submitted! We will review it shortly. Please do not send another application - If you haven't heard back in over 48 hours, or you forgot something in your application, please message <@{os.environ['ADMIN_SLACK_ID']}>! Here's a copy of your responses for your reference:\nSome info on your project(s): {body['view']['state']['values']['project-info']['project-info-body']['value']}{f'\nPlease fill out <https://forms.hackclub.com/eligibility?program=Onboard%20Live&slack_id={user}|the verification form>! We can only approve your application once this is done.' if not user_verified else ''}",
    )
    admin_convo = await bolt.client.conversations_open(
        users=os.environ["ADMIN_SLACK_ID"], return_im=True
    )
    will_behave = False
    boxes = body["view"]["state"]["values"]["c+wGI"]["checkboxes"]["selected_options"]
    if len(boxes) == 1 and boxes[0]["value"] == "value-1":
        will_behave = True
    await bolt.client.chat_postMessage(
        channel=admin_convo["channel"]["id"],
        text="New OnBoard Live application!",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":siren-real: New OnBoard Live application! :siren-real:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f":technologist: Name: {user_real_name}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f":white_check_mark: Is verified: {user_verified}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f":hammer_and_wrench: Will make: {body['view']['state']['values']['project-info']['project-info-body']['value']}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f":pray: Will behave on stream: {will_behave}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": f"Slack ID: {user}",
                    "emoji": True,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Approve",
                        },
                        "style": "primary",
                        "value": "approve",
                        "action_id": "approve",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "emoji": True, "text": "Deny"},
                        "style": "danger",
                        "value": "deny",
                        "action_id": "deny",
                    },
                ],
            },
        ],
    )


@bolt.command("/onboard-live-apply")
async def apply(ack: AsyncAck, command):
    await ack()
    async with httpx.AsyncClient() as client:
        print(
            (
                await client.post(
                    "https://slack.com/api/views.open",
                    headers={
                        "Authorization": f"Bearer {os.environ['SLACK_TOKEN']}",
                        "Content-type": "application/json; charset=utf-8",
                    },
                    json={
                        "trigger_id": command["trigger_id"],
                        "view": {
                            "type": "modal",
                            "callback_id": "apply",
                            "title": {
                                "type": "plain_text",
                                "text": "OnBoard Live Application",
                                "emoji": True,
                            },
                            "submit": {
                                "type": "plain_text",
                                "text": "Submit",
                                "emoji": True,
                            },
                            "close": {
                                "type": "plain_text",
                                "text": "Cancel",
                                "emoji": True,
                            },
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "Welcome to OnBoard Live!\n\n*Please make sure to read this form thoroughly.*\n\nWe can't wait to see what you make!\n\n_Depending on your screen, you might need to scroll down to see the whole form._",
                                    },
                                },
                                {"type": "divider"},
                                {
                                    "type": "input",
                                    "block_id": "project-info",
                                    "element": {
                                        "action_id": "project-info-body",
                                        "type": "plain_text_input",
                                        "multiline": True,
                                        "placeholder": {
                                            "type": "plain_text",
                                            "text": "I want to make...",
                                        },
                                    },
                                    "label": {
                                        "type": "plain_text",
                                        "text": "What do you plan on making?\n\nNote that you can make whatever you want, this is just so we know what level you're at!",
                                        "emoji": True,
                                    },
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "Examples of unacceptable behavior include (but are not limited to) streaming inappropriate content or content that is unrelated to PCB design, sharing your stream key with others, trying to abuse the system, streaming work that you did not do or is not actually live (i.e. pre-recorded). Inappropriate behavior may result in removal from the Hack Club Slack or other consequences, as stated in the <https://hackclub.com/conduct/|Code of Conduct>. Any use of your stream key is your responsibilty, so don't share it with anyone for any reason. Admins will never ask for your stream key. Please report any urgent rule violations by messaging <@U05C64XMMHV>. If they do not respond in 5 minutes, please ping <!subteam^S01E4DN8S0Y|fire-fighters>.",
                                    },
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Confirm that you have read the above by following these instructions:",
                                    },
                                    "accessory": {
                                        "type": "checkboxes",
                                        "options": [
                                            {
                                                "text": {
                                                    "type": "plain_text",
                                                    "text": "To agree that you will be well-behaved while you're live, DO NOT check this box. Instead, check the one below.",
                                                    "emoji": True,
                                                },
                                                "description": {
                                                    "type": "mrkdwn",
                                                    "text": "This is to make sure you're paying attention!",
                                                },
                                                "value": "value-0",
                                            },
                                            {
                                                "text": {
                                                    "type": "plain_text",
                                                    "text": "To agree that you will be well-behaved while you're live, check this box.",
                                                    "emoji": True,
                                                },
                                                "value": "value-1",
                                            },
                                        ],
                                        "action_id": "checkboxes",
                                    },
                                },
                                {"type": "divider"},
                                {
                                    "type": "context",
                                    "elements": [
                                        {
                                            "type": "mrkdwn",
                                            "text": "Please ask <@U05C64XMMHV> for help if you need it!",
                                        }
                                    ],
                                },
                            ],
                        },
                    },
                )
            ).text
        )


@bolt.action("checkboxes")
async def handle_some_action(ack):
    await ack()


@api.post("/slack/events")
async def slack_event_endpoint(req: Request):
    return await bolt_handler.handle(req)


# @api.on_event("startup")
# @repeat_every(seconds=5, wait_first=False,raise_exceptions=True)
# async def change_active_stream() -> None:
#     print('e')
#     global active_stream
#     with httpx.AsyncClient as client:
#         streams = (await client.get("http://localhost:9997/v3/paths/list")).json["items"]
#         active_stream = choice(streams)["name"]
