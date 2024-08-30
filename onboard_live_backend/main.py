import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from random import choice
from secrets import token_hex
from typing import Dict, List

import httpx
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from prisma import Prisma
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncAck, AsyncApp

load_dotenv(dotenv_path="./.env")

active_stream: Dict[str, str | bool] = {}
active_streams: List[Dict[str, str | bool]] = []

scheduler = AsyncIOScheduler()

FERNET = Fernet(os.environ["FERNET_KEY"])


def verify_gh_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise HTTPException(
            status_code=403, detail="x-hub-signature-256 header is missing!"
        )
    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")


async def get_recording_list(stream_key: str) -> List[str]:
    async with httpx.AsyncClient() as client:
        return [recording["start"] for recording in (await client.get(f"http://localhost:9997/v3/recordings/get/{stream_key}")).json()["segments"]]


async def update_active():
    global active_stream
    global active_streams
    async with httpx.AsyncClient() as client:
        streams_raw = (await client.get("http://localhost:9997/v3/paths/list")).json()[
            "items"
        ]
        streams = []
        for stream in streams_raw:
            streams.append({"name": stream["name"], "ready": stream["ready"]})
        for stream in streams:
            if stream["ready"] and stream not in active_streams:
                active_streams.append(stream)
        if len(active_streams) == 0:
            print("No active streams")
            return
        if active_stream == {}:
            print("No current active stream, picking new one...")
            active_stream = choice(active_streams)
            return
        if len(active_streams) == 1:
            return
        print(
            f"starting to pick new active stream (switching away from {active_stream['name']})"
        )
        new_stream = choice(active_streams)
        while new_stream["name"] == active_stream["name"]:
            print(
                f"re-attemppting to pick active stream since we picked {new_stream} again"
            )
            new_stream = choice(active_streams)
        print(f"found new stream to make active: {new_stream}")
        print(f"trying to find user associated with stream {active_stream['name']}")
        old_active_stream_user = await db.user.find_first(where={"id": (await db.stream.find_first(where={"key": str(active_stream["name"])})).user_id})  # type: ignore
        await bolt.client.chat_postMessage(channel="C07ERCGG989", text=f"Hey <@{old_active_stream_user.slack_id}>, you're no longer in focus!")  # type: ignore
        active_stream = new_stream
        active_stream_user = await db.user.find_first(where={"id": (await db.stream.find_first(where={"key": str(active_stream["name"])})).user_id})  # type: ignore
        await bolt.client.chat_postMessage(channel="C07ERCGG989", text=f"Hey <@{active_stream_user.slack_id}>, you're in focus! Make sure to tell us what you're working on!")  # type: ignore
        return True


async def check_for_new():
    global active_stream
    global active_streams
    async with httpx.AsyncClient() as client:
        streams_raw = (await client.get("http://localhost:9997/v3/paths/list")).json()[
            "items"
        ]
        streams_simple = []
        for stream in streams_raw:
            if stream["ready"]:
                streams_simple.append(stream["name"])
        active_streams_simple = []
        for i in active_streams:
            active_streams_simple.append(i["name"])
            if active_stream == {}:
                active_stream = {"name": i["name"], "ready": True}
        for stream in active_streams_simple:
            if stream not in streams_simple:
                active_streams.remove(
                    next(item for item in active_streams if item["name"] == stream)
                )
                active_stream = choice(active_streams)
        for stream in streams_simple:
            if stream not in active_streams_simple:
                active_streams.append({"name": stream, "ready": True})
        if len(active_streams) == 0:
            print("No active streams")
            active_stream = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await update_active()
    scheduler.start()
    scheduler.add_job(update_active, IntervalTrigger(seconds=5 * 60))
    scheduler.add_job(check_for_new, IntervalTrigger(seconds=3))
    await db.connect()
    async with httpx.AsyncClient() as client:
        for stream in await db.stream.find_many():
            await client.post(
                "http://127.0.0.1:9997/v3/config/paths/add/" + stream.key,
                json={"name": stream.key},
            )
    yield
    scheduler.shutdown()
    await db.disconnect()


api = FastAPI(lifespan=lifespan)  # type: ignore

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


@api.get("/auth/github/login")
async def github_redirect(request: Request):
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={os.environ['GH_CLIENT_ID']}&redirect_uri=https://live.onboard.hackclub.com/auth/github/callback&scopes=read:user&state={request.query_params['state']}"
    )


@api.get("/auth/github/callback")
async def github_callback(request: Request):
    code: str = request.query_params["code"]
    state: str = request.query_params["state"]
    user_id, pr_id = FERNET.decrypt(bytes.fromhex(state)).decode().split("+")
    db_user = await db.user.find_first_or_raise(where={"slack_id": user_id})
    user_stream_key = (await db.stream.find_first_or_raise(where={"user_id": db_user.id})).key
    db_pr = await db.pullrequest.find_first_or_raise(where={"github_id": int(pr_id)})
    async with httpx.AsyncClient() as client:
        token = (
            await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": os.environ["GH_CLIENT_ID"],
                    "client_secret": os.environ["GH_CLIENT_SECRET"],
                    "code": code,
                    "redirect_uri": "https://live.onboard.hackclub.com/auth/github/callback",
                },
                headers={"Accept": "application/json"},
            )
        ).json()["access_token"]

        gh_user: int = (
            await client.get(
                "https://api.github.com/user",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Bearer {token}",
                },
            )
        ).json()["id"]
        if gh_user == db_pr.gh_user_id:
            await db.pullrequest.update(
                {"user": {"connect": {"id": db_user.id}}, "gh_user_id": gh_user},
                {"id": db_pr.id},
            )
            stream_recs = await get_recording_list(user_stream_key)
            if stream_recs == []:
                return HTMLResponse(
                    "<h1>You don't have any sessions to submit! Please DM @mra on Slack if you think this is a mistake.</h1>"
                )
            await bolt.client.chat_postMessage(
                channel=user_id,
                text="Select your OnBoard Live sessions!",
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Select your sessions for review!",
                            "emoji": True,
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This is a section block with checkboxes.",
                        },
                        "accessory": {
                            "type": "checkboxes",
                            "options": [
                                json.loads("""{{"text": {{ "type": "mrkdwn", "text": "Your session on {pretty_time}"}}, "description": {{"type": "mrkdwn", "text": "You streamed for {length}"}}, "value": "checkbox-{filename}"}}""".format(pretty_time=recording, length=1, filename=recording)) for recording in stream_recs
                            ],
                            "action_id": "checkboxes",
                        },
                    },
                ],
            )
            return HTMLResponse(
                "<h1>Success! Your PR has been linked to your account. Check your Slack DMs for the next steps!</h1>"
            )
    return HTMLResponse(
        f"<h1>Looks like something went wrong! DM @mra on slack.</h1><p>This info might be of use to them: {FERNET.encrypt(bytes(str(db_pr.gh_user_id) + " " + str(gh_user) + " " + user_id + " " + pr_id + " " + state, encoding='utf-8'))}</p>", status_code=403
    )


@api.post("/api/v1/github/pr_event")
async def pr_event(request: Request):
    verify_gh_signature(
        await request.body(),
        os.environ["GH_HOOK_SECRET"],
        request.headers.get("x-hub-signature-256"),
    )
    body = json.loads(await request.body())
    if body["action"] == "labeled":
        if body["label"]["id"] == 7336079497:
            print("Added label has same id as OBL label!")
            await db.pullrequest.create(
                {
                    "github_id": body["pull_request"]["number"],
                    "gh_user_id": body["pull_request"]["user"]["id"],
                }
            )
    return


@api.get("/api/v1/stream_key/{stream_key}")
async def get_stream_by_key(stream_key: str):
    stream = await db.stream.find_first(where={"key": stream_key})
    return (
        stream if stream else Response(status_code=404, content="404: Stream not found")
    )


@api.get("/api/v1/active_stream")
async def get_active_stream():
    return active_stream["name"] if "name" in active_stream else ""


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
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://127.0.0.1:9997/v3/config/paths/add/" + new_stream.key,
            json={"name": new_stream.key},
        )
    await bolt.client.chat_postMessage(
        channel=sumbitter_convo["channel"]["id"],
        text=f"Welcome to OnBoard Live! Your stream key is {new_stream.key}. To use your stream key the easy way, go to <https://live.onboard.hackclub.com/{new_stream.key}/publish|this link>. You can also use it in OBS with the server URL of rtmp://live.onboard.hackclub.com:1935",
    )


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
        text=f"Your application has been submitted! We will review it shortly. Please do not send another application - If you haven't heard back in over 48 hours, or you forgot something in your application, please message <@{os.environ['ADMIN_SLACK_ID']}>! Here's a copy of your responses for your reference:\nSome info on your project(s): {body['view']['state']['values']['project-info']['project-info-body']['value']}\n{f'Please fill out <https://forms.hackclub.com/eligibility?program=Onboard%20Live&slack_id={user}|the verification form>! We can only approve your application once this is done.' if not user_verified else ''}",
    )
    will_behave = True
    # boxes = body["view"]["state"]["values"]["kAgeY"]["checkboxes"]["selected_options"]
    # if len(boxes) == 1 and boxes[0]["value"] == "value-1":
    #     will_behave = True
    await bolt.client.chat_postMessage(
        channel=os.environ["ADMIN_SLACK_ID"],
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
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Deny",
                        },
                        "style": "danger",
                        "value": "deny",
                        "action_id": "deny",
                    },
                ],
            },
        ],
    )


@bolt.command("/onboard-live-submit")
async def submit(ack: AsyncAck, command):
    await ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    text = command["text"]
    db_pr = await db.pullrequest.find_first(where={"github_id": int(text)})
    if db_pr is None:
        await bolt.client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="There doesn't seem to be a PR open with that ID! If this seems like a mistake, please message <@U05C64XMMHV> about it!",
        )
        return
    await bolt.client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"Please <https://live.onboard.hackclub.com/auth/github/login?state={FERNET.encrypt(bytes(f'{user_id}+{db_pr.github_id}', 'utf-8')).hex()}|click here> to authenticate with GitHub. This helps us verify that this is your PR!",
    )


@bolt.command("/onboard-live-apply")
async def apply(ack: AsyncAck, command):
    await ack()
    async with httpx.AsyncClient() as client:
        (
            await client.post(
                "https://slack.com/api/views.open",
                headers={
                    "Authorization": f"Bearer {os.environ['SLACK_TOKEN']}",
                    "Content-type": "application/json; charset=utf-8",
                },
                json={
                    "trigger_id": command["trigger_id"],
                    "unfurl_media": False,
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
                                    "type": "plain_text",
                                    "text": "As a participant in OnBoard Live, you must make sure that all your behavior on stream represents our values.",
                                    "emoji": True,
                                },
                            },
                            {
                                "type": "rich_text",
                                "elements": [
                                    {
                                        "type": "rich_text_section",
                                        "elements": [
                                            {
                                                "type": "text",
                                                "text": "Examples of unacceptable behavior include (but are not limited to):\n",
                                            }
                                        ],
                                    },
                                    {
                                        "type": "rich_text_list",
                                        "style": "bullet",
                                        "elements": [
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": "Streaming inappropriate content or content that is unrelated to PCB design",
                                                    }
                                                ],
                                            },
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": "Sharing your stream key with others",
                                                    }
                                                ],
                                            },
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": "Trying to abuse the system",
                                                    }
                                                ],
                                            },
                                            {
                                                "type": "rich_text_section",
                                                "elements": [
                                                    {
                                                        "type": "text",
                                                        "text": "Streaming pre-recorded work or work that is not yours",
                                                    }
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "Inappropriate behavior may result in removal from the Hack Club Slack or other consequences, as stated in the <https://hackclub.com/conduct/|Code of Conduct>. Any use of your stream key is your responsibilty, so don't share it with anyone for any reason. Admins will never ask for your stream key.\n\nPlease report any urgent rule violations by messaging <@U05C64XMMHV>. If they do not respond in 5 minutes, please ping <!subteam^S01E4DN8S0Y|fire-fighters>.",
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


@bolt.action("checkboxes")
async def handle_some_action(ack):
    await ack()


@api.post("/slack/events")
async def slack_event_endpoint(req: Request):
    return await bolt_handler.handle(req)


def main():
    uvicorn.run(api)


if __name__ == "__main__":
    main()
