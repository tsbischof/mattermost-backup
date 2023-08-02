# mattermostbackup
*mattermostbackup* is a Python module for fetching copies of the channels, posts, and files visible to you on a Mattermost server.

This is meant to be a basic backup solution for Mattermost users, suitlable for mirroring a meaningful subset of posts you can see.
If you have adminstrative access, you should consider a solution like the one laid out in the [Mattermost documentation](https://docs.mattermost.com/deploy/backup-disaster-recovery.html).

## Installation
### Dependencies
mattermostbackup requires:

* Python (>=3.7)
* mattermostdriver
* jsonschema

### User installation
`pip install .`

### Examples
The main entry point is the command-line interface `mattermost-backup`

`mattermost-backup --url your-mattermost-url --secrets your-mattermost-secrets.json`

This produces:

* `your-mattermost-url-YYYY-mm-dd.json`: the contents of your teams and posts
* `your-mattermost-url_files/`: all files attached to posts

## Configuration
User credentials should be stored in JSON format matching the one shown in `secrets.json.template`. 
These values are passed directly to [`mattermostdriver`](https://vaelor.github.io/python-mattermost-driver/).
You will need to either provide:

* your username and password
* a [user access token](https://docs.mattermost.com/integrations/cloud-personal-access-tokens.html)
