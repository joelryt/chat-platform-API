import re
import requests
from operator import itemgetter
from datetime import datetime
import pytz


def show_all_threads(session):
    """
    Prints a list of all available threads.
    User can open or delete an existing thread.
    :param session: requests session to be used in the requests
    :return: returns the response of the request that the user makes
        and the next state
    """
    threads_collection_url = "/api/threads/"
    resp = session.get(SERVER_URL + threads_collection_url)
    body = resp.json()
    thread_ids = body["thread_ids"]
    resp_headers = []
    if not thread_ids:
        print("No threads to show.")
    else:
        for thread_id in thread_ids:
            resp = session.get(
                SERVER_URL + threads_collection_url + f"thread-{thread_id}/"
            )
            resp_headers.append(resp.headers)
    for headers in resp_headers:
        print(f"{headers['thread_id']}.\t{headers['title']}")
    print("Open thread by typing a number.")
    print("Delete thread by typing 'delete' and number (example: 'delete 1').")
    while True:
        user_input = input(">")
        if re.match("delete \\d+", user_input):
            num = int(user_input.split(" ")[-1])
            if num in thread_ids:
                resp = session.delete(
                    SERVER_URL + threads_collection_url + f"thread-{num}/"
                )
                if resp.status_code != 204:
                    print("Failed to delete thread")
                else:
                    print("Thread deleted successfully.")
                return resp, "all threads"
        else:
            try:
                num = int(user_input)
            except ValueError:
                print("Invalid input.")
                continue
        if num not in thread_ids:
            print("Invalid thread number.")
            continue
        break
    resp = session.get(SERVER_URL + threads_collection_url + f"thread-{num}/")
    return resp, "thread view"


def print_message(message):
    """
    Creates a printable string for a message.
    :param message: message that nees to be printed
    :return: printable string for the message
    """
    id, content, timestamp, parent, reactions = itemgetter(
        "id", "content", "timestamp", "parent", "reactions"
    )(message)
    printed_message = f"Message: {id}, {timestamp}"
    printed_message += (
        f", reply to message {parent}, likes: {reactions}\n"
        if parent != "None"
        else f", likes: {reactions}\n"
    )
    printed_message += content
    return printed_message


def print_thread(thread_title, thread_id, messages):
    """
    Prints all the messages in a thread ordered by timestamp.
    :param thread_title: title of thread
    :param thread_id: id of thread
    :param messages: list of messages to be printed (list of dictionaries)
    """
    messages.sort(key=lambda x: x["timestamp"])
    printed_thread = f"Thread Title: {thread_title} Id: {thread_id}\n\n"
    for message in messages:
        printed_thread += f"{print_message(message)}\n\n"
    print(printed_thread)


def show_thread_view(session, thread):
    """
    Prints a list of the messages in a thread.
    Then asks the user for a message id as an input, and then returns
    the message id as an integer for the next state to use.
    """
    threads_coll_url = "/api/threads/"
    messages_coll_url = "/messages/"
    thread_title = thread.headers["title"]
    thread_id = thread.headers["thread_id"]

    resp = session.get(
        SERVER_URL + threads_coll_url + f"thread-{thread_id}" + messages_coll_url
    )
    body = resp.json()
    message_ids = body["message_ids"]
    messages = []
    for message_id in message_ids:
        resp = session.get(
            SERVER_URL
            + threads_coll_url
            + f"thread-{thread_id}/"
            + messages_coll_url
            + f"message-{message_id}/"
        )
        resp1 = session.get(
            SERVER_URL
            + threads_coll_url
            + f"thread-{thread_id}/"
            + messages_coll_url
            + f"message-{message_id}/reactions/"
        )
        reaction_amount = len(resp1.json()["reaction_ids"])
        message = {
            "id": message_id,
            "content": resp.headers["message_content"],
            "timestamp": resp.headers["timestamp"],
            "parent": resp.headers["parent_id"],
            "reactions": str(reaction_amount),
        }

        messages.append(message)

    print_thread(thread_title, thread_id, messages)

    print("Select a message by typing a number.")
    print("Edit thread title by typing 'title yourtitlehere'.")
    print(" To go back, type 'back' or 'b'.")
    while True:
        user_input = input(">")
        if user_input in ["back", "b"]:
            resp = resp
            state = "all threads"
            break
        elif user_input.startswith("title "):
            new_title = user_input[6:]
            thread_item = {
                "title": new_title
            }
            resp = session.put(SERVER_URL + threads_coll_url + f"thread-{thread_id}/", json=thread_item)
            if resp.status_code == 204:
                print(f"Updated thread title to {new_title}")
            else:
                print(f"Failed to update thread title to {new_title}")
            resp = session.get(SERVER_URL + threads_coll_url + f"thread-{thread_id}/")
            state = "thread view"
            break
        else:
            try:
                selected_id = int(user_input)
                if selected_id in message_ids:
                    resp = session.get(
                        SERVER_URL
                        + threads_coll_url
                        + f"thread-{thread_id}/"
                        + messages_coll_url
                        + f"message-{selected_id}/"
                    )
                    state = "message actions"
                    break
                else:
                    raise ValueError
            except ValueError:
                print("Invalid input.")
    return resp, state


def show_message_actions(session, resp):
    print("Select an action for the selected message by typing: ")
    print("[reply], for replying to the message")
    print("[like], for liking the message")
    print("[back], for previous window")
    while True:
        user_input = input(">")
        if user_input in ["back", "b"]:
            resp = None
            state = "thread view"
            break
        else:
            try:
                if user_input in ["reply", "like", "delethe"]:
                    if user_input == "reply":
                        state = "reply to message"
                        resp = resp
                        break
                    elif user_input == "like":
                        state = "like to message"
                        resp = resp
                        break
            except ValueError:
                print("!!!!!!INVALID INPUT!!!!!!!")
                print("Select an action for the selected message by typing: ")
                print("[reply], for replying to the message")
                print("[like], for liking the message")
                print("[back], for previous window")
                continue
    return resp, state


def reply_to_message(session, resp):
    parent_id = resp.headers["message_id"]
    thread_id = resp.headers["thread_id"]
    print(thread_id)
    threads_coll_url = "/api/threads/"
    messages_coll_url = "messages/"
    print(
        "Please write your reply for message "
        + str(parent_id)
        + " or go back by writing [back]"
    )
    while True:
        message_content = input(">")
        if message_content in ["back", "b"]:
            resp = None
            state = "message actions"
            break
        if len(message_content) > 0:
            user_id = ask_username(session)
            message_item = {
                "message_content": message_content,
                "timestamp": datetime.now(pytz.utc).isoformat(),
                "sender_id": int(user_id),
                "parent_id": int(parent_id),
            }
            url = (
                SERVER_URL
                + threads_coll_url
                + f"thread-{thread_id}/"
                + messages_coll_url
            )
            response = session.post(url, json=message_item)
            print("MESSAGE POSTED!")
            resp = None
            state = "all threads"
            break
        else:
            print("Message is not written")
            continue
    return resp, state


def give_like(session, resp):
    """
    Likes the message and creates an username
    """
    message_id = resp.headers["message_id"]
    thread_id = resp.headers["thread_id"]
    threads_collection_url = "/api/threads/"
    thread = f"thread-{thread_id}"
    reaction = "/messages/" + f"message-{message_id}" + "/reactions/"
    react_url = SERVER_URL + threads_collection_url + thread + reaction
    user_id = ask_username(session)
    data = {
        "reaction_type": int(1),
        "user_id": int(user_id),
        "message_id": int(message_id),
    }
    response = session.post(react_url, json=data)
    print("LIKED!")
    state = "all threads"
    return resp, state


def ask_username(session):
    while True:
        print("Please, insert your username")
        username = input(">")
        if len(username) > 16:
            print("Username can not be longer than 16 letters!")
            continue
        if type(username) is not str:
            print("Username must be a string of characters!")
            continue
        else:
            response = session.get(SERVER_URL + "/api/users/" + username + "/")
            if response.status_code == 404:
                url = SERVER_URL + "/api/users/"
                stock_password = "password"
                new_user = {"username": username, "password": stock_password}
                response = session.post(url, json=new_user)
                print(response)
                print("User " + username + " created")
                response = session.get(SERVER_URL + "/api/users/" + username + "/")
            user_id = response.headers["user_id"]
            return user_id


def main(session):
    state = "all threads"
    while True:
        if state == "all threads":
            resp, state = show_all_threads(session)
        elif state == "thread view":
            resp, state = show_thread_view(session, resp)
        elif state == "message actions":
            resp, state = show_message_actions(session, resp)
        elif state == "like to message":
            resp, state = give_like(session, resp)
        elif state == "reply to message":
            resp, state = reply_to_message(session, resp)


if __name__ == "__main__":
    SERVER_URL = "http://localhost:5000"
    with requests.Session() as s:
        main(s)
