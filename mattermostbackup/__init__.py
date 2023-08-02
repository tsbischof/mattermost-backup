import argparse
import datetime
import json
import itertools
import jsonschema
import logging
import mattermostdriver
import os
import pathlib


def get_file_contents(mm, posts_page, files_root):
    for post_id in posts_page["posts"]:
        if not "files" in posts_page["posts"][post_id]["metadata"]:
            continue

        for file_info in posts_page["posts"][post_id]["metadata"]["files"]:
            dst_path = files_root / file_info["id"]
            dst_path.parent.mkdir(exist_ok=True, parents=True)
            if dst_path.exists():
                logging.debug(f"using cached {file_info['id']=}")
            else:
                logging.debug(f"{file_info['id']=}")
                content = mm.files.get_file(file_info["id"]).content
                dst_path.write_bytes(content)


def get_all_posts_for_channel(mm, channel_id, posts, files_root):
    order = list()
    for page in itertools.count(0):
        logging.debug(f"{channel_id=}, {page=}")
        posts_page = mm.posts.get_posts_for_channel(channel_id, params={"page": page})

        if not posts_page["posts"]:
            return order

        order.extend(posts_page["order"])
        get_file_contents(mm, posts_page, files_root)
        for post_id, post in posts_page["posts"].items():
            posts[post_id] = post


def get_all_channels_for_team(
    mm, user_id, team_id, ignore_direct_messages, posts, files_root
):
    for channel in mm.channels.get_channels_for_user(user_id, team_id):
        if ignore_direct_messages and channel["type"] in ["D", "G"]:
            logging.debug(f"skip direct message channel {channel['id']=}")
        else:
            logging.debug(f"{channel['id']=}")
            yield {
                "channel": channel,
                "posts": get_all_posts_for_channel(
                    mm, channel["id"], posts, files_root
                ),
            }


def get_all_teams_for_user(mm, user_id, ignore_direct_messages, posts, files_root):
    for team in mm.teams.get_user_teams(user_id=user_id):
        logging.debug(f"{team['id']=}")
        yield {
            "team": team,
            "channels": list(
                get_all_channels_for_team(
                    mm, user_id, team["id"], ignore_direct_messages, posts, files_root
                )
            ),
        }


def get_all_users(mm, user_ids, ignore_direct_messages, files_root):
    result = {"posts": dict()}

    for user_id in user_ids:
        logging.debug(f"{user_id=}")
        result["users"] = {
            "id": user_id,
            "user": mm.users.get_user(user_id),
            "teams": list(
                get_all_teams_for_user(
                    mm, user_id, ignore_direct_messages, result["posts"], files_root
                )
            ),
        }

    return result


def main():
    parser = argparse.ArgumentParser(
        "fetch all visible posts from a mattermost server. Files are written to disk, and messages are kept in memory. If you have enough messages to fill memory, you will need to refactor that section"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed debugging information",
    )
    parser.add_argument(
        "-s",
        "--secrets",
        type=str,
        default="secrets.json",
        help="Path to the 'secrets.json' file containing the user credentials",
    )
    parser.add_argument(
        "-u", "--url", type=str, help="URL of the Mattermost server to connect to"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=443, help="Port number for the server"
    )
    parser.add_argument(
        "-d",
        "--ignore-direct-messages",
        action="store_true",
        help="Ignore direct messages. The typical use case is to back up channels visible to you, but not your own messages.",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)

    driver_config = {
        "url": args.url,
        "port": args.port,
    }
    user_config_schema = {
        "type": "object",
        "properties": {
            "login_id": {"type": "string"},
            "password": {"type": "string"},
            "token": {"type": "string"},
        },
    }
    user_config = json.load(open(args.secrets))
    jsonschema.validate(instance=user_config, schema=user_config_schema)

    config = {**driver_config, **user_config}
    mm = mattermostdriver.Driver(config)

    mm.login()
    content = get_all_users(
        mm,
        ["me"],
        args.ignore_direct_messages,
        pathlib.Path(f"{driver_config['url']}_files"),
    )
    with open(
        f"{driver_config['url']}-{datetime.datetime.today().isoformat()[:10]}.json", "w"
    ) as stream_out:
        json.dump(content, stream_out, indent=2)

    mm.logout()
